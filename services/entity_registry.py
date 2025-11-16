"""
Entity Registry for Relationship Sets
Maps entity types to their database tables and primary keys.
Provides safe, validated access to entity metadata.

This registry can operate in two modes:
1. Static mode: Uses the hardcoded ENTITY_REGISTRY for maximum security
2. Dynamic mode: Loads entity mappings from the standards_entities table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Optional, List
from tools.db_utils import execute_query

ENTITY_REGISTRY: Dict[str, tuple[str, str]] = {
    'utility_line': ('utility_lines', 'line_id'),
    'utility_structure': ('utility_structures', 'structure_id'),
    'bmp': ('bmps', 'bmp_id'),
    'ada_feature': ('ada_features', 'feature_id'),
    'survey_point': ('survey_points', 'point_id'),
    'survey_code': ('survey_codes', 'code_id'),
    'alignment': ('alignments', 'alignment_id'),
    'profile': ('profiles', 'profile_id'),
    'parcel': ('parcels', 'parcel_id'),
    'layer_standard': ('layer_standards', 'layer_id'),
    'block_standard': ('block_standards', 'block_id'),
    'detail_standard': ('detail_standards', 'detail_id'),
    'hatch_standard': ('hatch_standards', 'hatch_id'),
    'material_standard': ('material_standards', 'material_id'),
    'note_standard': ('note_standards', 'note_id'),
    'linetype_standard': ('linetype_standards', 'linetype_id'),
    'project': ('projects', 'project_id'),
    'project_note': ('project_notes', 'note_id'),
    'sheet_set': ('sheet_sets', 'set_id'),
    'sheet': ('sheets', 'sheet_id'),
    'drawing': ('drawings', 'drawing_id'),
    'drawing_entity': ('drawing_entities', 'entity_id'),
    'generic_object': ('generic_objects', 'object_id'),
    'client': ('clients', 'client_id'),
    'vendor': ('vendors', 'vendor_id'),
    'municipality': ('municipalities', 'municipality_id'),
    'coordinate_system': ('coordinate_systems', 'system_id'),
    'gis_data_layer': ('gis_data_layers', 'layer_id'),
    'relationship_set': ('project_relationship_sets', 'set_id'),
    'relationship_member': ('project_relationship_members', 'member_id'),
    'relationship_rule': ('project_relationship_rules', 'rule_id'),
    'relationship_violation': ('project_relationship_violations', 'violation_id'),
}


class EntityRegistry:
    """
    Safe registry for entity metadata lookups.
    
    Provides a secure interface to map entity types to their database tables
    and primary keys. Can load from either static registry or database.
    """
    
    _dynamic_registry: Optional[Dict[str, tuple[str, str]]] = None
    
    @classmethod
    def _load_from_database(cls):
        """
        Load entity registry from standards_entities table.
        This discovers entity types that may not be in the static registry.
        """
        query = """
            SELECT DISTINCT 
                entity_type,
                source_table,
                canonical_name
            FROM standards_entities
            WHERE entity_type IS NOT NULL
            AND source_table IS NOT NULL
            AND status = 'active'
        """
        
        results = execute_query(query)
        if not results:
            cls._dynamic_registry = {}
            return
        
        registry = {}
        for row in results:
            entity_type = row['entity_type']
            source_table = row['source_table']
            
            primary_key = cls._infer_primary_key(source_table)
            if primary_key:
                registry[entity_type] = (source_table, primary_key)
        
        cls._dynamic_registry = registry
    
    @staticmethod
    def _infer_primary_key(table_name: str) -> Optional[str]:
        """
        Infer primary key column name from table name.
        Uses standard naming conventions (e.g., 'layers' -> 'layer_id').
        """
        if not table_name:
            return None
        
        singular = table_name.rstrip('s')
        return f"{singular}_id"
    
    @classmethod
    def refresh(cls):
        """
        Refresh the dynamic registry from database.
        Call this after adding new entity types to standards_entities.
        """
        cls._load_from_database()
    
    @classmethod
    def get_table_info(cls, entity_type: str) -> Optional[tuple[str, str]]:
        """
        Get table name and primary key for an entity type.
        Checks both static and dynamic registries.
        
        Args:
            entity_type: Entity type code (e.g., 'utility_line', 'detail_standard')
            
        Returns:
            Tuple of (table_name, primary_key_column) or None if not found
        """
        info = ENTITY_REGISTRY.get(entity_type)
        if info:
            return info
        
        if cls._dynamic_registry is None:
            cls._load_from_database()
        
        return cls._dynamic_registry.get(entity_type) if cls._dynamic_registry else None
    
    @classmethod
    def is_valid_entity_type(cls, entity_type: str) -> bool:
        """Check if an entity type is registered in either static or dynamic registry"""
        if entity_type in ENTITY_REGISTRY:
            return True
        
        if cls._dynamic_registry is None:
            cls._load_from_database()
        
        return entity_type in cls._dynamic_registry if cls._dynamic_registry else False
    
    @classmethod
    def get_table_name(cls, entity_type: str) -> Optional[str]:
        """Get table name for an entity type"""
        info = cls.get_table_info(entity_type)
        return info[0] if info else None
    
    @classmethod
    def get_primary_key(cls, entity_type: str) -> Optional[str]:
        """Get primary key column name for an entity type"""
        info = cls.get_table_info(entity_type)
        return info[1] if info else None
    
    @classmethod
    def validate_table_name(cls, table_name: str) -> bool:
        """
        Validate that a table name is in the registry.
        CRITICAL: Use this before any dynamic SQL to prevent injection.
        """
        valid_tables = {info[0] for info in ENTITY_REGISTRY.values()}
        
        if cls._dynamic_registry is None:
            cls._load_from_database()
        
        if cls._dynamic_registry:
            valid_tables.update({info[0] for info in cls._dynamic_registry.values()})
        
        return table_name in valid_tables
    
    @classmethod
    def get_all_entity_types(cls) -> List[str]:
        """Get list of all registered entity types from both registries"""
        types = set(ENTITY_REGISTRY.keys())
        
        if cls._dynamic_registry is None:
            cls._load_from_database()
        
        if cls._dynamic_registry:
            types.update(cls._dynamic_registry.keys())
        
        return sorted(list(types))
    
    @classmethod
    def get_all_tables(cls) -> List[str]:
        """Get list of all registered tables from both registries"""
        tables = {info[0] for info in ENTITY_REGISTRY.values()}
        
        if cls._dynamic_registry is None:
            cls._load_from_database()
        
        if cls._dynamic_registry:
            tables.update({info[0] for info in cls._dynamic_registry.values()})
        
        return sorted(list(tables))
    
    @classmethod
    def get_registry_stats(cls) -> Dict:
        """
        Get statistics about the entity registry.
        
        Returns:
            Dictionary with counts of static and dynamic entities
        """
        if cls._dynamic_registry is None:
            cls._load_from_database()
        
        return {
            'static_entities': len(ENTITY_REGISTRY),
            'dynamic_entities': len(cls._dynamic_registry) if cls._dynamic_registry else 0,
            'total_entities': len(cls.get_all_entity_types()),
            'total_tables': len(cls.get_all_tables())
        }
    
    @classmethod
    def get_entities_by_table(cls, table_name: str) -> List[str]:
        """
        Get all entity types that use a specific table.
        
        Args:
            table_name: Database table name
            
        Returns:
            List of entity type codes
        """
        entities = []
        
        for entity_type, info in ENTITY_REGISTRY.items():
            if info[0] == table_name:
                entities.append(entity_type)
        
        if cls._dynamic_registry is None:
            cls._load_from_database()
        
        if cls._dynamic_registry:
            for entity_type, info in cls._dynamic_registry.items():
                if info[0] == table_name and entity_type not in entities:
                    entities.append(entity_type)
        
        return sorted(entities)
