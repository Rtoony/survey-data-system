"""
GraphRAG Service - Natural Language Query Engine for CAD/GIS Knowledge Graph

This service provides GraphRAG (Graph Retrieval-Augmented Generation) capabilities:
1. Multi-hop graph traversal with embedding context
2. Natural language query parsing and execution
3. Hybrid search (vector + full-text + spatial + graph)
4. Result ranking and relevance scoring
5. Query result caching

Author: AI Agent Toolkit
Date: 2025-11-18
"""

import re
import hashlib
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from database import execute_query, get_db
from psycopg2.extras import RealDictCursor
import psycopg2


class GraphRAGService:
    """
    GraphRAG query engine for CAD/GIS knowledge graphs
    """

    # Query pattern definitions for natural language understanding
    QUERY_PATTERNS = {
        'find_connections': [
            r'(find|show|get|list).*(connect|link|relat|assoc).*(to|from|with)',
            r'what.*connected.*to',
            r'which.*(pipes|lines|structures).*connected',
        ],
        'flow_path': [
            r'(flow|path|route).*(from|to|between)',
            r'trace.*(upstream|downstream)',
            r'follow.*(pipe|line|connection)',
        ],
        'similar_entities': [
            r'(similar|like|comparable|resemble)',
            r'find.*(same|similar).*design',
            r'show.*projects.*like',
        ],
        'spatial_query': [
            r'(within|near|around|inside|outside)',
            r'(distance|proximity|close to|far from)',
            r'(\d+)\s*(feet|ft|meters|m).*from',
        ],
        'attribute_filter': [
            r'(where|with|having).*(material|size|type|status)',
            r'filter.*by',
            r'(material|diameter|elevation).*=',
        ],
        'quality_check': [
            r'(quality|score|issue|problem|error)',
            r'(incomplete|missing|invalid)',
            r'check.*quality',
        ],
        'hierarchical': [
            r'(in|under|part of|belongs to).*(project|basin|zone)',
            r'all.*(in|from).*(project|area)',
        ],
    }

    def __init__(self):
        """Initialize the GraphRAG service"""
        self.max_hops = 10  # Maximum traversal depth
        self.default_cache_ttl = 3600  # 1 hour cache TTL
        self.min_similarity_threshold = 0.7  # Minimum similarity for semantic relationships

    def parse_query(self, query_text: str) -> Dict[str, Any]:
        """
        Parse natural language query and extract intent, entities, and parameters

        Args:
            query_text: Natural language query string

        Returns:
            Dictionary with query_type, entities, parameters, and confidence
        """
        query_lower = query_text.lower()

        # Determine query type by matching patterns
        query_type = 'general'
        max_matches = 0

        for qtype, patterns in self.QUERY_PATTERNS.items():
            matches = sum(1 for pattern in patterns if re.search(pattern, query_lower))
            if matches > max_matches:
                max_matches = matches
                query_type = qtype

        # Extract entity references (MH-101, Basin A, etc.)
        entity_references = re.findall(r'([A-Z]{2,}-\d+|Basin\s+[A-Z0-9]+|MH-\d+)', query_text)

        # Extract numeric parameters (distances, elevations, etc.)
        numeric_params = {}

        # Extract distance constraints
        distance_match = re.search(r'(\d+\.?\d*)\s*(feet|ft|meters|m)', query_lower)
        if distance_match:
            numeric_params['distance'] = float(distance_match.group(1))
            numeric_params['distance_unit'] = distance_match.group(2)

        # Extract elevation constraints
        elevation_match = re.search(r'elevation\s*([<>=]+)\s*(\d+\.?\d*)', query_lower)
        if elevation_match:
            numeric_params['elevation_operator'] = elevation_match.group(1)
            numeric_params['elevation_value'] = float(elevation_match.group(2))

        # Extract material/attribute filters
        material_match = re.search(r'material\s*=\s*["\']?([A-Z_]+)', query_text, re.IGNORECASE)
        if material_match:
            numeric_params['material'] = material_match.group(1)

        # Determine entity types mentioned
        entity_types = []
        type_keywords = {
            'pipe': 'utility_line',
            'line': 'utility_line',
            'manhole': 'utility_structure',
            'structure': 'utility_structure',
            'basin': 'utility_structure',
            'valve': 'utility_structure',
            'point': 'survey_point',
            'survey': 'survey_point',
            'project': 'project',
        }

        for keyword, etype in type_keywords.items():
            if keyword in query_lower and etype not in entity_types:
                entity_types.append(etype)

        return {
            'query_type': query_type,
            'entity_references': entity_references,
            'entity_types': entity_types if entity_types else None,
            'parameters': numeric_params,
            'confidence': max_matches / len(self.QUERY_PATTERNS.get(query_type, [1])),
            'original_query': query_text
        }

    def execute_query(self, query_text: str, use_cache: bool = True,
                     max_results: int = 100) -> Dict[str, Any]:
        """
        Execute a natural language query against the knowledge graph

        Args:
            query_text: Natural language query
            use_cache: Whether to use cached results
            max_results: Maximum number of results to return

        Returns:
            Query results with entities, relationships, and metadata
        """
        start_time = datetime.now()

        # Check cache first
        if use_cache:
            cached_result = self._get_cached_result(query_text)
            if cached_result:
                return cached_result

        # Parse the query
        parsed_query = self.parse_query(query_text)

        # Route to appropriate query handler
        query_type = parsed_query['query_type']

        if query_type == 'find_connections':
            result = self._execute_connection_query(parsed_query, max_results)
        elif query_type == 'flow_path':
            result = self._execute_flow_path_query(parsed_query, max_results)
        elif query_type == 'similar_entities':
            result = self._execute_similarity_query(parsed_query, max_results)
        elif query_type == 'spatial_query':
            result = self._execute_spatial_query(parsed_query, max_results)
        elif query_type == 'attribute_filter':
            result = self._execute_attribute_query(parsed_query, max_results)
        elif query_type == 'quality_check':
            result = self._execute_quality_query(parsed_query, max_results)
        elif query_type == 'hierarchical':
            result = self._execute_hierarchical_query(parsed_query, max_results)
        else:
            result = self._execute_hybrid_search(parsed_query, max_results)

        # Add metadata
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        result['metadata'] = {
            'query_type': query_type,
            'execution_time_ms': round(execution_time, 2),
            'parsed_query': parsed_query,
            'timestamp': datetime.now().isoformat()
        }

        # Cache the result
        if use_cache and result['entities']:
            self._cache_result(query_text, query_type, result, execution_time)

        # Log the query
        self._log_query(query_text, query_type, True, len(result['entities']), execution_time, False)

        return result

    def _execute_connection_query(self, parsed_query: Dict, max_results: int) -> Dict[str, Any]:
        """Find entities connected to a specific entity"""
        entities = parsed_query['entity_references']

        if not entities:
            return {'entities': [], 'relationships': [], 'explanation': 'No entity reference found in query'}

        # Find the source entity
        source_entity = self._resolve_entity_reference(entities[0])

        if not source_entity:
            return {'entities': [], 'relationships': [], 'explanation': f'Could not find entity: {entities[0]}'}

        # Query connected entities
        query = """
            WITH RECURSIVE entity_graph AS (
                -- Base case: start entity
                SELECT
                    se.entity_id,
                    se.entity_type,
                    se.canonical_name,
                    se.description,
                    se.quality_score,
                    0 as hop_distance,
                    ARRAY[se.entity_id] as path
                FROM standards_entities se
                WHERE se.entity_id = %s

                UNION ALL

                -- Recursive case: follow relationships
                SELECT
                    se.entity_id,
                    se.entity_type,
                    se.canonical_name,
                    se.description,
                    se.quality_score,
                    eg.hop_distance + 1,
                    eg.path || se.entity_id
                FROM entity_graph eg
                JOIN entity_relationships er ON (
                    er.subject_entity_id = eg.entity_id
                    OR er.object_entity_id = eg.entity_id
                )
                JOIN standards_entities se ON (
                    CASE
                        WHEN er.subject_entity_id = eg.entity_id THEN se.entity_id = er.object_entity_id
                        ELSE se.entity_id = er.subject_entity_id
                    END
                )
                WHERE eg.hop_distance < %s
                  AND NOT se.entity_id = ANY(eg.path)  -- Prevent cycles
            )
            SELECT DISTINCT
                entity_id,
                entity_type,
                canonical_name,
                description,
                quality_score,
                hop_distance
            FROM entity_graph
            WHERE hop_distance > 0
            ORDER BY hop_distance, quality_score DESC NULLS LAST
            LIMIT %s
        """

        entities_result = execute_query(query, (source_entity['entity_id'], self.max_hops, max_results))

        # Get relationships between these entities
        relationships = self._get_relationships_between_entities(
            [source_entity['entity_id']] + [e['entity_id'] for e in entities_result]
        )

        return {
            'entities': [source_entity] + entities_result,
            'relationships': relationships,
            'explanation': f"Found {len(entities_result)} entities connected to {source_entity['canonical_name']}"
        }

    def _execute_flow_path_query(self, parsed_query: Dict, max_results: int) -> Dict[str, Any]:
        """Trace flow path through utility network"""
        entities = parsed_query['entity_references']

        if len(entities) < 2:
            return {'entities': [], 'relationships': [], 'explanation': 'Flow path query requires start and end points'}

        source = self._resolve_entity_reference(entities[0])
        target = self._resolve_entity_reference(entities[1])

        if not source or not target:
            return {'entities': [], 'relationships': [], 'explanation': 'Could not resolve entity references'}

        # Find shortest path with direction awareness
        query = """
            WITH RECURSIVE flow_path AS (
                -- Start node
                SELECT
                    se.entity_id,
                    se.canonical_name,
                    se.entity_type,
                    ARRAY[se.entity_id] as path,
                    0 as path_length,
                    CAST(NULL AS UUID) as via_relationship
                FROM standards_entities se
                WHERE se.entity_id = %s

                UNION ALL

                -- Follow flow direction (considering elevation and flow relationships)
                SELECT
                    se.entity_id,
                    se.canonical_name,
                    se.entity_type,
                    fp.path || se.entity_id,
                    fp.path_length + 1,
                    er.relationship_id
                FROM flow_path fp
                JOIN entity_relationships er ON er.subject_entity_id = fp.entity_id
                JOIN standards_entities se ON se.entity_id = er.object_entity_id
                WHERE NOT se.entity_id = ANY(fp.path)
                  AND fp.path_length < %s
                  AND (
                      er.relationship_type = 'flows_to'
                      OR er.engineering_relationship->>'direction' = 'downstream'
                      OR er.spatial_relationship = 'connected_to'
                  )
            )
            SELECT * FROM flow_path
            WHERE entity_id = %s
            ORDER BY path_length
            LIMIT 1
        """

        path_result = execute_query(query, (source['entity_id'], max_results, target['entity_id']))

        if not path_result:
            return {
                'entities': [],
                'relationships': [],
                'explanation': f"No flow path found from {source['canonical_name']} to {target['canonical_name']}"
            }

        # Get all entities in the path
        path_entity_ids = path_result[0]['path']
        entities_result = execute_query(
            "SELECT * FROM standards_entities WHERE entity_id = ANY(%s)",
            (path_entity_ids,)
        )

        relationships = self._get_relationships_between_entities(path_entity_ids)

        return {
            'entities': entities_result,
            'relationships': relationships,
            'explanation': f"Flow path from {source['canonical_name']} to {target['canonical_name']}: {len(path_entity_ids)} hops"
        }

    def _execute_similarity_query(self, parsed_query: Dict, max_results: int) -> Dict[str, Any]:
        """Find similar entities using vector embeddings"""
        entities = parsed_query['entity_references']

        if not entities:
            return {'entities': [], 'relationships': [], 'explanation': 'No entity reference found for similarity search'}

        source = self._resolve_entity_reference(entities[0])

        if not source:
            return {'entities': [], 'relationships': [], 'explanation': f'Could not find entity: {entities[0]}'}

        # Find similar entities using vector similarity
        query = """
            SELECT
                se.entity_id,
                se.entity_type,
                se.canonical_name,
                se.description,
                se.quality_score,
                1 - (e1.embedding <=> e2.embedding) as similarity_score
            FROM entity_embeddings e1
            JOIN entity_embeddings e2 ON e1.model_id = e2.model_id AND e1.is_current AND e2.is_current
            JOIN standards_entities se ON se.entity_id = e2.entity_id
            WHERE e1.entity_id = %s
              AND e2.entity_id != %s
              AND (1 - (e1.embedding <=> e2.embedding)) >= %s
            ORDER BY similarity_score DESC
            LIMIT %s
        """

        similar_entities = execute_query(
            query,
            (source['entity_id'], source['entity_id'], self.min_similarity_threshold, max_results)
        )

        return {
            'entities': [source] + similar_entities,
            'relationships': [],
            'explanation': f"Found {len(similar_entities)} entities similar to {source['canonical_name']}"
        }

    def _execute_spatial_query(self, parsed_query: Dict, max_results: int) -> Dict[str, Any]:
        """Execute spatial proximity queries"""
        entities = parsed_query['entity_references']
        params = parsed_query['parameters']

        if not entities or 'distance' not in params:
            return {'entities': [], 'relationships': [], 'explanation': 'Spatial query requires entity and distance'}

        source = self._resolve_entity_reference(entities[0])
        if not source:
            return {'entities': [], 'relationships': [], 'explanation': f'Could not find entity: {entities[0]}'}

        # Convert distance to feet (if needed)
        distance_ft = params['distance']
        if params.get('distance_unit') in ['meters', 'm']:
            distance_ft *= 3.28084

        # Get source geometry
        source_geom_query = """
            SELECT ST_AsText(geometry) as geometry
            FROM (
                SELECT geometry FROM survey_points WHERE point_id = %s
                UNION ALL
                SELECT geometry FROM utility_structures WHERE structure_id = %s
                UNION ALL
                SELECT ST_Centroid(geometry) as geometry FROM utility_lines WHERE line_id = %s
            ) geoms
            WHERE geometry IS NOT NULL
            LIMIT 1
        """

        source_geom = execute_query(source_geom_query, (source['entity_id'], source['entity_id'], source['entity_id']))

        if not source_geom:
            return {'entities': [], 'relationships': [], 'explanation': 'Source entity has no geometry'}

        # Find nearby entities (this is a simplified version - you'd need to query each table)
        # For a complete implementation, you'd union queries across all spatial tables
        nearby_query = """
            SELECT
                'survey_point' as entity_type,
                point_id as entity_id,
                point_name as name,
                ST_Distance(geometry, ST_GeomFromText(%s, 6423)) as distance_ft
            FROM survey_points
            WHERE ST_DWithin(geometry, ST_GeomFromText(%s, 6423), %s)
              AND point_id != %s
            UNION ALL
            SELECT
                'utility_structure' as entity_type,
                structure_id as entity_id,
                structure_name as name,
                ST_Distance(geometry, ST_GeomFromText(%s, 6423)) as distance_ft
            FROM utility_structures
            WHERE ST_DWithin(geometry, ST_GeomFromText(%s, 6423), %s)
              AND structure_id != %s
            ORDER BY distance_ft
            LIMIT %s
        """

        geom_text = source_geom[0]['geometry']
        nearby_entities = execute_query(
            nearby_query,
            (geom_text, geom_text, distance_ft, source['entity_id'],
             geom_text, geom_text, distance_ft, source['entity_id'],
             max_results)
        )

        return {
            'entities': [source] + nearby_entities,
            'relationships': [],
            'explanation': f"Found {len(nearby_entities)} entities within {params['distance']} {params.get('distance_unit', 'feet')} of {source['canonical_name']}"
        }

    def _execute_attribute_query(self, parsed_query: Dict, max_results: int) -> Dict[str, Any]:
        """Filter entities by attributes"""
        params = parsed_query['parameters']
        entity_types = parsed_query['entity_types']

        # Build attribute filter conditions
        conditions = []
        values = []

        if 'material' in params:
            conditions.append("attributes->>'material' = %s")
            values.append(params['material'])

        if 'elevation_operator' in params:
            op = params['elevation_operator']
            conditions.append(f"CAST(attributes->>'elevation' AS DECIMAL) {op} %s")
            values.append(params['elevation_value'])

        if not conditions:
            return {'entities': [], 'relationships': [], 'explanation': 'No filter conditions specified'}

        where_clause = ' AND '.join(conditions)

        query = f"""
            SELECT
                entity_id,
                entity_type,
                canonical_name,
                description,
                attributes,
                quality_score
            FROM standards_entities
            WHERE {where_clause}
            ORDER BY quality_score DESC NULLS LAST
            LIMIT %s
        """

        values.append(max_results)
        entities_result = execute_query(query, tuple(values))

        return {
            'entities': entities_result,
            'relationships': [],
            'explanation': f"Found {len(entities_result)} entities matching filters"
        }

    def _execute_quality_query(self, parsed_query: Dict, max_results: int) -> Dict[str, Any]:
        """Find entities with quality issues"""
        entity_types = parsed_query['entity_types']

        # Query entities with low quality scores or missing data
        query = """
            SELECT
                entity_id,
                entity_type,
                canonical_name,
                description,
                quality_score,
                CASE
                    WHEN quality_score < 0.5 THEN 'critical'
                    WHEN quality_score < 0.7 THEN 'warning'
                    ELSE 'info'
                END as severity
            FROM standards_entities
            WHERE quality_score < 0.8
            ORDER BY quality_score ASC NULLS FIRST
            LIMIT %s
        """

        entities_result = execute_query(query, (max_results,))

        return {
            'entities': entities_result,
            'relationships': [],
            'explanation': f"Found {len(entities_result)} entities with quality scores below 0.8"
        }

    def _execute_hierarchical_query(self, parsed_query: Dict, max_results: int) -> Dict[str, Any]:
        """Query entities within a project or hierarchy"""
        # Extract project/area reference
        query_text = parsed_query['original_query']

        # Simple implementation - find project by name
        project_match = re.search(r'project\s+["\']?([^"\']+)["\']?', query_text, re.IGNORECASE)

        if not project_match:
            return {'entities': [], 'relationships': [], 'explanation': 'No project reference found'}

        project_name = project_match.group(1).strip()

        # Find entities in this project
        query = """
            SELECT
                se.entity_id,
                se.entity_type,
                se.canonical_name,
                se.description,
                se.quality_score,
                p.project_name
            FROM standards_entities se
            JOIN projects p ON p.project_id = se.attributes->>'project_id'::UUID
            WHERE p.project_name ILIKE %s
            ORDER BY se.quality_score DESC NULLS LAST
            LIMIT %s
        """

        entities_result = execute_query(query, (f'%{project_name}%', max_results))

        return {
            'entities': entities_result,
            'relationships': [],
            'explanation': f"Found {len(entities_result)} entities in project matching '{project_name}'"
        }

    def _execute_hybrid_search(self, parsed_query: Dict, max_results: int) -> Dict[str, Any]:
        """Execute hybrid search combining full-text, vector, and graph"""
        query_text = parsed_query['original_query']

        # Use the existing hybrid_search database function
        query = """
            SELECT * FROM hybrid_search(
                %s,  -- search_query
                %s,  -- vector_query (use same as search)
                NULL,  -- entity_types
                0.0,  -- min_quality_score
                %s   -- max_results
            )
        """

        entities_result = execute_query(query, (query_text, query_text, max_results))

        return {
            'entities': entities_result,
            'relationships': [],
            'explanation': f"Hybrid search found {len(entities_result)} relevant entities"
        }

    def _resolve_entity_reference(self, reference: str) -> Optional[Dict[str, Any]]:
        """Resolve entity reference (MH-101, Basin A, etc.) to entity record"""
        # Try exact canonical name match first
        query = """
            SELECT entity_id, entity_type, canonical_name, description, quality_score
            FROM standards_entities
            WHERE canonical_name = %s
            LIMIT 1
        """

        result = execute_query(query, (reference,))
        if result:
            return result[0]

        # Try fuzzy match on canonical name or aliases
        query = """
            SELECT entity_id, entity_type, canonical_name, description, quality_score
            FROM standards_entities
            WHERE canonical_name ILIKE %s
               OR %s = ANY(aliases)
            ORDER BY
                CASE WHEN canonical_name = %s THEN 0 ELSE 1 END,
                quality_score DESC NULLS LAST
            LIMIT 1
        """

        result = execute_query(query, (f'%{reference}%', reference, reference))
        return result[0] if result else None

    def _get_relationships_between_entities(self, entity_ids: List[str]) -> List[Dict[str, Any]]:
        """Get relationships between a list of entities"""
        if not entity_ids:
            return []

        query = """
            SELECT
                relationship_id,
                subject_entity_id,
                object_entity_id,
                relationship_type,
                predicate,
                confidence_score,
                spatial_relationship,
                engineering_relationship
            FROM entity_relationships
            WHERE subject_entity_id = ANY(%s)
              AND object_entity_id = ANY(%s)
        """

        return execute_query(query, (entity_ids, entity_ids))

    def _get_cached_result(self, query_text: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached query result if available and valid"""
        query_hash = hashlib.sha256(query_text.lower().encode()).hexdigest()

        query = """
            SELECT result_json, cache_id
            FROM ai_query_cache
            WHERE query_hash = %s
              AND is_valid = TRUE
              AND (expires_at IS NULL OR expires_at > NOW())
            LIMIT 1
        """

        try:
            result = execute_query(query, (query_hash,))

            if result:
                # Update hit count
                update_query = """
                    UPDATE ai_query_cache
                    SET hit_count = hit_count + 1,
                        last_accessed_at = NOW()
                    WHERE cache_id = %s
                """
                execute_query(update_query, (result[0]['cache_id'],))

                cached_data = result[0]['result_json']
                cached_data['metadata']['from_cache'] = True
                return cached_data

        except Exception as e:
            print(f"Cache retrieval error: {e}")

        return None

    def _cache_result(self, query_text: str, query_type: str, result: Dict[str, Any],
                     execution_time_ms: float):
        """Cache query result for future use"""
        query_hash = hashlib.sha256(query_text.lower().encode()).hexdigest()

        query = """
            INSERT INTO ai_query_cache (
                query_hash,
                query_text,
                query_type,
                result_json,
                entity_count,
                relationship_count,
                execution_time_ms,
                expires_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (query_hash) DO UPDATE
            SET result_json = EXCLUDED.result_json,
                execution_time_ms = EXCLUDED.execution_time_ms,
                created_at = NOW(),
                is_valid = TRUE
        """

        try:
            expires_at = datetime.now() + timedelta(seconds=self.default_cache_ttl)

            execute_query(query, (
                query_hash,
                query_text,
                query_type,
                json.dumps(result),
                len(result['entities']),
                len(result.get('relationships', [])),
                round(execution_time_ms, 2),
                expires_at
            ))
        except Exception as e:
            print(f"Cache write error: {e}")

    def _log_query(self, query_text: str, query_type: str, was_successful: bool,
                   result_count: int, execution_time_ms: float, used_cache: bool):
        """Log query execution for analytics"""
        query = """
            INSERT INTO ai_query_history (
                query_text,
                query_type,
                was_successful,
                result_count,
                execution_time_ms,
                used_cache
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """

        try:
            execute_query(query, (
                query_text,
                query_type,
                was_successful,
                result_count,
                round(execution_time_ms, 2),
                used_cache
            ))
        except Exception as e:
            print(f"Query logging error: {e}")

    def invalidate_cache(self, entity_ids: Optional[List[str]] = None,
                        reason: str = 'manual_invalidation'):
        """Invalidate cached query results"""
        if entity_ids:
            # Invalidate queries that might involve these entities
            # This is a simple implementation - could be more sophisticated
            query = """
                UPDATE ai_query_cache
                SET is_valid = FALSE,
                    invalidation_reason = %s
                WHERE is_valid = TRUE
            """
            execute_query(query, (reason,))
        else:
            # Invalidate all cache
            query = """
                UPDATE ai_query_cache
                SET is_valid = FALSE,
                    invalidation_reason = %s
                WHERE is_valid = TRUE
            """
            execute_query(query, (reason,))

    def get_query_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
        """Get query suggestions based on partial input and history"""
        # Find similar queries from history
        query = """
            SELECT DISTINCT query_text, hit_count
            FROM ai_query_cache
            WHERE query_text ILIKE %s
              AND is_valid = TRUE
            ORDER BY hit_count DESC
            LIMIT %s
        """

        results = execute_query(query, (f'%{partial_query}%', limit))
        return [r['query_text'] for r in results]


# Singleton instance
_graphrag_service = None

def get_graphrag_service() -> GraphRAGService:
    """Get singleton GraphRAG service instance"""
    global _graphrag_service
    if _graphrag_service is None:
        _graphrag_service = GraphRAGService()
    return _graphrag_service
