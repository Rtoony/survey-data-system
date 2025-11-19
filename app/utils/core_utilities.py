"""
Core Utility Functions for ACAD-GIS
Extracted from app.py during Phase 13 refactoring

This module contains reusable utility functions for:
- Active project session management
- Coordinate system transformations
- Test data configuration
- Database configuration parsing
"""
from typing import Dict, Optional, Any
from flask import session
from pyproj import Transformer
import os


def get_active_project_id() -> Optional[str]:
    """
    Get the current active project ID from session.
    Returns None if no project is active.

    Returns:
        Optional[str]: The active project ID or None
    """
    return session.get('active_project_id')


def state_plane_to_wgs84(x_feet: float, y_feet: float) -> Dict[str, float]:
    """
    Convert California State Plane Zone 2 (EPSG:2226) coordinates
    to WGS84 lat/lng (EPSG:4326) for web map display.

    Args:
        x_feet: X coordinate in US Survey Feet
        y_feet: Y coordinate in US Survey Feet

    Returns:
        dict: {'lat': latitude, 'lng': longitude}
    """
    transformer = Transformer.from_crs(
        "EPSG:2226",  # CA State Plane Zone 2 (US Survey Feet)
        "EPSG:4326",  # WGS84 (lat/lng)
        always_xy=True
    )
    lng, lat = transformer.transform(x_feet, y_feet)
    return {'lat': lat, 'lng': lng}


def get_test_coordinates_config() -> Dict[str, float]:
    """
    Returns standard test area configuration for all test data generation.
    All specialized tools should use these same coordinates.

    Returns:
        dict: Configuration with center_x, center_y, spacing, area_size, srid
    """
    return {
        'center_x': 6010000.0,  # State Plane feet
        'center_y': 2110000.0,  # State Plane feet
        'spacing': 150.0,       # feet between entities
        'area_size': 5000.0,    # total area size
        'srid': 2226            # EPSG:2226
    }


def get_batch_import_db_config() -> Dict[str, Any]:
    """
    Parse DATABASE_URL environment variable and return database connection config.
    Falls back to individual DB_* environment variables if DATABASE_URL not set.

    Returns:
        dict: Database configuration with host, database, user, password, port
    """
    database_url = os.getenv('DATABASE_URL')

    if database_url:
        # Parse DATABASE_URL format: postgresql://user:password@host:port/database
        # Remove 'postgresql://' prefix
        url_without_prefix = database_url.replace('postgresql://', '')

        # Split credentials and location
        credentials, location = url_without_prefix.split('@')
        user, password = credentials.split(':')

        # Split location into host/port and database
        host_port, database = location.split('/')

        if ':' in host_port:
            host, port = host_port.split(':')
        else:
            host = host_port
            port = '5432'

        return {
            'host': host,
            'database': database,
            'user': user,
            'password': password,
            'port': int(port)
        }
    else:
        # Fallback to individual environment variables
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'acad_gis'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'port': int(os.getenv('DB_PORT', '5432'))
        }
