"""
Project Mapping Service
Reusable service layer for project-entity mapping CRUD operations
"""
from typing import Dict, List, Optional, Any
from project_mapping_registry import get_entity_config
from database import get_db, execute_query


class ProjectMappingService:
    """Generic service for managing project-entity mappings"""
    
    def __init__(self, entity_type: str):
        """Initialize service with entity type configuration"""
        self.entity_type = entity_type
        self.config = get_entity_config(entity_type)
        self.table_name = self.config['table_name']
        self.mapping_id_column = self.config['mapping_id_column']
        self.entity_id_column = self.config['entity_id_column']
        self.entity_table = self.config['entity_table']
        self.entity_pk = self.config['entity_pk']
    
    def list_attached(self, project_id: str) -> List[Dict[str, Any]]:
        """List all entities attached to a project"""
        # Validate project exists
        self._validate_project_exists(project_id)
        
        # Execute configured list query
        results = execute_query(self.config['list_query'], (project_id,))
        return results if results else []
    
    def list_available(self, project_id: str) -> List[Dict[str, Any]]:
        """List all entities available to attach (not already attached)"""
        # Validate project exists
        self._validate_project_exists(project_id)
        
        # Execute configured available query
        results = execute_query(self.config['available_query'], (project_id,))
        return results if results else []
    
    def attach(self, project_id: str, entity_id: int, 
               is_primary: bool = False, 
               relationship_notes: Optional[str] = None,
               display_order: Optional[int] = None) -> Dict[str, Any]:
        """Attach an entity to a project"""
        # Validate project and entity exist
        self._validate_project_exists(project_id)
        self._validate_entity_exists(entity_id)
        
        # Check if already attached (including inactive)
        existing_check = execute_query(
            f"""
            SELECT {self.mapping_id_column}, is_active
            FROM {self.table_name}
            WHERE project_id = %s AND {self.entity_id_column} = %s
            """,
            (project_id, entity_id)
        )
        
        if existing_check:
            if existing_check[0]['is_active']:
                raise ValueError(f"{self.config['display_name']} already attached to this project")
            else:
                # Restore inactive mapping
                with get_db() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            f"""
                            UPDATE {self.table_name}
                            SET is_active = true,
                                is_primary = %s,
                                relationship_notes = %s,
                                display_order = %s,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE {self.mapping_id_column} = %s
                            RETURNING {self.mapping_id_column}
                            """,
                            (is_primary, relationship_notes, display_order, existing_check[0][self.mapping_id_column])
                        )
                        mapping_id = cur.fetchone()[0]
                        conn.commit()
                return {'mapping_id': mapping_id, 'restored': True}
        
        # If setting as primary, clear other primary flags
        if is_primary:
            self._clear_primary_flags(project_id)
        
        # Insert new mapping
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {self.table_name} 
                    (project_id, {self.entity_id_column}, is_primary, relationship_notes, display_order)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING {self.mapping_id_column}
                    """,
                    (project_id, entity_id, is_primary, relationship_notes, display_order)
                )
                mapping_id = cur.fetchone()[0]
                conn.commit()
        
        return {'mapping_id': mapping_id, 'restored': False}
    
    def update(self, project_id: str, mapping_id: int,
               is_primary: Optional[bool] = None,
               relationship_notes: Optional[str] = None,
               display_order: Optional[int] = None) -> Dict[str, Any]:
        """Update a project-entity mapping"""
        # Validate project exists and mapping belongs to project
        mapping = self._fetch_mapping_or_404(project_id, mapping_id)
        
        # If setting as primary, clear other primary flags
        if is_primary and not mapping['is_primary']:
            self._clear_primary_flags(project_id)
        
        # Build update statement dynamically based on provided fields
        update_fields = []
        params = []
        
        if is_primary is not None:
            update_fields.append("is_primary = %s")
            params.append(is_primary)
        
        if relationship_notes is not None:
            update_fields.append("relationship_notes = %s")
            params.append(relationship_notes)
        
        if display_order is not None:
            update_fields.append("display_order = %s")
            params.append(display_order)
        
        if not update_fields:
            return {'success': True, 'message': 'No changes to update'}
        
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        params.extend([mapping_id, project_id])
        
        # Execute update
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE {self.table_name}
                    SET {', '.join(update_fields)}
                    WHERE {self.mapping_id_column} = %s
                      AND project_id = %s
                      AND is_active = true
                    """,
                    params
                )
                conn.commit()
        
        return {'success': True}
    
    def detach(self, project_id: str, mapping_id: int) -> Dict[str, Any]:
        """Detach an entity from a project (set inactive)"""
        # Validate mapping exists and belongs to project
        self._fetch_mapping_or_404(project_id, mapping_id)
        
        # Set inactive
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE {self.table_name}
                    SET is_active = false,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE {self.mapping_id_column} = %s
                      AND project_id = %s
                    """,
                    (mapping_id, project_id)
                )
                conn.commit()
        
        return {'success': True}
    
    # Private helper methods
    
    def _validate_project_exists(self, project_id: str):
        """Validate that project exists"""
        result = execute_query(
            "SELECT project_id FROM projects WHERE project_id = %s",
            (project_id,)
        )
        if not result:
            raise ValueError('Project not found')
    
    def _validate_entity_exists(self, entity_id: int):
        """Validate that entity exists"""
        result = execute_query(
            f"SELECT {self.entity_pk} FROM {self.entity_table} WHERE {self.entity_pk} = %s AND is_active = true",
            (entity_id,)
        )
        if not result:
            raise ValueError(f'{self.config["display_name"]} not found')
    
    def _fetch_mapping_or_404(self, project_id: str, mapping_id: int) -> Dict[str, Any]:
        """Fetch mapping and validate it belongs to project"""
        result = execute_query(
            f"""
            SELECT * FROM {self.table_name}
            WHERE {self.mapping_id_column} = %s
              AND project_id = %s
              AND is_active = true
            """,
            (mapping_id, project_id)
        )
        if not result:
            raise ValueError('Mapping not found or does not belong to this project')
        return result[0]
    
    def _clear_primary_flags(self, project_id: str):
        """Clear is_primary flag for all mappings in this project"""
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE {self.table_name}
                    SET is_primary = FALSE,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE project_id = %s
                      AND is_active = true
                      AND is_primary = TRUE
                    """,
                    (project_id,)
                )
                conn.commit()
