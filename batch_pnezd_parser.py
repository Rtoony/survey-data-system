"""
Batch PNEZD Parser - Parse survey point files in PNEZD format
Point Number, Northing, Easting, Elevation, Description
"""

import re
from typing import List, Dict, Optional
import psycopg2
from psycopg2.extras import RealDictCursor


class PNEZDParser:
    """Parse PNEZD format survey point files"""
    
    def __init__(self, db_config: Dict):
        self.db_config = db_config
    
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
        Get list of available coordinate systems from database
        
        Returns:
            List of coordinate system dictionaries
        
        Raises:
            Exception: If database query fails or no coordinate systems found
        """
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cur.execute("""
                SELECT 
                    system_id as coord_system_id,
                    system_name,
                    epsg_code,
                    notes as description,
                    units
                FROM coordinate_systems 
                WHERE is_active = true 
                ORDER BY system_name
            """)
            
            systems = [dict(row) for row in cur.fetchall()]
            
            if not systems:
                raise Exception("No active coordinate systems found in database")
            
            return systems
            
        finally:
            cur.close()
            conn.close()
    
    def get_projects_and_drawings(self) -> Dict:
        """
        Get list of projects and their drawings for selection
        
        Returns:
            Dict with 'projects' key containing list of project dictionaries
        
        Raises:
            Exception: If database query fails
        """
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Get all projects with their drawings
            cur.execute("""
                SELECT 
                    p.project_id,
                    p.project_name,
                    p.project_number,
                    d.drawing_id,
                    d.drawing_name,
                    d.drawing_number
                FROM projects p
                LEFT JOIN drawings d ON p.project_id = d.project_id
                ORDER BY p.project_name, d.drawing_name
            """)
            
            rows = cur.fetchall()
            
            # Organize by project
            projects = {}
            for row in rows:
                project_id = row['project_id']
                
                if project_id not in projects:
                    projects[project_id] = {
                        'project_id': project_id,
                        'project_name': row['project_name'],
                        'project_number': row['project_number'],
                        'drawings': []
                    }
                
                # Add drawing if it exists
                if row['drawing_id']:
                    projects[project_id]['drawings'].append({
                        'drawing_id': row['drawing_id'],
                        'drawing_name': row['drawing_name'],
                        'drawing_number': row['drawing_number']
                    })
            
            # Only return projects that have at least one drawing
            projects_with_drawings = [p for p in projects.values() if p['drawings']]
            
            return {'projects': projects_with_drawings}
            
        finally:
            cur.close()
            conn.close()
