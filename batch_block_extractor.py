"""
Batch Block Extractor
Extracts block definitions from DXF files and generates SVG previews
"""

import ezdxf
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import io
import base64
from typing import List, Dict, Optional
import re
import psycopg2
from psycopg2.extras import RealDictCursor


class BatchBlockExtractor:
    """Extract block definitions from DXF files for batch import"""
    
    def __init__(self, db_config: Dict):
        """Initialize extractor with database configuration"""
        self.db_config = db_config
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
        """Return the list of valid categories for the frontend"""
        return self.valid_categories
    
    def extract_blocks_from_file(self, file_path: str, source_filename: str) -> List[Dict]:
        """
        Extract all block definitions from a DXF file.
        
        Args:
            file_path: Path to DXF file
            source_filename: Original filename for reference
            
        Returns:
            List of block dictionaries with metadata and SVG previews
        """
        blocks = []
        
        try:
            doc = ezdxf.readfile(file_path)
            
            # Iterate through all block definitions
            for block in doc.blocks:
                # Skip model space and paper space blocks
                if block.name.startswith('*'):
                    continue
                
                # Skip empty blocks
                if len(block) == 0:
                    continue
                
                try:
                    block_data = {
                        'name': block.name,
                        'source_file': source_filename,
                        'category': self._guess_category(block.name),
                        'description': self._generate_description(block),
                        'entity_count': len(block),
                        'svg_preview': self._generate_svg_preview(doc, block),
                        'exists': False,  # Will be checked by frontend
                        'action': 'import'  # Default action
                    }
                    
                    blocks.append(block_data)
                    
                except Exception as e:
                    # Skip blocks that fail to process
                    print(f"Failed to process block {block.name}: {str(e)}")
                    continue
        
        except Exception as e:
            raise Exception(f"Failed to read DXF file: {str(e)}")
        
        return blocks
    
    def _guess_category(self, block_name: str) -> str:
        """
        Guess block category based on naming conventions using valid CAD standards.
        
        Args:
            block_name: Name of the block
            
        Returns:
            Suggested category code from category_codes table
        """
        if not self.valid_categories:
            return ''
        
        name_upper = block_name.upper()
        
        # Define keyword mappings to category codes based on CAD Layer Vocabulary
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
        
        # Check each pattern
        for category_code, keywords in category_patterns.items():
            if any(keyword in name_upper for keyword in keywords):
                # Verify this category exists in our loaded categories
                if any(cat['code'] == category_code for cat in self.valid_categories):
                    return category_code
        
        # If no match found, return empty string to force manual selection
        return ''
    
    def _generate_description(self, block) -> str:
        """
        Generate a description based on block contents.
        
        Args:
            block: ezdxf block definition
            
        Returns:
            Description string
        """
        entity_types = {}
        for entity in block:
            entity_type = entity.dxftype()
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
        
        # Create description from entity composition
        parts = []
        for etype, count in sorted(entity_types.items()):
            if etype in ['LINE', 'LWPOLYLINE', 'POLYLINE', 'ARC', 'CIRCLE']:
                parts.append(f"{count} {etype.lower()}")
        
        if parts:
            return f"Contains: {', '.join(parts[:3])}"
        else:
            return f"Block with {len(block)} entities"
    
    def _generate_svg_preview(self, doc, block) -> str:
        """
        Generate SVG preview of the block.
        
        Args:
            doc: ezdxf document
            block: Block definition
            
        Returns:
            SVG string or empty string if generation fails
        """
        try:
            import matplotlib.pyplot as plt
            
            # Create a temporary document with just this block
            temp_doc = ezdxf.new()
            temp_msp = temp_doc.modelspace()
            
            # Copy block definition to temp document
            if block.name not in temp_doc.blocks:
                temp_block = temp_doc.blocks.new(block.name)
                for entity in block:
                    temp_block.add_entity(entity.copy())
            
            # Insert the block at origin
            temp_msp.add_blockref(block.name, (0, 0))
            
            # Create figure with dark gray background
            fig = plt.figure(figsize=(4, 4), facecolor='#2a2a2a')
            ax = fig.add_axes([0, 0, 1, 1])
            ax.set_aspect('equal')
            ax.set_facecolor('#2a2a2a')
            
            ctx = RenderContext(temp_doc)
            out = MatplotlibBackend(ax)
            Frontend(ctx, out).draw_layout(temp_msp, finalize=True)
            
            # Remove axes
            ax.axis('off')
            
            # Convert figure to SVG
            svg_buffer = io.StringIO()
            fig.savefig(svg_buffer, format='svg', bbox_inches='tight', pad_inches=0.1)
            svg_content = svg_buffer.getvalue()
            svg_buffer.close()
            
            # Clean up matplotlib figure
            plt.close(fig)
            
            return svg_content
            
        except Exception as e:
            # If SVG generation fails, return a placeholder
            print(f"Failed to generate SVG for {block.name}: {str(e)}")
            return self._generate_placeholder_svg(block.name)
    
    def _generate_placeholder_svg(self, block_name: str) -> str:
        """Generate a simple placeholder SVG"""
        return f'''<svg width="200" height="100" xmlns="http://www.w3.org/2000/svg">
            <rect width="200" height="100" fill="#1a1a1a" stroke="#00ffff" stroke-width="2"/>
            <text x="100" y="50" text-anchor="middle" fill="#00ffff" font-family="monospace" font-size="12">
                {block_name[:20]}
            </text>
        </svg>'''
