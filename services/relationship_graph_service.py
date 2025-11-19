"""
Relationship Graph Service
Core CRUD operations for the unified graph-based relationship system.

This service manages entity-to-entity relationships using the relationship_edges table,
providing a flexible graph model that can express any type of connection between entities.

References:
    - docs/PHASE_3_COMPREHENSIVE_ANALYSIS.md
    - database/migrations/022_create_relationship_edges.sql
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db, execute_query as db_execute_query
from tools.db_utils import execute_query
from services.entity_registry import EntityRegistry
from typing import Dict, List, Optional, Any, Tuple
import json
from datetime import datetime, date
from decimal import Decimal


class RelationshipGraphService:
    """Service for managing relationship edges in the graph model"""

    def __init__(self):
        self.registry = EntityRegistry()

    # ============================================================================
    # CRUD OPERATIONS
    # ============================================================================

    def create_edge(
        self,
        project_id: str,
        source_entity_type: str,
        source_entity_id: str,
        target_entity_type: str,
        target_entity_id: str,
        relationship_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new relationship edge between two entities.

        Args:
            project_id: Project UUID
            source_entity_type: Type of source entity (detail, block, material, etc.)
            source_entity_id: UUID of source entity
            target_entity_type: Type of target entity
            target_entity_id: UUID of target entity
            relationship_type: Type of relationship (USES, REFERENCES, CONTAINS, etc.)
            **kwargs: Optional parameters:
                - relationship_strength (float): 0.0-1.0
                - is_bidirectional (bool): Default False
                - relationship_metadata (dict): Additional attributes
                - created_by (str): User who created the relationship
                - source (str): Origin of relationship (manual, import, inference, template)
                - confidence_score (float): 0.0-1.0 for AI-inferred relationships
                - valid_from (date): Start of validity period
                - valid_to (date): End of validity period

        Returns:
            Created edge data with edge_id

        Raises:
            ValueError: If entity types are invalid or edge already exists
        """
        # Validate entity types
        if not self.registry.is_valid_entity_type(source_entity_type):
            raise ValueError(f"Invalid source_entity_type '{source_entity_type}'")

        if not self.registry.is_valid_entity_type(target_entity_type):
            raise ValueError(f"Invalid target_entity_type '{target_entity_type}'")

        # Validate relationship type (will be checked by trigger, but check early for better error messages)
        type_check = execute_query(
            "SELECT type_code FROM relationship_type_registry WHERE type_code = %s AND is_active = TRUE",
            (relationship_type,)
        )
        if not type_check:
            raise ValueError(f"Invalid relationship_type '{relationship_type}'. Must be registered in relationship_type_registry.")

        # Check for existing edge
        existing = execute_query(
            """
            SELECT edge_id, is_active FROM relationship_edges
            WHERE project_id = %s
              AND source_entity_type = %s
              AND source_entity_id = %s
              AND target_entity_type = %s
              AND target_entity_id = %s
              AND relationship_type = %s
            """,
            (project_id, source_entity_type, source_entity_id,
             target_entity_type, target_entity_id, relationship_type)
        )

        if existing:
            if existing[0]['is_active']:
                raise ValueError("Relationship edge already exists")
            else:
                # Restore inactive edge
                return self._restore_edge(existing[0]['edge_id'], **kwargs)

        # Create new edge
        query = """
            INSERT INTO relationship_edges (
                project_id, source_entity_type, source_entity_id,
                target_entity_type, target_entity_id, relationship_type,
                relationship_strength, is_bidirectional, relationship_metadata,
                created_by, source, confidence_score, valid_from, valid_to
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """

        params = (
            project_id,
            source_entity_type,
            str(source_entity_id),
            target_entity_type,
            str(target_entity_id),
            relationship_type,
            kwargs.get('relationship_strength'),
            kwargs.get('is_bidirectional', False),
            json.dumps(kwargs.get('relationship_metadata', {})),
            kwargs.get('created_by'),
            kwargs.get('source', 'manual'),
            kwargs.get('confidence_score'),
            kwargs.get('valid_from'),
            kwargs.get('valid_to')
        )

        results = execute_query(query, params)
        return results[0] if results else None

    def create_edges_batch(
        self,
        project_id: str,
        edges: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Create multiple relationship edges in a single transaction.

        Args:
            project_id: Project UUID
            edges: List of edge dictionaries with keys:
                - source_entity_type, source_entity_id
                - target_entity_type, target_entity_id
                - relationship_type
                - (optional) relationship_strength, is_bidirectional, relationship_metadata, etc.

        Returns:
            List of created edge records

        Raises:
            ValueError: If validation fails for any edge
        """
        created_edges = []

        with get_db() as conn:
            with conn.cursor() as cur:
                try:
                    for edge in edges:
                        # Validate required fields
                        required_fields = ['source_entity_type', 'source_entity_id',
                                         'target_entity_type', 'target_entity_id',
                                         'relationship_type']
                        for field in required_fields:
                            if field not in edge:
                                raise ValueError(f"Missing required field: {field}")

                        # Validate entity types
                        if not self.registry.is_valid_entity_type(edge['source_entity_type']):
                            raise ValueError(f"Invalid source_entity_type '{edge['source_entity_type']}'")

                        if not self.registry.is_valid_entity_type(edge['target_entity_type']):
                            raise ValueError(f"Invalid target_entity_type '{edge['target_entity_type']}'")

                        # Insert edge
                        cur.execute(
                            """
                            INSERT INTO relationship_edges (
                                project_id, source_entity_type, source_entity_id,
                                target_entity_type, target_entity_id, relationship_type,
                                relationship_strength, is_bidirectional, relationship_metadata,
                                created_by, source, confidence_score, valid_from, valid_to
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING *
                            """,
                            (
                                project_id,
                                edge['source_entity_type'],
                                str(edge['source_entity_id']),
                                edge['target_entity_type'],
                                str(edge['target_entity_id']),
                                edge['relationship_type'],
                                edge.get('relationship_strength'),
                                edge.get('is_bidirectional', False),
                                json.dumps(edge.get('relationship_metadata', {})),
                                edge.get('created_by'),
                                edge.get('source', 'manual'),
                                edge.get('confidence_score'),
                                edge.get('valid_from'),
                                edge.get('valid_to')
                            )
                        )
                        created_edge = cur.fetchone()
                        if created_edge:
                            created_edges.append(dict(created_edge))

                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    raise e

        return created_edges

    def get_edge(self, edge_id: str) -> Optional[Dict[str, Any]]:
        """Get a single relationship edge by ID"""
        query = "SELECT * FROM relationship_edges WHERE edge_id = %s"
        results = execute_query(query, (edge_id,))
        return results[0] if results else None

    def get_edges(
        self,
        project_id: Optional[str] = None,
        source_entity_type: Optional[str] = None,
        source_entity_id: Optional[str] = None,
        target_entity_type: Optional[str] = None,
        target_entity_id: Optional[str] = None,
        relationship_type: Optional[str] = None,
        is_active: bool = True,
        limit: int = 1000,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Query relationship edges with flexible filtering.

        Args:
            project_id: Filter by project
            source_entity_type: Filter by source entity type
            source_entity_id: Filter by source entity ID
            target_entity_type: Filter by target entity type
            target_entity_id: Filter by target entity ID
            relationship_type: Filter by relationship type
            is_active: Filter by active status (default True)
            limit: Maximum results to return
            offset: Pagination offset

        Returns:
            List of matching edges
        """
        conditions = []
        params = []

        if project_id is not None:
            conditions.append("project_id = %s")
            params.append(project_id)

        if source_entity_type is not None:
            conditions.append("source_entity_type = %s")
            params.append(source_entity_type)

        if source_entity_id is not None:
            conditions.append("source_entity_id = %s")
            params.append(str(source_entity_id))

        if target_entity_type is not None:
            conditions.append("target_entity_type = %s")
            params.append(target_entity_type)

        if target_entity_id is not None:
            conditions.append("target_entity_id = %s")
            params.append(str(target_entity_id))

        if relationship_type is not None:
            conditions.append("relationship_type = %s")
            params.append(relationship_type)

        if is_active is not None:
            conditions.append("is_active = %s")
            params.append(is_active)

        where_clause = " AND ".join(conditions) if conditions else "TRUE"

        query = f"""
            SELECT * FROM relationship_edges
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])

        return execute_query(query, tuple(params))

    def update_edge(
        self,
        edge_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Update an existing relationship edge.

        Args:
            edge_id: UUID of edge to update
            **kwargs: Fields to update:
                - relationship_strength
                - is_bidirectional
                - relationship_metadata (dict or JSON string)
                - status
                - valid_from
                - valid_to
                - is_active

        Returns:
            Updated edge data

        Raises:
            ValueError: If edge not found
        """
        # Check edge exists
        edge = self.get_edge(edge_id)
        if not edge:
            raise ValueError(f"Edge not found: {edge_id}")

        # Build update statement
        update_fields = []
        params = []

        if 'relationship_strength' in kwargs:
            update_fields.append("relationship_strength = %s")
            params.append(kwargs['relationship_strength'])

        if 'is_bidirectional' in kwargs:
            update_fields.append("is_bidirectional = %s")
            params.append(kwargs['is_bidirectional'])

        if 'relationship_metadata' in kwargs:
            metadata = kwargs['relationship_metadata']
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            update_fields.append("relationship_metadata = %s")
            params.append(json.dumps(metadata))

        if 'status' in kwargs:
            update_fields.append("status = %s")
            params.append(kwargs['status'])

        if 'valid_from' in kwargs:
            update_fields.append("valid_from = %s")
            params.append(kwargs['valid_from'])

        if 'valid_to' in kwargs:
            update_fields.append("valid_to = %s")
            params.append(kwargs['valid_to'])

        if 'is_active' in kwargs:
            update_fields.append("is_active = %s")
            params.append(kwargs['is_active'])

        if not update_fields:
            return edge  # No changes

        query = f"""
            UPDATE relationship_edges
            SET {', '.join(update_fields)}
            WHERE edge_id = %s
            RETURNING *
        """
        params.append(edge_id)

        results = execute_query(query, tuple(params))
        return results[0] if results else None

    def delete_edge(self, edge_id: str, soft_delete: bool = True) -> bool:
        """
        Delete a relationship edge.

        Args:
            edge_id: UUID of edge to delete
            soft_delete: If True, set is_active=False; if False, hard delete

        Returns:
            True if successful

        Raises:
            ValueError: If edge not found
        """
        edge = self.get_edge(edge_id)
        if not edge:
            raise ValueError(f"Edge not found: {edge_id}")

        if soft_delete:
            query = "UPDATE relationship_edges SET is_active = FALSE, status = 'deleted' WHERE edge_id = %s"
        else:
            query = "DELETE FROM relationship_edges WHERE edge_id = %s"

        execute_query(query, (edge_id,))
        return True

    def delete_edges_batch(
        self,
        edge_ids: List[str],
        soft_delete: bool = True
    ) -> int:
        """
        Delete multiple edges at once.

        Args:
            edge_ids: List of edge UUIDs
            soft_delete: If True, set is_active=False; if False, hard delete

        Returns:
            Number of edges deleted
        """
        if not edge_ids:
            return 0

        if soft_delete:
            query = """
                UPDATE relationship_edges
                SET is_active = FALSE, status = 'deleted'
                WHERE edge_id = ANY(%s)
            """
        else:
            query = "DELETE FROM relationship_edges WHERE edge_id = ANY(%s)"

        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (edge_ids,))
                count = cur.rowcount
                conn.commit()

        return count

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    def _restore_edge(self, edge_id: str, **kwargs) -> Dict[str, Any]:
        """Restore a soft-deleted edge and optionally update its properties"""
        update_data = {
            'is_active': True,
            'status': 'active'
        }
        update_data.update(kwargs)

        return self.update_edge(edge_id, **update_data)

    def get_edge_count(
        self,
        project_id: Optional[str] = None,
        relationship_type: Optional[str] = None,
        is_active: bool = True
    ) -> int:
        """Get count of edges matching criteria"""
        conditions = []
        params = []

        if project_id is not None:
            conditions.append("project_id = %s")
            params.append(project_id)

        if relationship_type is not None:
            conditions.append("relationship_type = %s")
            params.append(relationship_type)

        if is_active is not None:
            conditions.append("is_active = %s")
            params.append(is_active)

        where_clause = " AND ".join(conditions) if conditions else "TRUE"

        query = f"SELECT COUNT(*) as count FROM relationship_edges WHERE {where_clause}"
        result = execute_query(query, tuple(params))
        return result[0]['count'] if result else 0

    def get_relationship_types(self) -> List[Dict[str, Any]]:
        """Get all registered relationship types"""
        query = """
            SELECT * FROM relationship_type_registry
            WHERE is_active = TRUE
            ORDER BY category, type_code
        """
        return execute_query(query)

    def get_relationship_type(self, type_code: str) -> Optional[Dict[str, Any]]:
        """Get a specific relationship type definition"""
        query = "SELECT * FROM relationship_type_registry WHERE type_code = %s"
        results = execute_query(query, (type_code,))
        return results[0] if results else None

    def validate_edge_data(
        self,
        source_entity_type: str,
        target_entity_type: str,
        relationship_type: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate edge data against relationship type constraints.

        Returns:
            (is_valid, error_message)
        """
        # Get relationship type config
        rel_type = self.get_relationship_type(relationship_type)
        if not rel_type:
            return False, f"Invalid relationship_type: {relationship_type}"

        # Validate source entity type
        if rel_type['valid_source_types'] is not None:
            if source_entity_type not in rel_type['valid_source_types']:
                return False, f"Invalid source_entity_type '{source_entity_type}' for relationship_type '{relationship_type}'. Valid types: {', '.join(rel_type['valid_source_types'])}"

        # Validate target entity type
        if rel_type['valid_target_types'] is not None:
            if target_entity_type not in rel_type['valid_target_types']:
                return False, f"Invalid target_entity_type '{target_entity_type}' for relationship_type '{relationship_type}'. Valid types: {', '.join(rel_type['valid_target_types'])}"

        return True, None
