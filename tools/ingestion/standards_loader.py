"""
CAD Standards Data Ingestion Module

Load CAD standards from JSON/CSV files with automatic:
- Entity registration in standards_entities
- Tag extraction from descriptions and categories
- Quality score calculation based on completeness
- Full-text search vector generation (automatic via trigger)
"""

import json
import csv
from typing import List, Dict, Any, Optional
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from db_utils import (
    execute_query, execute_many, get_or_create_entity,
    update_quality_score, generate_uuid
)


class StandardsLoader:
    """Load CAD standards into the AI-optimized database with safety features."""
    
    def __init__(self, preview_mode: bool = False):
        """
        Initialize standards loader.
        
        Args:
            preview_mode: If True, show what would be done without modifying database
        """
        self.preview_mode = preview_mode
        self.stats = {
            'inserted': 0,
            'updated': 0,
            'skipped': 0,
            'errors': [],
            'previewed': 0
        }
    
    def _get_table_count(self, table_name: str) -> int:
        """Get current row count for a table."""
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        result = execute_query(query)
        return result[0]['count'] if result else 0
    
    def _validate_geometry(self, geometry_wkt: str, geometry_type: str = 'Point') -> bool:
        """
        Validate PostGIS geometry using ST_IsValid.
        
        Args:
            geometry_wkt: WKT string representation of geometry
            geometry_type: Expected geometry type (Point, LineString, Polygon, etc.)
            
        Returns:
            True if valid, False otherwise
        """
        if not geometry_wkt:
            return False
        
        try:
            # Check if geometry is valid and matches expected type
            query = """
                SELECT 
                    ST_IsValid(ST_GeomFromText(%s, 2226)) as is_valid,
                    GeometryType(ST_GeomFromText(%s, 2226)) as geom_type
            """
            result = execute_query(query, (geometry_wkt, geometry_wkt))
            
            if not result or not result[0]['is_valid']:
                return False
            
            # Check geometry type matches (case-insensitive)
            actual_type = result[0]['geom_type'].upper()
            expected_type = geometry_type.upper()
            
            # Handle variations (e.g., POINT vs POINTZ)
            if not actual_type.startswith(expected_type):
                return False
            
            return True
            
        except Exception as e:
            print(f"Geometry validation error: {e}")
            return False
    
    def load_layers(self, data: List[Dict]) -> Dict[str, Any]:
        """
        Load layer standards from list of dicts.
        
        Expected fields:
        - name (required) - IDEMPOTENT KEY
        - description
        - color_name
        - linetype_name
        - lineweight
        - is_plottable
        - category
        - discipline
        
        Returns:
            Statistics dict with before/after counts
        """
        self.stats = {'inserted': 0, 'updated': 0, 'skipped': 0, 'errors': [], 'previewed': 0}
        
        # Get initial count
        count_before = self._get_table_count('layer_standards')
        
        # PREVIEW MODE
        if self.preview_mode:
            print(f"\n{'='*70}")
            print(f"🔍 PREVIEW MODE - No changes will be made to database")
            print(f"{'='*70}")
            print(f"Current layer_standards count: {count_before}")
            print(f"Items to process: {len(data)}")
            print(f"\nSample items to be loaded:")
            for item in data[:5]:
                action = "UPDATE" if execute_query(
                    "SELECT 1 FROM layer_standards WHERE name = %s", 
                    (item.get('name'),)
                ) else "INSERT"
                print(f"  [{action}] {item.get('name')} - {item.get('description', 'No description')}")
            if len(data) > 5:
                print(f"  ... and {len(data) - 5} more")
            print(f"{'='*70}\n")
            self.stats['previewed'] = len(data)
            return self.stats
        
        for item in data:
            try:
                name = item.get('name')
                if not name:
                    self.stats['errors'].append('Missing layer name')
                    continue
                
                # IDEMPOTENT KEY: Check if layer exists (name is unique natural key for layers)
                # Note: For layers, name alone is sufficient as it must be unique per CAD standard
                existing = execute_query(
                    "SELECT layer_id, entity_id FROM layer_standards WHERE name = %s",
                    (name,)
                )
                
                # Extract tags from category, discipline, description
                tags = []
                if item.get('category'):
                    tags.append(item['category'].lower())
                if item.get('discipline'):
                    tags.append(item['discipline'].lower())
                
                # Build attributes JSON
                attributes = {
                    'color': item.get('color_name'),
                    'linetype': item.get('linetype_name'),
                    'lineweight': item.get('lineweight'),
                    'is_plottable': item.get('is_plottable', True)
                }
                
                if existing:
                    # Update existing layer
                    layer_id = existing[0]['layer_id']
                    entity_id = existing[0]['entity_id']
                    
                    query = """
                        UPDATE layer_standards
                        SET description = %s, color_name = %s, linetype_name = %s,
                            lineweight = %s, is_plottable = %s, tags = %s,
                            attributes = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE layer_id = %s
                    """
                    execute_query(query, (
                        item.get('description'),
                        item.get('color_name'),
                        item.get('linetype_name'),
                        item.get('lineweight'),
                        item.get('is_plottable', True),
                        tags,
                        json.dumps(attributes),
                        layer_id
                    ), fetch=False)
                    
                    self.stats['updated'] += 1
                else:
                    # Insert new layer
                    layer_id = generate_uuid()
                    entity_id = get_or_create_entity(
                        entity_type='layer',
                        canonical_name=name,
                        source_table='layer_standards',
                        source_id=layer_id,
                        tags=tags,
                        attributes=attributes
                    )
                    
                    query = """
                        INSERT INTO layer_standards (
                            layer_id, name, description, color_name, linetype_name,
                            lineweight, is_plottable, entity_id, tags, attributes
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    execute_query(query, (
                        layer_id, name, item.get('description'),
                        item.get('color_name'), item.get('linetype_name'),
                        item.get('lineweight'), item.get('is_plottable', True),
                        entity_id, tags, json.dumps(attributes)
                    ), fetch=False)
                    
                    self.stats['inserted'] += 1
                
                # Calculate quality score (count filled required fields)
                filled = sum([
                    1 for f in [name, item.get('description'), item.get('color_name'),
                               item.get('linetype_name')]
                    if f
                ])
                update_quality_score(entity_id, filled, total_required=4)
                
            except Exception as e:
                self.stats['errors'].append(f"Error loading layer {item.get('name')}: {str(e)}")
        
        # Get final count and show summary
        count_after = self._get_table_count('layer_standards')
        self.stats['count_before'] = count_before
        self.stats['count_after'] = count_after
        self.stats['net_change'] = count_after - count_before
        
        print(f"\n{'='*70}")
        print(f"Layer Standards Import Summary")
        print(f"{'='*70}")
        print(f"Before: {count_before} layers")
        print(f"After:  {count_after} layers")
        print(f"Net change: +{count_after - count_before}")
        print(f"  Inserted: {self.stats['inserted']}")
        print(f"  Updated: {self.stats['updated']}")
        if self.stats['errors']:
            print(f"  Errors: {len(self.stats['errors'])}")
        print(f"{'='*70}\n")
        
        return self.stats
    
    def load_blocks(self, data: List[Dict]) -> Dict[str, Any]:
        """
        Load block definitions from list of dicts.
        
        Expected fields:
        - name (required) - IDEMPOTENT KEY
        - description
        - category
        - file_path
        - insertion_units
        
        Returns:
            Statistics dict with before/after counts
        """
        self.stats = {'inserted': 0, 'updated': 0, 'skipped': 0, 'errors': [], 'previewed': 0}
        
        # Get initial count
        count_before = self._get_table_count('block_definitions')
        
        # PREVIEW MODE
        if self.preview_mode:
            print(f"\n{'='*70}")
            print(f"🔍 PREVIEW MODE - No changes will be made to database")
            print(f"{'='*70}")
            print(f"Current block_definitions count: {count_before}")
            print(f"Items to process: {len(data)}")
            print(f"\nSample items to be loaded:")
            for item in data[:5]:
                action = "UPDATE" if execute_query(
                    "SELECT 1 FROM block_definitions WHERE name = %s", 
                    (item.get('name'),)
                ) else "INSERT"
                print(f"  [{action}] {item.get('name')} - {item.get('description', 'No description')}")
            if len(data) > 5:
                print(f"  ... and {len(data) - 5} more")
            print(f"{'='*70}\n")
            self.stats['previewed'] = len(data)
            return self.stats
        
        for item in data:
            try:
                name = item.get('name')
                if not name:
                    self.stats['errors'].append('Missing block name')
                    continue
                
                existing = execute_query(
                    "SELECT block_id, entity_id FROM block_definitions WHERE name = %s",
                    (name,)
                )
                
                tags = []
                if item.get('category'):
                    tags.append(item['category'].lower())
                
                attributes = {
                    'file_path': item.get('file_path'),
                    'insertion_units': item.get('insertion_units', 'Inches'),
                    'is_dynamic': item.get('is_dynamic', False)
                }
                
                if existing:
                    block_id = existing[0]['block_id']
                    entity_id = existing[0]['entity_id']
                    
                    query = """
                        UPDATE block_definitions
                        SET description = %s, category = %s, file_path = %s,
                            tags = %s, attributes = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE block_id = %s
                    """
                    execute_query(query, (
                        item.get('description'), item.get('category'),
                        item.get('file_path'), tags, json.dumps(attributes),
                        block_id
                    ), fetch=False)
                    
                    self.stats['updated'] += 1
                else:
                    block_id = generate_uuid()
                    entity_id = get_or_create_entity(
                        entity_type='block',
                        canonical_name=name,
                        source_table='block_definitions',
                        source_id=block_id,
                        tags=tags,
                        attributes=attributes
                    )
                    
                    query = """
                        INSERT INTO block_definitions (
                            block_id, name, description, category, file_path,
                            entity_id, tags, attributes
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    execute_query(query, (
                        block_id, name, item.get('description'),
                        item.get('category'), item.get('file_path'),
                        entity_id, tags, json.dumps(attributes)
                    ), fetch=False)
                    
                    self.stats['inserted'] += 1
                
                filled = sum([1 for f in [name, item.get('description'), item.get('category')] if f])
                update_quality_score(entity_id, filled, total_required=3)
                
            except Exception as e:
                self.stats['errors'].append(f"Error loading block {item.get('name')}: {str(e)}")
        
        # Get final count and show summary
        count_after = self._get_table_count('block_definitions')
        self.stats['count_before'] = count_before
        self.stats['count_after'] = count_after
        self.stats['net_change'] = count_after - count_before
        
        print(f"\n{'='*70}")
        print(f"Block Definitions Import Summary")
        print(f"{'='*70}")
        print(f"Before: {count_before} blocks")
        print(f"After:  {count_after} blocks")
        print(f"Net change: +{count_after - count_before}")
        print(f"  Inserted: {self.stats['inserted']}")
        print(f"  Updated: {self.stats['updated']}")
        if self.stats['errors']:
            print(f"  Errors: {len(self.stats['errors'])}")
        print(f"{'='*70}\n")
        
        return self.stats
    
    def load_details(self, data: List[Dict]) -> Dict[str, Any]:
        """
        Load detail standards from list of dicts.
        
        Expected fields:
        - detail_number (required)
        - title
        - description
        - category
        - discipline
        - file_path
        """
        self.stats = {'inserted': 0, 'updated': 0, 'errors': []}
        
        for item in data:
            try:
                detail_number = item.get('detail_number')
                if not detail_number:
                    self.stats['errors'].append('Missing detail_number')
                    continue
                
                existing = execute_query(
                    "SELECT detail_id, entity_id FROM detail_standards WHERE detail_number = %s",
                    (detail_number,)
                )
                
                tags = []
                if item.get('category'):
                    tags.append(item['category'].lower())
                if item.get('discipline'):
                    tags.append(item['discipline'].lower())
                
                attributes = {
                    'file_path': item.get('file_path'),
                    'scale': item.get('scale'),
                    'sheet_size': item.get('sheet_size')
                }
                
                if existing:
                    detail_id = existing[0]['detail_id']
                    entity_id = existing[0]['entity_id']
                    
                    query = """
                        UPDATE detail_standards
                        SET title = %s, description = %s, category = %s, discipline = %s,
                            file_path = %s, tags = %s, attributes = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE detail_id = %s
                    """
                    execute_query(query, (
                        item.get('title'), item.get('description'),
                        item.get('category'), item.get('discipline'),
                        item.get('file_path'), tags, json.dumps(attributes),
                        detail_id
                    ), fetch=False)
                    
                    self.stats['updated'] += 1
                else:
                    detail_id = generate_uuid()
                    canonical_name = f"{detail_number} - {item.get('title', 'Untitled')}"
                    entity_id = get_or_create_entity(
                        entity_type='detail',
                        canonical_name=canonical_name,
                        source_table='detail_standards',
                        source_id=detail_id,
                        tags=tags,
                        attributes=attributes
                    )
                    
                    query = """
                        INSERT INTO detail_standards (
                            detail_id, detail_number, title, description, category, discipline,
                            file_path, entity_id, tags, attributes
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    execute_query(query, (
                        detail_id, detail_number, item.get('title'),
                        item.get('description'), item.get('category'),
                        item.get('discipline'), item.get('file_path'),
                        entity_id, tags, json.dumps(attributes)
                    ), fetch=False)
                    
                    self.stats['inserted'] += 1
                
                filled = sum([
                    1 for f in [detail_number, item.get('title'), item.get('description'),
                               item.get('category')]
                    if f
                ])
                update_quality_score(entity_id, filled, total_required=4)
                
            except Exception as e:
                self.stats['errors'].append(f"Error loading detail {item.get('detail_number')}: {str(e)}")
        
        return self.stats
    
    def load_from_json(self, file_path: str, standard_type: str) -> Dict[str, Any]:
        """
        Load standards from JSON file.
        
        Args:
            file_path: Path to JSON file
            standard_type: 'layers', 'blocks', or 'details'
        """
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if standard_type == 'layers':
            return self.load_layers(data)
        elif standard_type == 'blocks':
            return self.load_blocks(data)
        elif standard_type == 'details':
            return self.load_details(data)
        else:
            raise ValueError(f"Unknown standard_type: {standard_type}")
    
    def load_from_csv(self, file_path: str, standard_type: str) -> Dict[str, Any]:
        """
        Load standards from CSV file.
        
        Args:
            file_path: Path to CSV file
            standard_type: 'layers', 'blocks', or 'details'
        """
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            data = list(reader)
        
        if standard_type == 'layers':
            return self.load_layers(data)
        elif standard_type == 'blocks':
            return self.load_blocks(data)
        elif standard_type == 'details':
            return self.load_details(data)
        else:
            raise ValueError(f"Unknown standard_type: {standard_type}")


if __name__ == '__main__':
    # Example usage
    loader = StandardsLoader()
    
    # Example layer data
    sample_layers = [
        {
            'name': 'C-TOPO-MAJR',
            'description': 'Major topographic contours',
            'color_name': 'Brown',
            'linetype_name': 'Continuous',
            'lineweight': 0.35,
            'is_plottable': True,
            'category': 'Civil',
            'discipline': 'Site'
        },
        {
            'name': 'A-WALL',
            'description': 'Architectural walls',
            'color_name': 'Black',
            'linetype_name': 'Continuous',
            'lineweight': 0.50,
            'is_plottable': True,
            'category': 'Architecture',
            'discipline': 'Building'
        }
    ]
    
    stats = loader.load_layers(sample_layers)
    print(f"Loaded layers: {stats}")
