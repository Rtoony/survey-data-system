"""
Test data fixtures and factories for comprehensive testing.

This module provides pre-defined test data for various entities:
- DXF entities with different geometries
- Projects with various configurations
- Layers with different properties
- Survey data
- Standards and classifications
"""

import uuid
from datetime import datetime
from decimal import Decimal


# ============================================================================
# Sample DXF Entities
# ============================================================================

SAMPLE_DXF_ENTITIES = {
    "line": {
        "entity_type": "LINE",
        "geometry": "LINESTRING(0 0 0, 100 100 0)",
        "entity_data": {
            "start_point": [0.0, 0.0, 0.0],
            "end_point": [100.0, 100.0, 0.0],
            "color": "7",
            "linetype": "Continuous"
        }
    },
    "circle": {
        "entity_type": "CIRCLE",
        "geometry": "POINT(50 50 0)",
        "entity_data": {
            "center": [50.0, 50.0, 0.0],
            "radius": 25.0,
            "color": "3",
        }
    },
    "arc": {
        "entity_type": "ARC",
        "geometry": "LINESTRING(0 0 0, 50 50 0, 100 0 0)",
        "entity_data": {
            "center": [50.0, 0.0, 0.0],
            "radius": 50.0,
            "start_angle": 0.0,
            "end_angle": 180.0,
        }
    },
    "polyline": {
        "entity_type": "LWPOLYLINE",
        "geometry": "LINESTRING(0 0 0, 50 0 0, 50 50 0, 0 50 0, 0 0 0)",
        "entity_data": {
            "vertices": [[0, 0], [50, 0], [50, 50], [0, 50], [0, 0]],
            "closed": True,
        }
    },
    "text": {
        "entity_type": "TEXT",
        "geometry": "POINT(10 10 0)",
        "entity_data": {
            "text": "Sample Text",
            "height": 5.0,
            "rotation": 0.0,
            "insert_point": [10.0, 10.0, 0.0],
        }
    },
    "mtext": {
        "entity_type": "MTEXT",
        "geometry": "POINT(20 20 0)",
        "entity_data": {
            "text": "Sample Multiline\\PText Content",
            "char_height": 2.5,
            "width": 100.0,
            "insert": [20.0, 20.0, 0.0],
        }
    },
    "point": {
        "entity_type": "POINT",
        "geometry": "POINT(100 200 50)",
        "entity_data": {
            "location": [100.0, 200.0, 50.0],
        }
    },
}


# ============================================================================
# Sample Projects
# ============================================================================

SAMPLE_PROJECTS = {
    "basic": {
        "project_name": "Basic Test Project",
        "client_name": "Test Client",
        "project_number": "TEST-001",
        "description": "Basic project for unit testing",
        "quality_score": 0.5,
    },
    "survey": {
        "project_name": "Survey Project",
        "client_name": "Survey Corp",
        "project_number": "SURVEY-001",
        "description": "Project with survey data",
        "quality_score": 0.8,
    },
    "civil": {
        "project_name": "Civil Engineering Project",
        "client_name": "Engineering Inc",
        "project_number": "CIVIL-001",
        "description": "Civil infrastructure project",
        "quality_score": 0.9,
    },
    "complex": {
        "project_name": "Complex Multi-Phase Project",
        "client_name": "Large Client Corp",
        "project_number": "COMPLEX-001",
        "description": "Complex project with multiple phases and data types",
        "quality_score": 0.7,
    },
}


# ============================================================================
# Sample Layers (CAD Standards)
# ============================================================================

SAMPLE_LAYERS = {
    "walls": {
        "layer_name": "C-WALL",
        "color": "7",
        "linetype": "Continuous",
        "description": "Walls and partitions",
    },
    "annotation": {
        "layer_name": "C-ANNO",
        "color": "3",
        "linetype": "Continuous",
        "description": "Annotations and labels",
    },
    "property_line": {
        "layer_name": "C-PROP",
        "color": "1",
        "linetype": "PHANTOM",
        "description": "Property boundaries",
    },
    "utility_water": {
        "layer_name": "U-WATR",
        "color": "5",
        "linetype": "Continuous",
        "description": "Water lines",
    },
    "utility_sewer": {
        "layer_name": "U-SSWR",
        "color": "6",
        "linetype": "Continuous",
        "description": "Sanitary sewer",
    },
    "survey_points": {
        "layer_name": "V-NODE",
        "color": "2",
        "linetype": "Continuous",
        "description": "Survey control points",
    },
}


# ============================================================================
# Sample Survey Data
# ============================================================================

SAMPLE_SURVEY_POINTS = [
    {
        "point_number": "1",
        "northing": Decimal("1000.000"),
        "easting": Decimal("2000.000"),
        "elevation": Decimal("100.000"),
        "description": "Control Point",
        "code": "CTRL",
    },
    {
        "point_number": "2",
        "northing": Decimal("1050.000"),
        "easting": Decimal("2050.000"),
        "elevation": Decimal("102.500"),
        "description": "Property Corner",
        "code": "PC",
    },
    {
        "point_number": "3",
        "northing": Decimal("1000.000"),
        "easting": Decimal("2100.000"),
        "elevation": Decimal("98.750"),
        "description": "Utility Marker",
        "code": "UM",
    },
]


