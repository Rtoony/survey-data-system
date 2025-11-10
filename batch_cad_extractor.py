"""
Batch CAD Extractor - Unified extractor for blocks, details, hatches, and linetypes
Uses strategy pattern for clean separation of concerns
"""

import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for web server environment

import ezdxf
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import io
from typing import List, Dict, Optional
import re
import psycopg2
from psycopg2.extras import RealDictCursor
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


class CADExtractorStrategy:
    """Base strategy for extracting CAD elements"""
    
    def __init__(self, db_config: Dict):
        self.db_config = db_config
    
    def extract_from_file(self, file_path: str, source_filename: str) -> List[Dict]:
        """Extract elements from DXF file - to be implemented by subclasses"""
        raise NotImplementedError
    
    def generate_svg_preview(self, element) -> str:
        """Generate SVG preview - to be implemented by subclasses"""
        raise NotImplementedError
    
    def _generate_placeholder_svg(self, element_name: str) -> str:
        """Generate a simple placeholder SVG"""
        return f'''<svg width="200" height="100" xmlns="http://www.w3.org/2000/svg">
            <rect width="200" height="100" fill="#1a1a1a" stroke="#00ffff" stroke-width="2"/>
            <text x="100" y="50" text-anchor="middle" fill="#00ffff" font-family="monospace" font-size="12">
                {element_name[:20]}
            </text>
        </svg>'''


