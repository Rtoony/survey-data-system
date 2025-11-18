"""
AI Search API Routes - Semantic Search and Vector Similarity Endpoints

This module provides REST API endpoints for semantic search:
- Find similar entities by ID or text
- Cross-project similarity search
- Semantic clustering and duplicate detection
- Autocomplete with semantic understanding

Author: AI Agent Toolkit
Date: 2025-11-18
"""

from flask import Blueprint, request, jsonify
from services.semantic_search_service import get_semantic_search_service
from datetime import datetime

# Create blueprint
ai_search_bp = Blueprint('ai_search', __name__, url_prefix='/api/ai/search')

# Get service instance
search_service = get_semantic_search_service()


@ai_search_bp.route('/similar/entity/<entity_id>', methods=['GET'])
def find_similar_entities(entity_id: str):
    """
    Find entities similar to a given entity

    Query Parameters:
        - entity_type: Optional entity type filter
        - similarity_threshold: Minimum similarity (0-1, default 0.7)
        - max_results: Maximum results (default 50)
        - include_cross_type: Include different entity types (default true)

    Returns:
        [
            {
                "entity_id": "...",
                "entity_type": "...",
                "canonical_name": "...",
                "similarity_score": 0.95,
                ...
            }
        ]
    """
    try:
        entity_type = request.args.get('entity_type')
        similarity_threshold = float(request.args.get('similarity_threshold', 0.7))
        max_results = int(request.args.get('max_results', 50))
        include_cross_type = request.args.get('include_cross_type', 'true').lower() == 'true'

        results = search_service.find_similar_entities(
            entity_id=entity_id,
            entity_type=entity_type,
            similarity_threshold=similarity_threshold,
            max_results=max_results,
            include_cross_type=include_cross_type
        )

        return jsonify(results), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_search_bp.route('/similar/text', methods=['POST'])
def find_similar_by_text():
    """
    Find entities similar to a text description

    Request Body:
        {
            "search_text": "storm drain manhole with concrete material",
            "entity_type": "utility_structure",  // optional
            "similarity_threshold": 0.7,         // optional
            "max_results": 50                    // optional
        }

    Returns:
        [
            {
                "entity_id": "...",
                "canonical_name": "...",
                "similarity_score": 0.88,
                ...
            }
        ]
    """
    try:
        data = request.get_json()

        if not data or 'search_text' not in data:
            return jsonify({'error': 'search_text is required'}), 400

        results = search_service.find_similar_by_text(
            search_text=data['search_text'],
            entity_type=data.get('entity_type'),
            similarity_threshold=data.get('similarity_threshold'),
            max_results=data.get('max_results')
        )

        return jsonify(results), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_search_bp.route('/similar/projects/<project_id>', methods=['GET'])
def find_similar_projects(project_id: str):
    """
    Find projects similar to a given project

    Query Parameters:
        - similarity_threshold: Minimum similarity (default 0.7)
        - max_results: Maximum results (default 10)

    Returns:
        [
            {
                "project_id": "...",
                "project_name": "...",
                "similarity_score": 0.85,
                "entity_count": 150,
                ...
            }
        ]
    """
    try:
        similarity_threshold = float(request.args.get('similarity_threshold', 0.7))
        max_results = int(request.args.get('max_results', 10))

        results = search_service.find_similar_projects(
            project_id=project_id,
            similarity_threshold=similarity_threshold,
            max_results=max_results
        )

        return jsonify(results), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_search_bp.route('/cluster', methods=['POST'])
def cluster_entities():
    """
    Cluster entities based on embeddings

    Request Body:
        {
            "entity_ids": ["uuid-1", "uuid-2", ...],
            "num_clusters": 5,
            "method": "kmeans"  // kmeans, hierarchical, dbscan
        }

    Returns:
        {
            "clusters": [
                {
                    "cluster_id": 0,
                    "entity_ids": [...],
                    "size": 10
                }
            ],
            "method": "kmeans",
            "num_clusters": 5
        }
    """
    try:
        data = request.get_json()

        if not data or 'entity_ids' not in data:
            return jsonify({'error': 'entity_ids is required'}), 400

        result = search_service.cluster_entities(
            entity_ids=data['entity_ids'],
            num_clusters=data.get('num_clusters', 5),
            method=data.get('method', 'kmeans')
        )

        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_search_bp.route('/duplicates', methods=['GET'])
