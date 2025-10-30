"""
Flask API routes for ACAD-GIS AI toolkit.

Provides REST endpoints for:
- Loading standards
- Generating embeddings
- Building relationships
- Validating data
- Running maintenance
"""

import sys
from pathlib import Path
from flask import Blueprint, jsonify, request
import json

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from ingestion.standards_loader import StandardsLoader
from embeddings.embedding_generator import EmbeddingGenerator
from relationships.graph_builder import GraphBuilder
from validation.data_validator import DataValidator
from maintenance.db_maintenance import DatabaseMaintenance
from db_utils import get_entity_stats, get_table_stats

# Create Blueprint
toolkit_bp = Blueprint('toolkit', __name__, url_prefix='/api/toolkit')


# ============================================
# STATISTICS & STATUS
# ============================================

@toolkit_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get database and entity statistics."""
    try:
        entity_stats = get_entity_stats()
        table_stats = get_table_stats()
        
        return jsonify({
            'success': True,
            'entity_stats': entity_stats,
            'table_stats': table_stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================
# INGESTION
# ============================================

@toolkit_bp.route('/load/layers', methods=['POST'])
def load_layers():
    """Load layer standards from JSON data."""
    try:
        data = request.get_json()
        if not data or 'layers' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing layers data'
            }), 400
        
        loader = StandardsLoader()
        stats = loader.load_layers(data['layers'])
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@toolkit_bp.route('/load/blocks', methods=['POST'])
def load_blocks():
    """Load block definitions from JSON data."""
    try:
        data = request.get_json()
        if not data or 'blocks' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing blocks data'
            }), 400
        
        loader = StandardsLoader()
        stats = loader.load_blocks(data['blocks'])
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@toolkit_bp.route('/load/details', methods=['POST'])
def load_details():
    """Load detail standards from JSON data."""
    try:
        data = request.get_json()
        if not data or 'details' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing details data'
            }), 400
        
        loader = StandardsLoader()
        stats = loader.load_details(data['details'])
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================
# EMBEDDINGS
# ============================================

@toolkit_bp.route('/embeddings/generate', methods=['POST'])
def generate_embeddings():
    """
    Generate embeddings for a table.
    
    Body: {
        "table_name": "layer_standards",
        "text_columns": ["name", "description"],
        "limit": 100  // optional
    }
    """
    try:
        import os
        if not os.environ.get('OPENAI_API_KEY'):
            return jsonify({
                'success': False,
                'error': 'OPENAI_API_KEY not set'
            }), 400
        
        data = request.get_json()
        table_name = data.get('table_name')
        text_columns = data.get('text_columns', [])
        limit = data.get('limit')
        
        if not table_name or not text_columns:
            return jsonify({
                'success': False,
                'error': 'Missing table_name or text_columns'
            }), 400
        
        generator = EmbeddingGenerator(provider='openai', model='text-embedding-3-small')
        
        where_clause = f"WHERE entity_id IS NOT NULL"
        if limit:
            where_clause += f" LIMIT {limit}"
        
        stats = generator.generate_for_table(
            table_name=table_name,
            text_columns=text_columns,
            where_clause=where_clause
        )
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@toolkit_bp.route('/embeddings/refresh', methods=['POST'])
def refresh_embeddings():
    """
    Refresh old or missing embeddings.
    
    Body: {
        "entity_ids": ["uuid1", "uuid2"],  // optional
        "older_than_days": 30
    }
    """
    try:
        import os
        if not os.environ.get('OPENAI_API_KEY'):
            return jsonify({
                'success': False,
                'error': 'OPENAI_API_KEY not set'
            }), 400
        
        data = request.get_json() or {}
        entity_ids = data.get('entity_ids')
        older_than_days = data.get('older_than_days', 30)
        
        generator = EmbeddingGenerator(provider='openai', model='text-embedding-3-small')
        stats = generator.refresh_embeddings(
            entity_ids=entity_ids,
            older_than_days=older_than_days
        )
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================
# RELATIONSHIPS
# ============================================

@toolkit_bp.route('/relationships/spatial', methods=['POST'])
def create_spatial_relationships():
    """
    Create spatial relationships.
    
    Body: {
        "source_table": "parcels",
        "target_table": "utility_lines",
        "relationship_type": "contains",
        "distance_threshold": 10.0
    }
    """
    try:
        data = request.get_json()
        
        builder = GraphBuilder()
        count = builder.create_spatial_relationships(
            source_table=data.get('source_table'),
            target_table=data.get('target_table'),
            relationship_type=data.get('relationship_type'),
            distance_threshold=data.get('distance_threshold', 10.0)
        )
        
        return jsonify({
            'success': True,
            'count': count,
            'stats': builder.stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@toolkit_bp.route('/relationships/semantic', methods=['POST'])
def create_semantic_relationships():
    """
    Create semantic relationships from embeddings.
    
    Body: {
        "similarity_threshold": 0.85,
        "entity_types": ["layer", "block"],
        "limit_per_entity": 10
    }
    """
    try:
        data = request.get_json() or {}
        
        builder = GraphBuilder()
        count = builder.create_semantic_relationships(
            similarity_threshold=data.get('similarity_threshold', 0.85),
            entity_types=data.get('entity_types'),
            limit_per_entity=data.get('limit_per_entity', 10)
        )
        
        return jsonify({
            'success': True,
            'count': count,
            'stats': builder.stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@toolkit_bp.route('/relationships/build-complete', methods=['POST'])
def build_complete_graph():
    """Build complete knowledge graph (all relationship types)."""
    try:
        builder = GraphBuilder()
        stats = builder.build_complete_graph()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================
# VALIDATION
# ============================================

@toolkit_bp.route('/validate/all', methods=['GET'])
def validate_all():
    """Run comprehensive validation on all standards."""
    try:
        validator = DataValidator()
        results = validator.validate_all_standards()
        
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@toolkit_bp.route('/validate/table', methods=['POST'])
def validate_table():
    """
    Validate specific table.
    
    Body: {
        "table_name": "layer_standards",
        "required_fields": ["name"],
        "unique_fields": ["name"],
        "has_geometry": false
    }
    """
    try:
        data = request.get_json()
        table_name = data.get('table_name')
        
        if not table_name:
            return jsonify({
                'success': False,
                'error': 'Missing table_name'
            }), 400
        
        validator = DataValidator()
        results = validator.validate_table(
            table_name=table_name,
            required_fields=data.get('required_fields'),
            unique_fields=data.get('unique_fields'),
            has_geometry=data.get('has_geometry', False)
        )
        
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================
# MAINTENANCE
# ============================================

@toolkit_bp.route('/maintenance/refresh-views', methods=['POST'])
def refresh_views():
    """Refresh all materialized views."""
    try:
        maintenance = DatabaseMaintenance()
        result = maintenance.refresh_all_materialized_views()
        
        return jsonify({
            'success': result['success'],
            'duration': result.get('duration'),
            'error': result.get('error')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@toolkit_bp.route('/maintenance/recompute-quality', methods=['POST'])
def recompute_quality():
    """Recompute quality scores for all entities."""
    try:
        maintenance = DatabaseMaintenance()
        result = maintenance.recompute_all_quality_scores()
        
        return jsonify({
            'success': result['success'],
            'duration': result.get('duration'),
            'stats': result.get('stats'),
            'error': result.get('error')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@toolkit_bp.route('/maintenance/vacuum', methods=['POST'])
def vacuum_database():
    """Run VACUUM ANALYZE on database."""
    try:
        data = request.get_json() or {}
        full = data.get('full', False)
        
        maintenance = DatabaseMaintenance()
        result = maintenance.vacuum_analyze(full=full)
        
        return jsonify({
            'success': result['success'],
            'duration': result.get('duration'),
            'error': result.get('error')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@toolkit_bp.route('/maintenance/full', methods=['POST'])
def full_maintenance():
    """Run complete maintenance routine."""
    try:
        data = request.get_json() or {}
        include_vacuum_full = data.get('include_vacuum_full', False)
        
        maintenance = DatabaseMaintenance()
        results = maintenance.run_full_maintenance(include_vacuum_full=include_vacuum_full)
        
        return jsonify({
            'success': True,
            'results': results,
            'log': maintenance.maintenance_log
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================
# HEALTH CHECK
# ============================================

@toolkit_bp.route('/health', methods=['GET'])
def health_check():
    """Check toolkit health and API key status."""
    import os
    
    return jsonify({
        'success': True,
        'openai_api_key_set': bool(os.environ.get('OPENAI_API_KEY')),
        'database_url_set': bool(os.environ.get('DATABASE_URL')),
        'toolkit_version': '1.0.0'
    })
