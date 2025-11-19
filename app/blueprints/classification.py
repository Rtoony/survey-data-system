"""
Classification Blueprint
Handles entity classification, AI suggestions, review queue, and analytics
Extracted from app.py during Phase 13 refactoring
"""
from flask import Blueprint, render_template, jsonify, request, session, Response
from typing import Dict, List, Any, Optional
from database import get_db, execute_query, DB_CONFIG

classification_bp = Blueprint('classification', __name__)


# ============================================
# PAGE ROUTES (HTML Templates)
# ============================================

@classification_bp.route('/tools/classification-review')
def classification_review_tool():
    """Classification Review - Review and classify uncertain entities"""
    return render_template('tools/classification_review.html')


@classification_bp.route('/tools/classification-analytics')
def classification_analytics_tool():
    """Classification Analytics - Track accuracy and performance metrics"""
    return render_template('tools/classification_analytics.html')


# ============================================
# CLASSIFICATION REVIEW API ENDPOINTS
# ============================================

@classification_bp.route('/api/classification/review-queue', methods=['GET'])
def get_classification_review_queue() -> tuple[Dict[str, Any], int]:
    """Get entities needing classification review"""
    try:
        project_id = session.get('active_project_id')
        if not project_id:
            return jsonify({'error': 'No active project selected'}), 400

        min_confidence = float(request.args.get('min_confidence', 0.0))
        max_confidence = float(request.args.get('max_confidence', 1.0))
        limit = int(request.args.get('limit', 100))

        from services.classification_service import ClassificationService

        with get_db() as conn:
            service = ClassificationService(DB_CONFIG, conn=conn)
            entities = service.get_review_queue(
                project_id=project_id,
                min_confidence=min_confidence,
                max_confidence=max_confidence,
                limit=limit
            )

        return jsonify({
            'success': True,
            'count': len(entities),
            'entities': entities
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@classification_bp.route('/api/classification/reclassify', methods=['POST'])
def reclassify_entity() -> tuple[Dict[str, Any], int]:
    """Reclassify a single entity"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400
        entity_id = data.get('entity_id')
        new_type = data.get('new_type')
        user_notes = data.get('notes')

        if not entity_id or not new_type:
            return jsonify({'error': 'entity_id and new_type required'}), 400

        from services.classification_service import ClassificationService

        with get_db() as conn:
            service = ClassificationService(DB_CONFIG, conn=conn)
            result = service.reclassify_entity(entity_id, new_type, user_notes)

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@classification_bp.route('/api/classification/bulk-reclassify', methods=['POST'])
def bulk_reclassify() -> tuple[Dict[str, Any], int]:
    """Reclassify multiple entities at once"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400
        entity_ids = data.get('entity_ids', [])
        new_type = data.get('new_type')
        user_notes = data.get('notes')

        if not entity_ids or not new_type:
            return jsonify({'error': 'entity_ids and new_type required'}), 400

        from services.classification_service import ClassificationService

        with get_db() as conn:
            service = ClassificationService(DB_CONFIG, conn=conn)
            result = service.bulk_reclassify(entity_ids, new_type, user_notes)

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@classification_bp.route('/api/classification/ai-suggestions/<entity_id>', methods=['GET'])
def get_ai_classification_suggestions(entity_id: str) -> tuple[Dict[str, Any], int]:
    """Get AI-powered classification suggestions using vector embeddings"""
    try:
        limit = int(request.args.get('limit', 5))

        from services.ai_classification_service import AIClassificationService

        with get_db() as conn:
            ai_service = AIClassificationService(DB_CONFIG, conn=conn)
            suggestions = ai_service.get_ai_suggestions(entity_id, limit=limit)

        return jsonify({
            'success': True,
            'entity_id': entity_id,
            'suggestions': suggestions
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@classification_bp.route('/api/classification/spatial-context/<entity_id>', methods=['GET'])
def get_spatial_context(entity_id: str) -> tuple[Dict[str, Any], int]:
    """Get spatial context for an entity to aid classification"""
    try:
        search_radius = float(request.args.get('radius', 100.0))

        from services.ai_classification_service import AIClassificationService

        with get_db() as conn:
            ai_service = AIClassificationService(DB_CONFIG, conn=conn)
            context = ai_service.get_spatial_context(entity_id, search_radius_feet=search_radius)

        return jsonify({
            'success': True,
            'entity_id': entity_id,
            'context': context
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@classification_bp.route('/api/classification/analytics', methods=['GET'])
def get_classification_analytics() -> tuple[Dict[str, Any], int]:
    """Get classification analytics and accuracy metrics"""
    try:
        project_id = session.get('active_project_id')
        days_back = int(request.args.get('days', 30))

        from services.ai_classification_service import AIClassificationService

        with get_db() as conn:
            ai_service = AIClassificationService(DB_CONFIG, conn=conn)
            analytics = ai_service.get_classification_analytics(
                project_id=project_id,
                days_back=days_back
            )

        return jsonify({
            'success': True,
            'analytics': analytics
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@classification_bp.route('/api/classification/geometry-preview/<entity_id>', methods=['GET'])
def get_geometry_preview(entity_id: str) -> tuple[Response, int]:
    """Get SVG preview of entity geometry"""
    try:
        width = int(request.args.get('width', 400))
        height = int(request.args.get('height', 300))

        from services.geometry_preview_service import GeometryPreviewService

        with get_db() as conn:
            preview_service = GeometryPreviewService(DB_CONFIG, conn=conn)
            svg = preview_service.generate_svg(entity_id, width=width, height=height)

        return Response(svg, mimetype='image/svg+xml')

    except Exception as e:
        return Response(
            f'<svg><text x="10" y="20" fill="red">Error: {str(e)}</text></svg>',
            mimetype='image/svg+xml'
        ), 500


@classification_bp.route('/api/classification/geometry-thumbnail/<entity_id>', methods=['GET'])
def get_geometry_thumbnail(entity_id: str) -> tuple[Response, int]:
    """Get small thumbnail preview of entity geometry"""
    try:
        size = int(request.args.get('size', 100))

        from services.geometry_preview_service import GeometryPreviewService

        with get_db() as conn:
            preview_service = GeometryPreviewService(DB_CONFIG, conn=conn)
            svg = preview_service.generate_thumbnail(entity_id, size=size)

        return Response(svg, mimetype='image/svg+xml')

    except Exception as e:
        return Response(
            f'<svg><text x="10" y="20" fill="red">Error</text></svg>',
            mimetype='image/svg+xml'
        ), 500


@classification_bp.route('/api/classification/vocabulary', methods=['GET'])
def get_classification_vocabulary() -> tuple[Dict[str, Any], int]:
    """Get object types from CAD vocabulary for classification dropdowns"""
    try:
        query = """
            SELECT
                ot.code,
                ot.full_name,
                ot.database_table,
                c.code as category_code,
                c.full_name as category_name,
                d.code as discipline_code,
                d.full_name as discipline_name
            FROM object_type_codes ot
            LEFT JOIN category_codes c ON ot.category_id = c.category_id
            LEFT JOIN discipline_codes d ON c.discipline_id = d.discipline_id
            WHERE ot.is_active = true
            ORDER BY d.full_name, c.full_name, ot.full_name
        """

        types = execute_query(query)

        # Group by discipline for easier UI consumption
        grouped: Dict[str, Any] = {}
        for t in types:
            disc = t['discipline_code']
            if disc not in grouped:
                grouped[disc] = {
                    'name': t['discipline_name'],
                    'categories': {}
                }

            cat = t['category_code']
            if cat not in grouped[disc]['categories']:
                grouped[disc]['categories'][cat] = {
                    'name': t['category_name'],
                    'types': []
                }

            grouped[disc]['categories'][cat]['types'].append({
                'code': t['code'],
                'name': t['full_name'],
                'table': t['database_table']
            })

        return jsonify({
            'success': True,
            'vocabulary': grouped
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
