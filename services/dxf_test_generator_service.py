"""
DXF Test Generator Service
Generates randomized test DXF files with database-driven object types and layer classifications
"""

import ezdxf
import random
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.db_utils import execute_query


class DXFTestGeneratorService:
    """Service for generating test DXF files with random entities"""

    # Coordinate system configurations
    COORDINATE_SYSTEMS = {
        'LOCAL': {
            'srid': 0,
            'x_range': (1000, 10000),
            'y_range': (1000, 10000),
            'z_range': (0, 100)
        },
        'STATE_PLANE': {
            'srid': 2226,  # California State Plane Zone 2
            'x_range': (6000000, 6100000),
            'y_range': (2000000, 2100000),
            'z_range': (0, 500)
        },
        'WGS84': {
            'srid': 4326,  # GPS coordinates
            'x_range': (-122.5, -122.0),
            'y_range': (37.5, 38.0),
            'z_range': (0, 500)
        }
    }

    def __init__(self):
        """Initialize the service"""
        self.coord_config = self.COORDINATE_SYSTEMS['LOCAL']

    def get_available_object_types(self) -> List[Dict]:
        """
        Query database for all object types with their associated information.
        Returns object types grouped by their characteristics.
        """
        query = """
        SELECT DISTINCT
            ot.type_id,
            ot.code as object_type_code,
            ot.full_name,
            ot.database_table,
            c.code as category_code,
            c.full_name as category_name,
            d.code as discipline_code,
            d.full_name as discipline_name,
            g.code as default_geometry,
            g.dxf_entity_types
        FROM object_type_codes ot
        JOIN category_codes c ON ot.category_id = c.category_id
        JOIN discipline_codes d ON c.discipline_id = d.discipline_id
        LEFT JOIN geometry_codes g ON g.code IN ('LN', 'PT', 'PG')
        WHERE ot.is_active = TRUE AND c.is_active = TRUE AND d.is_active = TRUE
        ORDER BY d.code, c.code, ot.code
        """

        results = execute_query(query)

        # Group object types by category for organization
        object_types = []
        for row in results:
            # Determine default geometry based on object type and category
            geometry_code = self._determine_geometry_type(
                row['object_type_code'],
                row['category_code'],
                row['database_table']
            )

            object_types.append({
                'type_id': row['type_id'],
                'object_type_code': row['object_type_code'],
                'full_name': row['full_name'],
                'database_table': row['database_table'],
                'category_code': row['category_code'],
                'category_name': row['category_name'],
                'discipline_code': row['discipline_code'],
                'discipline_name': row['discipline_name'],
                'default_geometry': geometry_code,
                'entity_category': self._categorize_entity(row['object_type_code'], row['category_code'])
            })

        return object_types

    def _determine_geometry_type(self, object_type: str, category: str, database_table: Optional[str]) -> str:
        """Determine the appropriate geometry type for an object"""
        # Points/Structures
        if object_type in ['MH', 'INLET', 'CB', 'VALVE', 'METER', 'HYDRANT', 'LITE', 'SHOT', 'CTRL']:
            return 'PT'

        # Lines/Pipes
        if object_type in ['STORM', 'SANIT', 'WATER', 'GAS', 'ELEC', 'COMM', 'ALIGN', 'FENCE', 'CURB']:
            return 'LN'

        # Polygons/Areas
        if object_type in ['BIOR', 'SWALE', 'POND', 'BASIN', 'PVMT', 'PLNTR', 'BLDG']:
            return 'PG'

        # Default based on category
        if category in ['UTIL']:
            return 'LN'
        elif category in ['BMP', 'PVMT', 'GRAD']:
            return 'PG'
        else:
            return 'PT'

    def _categorize_entity(self, object_type: str, category: str) -> str:
        """Categorize entity for UI grouping"""
        if category == 'UTIL':
            if object_type in ['MH', 'INLET', 'CB', 'VALVE', 'METER', 'HYDRANT']:
                return 'Utility Structures'
            else:
                return 'Utility Lines'
        elif category == 'BMP':
            return 'BMPs'
        elif category == 'TOPO':
            return 'Survey Points'
        elif category == 'PVMT':
            return 'Pavement'
        elif category == 'LITE':
            return 'Street Lights'
        elif category == 'ALIGN':
            return 'Alignments'
        else:
            return 'Other'

    def get_applicable_attributes(self, object_type_code: str) -> List[Dict]:
        """
        Get attributes that can be applied to this object type.
        For now, returns common attributes. Can be enhanced with attribute_applicability table.
        """
        query = """
        SELECT DISTINCT
            a.attribute_id,
            a.code,
            a.full_name,
            a.attribute_category,
            a.description
        FROM attribute_codes a
        WHERE a.is_active = TRUE
        ORDER BY a.attribute_category, a.code
        """

        results = execute_query(query)
        return [dict(row) for row in results] if results else []

    def get_phase_codes(self) -> List[Dict]:
        """Get all active phase codes"""
        query = """
        SELECT phase_id, code, full_name, color_rgb
        FROM phase_codes
        WHERE is_active = TRUE
        ORDER BY sort_order
        """
        results = execute_query(query)
        return [dict(row) for row in results] if results else [
            {'code': 'NEW', 'full_name': 'New Construction'},
            {'code': 'EXIST', 'full_name': 'Existing'},
            {'code': 'DEMO', 'full_name': 'Demolition'}
        ]

    def build_layer_name(self, discipline: str, category: str, object_type: str,
                        attributes: List[str], phase: str, geometry: str) -> str:
        """
        Build standard layer name: DISCIPLINE-CATEGORY-TYPE-ATTRS-PHASE-GEOMETRY
        Example: CIV-UTIL-STORM-12IN-NEW-LN
        """
        parts = [discipline, category, object_type]

        # Add attributes if provided
        if attributes:
            parts.extend(attributes)

        # Add phase and geometry
        parts.extend([phase, geometry])

        return '-'.join(parts)

    def generate_test_dxf(self, config: Dict) -> str:
        """
        Main generation function.

        Config structure:
        {
            'coordinate_system': 'LOCAL' | 'STATE_PLANE' | 'WGS84',
            'entity_counts': {'object_type_code': count, ...},
            'project_name': 'Test Project 001',
            'include_attributes': True,
            'randomize_phases': True,
            'output_dir': '/tmp/dxf_uploads' (optional)
        }

        Returns: file path to generated DXF
        """
        # Set coordinate system
        coord_system = config.get('coordinate_system', 'LOCAL')
        self.coord_config = self.COORDINATE_SYSTEMS.get(coord_system, self.COORDINATE_SYSTEMS['LOCAL'])

        # Get configuration
        entity_counts = config.get('entity_counts', {})
        project_name = config.get('project_name', 'Test_Project')
        include_attributes = config.get('include_attributes', True)
        randomize_phases = config.get('randomize_phases', True)
        output_dir = config.get('output_dir', '/tmp/dxf_uploads')

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Create DXF document
        doc = ezdxf.new('AC1027')  # AutoCAD 2013 format
        msp = doc.modelspace()

        # Get object types and phases
        object_types_list = self.get_available_object_types()
        phase_codes = self.get_phase_codes()

        # Generate entities for each object type
        layers_created = set()
        entity_stats = {}

        for obj_type in object_types_list:
            object_type_code = obj_type['object_type_code']
            count = entity_counts.get(object_type_code, 0)

            if count <= 0:
                continue

            entity_stats[object_type_code] = 0

            for i in range(count):
                # Select phase
                if randomize_phases:
                    phase = random.choice(phase_codes)['code']
                else:
                    phase = 'NEW'

                # Select attributes
                attributes = []
                if include_attributes:
                    applicable_attrs = self._get_random_attributes(object_type_code)
                    attributes = applicable_attrs

                # Build layer name
                layer_name = self.build_layer_name(
                    obj_type['discipline_code'],
                    obj_type['category_code'],
                    object_type_code,
                    attributes,
                    phase,
                    obj_type['default_geometry']
                )

                # Create layer if not exists
                if layer_name not in layers_created:
                    doc.layers.add(layer_name)
                    layers_created.add(layer_name)

                # Generate entity based on geometry type
                geometry_type = obj_type['default_geometry']

                if geometry_type == 'LN':
                    self._create_line_entity(msp, layer_name, object_type_code)
                elif geometry_type == 'PT':
                    self._create_point_entity(msp, layer_name, object_type_code)
                elif geometry_type == 'PG':
                    self._create_polygon_entity(msp, layer_name, object_type_code)

                entity_stats[object_type_code] += 1

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_project_name = project_name.replace(' ', '_').replace('/', '_')
        filename = f"{safe_project_name}_{coord_system}_{timestamp}.dxf"
        file_path = os.path.join(output_dir, filename)

        # Save DXF file
        doc.saveas(file_path)

        return file_path

    def _get_random_attributes(self, object_type_code: str) -> List[str]:
        """Get random attributes appropriate for the object type"""
        # Common size attributes for pipes
        if object_type_code in ['STORM', 'SANIT', 'WATER']:
            sizes = ['8IN', '12IN', '18IN', '24IN']
            return [random.choice(sizes)]

        # Material attributes for structures
        if object_type_code in ['MH', 'INLET', 'CB']:
            materials = ['CONC', 'PVC', 'HDPE']
            return [random.choice(materials)] if random.random() > 0.5 else []

        # Function attributes for BMPs
        if object_type_code in ['BIOR', 'SWALE', 'POND', 'BASIN']:
            functions = ['STORAGE', 'TREATMENT', 'INFILTRATION']
            return [random.choice(functions)] if random.random() > 0.5 else []

        return []

    def _create_line_entity(self, msp, layer_name: str, object_type: str):
        """Create a line or polyline entity with 3D coordinates"""
        # Generate random coordinates
        num_vertices = random.randint(2, 5)
        points = []

        for i in range(num_vertices):
            x = random.uniform(*self.coord_config['x_range'])
            y = random.uniform(*self.coord_config['y_range'])
            z = random.uniform(*self.coord_config['z_range'])
            points.append((x, y, z))

        # Create polyline with elevation
        if num_vertices == 2:
            # Simple line
            msp.add_line(points[0], points[1], dxfattribs={'layer': layer_name})
        else:
            # Create 3D polyline
            msp.add_polyline3d(points, dxfattribs={'layer': layer_name})

    def _create_point_entity(self, msp, layer_name: str, object_type: str):
        """Create a point entity with 3D coordinates"""
        x = random.uniform(*self.coord_config['x_range'])
        y = random.uniform(*self.coord_config['y_range'])
        z = random.uniform(*self.coord_config['z_range'])

        # Create point
        msp.add_point((x, y, z), dxfattribs={'layer': layer_name})

        # Optionally add a circle for visibility
        if random.random() > 0.5:
            radius = random.uniform(0.5, 2.0)
            msp.add_circle((x, y, z), radius, dxfattribs={'layer': layer_name})

    def _create_polygon_entity(self, msp, layer_name: str, object_type: str):
        """Create a closed polyline (polygon) with elevation"""
        # Generate random polygon with 4-8 vertices
        num_vertices = random.randint(4, 8)

        # Generate center point
        center_x = random.uniform(*self.coord_config['x_range'])
        center_y = random.uniform(*self.coord_config['y_range'])
        z = random.uniform(*self.coord_config['z_range'])

        # Generate radius
        if self.coord_config['srid'] == 0:  # LOCAL
            radius = random.uniform(5, 20)
        elif self.coord_config['srid'] == 2226:  # STATE_PLANE
            radius = random.uniform(10, 50)
        else:  # WGS84
            radius = random.uniform(0.0001, 0.0005)

        # Generate vertices in a roughly circular pattern
        points = []
        for i in range(num_vertices):
            angle = (2 * 3.14159 * i) / num_vertices
            # Add some randomness to make it irregular
            r = radius * random.uniform(0.8, 1.2)
            x = center_x + r * random.uniform(0.8, 1.2) * (1 if i % 2 == 0 else -1) * abs(round(random.random() * 10) / 10)
            y = center_y + r * random.uniform(0.8, 1.2) * (1 if i % 2 == 1 else -1) * abs(round(random.random() * 10) / 10)
            points.append((x, y))

        # Close the polygon by adding first point at end
        points.append(points[0])

        # Create closed polyline with elevation
        lwpolyline = msp.add_lwpolyline(points, dxfattribs={
            'layer': layer_name,
            'elevation': z,
            'closed': True
        })

    def get_stats_summary(self, file_path: str) -> Dict:
        """Get statistics about a generated DXF file"""
        try:
            doc = ezdxf.readfile(file_path)
            msp = doc.modelspace()

            stats = {
                'total_entities': len(list(msp)),
                'layers': len(doc.layers),
                'layer_names': [layer.dxf.name for layer in doc.layers if layer.dxf.name != '0'],
                'entity_types': {}
            }

            # Count entity types
            for entity in msp:
                entity_type = entity.dxftype()
                stats['entity_types'][entity_type] = stats['entity_types'].get(entity_type, 0) + 1

            return stats
        except Exception as e:
            return {'error': str(e)}