# ============================================================================
# Sample Standards Data
# ============================================================================

SAMPLE_STANDARDS = {
    "layer_standard": {
        "standard_name": "NCS 6.0",
        "category": "layer_naming",
        "content": {
            "disciplines": ["C", "V", "U"],
            "major_groups": ["WALL", "ANNO", "NODE"],
        }
    },
    "color_standard": {
        "standard_name": "AIA CAD Layer Guidelines",
        "category": "colors",
        "content": {
            "bylayer": True,
            "standard_colors": [1, 2, 3, 4, 5, 6, 7],
        }
    },
}


# ============================================================================
# Sample Classification Data
# ============================================================================

SAMPLE_CLASSIFICATIONS = {
    "high_confidence": {
        "entity_type": "LINE",
        "layer_name": "C-WALL",
        "classification": "wall",
        "confidence_score": 0.95,
        "reasoning": "Standard wall layer naming convention",
    },
    "medium_confidence": {
        "entity_type": "CIRCLE",
        "layer_name": "U-WATR-VALVE",
        "classification": "valve",
        "confidence_score": 0.75,
        "reasoning": "Water valve based on layer and geometry",
    },
    "low_confidence": {
        "entity_type": "LWPOLYLINE",
        "layer_name": "MISC",
        "classification": "unknown",
        "confidence_score": 0.35,
        "reasoning": "Non-standard layer name",
    },
}


# ============================================================================
# Sample GIS Snapshot Data
# ============================================================================

SAMPLE_GIS_FEATURES = [
    {
        "feature_type": "parcel",
        "geometry": "POLYGON((0 0, 100 0, 100 100, 0 100, 0 0))",
        "properties": {
            "parcel_id": "12345",
            "owner": "John Doe",
            "area_sqft": 10000,
        }
    },
    {
        "feature_type": "road_centerline",
        "geometry": "LINESTRING(0 50, 200 50)",
        "properties": {
            "road_name": "Main Street",
            "width": 30,
            "surface_type": "asphalt",
        }
    },
]


# ============================================================================
# Sample Relationship Data
# ============================================================================

SAMPLE_RELATIONSHIPS = {
    "pipe_to_structure": {
        "relationship_type": "connects_to",
        "source_type": "pipe",
        "target_type": "structure",
        "properties": {
            "connection_type": "inlet",
            "flow_direction": "into",
        }
    },
    "survey_to_drawing": {
        "relationship_type": "derived_from",
        "source_type": "drawing_entity",
        "target_type": "survey_point",
        "properties": {
            "transformation": "direct",
        }
    },
}


# ============================================================================
# Test Data Generators
# ============================================================================

def generate_uuid():
    """Generate a random UUID for testing."""
    return str(uuid.uuid4())


def generate_project_number():
    """Generate a unique test project number."""
    return f"TEST-{uuid.uuid4().hex[:6].upper()}"


def generate_layer_name(discipline="C", major="TEST"):
    """Generate a standard layer name."""
    return f"{discipline}-{major}-{uuid.uuid4().hex[:4].upper()}"


def generate_coordinates(count=10, x_range=(0, 1000), y_range=(0, 1000), z_range=(0, 100)):
    """Generate random coordinates for testing."""
    import random
    coordinates = []
    for _ in range(count):
        x = random.uniform(*x_range)
        y = random.uniform(*y_range)
        z = random.uniform(*z_range)
        coordinates.append((x, y, z))
    return coordinates


def generate_linestring_wkt(points):
    """Generate a LINESTRING WKT from coordinate points."""
    coords = " ".join([f"{x} {y} {z}" for x, y, z in points])
    return f"LINESTRING({coords})"


def generate_polygon_wkt(points):
    """Generate a POLYGON WKT from coordinate points."""
    # Ensure the polygon is closed
    if points[0] != points[-1]:
        points.append(points[0])
    coords = ", ".join([f"{x} {y} {z}" for x, y, z in points])
    return f"POLYGON(({coords}))"


# ============================================================================
# Error Scenarios for Testing
# ============================================================================

ERROR_SCENARIOS = {
    "missing_required_field": {
        "description": "Entity missing required field",
        "data": {
            "entity_type": "LINE",
            # Missing geometry
            "entity_data": {}
        },
        "expected_error": "Missing required field: geometry"
    },
    "invalid_geometry": {
        "description": "Invalid WKT geometry",
        "data": {
            "entity_type": "LINE",
            "geometry": "INVALID_WKT(0 0, 100 100)",
            "entity_data": {}
        },
        "expected_error": "Invalid geometry"
    },
    "invalid_uuid": {
        "description": "Invalid UUID format",
        "data": {
            "project_id": "not-a-uuid",
        },
        "expected_error": "Invalid UUID"
    },
    "foreign_key_violation": {
        "description": "Reference to non-existent record",
        "data": {
            "layer_id": "00000000-0000-0000-0000-000000000000",
        },
        "expected_error": "Foreign key constraint violation"
    },
}
