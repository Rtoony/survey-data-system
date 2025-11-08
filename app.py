"""
ACAD-GIS Schema Explorer & Data Manager
A companion tool for viewing and managing your Supabase database
"""

from flask import Flask, render_template, jsonify, request, send_file, make_response, redirect
from flask_cors import CORS
from flask_caching import Cache
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import csv
import io
import uuid
from dotenv import load_dotenv
from contextlib import contextmanager
from werkzeug.utils import secure_filename
from dxf_importer import DXFImporter
from dxf_exporter import DXFExporter
from map_export_service import MapExportService
import threading
import json
from datetime import datetime, date
from decimal import Decimal

# Load environment variables (works with both .env file and Replit secrets)
load_dotenv()

# Custom JSON encoder for datetime, date, and Decimal objects
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)

app = Flask(__name__)
app.json_encoder = CustomJSONEncoder
CORS(app)

# Configure caching
app.config['CACHE_TYPE'] = 'SimpleCache'  # In-memory cache
app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # 5 minutes default
cache = Cache(app)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('PGHOST') or os.getenv('DB_HOST'),
    'port': os.getenv('PGPORT') or os.getenv('DB_PORT', '5432'),
    'database': os.getenv('PGDATABASE') or os.getenv('DB_NAME', 'postgres'),
    'user': os.getenv('PGUSER') or os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('PGPASSWORD') or os.getenv('DB_PASSWORD'),
    'sslmode': 'require',
    'connect_timeout': 10
}

# Debug: Check if DB credentials are available
print("=" * 50)
print("Database Configuration Status:")
print(f"DB_HOST: {'SET' if DB_CONFIG['host'] else 'MISSING'}")
print(f"DB_USER: {'SET' if DB_CONFIG['user'] else 'MISSING'}")
print(f"DB_NAME: {'SET' if DB_CONFIG['database'] else 'MISSING'}")
print(f"DB_PASSWORD: {'SET' if DB_CONFIG['password'] else 'MISSING'}")
print("=" * 50)

@contextmanager
def get_db():
    """Get database connection with autocommit enabled"""
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    try:
        yield conn
    finally:
        conn.close()

def execute_query(query, params=None):
    """Execute query and return results"""
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params or ())
            try:
                return [dict(row) for row in cur.fetchall()]
            except:
                return []

# ============================================
# PAGES
# ============================================

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/schema')
def schema_page():
    """Schema viewer page"""
    return render_template('schema.html')

@app.route('/projects')
def projects_page():
    """Projects manager page"""
    return render_template('projects.html')

@app.route('/drawings')
def drawings_page():
    """Drawings manager page"""
    return render_template('drawings.html')

# ============================================
# DATA MANAGER PAGES
# ============================================

@app.route('/data-manager')
def data_manager_home():
    """Data Manager home page"""
    return render_template('data_manager/index.html')

@app.route('/data-manager/abbreviations')
def data_manager_abbreviations():
    """Abbreviations data manager page"""
    return render_template('data_manager/abbreviations.html')

@app.route('/data-manager/layers')
def data_manager_layers():
    """Layers data manager page"""
    return render_template('data_manager/layers.html')

@app.route('/data-manager/blocks')
def data_manager_blocks():
    """Blocks data manager page"""
    return render_template('data_manager/blocks.html')

@app.route('/data-manager/details')
def data_manager_details():
    """Details data manager page"""
    return render_template('data_manager/details.html')

# ============================================
# CAD STANDARDS PORTAL PAGES
# ============================================

@app.route('/standards')
def standards_home():
    """CAD Standards Portal home page"""
    return render_template('standards/index.html')

@app.route('/standards/layers')
def standards_layers():
    """Layer standards page"""
    return render_template('standards/layers.html')

@app.route('/standards/blocks')
def standards_blocks():
    """Block/symbol standards page"""
    return render_template('standards/blocks.html')

@app.route('/standards/colors')
def standards_colors():
    """Color standards page"""
    return render_template('standards/colors.html')

@app.route('/standards/linetypes')
def standards_linetypes():
    """Linetype standards page"""
    return render_template('standards/linetypes.html')

@app.route('/standards/text')
def standards_text():
    """Text style standards page"""
    return render_template('standards/text.html')

@app.route('/standards/hatches')
def standards_hatches():
    """Hatch pattern standards page"""
    return render_template('standards/hatches.html')

@app.route('/standards/details')
def standards_details():
    """Detail standards page"""
    return render_template('standards/details.html')

@app.route('/standards/abbreviations')
def standards_abbreviations():
    """Abbreviation standards page"""
    return render_template('standards/abbreviations.html')

@app.route('/standards/materials')
def standards_materials():
    """Material standards page"""
    return render_template('standards/materials.html')

@app.route('/standards/vocabulary')
def standards_vocabulary():
    """CAD Standards Vocabulary browser page"""
    return render_template('standards/vocabulary.html')

@app.route('/standards/reference')
def standards_reference():
    """CAD Standards Layer Reference - visual layer examples"""
    return render_template('standards/reference.html')

@app.route('/standards/sheets')
def standards_sheets():
    """Sheet template standards page"""
    return render_template('standards/sheets.html')

@app.route('/standards/plotstyles')
def standards_plotstyles():
    """Plot style standards page"""
    return render_template('standards/plotstyles.html')

@app.route('/standards/viewports')
def standards_viewports():
    """Viewport standards page"""
    return render_template('standards/viewports.html')

@app.route('/standards/annotations')
def standards_annotations():
    """Annotation standards page"""
    return render_template('standards/annotations.html')

@app.route('/standards/categories')
def standards_categories():
    """Symbol categories page"""
    return render_template('standards/categories.html')

@app.route('/standards/codes')
def standards_codes():
    """Code references page"""
    return render_template('standards/codes.html')

@app.route('/standards/notes')
def standards_notes():
    """Standard notes page"""
    return render_template('standards/notes.html')

@app.route('/standards/scales')
def standards_scales():
    """Drawing scale standards page"""
    return render_template('standards/scales.html')

# ============================================
# API ENDPOINTS
# ============================================

@app.route('/api/health')
def health():
    """Check database connection"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT version()')
                version = cur.fetchone()[0]
                return jsonify({
                    'status': 'connected',
                    'database': version
                })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/schema')
def get_schema():
    """Get database schema information"""
    try:
        query = """
            SELECT 
                table_name,
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
        """
        columns = execute_query(query)
        
        # Group by table
        schema = {}
        for col in columns:
            table = col['table_name']
            if table not in schema:
                schema[table] = []
            schema[table].append({
                'name': col['column_name'],
                'type': col['data_type'],
                'nullable': col['is_nullable'] == 'YES',
                'default': col['column_default']
            })
        
        # Get row counts
        counts = {}
        for table in schema.keys():
            try:
                result = execute_query(f'SELECT COUNT(*) as count FROM {table}')
                counts[table] = result[0]['count'] if result else 0
            except:
                counts[table] = 0
        
        return jsonify({
            'tables': schema,
            'counts': counts
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects')
def get_projects():
    """Get all projects"""
    try:
        query = """
            SELECT 
                p.*,
                COUNT(d.drawing_id) as drawing_count
            FROM projects p
            LEFT JOIN drawings d ON p.project_id = d.project_id
            GROUP BY p.project_id
            ORDER BY p.created_at DESC
        """
        projects = execute_query(query)
        return jsonify({'projects': projects})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects', methods=['POST'])
def create_project():
    """Create a new project"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400
            
        project_name = data.get('project_name')
        client_name = data.get('client_name')
        project_number = data.get('project_number')
        description = data.get('description')

        if not project_name:
            return jsonify({'error': 'project_name is required'}), 400

        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO projects (
                        project_name, client_name, project_number, description,
                        quality_score, tags, attributes
                    )
                    VALUES (%s, %s, %s, %s, 0.5, '{}', '{}')
                    RETURNING project_id, project_name, client_name, project_number, created_at
                    """,
                    (project_name, client_name, project_number, description)
                )
                result = cur.fetchone()
                conn.commit()
                
                return jsonify({
                    'project_id': str(result[0]),
                    'project_name': result[1],
                    'client_name': result[2],
                    'project_number': result[3],
                    'created_at': result[4].isoformat() if result[4] else None
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete a project"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                # Delete associated drawings first
                cur.execute('DELETE FROM drawings WHERE project_id = %s', (project_id,))
                # Delete project
                cur.execute('DELETE FROM projects WHERE project_id = %s', (project_id,))
                conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>', methods=['PUT'])
def update_project(project_id):
    """Update an existing project"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400
            
        project_name = data.get('project_name')
        client_name = data.get('client_name')
        project_number = data.get('project_number')
        description = data.get('description')

        if not project_name:
            return jsonify({'error': 'project_name is required'}), 400

        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE projects 
                    SET project_name = %s, 
                        client_name = %s, 
                        project_number = %s, 
                        description = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE project_id = %s
                    RETURNING project_id, project_name, client_name, project_number, updated_at
                    """,
                    (project_name, client_name, project_number, description, project_id)
                )
                result = cur.fetchone()
                if not result:
                    return jsonify({'error': 'Project not found'}), 404
                conn.commit()
                
                return jsonify({
                    'project_id': str(result[0]),
                    'project_name': result[1],
                    'client_name': result[2],
                    'project_number': result[3],
                    'updated_at': result[4].isoformat() if result[4] else None
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/drawings')
def get_drawings():
    """Get all drawings"""
    try:
        query = """
            SELECT 
                d.*,
                p.project_name,
                p.project_number,
                COALESCE(COUNT(de.entity_id), 0) as entity_count,
                CASE 
                    WHEN COUNT(de.entity_id) > 0 THEN true 
                    ELSE false 
                END as has_content
            FROM drawings d
            LEFT JOIN projects p ON d.project_id = p.project_id
            LEFT JOIN drawing_entities de ON d.drawing_id = de.drawing_id
            GROUP BY d.drawing_id, p.project_name, p.project_number
            ORDER BY d.created_at DESC
            LIMIT 500
        """
        drawings = execute_query(query)
        return jsonify({'drawings': drawings})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/drawings', methods=['POST'])
def create_drawing():
    """Create a new drawing"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400
            
        drawing_name = data.get('drawing_name')
        drawing_number = data.get('drawing_number')
        project_id = data.get('project_id')
        drawing_type = data.get('drawing_type')
        scale = data.get('scale')
        discipline = data.get('discipline')

        if not drawing_name:
            return jsonify({'error': 'drawing_name is required'}), 400
        
        if not project_id:
            return jsonify({'error': 'project_id is required'}), 400

        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO drawings (
                        drawing_name, drawing_number, project_id, drawing_type, 
                        scale, discipline, quality_score, tags, attributes
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, 0.5, '{}', '{}')
                    RETURNING drawing_id, drawing_name, drawing_number, project_id, created_at
                    """,
                    (drawing_name, drawing_number, project_id, drawing_type, scale, discipline)
                )
                result = cur.fetchone()
                conn.commit()
                
                return jsonify({
                    'drawing_id': str(result[0]),
                    'drawing_name': result[1],
                    'drawing_number': result[2],
                    'project_id': str(result[3]),
                    'created_at': result[4].isoformat() if result[4] else None
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/drawings/<drawing_id>', methods=['DELETE'])
def delete_drawing(drawing_id):
    """Delete a drawing"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM drawings WHERE drawing_id = %s', (drawing_id,))
                conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/drawings/<drawing_id>', methods=['PUT'])
