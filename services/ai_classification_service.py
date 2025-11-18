"""
AI Classification Service
Provides intelligent classification suggestions using vector embeddings and similarity search.

Uses the existing entity_embeddings table and PostgreSQL pgvector extension
to find semantically similar entities and suggest classifications based on
what worked for similar entities in the past.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional
import json
from collections import defaultdict


class AIClassificationService:
    """Service for AI-powered classification suggestions using embeddings."""

    def __init__(self, db_config: Dict, conn=None):
        """
        Initialize AI Classification Service.

        Args:
            db_config: Database configuration dict
            conn: Optional existing database connection
        """
        self.db_config = db_config
        self.conn = conn
        self.should_close = conn is None

    def get_ai_suggestions(self, entity_id: str, limit: int = 5) -> List[Dict]:
        """
        Get AI-powered classification suggestions using embedding similarity.

        Finds similar entities that have been successfully classified (either
        auto-classified with high confidence or user-classified) and suggests
        their entity types as possibilities.

        Args:
            entity_id: UUID of entity needing classification
            limit: Maximum number of suggestions to return

        Returns:
            List of suggestion dicts with:
            - suggested_type: Object type code
            - confidence: Composite confidence score (0-1)
            - reason: Explanation of why this type is suggested
            - example_entity_id: UUID of similar entity
            - similarity_score: Vector similarity score
            - support_count: Number of similar entities with this type
        """
        if not self.conn:
            self.conn = psycopg2.connect(**self.db_config)

        try:
            cur = self.conn.cursor(cursor_factory=RealDictCursor)

            # Check if entity has embedding
            cur.execute("""
                SELECT embedding
                FROM entity_embeddings
                WHERE entity_id = %s AND is_current = TRUE
            """, (entity_id,))

            embedding_row = cur.fetchone()

            if not embedding_row or not embedding_row['embedding']:
                # No embedding available - return empty suggestions
                return []

            # Use PostgreSQL's vector similarity search to find similar entities
            # that have been successfully classified
            cur.execute("""
                WITH similar_entities AS (
                    SELECT
                        se.entity_id,
                        se.entity_type,
                        se.classification_state,
                        se.classification_confidence,
                        se.target_table,
                        se.canonical_name,
                        de.layer_name,
                        1 - (ee.embedding <=> target_ee.embedding) as similarity
                    FROM entity_embeddings ee
                    JOIN standards_entities se ON ee.entity_id = se.entity_id
                    LEFT JOIN drawing_entities de ON se.entity_id = de.entity_id
                    CROSS JOIN (
                        SELECT embedding
                        FROM entity_embeddings
                        WHERE entity_id = %s AND is_current = TRUE
                    ) target_ee
                    WHERE ee.is_current = TRUE
                      AND se.entity_id != %s
                      AND se.classification_state IN ('auto_classified', 'user_classified')
                      AND se.classification_confidence >= 0.7
                      AND ee.embedding IS NOT NULL
                    ORDER BY ee.embedding <=> target_ee.embedding
                    LIMIT 100
                )
                SELECT
                    entity_id,
                    entity_type,
                    classification_state,
                    classification_confidence,
                    target_table,
                    canonical_name,
                    layer_name,
                    similarity
                FROM similar_entities
                WHERE similarity >= 0.6
                ORDER BY similarity DESC
            """, (entity_id, entity_id))

            similar = cur.fetchall()

            if not similar:
                return []

            # Aggregate suggestions by entity_type
            type_data = defaultdict(lambda: {
                'count': 0,
                'total_similarity': 0.0,
                'total_confidence': 0.0,
                'example_entity_id': None,
                'example_layer': None,
                'max_similarity': 0.0,
                'user_classified_count': 0
            })

            for row in similar:
                entity_type = row['entity_type']
                data = type_data[entity_type]

                data['count'] += 1
                data['total_similarity'] += row['similarity']
                data['total_confidence'] += row['classification_confidence']

                if row['similarity'] > data['max_similarity']:
                    data['max_similarity'] = row['similarity']
                    data['example_entity_id'] = row['entity_id']
                    data['example_layer'] = row['layer_name']

                if row['classification_state'] == 'user_classified':
                    data['user_classified_count'] += 1

            # Calculate composite scores and build suggestions
            suggestions = []

            for entity_type, data in type_data.items():
                count = data['count']
                avg_similarity = data['total_similarity'] / count
                avg_confidence = data['total_confidence'] / count
                user_ratio = data['user_classified_count'] / count

                # Composite score calculation:
                # - 50% weight: Average similarity to similar entities
                # - 25% weight: Average classification confidence of similar entities
                # - 15% weight: Support count (normalized, max at 20 entities)
                # - 10% weight: User validation ratio
                composite_score = (
                    avg_similarity * 0.50 +
                    avg_confidence * 0.25 +
                    min(count / 20.0, 1.0) * 0.15 +
                    user_ratio * 0.10
                )

                # Build reason string
                reason_parts = [f"Similar to {count} classified {entity_type}"]
                if data['user_classified_count'] > 0:
                    reason_parts.append(f"{data['user_classified_count']} user-verified")
                reason = ", ".join(reason_parts)

                suggestions.append({
                    'suggested_type': entity_type,
                    'confidence': round(composite_score, 3),
                    'reason': reason,
                    'example_entity_id': data['example_entity_id'],
                    'example_layer': data['example_layer'],
                    'similarity_score': round(avg_similarity, 3),
                    'support_count': count,
                    'user_verified_count': data['user_classified_count'],
                    'avg_classification_confidence': round(avg_confidence, 3)
                })

            # Sort by composite score descending
            suggestions.sort(key=lambda x: x['confidence'], reverse=True)

            return suggestions[:limit]

        finally:
            if self.should_close and self.conn:
                self.conn.close()

    def get_spatial_context(self, entity_id: str, search_radius_feet: float = 100.0) -> Dict:
        """
        Get spatial context about nearby features to help with classification.

        Args:
            entity_id: UUID of entity
            search_radius_feet: Search radius in feet (default 100)

        Returns:
            Dict with spatial context information:
            - nearby_types: List of entity types found nearby
            - nearby_layers: Common layer names nearby
            - network_hints: Detected network connectivity
            - density: Feature density in area
        """
        if not self.conn:
            self.conn = psycopg2.connect(**self.db_config)

        try:
            cur = self.conn.cursor(cursor_factory=RealDictCursor)

            # Get entity geometry
            cur.execute("""
                SELECT geometry
                FROM drawing_entities
                WHERE entity_id = %s
            """, (entity_id,))

            entity = cur.fetchone()
            if not entity:
                return {}

            # Find nearby entities within search radius
            cur.execute("""
                WITH target_geom AS (
                    SELECT ST_Buffer(geometry, %s) as search_area
                    FROM drawing_entities
                    WHERE entity_id = %s
                )
                SELECT
                    se.entity_type,
                    de.layer_name,
                    se.classification_state,
                    ST_Distance(de.geometry, (SELECT geometry FROM drawing_entities WHERE entity_id = %s)) as distance
                FROM drawing_entities de
                JOIN standards_entities se ON de.entity_id = se.entity_id
                CROSS JOIN target_geom
                WHERE ST_Intersects(de.geometry, target_geom.search_area)
                  AND de.entity_id != %s
                  AND se.classification_state IN ('auto_classified', 'user_classified')
                ORDER BY distance
                LIMIT 50
            """, (search_radius_feet, entity_id, entity_id, entity_id))

            nearby = cur.fetchall()

            if not nearby:
                return {
                    'nearby_types': [],
                    'nearby_layers': [],
                    'network_hints': [],
                    'density': 'low',
                    'message': 'No classified entities found nearby'
                }

            # Aggregate nearby entity types
            type_counts = defaultdict(int)
            layer_counts = defaultdict(int)

            for row in nearby:
                type_counts[row['entity_type']] += 1
                if row['layer_name']:
                    layer_counts[row['layer_name']] += 1

            # Sort by frequency
            nearby_types = [
                {'type': t, 'count': c}
                for t, c in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
            ]

            nearby_layers = [
                {'layer': l, 'count': c}
                for l, c in sorted(layer_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            ]

            # Determine density
            density = 'high' if len(nearby) > 30 else 'medium' if len(nearby) > 10 else 'low'

            # Network connectivity hints
            network_hints = []
            if any('utility_line' in t for t, _ in type_counts.items()):
                network_hints.append('Part of utility network')
            if any('utility_structure' in t for t, _ in type_counts.items()):
                network_hints.append('Near utility structures')
            if any('survey_point' in t for t, _ in type_counts.items()):
                network_hints.append('Survey control nearby')

            return {
                'nearby_types': nearby_types[:5],
                'nearby_layers': nearby_layers,
                'network_hints': network_hints,
                'density': density,
                'total_nearby': len(nearby),
                'search_radius_feet': search_radius_feet
            }

        finally:
            if self.should_close and self.conn:
                self.conn.close()

    def explain_suggestion(self, entity_id: str, suggested_type: str) -> Dict:
        """
        Provide detailed explanation for why a type was suggested.

        Args:
            entity_id: Entity being classified
            suggested_type: The suggested entity type

        Returns:
            Dict with explanation details
        """
        if not self.conn:
            self.conn = psycopg2.connect(**self.db_config)

        try:
            cur = self.conn.cursor(cursor_factory=RealDictCursor)

            # Get examples of similar entities with this type
            cur.execute("""
                WITH target_embedding AS (
                    SELECT embedding
                    FROM entity_embeddings
                    WHERE entity_id = %s AND is_current = TRUE
                )
                SELECT
                    se.entity_id,
                    de.layer_name,
                    se.classification_state,
                    se.classification_confidence,
                    1 - (ee.embedding <=> te.embedding) as similarity
                FROM entity_embeddings ee
                CROSS JOIN target_embedding te
                JOIN standards_entities se ON ee.entity_id = se.entity_id
                LEFT JOIN drawing_entities de ON se.entity_id = de.entity_id
                WHERE ee.is_current = TRUE
                  AND se.entity_type = %s
                  AND se.classification_state IN ('auto_classified', 'user_classified')
                  AND se.classification_confidence >= 0.7
                ORDER BY ee.embedding <=> te.embedding
                LIMIT 5
            """, (entity_id, suggested_type))

            examples = cur.fetchall()

            return {
                'suggested_type': suggested_type,
                'example_count': len(examples),
                'examples': [
                    {
                        'entity_id': str(ex['entity_id']),
                        'layer_name': ex['layer_name'],
                        'similarity': round(ex['similarity'], 3),
                        'confidence': round(ex['classification_confidence'], 3),
                        'source': ex['classification_state']
                    }
                    for ex in examples
                ]
            }

        finally:
            if self.should_close and self.conn:
                self.conn.close()

    def get_classification_analytics(self, project_id: Optional[str] = None,
                                     days_back: int = 30) -> Dict:
        """
        Get analytics about classification accuracy and user corrections.

        Args:
            project_id: Optional project filter
            days_back: Number of days to analyze

        Returns:
            Dict with analytics data
        """
        if not self.conn:
            self.conn = psycopg2.connect(**self.db_config)

        try:
            cur = self.conn.cursor(cursor_factory=RealDictCursor)

            where_clause = "WHERE se.created_at >= NOW() - INTERVAL '%s days'" % days_back
            if project_id:
                where_clause += f" AND se.project_id = '{project_id}'"

            # Get classification stats
            cur.execute(f"""
                SELECT
                    COUNT(*) FILTER (WHERE classification_state = 'auto_classified') as auto_classified,
                    COUNT(*) FILTER (WHERE classification_state = 'user_classified') as user_classified,
                    COUNT(*) FILTER (WHERE classification_state = 'needs_review') as needs_review,
                    AVG(classification_confidence) FILTER (WHERE classification_state = 'auto_classified') as avg_auto_confidence,
                    AVG(classification_confidence) FILTER (WHERE classification_state = 'user_classified') as avg_user_confidence,
                    COUNT(*) FILTER (WHERE classification_metadata::text LIKE '%reclassified_from%') as reclassifications
                FROM standards_entities se
                {where_clause}
            """)

            stats = cur.fetchone()

            # Get most common reclassifications (from -> to)
            cur.execute(f"""
                SELECT
                    classification_metadata->>'reclassified_from' as from_type,
                    entity_type as to_type,
                    COUNT(*) as count
                FROM standards_entities se
                {where_clause}
                  AND classification_metadata::text LIKE '%reclassified_from%'
                GROUP BY from_type, to_type
                ORDER BY count DESC
                LIMIT 10
            """)

            reclassification_patterns = cur.fetchall()

            return {
                'period_days': days_back,
                'total_auto_classified': stats['auto_classified'] or 0,
                'total_user_classified': stats['user_classified'] or 0,
                'total_needs_review': stats['needs_review'] or 0,
                'avg_auto_confidence': round(float(stats['avg_auto_confidence'] or 0), 3),
                'avg_user_confidence': round(float(stats['avg_user_confidence'] or 0), 3),
                'total_reclassifications': stats['reclassifications'] or 0,
                'common_reclassifications': [
                    {
                        'from_type': r['from_type'],
                        'to_type': r['to_type'],
                        'count': r['count']
                    }
                    for r in reclassification_patterns
                ] if reclassification_patterns else []
            }

        finally:
            if self.should_close and self.conn:
                self.conn.close()
