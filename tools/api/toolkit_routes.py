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


# ============================================
# GRAPH VISUALIZATION
# ============================================

@toolkit_bp.route('/graph/data', methods=['GET'])
def get_graph_data():
    """
    Get nodes and edges for graph visualization.
    
    Query params:
    - limit: Max nodes to return (default 100)
    - relationship_types: Comma-separated types to include (spatial,semantic,engineering)
    - entity_types: Comma-separated entity types to include (layer,block,etc)
    """
    try:
        from db_utils import execute_query
        
        limit = request.args.get('limit', 100, type=int)
        relationship_types = request.args.get('relationship_types', '')
        entity_types = request.args.get('entity_types', '')
        
        # Build filters
        rel_filter = ""
        if relationship_types:
            types = [t.strip() for t in relationship_types.split(',')]
            rel_filter = f"AND relationship_category = ANY(ARRAY{types}::varchar[])"
        
        entity_filter = ""
        if entity_types:
            types = [t.strip() for t in entity_types.split(',')]
            entity_filter = f"AND entity_type = ANY(ARRAY{types}::varchar[])"
        
        # Get nodes (entities with relationships)
        nodes_query = f"""
            SELECT DISTINCT
                se.entity_id,
                se.entity_type,
                se.canonical_name,
                se.quality_score,
                se.tags,
                CASE 
                    WHEN EXISTS (
                        SELECT 1 FROM entity_embeddings ee 
                        WHERE ee.entity_id = se.entity_id
                    ) THEN true
                    ELSE false
                END as has_embedding
            FROM standards_entities se
            WHERE EXISTS (
                SELECT 1 FROM entity_relationships er
                WHERE er.source_entity_id = se.entity_id 
                   OR er.target_entity_id = se.entity_id
                   {rel_filter}
            )
            {entity_filter}
            LIMIT %s
        """
        nodes = execute_query(nodes_query, (limit,))
        
        # Get node IDs for edge filtering
        if nodes:
            node_ids = [n['entity_id'] for n in nodes]
            
            # Get edges (relationships between the nodes)
            edges_query = f"""
                SELECT 
                    er.relationship_id,
                    er.source_entity_id,
                    er.target_entity_id,
                    er.relationship_type,
                    er.relationship_category,
                    er.confidence,
                    er.metadata
                FROM entity_relationships er
                WHERE er.source_entity_id = ANY(%s::uuid[])
                  AND er.target_entity_id = ANY(%s::uuid[])
                  {rel_filter}
                LIMIT 500
            """
            edges = execute_query(edges_query, (node_ids, node_ids))
        else:
            edges = []
        
        return jsonify({
            'success': True,
            'nodes': nodes,
            'edges': edges,
            'counts': {
                'nodes': len(nodes),
                'edges': len(edges)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@toolkit_bp.route('/graph/entity/<entity_id>', methods=['GET'])
def get_entity_details(entity_id):
    """Get detailed information about a specific entity."""
    try:
        from db_utils import execute_query
        
        # Get entity details
        entity_query = """
            SELECT 
                se.*,
                (SELECT COUNT(*) FROM entity_relationships er 
                 WHERE er.source_entity_id = se.entity_id) as outgoing_relationships,
                (SELECT COUNT(*) FROM entity_relationships er 
                 WHERE er.target_entity_id = se.entity_id) as incoming_relationships
            FROM standards_entities se
            WHERE se.entity_id = %s
        """
        entity = execute_query(entity_query, (entity_id,))
        
        if not entity:
            return jsonify({
                'success': False,
                'error': 'Entity not found'
            }), 404
        
        # Get embeddings
        embeddings_query = """
            SELECT 
                ee.embedding_id,
                em.provider,
                em.model_name,
                ee.created_at
            FROM entity_embeddings ee
            JOIN embedding_models em ON ee.model_id = em.model_id
            WHERE ee.entity_id = %s
            ORDER BY ee.created_at DESC
        """
        embeddings = execute_query(embeddings_query, (entity_id,))
        
        # Get relationships
        relationships_query = """
            SELECT 
                er.relationship_type,
                er.relationship_category,
                er.confidence,
                se_target.entity_type as target_type,
                se_target.canonical_name as target_name,
                'outgoing' as direction
            FROM entity_relationships er
            JOIN standards_entities se_target ON er.target_entity_id = se_target.entity_id
            WHERE er.source_entity_id = %s
            
            UNION ALL
            
            SELECT 
                er.relationship_type,
                er.relationship_category,
                er.confidence,
                se_source.entity_type as source_type,
                se_source.canonical_name as source_name,
                'incoming' as direction
            FROM entity_relationships er
            JOIN standards_entities se_source ON er.source_entity_id = se_source.entity_id
            WHERE er.target_entity_id = %s
            
            ORDER BY relationship_category, relationship_type
        """
        relationships = execute_query(relationships_query, (entity_id, entity_id))
        
        return jsonify({
            'success': True,
            'entity': entity[0],
            'embeddings': embeddings,
            'relationships': relationships
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================
# QUALITY DASHBOARD
# ============================================

@toolkit_bp.route('/quality/metrics', methods=['GET'])
def get_quality_metrics():
    """Get quality and health metrics for dashboard."""
    try:
        from db_utils import execute_query
        
        # Embedding coverage
        coverage_query = """
            SELECT 
                COUNT(DISTINCT se.entity_id) as total_entities,
                COUNT(DISTINCT ee.entity_id) as entities_with_embeddings,
                ROUND(100.0 * COUNT(DISTINCT ee.entity_id) / NULLIF(COUNT(DISTINCT se.entity_id), 0), 2) as coverage_percent
            FROM standards_entities se
            LEFT JOIN entity_embeddings ee ON se.entity_id = ee.entity_id
        """
        coverage = execute_query(coverage_query)[0]
        
        # Relationship density
        density_query = """
            SELECT 
                COUNT(DISTINCT se.entity_id) as total_entities,
                COUNT(er.relationship_id) as total_relationships,
                ROUND(COUNT(er.relationship_id)::numeric / NULLIF(COUNT(DISTINCT se.entity_id), 0), 2) as avg_relationships_per_entity
            FROM standards_entities se
            LEFT JOIN entity_relationships er ON se.entity_id = er.source_entity_id OR se.entity_id = er.target_entity_id
        """
        density = execute_query(density_query)[0]
        
        # Quality score distribution
        quality_query = """
            SELECT 
                CASE 
                    WHEN quality_score >= 0.9 THEN 'excellent'
                    WHEN quality_score >= 0.7 THEN 'good'
                    WHEN quality_score >= 0.5 THEN 'fair'
                    ELSE 'poor'
                END as quality_tier,
                COUNT(*) as count
            FROM standards_entities
            GROUP BY quality_tier
            ORDER BY quality_tier
        """
        quality_dist = execute_query(quality_query)
        
        # Orphaned entities (no relationships)
        orphaned_query = """
            SELECT COUNT(*) as count
            FROM standards_entities se
            WHERE NOT EXISTS (
                SELECT 1 FROM entity_relationships er
                WHERE er.source_entity_id = se.entity_id 
                   OR er.target_entity_id = se.entity_id
            )
        """
        orphaned = execute_query(orphaned_query)[0]
        
        # Missing embeddings by entity type
        missing_embeddings_query = """
            SELECT 
                se.entity_type,
                COUNT(*) as count
            FROM standards_entities se
            WHERE NOT EXISTS (
                SELECT 1 FROM entity_embeddings ee
                WHERE ee.entity_id = se.entity_id
            )
            GROUP BY se.entity_type
            ORDER BY count DESC
            LIMIT 10
        """
        missing_embeddings = execute_query(missing_embeddings_query)
        
        # Relationship breakdown by category
        relationship_breakdown_query = """
            SELECT 
                relationship_category,
                COUNT(*) as count
            FROM entity_relationships
            GROUP BY relationship_category
            ORDER BY count DESC
        """
        relationship_breakdown = execute_query(relationship_breakdown_query)
        
        return jsonify({
            'success': True,
            'metrics': {
                'embedding_coverage': coverage,
                'relationship_density': density,
                'quality_distribution': quality_dist,
                'orphaned_entities': orphaned,
                'missing_embeddings_by_type': missing_embeddings,
                'relationship_breakdown': relationship_breakdown
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
