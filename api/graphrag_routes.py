"""
GraphRAG API Routes - Natural Language Query and Graph Analytics Endpoints

This module provides REST API endpoints for GraphRAG functionality:
- Natural language queries
- Graph analytics (PageRank, communities, centrality)
- Query history and suggestions
- Cache management

Author: AI Agent Toolkit
Date: 2025-11-18
"""

from flask import Blueprint, request, jsonify
from typing import Dict, Any, Optional
from services.graphrag_service import get_graphrag_service
from services.graph_analytics_service import get_graph_analytics_service
from datetime import datetime

# Create blueprint
graphrag_bp = Blueprint('graphrag', __name__, url_prefix='/api/graphrag')

# Get service instances
graphrag_service = get_graphrag_service()
analytics_service = get_graph_analytics_service()


@graphrag_bp.route('/query', methods=['POST'])
def execute_natural_language_query():
    """
    Execute a natural language query against the knowledge graph

    Request Body:
        {
            "query": "Find all pipes connected to Basin MH-101",
            "use_cache": true,
            "max_results": 100
        }

    Returns:
        {
            "entities": [...],
            "relationships": [...],
            "explanation": "...",
            "metadata": {...}
        }
    """
    try:
        data = request.get_json()

        if not data or 'query' not in data:
            return jsonify({'error': 'Query text is required'}), 400

        query_text = data['query']
        use_cache = data.get('use_cache', True)
        max_results = data.get('max_results', 100)

        # Execute query
        result = graphrag_service.execute_query(
            query_text=query_text,
            use_cache=use_cache,
            max_results=max_results
        )

        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@graphrag_bp.route('/query/parse', methods=['POST'])
def parse_query():
    """
    Parse a natural language query without executing it

    Request Body:
        {
            "query": "Show me pipes within 50 feet of MH-101"
        }

    Returns:
        {
            "query_type": "spatial_query",
            "entity_references": ["MH-101"],
            "entity_types": ["pipe"],
            "parameters": {"distance": 50, "distance_unit": "feet"},
            "confidence": 0.8
        }
    """
    try:
        data = request.get_json()

        if not data or 'query' not in data:
            return jsonify({'error': 'Query text is required'}), 400

        parsed = graphrag_service.parse_query(data['query'])

        return jsonify(parsed), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@graphrag_bp.route('/query/suggestions', methods=['GET'])
