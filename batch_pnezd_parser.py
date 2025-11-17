"""
Batch PNEZD Parser - Parse survey point files in PNEZD format
Point Number, Northing, Easting, Elevation, Description

Enhanced with dynamic coordinate system support.
"""

import re
import os
import sys
from typing import List, Dict, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

# Import coordinate system service for dynamic CRS support
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from services.coordinate_system_service import CoordinateSystemService


class PNEZDParser:
    """Parse PNEZD format survey point files with dynamic coordinate system support"""

    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.crs_service = CoordinateSystemService(db_config)
    
    def parse_file(self, file_content: str, source_filename: str) -> Dict:
        """
        Parse PNEZD text file content
        
        Returns:
            Dict with 'points' list and 'errors' list
        """
        points = []
        errors = []
        line_number = 0
        
        lines = file_content.strip().split('\n')
        
        for line in lines:
            line_number += 1
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Skip comment lines (if they start with #, //, or ;)
            if line.startswith('#') or line.startswith('//') or line.startswith(';'):
                continue
            
            # Parse comma-separated values
            parts = [p.strip() for p in line.split(',')]
            
            # Validate we have at least 5 fields (P, N, E, Z, D)
            if len(parts) < 5:
                errors.append({
                    'line': line_number,
                    'content': line,
                    'error': f'Invalid format: expected 5 fields (P,N,E,Z,D), found {len(parts)}'
                })
                continue
            
            try:
                point_number = parts[0].strip()
                northing = float(parts[1].strip())
                easting = float(parts[2].strip())
                elevation = float(parts[3].strip())
                # Description may contain commas, so join remaining parts
                description = ','.join(parts[4:]).strip()
                
                # Remove quotes from description if present
                if description.startswith('"') and description.endswith('"'):
                    description = description[1:-1]
                
                # Validate required fields are non-empty
                if not point_number:
                    errors.append({
                        'line': line_number,
                        'content': line,
                        'error': 'Point number is required and cannot be empty'
                    })
                    continue
                
                if not description:
                    errors.append({
                        'line': line_number,
                        'content': line,
                        'error': 'Description is required and cannot be empty'
                    })
                    continue
                
                point_data = {
                    'point_number': point_number,
                    'northing': northing,
                    'easting': easting,
                    'elevation': elevation,
                    'description': description,
                    'source_file': source_filename,
                    'line_number': line_number,
                    'exists': False,
                    'action': 'import'
                }
                
                points.append(point_data)
                
            except ValueError as e:
                errors.append({
                    'line': line_number,
                    'content': line,
                    'error': f'Invalid numeric value: {str(e)}'
                })
            except Exception as e:
                errors.append({
                    'line': line_number,
                    'content': line,
                    'error': f'Parse error: {str(e)}'
                })
        
        return {
            'points': points,
            'errors': errors,
            'total_lines': line_number,
            'valid_points': len(points),
            'error_count': len(errors)
        }
    
    def check_existing_points(self, points: List[Dict], project_id: str) -> List[Dict]:
        """
        Check which points already exist in the database for this project

        Args:
            points: List of point dictionaries
            project_id: UUID of the project to check against

        Returns:
            Updated points list with 'exists' flag set

        Raises:
            Exception: If database query fails
        """
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        try:
            # Get existing point numbers for this project
            cur.execute("""
                SELECT point_number
                FROM survey_points
                WHERE project_id = %s
            """, (project_id,))
            
            existing_points = {row['point_number'] for row in cur.fetchall()}
            
            # Mark points that already exist
            for point in points:
                if point['point_number'] in existing_points:
                    point['exists'] = True
                    point['action'] = 'update'
            
        finally:
            cur.close()
            conn.close()
        
        return points
    
    def get_coordinate_systems(self) -> List[Dict]:
        """
        Get list of available coordinate systems from database.

        This method now uses the CoordinateSystemService for consistency.

        Returns:
            List of coordinate system dictionaries with keys:
            - system_id (as coord_system_id for backward compatibility)
            - system_name
            - epsg_code
            - units

        Raises:
            Exception: If database query fails or no coordinate systems found
        """
        systems = self.crs_service.get_all_active_systems()

        if not systems:
            raise Exception("No active coordinate systems found in database")

        # Rename system_id to coord_system_id for backward compatibility
        for system in systems:
            system['coord_system_id'] = system['system_id']

        return systems
    
    def get_projects(self) -> Dict:
        """
        Get list of projects for selection

        Returns:
            Dict with 'projects' key containing list of project dictionaries

        Raises:
            Exception: If database query fails
        """
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        try:
            # Get all projects
            cur.execute("""
                SELECT
                    p.project_id,
                    p.project_name,
                    p.project_number,
                    p.client_name,
                    p.created_at
                FROM projects p
                ORDER BY p.project_name
            """)

            projects = cur.fetchall()

            # Convert to list of dicts
            project_list = [dict(row) for row in projects]

            return {'projects': project_list}

        finally:
            cur.close()
            conn.close()
