"""
Coordinate System Service
Centralized management of coordinate reference systems and transformations

This service provides:
- Project CRS lookup and management
- Coordinate transformations between any two systems
- Cached transformers for performance
- Support for all California State Plane zones (with architecture for future expansion)
"""

from typing import Dict, Optional, Tuple, List
from pyproj import Transformer
import psycopg2
from psycopg2.extras import RealDictCursor


class CoordinateSystemService:
    """Manages coordinate systems and transformations for projects"""

    def __init__(self, db_config: Dict):
        """
        Initialize the coordinate system service.

        Args:
            db_config: Database connection parameters dict
        """
        self.db_config = db_config
        self._transformer_cache = {}

    def get_project_crs(self, project_id: str, conn=None) -> Dict:
        """
        Get the canonical coordinate system for a project.

        Args:
            project_id: UUID of the project
            conn: Optional database connection (if None, creates a new one)

        Returns:
            Dict with keys: system_id, epsg_code, system_name, units, datum, etc.

        Raises:
            ValueError: If no coordinate system found for the project
        """
        should_close = False
        if conn is None:
            conn = psycopg2.connect(**self.db_config)
            should_close = True

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT
                        cs.system_id,
                        cs.epsg_code,
                        cs.system_name,
                        cs.region,
                        cs.datum,
                        cs.units,
                        cs.zone_number
                    FROM projects p
                    JOIN coordinate_systems cs ON p.default_coordinate_system_id = cs.system_id
                    WHERE p.project_id = %s
                """, (project_id,))

                result = cur.fetchone()
                if not result:
                    raise ValueError(f"No coordinate system found for project {project_id}")

                return dict(result)
        finally:
            if should_close:
                conn.close()

    def get_coordinate_system_by_epsg(self, epsg_code: str, conn=None) -> Optional[Dict]:
        """
        Get coordinate system info by EPSG code.

        Args:
            epsg_code: EPSG code (e.g., 'EPSG:2226')
            conn: Optional database connection

        Returns:
            Dict with coordinate system info or None if not found
        """
        should_close = False
        if conn is None:
            conn = psycopg2.connect(**self.db_config)
            should_close = True

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT
                        system_id,
                        epsg_code,
                        system_name,
                        region,
                        datum,
                        units,
                        zone_number
                    FROM coordinate_systems
                    WHERE epsg_code = %s AND is_active = true
                """, (epsg_code,))

                result = cur.fetchone()
                return dict(result) if result else None
        finally:
            if should_close:
                conn.close()

    def get_coordinate_system_by_id(self, system_id: str, conn=None) -> Optional[Dict]:
        """
        Get coordinate system info by system_id.

        Args:
            system_id: UUID of the coordinate system
            conn: Optional database connection

        Returns:
            Dict with coordinate system info or None if not found
        """
        should_close = False
        if conn is None:
            conn = psycopg2.connect(**self.db_config)
            should_close = True

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT
                        system_id,
                        epsg_code,
                        system_name,
                        region,
                        datum,
                        units,
                        zone_number
                    FROM coordinate_systems
                    WHERE system_id = %s AND is_active = true
                """, (system_id,))

                result = cur.fetchone()
                return dict(result) if result else None
        finally:
            if should_close:
                conn.close()

    def get_all_california_systems(self, conn=None) -> List[Dict]:
        """
        Get all California State Plane zones for UI dropdowns.

        Args:
            conn: Optional database connection

        Returns:
            List of coordinate system dictionaries, ordered by zone number
        """
        should_close = False
        if conn is None:
            conn = psycopg2.connect(**self.db_config)
            should_close = True

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT
                        system_id,
                        epsg_code,
                        system_name,
                        region,
                        datum,
                        units,
                        zone_number
                    FROM coordinate_systems
                    WHERE region LIKE '%California%'
                      AND is_active = true
                    ORDER BY zone_number
                """)

                return [dict(row) for row in cur.fetchall()]
        finally:
            if should_close:
                conn.close()

    def get_all_active_systems(self, conn=None) -> List[Dict]:
        """
        Get all active coordinate systems.

        Args:
            conn: Optional database connection

        Returns:
            List of coordinate system dictionaries
        """
        should_close = False
        if conn is None:
            conn = psycopg2.connect(**self.db_config)
            should_close = True

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT
                        system_id,
                        epsg_code,
                        system_name,
                        region,
                        datum,
                        units,
                        zone_number
                    FROM coordinate_systems
                    WHERE is_active = true
                    ORDER BY system_name
                """)

                return [dict(row) for row in cur.fetchall()]
        finally:
            if should_close:
                conn.close()

    def get_transformer(self, from_epsg: str, to_epsg: str) -> Transformer:
        """
        Get a cached pyproj Transformer for coordinate transformations.

        This method caches transformers for performance - creating transformers
        is expensive, so we reuse them whenever possible.

        Args:
            from_epsg: Source EPSG code (e.g., 'EPSG:4326')
            to_epsg: Target EPSG code (e.g., 'EPSG:2226')

        Returns:
            pyproj.Transformer instance (cached for performance)
        """
        # Normalize EPSG codes to ensure consistent cache keys
        from_epsg = from_epsg.upper()
        to_epsg = to_epsg.upper()

        cache_key = f"{from_epsg}→{to_epsg}"

        if cache_key not in self._transformer_cache:
            self._transformer_cache[cache_key] = Transformer.from_crs(
                from_epsg, to_epsg, always_xy=True
            )

        return self._transformer_cache[cache_key]

    def transform_point(self, x: float, y: float, from_epsg: str, to_epsg: str) -> Tuple[float, float]:
        """
        Transform a single point between coordinate systems.

        Args:
            x: X coordinate (or longitude)
            y: Y coordinate (or latitude)
            from_epsg: Source EPSG code
            to_epsg: Target EPSG code

        Returns:
            Tuple of (x, y) in target coordinate system
        """
        transformer = self.get_transformer(from_epsg, to_epsg)
        return transformer.transform(x, y)

    def transform_to_project_crs(self, x: float, y: float, source_epsg: str, project_id: str, conn=None) -> Tuple[float, float]:
        """
        Transform coordinates into a project's canonical CRS.

        Args:
            x: X coordinate (or longitude)
            y: Y coordinate (or latitude)
            source_epsg: Source EPSG code
            project_id: UUID of the project
            conn: Optional database connection

        Returns:
            Tuple of (x, y) in project's coordinate system
        """
        project_crs = self.get_project_crs(project_id, conn)
        return self.transform_point(x, y, source_epsg, project_crs['epsg_code'])

    def transform_from_project_crs(self, x: float, y: float, target_epsg: str, project_id: str, conn=None) -> Tuple[float, float]:
        """
        Transform coordinates from a project's canonical CRS to another system.

        Args:
            x: X coordinate in project CRS
            y: Y coordinate in project CRS
            target_epsg: Target EPSG code
            project_id: UUID of the project
            conn: Optional database connection

        Returns:
            Tuple of (x, y) in target coordinate system
        """
        project_crs = self.get_project_crs(project_id, conn)
        return self.transform_point(x, y, project_crs['epsg_code'], target_epsg)

    def set_project_crs(self, project_id: str, system_id: str, conn=None) -> bool:
        """
        Set the default coordinate system for a project.

        Args:
            project_id: UUID of the project
            system_id: UUID of the coordinate system
            conn: Optional database connection

        Returns:
            True if successful

        Raises:
            Exception: If update fails
        """
        should_close = False
        if conn is None:
            conn = psycopg2.connect(**self.db_config)
            should_close = True

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE projects
                    SET default_coordinate_system_id = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE project_id = %s
                """, (system_id, project_id))

                if not conn.autocommit:
                    conn.commit()

                return cur.rowcount > 0
        finally:
            if should_close:
                conn.close()

    def clear_transformer_cache(self):
        """
        Clear the transformer cache.

        Useful if you need to free up memory or force recreation of transformers.
        """
        self._transformer_cache.clear()
