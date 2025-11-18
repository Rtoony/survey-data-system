"""
CSI MasterFormat Service
Handles CSI code hierarchy queries and management
"""

from typing import List, Dict, Optional, Any
from db import execute_query


class CSIMasterformatService:
    """Service for CSI MasterFormat taxonomy operations"""

    @staticmethod
    def get_all_codes(filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get all CSI codes with optional filters

        Args:
            filters: Optional filters:
                - division: Filter by division number
                - level: Filter by hierarchy level (1, 2, 3)
                - is_civil_engineering: Filter for civil codes only
                - is_active: Filter active codes

        Returns:
            List of CSI codes
        """
        filters = filters or {}

        where_clauses = []
        params = []

        if filters.get('division') is not None:
            where_clauses.append("division = %s")
            params.append(filters['division'])

        if filters.get('level') is not None:
            where_clauses.append("level = %s")
            params.append(filters['level'])

        if filters.get('is_civil_engineering') is not None:
            where_clauses.append("is_civil_engineering = %s")
            params.append(filters['is_civil_engineering'])

        if filters.get('is_active') is not None:
            where_clauses.append("is_active = %s")
            params.append(filters['is_active'])

        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        query = f"""
            SELECT *
            FROM csi_masterformat
            {where_sql}
            ORDER BY csi_code
        """

        return execute_query(query, tuple(params) if params else None)

    @staticmethod
    def get_by_code(csi_code: str) -> Optional[Dict[str, Any]]:
        """Get a single CSI code by its code"""
        query = "SELECT * FROM csi_masterformat WHERE csi_code = %s"
        result = execute_query(query, (csi_code,))
        return result[0] if result else None

    @staticmethod
    def get_divisions(civil_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get all top-level divisions

        Args:
            civil_only: If True, return only civil engineering divisions

        Returns:
            List of division-level CSI codes
        """
        where_clause = "WHERE level = 1"

        if civil_only:
            where_clause += " AND is_civil_engineering = TRUE"

        query = f"""
            SELECT *
            FROM csi_masterformat
            {where_clause}
            ORDER BY division
        """

        return execute_query(query)

    @staticmethod
    def get_children(parent_code: str) -> List[Dict[str, Any]]:
        """
        Get direct children of a CSI code

        Args:
            parent_code: Parent CSI code (e.g., '33 00 00')

        Returns:
            List of child CSI codes
        """
        query = """
            SELECT *
            FROM csi_masterformat
            WHERE parent_code = %s
            ORDER BY csi_code
        """

        return execute_query(query, (parent_code,))

    @staticmethod
    def get_children_recursive(parent_code: str) -> List[Dict[str, Any]]:
        """
        Get all descendants of a CSI code (recursive)

        Args:
            parent_code: Parent CSI code

        Returns:
            List of all descendant CSI codes
        """
        query = "SELECT * FROM get_csi_children(%s)"
        return execute_query(query, (parent_code,))

    @staticmethod
    def get_hierarchy_tree(division: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get hierarchical tree structure

        Args:
            division: Optional division filter

        Returns:
            Nested structure of CSI codes
        """
        where_clause = ""
        params = []

        if division is not None:
            where_clause = "WHERE division = %s OR division IS NULL"
            params.append(division)

        query = f"""
            WITH RECURSIVE csi_tree AS (
                -- Level 1: Divisions
                SELECT
                    csi_code,
                    csi_title,
                    division,
                    section,
                    subsection,
                    parent_code,
                    level,
                    description,
                    is_civil_engineering,
                    ARRAY[csi_code] as path,
                    0 as depth
                FROM csi_masterformat
                WHERE level = 1 {('AND division = %s' if division is not None else '')}

                UNION ALL

                -- Recursive: All children
                SELECT
                    m.csi_code,
                    m.csi_title,
                    m.division,
                    m.section,
                    m.subsection,
                    m.parent_code,
                    m.level,
                    m.description,
                    m.is_civil_engineering,
                    t.path || m.csi_code,
                    t.depth + 1
                FROM csi_masterformat m
                INNER JOIN csi_tree t ON m.parent_code = t.csi_code
            )
            SELECT * FROM csi_tree
            ORDER BY path
        """

        return execute_query(query, (division,) if division is not None else None)

    @staticmethod
    def get_civil_engineering_codes() -> List[Dict[str, Any]]:
        """Get all civil engineering related CSI codes"""
        query = """
            SELECT *
            FROM csi_masterformat
            WHERE is_civil_engineering = TRUE
            ORDER BY csi_code
        """

        return execute_query(query)

    @staticmethod
    def search_codes(search_term: str, civil_only: bool = False) -> List[Dict[str, Any]]:
        """
        Search CSI codes by code or title

        Args:
            search_term: Search string
            civil_only: Limit to civil engineering codes

        Returns:
            Matching CSI codes
        """
        where_clauses = [
            "(csi_code ILIKE %s OR csi_title ILIKE %s OR description ILIKE %s)"
        ]

        search_pattern = f"%{search_term}%"
        params = [search_pattern, search_pattern, search_pattern]

        if civil_only:
            where_clauses.append("is_civil_engineering = TRUE")

        where_sql = " AND ".join(where_clauses)

        query = f"""
            SELECT *
            FROM csi_masterformat
            WHERE {where_sql}
            ORDER BY
                CASE
                    WHEN csi_code ILIKE %s THEN 1
                    WHEN csi_title ILIKE %s THEN 2
                    ELSE 3
                END,
                csi_code
            LIMIT 50
        """

        params.extend([f"{search_term}%", f"{search_term}%"])

        return execute_query(query, tuple(params))

    @staticmethod
    def get_specs_by_csi_code(csi_code: str, include_children: bool = False) -> List[Dict[str, Any]]:
        """
        Get all specs associated with a CSI code

        Args:
            csi_code: CSI code
            include_children: If True, include specs from child codes

        Returns:
            List of specs
        """
        if include_children:
            # Get all child codes
            child_codes = CSIMasterformatService.get_children_recursive(csi_code)
            code_list = [csi_code] + [c['csi_code'] for c in child_codes]

            query = """
                SELECT
                    s.*,
                    ss.standard_name,
                    ss.abbreviation,
                    cm.csi_title
                FROM spec_library s
                LEFT JOIN spec_standards ss ON s.spec_standard_id = ss.spec_standard_id
                LEFT JOIN csi_masterformat cm ON s.csi_code = cm.csi_code
                WHERE s.csi_code = ANY(%s)
                ORDER BY s.spec_number
            """

            return execute_query(query, (code_list,))
        else:
            query = """
                SELECT
                    s.*,
                    ss.standard_name,
                    ss.abbreviation,
                    cm.csi_title
                FROM spec_library s
                LEFT JOIN spec_standards ss ON s.spec_standard_id = ss.spec_standard_id
                LEFT JOIN csi_masterformat cm ON s.csi_code = cm.csi_code
                WHERE s.csi_code = %s
                ORDER BY s.spec_number
            """

            return execute_query(query, (csi_code,))

    @staticmethod
    def get_usage_statistics(csi_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Get usage statistics for CSI codes

        Args:
            csi_code: Optional specific code, otherwise overall stats

        Returns:
            Usage statistics
        """
        if csi_code:
            query = """
                SELECT
                    cm.csi_code,
                    cm.csi_title,
                    COUNT(DISTINCT s.spec_library_id) as spec_count,
                    COUNT(DISTINCT l.link_id) as link_count,
                    COUNT(DISTINCT l.entity_id) as entity_count,
                    COUNT(DISTINCT l.project_id) as project_count
                FROM csi_masterformat cm
                LEFT JOIN spec_library s ON cm.csi_code = s.csi_code
                LEFT JOIN spec_geometry_links l ON s.spec_library_id = l.spec_library_id
                    AND l.is_active = TRUE
                WHERE cm.csi_code = %s
                GROUP BY cm.csi_code, cm.csi_title
            """

            result = execute_query(query, (csi_code,))
            return result[0] if result else {}
        else:
            query = """
                SELECT
                    cm.division,
                    COUNT(DISTINCT cm.csi_code) as code_count,
                    COUNT(DISTINCT s.spec_library_id) as spec_count,
                    COUNT(DISTINCT l.link_id) as link_count,
                    COUNT(DISTINCT l.entity_id) as entity_count
                FROM csi_masterformat cm
                LEFT JOIN spec_library s ON cm.csi_code = s.csi_code
                LEFT JOIN spec_geometry_links l ON s.spec_library_id = l.spec_library_id
                    AND l.is_active = TRUE
                WHERE cm.level = 1
                GROUP BY cm.division
                ORDER BY cm.division
            """

            return execute_query(query)

    @staticmethod
    def create_custom_code(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a custom CSI-style code (for organization-specific needs)

        Args:
            data: Code definition

        Returns:
            Created code record
        """
        query = """
            INSERT INTO csi_masterformat (
                csi_code, csi_title, division, section, subsection,
                parent_code, level, description, notes, is_civil_engineering, is_active
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """

        params = (
            data['csi_code'],
            data['csi_title'],
            data.get('division'),
            data.get('section'),
            data.get('subsection'),
            data.get('parent_code'),
            data['level'],
            data.get('description'),
            data.get('notes'),
            data.get('is_civil_engineering', True),
            data.get('is_active', True)
        )

        result = execute_query(query, params)
        return result[0] if result else None

    @staticmethod
    def update_code(csi_code: str, data: Dict[str, Any]) -> bool:
        """Update a CSI code (mainly for custom codes)"""
        allowed_fields = ['csi_title', 'description', 'notes', 'is_active']

        update_fields = []
        params = []

        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                params.append(data[field])

        if not update_fields:
            return False

        params.append(csi_code)

        query = f"""
            UPDATE csi_masterformat
            SET {', '.join(update_fields)}, updated_at = NOW()
            WHERE csi_code = %s
            RETURNING csi_code
        """

        result = execute_query(query, tuple(params))
        return len(result) > 0

    @staticmethod
    def get_breadcrumb(csi_code: str) -> List[Dict[str, Any]]:
        """
        Get breadcrumb trail for a CSI code (all ancestors)

        Args:
            csi_code: CSI code to get trail for

        Returns:
            List of ancestor codes from root to current
        """
        query = """
            WITH RECURSIVE breadcrumb AS (
                -- Start with the requested code
                SELECT
                    csi_code,
                    csi_title,
                    parent_code,
                    level,
                    1 as depth
                FROM csi_masterformat
                WHERE csi_code = %s

                UNION ALL

                -- Add parents recursively
                SELECT
                    m.csi_code,
                    m.csi_title,
                    m.parent_code,
                    m.level,
                    b.depth + 1
                FROM csi_masterformat m
                INNER JOIN breadcrumb b ON m.csi_code = b.parent_code
            )
            SELECT csi_code, csi_title, level
            FROM breadcrumb
            ORDER BY depth DESC
        """

        return execute_query(query, (csi_code,))
