"""
Entity Registry for Relationship Sets
Maps entity types to their database tables and primary keys.
Provides safe, validated access to entity metadata.
"""

from typing import Dict, Optional

# Entity Registry: Maps entity_type → (table_name, primary_key_column)
# This prevents SQL injection and ensures correct primary key references
ENTITY_REGISTRY: Dict[str, tuple[str, str]] = {
    # Utility Systems
    'utility_line': ('utility_lines', 'line_id'),
    'utility_structure': ('utility_structures', 'structure_id'),
    'bmp': ('bmps', 'bmp_id'),
    'ada_feature': ('ada_features', 'feature_id'),
    
    # Survey & Civil
    'survey_point': ('survey_points', 'point_id'),
    'survey_code': ('survey_codes', 'code_id'),
    'alignment': ('alignments', 'alignment_id'),
    'profile': ('profiles', 'profile_id'),
    'parcel': ('parcels', 'parcel_id'),
    
    # CAD Standards
    'layer_standard': ('layer_standards', 'layer_id'),
    'block_standard': ('block_standards', 'block_id'),
    'detail_standard': ('detail_standards', 'detail_id'),
    'hatch_standard': ('hatch_standards', 'hatch_id'),
    'material_standard': ('material_standards', 'material_id'),
    'note_standard': ('note_standards', 'note_id'),
    'linetype_standard': ('linetype_standards', 'linetype_id'),
    
    # Project Elements
    'project': ('projects', 'project_id'),
    'project_note': ('project_notes', 'note_id'),
    'sheet_set': ('sheet_sets', 'set_id'),
    'sheet': ('sheets', 'sheet_id'),
    
    # Drawing Entities
    'drawing': ('drawings', 'drawing_id'),
    'drawing_entity': ('drawing_entities', 'entity_id'),
    'generic_object': ('generic_objects', 'object_id'),
    
    # Reference Data
    'client': ('clients', 'client_id'),
    'vendor': ('vendors', 'vendor_id'),
    'municipality': ('municipalities', 'municipality_id'),
    'coordinate_system': ('coordinate_systems', 'system_id'),
    'gis_data_layer': ('gis_data_layers', 'layer_id'),
    
    # Relationship Sets (self-reference)
    'relationship_set': ('project_relationship_sets', 'set_id'),
    'relationship_member': ('project_relationship_members', 'member_id'),
    'relationship_rule': ('project_relationship_rules', 'rule_id'),
    'relationship_violation': ('project_relationship_violations', 'violation_id'),
}


class EntityRegistry:
    """Safe registry for entity metadata lookups"""
    
    @staticmethod
    def get_table_info(entity_type: str) -> Optional[tuple[str, str]]:
        """
        Get table name and primary key for an entity type.
        
        Args:
            entity_type: Entity type code (e.g., 'utility_line', 'detail_standard')
            
        Returns:
            Tuple of (table_name, primary_key_column) or None if not found
        """
        return ENTITY_REGISTRY.get(entity_type)
    
    @staticmethod
    def is_valid_entity_type(entity_type: str) -> bool:
        """Check if an entity type is registered"""
        return entity_type in ENTITY_REGISTRY
    
    @staticmethod
    def get_table_name(entity_type: str) -> Optional[str]:
        """Get table name for an entity type"""
        info = ENTITY_REGISTRY.get(entity_type)
        return info[0] if info else None
    
    @staticmethod
    def get_primary_key(entity_type: str) -> Optional[str]:
        """Get primary key column name for an entity type"""
        info = ENTITY_REGISTRY.get(entity_type)
        return info[1] if info else None
    
    @staticmethod
    def validate_table_name(table_name: str) -> bool:
        """
        Validate that a table name is in the registry.
        CRITICAL: Use this before any dynamic SQL to prevent injection.
        """
        valid_tables = {info[0] for info in ENTITY_REGISTRY.values()}
        return table_name in valid_tables
    
    @staticmethod
    def get_all_entity_types() -> list[str]:
        """Get list of all registered entity types"""
        return list(ENTITY_REGISTRY.keys())
    
    @staticmethod
    def get_all_tables() -> list[str]:
        """Get list of all registered tables"""
        return list(set(info[0] for info in ENTITY_REGISTRY.values()))