def get_query_suggestions():
    """
    Get query suggestions based on partial input

    Query Parameters:
        - q: Partial query text
        - limit: Maximum number of suggestions (default: 5)

    Returns:
        {
            "suggestions": [
                "Find all pipes connected to Basin MH-101",
                "Find pipes within 50 feet of Basin A"
            ]
        }
    """
    try:
        partial_query = request.args.get('q', '')
        limit = int(request.args.get('limit', 5))

        if not partial_query:
            return jsonify({'suggestions': []}), 200

        suggestions = graphrag_service.get_query_suggestions(partial_query, limit)

        return jsonify({'suggestions': suggestions}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@graphrag_bp.route('/analytics/pagerank', methods=['GET'])
def compute_pagerank():
    """
    Compute PageRank scores for entities

    Query Parameters:
        - project_id: Optional project scope
        - entity_type: Optional entity type filter
        - use_cache: Whether to use cached results (default: true)

    Returns:
        {
            "pagerank_scores": {
                "entity_id_1": 0.023,
                "entity_id_2": 0.018,
                ...
            },
            "metadata": {...}
        }
    """
    try:
        project_id = request.args.get('project_id')
        entity_type = request.args.get('entity_type')
        use_cache = request.args.get('use_cache', 'true').lower() == 'true'

        scores = analytics_service.compute_pagerank(
            project_id=project_id,
            entity_type=entity_type,
            use_cache=use_cache
        )

        return jsonify({
            'pagerank_scores': scores,
            'metadata': {
                'project_id': project_id,
                'entity_type': entity_type,
                'num_entities': len(scores),
                'timestamp': datetime.now().isoformat()
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@graphrag_bp.route('/analytics/communities', methods=['GET'])
def detect_communities():
    """
    Detect communities in the graph

    Query Parameters:
        - project_id: Optional project scope
        - algorithm: Algorithm to use (louvain, label_propagation, greedy_modularity)
        - use_cache: Whether to use cached results

    Returns:
        {
            "communities": [
                {
                    "community_id": 0,
                    "entity_ids": [...],
                    "size": 15
                }
            ],
            "modularity": 0.42,
            "num_communities": 5,
            "algorithm": "louvain"
        }
    """
    try:
        project_id = request.args.get('project_id')
        algorithm = request.args.get('algorithm', 'louvain')
        use_cache = request.args.get('use_cache', 'true').lower() == 'true'

        result = analytics_service.detect_communities(
            project_id=project_id,
            algorithm=algorithm,
            use_cache=use_cache
        )

        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@graphrag_bp.route('/analytics/centrality', methods=['GET'])
def compute_centrality():
    """
    Compute centrality measures

    Query Parameters:
        - project_id: Optional project scope
        - measures: Comma-separated list (degree,betweenness,closeness,eigenvector)
        - use_cache: Whether to use cached results

    Returns:
        {
            "degree": {"entity_id_1": 5, ...},
            "betweenness": {"entity_id_1": 0.12, ...},
            "closeness": {"entity_id_1": 0.34, ...}
        }
    """
    try:
        project_id = request.args.get('project_id')
        measures_str = request.args.get('measures', 'degree,betweenness')
        use_cache = request.args.get('use_cache', 'true').lower() == 'true'

        measures = [m.strip() for m in measures_str.split(',')]

        result = analytics_service.compute_centrality_measures(
            project_id=project_id,
            measures=measures,
            use_cache=use_cache
        )

        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@graphrag_bp.route('/analytics/influential-nodes', methods=['GET'])
def find_influential_nodes():
    """
    Find most influential nodes in the graph

    Query Parameters:
        - project_id: Optional project scope
        - top_k: Number of top nodes (default: 10)
        - metric: Metric to use (pagerank, degree, betweenness)

    Returns:
        [
            {
                "entity_id": "...",
                "canonical_name": "...",
                "entity_type": "...",
                "pagerank_score": 0.023
            }
        ]
    """
    try:
        project_id = request.args.get('project_id')
        top_k = int(request.args.get('top_k', 10))
        metric = request.args.get('metric', 'pagerank')

        result = analytics_service.find_influential_nodes(
            project_id=project_id,
            top_k=top_k,
            metric=metric
        )

        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@graphrag_bp.route('/analytics/structure', methods=['GET'])
def analyze_structure():
    """
    Analyze overall graph structure

    Query Parameters:
        - project_id: Optional project scope

    Returns:
        {
            "num_nodes": 1500,
            "num_edges": 3200,
            "density": 0.0014,
            "avg_degree": 4.27,
            "is_connected": false,
            ...
        }
    """
    try:
        project_id = request.args.get('project_id')

        result = analytics_service.analyze_graph_structure(project_id=project_id)

        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@graphrag_bp.route('/analytics/shortest-path', methods=['POST'])
def find_shortest_path():
    """
    Find shortest path between two entities

    Request Body:
        {
            "source_entity_id": "uuid-1",
            "target_entity_id": "uuid-2",
            "weight_attribute": "distance"  // optional
        }

    Returns:
        {
            "path": ["uuid-1", "uuid-3", "uuid-2"],
            "path_entities": [...],
            "length": 2,
            "exists": true
        }
    """
    try:
        data = request.get_json()

        if not data or 'source_entity_id' not in data or 'target_entity_id' not in data:
            return jsonify({'error': 'source_entity_id and target_entity_id are required'}), 400

        result = analytics_service.find_shortest_path(
            source_entity_id=data['source_entity_id'],
            target_entity_id=data['target_entity_id'],
            weight_attribute=data.get('weight_attribute')
        )

        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@graphrag_bp.route('/analytics/connected-components', methods=['GET'])
def find_connected_components():
    """
    Find connected components in the graph

    Query Parameters:
        - project_id: Optional project scope

    Returns:
        {
            "components": [
                ["entity_id_1", "entity_id_2", ...],
                ["entity_id_10", "entity_id_11", ...]
            ],
            "num_components": 3
        }
    """
    try:
        project_id = request.args.get('project_id')

        components = analytics_service.find_connected_components(project_id=project_id)

        return jsonify({
            'components': [list(comp) for comp in components],
            'num_components': len(components)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@graphrag_bp.route('/analytics/bridges', methods=['GET'])
def identify_bridges():
    """
    Identify bridge edges (critical connections)

    Query Parameters:
        - project_id: Optional project scope

    Returns:
        {
            "bridges": [
                ["entity_id_1", "entity_id_2"],
                ["entity_id_5", "entity_id_6"]
            ],
            "count": 2
        }
    """
    try:
        project_id = request.args.get('project_id')

        bridges = analytics_service.identify_bridges(project_id=project_id)

        return jsonify({
            'bridges': bridges,
            'count': len(bridges)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@graphrag_bp.route('/analytics/articulation-points', methods=['GET'])
def identify_articulation_points():
    """
    Identify articulation points (critical nodes)

    Query Parameters:
        - project_id: Optional project scope

    Returns:
        {
            "articulation_points": ["entity_id_1", "entity_id_5", ...],
            "count": 3
        }
    """
    try:
        project_id = request.args.get('project_id')

        points = analytics_service.identify_articulation_points(project_id=project_id)

        return jsonify({
            'articulation_points': points,
            'count': len(points)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@graphrag_bp.route('/cache/invalidate', methods=['POST'])
def invalidate_cache():
    """
    Invalidate query and analytics cache

    Request Body:
        {
            "entity_ids": ["uuid-1", "uuid-2"],  // optional
            "reason": "manual_invalidation"
        }

    Returns:
        {
            "message": "Cache invalidated successfully"
        }
    """
    try:
        data = request.get_json() or {}

        entity_ids = data.get('entity_ids')
        reason = data.get('reason', 'manual_invalidation')

        # Invalidate query cache
        graphrag_service.invalidate_cache(entity_ids=entity_ids, reason=reason)

        # Invalidate analytics cache
        analytics_service.invalidate_analytics_cache()

        return jsonify({'message': 'Cache invalidated successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@graphrag_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint

    Returns:
        {
            "status": "healthy",
            "services": {
                "graphrag": true,
                "analytics": true
            },
            "timestamp": "2025-11-18T12:00:00"
        }
    """
    return jsonify({
        'status': 'healthy',
        'services': {
            'graphrag': graphrag_service is not None,
            'analytics': analytics_service is not None
        },
        'timestamp': datetime.now().isoformat()
    }), 200


# Error handlers
@graphrag_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request', 'message': str(error)}), 400


@graphrag_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found', 'message': str(error)}), 404


@graphrag_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error', 'message': str(error)}), 500
