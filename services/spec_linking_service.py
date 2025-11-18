"""
Spec-Geometry Linking Service
Handles CRUD operations for linking specifications to CAD/GIS entities
"""

import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any
from db import get_db, execute_query


class SpecLinkingService:
    """Service for managing specification-to-geometry links"""

    @staticmethod
    def create_link(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new spec-geometry link

        Args:
            data: Dictionary containing:
                - spec_library_id (required)
                - entity_id (required)
                - entity_type (required)
                - project_id (optional)
                - link_type (default: 'governs')
                - compliance_status (default: 'pending')
                - linked_by (optional)
                - auto_linked (default: False)
                - link_confidence (optional)
                - relationship_notes (optional)

        Returns:
            Created link record
        """
        link_id = uuid.uuid4()

        query = """
            INSERT INTO spec_geometry_links (
                link_id, spec_library_id, entity_id, entity_type, entity_table,
                project_id, link_type, compliance_status, linked_by,
                auto_linked, link_confidence, relationship_notes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """

        params = (
            link_id,
            data['spec_library_id'],
            data['entity_id'],
            data['entity_type'],
            data.get('entity_table'),
            data.get('project_id'),
            data.get('link_type', 'governs'),
            data.get('compliance_status', 'pending'),
            data.get('linked_by'),
            data.get('auto_linked', False),
            data.get('link_confidence'),
            data.get('relationship_notes')
        )

        result = execute_query(query, params)
        return result[0] if result else None

    @staticmethod
    def get_link_by_id(link_id: str) -> Optional[Dict[str, Any]]:
        """Get a single link by ID"""
        query = """
            SELECT
                l.*,
                s.spec_number,
                s.spec_title,
                ss.standard_name,
                ss.abbreviation as standard_abbr,
                cm.csi_title
            FROM spec_geometry_links l
            LEFT JOIN spec_library s ON l.spec_library_id = s.spec_library_id
            LEFT JOIN spec_standards ss ON s.spec_standard_id = ss.spec_standard_id
            LEFT JOIN csi_masterformat cm ON s.csi_code = cm.csi_code
            WHERE l.link_id = %s AND l.is_active = TRUE
        """

        result = execute_query(query, (link_id,))
        return result[0] if result else None

    @staticmethod
    def get_links_by_entity(entity_id: str, entity_type: str) -> List[Dict[str, Any]]:
        """
        Get all spec links for a specific entity

        Args:
            entity_id: UUID of the entity
            entity_type: Type of entity (e.g., 'pipe', 'manhole')

        Returns:
            List of links with spec details
        """
        query = """
            SELECT
                l.*,
                s.spec_number,
                s.spec_title,
                s.content_structure,
                ss.standard_name,
                ss.abbreviation as standard_abbr,
                cm.csi_code,
                cm.csi_title
            FROM spec_geometry_links l
            INNER JOIN spec_library s ON l.spec_library_id = s.spec_library_id
            LEFT JOIN spec_standards ss ON s.spec_standard_id = ss.spec_standard_id
            LEFT JOIN csi_masterformat cm ON s.csi_code = cm.csi_code
            WHERE l.entity_id = %s
                AND l.entity_type = %s
                AND l.is_active = TRUE
            ORDER BY l.link_type, s.spec_number
        """

        return execute_query(query, (entity_id, entity_type))

    @staticmethod
    def get_entities_by_spec(spec_library_id: str, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all entities linked to a specific spec

        Args:
            spec_library_id: UUID of the spec
            project_id: Optional project filter

        Returns:
            List of linked entities
        """
        query = """
            SELECT
                l.*,
                COUNT(*) OVER() as total_count
            FROM spec_geometry_links l
            WHERE l.spec_library_id = %s
                AND l.is_active = TRUE
                AND (%s IS NULL OR l.project_id = %s)
            ORDER BY l.entity_type, l.linked_at DESC
        """

        return execute_query(query, (spec_library_id, project_id, project_id))

    @staticmethod
    def get_project_links(project_id: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get all spec-geometry links for a project with optional filters

        Args:
            project_id: Project UUID
            filters: Optional filters:
                - compliance_status: Filter by status
                - link_type: Filter by link type
                - entity_type: Filter by entity type
                - csi_code: Filter by CSI code

        Returns:
            List of links
        """
        filters = filters or {}

        where_clauses = ["l.project_id = %s", "l.is_active = TRUE"]
        params = [project_id]

        if filters.get('compliance_status'):
            where_clauses.append("l.compliance_status = %s")
            params.append(filters['compliance_status'])

        if filters.get('link_type'):
            where_clauses.append("l.link_type = %s")
            params.append(filters['link_type'])

        if filters.get('entity_type'):
            where_clauses.append("l.entity_type = %s")
            params.append(filters['entity_type'])

        if filters.get('csi_code'):
            where_clauses.append("s.csi_code = %s")
            params.append(filters['csi_code'])

        where_sql = " AND ".join(where_clauses)

        query = f"""
            SELECT
                l.*,
                s.spec_number,
                s.spec_title,
                ss.standard_name,
                ss.abbreviation as standard_abbr,
                cm.csi_code,
                cm.csi_title
            FROM spec_geometry_links l
            INNER JOIN spec_library s ON l.spec_library_id = s.spec_library_id
            LEFT JOIN spec_standards ss ON s.spec_standard_id = ss.spec_standard_id
            LEFT JOIN csi_masterformat cm ON s.csi_code = cm.csi_code
            WHERE {where_sql}
            ORDER BY l.compliance_status DESC, s.spec_number
        """

        return execute_query(query, tuple(params))

    @staticmethod
    def update_link(link_id: str, data: Dict[str, Any]) -> bool:
        """
        Update an existing link

        Args:
            link_id: UUID of the link
            data: Fields to update

        Returns:
            True if successful
        """
        allowed_fields = [
            'link_type', 'compliance_status', 'compliance_notes',
            'relationship_notes', 'updated_by', 'compliance_data'
        ]

        update_fields = []
        params = []

        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                params.append(data[field])

        if not update_fields:
            return False

        # Add updated_at timestamp
        update_fields.append("updated_at = NOW()")
        params.append(link_id)

        query = f"""
            UPDATE spec_geometry_links
            SET {', '.join(update_fields)}
            WHERE link_id = %s AND is_active = TRUE
            RETURNING link_id
        """

        result = execute_query(query, tuple(params))
        return len(result) > 0

    @staticmethod
    def delete_link(link_id: str, soft_delete: bool = True) -> bool:
        """
        Delete a link (soft or hard delete)

        Args:
            link_id: UUID of the link
            soft_delete: If True, mark as inactive; if False, remove from database

        Returns:
            True if successful
        """
        if soft_delete:
            query = """
                UPDATE spec_geometry_links
                SET is_active = FALSE, deleted_at = NOW()
                WHERE link_id = %s
                RETURNING link_id
            """
        else:
            query = """
                DELETE FROM spec_geometry_links
                WHERE link_id = %s
                RETURNING link_id
            """

        result = execute_query(query, (link_id,))
        return len(result) > 0

    @staticmethod
    def bulk_create_links(links_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create multiple links in a single transaction

        Args:
            links_data: List of link dictionaries

        Returns:
            Dict with counts of created, failed, duplicate links
        """
        created = 0
        failed = 0
        duplicates = 0
        errors = []

        with get_db() as conn:
            with conn.cursor() as cur:
                for link_data in links_data:
                    try:
                        # Check for existing link
                        check_query = """
                            SELECT link_id FROM spec_geometry_links
                            WHERE spec_library_id = %s
                                AND entity_id = %s
                                AND entity_type = %s
                                AND is_active = TRUE
                        """

                        cur.execute(check_query, (
                            link_data['spec_library_id'],
                            link_data['entity_id'],
                            link_data['entity_type']
                        ))

                        if cur.fetchone():
                            duplicates += 1
                            continue

                        # Create link
                        link_id = uuid.uuid4()
                        insert_query = """
                            INSERT INTO spec_geometry_links (
                                link_id, spec_library_id, entity_id, entity_type,
                                project_id, link_type, compliance_status, linked_by,
                                auto_linked, link_confidence
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """

                        cur.execute(insert_query, (
                            link_id,
                            link_data['spec_library_id'],
                            link_data['entity_id'],
                            link_data['entity_type'],
                            link_data.get('project_id'),
                            link_data.get('link_type', 'governs'),
                            link_data.get('compliance_status', 'pending'),
                            link_data.get('linked_by'),
                            link_data.get('auto_linked', False),
                            link_data.get('link_confidence')
                        ))

                        created += 1

                    except Exception as e:
                        failed += 1
                        errors.append(str(e))
                        continue

                conn.commit()

        return {
            'created': created,
            'failed': failed,
            'duplicates': duplicates,
            'errors': errors if errors else None
        }

    @staticmethod
    def get_link_statistics(project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about spec-geometry links

        Args:
            project_id: Optional project filter

        Returns:
            Dictionary with various statistics
        """
        where_clause = "WHERE is_active = TRUE"
        params = []

        if project_id:
            where_clause += " AND project_id = %s"
            params.append(project_id)

        query = f"""
            SELECT
                COUNT(*) as total_links,
                COUNT(DISTINCT entity_id) as unique_entities,
                COUNT(DISTINCT spec_library_id) as unique_specs,
                COUNT(*) FILTER (WHERE link_type = 'governs') as governs_count,
                COUNT(*) FILTER (WHERE link_type = 'references') as references_count,
                COUNT(*) FILTER (WHERE link_type = 'impacts') as impacts_count,
                COUNT(*) FILTER (WHERE compliance_status = 'compliant') as compliant_count,
                COUNT(*) FILTER (WHERE compliance_status = 'violation') as violation_count,
                COUNT(*) FILTER (WHERE compliance_status = 'warning') as warning_count,
                COUNT(*) FILTER (WHERE compliance_status = 'pending') as pending_count,
                COUNT(*) FILTER (WHERE auto_linked = TRUE) as auto_linked_count,
                AVG(link_confidence) FILTER (WHERE link_confidence IS NOT NULL) as avg_confidence
            FROM spec_geometry_links
            {where_clause}
        """

        result = execute_query(query, tuple(params) if params else None)
        return result[0] if result else {}

    @staticmethod
    def find_unlinked_entities(project_id: str, entity_type: str, table_name: str, id_column: str = 'id') -> List[Dict[str, Any]]:
        """
        Find entities that don't have any spec links

        Args:
            project_id: Project UUID
            entity_type: Type of entity
            table_name: Database table name
            id_column: Primary key column name

        Returns:
            List of unlinked entity IDs
        """
        # Note: This is a simplified version. In production, you'd need to handle
        # different entity tables dynamically or have specific methods for each type
        query = f"""
            SELECT e.{id_column} as entity_id
            FROM {table_name} e
            LEFT JOIN spec_geometry_links l
                ON e.{id_column}::TEXT = l.entity_id::TEXT
                AND l.entity_type = %s
                AND l.is_active = TRUE
            WHERE e.project_id = %s
                AND l.link_id IS NULL
            ORDER BY e.{id_column}
        """

        return execute_query(query, (entity_type, project_id))
