"""
Classification Service
Handles entity classification, reclassification, and review workflows.

This service manages the lifecycle of entity classification in the new
standards_entities-based system, replacing the old generic_objects approach.
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional
import json
from datetime import datetime


class ClassificationService:
    """Service for managing entity classification lifecycle."""

    def __init__(self, db_config: Dict, conn=None):
        self.db_config = db_config
        self.conn = conn
        self.should_close = conn is None

    def get_review_queue(self, project_id: Optional[str] = None,
                        min_confidence: float = 0.0,
                        max_confidence: float = 1.0,
                        geometry_types: Optional[List[str]] = None,
                        limit: int = 100) -> List[Dict]:
        """
        Get entities needing review with enriched context.

        Args:
            project_id: Filter by project (optional)
            min_confidence: Minimum classification confidence
            max_confidence: Maximum classification confidence
            geometry_types: Filter by geometry types (optional)
            limit: Maximum number of results

        Returns:
            List of entity dicts with classification metadata
        """
        if not self.conn:
            self.conn = psycopg2.connect(**self.db_config)

        try:
            cur = self.conn.cursor(cursor_factory=RealDictCursor)

            # Build dynamic WHERE clause
            where_conditions = ["se.classification_state = 'needs_review'"]
            params = []

            if project_id:
                where_conditions.append("se.project_id = %s")
                params.append(project_id)

            where_conditions.append("se.classification_confidence BETWEEN %s AND %s")
            params.extend([min_confidence, max_confidence])

            where_clause = " AND ".join(where_conditions)

            query = f"""
                SELECT
                    se.entity_id,
                    se.entity_type,
                    se.source_table,
                    se.canonical_name,
                    se.classification_state,
                    se.classification_confidence,
                    se.classification_metadata,
                    se.target_table,
                    se.target_id,
                    se.project_id,
                    de.layer_name,
                    de.entity_type as dxf_entity_type,
                    ST_AsText(de.geometry) as geometry_wkt,
                    ST_GeometryType(de.geometry) as geometry_type
                FROM standards_entities se
                LEFT JOIN drawing_entities de ON se.entity_id = de.entity_id
                WHERE {where_clause}
                ORDER BY se.classification_confidence ASC
                LIMIT %s
            """
            params.append(limit)

            cur.execute(query, params)
            results = cur.fetchall()

            # Convert to list of dicts
            entities = []
            for row in results:
                entity_dict = dict(row)
                entities.append(entity_dict)

            return entities

        finally:
            if self.should_close and self.conn:
                self.conn.close()

    def reclassify_entity(self, entity_id: str, new_type: str,
                         user_notes: Optional[str] = None) -> Dict:
        """
        Reclassify an entity to a different type.
        Moves data from source table to target table.

        Args:
            entity_id: UUID of entity to reclassify
            new_type: New object type code
            user_notes: Optional notes about the reclassification

        Returns:
            Dict with success status and details
        """
        if not self.conn:
            self.conn = psycopg2.connect(**self.db_config)

        try:
            cur = self.conn.cursor(cursor_factory=RealDictCursor)

            # Get current entity info
            cur.execute("""
                SELECT * FROM standards_entities WHERE entity_id = %s
            """, (entity_id,))
            entity = cur.fetchone()

            if not entity:
                raise ValueError(f"Entity {entity_id} not found")

            old_type = entity['entity_type']
            old_table = entity['target_table']

            # Import entity registry to get new table
            from services.entity_registry import EntityRegistry
            new_table, new_pk = EntityRegistry.get_table_and_pk(new_type)

            # If same type, just update state
            if old_table == new_table:
                metadata = json.loads(entity['classification_metadata'] or '{}')
                metadata.update({
                    'user_notes': user_notes,
                    'reclassified_at': datetime.utcnow().isoformat()
                })

                cur.execute("""
                    UPDATE standards_entities
                    SET classification_state = 'user_classified',
                        classification_confidence = 1.0,
                        classification_metadata = %s
                    WHERE entity_id = %s
                """, (
                    json.dumps(metadata),
                    entity_id
                ))
                self.conn.commit()
                return {'success': True, 'action': 'confirmed'}

            # Different type - need to migrate data
            # Get geometry and project info from drawing_entities
            cur.execute("""
                SELECT * FROM drawing_entities WHERE entity_id = %s
            """, (entity_id,))
            drawing_entity = cur.fetchone()

            if not drawing_entity:
                raise ValueError("No drawing_entities record found")

            # Delete from old table (if exists)
            if old_table and entity['target_id']:
                old_pk_field = EntityRegistry.get_table_and_pk(old_type)[1]
                cur.execute(f"DELETE FROM {old_table} WHERE {old_pk_field} = %s",
                           (entity['target_id'],))

            # Create in new table using IntelligentObjectCreator
            from intelligent_object_creator import IntelligentObjectCreator
            from layer_classifier import LayerClassification

            entity_data = {
                'layer_name': drawing_entity['layer_name'],
                'entity_type': drawing_entity['entity_type'],
                'geometry_wkt': str(drawing_entity.get('geometry')),  # WKT from geometry
                'geometry_type': str(drawing_entity.get('geometry_type', '')),
                'dxf_handle': drawing_entity.get('dxf_handle', ''),
                'attributes': drawing_entity.get('attributes', {})
            }

            # Get geometry as WKT
            cur.execute("""
                SELECT ST_AsText(geometry) as wkt FROM drawing_entities WHERE entity_id = %s
            """, (entity_id,))
            geom_result = cur.fetchone()
            if geom_result:
                entity_data['geometry_wkt'] = geom_result['wkt']

            # Mock high-confidence classification
            classification = LayerClassification(
                object_type=new_type,
                confidence=1.0,
                properties={},
                network_mode=None
            )

            creator = IntelligentObjectCreator(self.db_config, conn=self.conn)

            # Call appropriate create method based on new_type
            result = None
            if new_type == 'utility_line':
                result = creator._create_utility_line(entity_data, classification, drawing_entity['project_id'])
            elif new_type == 'utility_structure':
                result = creator._create_utility_structure(entity_data, classification, drawing_entity['project_id'])
            elif new_type == 'bmp':
                result = creator._create_bmp(entity_data, classification, drawing_entity['project_id'])
            elif new_type == 'survey_point':
                result = creator._create_survey_point(entity_data, classification, drawing_entity['project_id'])
            elif new_type == 'site_tree':
                result = creator._create_site_tree(entity_data, classification, drawing_entity['project_id'])
            elif new_type == 'parcel':
                result = creator._create_parcel(entity_data, classification, drawing_entity['project_id'])
            elif new_type == 'grading_feature':
                result = creator._create_grading_feature(entity_data, classification, drawing_entity['project_id'])
            elif new_type in ['surface_feature', 'ada_feature']:
                result = creator._create_surface_feature(entity_data, classification, drawing_entity['project_id'])
            elif new_type == 'street_light':
                result = creator._create_street_light(entity_data, classification, drawing_entity['project_id'])
            elif new_type == 'pavement_zone':
                result = creator._create_pavement_zone(entity_data, classification, drawing_entity['project_id'])
            elif new_type == 'service_connection':
                result = creator._create_service_connection(entity_data, classification, drawing_entity['project_id'])
            # Add other types as needed

            if not result:
                raise ValueError(f"Failed to create {new_type} record")

            new_object_type, new_object_id, new_table_name = result

            # Update standards_entities
            metadata = json.loads(entity['classification_metadata'] or '{}')
            metadata.update({
                'reclassified_from': old_type,
                'reclassified_at': datetime.utcnow().isoformat(),
                'user_notes': user_notes
            })

            cur.execute("""
                UPDATE standards_entities
                SET entity_type = %s,
                    target_table = %s,
                    target_id = %s,
                    classification_state = 'user_classified',
                    classification_confidence = 1.0,
                    classification_metadata = %s
                WHERE entity_id = %s
            """, (
                new_type,
                new_table_name,
                new_object_id,
                json.dumps(metadata),
                entity_id
            ))

            self.conn.commit()

            return {
                'success': True,
                'action': 'reclassified',
                'old_type': old_type,
                'new_type': new_type,
                'new_id': new_object_id
            }

        except Exception as e:
            if self.conn:
                self.conn.rollback()
            raise
        finally:
            if self.should_close and self.conn:
                self.conn.close()

    def bulk_reclassify(self, entity_ids: List[str], new_type: str,
                       user_notes: Optional[str] = None) -> Dict:
        """
        Reclassify multiple entities at once.

        Args:
            entity_ids: List of entity UUIDs
            new_type: New object type for all entities
            user_notes: Optional notes

        Returns:
            Dict with success/failed counts and errors
        """
        results = {
            'success': 0,
            'failed': 0,
            'errors': []
        }

        for entity_id in entity_ids:
            try:
                self.reclassify_entity(entity_id, new_type, user_notes)
                results['success'] += 1
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'entity_id': entity_id,
                    'error': str(e)
                })

        return results
