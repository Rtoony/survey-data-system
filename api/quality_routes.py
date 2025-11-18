"""
Quality Scoring API Routes - Entity Quality Analytics Endpoints

This module provides REST API endpoints for quality scoring:
- Entity quality details and history
- Project quality summaries
- Quality score recalculation
- Quality trends and analytics

Author: AI Agent Toolkit
Date: 2025-11-18
"""

from flask import Blueprint, request, jsonify
from database import execute_query
from datetime import datetime, timedelta

# Create blueprint
quality_bp = Blueprint('quality', __name__, url_prefix='/api/ai/quality')


@quality_bp.route('/entity/<entity_id>', methods=['GET'])
def get_entity_quality(entity_id: str):
    """
    Get quality details for a specific entity

    Returns:
        {
            "entity_id": "...",
            "entity_type": "...",
            "canonical_name": "...",
            "quality_score": 0.85,
            "quality_factors": {
                "has_embedding": true,
                "has_relationships": true,
                "completeness": 0.9,
                "relationship_count": 5
            },
            "last_updated": "2025-11-18T12:00:00"
        }
    """
    try:
        query = """
            SELECT
                se.entity_id,
                se.entity_type,
                se.canonical_name,
                se.description,
                se.quality_score,
                (SELECT COUNT(*) FROM entity_embeddings WHERE entity_id = se.entity_id AND is_current = TRUE) > 0 as has_embedding,
                (SELECT COUNT(*) FROM entity_relationships WHERE subject_entity_id = se.entity_id OR object_entity_id = se.entity_id) as relationship_count
            FROM standards_entities se
            WHERE se.entity_id = %s
        """

        result = execute_query(query, (entity_id,))

        if not result:
            return jsonify({'error': 'Entity not found'}), 404

        entity = result[0]

        # Build quality factors
        quality_factors = {
            'has_embedding': entity['has_embedding'],
            'has_relationships': entity['relationship_count'] > 0,
            'relationship_count': entity['relationship_count'],
            'completeness': min(1.0, entity['relationship_count'] / 3.0)  # Simple heuristic
        }

        return jsonify({
            'entity_id': entity['entity_id'],
            'entity_type': entity['entity_type'],
            'canonical_name': entity['canonical_name'],
            'description': entity['description'],
            'quality_score': float(entity['quality_score']) if entity['quality_score'] else 0.0,
            'quality_factors': quality_factors,
            'last_updated': datetime.now().isoformat()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@quality_bp.route('/entity/<entity_id>/history', methods=['GET'])
def get_quality_history(entity_id: str):
    """
    Get quality score history for an entity

    Query Parameters:
        - days: Number of days to look back (default 30)
        - limit: Maximum history entries (default 100)

    Returns:
        [
            {
                "quality_score": 0.85,
                "previous_score": 0.80,
                "score_delta": 0.05,
                "trigger_event": "embedding_added",
                "calculated_at": "2025-11-18T12:00:00"
            }
        ]
    """
    try:
        days = int(request.args.get('days', 30))
        limit = int(request.args.get('limit', 100))

        query = """
            SELECT
                quality_score,
                previous_score,
                score_delta,
                score_factors,
                trigger_event,
                calculated_at
            FROM quality_history
            WHERE entity_id = %s
              AND calculated_at >= NOW() - INTERVAL '%s days'
            ORDER BY calculated_at DESC
            LIMIT %s
        """

        history = execute_query(query, (entity_id, days, limit))

        return jsonify(history), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@quality_bp.route('/project/<project_id>/summary', methods=['GET'])
def get_project_quality_summary(project_id: str):
    """
    Get quality summary for a project

    Returns:
        {
            "project_id": "...",
            "avg_quality_score": 0.82,
            "entity_count": 1500,
            "quality_distribution": {
                "excellent": 450,    // >= 0.9
                "good": 750,         // 0.7-0.9
                "fair": 250,         // 0.5-0.7
                "poor": 50           // < 0.5
            },
            "entities_with_embeddings": 1200,
            "entities_with_relationships": 1100,
            "timestamp": "2025-11-18T12:00:00"
        }
    """
    try:
        query = """
            SELECT
                COUNT(*) as entity_count,
                AVG(quality_score) as avg_quality_score,
                SUM(CASE WHEN quality_score >= 0.9 THEN 1 ELSE 0 END) as excellent,
                SUM(CASE WHEN quality_score >= 0.7 AND quality_score < 0.9 THEN 1 ELSE 0 END) as good,
                SUM(CASE WHEN quality_score >= 0.5 AND quality_score < 0.7 THEN 1 ELSE 0 END) as fair,
                SUM(CASE WHEN quality_score < 0.5 THEN 1 ELSE 0 END) as poor,
                SUM(CASE WHEN EXISTS (
                    SELECT 1 FROM entity_embeddings WHERE entity_id = se.entity_id AND is_current = TRUE
                ) THEN 1 ELSE 0 END) as entities_with_embeddings,
                SUM(CASE WHEN EXISTS (
                    SELECT 1 FROM entity_relationships WHERE subject_entity_id = se.entity_id OR object_entity_id = se.entity_id
                ) THEN 1 ELSE 0 END) as entities_with_relationships
            FROM standards_entities se
            WHERE se.attributes->>'project_id' = %s
        """

        result = execute_query(query, (project_id,))

        if not result or result[0]['entity_count'] == 0:
            return jsonify({
                'project_id': project_id,
                'entity_count': 0,
                'message': 'No entities found for project'
            }), 200

        summary = result[0]

        return jsonify({
            'project_id': project_id,
            'avg_quality_score': round(float(summary['avg_quality_score'] or 0), 2),
            'entity_count': summary['entity_count'],
            'quality_distribution': {
                'excellent': summary['excellent'] or 0,
                'good': summary['good'] or 0,
                'fair': summary['fair'] or 0,
                'poor': summary['poor'] or 0
            },
            'entities_with_embeddings': summary['entities_with_embeddings'] or 0,
            'entities_with_relationships': summary['entities_with_relationships'] or 0,
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@quality_bp.route('/trends', methods=['GET'])
def get_quality_trends():
    """
    Get quality score trends over time

    Query Parameters:
        - entity_type: Optional entity type filter
        - days: Number of days (default 30)

    Returns:
        [
            {
                "entity_type": "utility_structure",
                "date": "2025-11-18",
                "avg_score": 0.85,
                "score_changes": 15,
                "improvements": 12,
                "degradations": 3
            }
        ]
    """
    try:
        entity_type = request.args.get('entity_type')
        days = int(request.args.get('days', 30))

        type_filter = ""
        params = [days]

        if entity_type:
            type_filter = "AND entity_type = %s"
            params.append(entity_type)

        query = f"""
            SELECT
                entity_type,
                DATE(calculated_at) as date,
                AVG(quality_score) as avg_score,
                COUNT(*) as score_changes,
                SUM(CASE WHEN score_delta > 0 THEN 1 ELSE 0 END) as improvements,
                SUM(CASE WHEN score_delta < 0 THEN 1 ELSE 0 END) as degradations
            FROM quality_history
            WHERE calculated_at >= NOW() - INTERVAL '%s days'
              {type_filter}
            GROUP BY entity_type, DATE(calculated_at)
            ORDER BY date DESC, entity_type
        """

        trends = execute_query(query, tuple(params))

        return jsonify(trends), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@quality_bp.route('/low-quality-entities', methods=['GET'])
def get_low_quality_entities():
    """
    Get entities with low quality scores

    Query Parameters:
        - threshold: Quality score threshold (default 0.5)
        - entity_type: Optional entity type filter
        - limit: Maximum results (default 100)

    Returns:
        [
            {
                "entity_id": "...",
                "entity_type": "...",
                "canonical_name": "...",
                "quality_score": 0.35,
                "issues": ["no_embedding", "no_relationships", "incomplete_attributes"]
            }
        ]
    """
    try:
        threshold = float(request.args.get('threshold', 0.5))
        entity_type = request.args.get('entity_type')
        limit = int(request.args.get('limit', 100))

        type_filter = ""
        params = [threshold]

        if entity_type:
            type_filter = "AND se.entity_type = %s"
            params.append(entity_type)

        query = f"""
            SELECT
                se.entity_id,
                se.entity_type,
                se.canonical_name,
                se.description,
                se.quality_score,
                CASE WHEN EXISTS (
                    SELECT 1 FROM entity_embeddings WHERE entity_id = se.entity_id AND is_current = TRUE
                ) THEN FALSE ELSE TRUE END as missing_embedding,
                CASE WHEN EXISTS (
                    SELECT 1 FROM entity_relationships WHERE subject_entity_id = se.entity_id OR object_entity_id = se.entity_id
                ) THEN FALSE ELSE TRUE END as missing_relationships
            FROM standards_entities se
            WHERE se.quality_score < %s
              {type_filter}
            ORDER BY se.quality_score ASC NULLS FIRST
            LIMIT %s
        """

        params.append(limit)
        entities = execute_query(query, tuple(params))

        # Add issues list
        for entity in entities:
            issues = []
            if entity.get('missing_embedding'):
                issues.append('no_embedding')
            if entity.get('missing_relationships'):
                issues.append('no_relationships')
            if not entity.get('description'):
                issues.append('no_description')

            entity['issues'] = issues
            # Remove temporary fields
            entity.pop('missing_embedding', None)
            entity.pop('missing_relationships', None)

        return jsonify(entities), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@quality_bp.route('/recalculate', methods=['POST'])
def recalculate_quality_scores():
    """
    Trigger quality score recalculation

    Request Body:
        {
            "entity_ids": ["uuid-1", "uuid-2"],  // optional, if not provided recalculates all
            "entity_type": "utility_structure"   // optional
        }

    Returns:
        {
            "message": "Quality scores recalculated",
            "entities_updated": 150
        }
    """
    try:
        data = request.get_json() or {}

        entity_ids = data.get('entity_ids')
        entity_type = data.get('entity_type')

        # This would trigger the quality score recalculation
        # For now, return a placeholder response
        # Full implementation would update quality_score column and insert into quality_history

        return jsonify({
            'message': 'Quality score recalculation triggered',
            'note': 'Implementation pending - would recalculate scores based on compute_quality_score function'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@quality_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'quality_scoring',
        'timestamp': datetime.now().isoformat()
    }), 200


# Error handlers
@quality_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request', 'message': str(error)}), 400


@quality_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found', 'message': str(error)}), 404


@quality_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error', 'message': str(error)}), 500
