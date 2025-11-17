"""
GIS Snapshot Service
Handles importing GIS data from external services (ArcGIS REST, WFS, GeoJSON)

This service:
- Fetches data from external GIS services
- Transforms coordinates to project CRS
- Maps attributes to canonical database columns
- Tracks provenance in snapshot_metadata
"""

import requests
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from services.coordinate_system_service import CoordinateSystemService


class GISSnapshotService:
    """Handles importing GIS data from external services"""

    def __init__(self, db_config: Dict):
        """
        Initialize the GIS snapshot service.

        Args:
            db_config: Database connection parameters dict
        """
        self.db_config = db_config
        self.crs_service = CoordinateSystemService(db_config)

    def execute_snapshot(self, snapshot_id: str, project_id: str) -> Dict:
        """
        Execute a GIS snapshot import.

        Args:
            snapshot_id: UUID of the snapshot to execute
            project_id: UUID of the project

        Returns:
            Dict with status and results
        """
        conn = None
        try:
            # Connect to database
            conn = psycopg2.connect(**self.db_config)
            conn.autocommit = False

            # 1. Get snapshot + layer metadata
            snapshot_info = self._get_snapshot_info(snapshot_id, project_id, conn)
            if not snapshot_info:
                raise ValueError(f"Snapshot {snapshot_id} not found for project {project_id}")

            # Update status to processing
            self._update_snapshot_status(snapshot_id, 'processing', conn)

            # 2. Calculate project boundary with buffer
            boundary_wkt = self._calculate_project_boundary(project_id, buffer_feet=500, conn=conn)

            if not boundary_wkt:
                raise ValueError(f"Project {project_id} has no spatial data to define boundary")

            # Update snapshot boundary
            self._update_snapshot_boundary(snapshot_id, boundary_wkt, conn)

            # 3. Fetch data from external service
            service_type = snapshot_info['service_type']
            service_url = snapshot_info['service_url']

            if service_type == 'arcgis_rest':
                features = self._fetch_arcgis_features(service_url, boundary_wkt, conn)
            elif service_type == 'geojson_url':
                features = self._fetch_geojson_features(service_url, boundary_wkt)
            else:
                raise ValueError(f"Unsupported service type: {service_type}")

            # 4. Import features into target table
            entity_count = self._import_features(
                features=features,
                target_table=snapshot_info['target_table_name'],
                attribute_mapping=snapshot_info['attribute_mapping'],
                snapshot_id=snapshot_id,
                project_id=project_id,
                conn=conn
            )

            # 5. Update snapshot record
            self._update_snapshot_complete(snapshot_id, entity_count, conn)

            # Commit transaction
            conn.commit()

            return {
                'status': 'completed',
                'entity_count': entity_count,
                'snapshot_id': snapshot_id
            }

        except Exception as e:
            if conn:
                conn.rollback()
            # Update snapshot to failed status
            if conn:
                self._update_snapshot_failed(snapshot_id, str(e), conn)
                conn.commit()
            raise e

        finally:
            if conn:
                conn.close()

    def _get_snapshot_info(self, snapshot_id: str, project_id: str, conn) -> Optional[Dict]:
        """Get snapshot and layer metadata"""
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    pgs.snapshot_id,
                    pgs.project_id,
                    gdl.layer_id,
                    gdl.layer_name,
                    gdl.service_url,
                    gdl.service_type,
                    gdl.target_entity_type,
                    gdl.target_table_name,
                    gdl.attribute_mapping
                FROM project_gis_snapshots pgs
                JOIN gis_data_layers gdl ON pgs.gis_data_layer_id = gdl.layer_id
                WHERE pgs.snapshot_id = %s AND pgs.project_id = %s
            """, (snapshot_id, project_id))

            result = cur.fetchone()
            return dict(result) if result else None

    def _calculate_project_boundary(self, project_id: str, buffer_feet: float = 500, conn=None) -> Optional[str]:
        """
        Calculate buffered project extent in SRID 2226.

        Args:
            project_id: UUID of the project
            buffer_feet: Buffer distance in feet
            conn: Database connection

        Returns:
            WKT string of buffered boundary or None if no geometries found
        """
        should_close = False
        if conn is None:
            conn = psycopg2.connect(**self.db_config)
            should_close = True

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT ST_AsText(
                        ST_Buffer(
                            ST_ConvexHull(ST_Collect(geometry)),
                            %s
                        )
                    ) as boundary
                    FROM drawing_entities
                    WHERE project_id = %s
                      AND geometry IS NOT NULL
                      AND ST_SRID(geometry) = 2226
                    HAVING COUNT(*) > 0
                """, (buffer_feet, project_id))

                result = cur.fetchone()
                return result['boundary'] if result else None

        finally:
            if should_close:
                conn.close()

    def _update_snapshot_status(self, snapshot_id: str, status: str, conn):
        """Update snapshot status"""
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE project_gis_snapshots
                SET snapshot_status = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE snapshot_id = %s
            """, (status, snapshot_id))

    def _update_snapshot_boundary(self, snapshot_id: str, boundary_wkt: str, conn):
        """Update snapshot boundary"""
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE project_gis_snapshots
                SET snapshot_boundary = ST_GeomFromText(%s, 2226)
                WHERE snapshot_id = %s
            """, (boundary_wkt, snapshot_id))

    def _update_snapshot_complete(self, snapshot_id: str, entity_count: int, conn):
        """Mark snapshot as completed"""
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE project_gis_snapshots
                SET snapshot_status = 'completed',
                    last_snapshot_at = CURRENT_TIMESTAMP,
                    entity_count = %s,
                    error_message = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE snapshot_id = %s
            """, (entity_count, snapshot_id))

    def _update_snapshot_failed(self, snapshot_id: str, error_message: str, conn):
        """Mark snapshot as failed"""
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE project_gis_snapshots
                SET snapshot_status = 'failed',
                    error_message = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE snapshot_id = %s
            """, (error_message, snapshot_id))

    def _fetch_arcgis_features(self, service_url: str, boundary_wkt: str, conn) -> List[Dict]:
        """
        Fetch features from ArcGIS REST service within boundary.

        Args:
            service_url: ArcGIS REST endpoint URL
            boundary_wkt: WKT string of search boundary (SRID 2226)
            conn: Database connection

        Returns:
            List of GeoJSON-like feature dicts
        """
        # Convert boundary to WGS84 for ArcGIS query
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT ST_AsGeoJSON(
                    ST_Transform(
                        ST_GeomFromText(%s, 2226),
                        4326
                    )
                ) as geojson
            """, (boundary_wkt,))

            result = cur.fetchone()
            boundary_geojson = json.loads(result['geojson'])

        # Build ArcGIS query URL
        query_params = {
            'where': '1=1',
            'geometry': json.dumps(boundary_geojson),
            'geometryType': 'esriGeometryPolygon',
            'spatialRel': 'esriSpatialRelIntersects',
            'outFields': '*',
            'returnGeometry': 'true',
            'f': 'geojson',
            'inSR': '4326',
            'outSR': '4326'
        }

        # Make request
        response = requests.get(f"{service_url}/query", params=query_params, timeout=60)
        response.raise_for_status()

        data = response.json()

        # Return features in GeoJSON format
        if 'features' in data:
            return data['features']
        else:
            return []

    def _fetch_geojson_features(self, service_url: str, boundary_wkt: str) -> List[Dict]:
        """
        Fetch features from a GeoJSON URL and filter by boundary.

        Args:
            service_url: URL to GeoJSON file
            boundary_wkt: WKT string of search boundary (SRID 2226)

        Returns:
            List of GeoJSON features
        """
        # Fetch GeoJSON
        response = requests.get(service_url, timeout=60)
        response.raise_for_status()

        data = response.json()

        # For MVP, return all features
        # TODO: Implement spatial filtering
        if 'features' in data:
            return data['features']
        else:
            return []

    def _import_features(
        self,
        features: List[Dict],
        target_table: str,
        attribute_mapping: Dict,
        snapshot_id: str,
        project_id: str,
        conn
    ) -> int:
        """
        Import features into target table.

        Args:
            features: List of GeoJSON features
            target_table: Target database table name
            attribute_mapping: Dict mapping source fields to target columns
            snapshot_id: UUID of snapshot
            project_id: UUID of project
            conn: Database connection

        Returns:
            Number of features imported
        """
        if not features:
            return 0

        # First, delete existing entities from this snapshot
        with conn.cursor() as cur:
            cur.execute(f"""
                DELETE FROM {target_table}
                WHERE project_id = %s
                  AND snapshot_metadata->>'snapshot_id' = %s
            """, (project_id, snapshot_id))

        imported_count = 0

        with conn.cursor() as cur:
            for feature in features:
                try:
                    # Extract geometry
                    geometry = feature.get('geometry')
                    properties = feature.get('properties', {})

                    if not geometry:
                        continue

                    # Convert GeoJSON geometry to WKT in WGS84, then transform to SRID 2226
                    geometry_json = json.dumps(geometry)

                    # Map attributes using attribute_mapping
                    mapped_attrs = {}
                    for source_field, target_column in attribute_mapping.items():
                        if source_field in properties:
                            mapped_attrs[target_column] = properties[source_field]

                    # Build snapshot metadata
                    snapshot_metadata = {
                        'snapshot_id': snapshot_id,
                        'source_gis_object_id': properties.get('OBJECTID') or properties.get('FID') or properties.get('id'),
                        'imported_at': datetime.utcnow().isoformat(),
                        'source_layer': 'GIS Import'
                    }

                    # Build insert query dynamically based on target table
                    if target_table == 'parcels':
                        self._insert_parcel(
                            cur, project_id, geometry_json, mapped_attrs, snapshot_metadata
                        )
                    elif target_table == 'utility_lines':
                        self._insert_utility_line(
                            cur, project_id, geometry_json, mapped_attrs, snapshot_metadata
                        )
                    elif target_table == 'utility_structures':
                        self._insert_utility_structure(
                            cur, project_id, geometry_json, mapped_attrs, snapshot_metadata
                        )
                    else:
                        # Skip unsupported tables
                        continue

                    imported_count += 1

                except Exception as e:
                    # Log error but continue with other features
                    print(f"Error importing feature: {e}")
                    continue

        return imported_count

    def _insert_parcel(self, cur, project_id: str, geometry_json: str, attrs: Dict, metadata: Dict):
        """Insert a parcel feature"""
        cur.execute("""
            INSERT INTO parcels (
                project_id,
                parcel_number,
                owner_name,
                legal_description,
                area_acres,
                address,
                geometry,
                snapshot_metadata
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                ST_Transform(ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326), 2226),
                %s
            )
        """, (
            project_id,
            attrs.get('parcel_number'),
            attrs.get('owner_name'),
            attrs.get('legal_description'),
            attrs.get('area_acres'),
            attrs.get('address'),
            geometry_json,
            json.dumps(metadata)
        ))

    def _insert_utility_line(self, cur, project_id: str, geometry_json: str, attrs: Dict, metadata: Dict):
        """Insert a utility line feature"""
        cur.execute("""
            INSERT INTO utility_lines (
                project_id,
                utility_type,
                material,
                diameter_inches,
                geometry,
                snapshot_metadata
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                ST_Transform(ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326), 2226),
                %s
            )
        """, (
            project_id,
            attrs.get('utility_type'),
            attrs.get('material'),
            attrs.get('diameter_inches'),
            geometry_json,
            json.dumps(metadata)
        ))

    def _insert_utility_structure(self, cur, project_id: str, geometry_json: str, attrs: Dict, metadata: Dict):
        """Insert a utility structure feature"""
        cur.execute("""
            INSERT INTO utility_structures (
                project_id,
                structure_type,
                material,
                geometry,
                snapshot_metadata
            )
            VALUES (
                %s,
                %s,
                %s,
                ST_Transform(ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326), 2226),
                %s
            )
        """, (
            project_id,
            attrs.get('structure_type'),
            attrs.get('material'),
            geometry_json,
            json.dumps(metadata)
        ))
