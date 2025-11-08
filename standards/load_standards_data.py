"""
Load CAD Standards Vocabulary into Database
Populates the standards tables with the revolutionary CAD naming system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.db_utils import execute_query, execute_many

def load_discipline_codes():
    """Load discipline codes"""
    disciplines = [
        ('CIV', 'Civil', 'Civil engineering infrastructure', 1),
        ('SITE', 'Site', 'Site development, grading, earthwork', 2),
        ('SURV', 'Survey', 'Survey data, control points, topography', 3),
        ('LAND', 'Landscape', 'Planting, irrigation, landscape features', 4),
        ('ARCH', 'Architectural', 'Buildings, structures, architecture', 5),
        ('UTIL', 'Utility', 'General utilities (when not civil-led)', 6),
        ('ANNO', 'Annotation', 'Notes, labels, dimensions, callouts', 7),
        ('XREF', 'External Reference', 'Referenced drawings', 8),
    ]
    
    query = """
        INSERT INTO discipline_codes (code, full_name, description, sort_order)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (code) DO UPDATE SET
            full_name = EXCLUDED.full_name,
            description = EXCLUDED.description,
            sort_order = EXCLUDED.sort_order,
            updated_at = CURRENT_TIMESTAMP
        RETURNING discipline_id, code
    """
    
    result = execute_many(query, disciplines)
    print(f"✓ Loaded {len(disciplines)} discipline codes")
    return result

def load_category_codes():
    """Load category codes"""
    categories = [
        # CIV categories
        ('CIV', 'UTIL', 'Utility', 'All underground utilities', 1),
        ('CIV', 'ROAD', 'Road', 'Streets, pavements, curbs', 2),
        ('CIV', 'GRAD', 'Grading', 'Earthwork, slopes, pads', 3),
        ('CIV', 'STOR', 'Stormwater', 'Storm drainage, BMP, water quality', 4),
        ('CIV', 'POND', 'Pond', 'Detention/retention ponds', 5),
        ('CIV', 'TANK', 'Tank', 'Water storage tanks', 6),
        ('CIV', 'ADA', 'ADA', 'Accessibility features, ramps, paths', 7),
        ('CIV', 'EROS', 'Erosion Control', 'SWPPP, erosion control measures', 8),
        
        # SITE categories
        ('SITE', 'GRAD', 'Grading', 'Site grading, mass grading', 1),
        ('SITE', 'DEMO', 'Demolition', 'Demolition work', 2),
        ('SITE', 'FENCE', 'Fencing', 'Fences, gates, barriers', 3),
        ('SITE', 'PAVE', 'Pavement', 'Parking lots, driveways', 4),
        ('SITE', 'WALL', 'Retaining Wall', 'Retaining walls, seat walls', 5),
        ('SITE', 'SIGN', 'Signage', 'Site signage', 6),
        
        # SURV categories
        ('SURV', 'CTRL', 'Control', 'Control points, benchmarks', 1),
        ('SURV', 'TOPO', 'Topographic', 'Topo shots, ground shots', 2),
        ('SURV', 'BLDG', 'Building', 'Building corners, features', 3),
        ('SURV', 'UTIL', 'Utility', 'Located utilities', 4),
        ('SURV', 'TREE', 'Tree', 'Tree locations, sizes', 5),
        ('SURV', 'BNDY', 'Boundary', 'Property boundaries', 6),
        
        # LAND categories
        ('LAND', 'TREE', 'Trees', 'Trees, palms', 1),
        ('LAND', 'SHRU', 'Shrubs', 'Shrubs, plants', 2),
        ('LAND', 'TURF', 'Turf', 'Lawn, groundcover', 3),
        ('LAND', 'IRIG', 'Irrigation', 'Irrigation systems', 4),
        ('LAND', 'HARD', 'Hardscape', 'Paving, walkways, plazas', 5),
    ]
    
    query = """
        INSERT INTO category_codes (discipline_id, code, full_name, description, sort_order)
        SELECT d.discipline_id, %s, %s, %s, %s
        FROM discipline_codes d
        WHERE d.code = %s
        ON CONFLICT (discipline_id, code) DO UPDATE SET
            full_name = EXCLUDED.full_name,
            description = EXCLUDED.description,
            sort_order = EXCLUDED.sort_order,
            updated_at = CURRENT_TIMESTAMP
        RETURNING category_id, code
    """
    
    category_data = [(cat[1], cat[2], cat[3], cat[4], cat[0]) for cat in categories]
    result = execute_many(query, category_data)
    print(f"✓ Loaded {len(categories)} category codes")
    return result

def load_object_type_codes():
    """Load object type codes"""
    object_types = [
        # CIV-UTIL types
        ('CIV', 'UTIL', 'STORM', 'Storm Drain', 'Storm drain pipes and structures', 'utility_lines', 1),
        ('CIV', 'UTIL', 'SANIT', 'Sanitary Sewer', 'Sanitary sewer pipes and structures', 'utility_lines', 2),
        ('CIV', 'UTIL', 'WATER', 'Water', 'Potable water pipes', 'utility_lines', 3),
        ('CIV', 'UTIL', 'RECYC', 'Recycled Water', 'Recycled/reclaimed water pipes', 'utility_lines', 4),
        ('CIV', 'UTIL', 'GAS', 'Gas', 'Natural gas pipes', 'utility_lines', 5),
        ('CIV', 'UTIL', 'ELEC', 'Electric', 'Electric conduits and cables', 'utility_lines', 6),
        ('CIV', 'UTIL', 'TELE', 'Telecom', 'Telephone conduits', 'utility_lines', 7),
        ('CIV', 'UTIL', 'FIBER', 'Fiber Optic', 'Fiber optic conduits', 'utility_lines', 8),
        ('CIV', 'UTIL', 'MH', 'Manhole', 'Manholes', 'utility_structures', 9),
        ('CIV', 'UTIL', 'INLET', 'Inlet', 'Storm drain inlets', 'utility_structures', 10),
        ('CIV', 'UTIL', 'CB', 'Catch Basin', 'Catch basins', 'utility_structures', 11),
        ('CIV', 'UTIL', 'CLNOUT', 'Cleanout', 'Cleanouts', 'utility_structures', 12),
        ('CIV', 'UTIL', 'VALVE', 'Valve', 'Valves', 'utility_structures', 13),
        ('CIV', 'UTIL', 'METER', 'Meter', 'Meters', 'utility_structures', 14),
        ('CIV', 'UTIL', 'HYDRA', 'Hydrant', 'Fire hydrants', 'utility_structures', 15),
        ('CIV', 'UTIL', 'PUMP', 'Pump Station', 'Pump stations', 'utility_structures', 16),
        
        # CIV-ROAD types
        ('CIV', 'ROAD', 'CL', 'Centerline', 'Road centerlines', 'horizontal_alignments', 1),
        ('CIV', 'ROAD', 'CURB', 'Curb', 'Curbs', 'drawing_entities', 2),
        ('CIV', 'ROAD', 'GUTR', 'Gutter', 'Gutters', 'drawing_entities', 3),
        ('CIV', 'ROAD', 'SDWK', 'Sidewalk', 'Sidewalks', 'drawing_entities', 4),
        ('CIV', 'ROAD', 'PVMT', 'Pavement', 'Pavement areas', 'drawing_entities', 5),
        ('CIV', 'ROAD', 'STRP', 'Striping', 'Pavement striping', 'drawing_entities', 6),
        ('CIV', 'ROAD', 'RAMP', 'Ramp', 'Ramps', 'drawing_entities', 7),
        
        # CIV-STOR types
        ('CIV', 'STOR', 'BIORT', 'Bioretention', 'Bioretention areas', 'drawing_entities', 1),
        ('CIV', 'STOR', 'SWALE', 'Swale', 'Vegetated swales', 'drawing_entities', 2),
        ('CIV', 'STOR', 'BASIN', 'Detention Basin', 'Detention/retention basins', 'drawing_entities', 3),
        ('CIV', 'STOR', 'FILTR', 'Filter', 'Filter systems', 'utility_structures', 4),
        ('CIV', 'STOR', 'VNDR', 'Vendor Device', 'Proprietary treatment devices', 'utility_structures', 5),
        ('CIV', 'STOR', 'PERVP', 'Pervious Pavement', 'Pervious pavement areas', 'drawing_entities', 6),
        
        # CIV-ADA types
        ('CIV', 'ADA', 'RAMP', 'Accessible Ramp', 'ADA compliant ramps', 'drawing_entities', 1),
        ('CIV', 'ADA', 'PATH', 'Accessible Path', 'ADA compliant paths', 'drawing_entities', 2),
        ('CIV', 'ADA', 'PARK', 'Accessible Parking', 'Accessible parking spaces', 'drawing_entities', 3),
        ('CIV', 'ADA', 'DCRB', 'Detectable Curb Ramp', 'Detectable warning curb ramps', 'drawing_entities', 4),
        
        # SITE-GRAD types
        ('SITE', 'GRAD', 'CNTR', 'Contour', 'Contour lines', 'drawing_entities', 1),
        ('SITE', 'GRAD', 'SPOT', 'Spot Elevation', 'Spot elevations', 'drawing_text', 2),
        ('SITE', 'GRAD', 'SLOPE', 'Slope', 'Slope indicators', 'drawing_entities', 3),
        ('SITE', 'GRAD', 'PAD', 'Building Pad', 'Building pads', 'drawing_entities', 4),
        ('SITE', 'GRAD', 'SWALE', 'Swale', 'Drainage swales', 'drawing_entities', 5),
        ('SITE', 'GRAD', 'BERM', 'Berm', 'Berms', 'drawing_entities', 6),
        
        # SURV types
        ('SURV', 'CTRL', 'MONUMENT', 'Monument', 'Control monuments', 'survey_points', 1),
        ('SURV', 'CTRL', 'BENCH', 'Benchmark', 'Benchmarks', 'survey_points', 2),
        ('SURV', 'TOPO', 'SHOT', 'Topo Shot', 'Topographic shots', 'survey_points', 3),
        ('SURV', 'TREE', 'OAK', 'Oak Tree', 'Oak trees', 'site_trees', 4),
        ('SURV', 'TREE', 'PINE', 'Pine Tree', 'Pine trees', 'site_trees', 5),
        
        # LAND types
        ('LAND', 'TREE', 'TREE', 'Tree', 'Generic tree', 'site_trees', 1),
        ('LAND', 'IRIG', 'MAIN', 'Irrigation Main', 'Irrigation mainline', 'drawing_entities', 2),
        ('LAND', 'IRIG', 'LATERAL', 'Irrigation Lateral', 'Irrigation laterals', 'drawing_entities', 3),
    ]
    
    query = """
        INSERT INTO object_type_codes (category_id, code, full_name, description, database_table, sort_order)
        SELECT c.category_id, %s, %s, %s, %s, %s
        FROM category_codes c
        JOIN discipline_codes d ON c.discipline_id = d.discipline_id
        WHERE d.code = %s AND c.code = %s
        ON CONFLICT (category_id, code) DO UPDATE SET
            full_name = EXCLUDED.full_name,
            description = EXCLUDED.description,
            database_table = EXCLUDED.database_table,
            sort_order = EXCLUDED.sort_order,
            updated_at = CURRENT_TIMESTAMP
        RETURNING type_id, code
    """
    
    type_data = [(t[2], t[3], t[4], t[5], t[6], t[0], t[1]) for t in object_types]
    result = execute_many(query, type_data)
    print(f"✓ Loaded {len(object_types)} object type codes")
    return result

def load_phase_codes():
    """Load phase codes"""
    phases = [
        ('EXIST', 'Existing', 'Existing features to remain', '#808080', 1),
        ('DEMO', 'Demolish', 'To be demolished/removed', '#FF0000', 2),
        ('NEW', 'New', 'New construction', '#0000FF', 3),
        ('TEMP', 'Temporary', 'Temporary work', '#FFA500', 4),
        ('FUTR', 'Future', 'Future phase', '#800080', 5),
        ('PROP', 'Proposed', 'Proposed (generic)', '#00FF00', 6),
        ('PH1', 'Phase 1', 'Construction phase 1', '#00FFFF', 7),
        ('PH2', 'Phase 2', 'Construction phase 2', '#FF00FF', 8),
        ('PH3', 'Phase 3', 'Construction phase 3', '#FFFF00', 9),
    ]
    
    query = """
        INSERT INTO phase_codes (code, full_name, description, color_rgb, sort_order)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (code) DO UPDATE SET
            full_name = EXCLUDED.full_name,
            description = EXCLUDED.description,
            color_rgb = EXCLUDED.color_rgb,
            sort_order = EXCLUDED.sort_order,
            updated_at = CURRENT_TIMESTAMP
        RETURNING phase_id, code
    """
    
    result = execute_many(query, phases)
    print(f"✓ Loaded {len(phases)} phase codes")
    return result

def load_geometry_codes():
    """Load geometry codes"""
    geometries = [
        ('LN', 'Line/Polyline', 'Line and polyline entities', ['LINE', 'LWPOLYLINE', 'POLYLINE'], 1),
        ('PT', 'Point', 'Point entities', ['POINT'], 2),
        ('PG', 'Polygon/Area', 'Closed polylines and hatches', ['LWPOLYLINE', 'HATCH'], 3),
        ('TX', 'Text/Label', 'Text entities', ['TEXT', 'MTEXT'], 4),
        ('3D', '3D Object', '3D entities', ['3DFACE', 'SOLID', 'MESH'], 5),
        ('BK', 'Block Reference', 'Block inserts', ['INSERT'], 6),
        ('HT', 'Hatch Pattern', 'Hatch patterns', ['HATCH'], 7),
        ('DIM', 'Dimension', 'Dimension entities', ['DIMENSION'], 8),
    ]
    
    query = """
        INSERT INTO geometry_codes (code, full_name, description, dxf_entity_types, sort_order)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (code) DO UPDATE SET
            full_name = EXCLUDED.full_name,
            description = EXCLUDED.description,
            dxf_entity_types = EXCLUDED.dxf_entity_types,
            sort_order = EXCLUDED.sort_order,
            updated_at = CURRENT_TIMESTAMP
        RETURNING geometry_id, code
    """
    
    result = execute_many(query, geometries)
    print(f"✓ Loaded {len(geometries)} geometry codes")
    return result

def load_attribute_codes():
    """Load attribute codes"""
    attributes = [
        # Size attributes
        ('12IN', '12 inches', 'size', 'Diameter: 12 inches', r'\d+IN'),
        ('8IN', '8 inches', 'size', 'Diameter: 8 inches', r'\d+IN'),
        ('6IN', '6 inches', 'size', 'Diameter: 6 inches', r'\d+IN'),
        ('4FT', '4 feet', 'size', 'Width: 4 feet', r'\d+FT'),
        ('5FT', '5 feet', 'size', 'Width: 5 feet', r'\d+FT'),
        ('500CF', '500 cubic feet', 'volume', 'Volume: 500 cubic feet', r'\d+CF'),
        ('2AC', '2 acres', 'area', 'Area: 2 acres', r'\d+AC'),
        
        # Material attributes
        ('PVC', 'PVC', 'material', 'Material: PVC', None),
        ('HDPE', 'HDPE', 'material', 'Material: HDPE', None),
        ('RCP', 'Reinforced Concrete Pipe', 'material', 'Material: RCP', None),
        ('DI', 'Ductile Iron', 'material', 'Material: Ductile Iron', None),
        ('CONC', 'Concrete', 'material', 'Material: Concrete', None),
        ('AC', 'Asphalt Concrete', 'material', 'Material: Asphalt Concrete', None),
        
        # Type attributes
        ('STD', 'Standard', 'type', 'Standard type', None),
        ('CUST', 'Custom', 'type', 'Custom type', None),
        ('TYP', 'Typical', 'type', 'Typical configuration', None),
        
        # Slope/grade attributes
        ('2PCT', '2 percent', 'slope', 'Slope: 2%', r'\d+PCT'),
        ('8PCT', '8 percent', 'slope', 'Slope: 8%', r'\d+PCT'),
        ('SLP2:1', 'Slope 2:1', 'slope', 'Slope ratio: 2:1', r'SLP\d+:\d+'),
    ]
    
    query = """
        INSERT INTO attribute_codes (code, full_name, attribute_category, description, pattern)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (code) DO UPDATE SET
            full_name = EXCLUDED.full_name,
            attribute_category = EXCLUDED.attribute_category,
            description = EXCLUDED.description,
            pattern = EXCLUDED.pattern,
            updated_at = CURRENT_TIMESTAMP
        RETURNING attribute_id, code
    """
    
    result = execute_many(query, attributes)
    print(f"✓ Loaded {len(attributes)} attribute codes")
    return result

def main():
    """Load all standards data"""
    print("\n" + "="*60)
    print("Loading CAD Standards Vocabulary")
    print("="*60 + "\n")
    
    try:
        load_discipline_codes()
        load_category_codes()
        load_object_type_codes()
        load_phase_codes()
        load_geometry_codes()
        load_attribute_codes()
        
        print("\n" + "="*60)
        print("✓ All standards data loaded successfully!")
        print("="*60 + "\n")
        
        # Show summary
        summary_query = """
            SELECT 
                (SELECT COUNT(*) FROM discipline_codes) as disciplines,
                (SELECT COUNT(*) FROM category_codes) as categories,
                (SELECT COUNT(*) FROM object_type_codes) as object_types,
                (SELECT COUNT(*) FROM phase_codes) as phases,
                (SELECT COUNT(*) FROM geometry_codes) as geometries,
                (SELECT COUNT(*) FROM attribute_codes) as attributes
        """
        summary = execute_query(summary_query)
        
        if summary:
            s = summary[0]
            print("Summary:")
            print(f"  Disciplines:   {s['disciplines']}")
            print(f"  Categories:    {s['categories']}")
            print(f"  Object Types:  {s['object_types']}")
            print(f"  Phases:        {s['phases']}")
            print(f"  Geometries:    {s['geometries']}")
            print(f"  Attributes:    {s['attributes']}")
            print()
        
    except Exception as e:
        print(f"\n✗ Error loading standards: {e}")
        raise

if __name__ == '__main__':
    main()