def find_duplicates():
    """
    Find potential duplicate entities

    Query Parameters:
        - entity_type: Optional entity type filter
        - similarity_threshold: High threshold (default 0.95)
        - max_results: Maximum duplicate pairs (default 100)

    Returns:
        [
            {
                "entity1_id": "...",
                "entity1_name": "...",
                "entity2_id": "...",
                "entity2_name": "...",
                "similarity_score": 0.98
            }
        ]
    """
    try:
        entity_type = request.args.get('entity_type')
        similarity_threshold = float(request.args.get('similarity_threshold', 0.95))
        max_results = int(request.args.get('max_results', 100))

        results = search_service.find_semantic_duplicates(
            entity_type=entity_type,
            similarity_threshold=similarity_threshold,
            max_results=max_results
        )

        return jsonify(results), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_search_bp.route('/autocomplete', methods='GET'])
def autocomplete():
    """
    Semantic autocomplete suggestions

    Query Parameters:
        - q: Partial query text
        - entity_type: Optional entity type filter
        - max_results: Maximum suggestions (default 10)

    Returns:
        [
            {
                "entity_id": "...",
                "canonical_name": "...",
                "entity_type": "...",
                "quality_score": 0.95
            }
        ]
    """
    try:
        partial_query = request.args.get('q', '')
        entity_type = request.args.get('entity_type')
        max_results = int(request.args.get('max_results', 10))

        if not partial_query:
            return jsonify([]), 200

        results = search_service.semantic_autocomplete(
            partial_query=partial_query,
            entity_type=entity_type,
            max_results=max_results
        )

        return jsonify(results), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_search_bp.route('/similarity-matrix', methods=['POST'])
def compute_similarity_matrix():
    """
    Compute pairwise similarity matrix

    Request Body:
        {
            "entity_ids": ["uuid-1", "uuid-2", "uuid-3", ...]
        }

    Returns:
        {
            "similarity_matrix": {
                "uuid-1": {"uuid-1": 1.0, "uuid-2": 0.85, ...},
                "uuid-2": {"uuid-1": 0.85, "uuid-2": 1.0, ...}
            },
            "entities": [...],
            "size": 3
        }
    """
    try:
        data = request.get_json()

        if not data or 'entity_ids' not in data:
            return jsonify({'error': 'entity_ids is required'}), 400

        result = search_service.compute_entity_similarity_matrix(
            entity_ids=data['entity_ids']
        )

        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_search_bp.route('/trending', methods=['GET'])
def get_trending_searches():
    """
    Get trending searches from query history

    Query Parameters:
        - days: Number of days to look back (default 7)
        - limit: Maximum results (default 10)

    Returns:
        [
            {
                "query_text": "...",
                "search_count": 25,
                "avg_results": 12.5,
                "last_searched": "2025-11-18T10:00:00"
            }
        ]
    """
    try:
        days = int(request.args.get('days', 7))
        limit = int(request.args.get('limit', 10))

        results = search_service.get_trending_searches(
            days=days,
            limit=limit
        )

        return jsonify(results), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_search_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint

    Returns:
        {
            "status": "healthy",
            "timestamp": "2025-11-18T12:00:00"
        }
    """
    return jsonify({
        'status': 'healthy',
        'service': 'semantic_search',
        'timestamp': datetime.now().isoformat()
    }), 200


# Error handlers
@ai_search_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request', 'message': str(error)}), 400


@ai_search_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found', 'message': str(error)}), 404


@ai_search_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error', 'message': str(error)}), 500
