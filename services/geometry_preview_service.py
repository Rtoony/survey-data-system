"""
Geometry Preview Service
Generates SVG previews of entity geometries for visual review during classification.

Supports common CAD entity types:
- Points (survey points, structures, symbols)
- Lines/Polylines (utility lines, property lines)
- Circles (manholes, valves, structures)
- Polygons (parcels, BMPs, zones)
- Arcs (curve segments)
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Tuple, Optional
import re
from shapely import wkt
from shapely.geometry import Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon


class GeometryPreviewService:
    """Service for generating SVG previews of entity geometries."""

    # AutoCAD Color Index (ACI) to hex color mapping
    ACI_COLORS = {
        1: '#FF0000',   # Red
        2: '#FFFF00',   # Yellow
        3: '#00FF00',   # Green
        4: '#00FFFF',   # Cyan
        5: '#0000FF',   # Blue
        6: '#FF00FF',   # Magenta
        7: '#FFFFFF',   # White
        8: '#808080',   # Gray
        9: '#C0C0C0',   # Light Gray
        10: '#FF0000',  # Red
        30: '#FF6600',  # Orange
        40: '#FF9933',  # Light Orange
        50: '#996633',  # Brown
        60: '#FF9999',  # Pink
        70: '#0099FF',  # Light Blue
        80: '#009966',  # Teal
        90: '#663399',  # Purple
        250: '#333333', # Dark Gray
    }

    def __init__(self, db_config: Dict, conn=None):
        """
        Initialize Geometry Preview Service.

        Args:
            db_config: Database configuration dict
            conn: Optional existing database connection
        """
        self.db_config = db_config
        self.conn = conn
        self.should_close = conn is None

    def generate_svg(self, entity_id: str, width: int = 400, height: int = 300,
                     background: str = '#1a1a1a', stroke_width: float = 2.0) -> str:
        """
        Generate SVG preview of entity geometry.

        Args:
            entity_id: UUID of entity
            width: SVG width in pixels
            height: SVG height in pixels
            background: Background color (hex)
            stroke_width: Line stroke width

        Returns:
            SVG string ready for rendering
        """
        if not self.conn:
            self.conn = psycopg2.connect(**self.db_config)

        try:
            cur = self.conn.cursor(cursor_factory=RealDictCursor)

            # Get entity geometry and attributes
            cur.execute("""
                SELECT
                    ST_AsText(de.geometry) as geom_wkt,
                    ST_GeometryType(de.geometry) as geom_type,
                    ST_XMin(de.geometry) as xmin,
                    ST_YMin(de.geometry) as ymin,
                    ST_XMax(de.geometry) as xmax,
                    ST_YMax(de.geometry) as ymax,
                    de.color_aci,
                    de.entity_type,
                    de.layer_name
                FROM drawing_entities de
                WHERE de.entity_id = %s
            """, (entity_id,))

            entity = cur.fetchone()

            if not entity or not entity['geom_wkt']:
                return self._create_empty_svg(width, height, background, "No geometry found")

            # Calculate viewbox with padding
            bbox_width = entity['xmax'] - entity['xmin']
            bbox_height = entity['ymax'] - entity['ymin']

            # Handle point geometries (no width/height)
            if bbox_width == 0 and bbox_height == 0:
                padding = 50  # Fixed padding for points
                viewbox_xmin = entity['xmin'] - padding
                viewbox_ymin = entity['ymin'] - padding
                viewbox_width = padding * 2
                viewbox_height = padding * 2
            else:
                padding = max(bbox_width, bbox_height) * 0.15
                viewbox_xmin = entity['xmin'] - padding
                viewbox_ymin = entity['ymin'] - padding
                viewbox_width = bbox_width + 2 * padding
                viewbox_height = bbox_height + 2 * padding

            # Get color
            color = self._get_color(entity['color_aci'])

            # Start SVG
            svg = f'''<svg width="{width}" height="{height}"
                 viewBox="{viewbox_xmin} {viewbox_ymin} {viewbox_width} {viewbox_height}"
                 xmlns="http://www.w3.org/2000/svg"
                 style="background: {background};">
                <g transform="scale(1, -1) translate(0, -{viewbox_ymin * 2 + viewbox_height})">
            '''

            # Render geometry based on type
            geom_type = entity['geom_type']

            if 'Point' in geom_type:
                svg += self._render_point(entity['geom_wkt'], color, stroke_width * 3)
            elif 'LineString' in geom_type:
                svg += self._render_linestring(entity['geom_wkt'], color, stroke_width)
            elif 'Polygon' in geom_type:
                svg += self._render_polygon(entity['geom_wkt'], color, stroke_width)
            else:
                # Fallback for unknown types
                svg += f'<text x="{viewbox_xmin + viewbox_width/2}" y="{viewbox_ymin + viewbox_height/2}" fill="{color}" font-size="{viewbox_width/10}">?</text>'

            # Add layer name label
            label_y = viewbox_ymin + viewbox_height - padding / 2
            svg += f'''
                <text x="{viewbox_xmin + padding/2}" y="{label_y}"
                      fill="#888" font-size="{viewbox_width/20}"
                      font-family="monospace" transform="scale(1, -1) translate(0, -{label_y * 2})">
                    {entity['layer_name'] or 'Unknown Layer'}
                </text>
            '''

            svg += '''
                </g>
            </svg>
            '''

            return svg

        finally:
            if self.should_close and self.conn:
                self.conn.close()

    def _render_point(self, wkt: str, color: str, radius: float = 5) -> str:
        """Render point geometry as SVG circle."""
        try:
            geom = wkt.loads(wkt)

            if isinstance(geom, Point):
                x, y = geom.x, geom.y
                return f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{color}" stroke="{color}" stroke-width="1"/>'

            elif isinstance(geom, MultiPoint):
                svg = ''
                for point in geom.geoms:
                    x, y = point.x, point.y
                    svg += f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{color}" stroke="{color}" stroke-width="1"/>'
                return svg

        except Exception:
            return ''

    def _render_linestring(self, wkt_str: str, color: str, stroke_width: float = 2) -> str:
        """Render linestring geometry as SVG path."""
        try:
            geom = wkt.loads(wkt_str)

            if isinstance(geom, LineString):
                coords = geom.coords
                if len(coords) < 2:
                    return ''

                path_data = f'M {coords[0][0]},{coords[0][1]}'
                for x, y in coords[1:]:
                    path_data += f' L {x},{y}'

                return f'<path d="{path_data}" stroke="{color}" stroke-width="{stroke_width}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'

            elif isinstance(geom, MultiLineString):
                svg = ''
                for line in geom.geoms:
                    coords = line.coords
                    if len(coords) < 2:
                        continue

                    path_data = f'M {coords[0][0]},{coords[0][1]}'
                    for x, y in coords[1:]:
                        path_data += f' L {x},{y}'

                    svg += f'<path d="{path_data}" stroke="{color}" stroke-width="{stroke_width}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
                return svg

        except Exception:
            return ''

    def _render_polygon(self, wkt_str: str, color: str, stroke_width: float = 2) -> str:
        """Render polygon geometry as SVG path with fill."""
        try:
            geom = wkt.loads(wkt_str)

            if isinstance(geom, Polygon):
                # Exterior ring
                coords = geom.exterior.coords
                if len(coords) < 3:
                    return ''

                path_data = f'M {coords[0][0]},{coords[0][1]}'
                for x, y in coords[1:]:
                    path_data += f' L {x},{y}'
                path_data += ' Z'

                # Use semi-transparent fill
                fill_color = color + '33'  # Add alpha

                svg = f'<path d="{path_data}" stroke="{color}" stroke-width="{stroke_width}" fill="{fill_color}" stroke-linejoin="round"/>'

                # Add interior rings (holes) if any
                for interior in geom.interiors:
                    coords = interior.coords
                    hole_data = f'M {coords[0][0]},{coords[0][1]}'
                    for x, y in coords[1:]:
                        hole_data += f' L {x},{y}'
                    hole_data += ' Z'

                    svg += f'<path d="{hole_data}" stroke="{color}" stroke-width="{stroke_width/2}" fill="#1a1a1a"/>'

                return svg

            elif isinstance(geom, MultiPolygon):
                svg = ''
                for poly in geom.geoms:
                    coords = poly.exterior.coords
                    if len(coords) < 3:
                        continue

                    path_data = f'M {coords[0][0]},{coords[0][1]}'
                    for x, y in coords[1:]:
                        path_data += f' L {x},{y}'
                    path_data += ' Z'

                    fill_color = color + '33'
                    svg += f'<path d="{path_data}" stroke="{color}" stroke-width="{stroke_width}" fill="{fill_color}" stroke-linejoin="round"/>'

                return svg

        except Exception:
            return ''

    def _get_color(self, aci: Optional[int]) -> str:
        """Convert AutoCAD Color Index to hex color."""
        if aci is None:
            return '#00FFFF'  # Default cyan

        # Direct lookup
        if aci in self.ACI_COLORS:
            return self.ACI_COLORS[aci]

        # Color ranges
        if 10 <= aci <= 19:
            return '#FF0000'  # Red range
        elif 20 <= aci <= 29:
            return '#FF6600'  # Orange range
        elif 30 <= aci <= 39:
            return '#FFFF00'  # Yellow range
        elif 40 <= aci <= 49:
            return '#00FF00'  # Green range
        elif 50 <= aci <= 59:
            return '#00FFFF'  # Cyan range
        elif 60 <= aci <= 69:
            return '#0000FF'  # Blue range
        elif 70 <= aci <= 79:
            return '#FF00FF'  # Magenta range
        elif 80 <= aci <= 249:
            # Grayscale range
            gray_value = int((aci - 80) / 170 * 255)
            return f'#{gray_value:02x}{gray_value:02x}{gray_value:02x}'
        else:
            return '#00FFFF'  # Default cyan

    def _create_empty_svg(self, width: int, height: int, background: str, message: str) -> str:
        """Create empty SVG with message."""
        return f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" style="background: {background};">
            <text x="{width/2}" y="{height/2}" fill="#666" font-size="14" text-anchor="middle" font-family="sans-serif">
                {message}
            </text>
        </svg>'''

    def generate_comparison_svg(self, entity_id1: str, entity_id2: str,
                               width: int = 800, height: int = 400) -> str:
        """
        Generate side-by-side comparison of two entities.

        Useful for showing similar entities during classification.

        Args:
            entity_id1: First entity UUID
            entity_id2: Second entity UUID
            width: Total SVG width
            height: SVG height

        Returns:
            SVG string with split view
        """
        svg1 = self.generate_svg(entity_id1, width=width//2, height=height)
        svg2 = self.generate_svg(entity_id2, width=width//2, height=height)

        return f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
            <g transform="translate(0, 0)">
                {svg1}
            </g>
            <g transform="translate({width//2}, 0)">
                {svg2}
            </g>
            <line x1="{width//2}" y1="0" x2="{width//2}" y2="{height}" stroke="#444" stroke-width="2"/>
        </svg>'''

    def generate_thumbnail(self, entity_id: str, size: int = 100) -> str:
        """
        Generate small thumbnail for entity lists.

        Args:
            entity_id: Entity UUID
            size: Thumbnail size (square)

        Returns:
            SVG string
        """
        return self.generate_svg(entity_id, width=size, height=size, stroke_width=1.5)