def update_drawing(drawing_id):
    """Update an existing drawing"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400
            
        drawing_name = data.get('drawing_name')
        drawing_number = data.get('drawing_number')
        project_id = data.get('project_id') or None
        drawing_type = data.get('drawing_type')
        scale = data.get('scale')
        discipline = data.get('discipline')
        sheet_title = data.get('sheet_title')

        if not drawing_name:
            return jsonify({'error': 'drawing_name is required'}), 400

        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE drawings 
                    SET drawing_name = %s, 
                        drawing_number = %s, 
                        project_id = %s, 
                        drawing_type = %s, 
                        scale = %s, 
                        discipline = %s,
                        sheet_title = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE drawing_id = %s
                    RETURNING drawing_id, drawing_name, drawing_number, project_id, updated_at
                    """,
                    (drawing_name, drawing_number, project_id, drawing_type, scale, discipline, sheet_title, drawing_id)
                )
                result = cur.fetchone()
                if not result:
                    return jsonify({'error': 'Drawing not found'}), 404
                conn.commit()
                
                return jsonify({
                    'drawing_id': str(result[0]),
                    'drawing_name': result[1],
                    'drawing_number': result[2],
                    'project_id': str(result[3]) if result[3] else None,
                    'updated_at': result[4].isoformat() if result[4] else None
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recent-activity')
@cache.cached(timeout=60)  # Cache for 1 minute
def get_recent_activity():
    """Get recent projects and drawings for dashboard"""
    try:
        # Get 5 most recent projects
        projects_query = """
            SELECT 
                p.project_id,
                p.project_name,
                p.project_number,
                p.client_name,
                p.created_at,
                COUNT(d.drawing_id) as drawing_count
            FROM projects p
            LEFT JOIN drawings d ON p.project_id = d.project_id
            GROUP BY p.project_id, p.project_name, p.project_number, p.client_name, p.created_at
            ORDER BY p.created_at DESC
            LIMIT 5
        """
        recent_projects = execute_query(projects_query)
        
        # Get 5 most recent drawings
        drawings_query = """
            SELECT 
                d.drawing_id,
                d.drawing_name,
                d.drawing_number,
                d.drawing_type,
                d.created_at,
                p.project_name,
                p.project_number
            FROM drawings d
            LEFT JOIN projects p ON d.project_id = p.project_id
            ORDER BY d.created_at DESC
            LIMIT 5
        """
        recent_drawings = execute_query(drawings_query)
        
        # Get database stats
        stats_query = """
            SELECT 
                (SELECT COUNT(*) FROM projects) as total_projects,
                (SELECT COUNT(*) FROM drawings) as total_drawings,
                (SELECT COUNT(*) FROM layer_standards) as total_layers,
                (SELECT COUNT(*) FROM block_definitions) as total_blocks
        """
        stats = execute_query(stats_query)
        
        return jsonify({
            'recent_projects': recent_projects,
            'recent_drawings': recent_drawings,
            'stats': stats[0] if stats else {}
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# CAD STANDARDS API ENDPOINTS
# ============================================

@app.route('/api/standards/overview')
@cache.cached(timeout=600)  # Cache for 10 minutes
def standards_overview():
    """Get overview of all standards"""
    try:
        overview = {}
        tables = {
            'layers': 'layer_standards',
            'blocks': 'block_definitions',
            'colors': 'color_standards',
            'linetypes': 'linetypes',
            'text_styles': 'text_styles',
            'hatches': 'hatch_patterns',
            'details': 'detail_standards',
            'dimensions': 'dimension_styles',
            'abbreviations': 'abbreviation_standards',
            'materials': 'material_standards',
            'sheets': 'sheet_templates',
            'plotstyles': 'plot_style_standards',
            'viewports': 'viewport_standards',
            'annotations': 'annotation_standards',
            'categories': 'symbol_categories',
            'codes': 'code_references',
            'notes': 'standard_notes',
            'scales': 'drawing_scale_standards'
        }
        
        for key, table in tables.items():
            try:
                result = execute_query(f'SELECT COUNT(*) as count FROM {table}')
                overview[key] = result[0]['count'] if result else 0
            except:
                overview[key] = 0
        
        return jsonify(overview)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/standards/layers')
@cache.cached(timeout=600)  # Cache for 10 minutes
def get_layer_standards():
    """Get all layer standards"""
    try:
        query = """
            SELECT 
                layer_standard_id,
                layer_name,
                discipline,
                category,
                type,
                status,
                color,
                color_rgb,
                linetype,
                lineweight,
                is_plottable,
                is_locked,
                plot_style,
                transparency,
                description,
                usage_context,
                display_order,
                tags,
                standard_reference
            FROM layer_standards
            ORDER BY discipline, category, layer_name
        """
        layers = execute_query(query)
        return jsonify(layers)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/standards/blocks')
@cache.cached(timeout=600)  # Cache for 10 minutes
def get_block_standards():
    """Get all block/symbol standards"""
    try:
        query = """
            SELECT 
                block_id,
                block_name,
                block_type,
                category,
                domain,
                description,
                space_type,
                svg_content,
                svg_viewbox,
                semantic_type,
                semantic_label,
                usage_context,
                tags,
                is_title_block,
                is_detail,
                title_block_size,
                detail_category
            FROM block_definitions
            ORDER BY category, block_name
        """
        blocks = execute_query(query)
        return jsonify(blocks)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/standards/colors')
@cache.cached(timeout=600)  # Cache for 10 minutes
def get_color_standards():
    """Get all color standards"""
    try:
        query = """
            SELECT 
                color_id,
                color_index,
                color_name,
                color_rgb,
                hex_code,
                usage_category,
                description
            FROM color_standards
            ORDER BY color_index
        """
        colors = execute_query(query)
        return jsonify(colors)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/standards/linetypes')
@cache.cached(timeout=600)  # Cache for 10 minutes
def get_linetype_standards():
    """Get all linetype standards"""
    try:
        query = """
            SELECT 
                linetype_id,
                linetype_name,
                description,
                pattern_definition,
                usage_context
            FROM linetypes
            WHERE is_active = true
            ORDER BY linetype_name
        """
        linetypes = execute_query(query)
        return jsonify(linetypes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/standards/text')
@cache.cached(timeout=600)  # Cache for 10 minutes
def get_text_standards():
    """Get all text style standards"""
    try:
        query = """
            SELECT 
                style_id,
                style_name,
                font_name,
                font_file,
                height,
                width_factor,
                oblique_angle,
                is_backward,
                is_upside_down,
                is_vertical,
                usage_context
            FROM text_styles
            ORDER BY style_name
        """
        text_styles = execute_query(query)
        return jsonify(text_styles)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/standards/hatches')
@cache.cached(timeout=600)  # Cache for 10 minutes
def get_hatch_standards():
    """Get all hatch pattern standards"""
    try:
        query = """
            SELECT 
                hatch_id,
                pattern_name,
                pattern_type,
                angle,
                scale,
                pattern_definition,
                material_type,
                description,
                usage_context,
                svg_preview
            FROM hatch_patterns
            ORDER BY pattern_name
        """
        hatches = execute_query(query)
        return jsonify(hatches)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/standards/details')
@cache.cached(timeout=600)  # Cache for 10 minutes
def get_detail_standards():
    """Get all detail standards"""
    try:
        query = """
            SELECT 
                ds.detail_id,
                ds.detail_number,
                ds.detail_title,
                ds.detail_category,
                ds.applicable_layers,
                ds.applicable_symbols,
                ds.scale,
                ds.description,
                ds.usage_context,
                ds.typical_application,
                ds.code_references,
                bd.block_name,
                bd.svg_content
            FROM detail_standards ds
            LEFT JOIN block_definitions bd ON ds.block_id = bd.block_id
            ORDER BY ds.detail_category, ds.detail_number
        """
        details = execute_query(query)
        return jsonify(details)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/standards/abbreviations')
@cache.cached(timeout=600)  # Cache for 10 minutes
def get_abbreviation_standards():
    """Get all abbreviation standards"""
    try:
        query = """
            SELECT * FROM abbreviation_standards
            ORDER BY discipline, abbreviation
        """
        abbreviations = execute_query(query)
        return jsonify(abbreviations)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/standards/materials')
@cache.cached(timeout=600)  # Cache for 10 minutes
def get_material_standards():
    """Get all material standards"""
    try:
        query = """
            SELECT * FROM material_standards
            ORDER BY category, material_name
        """
        materials = execute_query(query)
        return jsonify(materials)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/standards/sheets')
@cache.cached(timeout=600)  # Cache for 10 minutes
def get_sheet_templates():
    """Get all sheet template standards"""
    try:
        query = """
            SELECT * FROM sheet_templates
            ORDER BY discipline, sheet_size, template_name
        """
        sheets = execute_query(query)
        return jsonify(sheets)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/standards/plotstyles')
@cache.cached(timeout=600)  # Cache for 10 minutes
def get_plotstyle_standards():
    """Get all plot style standards"""
    try:
        query = """
            SELECT * FROM plot_style_standards
            ORDER BY style_name
        """
        plotstyles = execute_query(query)
        return jsonify(plotstyles)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/standards/viewports')
@cache.cached(timeout=600)  # Cache for 10 minutes
def get_viewport_standards():
    """Get all viewport standards"""
    try:
        query = """
            SELECT * FROM viewport_standards
            ORDER BY discipline, scale_factor
        """
        viewports = execute_query(query)
        return jsonify(viewports)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/standards/annotations')
@cache.cached(timeout=600)  # Cache for 10 minutes
def get_annotation_standards():
    """Get all annotation standards"""
    try:
        query = """
            SELECT * FROM annotation_standards
            ORDER BY discipline, annotation_type, annotation_name
        """
        annotations = execute_query(query)
        return jsonify(annotations)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/standards/categories')
@cache.cached(timeout=600)  # Cache for 10 minutes
def get_symbol_categories():
    """Get all symbol categories"""
    try:
        query = """
            SELECT * FROM symbol_categories
            ORDER BY sort_order, category_name
        """
        categories = execute_query(query)
        return jsonify(categories)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/standards/codes')
@cache.cached(timeout=600)  # Cache for 10 minutes
def get_code_references():
    """Get all code references"""
    try:
        query = """
            SELECT * FROM code_references
            ORDER BY code_type, code_name
        """
        codes = execute_query(query)
        return jsonify(codes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/standards/notes')
@cache.cached(timeout=600)  # Cache for 10 minutes
def get_standard_notes():
    """Get all standard notes"""
    try:
        query = """
            SELECT * FROM standard_notes
            ORDER BY discipline, note_category, sort_order
        """
        notes = execute_query(query)
        return jsonify(notes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/standards/scales')
@cache.cached(timeout=600)  # Cache for 10 minutes
def get_drawing_scales():
    """Get all drawing scale standards"""
    try:
        query = """
            SELECT * FROM drawing_scale_standards
            ORDER BY scale_type, scale_factor
        """
        scales = execute_query(query)
        return jsonify(scales)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# DATA MANAGER API ENDPOINTS
# ============================================

# ABBREVIATIONS CRUD

@app.route('/api/data-manager/abbreviations', methods=['POST'])
def create_abbreviation():
    """Create a new abbreviation"""
    try:
        data = request.json
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO abbreviation_standards (category, discipline, abbreviation, full_text, context_usage_notes)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING abbreviation_id
                """, (data.get('discipline'), 'civil', data.get('abbreviation'), 
                      data.get('full_text'), data.get('description')))
                abbreviation_id = cur.fetchone()[0]
                conn.commit()
        
        cache.clear()
        return jsonify({'success': True, 'abbreviation_id': abbreviation_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/abbreviations/<int:abbreviation_id>', methods=['PUT'])
def update_abbreviation(abbreviation_id):
    """Update an existing abbreviation"""
    try:
        data = request.json
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE abbreviation_standards
                    SET category = %s, abbreviation = %s, full_text = %s, context_usage_notes = %s
                    WHERE abbreviation_id = %s
                """, (data.get('discipline'), data.get('abbreviation'), data.get('full_text'), 
                      data.get('description'), abbreviation_id))
                conn.commit()
        
        cache.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/abbreviations/<int:abbreviation_id>', methods=['DELETE'])
def delete_abbreviation(abbreviation_id):
    """Delete an abbreviation"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM abbreviation_standards WHERE abbreviation_id = %s", (abbreviation_id,))
                conn.commit()
        
        cache.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/abbreviations/import-csv', methods=['POST'])
def import_abbreviations_csv():
    """Import abbreviations from CSV file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Read CSV file
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        imported_count = 0
        updated_count = 0
        
        with get_db() as conn:
            with conn.cursor() as cur:
                for row in csv_reader:
                    # Map CSV columns to database columns
                    # CSV: Category, Full_Term, Abbreviation, Context_Usage_Notes
                    # DB: category, discipline, abbreviation, full_text, context_usage_notes
                    
                    category = row.get('Category', '').strip()
                    abbreviation_text = row.get('Abbreviation', '').strip()
                    full_text = row.get('Full_Term', '').strip()
                    context_notes = row.get('Context_Usage_Notes', '').strip()
                    
                    if not abbreviation_text:
                        continue
                    
                    # Check if abbreviation already exists
                    cur.execute("""
                        SELECT abbreviation_id FROM abbreviation_standards 
                        WHERE LOWER(abbreviation) = LOWER(%s) AND LOWER(category) = LOWER(%s)
                    """, (abbreviation_text, category))
                    
                    existing = cur.fetchone()
                    
                    if existing:
                        # Update existing record
                        cur.execute("""
                            UPDATE abbreviation_standards
                            SET full_text = %s, context_usage_notes = %s
                            WHERE abbreviation_id = %s
                        """, (full_text, context_notes, existing[0]))
                        updated_count += 1
                    else:
                        # Insert new record (discipline defaults to 'civil')
                        cur.execute("""
                            INSERT INTO abbreviation_standards (category, discipline, abbreviation, full_text, context_usage_notes)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (category, 'civil', abbreviation_text, full_text, context_notes))
                        imported_count += 1
                
                conn.commit()
        
        cache.clear()
        return jsonify({
            'success': True, 
            'imported': imported_count, 
            'updated': updated_count,
            'total': imported_count + updated_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/abbreviations/export-csv', methods=['GET'])
def export_abbreviations_csv():
    """Export abbreviations to CSV file"""
    try:
        query = """
            SELECT category, abbreviation, full_text, context_usage_notes
            FROM abbreviation_standards
            ORDER BY category, abbreviation
        """
        data = execute_query(query)
        
        # Create CSV in memory
        output = io.StringIO()
        if data:
            fieldnames = ['Category', 'Abbreviation', 'Full_Term', 'Context_Usage_Notes']
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in data:
                writer.writerow({
                    'Category': row.get('category', ''),
                    'Abbreviation': row.get('abbreviation', ''),
                    'Full_Term': row.get('full_text', ''),
                    'Context_Usage_Notes': row.get('context_usage_notes', '')
                })
        
        # Convert to bytes
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name='abbreviations.csv'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# LAYERS MANAGER ROUTES
# ============================================================================

@app.route('/data-manager/layers')
def layers_manager():
    """Render the Layers Manager page"""
    return render_template('data_manager/layers.html')

@app.route('/api/data-manager/layers', methods=['GET'])
def get_layers():
    """Get all layers"""
    try:
        query = """
            SELECT layer_standard_id, category, discipline, layer_name, color_rgb, 
                   description, linetype, lineweight, plot_style
            FROM layer_standards
            ORDER BY category, layer_name
        """
        layers = execute_query(query)
        return jsonify({'layers': layers})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/layers', methods=['POST'])
def create_layer():
    """Create a new layer"""
    try:
        data = request.get_json()
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO layer_standards 
                    (category, discipline, layer_name, color_rgb, description)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING layer_standard_id
                """, (
                    data.get('category'),
                    data.get('discipline', 'CIVIL'),
                    data.get('layer_name'),
                    data.get('color_rgb'),
                    data.get('description')
                ))
                layer_id = cur.fetchone()[0]
                conn.commit()
        
        cache.clear()
        return jsonify({'layer_standard_id': layer_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/layers/<layer_id>', methods=['PUT'])
def update_layer(layer_id):
    """Update an existing layer"""
    try:
        data = request.get_json()
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE layer_standards
                    SET category = %s, layer_name = %s, color_rgb = %s, description = %s
                    WHERE layer_standard_id = %s
                """, (
                    data.get('category'),
                    data.get('layer_name'),
                    data.get('color_rgb'),
                    data.get('description'),
                    layer_id
                ))
                conn.commit()
        
        cache.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/layers/<layer_id>', methods=['DELETE'])
def delete_layer(layer_id):
    """Delete a layer"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM layer_standards WHERE layer_standard_id = %s", (layer_id,))
                conn.commit()
        
        cache.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/layers/import-csv', methods=['POST'])
def import_layers_csv():
    """Import layers from CSV file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Read CSV file
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        imported_count = 0
        updated_count = 0
        
        with get_db() as conn:
            with conn.cursor() as cur:
                for row in csv_reader:
                    # Map CSV columns to database columns
                    # CSV: Category, Layer_Name, Color_RGB, Color_Name, Description
                    # DB: category, discipline, layer_name, color_rgb, color_name, description
                    
                    category = row.get('Category', '').strip()
                    layer_name = row.get('Layer_Name', '').strip()
                    color_rgb = row.get('Color_RGB', '').strip()
                    color_name = row.get('Color_Name', '').strip()
                    description = row.get('Description', '').strip()
                    
                    if not layer_name:
                        continue
                    
                    # Check if layer already exists
                    cur.execute("""
                        SELECT layer_standard_id FROM layer_standards 
                        WHERE LOWER(layer_name) = LOWER(%s)
                    """, (layer_name,))
                    
                    existing = cur.fetchone()
                    
                    if existing:
                        # Update existing record
                        cur.execute("""
                            UPDATE layer_standards
                            SET category = %s, color_rgb = %s, description = %s
                            WHERE layer_standard_id = %s
                        """, (category, color_rgb, description, existing[0]))
                        updated_count += 1
                    else:
                        # Insert new record (discipline defaults to 'CIVIL')
                        cur.execute("""
                            INSERT INTO layer_standards (category, discipline, layer_name, color_rgb, description)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (category, 'CIVIL', layer_name, color_rgb, description))
                        imported_count += 1
                
                conn.commit()
        
        cache.clear()
        return jsonify({
            'imported': imported_count,
            'updated': updated_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/layers/export-csv', methods=['GET'])
def export_layers_csv():
    """Export layers to CSV file"""
    try:
        query = """
            SELECT category, layer_name, color_rgb, description
            FROM layer_standards
            ORDER BY category, layer_name
        """
        data = execute_query(query)
        
        # Create CSV in memory
        output = io.StringIO()
        if data:
            fieldnames = ['Category', 'Layer_Name', 'Color_RGB', 'Description']
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in data:
                writer.writerow({
                    'Category': row.get('category', ''),
                    'Layer_Name': row.get('layer_name', ''),
                    'Color_RGB': row.get('color_rgb', ''),
                    'Description': row.get('description', '')
                })
        
        # Convert to bytes
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name='layers.csv'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# BLOCKS MANAGER ROUTES
# ============================================================================

@app.route('/data-manager/blocks')
def blocks_manager():
    """Render the Blocks Manager page"""
    return render_template('data_manager/blocks.html')

@app.route('/api/data-manager/blocks', methods=['GET'])
def get_blocks():
    """Get all blocks"""
    try:
        query = """
            SELECT block_id, block_name, block_type, category, domain, 
                   description, svg_content, svg_viewbox
            FROM block_definitions
            ORDER BY category, block_name
        """
        blocks = execute_query(query)
        return jsonify({'blocks': blocks})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/blocks', methods=['POST'])
def create_block():
    """Create a new block"""
    try:
        data = request.get_json()
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO block_definitions 
                    (block_name, category, domain, description)
                    VALUES (%s, %s, %s, %s)
                    RETURNING block_id
                """, (
                    data.get('block_name'),
                    data.get('category'),
                    data.get('domain'),
                    data.get('description')
                ))
                block_id = cur.fetchone()[0]
                conn.commit()
        
        cache.clear()
        return jsonify({'block_id': block_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/blocks/<block_id>', methods=['PUT'])
def update_block(block_id):
    """Update an existing block"""
    try:
        data = request.get_json()
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE block_definitions
                    SET block_name = %s, category = %s, domain = %s, description = %s
                    WHERE block_id = %s
                """, (
                    data.get('block_name'),
                    data.get('category'),
                    data.get('domain'),
                    data.get('description'),
                    block_id
                ))
                conn.commit()
        
        cache.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/blocks/<block_id>', methods=['DELETE'])
def delete_block(block_id):
    """Delete a block"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM block_definitions WHERE block_id = %s", (block_id,))
                conn.commit()
        
        cache.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/blocks/import-csv', methods=['POST'])
def import_blocks_csv():
    """Import blocks from CSV file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Read CSV file
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        imported_count = 0
        updated_count = 0
        
        with get_db() as conn:
            with conn.cursor() as cur:
                for row in csv_reader:
                    # Map CSV columns to database columns
                    # CSV: Block_Name, Type_Prefix, Discipline, Element, Size_Variant, Category, Description
                    # DB: block_name, category, domain, description
                    
                    block_name = row.get('Block_Name', '').strip()
                    category = row.get('Category', '').strip()
                    discipline = row.get('Discipline', '').strip()
                    description = row.get('Description', '').strip()
                    
                    if not block_name:
                        continue
                    
                    # Check if block already exists
                    cur.execute("""
                        SELECT block_id FROM block_definitions 
                        WHERE LOWER(block_name) = LOWER(%s)
                    """, (block_name,))
                    
                    existing = cur.fetchone()
                    
                    if existing:
                        # Update existing record
                        cur.execute("""
                            UPDATE block_definitions
                            SET category = %s, domain = %s, description = %s
                            WHERE block_id = %s
                        """, (category, discipline, description, existing[0]))
                        updated_count += 1
                    else:
                        # Insert new record
                        cur.execute("""
                            INSERT INTO block_definitions (block_name, category, domain, description)
                            VALUES (%s, %s, %s, %s)
                        """, (block_name, category, discipline, description))
                        imported_count += 1
                
                conn.commit()
        
        cache.clear()
        return jsonify({
            'imported': imported_count,
            'updated': updated_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/blocks/export-csv', methods=['GET'])
def export_blocks_csv():
    """Export blocks to CSV file"""
    try:
        query = """
            SELECT block_name, category, domain, description
            FROM block_definitions
            ORDER BY category, block_name
        """
        data = execute_query(query)
        
        # Create CSV in memory
        output = io.StringIO()
        if data:
            fieldnames = ['Block_Name', 'Category', 'Domain', 'Description']
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in data:
                writer.writerow({
                    'Block_Name': row.get('block_name', ''),
                    'Category': row.get('category', ''),
                    'Domain': row.get('domain', ''),
                    'Description': row.get('description', '')
                })
        
        # Convert to bytes
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name='blocks.csv'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# DETAILS MANAGER ROUTES
# ============================================================================

@app.route('/data-manager/details')
def details_manager():
    """Render the Details Manager page"""
    return render_template('data_manager/details.html')

@app.route('/api/data-manager/details', methods=['GET'])
def get_details():
    """Get all details"""
    try:
        query = """
            SELECT detail_id, detail_number, detail_title, detail_category, 
                   scale, description, usage_context, typical_application
            FROM detail_standards
            ORDER BY detail_category, detail_number
        """
        details = execute_query(query)
        return jsonify({'details': details})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/details', methods=['POST'])
def create_detail():
    """Create a new detail"""
    try:
        data = request.get_json()
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO detail_standards 
                    (detail_number, detail_title, detail_category, scale, description)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING detail_id
                """, (
                    data.get('detail_number'),
                    data.get('detail_title'),
                    data.get('detail_category'),
                    data.get('scale'),
                    data.get('description')
                ))
                detail_id = cur.fetchone()[0]
                conn.commit()
        
        cache.clear()
        return jsonify({'detail_id': detail_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/details/<detail_id>', methods=['PUT'])
def update_detail(detail_id):
    """Update an existing detail"""
    try:
        data = request.get_json()
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE detail_standards
                    SET detail_number = %s, detail_title = %s, detail_category = %s, 
                        scale = %s, description = %s
                    WHERE detail_id = %s
                """, (
                    data.get('detail_number'),
                    data.get('detail_title'),
                    data.get('detail_category'),
                    data.get('scale'),
                    data.get('description'),
                    detail_id
                ))
                conn.commit()
        
        cache.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/details/<detail_id>', methods=['DELETE'])
def delete_detail(detail_id):
    """Delete a detail"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM detail_standards WHERE detail_id = %s", (detail_id,))
                conn.commit()
        
        cache.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/details/import-csv', methods=['POST'])
def import_details_csv():
    """Import details from CSV file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Read CSV file
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        imported_count = 0
        updated_count = 0
        
        with get_db() as conn:
            with conn.cursor() as cur:
                for row in csv_reader:
                    # Map CSV columns to database columns
                    # CSV: Detail_Number, Detail_Title, Category, Scale, Description
                    # DB: detail_number, detail_title, detail_category, scale, description
                    
                    detail_number = row.get('Detail_Number', '').strip()
                    detail_title = row.get('Detail_Title', '').strip()
                    category = row.get('Category', '').strip()
                    scale = row.get('Scale', '').strip()
                    description = row.get('Description', '').strip()
                    
                    if not detail_number:
                        continue
                    
                    # Check if detail already exists
                    cur.execute("""
                        SELECT detail_id FROM detail_standards 
                        WHERE LOWER(detail_number) = LOWER(%s)
                    """, (detail_number,))
                    
                    existing = cur.fetchone()
                    
                    if existing:
                        # Update existing record
                        cur.execute("""
                            UPDATE detail_standards
                            SET detail_title = %s, detail_category = %s, scale = %s, description = %s
                            WHERE detail_id = %s
                        """, (detail_title, category, scale, description, existing[0]))
                        updated_count += 1
                    else:
                        # Insert new record
                        cur.execute("""
                            INSERT INTO detail_standards (detail_number, detail_title, detail_category, scale, description)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (detail_number, detail_title, category, scale, description))
                        imported_count += 1
                
                conn.commit()
        
        cache.clear()
        return jsonify({
            'imported': imported_count,
            'updated': updated_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/details/export-csv', methods=['GET'])
def export_details_csv():
    """Export details to CSV file"""
    try:
        query = """
            SELECT detail_number, detail_title, detail_category, scale, description
            FROM detail_standards
            ORDER BY detail_category, detail_number
        """
        data = execute_query(query)
        
        # Create CSV in memory
        output = io.StringIO()
        if data:
            fieldnames = ['Detail_Number', 'Detail_Title', 'Category', 'Scale', 'Description']
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in data:
                writer.writerow({
                    'Detail_Number': row.get('detail_number', ''),
                    'Detail_Title': row.get('detail_title', ''),
                    'Category': row.get('detail_category', ''),
                    'Scale': row.get('scale', ''),
                    'Description': row.get('description', '')
                })
        
        # Convert to bytes
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name='details.csv'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# PIPE NETWORK EDITOR API ENDPOINTS
# ============================================================================

@app.route('/api/pipe-networks')
def get_pipe_networks():
    """Get list of all pipe networks, optionally filtered by project or mode"""
    try:
        project_id = request.args.get('project_id')
        network_mode = request.args.get('mode')
        
        query = """
            SELECT 
                pn.network_id,
                pn.project_id,
                pn.network_name,
                pn.utility_system,
                pn.network_mode,
                pn.network_status,
                pn.description,
                p.project_name,
                COUNT(DISTINCT unm_lines.line_id) as line_count,
                COUNT(DISTINCT unm_struct.structure_id) as structure_count
            FROM pipe_networks pn
            LEFT JOIN projects p ON pn.project_id = p.project_id
            LEFT JOIN utility_network_memberships unm_lines ON pn.network_id = unm_lines.network_id AND unm_lines.line_id IS NOT NULL
            LEFT JOIN utility_network_memberships unm_struct ON pn.network_id = unm_struct.network_id AND unm_struct.structure_id IS NOT NULL
            WHERE 1=1
        """
        params = []
        
        if project_id:
            query += " AND pn.project_id = %s"
            params.append(project_id)
        
        if network_mode:
            query += " AND pn.network_mode = %s"
            params.append(network_mode)
        
        query += """
            GROUP BY pn.network_id, pn.project_id, pn.network_name, pn.utility_system, 
                     pn.network_mode, pn.network_status, pn.description, p.project_name
            ORDER BY pn.created_at DESC
        """
        
        networks = execute_query(query, tuple(params) if params else None)
        return jsonify({'networks': networks})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pipe-networks/<network_id>')
def get_network_details(network_id):
    """Get detailed information about a specific pipe network"""
    try:
        query = """
            SELECT 
                pn.network_id,
                pn.project_id,
                pn.network_name,
                pn.utility_system,
                pn.network_mode,
                pn.network_status,
                pn.description,
                pn.attributes,
                p.project_name,
                p.client_name
            FROM pipe_networks pn
            LEFT JOIN projects p ON pn.project_id = p.project_id
            WHERE pn.network_id = %s
        """
        network = execute_query(query, (network_id,))
        
        if not network or len(network) == 0:
            return jsonify({'error': 'Network not found'}), 404
        
        return jsonify({'network': network[0]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pipe-networks/<network_id>/pipes')
def get_network_pipes(network_id):
    """Get all pipes in a network with from/to structure information"""
    try:
        query = """
            SELECT 
                ul.line_id,
                ul.line_number,
                ul.utility_system,
                ul.material,
                ul.diameter_mm,
                ul.invert_elevation_start,
                ul.invert_elevation_end,
                ul.slope,
                ul.length,
                ul.from_structure_id,
                ul.to_structure_id,
                from_struct.structure_number as from_structure_number,
                from_struct.structure_type as from_structure_type,
                to_struct.structure_number as to_structure_number,
                to_struct.structure_type as to_structure_type,
                ST_AsGeoJSON(ul.geometry) as geometry,
                ul.attributes
            FROM utility_network_memberships unm
            JOIN utility_lines ul ON unm.line_id = ul.line_id
            LEFT JOIN utility_structures from_struct ON ul.from_structure_id = from_struct.structure_id
            LEFT JOIN utility_structures to_struct ON ul.to_structure_id = to_struct.structure_id
            WHERE unm.network_id = %s
            ORDER BY ul.line_number, ul.created_at
        """
        pipes = execute_query(query, (network_id,))
        return jsonify({'pipes': pipes})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pipe-networks/<network_id>/structures')
def get_network_structures(network_id):
    """Get all structures in a network"""
    try:
        query = """
            SELECT 
                us.structure_id,
                us.structure_number,
                us.structure_type,
                us.utility_system,
                us.rim_elevation,
                us.invert_elevation,
                us.size_mm,
                us.material,
                us.manhole_depth_ft,
                us.condition,
                ST_AsGeoJSON(us.rim_geometry) as geometry,
                us.attributes
            FROM utility_network_memberships unm
            JOIN utility_structures us ON unm.structure_id = us.structure_id
            WHERE unm.network_id = %s
            ORDER BY us.structure_number, us.created_at
        """
        structures = execute_query(query, (network_id,))
        return jsonify({'structures': structures})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pipe-networks/<network_id>/pipes/<pipe_id>', methods=['PUT'])
def update_network_pipe(network_id, pipe_id):
    """Update pipe attributes (preserves geometry)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400
        
        allowed_fields = [
            'line_number', 'material', 'diameter_mm', 
            'invert_elevation_start', 'invert_elevation_end', 
            'slope', 'from_structure_id', 'to_structure_id', 'notes'
        ]
        
        updates = []
        params = []
        for field in allowed_fields:
            if field in data:
                updates.append(f"{field} = %s")
                params.append(data[field])
        
        if not updates:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        params.append(pipe_id)
        
        with get_db() as conn:
            with conn.cursor() as cur:
                query = f"""
                    UPDATE utility_lines 
                    SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
                    WHERE line_id = %s
                    RETURNING line_id
                """
                cur.execute(query, tuple(params))
                result = cur.fetchone()
                conn.commit()
                
                if not result:
                    return jsonify({'error': 'Pipe not found'}), 404
                
                return jsonify({'success': True, 'line_id': str(result[0])})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pipe-networks/<network_id>/structures/<structure_id>', methods=['PUT'])
def update_network_structure(network_id, structure_id):
    """Update structure attributes (preserves geometry)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400
        
        allowed_fields = [
            'structure_number', 'structure_type', 'rim_elevation', 
            'invert_elevation', 'size_mm', 'material', 
            'manhole_depth_ft', 'condition', 'notes'
        ]
        
        updates = []
        params = []
        for field in allowed_fields:
            if field in data:
                updates.append(f"{field} = %s")
                params.append(data[field])
        
        if not updates:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        params.append(structure_id)
        
        with get_db() as conn:
            with conn.cursor() as cur:
                query = f"""
                    UPDATE utility_structures 
                    SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
                    WHERE structure_id = %s
                    RETURNING structure_id
                """
                cur.execute(query, tuple(params))
                result = cur.fetchone()
                conn.commit()
                
                if not result:
                    return jsonify({'error': 'Structure not found'}), 404
                
                return jsonify({'success': True, 'structure_id': str(result[0])})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pipe-networks/<network_id>/auto-connect', methods=['POST'])
def auto_connect_pipes(network_id):
    """Automatically connect pipes to nearby structures using spatial snapping"""
    try:
        from pipe_structure_connector import PipeStructureConnector
        
        data = request.get_json() or {}
        tolerance_feet = data.get('tolerance_feet', 5.0)
        
        connector = PipeStructureConnector(tolerance_feet=tolerance_feet)
        results = connector.connect_network_pipes(network_id)
        
        if results.get('success'):
            return jsonify(results), 200
        else:
            return jsonify(results), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# SCHEMA RELATIONSHIPS ROUTES
# ============================================================================

@app.route('/schema/relationships')
def schema_relationships():
    """Render the Schema Relationships visualization page"""
    return render_template('schema_relationships.html')

@app.route('/why-this-matters')
def why_this_matters():
    """Render the Why This Matters comparison page"""
    return render_template('why_this_matters.html')

@app.route('/architecture')
def architecture():
    """Render the System Architecture diagram page"""
    return render_template('architecture.html')

@app.route('/api/schema/relationships', methods=['GET'])
def get_schema_relationships():
    """Get table relationships and metadata for visualization"""
    try:
        # Get all tables with estimated row counts (much faster than COUNT(*))
        tables_query = """
            SELECT 
                t.table_name,
                obj_description((quote_ident(t.table_schema)||'.'||quote_ident(t.table_name))::regclass, 'pg_class') as table_description,
                (SELECT count(*) FROM information_schema.columns c 
                 WHERE c.table_name = t.table_name AND c.table_schema = t.table_schema) as column_count,
                COALESCE(
                    (SELECT n_live_tup 
                     FROM pg_stat_user_tables 
                     WHERE schemaname = 'public' AND relname = t.table_name),
                    0
                ) as row_count
            FROM information_schema.tables t
            WHERE t.table_schema = 'public' 
            AND t.table_type = 'BASE TABLE'
            ORDER BY t.table_name
        """
        tables = execute_query(tables_query)
        
        # Get foreign key relationships
        fk_query = """
            SELECT
                tc.table_name as source_table,
                kcu.column_name as source_column,
                ccu.table_name AS target_table,
                ccu.column_name AS target_column,
                tc.constraint_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public'
            ORDER BY tc.table_name
        """
        relationships = execute_query(fk_query)
        
        # Get column details for each table
        columns_query = """
            SELECT 
                c.table_name,
                c.column_name,
                c.data_type,
                c.is_nullable,
                CASE 
                    WHEN pk.column_name IS NOT NULL THEN true 
                    ELSE false 
                END as is_primary_key
            FROM information_schema.columns c
            LEFT JOIN (
                SELECT ku.table_name, ku.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage ku
                    ON tc.constraint_name = ku.constraint_name
                WHERE tc.constraint_type = 'PRIMARY KEY'
                AND tc.table_schema = 'public'
            ) pk ON c.table_name = pk.table_name AND c.column_name = pk.column_name
            WHERE c.table_schema = 'public'
            ORDER BY c.table_name, c.ordinal_position
        """
        all_columns = execute_query(columns_query)
        
        # Group columns by table
        columns_by_table = {}
        for col in all_columns:
            table_name = col['table_name']
            if table_name not in columns_by_table:
                columns_by_table[table_name] = []
            columns_by_table[table_name].append(col)
        
        return jsonify({
            'tables': tables,
            'relationships': relationships,
            'columns': columns_by_table
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# SHEET NOTE MANAGER
# ============================================

@app.route('/sheet-notes')
def sheet_notes_page():
    """Sheet Note Manager page"""
    return render_template('sheet_notes.html')

# ============================================
# GRAVITY PIPE NETWORK EDITOR
# ============================================

@app.route('/gravity-network-editor')
def gravity_network_editor():
    """Gravity Pipe Network Editor page"""
    return render_template('gravity_network_editor.html')

# ============================================
# DXF IMPORT/EXPORT
# ============================================

@app.route('/dxf-tools')
def dxf_tools_page():
    """DXF Import/Export tools page"""
    return render_template('dxf_tools.html')

@app.route('/api/dxf/import', methods=['POST'])
def import_dxf():
    """Import DXF file into database"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.dxf'):
            return jsonify({'error': 'File must be a DXF file'}), 400
        
        # Get parameters
        drawing_id = request.form.get('drawing_id')
        if not drawing_id:
            return jsonify({'error': 'drawing_id is required'}), 400
        
        import_modelspace = request.form.get('import_modelspace', 'true') == 'true'
        import_paperspace = request.form.get('import_paperspace', 'true') == 'true'
        
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join('/tmp', f'{uuid.uuid4()}_{filename}')
        file.save(temp_path)
        
        try:
            # Import DXF
            importer = DXFImporter(DB_CONFIG)
            stats = importer.import_dxf(
                temp_path,
                drawing_id,
                import_modelspace=import_modelspace,
                import_paperspace=import_paperspace
            )
            
            return jsonify({
                'success': len(stats['errors']) == 0,
                'stats': stats
            })
        
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dxf/export', methods=['POST'])
def export_dxf():
    """Export drawing to DXF file"""
    try:
        data = request.get_json()
        
        drawing_id = data.get('drawing_id')
        if not drawing_id:
            return jsonify({'error': 'drawing_id is required'}), 400
        
        dxf_version = data.get('dxf_version', 'AC1027')
        include_modelspace = data.get('include_modelspace', True)
        include_paperspace = data.get('include_paperspace', True)
        layer_filter = data.get('layer_filter')
        
        # Generate output file
        output_filename = f'drawing_{drawing_id}_{uuid.uuid4().hex[:8]}.dxf'
        output_path = os.path.join('/tmp', output_filename)
        
        # Export DXF
        exporter = DXFExporter(DB_CONFIG)
        stats = exporter.export_dxf(
            drawing_id,
            output_path,
            dxf_version=dxf_version,
            include_modelspace=include_modelspace,
            include_paperspace=include_paperspace,
            layer_filter=layer_filter
        )
        
        if not os.path.exists(output_path):
            return jsonify({'error': 'Export failed - file not created'}), 500
        
        # Send file for download
        return send_file(
            output_path,
            as_attachment=True,
            download_name=output_filename,
            mimetype='application/dxf'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dxf/drawings', methods=['GET'])
def get_drawings_for_dxf():
    """Get list of drawings for DXF tools"""
    try:
        query = """
            SELECT 
                d.drawing_id,
                d.drawing_name,
                p.project_name,
                p.client_name,
                d.created_at,
                (SELECT COUNT(*) FROM drawing_entities WHERE drawing_id = d.drawing_id) as entity_count,
                (SELECT COUNT(*) FROM drawing_text WHERE drawing_id = d.drawing_id) as text_count
            FROM drawings d
            LEFT JOIN projects p ON d.project_id = p.project_id
            ORDER BY d.created_at DESC
            LIMIT 100
        """
        
        drawings = execute_query(query)
        return jsonify({'drawings': drawings})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dxf/export-jobs', methods=['GET'])
def get_export_jobs():
    """Get export job history from map export jobs table"""
    try:
        query = """
            SELECT 
                ej.id as export_job_id,
                ej.params->>'drawing_id' as drawing_id,
                d.drawing_name,
                ej.params->>'export_format' as export_format,
                ej.params->>'dxf_version' as dxf_version,
                ej.status,
                ej.params->>'metrics' as metrics,
                ej.created_at as started_at,
                ej.expires_at as completed_at,
                ej.download_url,
                ej.file_size_mb,
                ej.error_message
            FROM export_jobs ej
            LEFT JOIN drawings d ON (ej.params->>'drawing_id')::uuid = d.drawing_id
            ORDER BY ej.created_at DESC
            LIMIT 50
        """
        
        jobs = execute_query(query)
        return jsonify({'jobs': jobs})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# INTELLIGENT DXF WORKFLOW API
# ============================================

@app.route('/api/dxf/import-intelligent', methods=['POST'])
def import_intelligent_dxf():
    """Import DXF file with intelligent object creation from layer patterns"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.dxf'):
            return jsonify({'error': 'File must be a DXF file'}), 400
        
        # Get parameters
        drawing_id = request.form.get('drawing_id')
        if not drawing_id:
            return jsonify({'error': 'drawing_id is required'}), 400
        
        import_modelspace = request.form.get('import_modelspace', 'true') == 'true'
        import_paperspace = request.form.get('import_paperspace', 'true') == 'true'
        
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join('/tmp', f'{uuid.uuid4()}_{filename}')
        file.save(temp_path)
        
        try:
            # Import DXF with intelligent object creation enabled
            importer = DXFImporter(DB_CONFIG, create_intelligent_objects=True)
            stats = importer.import_dxf(
                temp_path,
                drawing_id,
                import_modelspace=import_modelspace,
                import_paperspace=import_paperspace
            )
            
            return jsonify({
                'success': len(stats['errors']) == 0,
                'stats': stats,
                'message': f"Imported {stats.get('entities', 0)} entities and created {stats.get('intelligent_objects_created', 0)} intelligent objects"
            })
        
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dxf/export-intelligent', methods=['POST'])
def export_intelligent_dxf():
    """Export intelligent objects from a project to DXF file with proper layer names"""
    try:
        data = request.get_json()
        
        project_id = data.get('project_id')
        if not project_id:
            return jsonify({'error': 'project_id is required'}), 400
        
        include_types = data.get('include_types')  # Optional filter
        
        # Generate output file
        output_filename = f'project_{project_id}_{uuid.uuid4().hex[:8]}.dxf'
        output_path = os.path.join('/tmp', output_filename)
        
        # Export intelligent objects
        exporter = DXFExporter(DB_CONFIG)
        stats = exporter.export_intelligent_objects_to_dxf(
            project_id,
            output_path,
            include_types=include_types
        )
        
        if not os.path.exists(output_path):
            return jsonify({'error': 'Export failed - file not created'}), 500
        
        # Send file for download
        return send_file(
            output_path,
            as_attachment=True,
            download_name=output_filename,
            mimetype='application/dxf'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dxf/reimport', methods=['POST'])
def reimport_dxf_with_changes():
    """Re-import a DXF file and detect/merge changes to intelligent objects"""
    try:
        from dxf_change_detector import DXFChangeDetector
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.dxf'):
            return jsonify({'error': 'File must be a DXF file'}), 400
        
        # Get parameters
        drawing_id = request.form.get('drawing_id')
        if not drawing_id:
            return jsonify({'error': 'drawing_id is required'}), 400
        
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join('/tmp', f'{uuid.uuid4()}_{filename}')
        file.save(temp_path)
        
        try:
            # Step 1: Import DXF entities (without creating new intelligent objects yet)
            importer = DXFImporter(DB_CONFIG, create_intelligent_objects=False)
            import_stats = importer.import_dxf(
                temp_path,
                drawing_id,
                import_modelspace=True,
                import_paperspace=True
            )
            
            # Step 2: Get the reimported entities from database
            with get_db() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT 
                            entity_id,
                            entity_type,
                            layer_name,
                            ST_AsText(geometry) as geometry_wkt,
                            ST_GeometryType(geometry) as geometry_type,
                            dxf_handle
                        FROM drawing_entities
                        WHERE drawing_id = %s
                    """, (drawing_id,))
                    
                    reimported_entities = [dict(row) for row in cur.fetchall()]
            
            # Step 3: Detect changes
            detector = DXFChangeDetector(DB_CONFIG)
            change_stats = detector.detect_changes(drawing_id, reimported_entities)
            
            return jsonify({
                'success': len(import_stats['errors']) == 0 and len(change_stats['errors']) == 0,
                'import_stats': import_stats,
                'change_stats': change_stats,
                'message': f"Reimported {import_stats.get('entities', 0)} entities, detected {change_stats['geometry_changes']} geometry changes, {change_stats['layer_changes']} layer changes, {change_stats['new_entities']} new entities ({change_stats['new_objects_created']} intelligent objects created), {change_stats['deleted_entities']} deletions"
            })
        
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dxf/sync-status/<drawing_id>', methods=['GET'])
def get_sync_status(drawing_id):
    """Get synchronization status for a drawing's intelligent objects"""
    try:
        query = """
            SELECT 
                object_type,
                sync_status,
                COUNT(*) as count
            FROM dxf_entity_links
            WHERE drawing_id = %s
            GROUP BY object_type, sync_status
            ORDER BY object_type, sync_status
        """
        
        status_counts = execute_query(query, (drawing_id,))
        
        # Get total counts by object type
        query_totals = """
            SELECT 
                object_type,
                COUNT(*) as total_count,
                MAX(last_sync_at) as last_sync
            FROM dxf_entity_links
            WHERE drawing_id = %s
            GROUP BY object_type
            ORDER BY object_type
        """
        
        totals = execute_query(query_totals, (drawing_id,))
        
        return jsonify({
            'status_by_type': status_counts,
            'totals': totals
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# SHEET NOTE MANAGER API
# ============================================

@app.route('/api/sheet-note-sets', methods=['GET'])
def get_sheet_note_sets():
    """Get all sheet note sets for a project"""
    try:
        project_id = request.args.get('project_id')
        
        if not project_id:
            return jsonify({'error': 'project_id is required'}), 400
        
        query = """
            SELECT 
                sns.set_id,
                sns.project_id,
                sns.set_name,
                sns.description,
                sns.discipline,
                sns.is_active,
                sns.created_at,
                (SELECT COUNT(*) FROM project_sheet_notes WHERE set_id = sns.set_id) as note_count
            FROM sheet_note_sets sns
            WHERE sns.project_id = %s::uuid
            ORDER BY sns.is_active DESC, sns.set_name
        """
        
        sets = execute_query(query, (project_id,))
        return jsonify({'sets': sets})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sheet-note-sets', methods=['POST'])
def create_sheet_note_set():
    """Create a new sheet note set"""
    try:
        data = request.get_json()
        
        project_id = data.get('project_id')
        set_name = data.get('set_name')
        description = data.get('description', '')
        discipline = data.get('discipline')
        is_active = data.get('is_active', False)
        
        if not project_id or not set_name:
            return jsonify({'error': 'project_id and set_name are required'}), 400
        
        set_id = str(uuid.uuid4())
        
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO sheet_note_sets 
                    (set_id, project_id, set_name, description, discipline, is_active)
                    VALUES (%s::uuid, %s::uuid, %s, %s, %s, %s)
                    RETURNING set_id, project_id, set_name, description, discipline, is_active, created_at
                """, (set_id, project_id, set_name, description, discipline, is_active))
                
                new_set = dict(cur.fetchone())
                conn.commit()
                
                cache.clear()
                return jsonify({'set': new_set}), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sheet-note-sets/<set_id>', methods=['PUT'])
def update_sheet_note_set(set_id):
    """Update an existing sheet note set"""
    try:
        data = request.get_json()
        
        set_name = data.get('set_name')
        description = data.get('description')
        discipline = data.get('discipline')
        is_active = data.get('is_active')
        
        updates = []
        params = []
        
        if set_name is not None:
            updates.append('set_name = %s')
            params.append(set_name)
        if description is not None:
            updates.append('description = %s')
            params.append(description)
        if discipline is not None:
            updates.append('discipline = %s')
            params.append(discipline)
        if is_active is not None:
            updates.append('is_active = %s')
            params.append(is_active)
        
        if not updates:
            return jsonify({'error': 'No fields to update'}), 400
        
        updates.append('modified_at = CURRENT_TIMESTAMP')
        params.append(set_id)
        
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f"""
                    UPDATE sheet_note_sets 
                    SET {', '.join(updates)}
                    WHERE set_id = %s::uuid
                    RETURNING set_id, project_id, set_name, description, discipline, is_active, modified_at
                """, params)
                
                updated_set = cur.fetchone()
                if not updated_set:
                    return jsonify({'error': 'Set not found'}), 404
                
                conn.commit()
                cache.clear()
                return jsonify({'set': dict(updated_set)})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sheet-note-sets/<set_id>', methods=['DELETE'])
def delete_sheet_note_set(set_id):
    """Delete a sheet note set"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM sheet_note_sets WHERE set_id = %s::uuid', (set_id,))
                
                if cur.rowcount == 0:
                    return jsonify({'error': 'Set not found'}), 404
                
                conn.commit()
                cache.clear()
                return jsonify({'message': 'Set deleted successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-sheet-notes', methods=['GET'])
def get_project_sheet_notes():
    """Get all project sheet notes for a set"""
    try:
        set_id = request.args.get('set_id')
        
        if not set_id:
            return jsonify({'error': 'set_id is required'}), 400
        
        query = """
            SELECT 
                psn.project_note_id,
                psn.set_id,
                psn.standard_note_id,
                psn.display_code,
                psn.custom_title,
                psn.custom_text,
                psn.is_modified,
                psn.sort_order,
                psn.usage_count,
                sn.note_title as standard_title,
                sn.note_text as standard_text,
                sn.note_category,
                sn.discipline
            FROM project_sheet_notes psn
            LEFT JOIN standard_notes sn ON psn.standard_note_id = sn.note_id
            WHERE psn.set_id = %s::uuid
            ORDER BY psn.sort_order, psn.display_code
        """
        
        notes = execute_query(query, (set_id,))
        return jsonify({'notes': notes})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-sheet-notes', methods=['POST'])
def create_project_sheet_note():
    """Create a new project sheet note"""
    try:
        data = request.get_json()
        
        set_id = data.get('set_id')
        standard_note_id = data.get('standard_note_id')
        display_code = data.get('display_code')
        custom_title = data.get('custom_title')
        custom_text = data.get('custom_text')
        
        if not set_id or not display_code:
            return jsonify({'error': 'set_id and display_code are required'}), 400
        
        is_custom = standard_note_id is None
        
        if is_custom and (not custom_title or not custom_text):
            return jsonify({'error': 'custom_title and custom_text required for custom notes'}), 400
        
        if not is_custom and not standard_note_id:
            return jsonify({'error': 'standard_note_id required for standard notes'}), 400
        
        project_note_id = str(uuid.uuid4())
        
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute('SELECT COALESCE(MAX(sort_order), 0) + 1 as next_order FROM project_sheet_notes WHERE set_id = %s::uuid', (set_id,))
                next_sort_order = cur.fetchone()['next_order']
                
                cur.execute("""
                    INSERT INTO project_sheet_notes 
                    (project_note_id, set_id, standard_note_id, display_code, custom_title, custom_text, sort_order)
                    VALUES (%s::uuid, %s::uuid, %s, %s, %s, %s, %s)
                    RETURNING project_note_id, set_id, standard_note_id, display_code, custom_title, custom_text, is_modified, sort_order, usage_count
                """, (project_note_id, set_id, standard_note_id, display_code, custom_title, custom_text, next_sort_order))
                
                new_note = dict(cur.fetchone())
                conn.commit()
                
                cache.clear()
                return jsonify({'note': new_note}), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-sheet-notes/<project_note_id>', methods=['PUT'])
def update_project_sheet_note(project_note_id):
    """Update an existing project sheet note"""
    try:
        data = request.get_json()
        
        display_code = data.get('display_code')
        custom_title = data.get('custom_title')
        custom_text = data.get('custom_text')
        is_modified = data.get('is_modified')
        
        updates = []
        params = []
        
        if display_code is not None:
            updates.append('display_code = %s')
            params.append(display_code)
        if custom_title is not None:
            updates.append('custom_title = %s')
            params.append(custom_title)
        if custom_text is not None:
            updates.append('custom_text = %s')
            params.append(custom_text)
        if is_modified is not None:
            updates.append('is_modified = %s')
            params.append(is_modified)
        
        if not updates:
            return jsonify({'error': 'No fields to update'}), 400
        
        params.append(project_note_id)
        
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f"""
                    UPDATE project_sheet_notes 
                    SET {', '.join(updates)}
                    WHERE project_note_id = %s::uuid
                    RETURNING project_note_id, set_id, standard_note_id, display_code, custom_title, custom_text, is_modified, sort_order, usage_count
                """, params)
                
                updated_note = cur.fetchone()
                if not updated_note:
                    return jsonify({'error': 'Note not found'}), 404
                
                conn.commit()
                cache.clear()
                return jsonify({'note': dict(updated_note)})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-sheet-notes/<project_note_id>', methods=['DELETE'])
def delete_project_sheet_note(project_note_id):
    """Delete a project sheet note"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM project_sheet_notes WHERE project_note_id = %s::uuid', (project_note_id,))
                
                if cur.rowcount == 0:
                    return jsonify({'error': 'Note not found'}), 404
                
                conn.commit()
                cache.clear()
                return jsonify({'message': 'Note deleted successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-sheet-notes/<project_note_id>/reorder', methods=['PATCH'])
def reorder_project_sheet_note(project_note_id):
    """Update sort order for a project sheet note"""
    try:
        data = request.get_json()
        new_sort_order = data.get('sort_order')
        
        if new_sort_order is None:
            return jsonify({'error': 'sort_order is required'}), 400
        
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    UPDATE project_sheet_notes 
                    SET sort_order = %s
                    WHERE project_note_id = %s::uuid
                    RETURNING project_note_id, sort_order
                """, (new_sort_order, project_note_id))
                
                updated_note = cur.fetchone()
                if not updated_note:
                    return jsonify({'error': 'Note not found'}), 404
                
                conn.commit()
                cache.clear()
                return jsonify({'note': dict(updated_note)})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sheet-note-assignments', methods=['GET'])
def get_sheet_note_assignments():
    """Get sheet note assignments by drawing/layout or by project note"""
    try:
        drawing_id = request.args.get('drawing_id')
        layout_name = request.args.get('layout_name')
        project_note_id = request.args.get('project_note_id')
        
        if project_note_id:
            query = """
                SELECT 
                    sna.assignment_id,
                    sna.project_note_id,
                    sna.drawing_id,
                    sna.layout_name,
                    sna.legend_sequence,
                    d.drawing_name,
                    d.drawing_number,
                    p.project_name
                FROM sheet_note_assignments sna
                LEFT JOIN drawings d ON sna.drawing_id = d.drawing_id
                LEFT JOIN projects p ON d.project_id = p.project_id
                WHERE sna.project_note_id = %s::uuid
                ORDER BY d.drawing_name, sna.layout_name, sna.legend_sequence
            """
            assignments = execute_query(query, (project_note_id,))
        
        elif drawing_id and layout_name:
            query = """
                SELECT 
                    sna.assignment_id,
                    sna.project_note_id,
                    sna.drawing_id,
                    sna.layout_name,
                    sna.legend_sequence,
                    psn.display_code,
                    COALESCE(psn.custom_title, sn.note_title) as note_title,
                    COALESCE(psn.custom_text, sn.note_text) as note_text
                FROM sheet_note_assignments sna
                LEFT JOIN project_sheet_notes psn ON sna.project_note_id = psn.project_note_id
                LEFT JOIN standard_notes sn ON psn.standard_note_id = sn.note_id
                WHERE sna.drawing_id = %s::uuid AND sna.layout_name = %s
                ORDER BY sna.legend_sequence
            """
            assignments = execute_query(query, (drawing_id, layout_name))
        
        else:
            return jsonify({'error': 'Either (drawing_id and layout_name) or project_note_id required'}), 400
        
        return jsonify({'assignments': assignments})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sheet-note-assignments', methods=['POST'])
def create_sheet_note_assignment():
    """Create a new sheet note assignment"""
    try:
        data = request.get_json()
        
        project_note_id = data.get('project_note_id')
        drawing_id = data.get('drawing_id')
        layout_name = data.get('layout_name', 'Model')
        
        if not project_note_id or not drawing_id:
            return jsonify({'error': 'project_note_id and drawing_id are required'}), 400
        
        assignment_id = str(uuid.uuid4())
        
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT COALESCE(MAX(legend_sequence), 0) + 1 
                    FROM sheet_note_assignments 
                    WHERE drawing_id = %s::uuid AND layout_name = %s
                """, (drawing_id, layout_name))
                next_sequence = cur.fetchone()[0]
                
                cur.execute("""
                    INSERT INTO sheet_note_assignments 
                    (assignment_id, project_note_id, drawing_id, layout_name, legend_sequence)
                    VALUES (%s::uuid, %s::uuid, %s::uuid, %s, %s)
                    RETURNING assignment_id, project_note_id, drawing_id, layout_name, legend_sequence
                """, (assignment_id, project_note_id, drawing_id, layout_name, next_sequence))
                
                new_assignment = dict(cur.fetchone())
                conn.commit()
                
                cache.clear()
                return jsonify({'assignment': new_assignment}), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sheet-note-assignments/<assignment_id>', methods=['DELETE'])
def delete_sheet_note_assignment(assignment_id):
    """Delete a sheet note assignment"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM sheet_note_assignments WHERE assignment_id = %s::uuid', (assignment_id,))
                
                if cur.rowcount == 0:
                    return jsonify({'error': 'Assignment not found'}), 404
                
                conn.commit()
                cache.clear()
                return jsonify({'message': 'Assignment deleted successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sheet-note-legend', methods=['GET'])
def get_sheet_note_legend():
    """Generate note legend for a drawing/layout"""
    try:
        drawing_id = request.args.get('drawing_id')
        layout_name = request.args.get('layout_name', 'Model')
        
        if not drawing_id:
            return jsonify({'error': 'drawing_id is required'}), 400
        
        query = """
            SELECT 
                sna.legend_sequence,
                psn.display_code,
                COALESCE(psn.custom_title, sn.note_title) as note_title,
                COALESCE(psn.custom_text, sn.note_text) as note_text,
                psn.standard_note_id,
                psn.is_modified
            FROM sheet_note_assignments sna
            LEFT JOIN project_sheet_notes psn ON sna.project_note_id = psn.project_note_id
            LEFT JOIN standard_notes sn ON psn.standard_note_id = sn.note_id
            WHERE sna.drawing_id = %s::uuid AND sna.layout_name = %s
            ORDER BY sna.legend_sequence
        """
        
        legend_items = execute_query(query, (drawing_id, layout_name))
        
        return jsonify({
            'drawing_id': drawing_id,
            'layout_name': layout_name,
            'legend': legend_items,
            'total_notes': len(legend_items)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==========================
# SHEET SET MANAGER API
# ==========================

@app.route('/api/project-details', methods=['GET'])
def get_all_project_details():
    """Get project details for all projects"""
    try:
        query = """
            SELECT pd.*, p.project_name, p.project_number
            FROM project_details pd
            JOIN projects p ON pd.project_id = p.project_id
            ORDER BY p.project_name
        """
        result = execute_query(query)
        return jsonify({'project_details': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-details/<project_id>', methods=['GET'])
def get_project_details(project_id):
    """Get project details for a specific project"""
    try:
        query = """
            SELECT pd.*, p.project_name, p.project_number
            FROM project_details pd
            JOIN projects p ON pd.project_id = p.project_id
            WHERE pd.project_id = %s::uuid
        """
        result = execute_query(query, (project_id,))
        
        if not result:
            return jsonify({'project_details': None})
        
        return jsonify({'project_details': result[0]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-details', methods=['POST'])
def create_project_details():
    """Create project details"""
    try:
        data = request.json
        
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO project_details 
                    (project_id, project_address, project_city, project_state, project_zip,
                     engineer_name, engineer_license, jurisdiction, permit_number,
                     contact_name, contact_phone, contact_email, notes)
                    VALUES (%s::uuid, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                """, (
                    data['project_id'], data.get('project_address'), data.get('project_city'),
                    data.get('project_state'), data.get('project_zip'), data.get('engineer_name'),
                    data.get('engineer_license'), data.get('jurisdiction'), data.get('permit_number'),
                    data.get('contact_name'), data.get('contact_phone'), data.get('contact_email'),
                    data.get('notes')
                ))
                
                details = dict(cur.fetchone())
                conn.commit()
                return jsonify({'project_details': details}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-details/<project_id>', methods=['PUT'])
def update_project_details(project_id):
    """Update project details"""
    try:
        data = request.json
        
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    UPDATE project_details
                    SET project_address = %s, project_city = %s, project_state = %s, project_zip = %s,
                        engineer_name = %s, engineer_license = %s, jurisdiction = %s, permit_number = %s,
                        contact_name = %s, contact_phone = %s, contact_email = %s, notes = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE project_id = %s::uuid
                    RETURNING *
                """, (
                    data.get('project_address'), data.get('project_city'), data.get('project_state'),
                    data.get('project_zip'), data.get('engineer_name'), data.get('engineer_license'),
                    data.get('jurisdiction'), data.get('permit_number'), data.get('contact_name'),
                    data.get('contact_phone'), data.get('contact_email'), data.get('notes'),
                    project_id
                ))
                
                if cur.rowcount == 0:
                    return jsonify({'error': 'Project details not found'}), 404
                
                details = dict(cur.fetchone())
                conn.commit()
                return jsonify({'project_details': details})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Sheet Category Standards
@app.route('/api/sheet-category-standards', methods=['GET'])
def get_sheet_category_standards():
    """Get all sheet category standards"""
    try:
        query = """
            SELECT * FROM sheet_category_standards
            WHERE is_active = TRUE
            ORDER BY default_hierarchy
        """
        result = execute_query(query)
        return jsonify({'categories': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sheet-category-standards', methods=['POST'])
def create_sheet_category_standard():
    """Create new sheet category standard"""
    try:
        data = request.json
        
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO sheet_category_standards
                    (category_code, category_name, default_hierarchy, description)
                    VALUES (%s, %s, %s, %s)
                    RETURNING *
                """, (
                    data['category_code'], data['category_name'],
                    data['default_hierarchy'], data.get('description')
                ))
                
                category = dict(cur.fetchone())
                conn.commit()
                return jsonify({'category': category}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Sheet Sets
@app.route('/api/sheet-sets', methods=['GET'])
def get_sheet_sets():
    """Get all sheet sets, optionally filtered by project"""
    try:
        project_id = request.args.get('project_id')
        
        if project_id:
            query = """
                SELECT ss.*, 
                    COUNT(DISTINCT s.sheet_id) as sheet_count,
                    p.project_name, p.project_number
                FROM sheet_sets ss
                LEFT JOIN sheets s ON ss.set_id = s.set_id
                JOIN projects p ON ss.project_id = p.project_id
                WHERE ss.project_id = %s::uuid
                GROUP BY ss.set_id, p.project_name, p.project_number
                ORDER BY ss.created_at DESC
            """
            result = execute_query(query, (project_id,))
        else:
            query = """
                SELECT ss.*, 
                    COUNT(DISTINCT s.sheet_id) as sheet_count,
                    p.project_name, p.project_number
                FROM sheet_sets ss
                LEFT JOIN sheets s ON ss.set_id = s.set_id
                JOIN projects p ON ss.project_id = p.project_id
                GROUP BY ss.set_id, p.project_name, p.project_number
                ORDER BY ss.created_at DESC
            """
            result = execute_query(query)
        
        return jsonify({'sheet_sets': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sheet-sets', methods=['POST'])
def create_sheet_set():
    """Create new sheet set"""
    try:
        data = request.json
        
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO sheet_sets
                    (project_id, set_name, set_number, phase, discipline, issue_date, status,
                     recipient, transmittal_notes, sheet_note_set_id, is_active)
                    VALUES (%s::uuid, %s, %s, %s, %s, %s, %s, %s, %s, %s::uuid, %s)
                    RETURNING *
                """, (
                    data['project_id'], data['set_name'], data.get('set_number'),
                    data.get('phase'), data.get('discipline'), data.get('issue_date'),
                    data.get('status', 'draft'), data.get('recipient'),
                    data.get('transmittal_notes'), data.get('sheet_note_set_id'),
                    data.get('is_active', True)
                ))
                
                sheet_set = dict(cur.fetchone())
                conn.commit()
                cache.clear()
                return jsonify({'sheet_set': sheet_set}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sheet-sets/<set_id>', methods=['PUT'])
def update_sheet_set(set_id):
    """Update sheet set"""
    try:
        data = request.json
        
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    UPDATE sheet_sets
                    SET set_name = %s, set_number = %s, phase = %s, discipline = %s,
                        issue_date = %s, status = %s, recipient = %s, transmittal_notes = %s,
                        sheet_note_set_id = %s::uuid, is_active = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE set_id = %s::uuid
                    RETURNING *
                """, (
                    data['set_name'], data.get('set_number'), data.get('phase'),
                    data.get('discipline'), data.get('issue_date'), data.get('status'),
                    data.get('recipient'), data.get('transmittal_notes'),
                    data.get('sheet_note_set_id'), data.get('is_active'),
                    set_id
                ))
                
                if cur.rowcount == 0:
                    return jsonify({'error': 'Sheet set not found'}), 404
                
                sheet_set = dict(cur.fetchone())
                conn.commit()
                cache.clear()
                return jsonify({'sheet_set': sheet_set})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sheet-sets/<set_id>', methods=['DELETE'])
def delete_sheet_set(set_id):
    """Delete sheet set and all its sheets"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM sheet_sets WHERE set_id = %s::uuid', (set_id,))
                
                if cur.rowcount == 0:
                    return jsonify({'error': 'Sheet set not found'}), 404
                
                conn.commit()
                cache.clear()
                return jsonify({'message': 'Sheet set deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Sheets
@app.route('/api/sheets', methods=['GET'])
def get_sheets():
    """Get all sheets, optionally filtered by set"""
    try:
        set_id = request.args.get('set_id')
        
        if not set_id:
            return jsonify({'error': 'set_id is required'}), 400
        
        query = """
            SELECT s.*,
                sda.drawing_id,
                sda.layout_name,
                CASE WHEN sda.assignment_id IS NOT NULL THEN 'assigned' ELSE 'unassigned' END as assignment_status
            FROM sheets s
            LEFT JOIN sheet_drawing_assignments sda ON s.sheet_id = sda.sheet_id
            WHERE s.set_id = %s::uuid
            ORDER BY s.sheet_hierarchy_number, s.sheet_code
        """
        result = execute_query(query, (set_id,))
        
        return jsonify({'sheets': result})
    except Exception as e:
        import traceback
        print("ERROR in get_sheets:", str(e))
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/sheets', methods=['POST'])
def create_sheet():
    """Create new sheet"""
    try:
        data = request.json
        
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Insert sheet
                cur.execute("""
                    INSERT INTO sheets
                    (set_id, sheet_code, sheet_title, discipline_code, sheet_type,
                     sheet_category, sheet_hierarchy_number, scale, sheet_size,
                     template_id, revision_number, revision_date, notes, tags)
                    VALUES (%s::uuid, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                """, (
                    data['set_id'], data['sheet_code'], data['sheet_title'],
                    data.get('discipline_code'), data.get('sheet_type'),
                    data.get('sheet_category'), data.get('sheet_hierarchy_number'),
                    data.get('scale'), data.get('sheet_size', '24x36'),
                    data.get('template_id'), data.get('revision_number', 0),
                    data.get('revision_date'), data.get('notes'), data.get('tags')
                ))
                
                sheet = dict(cur.fetchone())
                set_id = sheet['set_id']
                conn.commit()
                
        # Trigger auto-renumbering
        renumber_sheets(str(set_id))
        
        cache.clear()
        return jsonify({'sheet': sheet}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sheets/<sheet_id>', methods=['PUT'])
def update_sheet(sheet_id):
    """Update sheet"""
    try:
        data = request.json
        
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    UPDATE sheets
                    SET sheet_code = %s, sheet_title = %s, discipline_code = %s, sheet_type = %s,
                        sheet_category = %s, sheet_hierarchy_number = %s, scale = %s, sheet_size = %s,
                        template_id = %s, revision_number = %s, revision_date = %s,
                        notes = %s, tags = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE sheet_id = %s::uuid
                    RETURNING *
                """, (
                    data['sheet_code'], data['sheet_title'], data.get('discipline_code'),
                    data.get('sheet_type'), data.get('sheet_category'),
                    data.get('sheet_hierarchy_number'), data.get('scale'),
                    data.get('sheet_size'), data.get('template_id'),
                    data.get('revision_number'), data.get('revision_date'),
                    data.get('notes'), data.get('tags'),
                    sheet_id
                ))
                
                if cur.rowcount == 0:
                    return jsonify({'error': 'Sheet not found'}), 404
                
                sheet = dict(cur.fetchone())
                set_id = sheet['set_id']
                conn.commit()
        
        # Trigger auto-renumbering if hierarchy or category changed
        renumber_sheets(str(set_id))
        
        cache.clear()
        return jsonify({'sheet': sheet})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sheets/<sheet_id>', methods=['DELETE'])
def delete_sheet(sheet_id):
    """Delete sheet"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                # Get set_id before deleting
                cur.execute('SELECT set_id FROM sheets WHERE sheet_id = %s::uuid', (sheet_id,))
                result = cur.fetchone()
                
                if not result:
                    return jsonify({'error': 'Sheet not found'}), 404
                
                set_id = str(result[0])
                
                cur.execute('DELETE FROM sheets WHERE sheet_id = %s::uuid', (sheet_id,))
                conn.commit()
        
        # Trigger auto-renumbering
        renumber_sheets(set_id)
        
        cache.clear()
        return jsonify({'message': 'Sheet deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sheets/renumber/<set_id>', methods=['POST'])
def renumber_sheets_route(set_id):
    """Manually trigger sheet renumbering"""
    try:
        count = renumber_sheets(set_id)
        cache.clear()
        return jsonify({'message': f'Renumbered {count} sheets', 'count': count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def renumber_sheets(set_id):
    """Auto-renumber sheets in a set based on hierarchy and code"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                # Get all sheets sorted by hierarchy and code
                cur.execute("""
                    SELECT sheet_id
                    FROM sheets
                    WHERE set_id = %s::uuid
                    ORDER BY sheet_hierarchy_number NULLS LAST, sheet_code
                """, (set_id,))
                
                sheets = cur.fetchall()
                
                # Update sheet numbers sequentially
                for idx, sheet in enumerate(sheets, start=1):
                    cur.execute("""
                        UPDATE sheets
                        SET sheet_number = %s
                        WHERE sheet_id = %s
                    """, (idx, sheet[0]))
                
                conn.commit()
                return len(sheets)
    except Exception as e:
        print(f"Error renumbering sheets: {e}")
        return 0

# Sheet Drawing Assignments
@app.route('/api/sheet-drawing-assignments', methods=['GET'])
def get_sheet_drawing_assignments():
    """Get drawing assignments for a sheet"""
    try:
        sheet_id = request.args.get('sheet_id')
        
        if not sheet_id:
            return jsonify({'error': 'sheet_id is required'}), 400
        
        query = """
            SELECT sda.*, d.drawing_name
            FROM sheet_drawing_assignments sda
            LEFT JOIN drawings d ON sda.drawing_id = d.drawing_id
            WHERE sda.sheet_id = %s::uuid
        """
        result = execute_query(query, (sheet_id,))
        
        return jsonify({'assignments': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sheet-drawing-assignments', methods=['POST'])
def create_sheet_drawing_assignment():
    """Assign a drawing to a sheet"""
    try:
        data = request.json
        
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO sheet_drawing_assignments
                    (sheet_id, drawing_id, layout_name, assigned_by, notes)
                    VALUES (%s::uuid, %s::uuid, %s, %s, %s)
                    RETURNING *
                """, (
                    data['sheet_id'], data.get('drawing_id'),
                    data.get('layout_name'), data.get('assigned_by'),
                    data.get('notes')
                ))
                
                assignment = dict(cur.fetchone())
                conn.commit()
                cache.clear()
                return jsonify({'assignment': assignment}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sheet-drawing-assignments/<assignment_id>', methods=['DELETE'])
def delete_sheet_drawing_assignment(assignment_id):
    """Unassign drawing from sheet"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM sheet_drawing_assignments WHERE assignment_id = %s::uuid', (assignment_id,))
                
                if cur.rowcount == 0:
                    return jsonify({'error': 'Assignment not found'}), 404
                
                conn.commit()
                cache.clear()
                return jsonify({'message': 'Assignment deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Sheet Revisions
@app.route('/api/sheet-revisions', methods=['GET'])
def get_sheet_revisions():
    """Get revision history for a sheet"""
    try:
        sheet_id = request.args.get('sheet_id')
        
        if not sheet_id:
            return jsonify({'error': 'sheet_id is required'}), 400
        
        query = """
            SELECT * FROM sheet_revisions
            WHERE sheet_id = %s::uuid
            ORDER BY revision_date DESC, revision_number DESC
        """
        result = execute_query(query, (sheet_id,))
        
        return jsonify({'revisions': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sheet-revisions', methods=['POST'])
def create_sheet_revision():
    """Add a revision to a sheet"""
    try:
        data = request.json
        
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO sheet_revisions
                    (sheet_id, revision_number, revision_date, description, revised_by)
                    VALUES (%s::uuid, %s, %s, %s, %s)
                    RETURNING *
                """, (
                    data['sheet_id'], data['revision_number'],
                    data['revision_date'], data.get('description'),
                    data.get('revised_by')
                ))
                
                revision = dict(cur.fetchone())
                conn.commit()
                cache.clear()
                return jsonify({'revision': revision}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Sheet Relationships
@app.route('/api/sheet-relationships', methods=['GET'])
def get_sheet_relationships():
    """Get relationships for a sheet"""
    try:
        sheet_id = request.args.get('sheet_id')
        
        if not sheet_id:
            return jsonify({'error': 'sheet_id is required'}), 400
        
        query = """
            SELECT sr.*,
                s_source.sheet_code as source_sheet_code,
                s_source.sheet_title as source_sheet_title,
                s_target.sheet_code as target_sheet_code,
                s_target.sheet_title as target_sheet_title
            FROM sheet_relationships sr
            JOIN sheets s_source ON sr.source_sheet_id = s_source.sheet_id
            JOIN sheets s_target ON sr.target_sheet_id = s_target.sheet_id
            WHERE sr.source_sheet_id = %s::uuid OR sr.target_sheet_id = %s::uuid
            ORDER BY sr.created_at DESC
        """
        result = execute_query(query, (sheet_id, sheet_id))
        
        return jsonify({'relationships': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sheet-relationships', methods=['POST'])
def create_sheet_relationship():
    """Create a relationship between sheets"""
    try:
        data = request.json
        
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO sheet_relationships
                    (source_sheet_id, target_sheet_id, relationship_type, notes)
                    VALUES (%s::uuid, %s::uuid, %s, %s)
                    RETURNING *
                """, (
                    data['source_sheet_id'], data['target_sheet_id'],
                    data['relationship_type'], data.get('notes')
                ))
                
                relationship = dict(cur.fetchone())
                conn.commit()
                cache.clear()
                return jsonify({'relationship': relationship}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sheet-relationships/<relationship_id>', methods=['DELETE'])
def delete_sheet_relationship(relationship_id):
    """Delete a sheet relationship"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM sheet_relationships WHERE relationship_id = %s::uuid', (relationship_id,))
                
                if cur.rowcount == 0:
                    return jsonify({'error': 'Relationship not found'}), 404
                
                conn.commit()
                cache.clear()
                return jsonify({'message': 'Relationship deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Sheet Index Generator
@app.route('/api/sheet-index/<set_id>', methods=['GET'])
def generate_sheet_index(set_id):
    """Generate sheet index for a set"""
    try:
        query = """
            SELECT 
                sheet_number,
                sheet_code,
                sheet_title,
                scale,
                revision_number,
                revision_date
            FROM sheets
            WHERE set_id = %s::uuid
            ORDER BY sheet_number
        """
        result = execute_query(query, (set_id,))
        
        return jsonify({
            'set_id': set_id,
            'sheets': result,
            'total_sheets': len(result)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Sheet Set Manager UI
@app.route('/sheet-sets')
def sheet_sets():
    """Sheet Set Manager page"""
    return render_template('sheet_sets.html')

# ============================================
# AI TOOLKIT ROUTES
# ============================================

# Import and register toolkit blueprint
try:
    import sys
    sys.path.append('tools')
    from api.toolkit_routes import toolkit_bp
    app.register_blueprint(toolkit_bp)
    print("✓ AI Toolkit API routes registered at /api/toolkit")
except Exception as e:
    print(f"✗ Failed to load AI Toolkit routes: {e}")

@app.route('/toolkit')
def toolkit_page():
    """AI Toolkit Management Page"""
    return render_template('toolkit.html')

@app.route('/graph')
def graph_page():
    """Knowledge Graph Visualization Page"""
    return render_template('graph.html')

@app.route('/quality-dashboard')
def quality_dashboard_page():
    """Quality and Health Dashboard Page"""
    return render_template('quality-dashboard.html')

# ============================================
# MAP VIEWER & EXPORT ROUTES
# ============================================

# Initialize map export service
map_export = MapExportService()

@app.route('/map-viewer')
def map_viewer_page():
    """Redirect to uncached map viewer"""
    return redirect('/map-viewer-v2', code=302)

@app.route('/map-viewer-v2')
def map_viewer_v2_page():
    """Map Viewer Page V2 - Uncached"""
    import time
    response = make_response(render_template('map_viewer_simple.html', cache_bust=int(time.time())))
    response.headers['Cache-Control'] = 'private, no-cache, no-store, must-revalidate, max-age=0, s-maxage=0'
    response.headers['Surrogate-Control'] = 'no-store'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['X-Accel-Expires'] = '0'
    return response

@app.route('/map-test')
def map_test_page():
    """Simple Map Test Page (no base template)"""
    return render_template('map_viewer_simple.html')

@app.route('/api/map-viewer/layers')
def get_gis_layers():
    """Get available GIS layers (external Sonoma County layers)"""
    try:
        query = "SELECT * FROM gis_layers WHERE enabled = true ORDER BY name"
        layers = execute_query(query)
        return jsonify({'layers': layers})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/map-viewer/database-layers')
def get_database_layers():
    """Get available database layers (user's PostGIS data)"""
    try:
        # Define the database layers that contain geospatial data
        db_layers = [
            {
                'id': 'survey_points',
                'name': 'Survey Points',
                'table': 'survey_points',
                'geom_column': 'geometry',
                'geom_type': 'Point',
                'enabled': True,
                'description': 'Survey control points and topo shots'
            },
            {
                'id': 'utility_lines',
                'name': 'Utility Lines',
                'table': 'utility_lines',
                'geom_column': 'geometry',
                'geom_type': 'LineString',
                'enabled': True,
                'description': 'Water, sewer, storm, electric, gas lines'
            },
            {
                'id': 'utility_structures',
                'name': 'Utility Structures',
                'table': 'utility_structures',
                'geom_column': 'geometry',
                'geom_type': 'Point',
                'enabled': True,
                'description': 'Manholes, valves, meters, structures'
            },
            {
                'id': 'parcels',
                'name': 'Parcels',
                'table': 'parcels',
                'geom_column': 'geometry',
                'geom_type': 'Polygon',
                'enabled': True,
                'description': 'Property parcel boundaries'
            },
            {
                'id': 'horizontal_alignments',
                'name': 'Alignments',
                'table': 'horizontal_alignments',
                'geom_column': 'geometry',
                'geom_type': 'LineString',
                'enabled': True,
                'description': 'Horizontal centerline alignments'
            },
            {
                'id': 'surface_features',
                'name': 'Surface Features',
                'table': 'surface_features',
                'geom_column': 'geometry',
                'geom_type': 'Mixed',
                'enabled': True,
                'description': 'General site features (points, lines, polygons)'
            },
            {
                'id': 'drawing_entities',
                'name': 'CAD Entities',
                'table': 'drawing_entities',
                'geom_column': 'geometry',
                'geom_type': 'Mixed',
                'enabled': True,
                'description': 'Lines, polylines, arcs, circles from CAD drawings'
            }
        ]
        
        # Check which tables actually exist and have data
        available_layers = []
        for layer in db_layers:
            try:
                count_query = f"SELECT COUNT(*) as count FROM {layer['table']}"
                result = execute_query(count_query)
                if result and result[0]['count'] > 0:
                    layer['feature_count'] = result[0]['count']
                    available_layers.append(layer)
            except Exception as e:
                # Table doesn't exist or error checking - skip it
                print(f"Skipping layer {layer['id']}: {e}")
                continue
        
        return jsonify({'layers': available_layers})
    except Exception as e:
        print(f"Error getting database layers: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/map-viewer/layer-data/<layer_id>')
def get_layer_data(layer_id):
    """Fetch GIS layer data from FeatureServer and convert to GeoJSON"""
    try:
        import requests
        from arcgis2geojson import arcgis2geojson
        
        # Get layer config
        query = "SELECT * FROM gis_layers WHERE id = %s AND enabled = true"
        layers = execute_query(query, (layer_id,))
        
        if not layers:
            return jsonify({'error': 'Layer not found'}), 404
        
        layer_config = layers[0]
        
        # Get bbox from request params
        minx = request.args.get('minx', type=float)
        miny = request.args.get('miny', type=float)
        maxx = request.args.get('maxx', type=float)
        maxy = request.args.get('maxy', type=float)
        
        if not all([minx, miny, maxx, maxy]):
            return jsonify({'error': 'Missing bbox parameters'}), 400
        
        # Query FeatureServer with ESRI JSON format
        query_url = f"{layer_config['url']}/query"
        query_params = {
            'where': '1=1',
            'geometry': f'{minx},{miny},{maxx},{maxy}',
            'geometryType': 'esriGeometryEnvelope',
            'inSR': '4326',
            'outSR': '4326',
            'spatialRel': 'esriSpatialRelIntersects',
            'outFields': '*',
            'returnGeometry': 'true',
            'resultRecordCount': '1000',
            'f': 'json'  # ESRI JSON format
        }
        
        response = requests.get(query_url, params=query_params, timeout=30)
        response.raise_for_status()
        esri_data = response.json()
        
        # Convert ESRI JSON to GeoJSON
        features = []
        for esri_feature in esri_data.get('features', []):
            try:
                geojson_feature = arcgis2geojson(esri_feature)
                if geojson_feature.get('geometry') is not None:
                    features.append(geojson_feature)
            except Exception as e:
                print(f"Failed to convert feature: {e}")
                continue
        
        return jsonify({
            'type': 'FeatureCollection',
            'features': features
        })
        
    except Exception as e:
        print(f"Error fetching layer data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/map-viewer/database-layer-data/<layer_id>')
def get_database_layer_data(layer_id):
    """Fetch database layer data from PostGIS tables"""
    try:
        # Map layer IDs to table and geometry column
        layer_map = {
            'survey_points': ('survey_points', 'geometry', 'Point'),
            'utility_lines': ('utility_lines', 'geometry', 'LineString'),
            'utility_structures': ('utility_structures', 'geometry', 'Point'),
            'parcels': ('parcels', 'geometry', 'Polygon'),
            'horizontal_alignments': ('horizontal_alignments', 'geometry', 'LineString'),
            'surface_features': ('surface_features', 'geometry', 'Mixed'),
            'drawing_entities': ('drawing_entities', 'geometry', 'Mixed')
        }
        
        if layer_id not in layer_map:
            return jsonify({'error': 'Invalid layer ID'}), 400
        
        table_name, geom_column, geom_type = layer_map[layer_id]
        
        # Get bbox from request params (WGS84)
        minx = request.args.get('minx', type=float)
        miny = request.args.get('miny', type=float)
        maxx = request.args.get('maxx', type=float)
        maxy = request.args.get('maxy', type=float)
        
        if not all([minx, miny, maxx, maxy]):
            return jsonify({'error': 'Missing bbox parameters'}), 400
        
        # Transform bbox from WGS84 to EPSG:2226 for PostGIS query
        from pyproj import Transformer
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:2226", always_xy=True)
        min_x_2226, min_y_2226 = transformer.transform(minx, miny)
        max_x_2226, max_y_2226 = transformer.transform(maxx, maxy)
        
        # Build query to fetch features within bbox (data in EPSG:2226, transformed to WGS84 for output)
        # Get all columns except the geometry column to avoid conflicts
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}' 
                    AND column_name != '{geom_column}'
                """)
                columns = [row[0] for row in cur.fetchall()]
        
        columns_str = ', '.join(columns)
        query = f"""
            SELECT 
                ST_AsGeoJSON(ST_Transform({geom_column}, 4326)) as geometry_json,
                {columns_str}
            FROM {table_name}
            WHERE {geom_column} && ST_MakeEnvelope(%s, %s, %s, %s, 2226)
            LIMIT 1000
        """
        
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (min_x_2226, min_y_2226, max_x_2226, max_y_2226))
                rows = cur.fetchall()
        
        # Convert to GeoJSON features
        features = []
        for row in rows:
            import json
            geom_json = json.loads(row['geometry_json'])
            
            # Build properties (exclude geometry_json column)
            properties = {}
            for key, value in row.items():
                if key != 'geometry_json':
                    # Convert datetime/UUID/etc to string
                    if hasattr(value, 'isoformat'):
                        properties[key] = value.isoformat()
                    elif value is None:
                        continue
                    else:
                        properties[key] = str(value)
            
            features.append({
                'type': 'Feature',
                'geometry': geom_json,
                'properties': properties
            })
        
        return jsonify({
            'type': 'FeatureCollection',
            'features': features
        })
        
    except Exception as e:
        print(f"Error fetching database layer data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/map-viewer/projects')
def get_map_projects():
    """Get all projects with spatial data for map display"""
    try:
        from pyproj import Transformer
        
        # Query all drawings with their projects and bbox
        query = """
            SELECT 
                d.drawing_id,
                d.drawing_name,
                d.drawing_number,
                d.bbox_min_x,
                d.bbox_min_y,
                d.bbox_max_x,
                d.bbox_max_y,
                d.created_at,
                p.project_id,
                p.project_name,
                p.client_name
            FROM drawings d
            JOIN projects p ON d.project_id = p.project_id
            WHERE d.bbox_min_x IS NOT NULL 
              AND d.bbox_min_y IS NOT NULL 
              AND d.bbox_max_x IS NOT NULL 
              AND d.bbox_max_y IS NOT NULL
            ORDER BY d.created_at DESC
        """
        
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                drawings = cur.fetchall()
        
        # Transformer to convert EPSG:2226 to WGS84 for map display
        transformer = Transformer.from_crs("EPSG:2226", "EPSG:4326", always_xy=True)
        
        features = []
        for drawing in drawings:
            # Get bbox in EPSG:2226 (State Plane)
            min_x_2226 = drawing['bbox_min_x']
            min_y_2226 = drawing['bbox_min_y']
            max_x_2226 = drawing['bbox_max_x']
            max_y_2226 = drawing['bbox_max_y']
            
            # Transform all 4 corners to WGS84
            min_lon, min_lat = transformer.transform(min_x_2226, min_y_2226)
            max_lon, max_lat = transformer.transform(max_x_2226, max_y_2226)
            
            # Also transform the other two corners for accurate bbox
            top_left_lon, top_left_lat = transformer.transform(min_x_2226, max_y_2226)
            bottom_right_lon, bottom_right_lat = transformer.transform(max_x_2226, min_y_2226)
            
            # Create GeoJSON polygon in WGS84 (lon, lat order for GeoJSON)
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [[
                        [min_lon, min_lat],              # Bottom-left
                        [bottom_right_lon, bottom_right_lat],  # Bottom-right
                        [max_lon, max_lat],              # Top-right
                        [top_left_lon, top_left_lat],    # Top-left
                        [min_lon, min_lat]               # Close the ring
                    ]]
                },
                'properties': {
                    'drawing_id': str(drawing['drawing_id']),
                    'drawing_name': drawing['drawing_name'],
                    'drawing_number': drawing['drawing_number'],
                    'project_id': str(drawing['project_id']),
                    'project_name': drawing['project_name'],
                    'client_name': drawing['client_name'],
                    'epsg_code': 'EPSG:2226',
                    'created_at': drawing['created_at'].isoformat() if drawing['created_at'] else None
                }
            }
            features.append(feature)
        
        return jsonify({
            'type': 'FeatureCollection',
            'features': features
        })
    except Exception as e:
        print(f"Error fetching projects: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/map-viewer/project-structure')
def get_project_structure():
    """Get all projects with nested drawings and entity type counts"""
    try:
        # Query all projects with their drawings
        # Include projects even without bbox - will calculate from entities if needed
        query = """
            SELECT 
                p.project_id,
                p.project_name,
                p.client_name,
                p.description,
                d.drawing_id,
                d.drawing_name,
                d.drawing_number,
                d.bbox_min_x,
                d.bbox_min_y,
                d.bbox_max_x,
                d.bbox_max_y,
                -- Calculate bbox from entities if drawing bbox is null
                -- Only calculate from entities if they exist (COUNT > 0)
                COALESCE(
                    d.bbox_min_x, 
                    CASE WHEN (SELECT COUNT(*) FROM drawing_entities WHERE drawing_id = d.drawing_id) > 0 
                        THEN (SELECT ST_XMin(ST_Extent(geometry)) FROM drawing_entities WHERE drawing_id = d.drawing_id AND geometry IS NOT NULL)
                        ELSE NULL 
                    END
                ) as calc_min_x,
                COALESCE(
                    d.bbox_min_y, 
                    CASE WHEN (SELECT COUNT(*) FROM drawing_entities WHERE drawing_id = d.drawing_id) > 0 
                        THEN (SELECT ST_YMin(ST_Extent(geometry)) FROM drawing_entities WHERE drawing_id = d.drawing_id AND geometry IS NOT NULL)
                        ELSE NULL 
                    END
                ) as calc_min_y,
                COALESCE(
                    d.bbox_max_x, 
                    CASE WHEN (SELECT COUNT(*) FROM drawing_entities WHERE drawing_id = d.drawing_id) > 0 
                        THEN (SELECT ST_XMax(ST_Extent(geometry)) FROM drawing_entities WHERE drawing_id = d.drawing_id AND geometry IS NOT NULL)
                        ELSE NULL 
                    END
                ) as calc_max_x,
                COALESCE(
                    d.bbox_max_y, 
                    CASE WHEN (SELECT COUNT(*) FROM drawing_entities WHERE drawing_id = d.drawing_id) > 0 
                        THEN (SELECT ST_YMax(ST_Extent(geometry)) FROM drawing_entities WHERE drawing_id = d.drawing_id AND geometry IS NOT NULL)
                        ELSE NULL 
                    END
                ) as calc_max_y
            FROM projects p
            LEFT JOIN drawings d ON p.project_id = d.project_id
            WHERE d.drawing_id IS NOT NULL
            ORDER BY p.created_at DESC, p.project_name, d.drawing_name
        """
        
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                rows = cur.fetchall()
        
        # Group by project
        projects = {}
        for row in rows:
            project_id = str(row['project_id'])
            
            # Use calculated bbox (from entities) if drawing bbox is null
            bbox_min_x = row['calc_min_x']
            bbox_min_y = row['calc_min_y']
            bbox_max_x = row['calc_max_x']
            bbox_max_y = row['calc_max_y']
            
            if project_id not in projects:
                projects[project_id] = {
                    'project_id': project_id,
                    'project_name': row['project_name'],
                    'client_name': row['client_name'],
                    'description': row['description'],
                    'drawings': [],
                    'bbox': {
                        'min_x': bbox_min_x,
                        'min_y': bbox_min_y,
                        'max_x': bbox_max_x,
                        'max_y': bbox_max_y
                    } if bbox_min_x is not None else None
                }
            
            # Update project bbox to include all drawings
            if bbox_min_x is not None:
                if projects[project_id]['bbox'] is None:
                    projects[project_id]['bbox'] = {
                        'min_x': bbox_min_x,
                        'min_y': bbox_min_y,
                        'max_x': bbox_max_x,
                        'max_y': bbox_max_y
                    }
                else:
                    projects[project_id]['bbox']['min_x'] = min(projects[project_id]['bbox']['min_x'], bbox_min_x)
                    projects[project_id]['bbox']['min_y'] = min(projects[project_id]['bbox']['min_y'], bbox_min_y)
                    projects[project_id]['bbox']['max_x'] = max(projects[project_id]['bbox']['max_x'], bbox_max_x)
                    projects[project_id]['bbox']['max_y'] = max(projects[project_id]['bbox']['max_y'], bbox_max_y)
            
            if row['drawing_id']:
                drawing_id = str(row['drawing_id'])
                
                # Get entity type counts for this drawing (combine LINE/ARC/LWPOLYLINE into Linework)
                entity_query = """
                    SELECT 
                        CASE 
                            WHEN entity_type IN ('LINE', 'ARC', 'LWPOLYLINE', 'POLYLINE', 'CIRCLE', 'ELLIPSE', 'SPLINE') 
                            THEN 'Linework'
                            ELSE entity_type
                        END as entity_type,
                        COUNT(*) as count
                    FROM drawing_entities
                    WHERE drawing_id = %s
                    AND entity_type NOT IN ('TEXT', 'MTEXT', 'HATCH', 'ATTDEF', 'ATTRIB')
                    GROUP BY CASE 
                        WHEN entity_type IN ('LINE', 'ARC', 'LWPOLYLINE', 'POLYLINE', 'CIRCLE', 'ELLIPSE', 'SPLINE') 
                        THEN 'Linework'
                        ELSE entity_type
                    END
                    ORDER BY count DESC
                """
                
                with get_db() as conn2:
                    with conn2.cursor(cursor_factory=RealDictCursor) as cur2:
                        cur2.execute(entity_query, (drawing_id,))
                        entity_types = cur2.fetchall()
                
                projects[project_id]['drawings'].append({
                    'drawing_id': drawing_id,
                    'drawing_name': row['drawing_name'],
                    'drawing_number': row['drawing_number'],
                    'entity_types': [
                        {
                            'type': et['entity_type'],
                            'count': et['count']
                        }
                        for et in entity_types
                    ],
                    'total_entities': sum(et['count'] for et in entity_types)
                })
        
        return jsonify({
            'projects': list(projects.values())
        })
    except Exception as e:
        print(f"Error fetching project structure: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/map-viewer/project-entities/<drawing_id>')
def get_project_entities(drawing_id):
    """Get all drawing entities for a specific DXF project, optionally filtered by entity type"""
    try:
        import json
        
        # Get optional entity_type filter from query params
        entity_type = request.args.get('entity_type', None)
        
        # Query drawing entities with layer information
        query = """
            SELECT 
                e.entity_id,
                e.entity_type,
                e.color_aci,
                e.linetype,
                e.lineweight,
                e.transparency,
                e.attributes,
                l.layer_name,
                l.color as layer_color,
                CASE 
                    WHEN ST_SRID(e.geometry) = 0 THEN ST_AsGeoJSON(e.geometry)
                    ELSE ST_AsGeoJSON(ST_Transform(e.geometry, 4326))
                END as geometry,
                ST_SRID(e.geometry) as srid
            FROM drawing_entities e
            LEFT JOIN layers l ON e.layer_id = l.layer_id
            WHERE e.drawing_id = %s
            AND e.entity_type NOT IN ('TEXT', 'MTEXT', 'HATCH', 'ATTDEF', 'ATTRIB')
        """
        
        params = [drawing_id]
        
        # Add entity type filter if specified (translate "Linework" to all line-based types)
        if entity_type:
            if entity_type == 'Linework':
                query += " AND e.entity_type IN ('LINE', 'ARC', 'LWPOLYLINE', 'POLYLINE', 'CIRCLE', 'ELLIPSE', 'SPLINE')"
            else:
                query += " AND e.entity_type = %s"
                params.append(entity_type)
        
        query += " LIMIT 5000"
        
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, tuple(params))
                entities = cur.fetchall()
        
        # Convert to GeoJSON features
        features = []
        for entity in entities:
            try:
                geom_json = json.loads(entity['geometry'])
                
                # Build properties
                properties = {
                    'entity_id': str(entity['entity_id']),
                    'entity_type': entity['entity_type'],
                    'layer_name': entity['layer_name'],
                    'color_aci': entity['color_aci'],
                    'layer_color': entity['layer_color'],
                    'linetype': entity['linetype'],
                    'lineweight': entity['lineweight'],
                    'transparency': entity['transparency'],
                    'srid': entity['srid']
                }
                
                # Add attributes if present
                if entity['attributes']:
                    properties['attributes'] = entity['attributes']
                
                features.append({
                    'type': 'Feature',
                    'geometry': geom_json,
                    'properties': properties
                })
            except Exception as e:
                print(f"Error processing entity {entity.get('entity_id')}: {e}")
                continue
        
        return jsonify({
            'type': 'FeatureCollection',
            'features': features,
            'count': len(features)
        })
        
    except Exception as e:
        print(f"Error fetching project entities: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/map-viewer/drawing-extent/<drawing_id>')
def get_drawing_extent(drawing_id):
    """Get bounding box extent for a drawing's entities"""
    try:
        from pyproj import Transformer
        
        query = """
            SELECT 
                ST_XMin(ST_Extent(geometry)) as xmin,
                ST_YMin(ST_Extent(geometry)) as ymin,
                ST_XMax(ST_Extent(geometry)) as xmax,
                ST_YMax(ST_Extent(geometry)) as ymax,
                COUNT(*) as entity_count,
                (SELECT ST_SRID(geometry) FROM drawing_entities WHERE drawing_id = %s LIMIT 1) as srid
            FROM drawing_entities
            WHERE drawing_id = %s
        """
        
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (drawing_id, drawing_id))
                result = cur.fetchone()
        
        if not result or result['entity_count'] == 0:
            return jsonify({'error': 'No entities found for this drawing'}), 404
        
        srid = result['srid'] or 0
        
        # For SRID 0 (local CAD coordinates), return native bounds without transformation
        if srid == 0:
            return jsonify({
                'bounds': None,  # Can't display on geographic map
                'entity_count': result['entity_count'],
                'native_bounds': {
                    'xmin': float(result['xmin']),
                    'ymin': float(result['ymin']),
                    'xmax': float(result['xmax']),
                    'ymax': float(result['ymax']),
                    'srid': 0
                },
                'is_local_coordinates': True
            })
        
        # Transform from geographic SRID to WGS84 for map display
        transformer = Transformer.from_crs(f"EPSG:{srid}", "EPSG:4326", always_xy=True)
        
        # Transform the bounding box corners
        sw_lon, sw_lat = transformer.transform(result['xmin'], result['ymin'])
        ne_lon, ne_lat = transformer.transform(result['xmax'], result['ymax'])
        
        return jsonify({
            'bounds': [[sw_lat, sw_lon], [ne_lat, ne_lon]],
            'entity_count': result['entity_count'],
            'native_bounds': {
                'xmin': float(result['xmin']),
                'ymin': float(result['ymin']),
                'xmax': float(result['xmax']),
                'ymax': float(result['ymax']),
                'srid': srid
            },
            'is_local_coordinates': False
        })
        
    except Exception as e:
        print(f"Error getting drawing extent: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/map-export/create-simple', methods=['POST'])
def create_simple_export():
    """Create shapefile with real GIS data from Sonoma County"""
    try:
        import requests
        from shapely.geometry import shape, box
        from shapely import geometry as geom_lib
        from pyproj import Transformer
        import fiona
        from fiona.crs import from_epsg
        
        params = request.json
        bbox = params.get('bbox', {})
        requested_layers = params.get('layers', ['parcels', 'buildings', 'roads'])
        
        print(f"Creating export for bbox: {bbox}")
        print(f"Requested layers: {requested_layers}")
        
        # Create unique ID for this export
        export_id = str(uuid.uuid4())
        export_dir = os.path.join('/tmp/exports', export_id)
        os.makedirs(export_dir, exist_ok=True)
        
        # Get bounding box in WGS84
        minx, miny, maxx, maxy = bbox['minx'], bbox['miny'], bbox['maxx'], bbox['maxy']
        
        # Coordinate transformer
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:2226", always_xy=True)
        
        # Get GIS layer configurations from database
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM gis_layers WHERE enabled = true AND id = ANY(%s)", (requested_layers,))
                layers = cur.fetchall()
        
        print(f"Found {len(layers)} layers in database matching requested layers")
        if len(layers) == 0:
            print(f"WARNING: No layers found! Requested: {requested_layers}")
            print("Checking all available layers...")
            with get_db() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT id, name, enabled FROM gis_layers")
                    all_layers = cur.fetchall()
                    print(f"All layers in DB: {all_layers}")
        
        feature_counts = {}
        
        # Fetch and export each layer
        for layer_config in layers:
            layer_id = layer_config['id']
            layer_url = layer_config['url']
            layer_name = layer_config['name']
            
            print(f"Fetching {layer_name} from {layer_url}")
            
            try:
                # Query FeatureServer with bounding box
                query_url = f"{layer_url}/query"
                query_params = {
                    'where': '1=1',
                    'geometry': f'{minx},{miny},{maxx},{maxy}',
                    'geometryType': 'esriGeometryEnvelope',
                    'inSR': '4326',
                    'spatialRel': 'esriSpatialRelIntersects',
                    'outFields': '*',
                    'returnGeometry': 'true',
                    'outSR': '4326',  # Return in WGS84
                    'f': 'json'  # ESRI JSON format (geojson not supported)
                }
                
                response = requests.get(query_url, params=query_params, timeout=30)
                response.raise_for_status()
                esri_data = response.json()
                
                # Convert ESRI JSON features to GeoJSON using arcgis2geojson library
                from arcgis2geojson import arcgis2geojson
                
                features = []
                skipped = 0
                total_features = len(esri_data.get('features', []))
                
                for esri_feature in esri_data.get('features', []):
                    try:
                        # arcgis2geojson handles all geometry types, MultiPolygons, null geoms
                        geojson_feature = arcgis2geojson(esri_feature)
                        
                        # Skip features with null geometries
                        if geojson_feature.get('geometry') is not None:
                            features.append(geojson_feature)
                        else:
                            skipped += 1
                    except Exception as e:
                        print(f"  WARNING: Failed to convert feature: {e}")
                        skipped += 1
                        continue
                
                feature_counts[layer_id] = len(features)
                if skipped > 0:
                    print(f"  Skipped {skipped}/{total_features} features (null/invalid geometries)")
                
                print(f"  Found {len(features)} features in {layer_name}")
                
                if len(features) == 0:
                    continue
                
                # Determine geometry type from first feature
                first_geom = shape(features[0]['geometry'])
                geom_type = first_geom.geom_type
                
                # Create schema based on first feature properties
                sample_props = features[0]['properties']
                schema_props = {}
                for key, value in sample_props.items():
                    if value is None:
                        schema_props[key] = 'str'
                    elif isinstance(value, bool):
                        schema_props[key] = 'bool'
                    elif isinstance(value, int):
                        schema_props[key] = 'int'
                    elif isinstance(value, float):
                        schema_props[key] = 'float'
                    else:
                        schema_props[key] = 'str'
                
                schema = {
                    'geometry': geom_type,
                    'properties': schema_props
                }
                
                # Create shapefile for this layer
                shp_path = os.path.join(export_dir, f'{layer_id}.shp')
                
                with fiona.open(shp_path, 'w', driver='ESRI Shapefile',
                               crs=from_epsg(2226), schema=schema) as output:
                    for feature in features:
                        # Transform geometry to EPSG:2226
                        geom_wgs84 = shape(feature['geometry'])
                        
                        # Transform coordinates
                        if geom_wgs84.geom_type == 'Point':
                            x, y = transformer.transform(geom_wgs84.x, geom_wgs84.y)
                            geom_2226 = geom_lib.Point(x, y)
                        elif geom_wgs84.geom_type in ['LineString', 'MultiLineString']:
                            coords_2226 = [transformer.transform(x, y) for x, y in geom_wgs84.coords]
                            geom_2226 = geom_lib.LineString(coords_2226)
                        elif geom_wgs84.geom_type == 'Polygon':
                            exterior_2226 = [transformer.transform(x, y) for x, y in geom_wgs84.exterior.coords]
                            geom_2226 = geom_lib.Polygon(exterior_2226)
                        elif geom_wgs84.geom_type == 'MultiPolygon':
                            polys_2226 = []
                            for poly in geom_wgs84.geoms:
                                exterior_2226 = [transformer.transform(x, y) for x, y in poly.exterior.coords]
                                polys_2226.append(geom_lib.Polygon(exterior_2226))
                            geom_2226 = geom_lib.MultiPolygon(polys_2226)
                        else:
                            continue  # Skip unsupported geometry types
                        
                        output.write({
                            'geometry': geom_2226.__geo_interface__,
                            'properties': feature['properties']
                        })
                
                print(f"  Wrote {len(features)} features to {layer_id}.shp")
                
            except Exception as e:
                print(f"  ERROR fetching {layer_name}: {e}")
                feature_counts[layer_id] = 0
        
        # Create download URL
        download_url = f"/api/map-export/download-simple/{export_id}"
        
        return jsonify({
            'status': 'complete',
            'download_url': download_url,
            'export_id': export_id,
            'feature_counts': feature_counts,
            'message': f'Exported {sum(feature_counts.values())} total features'
        })
        
    except Exception as e:
        print(f"ERROR in create_simple_export: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/map-export/create', methods=['POST'])
def create_multi_format_export():
    """Create export with multiple formats (PNG, DXF, SHP, KML)"""
    try:
        import requests
        from shapely.geometry import shape
        from shapely import geometry as geom_lib
        from pyproj import Transformer
        
        params = request.json
        bbox = params.get('bbox', {})
        requested_layers = params.get('layers', [])
        formats = params.get('formats', ['shp'])  # Default to shapefile only
        png_options = params.get('png_options', {'north_arrow': True, 'scale_bar': True})
        
        print(f"Creating multi-format export:")
        print(f"  Formats: {formats}")
        print(f"  Layers: {requested_layers}")
        print(f"  PNG options: {png_options}")
        
        # Create unique ID for this export
        export_id = str(uuid.uuid4())
        export_dir = os.path.join('/tmp/exports', export_id)
        os.makedirs(export_dir, exist_ok=True)
        
        # Get bounding box in WGS84
        minx, miny, maxx, maxy = bbox['minx'], bbox['miny'], bbox['maxx'], bbox['maxy']
        
        # Coordinate transformer
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:2226", always_xy=True)
        
        # Get GIS layer configurations from database
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM gis_layers WHERE enabled = true AND id = ANY(%s)", (requested_layers,))
                layers = cur.fetchall()
        
        print(f"Found {len(layers)} layers in database")
        
        # PRIORITY 1: Fetch drawing entities from database (automatic, ALL layers)
        print("Fetching drawing entities from database...")
        all_layers_data = {}
        feature_counts = {}
        
        # Transform bbox to EPSG:2226 for PostGIS query
        min_x_2226, min_y_2226 = transformer.transform(minx, miny)
        max_x_2226, max_y_2226 = transformer.transform(maxx, maxy)
        bbox_2226 = (min_x_2226, min_y_2226, max_x_2226, max_y_2226)
        
        # Use MapExportService with database connection
        from map_export_service import MapExportService
        with get_db() as conn:
            export_service = MapExportService(db_conn=conn)
            drawing_layers = export_service.fetch_drawing_entities_by_layer(bbox_2226)
            
            if drawing_layers:
                print(f"Found {len(drawing_layers)} DXF-imported layers")
                for layer_name, features in drawing_layers.items():
                    # Features are already in EPSG:2226, need to transform to WGS84 for consistency
                    features_wgs84 = []
                    back_transformer = Transformer.from_crs("EPSG:2226", "EPSG:4326", always_xy=True)
                    
                    for feature in features:
                        try:
                            geom_2226 = shape(feature['geometry'])
                            
                            # Transform to WGS84 (handle both 2D and 3D geometries)
                            if geom_2226.geom_type == 'LineString':
                                # Handle 3D coordinates (x, y, z) by ignoring Z
                                coords_wgs84 = []
                                for coord in geom_2226.coords:
                                    x, y = coord[0], coord[1]  # Ignore Z if present
                                    lon, lat = back_transformer.transform(x, y)
                                    coords_wgs84.append((lon, lat))
                                geom_wgs84 = geom_lib.LineString(coords_wgs84)
                            elif geom_2226.geom_type == 'Polygon':
                                exterior_wgs84 = []
                                for coord in geom_2226.exterior.coords:
                                    x, y = coord[0], coord[1]  # Ignore Z if present
                                    lon, lat = back_transformer.transform(x, y)
                                    exterior_wgs84.append((lon, lat))
                                geom_wgs84 = geom_lib.Polygon(exterior_wgs84)
                            elif geom_2226.geom_type == 'Point':
                                x, y = geom_2226.x, geom_2226.y
                                lon, lat = back_transformer.transform(x, y)
                                geom_wgs84 = geom_lib.Point(lon, lat)
                            else:
                                geom_wgs84 = geom_2226  # Keep as-is for unsupported types
                            
                            features_wgs84.append({
                                'type': 'Feature',
                                'geometry': geom_wgs84.__geo_interface__,
                                'properties': feature['properties']
                            })
                        except Exception as e:
                            print(f"Error transforming drawing entity: {e}")
                            import traceback
                            traceback.print_exc()
                            continue
                    
                    all_layers_data[layer_name] = features_wgs84
                    feature_counts[layer_name] = len(features_wgs84)
                    print(f"  {layer_name}: {len(features_wgs84)} features")
        
        # PRIORITY 2: Fetch external WFS layers
        for layer_config in layers:
            layer_id = layer_config['id']
            layer_url = layer_config['url']
            layer_name = layer_config['name']
            
            print(f"Fetching external WFS layer {layer_name}...")
            
            try:
                # Query FeatureServer with bounding box
                query_url = f"{layer_url}/query"
                query_params = {
                    'where': '1=1',
                    'geometry': f'{minx},{miny},{maxx},{maxy}',
                    'geometryType': 'esriGeometryEnvelope',
                    'inSR': '4326',
                    'spatialRel': 'esriSpatialRelIntersects',
                    'outFields': '*',
                    'returnGeometry': 'true',
                    'outSR': '4326',
                    'f': 'json'
                }
                
                response = requests.get(query_url, params=query_params, timeout=30)
                response.raise_for_status()
                esri_data = response.json()
                
                # Convert ESRI JSON to GeoJSON
                from arcgis2geojson import arcgis2geojson
                
                features = []
                for esri_feature in esri_data.get('features', []):
                    try:
                        geojson_feature = arcgis2geojson(esri_feature)
                        if geojson_feature.get('geometry') is not None:
                            features.append(geojson_feature)
                    except Exception as e:
                        continue
                
                feature_counts[layer_id] = len(features)
                all_layers_data[layer_id] = features
                print(f"  Found {len(features)} features")
                
            except Exception as e:
                print(f"  ERROR fetching {layer_name}: {e}")
                feature_counts[layer_id] = 0
        
        # Legacy: Fetch CAD entity layers if explicitly requested (backwards compatibility)
        entity_layers = params.get('entity_layers', [])
        if entity_layers:
            print(f"Fetching {len(entity_layers)} CAD entity layer(s)...")
            
            # Transform bbox to EPSG:2226 for PostGIS query
            min_x_2226, min_y_2226 = transformer.transform(minx, miny)
            max_x_2226, max_y_2226 = transformer.transform(maxx, maxy)
            
            for entity_layer in entity_layers:
                drawing_id = entity_layer.get('drawingId')
                entity_type = entity_layer.get('entityType')
                layer_key = f"entities_{drawing_id}_{entity_type}"
                
                print(f"  Fetching {entity_type} from drawing {drawing_id}...")
                
                try:
                    with get_db() as conn:
                        with conn.cursor(cursor_factory=RealDictCursor) as cur:
                            # Query drawing_entities within bbox
                            cur.execute("""
                                SELECT 
                                    entity_id,
                                    entity_type,
                                    color_aci,
                                    linetype,
                                    lineweight,
                                    transparency,
                                    ST_AsGeoJSON(ST_Transform(geometry, 4326)) as geometry_json,
                                    attributes
                                FROM drawing_entities
                                WHERE drawing_id = %s 
                                AND entity_type = %s
                                AND geometry && ST_MakeEnvelope(%s, %s, %s, %s, 2226)
                                AND geometry IS NOT NULL
                                LIMIT 5000
                            """, (drawing_id, entity_type, min_x_2226, min_y_2226, max_x_2226, max_y_2226))
                            
                            rows = cur.fetchall()
                            
                            # Convert to GeoJSON features
                            features = []
                            for row in rows:
                                feature = {
                                    'type': 'Feature',
                                    'geometry': json.loads(row['geometry_json']),
                                    'properties': {
                                        'entity_id': str(row['entity_id']),
                                        'entity_type': row['entity_type'],
                                        'color_aci': row['color_aci'],
                                        'linetype': row['linetype'] or 'Continuous',
                                        'lineweight': row['lineweight'] or 0,
                                        'transparency': row['transparency'] or 0
                                    }
                                }
                                features.append(feature)
                            
                            feature_counts[layer_key] = len(features)
                            all_layers_data[layer_key] = features
                            print(f"    Found {len(features)} {entity_type} entities")
                            
                except Exception as e:
                    print(f"    ERROR fetching {entity_type}: {e}")
                    import traceback
                    traceback.print_exc()
                    feature_counts[layer_key] = 0
        
        # Transform all features to EPSG:2226 first (needed for DXF, SHP, KML, PNG)
        from shapely import geometry as geom_lib
        all_layers_2226 = {}
        
        for layer_id, features_wgs84 in all_layers_data.items():
            if not features_wgs84:
                continue
            
            transformed_features = []
            for feature in features_wgs84:
                try:
                    geom_wgs84 = shape(feature['geometry'])
                    
                    # Transform to EPSG:2226
                    if geom_wgs84.geom_type == 'Polygon':
                        exterior_2226 = [transformer.transform(x, y) for x, y in geom_wgs84.exterior.coords]
                        geom_2226 = geom_lib.Polygon(exterior_2226)
                    elif geom_wgs84.geom_type == 'MultiPolygon':
                        polys_2226 = []
                        for poly in geom_wgs84.geoms:
                            exterior_2226 = [transformer.transform(x, y) for x, y in poly.exterior.coords]
                            polys_2226.append(geom_lib.Polygon(exterior_2226))
                        geom_2226 = geom_lib.MultiPolygon(polys_2226)
                    elif geom_wgs84.geom_type == 'LineString':
                        coords_2226 = [transformer.transform(x, y) for x, y in geom_wgs84.coords]
                        geom_2226 = geom_lib.LineString(coords_2226)
                    elif geom_wgs84.geom_type == 'MultiLineString':
                        lines_2226 = []
                        for line in geom_wgs84.geoms:
                            coords_2226 = [transformer.transform(x, y) for x, y in line.coords]
                            lines_2226.append(geom_lib.LineString(coords_2226))
                        geom_2226 = geom_lib.MultiLineString(lines_2226)
                    elif geom_wgs84.geom_type == 'Point':
                        x, y = transformer.transform(geom_wgs84.x, geom_wgs84.y)
                        geom_2226 = geom_lib.Point(x, y)
                    elif geom_wgs84.geom_type == 'MultiPoint':
                        points_2226 = []
                        for point in geom_wgs84.geoms:
                            x, y = transformer.transform(point.x, point.y)
                            points_2226.append(geom_lib.Point(x, y))
                        geom_2226 = geom_lib.MultiPoint(points_2226)
                    else:
                        continue  # Skip unsupported geometry types
                    
                    transformed_features.append({
                        'type': 'Feature',
                        'geometry': geom_2226.__geo_interface__,
                        'properties': feature['properties']
                    })
                except Exception as e:
                    print(f"Error transforming feature: {e}")
                    continue
            
            all_layers_2226[layer_id] = transformed_features
        
        # Now create each requested format
        created_files = []
        
        # 1. Shapefile (SHP)
        if 'shp' in formats:
            print("Creating Shapefile...")
            from map_export_service import MapExportService
            export_service = MapExportService()
            
            for layer_id, features_2226 in all_layers_2226.items():
                if not features_2226:
                    continue
                
                try:
                    shp_path = os.path.join(export_dir, f'{layer_id}.shp')
                    if export_service.export_to_shapefile(features_2226, layer_id, shp_path):
                        created_files.append(f'{layer_id}.shp')
                except Exception as e:
                    print(f"Error creating shapefile for {layer_id}: {e}")
        
        # 2. DXF
        if 'dxf' in formats:
            print("Creating DXF...")
            try:
                from map_export_service import MapExportService
                export_service = MapExportService()
                
                dxf_path = os.path.join(export_dir, 'export.dxf')
                if export_service.export_to_dxf(all_layers_2226, dxf_path):
                    created_files.append('export.dxf')
            except Exception as e:
                print(f"Error creating DXF: {e}")
        
        # 3. KML
        if 'kml' in formats:
            print("Creating KML...")
            try:
                from map_export_service import MapExportService
                export_service = MapExportService()
                
                # KML export expects EPSG:2226 data and transforms to WGS84 internally
                kml_path = os.path.join(export_dir, 'export.kml')
                if export_service.export_to_kml(all_layers_2226, kml_path):
                    created_files.append('export.kml')
            except Exception as e:
                print(f"Error creating KML: {e}")
        
        # 4. PNG
        if 'png' in formats:
            print("Creating PNG...")
            try:
                from map_export_service import MapExportService
                export_service = MapExportService()
                
                # Transform bbox to EPSG:2226 for scale calculations
                bbox_2226 = export_service.transform_bbox(bbox, 'EPSG:4326')
                bbox_dict = {
                    'minx': bbox_2226[0],
                    'miny': bbox_2226[1],
                    'maxx': bbox_2226[2],
                    'maxy': bbox_2226[3]
                }
                
                png_path = export_service.create_map_image(
                    bbox_dict,
                    north_arrow=png_options.get('north_arrow', True),
                    scale_bar=png_options.get('scale_bar', True)
                )
                
                if png_path and os.path.exists(png_path):
                    # Move to export dir
                    import shutil
                    dest_path = os.path.join(export_dir, 'map.png')
                    shutil.move(png_path, dest_path)
                    created_files.append('map.png')
            except Exception as e:
                print(f"Error creating PNG: {e}")
        
        print(f"Created files: {created_files}")
        
        # Create download URL
        download_url = f"/api/map-export/download-simple/{export_id}"
        
        return jsonify({
            'status': 'complete',
            'download_url': download_url,
            'export_id': export_id,
            'feature_counts': feature_counts,
            'formats': formats,
            'created_files': created_files,
            'message': f'Exported {sum(feature_counts.values())} total features in {len(formats)} format(s)'
        })
        
    except Exception as e:
        print(f"ERROR in create_multi_format_export: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/map-export/download-simple/<export_id>')
def download_simple_export(export_id):
    """Download simple export as ZIP file"""
    try:
        export_dir = os.path.join('/tmp/exports', export_id)
        
        if not os.path.exists(export_dir):
            return jsonify({'error': 'Export not found or expired'}), 404
        
        # Create ZIP file with all shapefile components
        import zipfile
        zip_path = os.path.join('/tmp', f'{export_id}.zip')
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for filename in os.listdir(export_dir):
                file_path = os.path.join(export_dir, filename)
                zipf.write(file_path, filename)
        
        return send_file(zip_path, 
                        as_attachment=True,
                        download_name=f'sonoma_export_{export_id[:8]}.zip',
                        mimetype='application/zip')
        
    except Exception as e:
        print(f"Download error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/map-export/status/<job_id>')
def get_export_status(job_id):
    """Get export job status"""
    try:
        query = """
            SELECT id, status, download_url, file_size_mb, 
                   error_message, created_at, expires_at
            FROM map_export_jobs
            WHERE id = %s::uuid
        """
        result = execute_query(query, (job_id,))
        
        if not result:
            return jsonify({'error': 'Job not found'}), 404
        
        job = result[0]
        response = {
            'job_id': str(job['id']),
            'status': job['status']
        }
        
        if job['status'] == 'complete':
            response.update({
                'download_url': job['download_url'],
                'file_size_mb': job['file_size_mb'],
                'expires_at': job['expires_at'].isoformat() if job['expires_at'] else None
            })
        elif job['status'] == 'failed':
            response['error'] = job['error_message']
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/map-export/download/<job_id>/<filename>')
def download_export(job_id, filename):
    """Download export file"""
    try:
        file_path = os.path.join('/tmp/exports', job_id, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found or expired'}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# CAD STANDARDS VOCABULARY API
# ============================================

@app.route('/api/vocabulary/disciplines')
def get_disciplines():
    """Get all discipline codes"""
    try:
        query = """
            SELECT discipline_id, code, full_name, description, sort_order
            FROM discipline_codes
            WHERE is_active = TRUE
            ORDER BY sort_order NULLS LAST, code
        """
        disciplines = execute_query(query)
        return jsonify({'disciplines': disciplines})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vocabulary/categories')
def get_categories():
    """Get all category codes with discipline info"""
    try:
        discipline_id = request.args.get('discipline_id')
        
        query = """
            SELECT c.category_id, c.code, c.full_name, c.description, c.sort_order,
                   d.code as discipline_code, d.full_name as discipline_name
            FROM category_codes c
            JOIN discipline_codes d ON c.discipline_id = d.discipline_id
            WHERE c.is_active = TRUE
        """
        
        params = None
        if discipline_id:
            query += " AND c.discipline_id = %s"
            params = (discipline_id,)
        
        query += " ORDER BY d.code, c.sort_order NULLS LAST, c.code"
        
        categories = execute_query(query, params)
        return jsonify({'categories': categories})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vocabulary/object-types')
def get_object_types():
    """Get all object type codes"""
    try:
        category_id = request.args.get('category_id')
        
        query = """
            SELECT t.type_id, t.code, t.full_name, t.description, t.database_table,
                   c.code as category_code, c.full_name as category_name,
                   d.code as discipline_code
            FROM object_type_codes t
            JOIN category_codes c ON t.category_id = c.category_id
            JOIN discipline_codes d ON c.discipline_id = d.discipline_id
            WHERE t.is_active = TRUE
        """
        
        params = None
        if category_id:
            query += " AND t.category_id = %s"
            params = (category_id,)
        
        query += " ORDER BY d.code, c.code, t.sort_order NULLS LAST, t.code"
        
        types = execute_query(query, params)
        return jsonify({'object_types': types})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vocabulary/phases')
def get_phases():
    """Get all phase codes"""
    try:
        query = """
            SELECT phase_id, code, full_name, description, color_rgb, sort_order
            FROM phase_codes
            WHERE is_active = TRUE
            ORDER BY sort_order NULLS LAST, code
        """
        phases = execute_query(query)
        return jsonify({'phases': phases})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vocabulary/geometries')
def get_geometries():
    """Get all geometry codes"""
    try:
        query = """
            SELECT geometry_id, code, full_name, description, dxf_entity_types, sort_order
            FROM geometry_codes
            WHERE is_active = TRUE
            ORDER BY sort_order NULLS LAST, code
        """
        geometries = execute_query(query)
        return jsonify({'geometries': geometries})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vocabulary/layer-patterns')
def get_layer_patterns():
    """Get standard layer patterns"""
    try:
        query = """
            SELECT p.pattern_id, p.full_layer_name, p.description,
                   p.database_table, p.example_attributes,
                   d.code as discipline_code, d.full_name as discipline_name,
                   c.code as category_code, c.full_name as category_name,
                   t.code as type_code, t.full_name as type_name,
                   ph.code as phase_code, ph.full_name as phase_name,
                   g.code as geometry_code, g.full_name as geometry_name
            FROM standard_layer_patterns p
            JOIN discipline_codes d ON p.discipline_id = d.discipline_id
            JOIN category_codes c ON p.category_id = c.category_id
            JOIN object_type_codes t ON p.type_id = t.type_id
            JOIN phase_codes ph ON p.phase_id = ph.phase_id
            JOIN geometry_codes g ON p.geometry_id = g.geometry_id
            WHERE p.is_active = TRUE
            ORDER BY p.full_layer_name
        """
        patterns = execute_query(query)
        return jsonify({'layer_patterns': patterns})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vocabulary/import-mappings')
def get_import_mappings():
    """Get import mapping patterns"""
    try:
        query = """
            SELECT m.mapping_id, m.client_name, m.source_pattern,
                   m.regex_pattern, m.extraction_rules, m.confidence_score,
                   d.code as discipline_code,
                   c.code as category_code,
                   t.code as type_code
            FROM import_mapping_patterns m
            LEFT JOIN discipline_codes d ON m.target_discipline_id = d.discipline_id
            LEFT JOIN category_codes c ON m.target_category_id = c.category_id
            LEFT JOIN object_type_codes t ON m.target_type_id = t.type_id
            WHERE m.is_active = TRUE
            ORDER BY m.confidence_score DESC, m.client_name, m.source_pattern
        """
        mappings = execute_query(query)
        return jsonify({'import_mappings': mappings})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vocabulary/layer-examples')
def get_layer_examples():
    """Generate comprehensive layer name examples for all object types"""
    try:
        from standards.export_layer_generator import ExportLayerGenerator
        
        generator = ExportLayerGenerator()
        examples = []
        
        # Get all object types with their relationships
        query = """
            SELECT t.type_id, t.code as type_code, t.full_name as type_name, 
                   t.description, t.database_table,
                   c.code as category_code, c.full_name as category_name,
                   d.code as discipline_code, d.full_name as discipline_name,
                   d.discipline_id
            FROM object_type_codes t
            JOIN category_codes c ON t.category_id = c.category_id
            JOIN discipline_codes d ON c.discipline_id = d.discipline_id
            WHERE t.is_active = TRUE
            ORDER BY d.sort_order, c.sort_order, t.sort_order
        """
        
        object_types = execute_query(query)
        
        # Get phases and geometries for variations
        phases = execute_query("""
            SELECT code, full_name, color_rgb FROM phase_codes 
            WHERE is_active = TRUE ORDER BY sort_order
        """)
        
        geometries = execute_query("""
            SELECT code, full_name, dxf_entity_types FROM geometry_codes 
            WHERE is_active = TRUE ORDER BY sort_order
        """)
        
        # Generate examples for each object type
        for obj_type in object_types:
            db_table = obj_type.get('database_table', '')
            type_code = obj_type.get('type_code', '')
            
            # Map object type to generator input format
            object_type_key = db_table if db_table else type_code.lower()
            
            # Generate variations
            for phase in phases[:3]:  # Show 3 phase examples
                for geom in geometries[:4]:  # Show 4 geometry examples
                    
                    # Build sample properties based on object type
                    properties = {
                        'phase': phase['code'].lower(),
                    }
                    
                    # Add object-specific properties
                    if 'util' in type_code.lower() or 'pipe' in type_code.lower():
                        properties.update({
                            'utility_type': 'storm',
                            'diameter': 12,
                            'material': 'pvc'
                        })
                    elif 'road' in type_code.lower() or 'align' in type_code.lower():
                        properties.update({
                            'alignment_type': 'road',
                            'name': 'MAIN'
                        })
                    elif 'bmp' in type_code.lower():
                        properties.update({
                            'bmp_type': 'bioretention',
                            'design_volume_cf': 500
                        })
                    elif 'tree' in type_code.lower():
                        properties.update({
                            'tree_status': 'existing',
                            'species': 'oak'
                        })
                    elif 'survey' in type_code.lower():
                        properties.update({
                            'point_type': 'monument'
                        })
                    elif 'surface' in type_code.lower() or 'grad' in type_code.lower():
                        properties.update({
                            'surface_type': 'existing_grade'
                        })
                    
                    # Try to generate layer name
                    try:
                        layer_name = generator.generate_layer_name(
                            object_type_key, 
                            properties, 
                            geom['code']
                        )
                        
                        if layer_name:
                            examples.append({
                                'layer_name': layer_name,
                                'object_type': obj_type['type_name'],
                                'object_code': type_code,
                                'discipline': obj_type['discipline_name'],
                                'discipline_code': obj_type['discipline_code'],
                                'category': obj_type['category_name'],
                                'category_code': obj_type['category_code'],
                                'phase': phase['full_name'],
                                'phase_code': phase['code'],
                                'phase_color': phase.get('color_rgb'),
                                'geometry': geom['full_name'],
                                'geometry_code': geom['code'],
                                'dxf_types': geom.get('dxf_entity_types', ''),
                                'properties': properties,
                                'database_table': db_table
                            })
                            
                            # Only generate one example per object type for first pass
                            break
                    except Exception as e:
                        continue
                
                # Got one example, move to next object type
                if examples and examples[-1]['object_code'] == type_code:
                    break
        
        return jsonify({
            'examples': examples,
            'count': len(examples)
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