class BlockExtractor(CADExtractorStrategy):
    """Extract block definitions for symbols"""
    
    def __init__(self, db_config: Dict):
        super().__init__(db_config)
        self.valid_categories = self._load_valid_categories()
    
    def _load_valid_categories(self) -> List[Dict]:
        """Load valid categories from the category_codes table"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            cur.execute("""
                SELECT DISTINCT code, full_name, description 
                FROM category_codes 
                WHERE is_active = true 
                ORDER BY code
            """)
            
            categories = [dict(row) for row in cur.fetchall()]
            cur.close()
            conn.close()
            
            return categories
            
        except Exception as e:
            print(f"Failed to load categories from database: {str(e)}")
            return []
    
    def get_valid_categories(self) -> List[Dict]:
        return self.valid_categories
    
    def extract_from_file(self, file_path: str, source_filename: str) -> List[Dict]:
        elements = []
        
        try:
            doc = ezdxf.readfile(file_path)
            
            for block in doc.blocks:
                if block.name.startswith('*') or len(block) == 0:
                    continue
                
                try:
                    element_data = {
                        'name': block.name,
                        'source_file': source_filename,
                        'category': self._guess_category(block.name),
                        'description': self._generate_description(block),
                        'entity_count': len(block),
                        'svg_preview': self.generate_svg_preview((doc, block)),
                        'exists': False,
                        'action': 'import',
                        'import_type': 'blocks'
                    }
                    elements.append(element_data)
                    
                except Exception as e:
                    print(f"Failed to process block {block.name}: {str(e)}")
                    continue
        
        except Exception as e:
            raise Exception(f"Failed to read DXF file: {str(e)}")
        
        return elements
    
    def generate_svg_preview(self, element) -> str:
        try:
            doc, block = element
            
            temp_doc = ezdxf.new()
            temp_msp = temp_doc.modelspace()
            
            if block.name not in temp_doc.blocks:
                temp_block = temp_doc.blocks.new(block.name)
                for entity in block:
                    temp_block.add_entity(entity.copy())
            
            temp_msp.add_blockref(block.name, (0, 0))
            
            fig = plt.figure(figsize=(4, 4), facecolor='#2a2a2a')
            ax = fig.add_axes([0, 0, 1, 1])
            ax.set_aspect('equal')
            ax.set_facecolor('#2a2a2a')
            
            ctx = RenderContext(temp_doc)
            out = MatplotlibBackend(ax)
            Frontend(ctx, out).draw_layout(temp_msp, finalize=True)
            
            ax.axis('off')
            
            svg_buffer = io.StringIO()
            fig.savefig(svg_buffer, format='svg', bbox_inches='tight', pad_inches=0.1)
            svg_content = svg_buffer.getvalue()
            svg_buffer.close()
            
            plt.close(fig)
            
            return svg_content
            
        except Exception as e:
            print(f"Failed to generate SVG: {str(e)}")
            return self._generate_placeholder_svg("BLOCK")
    
    def _guess_category(self, block_name: str) -> str:
        if not self.valid_categories:
            return ''
        
        name_upper = block_name.upper()
        
        category_patterns = {
            'UTIL': ['UTIL', 'PIPE', 'VALVE', 'MANHOLE', 'MH', 'SEWER', 'WATER', 'GAS', 'ELECTRIC'],
            'TREE': ['TREE', 'PALM'],
            'SHRU': ['SHRUB', 'PLANT', 'BUSH'],
            'TURF': ['TURF', 'LAWN', 'GRASS'],
            'HARD': ['PAVE', 'WALK', 'SIDEWALK', 'PLAZA'],
            'ROAD': ['ROAD', 'STREET', 'CURB'],
            'PAVE': ['PARKING', 'DRIVEWAY'],
            'STOR': ['STORM', 'DRAIN', 'BMP', 'SWALE'],
            'POND': ['POND', 'BASIN', 'DETENTION', 'RETENTION'],
            'GRAD': ['GRAD', 'SLOPE', 'CONTOUR'],
            'WALL': ['WALL', 'RETAINING'],
            'BLDG': ['BLDG', 'BUILDING', 'STRUCTURE'],
            'FENCE': ['FENCE', 'GATE', 'BARRIER'],
            'SIGN': ['SIGN', 'SIGNAGE'],
            'TOPO': ['TOPO', 'SURVEY', 'SHOT'],
            'CTRL': ['CTRL', 'CONTROL', 'BENCHMARK', 'MONUMENT'],
            'BNDY': ['BNDY', 'BOUNDARY', 'PROPERTY'],
            'DEMO': ['DEMO', 'DEMOLITION', 'REMOVE'],
            'EROS': ['EROS', 'EROSION', 'SWPPP'],
            'ADA': ['ADA', 'ACCESSIBLE', 'RAMP'],
            'IRIG': ['IRIG', 'IRRIGATION', 'SPRINKLER']
        }
        
        for category_code, keywords in category_patterns.items():
            if any(keyword in name_upper for keyword in keywords):
                if any(cat['code'] == category_code for cat in self.valid_categories):
                    return category_code
        
        return ''
    
    def _generate_description(self, block) -> str:
        entity_types = {}
        for entity in block:
            entity_type = entity.dxftype()
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
        
        parts = []
        for etype, count in sorted(entity_types.items()):
            if etype in ['LINE', 'LWPOLYLINE', 'POLYLINE', 'ARC', 'CIRCLE', 'TEXT']:
                parts.append(f"{count} {etype.lower()}")
        
        if parts:
            return f"Contains: {', '.join(parts[:3])}"
        else:
            return f"Block with {len(block)} entities"


class DetailExtractor(BlockExtractor):
    """Extract block definitions for construction details"""
    
    def __init__(self, db_config: Dict):
        super().__init__(db_config)
        self.valid_disciplines = self._load_valid_disciplines()
    
    def _load_valid_disciplines(self) -> List[Dict]:
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            cur.execute("""
                SELECT DISTINCT code, full_name, description 
                FROM discipline_codes 
                WHERE is_active = true 
                ORDER BY code
            """)
            
            disciplines = [dict(row) for row in cur.fetchall()]
            cur.close()
            conn.close()
            
            return disciplines
            
        except Exception as e:
            print(f"Failed to load disciplines from database: {str(e)}")
            return []
    
    def get_valid_disciplines(self) -> List[Dict]:
        return self.valid_disciplines
    
    def extract_from_file(self, file_path: str, source_filename: str) -> List[Dict]:
        elements = super().extract_from_file(file_path, source_filename)
        
        # Modify for detail-specific fields
        for element in elements:
            element['import_type'] = 'details'
            element['discipline'] = self._guess_discipline(element['name'])
            element['detail_category'] = element.pop('category', '')
        
        return elements
    
    def _guess_discipline(self, detail_name: str) -> str:
        if not self.valid_disciplines:
            return ''
        
        name_upper = detail_name.upper()
        
        discipline_patterns = {
            'C': ['C-', 'CIVIL'],
            'L': ['L-', 'LAND', 'LANDSCAPE'],
            'S': ['S-', 'STRUCT'],
            'A': ['A-', 'ARCH'],
            'M': ['M-', 'MECH'],
            'E': ['E-', 'ELEC'],
            'P': ['P-', 'PLUMB']
        }
        
        for disc_code, keywords in discipline_patterns.items():
            if any(name_upper.startswith(keyword) for keyword in keywords):
                if any(disc['code'] == disc_code for disc in self.valid_disciplines):
                    return disc_code
        
        return ''


class HatchExtractor(CADExtractorStrategy):
    """Extract hatch pattern definitions"""
    
    def extract_from_file(self, file_path: str, source_filename: str) -> List[Dict]:
        elements = []
        
        try:
            doc = ezdxf.readfile(file_path)
            
            hatch_patterns = {}
            msp = doc.modelspace()
            
            for entity in msp.query('HATCH'):
                pattern_name = entity.dxf.pattern_name
                if pattern_name and pattern_name != 'SOLID':
                    if pattern_name not in hatch_patterns:
                        hatch_patterns[pattern_name] = entity
            
            for pattern_name, hatch_entity in hatch_patterns.items():
                try:
                    element_data = {
                        'name': pattern_name,
                        'source_file': source_filename,
                        'pattern_type': self._determine_pattern_type(pattern_name),
                        'description': f"Hatch pattern: {pattern_name}",
                        'svg_preview': self.generate_svg_preview(pattern_name),
                        'exists': False,
                        'action': 'import',
                        'import_type': 'hatches'
                    }
                    
                    elements.append(element_data)
                    
                except Exception as e:
                    print(f"Failed to process hatch pattern {pattern_name}: {str(e)}")
                    continue
        
        except Exception as e:
            raise Exception(f"Failed to read DXF file: {str(e)}")
        
        return elements
    
    def generate_svg_preview(self, pattern_name) -> str:
        try:
            fig, ax = plt.subplots(figsize=(4, 2), facecolor='#2a2a2a')
            ax.set_facecolor('#2a2a2a')
            ax.set_xlim(0, 4)
            ax.set_ylim(0, 2)
            ax.axis('off')
            
            rect = mpatches.Rectangle((0.5, 0.5), 3, 1, linewidth=2, 
                                     edgecolor='#00ffff', facecolor='none')
            ax.add_patch(rect)
            
            ax.text(2, 0.2, pattern_name, ha='center', va='center', 
                   color='#00ffff', fontsize=10, family='monospace')
            
            svg_buffer = io.StringIO()
            fig.savefig(svg_buffer, format='svg', bbox_inches='tight', pad_inches=0.1)
            svg_content = svg_buffer.getvalue()
            svg_buffer.close()
            
            plt.close(fig)
            
            return svg_content
            
        except Exception as e:
            print(f"Failed to generate hatch SVG: {str(e)}")
            return self._generate_placeholder_svg("HATCH")
    
    def _determine_pattern_type(self, pattern_name: str) -> str:
        standard_patterns = ['ANSI31', 'ANSI32', 'ANSI33', 'ANSI34', 'ANSI35', 'ANSI36', 'ANSI37', 'ANSI38',
                           'AR-B816', 'AR-CONC', 'AR-HBONE', 'AR-PARQ1', 'AR-RROOF', 'AR-RSHKE', 'AR-SAND',
                           'BOX', 'BRASS', 'BRICK', 'BRSTONE', 'CLAY', 'CORK', 'CROSS', 'DASH', 'DOLMIT',
                           'DOTS', 'EARTH', 'ESCHER', 'FLEX', 'GRASS', 'GRATE', 'GRAVEL', 'HEX', 'HONEY',
                           'HOUND', 'INSUL', 'LINE', 'MUDST', 'NET', 'NET3', 'PLAST', 'PLASTI', 'SACNCR',
                           'SQUARE', 'STARS', 'STEEL', 'SWAMP', 'TRANS', 'TRIANG', 'ZIGZAG']
        
        return 'Predefined' if pattern_name.upper() in standard_patterns else 'User-defined'


class LinetypeExtractor(CADExtractorStrategy):
    """Extract linetype definitions"""
    
    def extract_from_file(self, file_path: str, source_filename: str) -> List[Dict]:
        elements = []
        
        try:
            doc = ezdxf.readfile(file_path)
            
            for linetype in doc.linetypes:
                if linetype.dxf.name in ['CONTINUOUS', 'ByLayer', 'ByBlock']:
                    continue
                
                try:
                    element_data = {
                        'name': linetype.dxf.name,
                        'source_file': source_filename,
                        'description': linetype.dxf.description if hasattr(linetype.dxf, 'description') else '',
                        'pattern_definition': str(linetype.pattern),
                        'svg_preview': self.generate_svg_preview(linetype.dxf.name),
                        'exists': False,
                        'action': 'import',
                        'import_type': 'linetypes'
                    }
                    
                    elements.append(element_data)
                    
                except Exception as e:
                    print(f"Failed to process linetype {linetype.dxf.name}: {str(e)}")
                    continue
        
        except Exception as e:
            raise Exception(f"Failed to read DXF file: {str(e)}")
        
        return elements
    
    def generate_svg_preview(self, linetype_name) -> str:
        try:
            fig, ax = plt.subplots(figsize=(4, 1), facecolor='#2a2a2a')
            ax.set_facecolor('#2a2a2a')
            ax.set_xlim(0, 4)
            ax.set_ylim(0, 1)
            ax.axis('off')
            
            ax.plot([0.5, 3.5], [0.5, 0.5], color='#00ffff', linewidth=2)
            
            ax.text(2, 0.15, linetype_name, ha='center', va='center',
                   color='#00ffff', fontsize=9, family='monospace')
            
            svg_buffer = io.StringIO()
            fig.savefig(svg_buffer, format='svg', bbox_inches='tight', pad_inches=0.1)
            svg_content = svg_buffer.getvalue()
            svg_buffer.close()
            
            plt.close(fig)
            
            return svg_content
            
        except Exception as e:
            print(f"Failed to generate linetype SVG: {str(e)}")
            return self._generate_placeholder_svg("LINETYPE")


class BatchCADExtractor:
    """Factory for creating appropriate extractor strategy based on import type"""
    
    EXTRACTORS = {
        'blocks': BlockExtractor,
        'details': DetailExtractor,
        'hatches': HatchExtractor,
        'linetypes': LinetypeExtractor
    }
    
    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.extractors = {
            import_type: extractor_class(db_config)
            for import_type, extractor_class in self.EXTRACTORS.items()
        }
    
    def extract_from_file(self, file_path: str, source_filename: str, import_type: str) -> List[Dict]:
        """Extract CAD elements using appropriate strategy"""
        if import_type not in self.EXTRACTORS:
            raise ValueError(f"Invalid import type: {import_type}")
        
        extractor = self.extractors[import_type]
        return extractor.extract_from_file(file_path, source_filename)
    
    def get_metadata(self, import_type: str) -> Dict:
        """Get metadata (valid categories, disciplines) for import type"""
        metadata = {}
        
        if import_type == 'blocks':
            metadata['valid_categories'] = self.extractors['blocks'].get_valid_categories()
        elif import_type == 'details':
            metadata['valid_categories'] = self.extractors['details'].get_valid_categories()
            metadata['valid_disciplines'] = self.extractors['details'].get_valid_disciplines()
        
        return metadata
