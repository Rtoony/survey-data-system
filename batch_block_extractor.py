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


class BatchBlockExtractor:
    """Extract block definitions from DXF files for batch import"""
    
    def __init__(self, db_config: Dict):
        """Initialize extractor with database configuration"""
        self.db_config = db_config
    
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
        Guess block category based on naming conventions.
        
        Args:
            block_name: Name of the block
            
        Returns:
            Suggested category string
        """
        name_upper = block_name.upper()
        
        # Common CAD block naming patterns
        if any(x in name_upper for x in ['TITLE', 'BORDER', 'SHEET']):
            return 'Title Blocks'
        elif any(x in name_upper for x in ['NORTH', 'ARROW', 'SCALE']):
            return 'Symbols'
        elif any(x in name_upper for x in ['TREE', 'PLANT', 'SHRUB', 'LANDSCAPE']):
            return 'Landscape'
        elif any(x in name_upper for x in ['VEHICLE', 'CAR', 'TRUCK', 'AUTO']):
            return 'Vehicles'
        elif any(x in name_upper for x in ['PERSON', 'PEOPLE', 'HUMAN']):
            return 'People'
        elif any(x in name_upper for x in ['FURNITURE', 'CHAIR', 'DESK', 'TABLE']):
            return 'Furniture'
        elif any(x in name_upper for x in ['UTIL', 'PIPE', 'VALVE', 'MANHOLE', 'MH']):
            return 'Utilities'
        elif any(x in name_upper for x in ['DETAIL', 'DTL']):
            return 'Details'
        elif any(x in name_upper for x in ['NOTE', 'CALLOUT', 'LABEL']):
            return 'Annotations'
        elif re.match(r'^[A-Z]{1,4}-[A-Z]{3,6}', block_name):
            # Discipline-based naming (e.g., C-UTIL, E-LGHT)
            return 'Discipline Symbols'
        else:
            return 'Uncategorized'
    
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
            
            # Create figure and render using matplotlib backend
            fig = plt.figure(figsize=(4, 4))
            ax = fig.add_axes([0, 0, 1, 1])
            ax.set_aspect('equal')
            
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
