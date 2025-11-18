"""
Flask API routes for Relationship Graph Management System.

Provides REST endpoints for:
- Relationship edge CRUD operations
- Graph traversal and querying
- Relationship validation
- Analytics and metrics
- Relationship type management

References:
    - docs/PHASE_3_COMPREHENSIVE_ANALYSIS.md
    - services/relationship_graph_service.py
    - services/relationship_query_service.py
    - services/relationship_validation_service.py
    - services/relationship_analytics_service.py
"""

import sys
from pathlib import Path
from flask import Blueprint, jsonify, request
import json

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from services.relationship_graph_service import RelationshipGraphService
from services.relationship_query_service import RelationshipQueryService
from services.relationship_validation_service import RelationshipValidationService
from services.relationship_analytics_service import RelationshipAnalyticsService

# Create Blueprint
relationship_bp = Blueprint('relationships', __name__, url_prefix='/api/relationships')


# ============================================================================
# RELATIONSHIP EDGE CRUD OPERATIONS
# ============================================================================

@relationship_bp.route('/edges', methods=['POST'])
def create_edge():
    """Create a new relationship edge."""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['project_id', 'source_entity_type', 'source_entity_id',
                          'target_entity_type', 'target_entity_id', 'relationship_type']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        service = RelationshipGraphService()
        result = service.create_edge(
            project_id=data['project_id'],
            source_entity_type=data['source_entity_type'],
            source_entity_id=data['source_entity_id'],
            target_entity_type=data['target_entity_type'],
            target_entity_id=data['target_entity_id'],
            relationship_type=data['relationship_type'],
            relationship_strength=data.get('relationship_strength'),
            is_bidirectional=data.get('is_bidirectional', False),
            relationship_metadata=data.get('relationship_metadata', {}),
            created_by=data.get('created_by'),
            source=data.get('source', 'manual'),
            confidence_score=data.get('confidence_score'),
            valid_from=data.get('valid_from'),
            valid_to=data.get('valid_to')
        )

        return jsonify({
            'success': True,
            'edge': result
        }), 201

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@relationship_bp.route('/edges/batch', methods=['POST'])
def create_edges_batch():
    """Create multiple relationship edges in a batch."""
    try:
        data = request.get_json()

        if not data or 'project_id' not in data or 'edges' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing project_id or edges array'
            }), 400

        service = RelationshipGraphService()
        results = service.create_edges_batch(
            project_id=data['project_id'],
            edges=data['edges']
        )

        return jsonify({
            'success': True,
            'edges': results,
            'count': len(results)
        }), 201

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@relationship_bp.route('/edges/<edge_id>', methods=['GET'])
def get_edge(edge_id):
    """Get a single relationship edge by ID."""
    try:
        service = RelationshipGraphService()
        result = service.get_edge(edge_id)

        if not result:
            return jsonify({
                'success': False,
                'error': 'Edge not found'
            }), 404

        return jsonify({
            'success': True,
            'edge': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@relationship_bp.route('/edges', methods=['GET'])
def get_edges():
    """Query relationship edges with filtering."""
    try:
        service = RelationshipGraphService()

        # Extract query parameters
        project_id = request.args.get('project_id')
        source_entity_type = request.args.get('source_entity_type')
        source_entity_id = request.args.get('source_entity_id')
        target_entity_type = request.args.get('target_entity_type')
        target_entity_id = request.args.get('target_entity_id')
        relationship_type = request.args.get('relationship_type')
        is_active = request.args.get('is_active', 'true').lower() == 'true'
        limit = int(request.args.get('limit', 1000))
        offset = int(request.args.get('offset', 0))

        results = service.get_edges(
            project_id=project_id,
            source_entity_type=source_entity_type,
            source_entity_id=source_entity_id,
            target_entity_type=target_entity_type,
            target_entity_id=target_entity_id,
            relationship_type=relationship_type,
            is_active=is_active,
            limit=limit,
            offset=offset
        )

        return jsonify({
            'success': True,
            'edges': results,
            'count': len(results),
            'limit': limit,
            'offset': offset
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@relationship_bp.route('/edges/<edge_id>', methods=['PUT', 'PATCH'])
def update_edge(edge_id):
    """Update an existing relationship edge."""
    try:
        data = request.get_json()
        service = RelationshipGraphService()

        result = service.update_edge(edge_id, **data)

        return jsonify({
            'success': True,
            'edge': result
        })

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@relationship_bp.route('/edges/<edge_id>', methods=['DELETE'])
def delete_edge(edge_id):
    """Delete a relationship edge."""
    try:
        soft_delete = request.args.get('soft', 'true').lower() == 'true'
        service = RelationshipGraphService()

        service.delete_edge(edge_id, soft_delete=soft_delete)

        return jsonify({
            'success': True,
            'message': 'Edge deleted successfully'
        })

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# GRAPH QUERYING & TRAVERSAL
# ============================================================================

@relationship_bp.route('/query/related', methods=['GET'])
def get_related_entities():
    """Get entities related to a given entity."""
    try:
        entity_type = request.args.get('entity_type')
        entity_id = request.args.get('entity_id')
        project_id = request.args.get('project_id')
        relationship_type = request.args.get('relationship_type')
        direction = request.args.get('direction', 'both')

        if not entity_type or not entity_id:
            return jsonify({
                'success': False,
                'error': 'Missing entity_type or entity_id'
            }), 400

        service = RelationshipQueryService()
        results = service.get_related_entities(
            entity_type=entity_type,
            entity_id=entity_id,
            project_id=project_id,
            relationship_type=relationship_type,
            direction=direction
        )

        return jsonify({
            'success': True,
            'related_entities': results,
            'count': len(results)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@relationship_bp.route('/query/subgraph', methods=['GET'])
def get_subgraph():
    """Get subgraph centered on an entity."""
    try:
        entity_type = request.args.get('entity_type')
        entity_id = request.args.get('entity_id')
        project_id = request.args.get('project_id')
        depth = int(request.args.get('depth', 2))
        relationship_types = request.args.getlist('relationship_types')

        if not entity_type or not entity_id or not project_id:
            return jsonify({
                'success': False,
                'error': 'Missing required parameters'
            }), 400

        service = RelationshipQueryService()
        result = service.get_entity_subgraph(
            entity_type=entity_type,
            entity_id=entity_id,
            project_id=project_id,
            depth=depth,
            relationship_types=relationship_types if relationship_types else None
        )

        return jsonify({
            'success': True,
            'subgraph': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@relationship_bp.route('/query/path', methods=['GET'])
def find_path():
    """Find shortest path between two entities."""
    try:
        project_id = request.args.get('project_id')
        source_entity_type = request.args.get('source_entity_type')
        source_entity_id = request.args.get('source_entity_id')
        target_entity_type = request.args.get('target_entity_type')
        target_entity_id = request.args.get('target_entity_id')
        max_depth = int(request.args.get('max_depth', 5))

        if not all([project_id, source_entity_type, source_entity_id,
                   target_entity_type, target_entity_id]):
            return jsonify({
                'success': False,
                'error': 'Missing required parameters'
            }), 400

        service = RelationshipQueryService()
        path = service.find_path(
            project_id=project_id,
            source_entity_type=source_entity_type,
            source_entity_id=source_entity_id,
            target_entity_type=target_entity_type,
            target_entity_id=target_entity_id,
            max_depth=max_depth
        )

        if path is None:
            return jsonify({
                'success': True,
                'path': None,
                'message': 'No path found'
            })

        return jsonify({
            'success': True,
            'path': path,
            'length': len(path)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@relationship_bp.route('/query/cycles', methods=['GET'])
def detect_cycles():
    """Detect cycles in the relationship graph."""
    try:
        project_id = request.args.get('project_id')

        if not project_id:
            return jsonify({
                'success': False,
                'error': 'Missing project_id'
            }), 400

        service = RelationshipQueryService()
        cycles = service.detect_cycles(project_id)

        return jsonify({
            'success': True,
            'cycles': cycles,
            'count': len(cycles)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# VALIDATION
# ============================================================================

@relationship_bp.route('/validate/<project_id>', methods=['POST'])
def validate_project(project_id):
    """Run validation rules on a project's relationships."""
    try:
        data = request.get_json() or {}
        rule_types = data.get('rule_types')

        service = RelationshipValidationService()
        violations = service.validate_project_relationships(
            project_id=project_id,
            rule_types=rule_types
        )

        return jsonify({
            'success': True,
            'violations': violations,
            'count': len(violations)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@relationship_bp.route('/violations/<project_id>', methods=['GET'])
def get_violations(project_id):
    """Get violations for a project."""
    try:
        status = request.args.get('status')
        severity = request.args.get('severity')
        limit = int(request.args.get('limit', 100))

        service = RelationshipValidationService()
        violations = service.get_violations(
            project_id=project_id,
            status=status,
            severity=severity,
            limit=limit
        )

        return jsonify({
            'success': True,
            'violations': violations,
            'count': len(violations)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@relationship_bp.route('/violations/<violation_id>/resolve', methods=['POST'])
def resolve_violation(violation_id):
    """Mark a violation as resolved."""
    try:
        data = request.get_json() or {}
        resolution_notes = data.get('resolution_notes')
        resolved_by = data.get('resolved_by')

        service = RelationshipValidationService()
        result = service.resolve_violation(
            violation_id=violation_id,
            resolution_notes=resolution_notes,
            resolved_by=resolved_by
        )

        return jsonify({
            'success': True,
            'violation': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# ANALYTICS
# ============================================================================

@relationship_bp.route('/analytics/<project_id>/density', methods=['GET'])
def get_density(project_id):
    """Get relationship density metrics."""
    try:
        service = RelationshipAnalyticsService()
        result = service.get_relationship_density(project_id)

        return jsonify({
            'success': True,
            'density': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@relationship_bp.route('/analytics/<project_id>/summary', methods=['GET'])
def get_summary(project_id):
    """Get comprehensive relationship summary."""
    try:
        service = RelationshipAnalyticsService()
        result = service.get_comprehensive_summary(project_id)

        return jsonify({
            'success': True,
            'summary': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@relationship_bp.route('/analytics/<project_id>/health', methods=['GET'])
def get_health(project_id):
    """Get project relationship health score."""
    try:
        service = RelationshipAnalyticsService()
        result = service.get_project_health_score(project_id)

        return jsonify({
            'success': True,
            'health': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@relationship_bp.route('/analytics/<project_id>/most-connected', methods=['GET'])
def get_most_connected(project_id):
    """Get most connected entities."""
    try:
        limit = int(request.args.get('limit', 10))
        entity_type = request.args.get('entity_type')

        service = RelationshipAnalyticsService()
        results = service.get_most_connected_entities(
            project_id=project_id,
            limit=limit,
            entity_type=entity_type
        )

        return jsonify({
            'success': True,
            'entities': results
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# RELATIONSHIP TYPE MANAGEMENT
# ============================================================================

@relationship_bp.route('/types', methods=['GET'])
def get_relationship_types():
    """Get all registered relationship types."""
    try:
        service = RelationshipGraphService()
        types = service.get_relationship_types()

        return jsonify({
            'success': True,
            'types': types,
            'count': len(types)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@relationship_bp.route('/types/<type_code>', methods=['GET'])
def get_relationship_type(type_code):
    """Get a specific relationship type definition."""
    try:
        service = RelationshipGraphService()
        result = service.get_relationship_type(type_code)

        if not result:
            return jsonify({
                'success': False,
                'error': 'Relationship type not found'
            }), 404

        return jsonify({
            'success': True,
            'type': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@relationship_bp.route('/stats/<project_id>', methods=['GET'])
def get_stats(project_id):
    """Get overall statistics for a project's relationships."""
    try:
        query_service = RelationshipQueryService()
        graph_service = RelationshipGraphService()

        total_edges = graph_service.get_edge_count(project_id=project_id, is_active=True)
        summary = query_service.get_relationship_summary(project_id)

        return jsonify({
            'success': True,
            'stats': {
                'total_edges': total_edges,
                'summary': summary
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@relationship_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'service': 'Relationship Graph Management API',
        'version': '1.0.0'
    })
