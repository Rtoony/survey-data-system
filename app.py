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
import openpyxl
from openpyxl.styles import Font, PatternFill
import zipfile
import tempfile
from weasyprint import HTML, CSS

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

@app.route('/standards-library')
def standards_library():
    """Standards Library landing page"""
    return render_template('standards_library.html')

@app.route('/project-operations')
def project_operations():
    """Project Operations landing page"""
    return render_template('project_operations.html')

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

@app.route('/project-standards-assignment')
def project_standards_assignment():
    """Project Standards Assignment page"""
    return render_template('project_standards_assignment.html')

@app.route('/project-compliance')
def project_compliance():
    """Project Compliance Dashboard page"""
    return render_template('project_compliance.html')

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

@app.route('/standards/import-manager')
def standards_import_manager():
    """Import Template Manager page"""
    return render_template('standards/import_manager.html')

@app.route('/standards/bulk-editor')
def standards_bulk_editor():
    """Bulk Standards Editor page"""
    return render_template('standards/bulk_editor.html')

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

@app.route('/data-manager/standard-notes')
def standard_notes_manager():
    """Render the Standard Notes Manager page"""
    return render_template('data_manager/standard_notes.html')

@app.route('/data-manager/materials')
def materials_manager():
    """Render the Materials Manager page"""
    return render_template('data_manager/materials.html')

@app.route('/data-manager/projects')
def projects_manager():
    """Render the Projects Manager page"""
    return render_template('data_manager/projects.html')

@app.route('/data-manager/drawings')
def drawings_manager():
    """Render the Drawings Manager page"""
    return render_template('data_manager/drawings.html')

@app.route('/data-manager/sheet-sets')
def sheet_sets_manager():
    """Render the Sheet Sets Manager page"""
    return render_template('data_manager/sheet_sets.html')

@app.route('/data-manager/hatches')
def hatches_manager():
    """Render the Hatches Manager page"""
    return render_template('data_manager/hatches.html')

@app.route('/data-manager/linetypes')
def linetypes_manager():
    """Render the Linetypes Manager page"""
    return render_template('data_manager/linetypes.html')

@app.route('/data-manager/text-styles')
def text_styles_manager():
    """Render the Text Styles Manager page"""
    return render_template('data_manager/text-styles.html')

@app.route('/data-manager/dimension-styles')
def dimension_styles_manager():
    """Render the Dimension Styles Manager page"""
    return render_template('data_manager/dimension-styles.html')

@app.route('/data-manager/drawing-materials')
def drawing_materials_manager():
    """Render the Drawing-Materials Relationship Manager page"""
    return render_template('data_manager/drawing_materials.html')

@app.route('/usage-dashboard')
def usage_dashboard():
    """Render the Usage Tracking Dashboard page"""
    return render_template('usage_dashboard.html')

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
# STANDARD NOTES MANAGER API ENDPOINTS
# ============================================================================

@app.route('/api/data-manager/standard-notes', methods=['GET'])
def get_standard_notes_manager():
    """Get all standard notes"""
    try:
        query = """
            SELECT note_id, note_title, note_text, note_category, discipline, 
                   tags, usage_frequency, created_at, updated_at
            FROM standard_notes
            ORDER BY note_category, note_title
        """
        notes = execute_query(query)
        return jsonify({'notes': notes})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/standard-notes', methods=['POST'])
def create_standard_note():
    """Create a new standard note"""
    try:
        data = request.get_json()
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO standard_notes 
                    (note_title, note_text, note_category, discipline, tags)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING note_id
                """, (
                    data.get('note_title'),
                    data.get('note_text'),
                    data.get('note_category'),
                    data.get('discipline'),
                    data.get('tags', [])
                ))
                note_id = cur.fetchone()[0]
                conn.commit()
        
        cache.clear()
        return jsonify({'note_id': note_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/standard-notes/<note_id>', methods=['PUT'])
def update_standard_note(note_id):
    """Update an existing standard note"""
    try:
        data = request.get_json()
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE standard_notes
                    SET note_title = %s, note_text = %s, note_category = %s, 
                        discipline = %s, tags = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE note_id = %s
                """, (
                    data.get('note_title'),
                    data.get('note_text'),
                    data.get('note_category'),
                    data.get('discipline'),
                    data.get('tags', []),
                    note_id
                ))
                conn.commit()
        
        cache.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/standard-notes/<note_id>', methods=['DELETE'])
def delete_standard_note(note_id):
    """Delete a standard note"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM standard_notes WHERE note_id = %s", (note_id,))
                conn.commit()
        
        cache.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# MATERIALS MANAGER API ENDPOINTS
# ============================================================================

@app.route('/api/data-manager/materials', methods=['GET'])
def get_materials():
    """Get all materials"""
    try:
        query = """
            SELECT material_id, material_name, material_type, description, 
                   specifications, manufacturer, product_code, cost_per_unit,
                   unit_of_measure, environmental_rating, usage_frequency
            FROM material_standards
            ORDER BY material_type, material_name
        """
        materials = execute_query(query)
        return jsonify({'materials': materials})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/materials', methods=['POST'])
def create_material():
    """Create a new material"""
    try:
        data = request.get_json()
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO material_standards 
                    (material_name, material_type, description, specifications, manufacturer,
                     product_code, cost_per_unit, unit_of_measure, environmental_rating)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING material_id
                """, (
                    data.get('material_name'),
                    data.get('material_type'),
                    data.get('description'),
                    data.get('specifications'),
                    data.get('manufacturer'),
                    data.get('product_code'),
                    data.get('cost_per_unit'),
                    data.get('unit_of_measure'),
                    data.get('environmental_rating')
                ))
                material_id = cur.fetchone()[0]
                conn.commit()
        
        cache.clear()
        return jsonify({'material_id': material_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/materials/<material_id>', methods=['PUT'])
def update_material(material_id):
    """Update an existing material"""
    try:
        data = request.get_json()
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE material_standards
                    SET material_name = %s, material_type = %s, description = %s,
                        specifications = %s, manufacturer = %s, product_code = %s,
                        cost_per_unit = %s, unit_of_measure = %s, environmental_rating = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE material_id = %s
                """, (
                    data.get('material_name'),
                    data.get('material_type'),
                    data.get('description'),
                    data.get('specifications'),
                    data.get('manufacturer'),
                    data.get('product_code'),
                    data.get('cost_per_unit'),
                    data.get('unit_of_measure'),
                    data.get('environmental_rating'),
                    material_id
                ))
                conn.commit()
        
        cache.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/materials/<material_id>', methods=['DELETE'])
def delete_material(material_id):
    """Delete a material"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM material_standards WHERE material_id = %s", (material_id,))
                conn.commit()
        
        cache.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# DRAWING-MATERIALS RELATIONSHIP API ENDPOINTS
# ============================================================================

@app.route('/api/data-manager/drawing-materials/<drawing_id>', methods=['GET'])
def get_drawing_materials(drawing_id):
    """Get all materials assigned to a specific drawing"""
    try:
        query = """
            SELECT 
                dm.assignment_id,
                dm.drawing_id,
                dm.material_id,
                dm.quantity,
                dm.unit_of_measure,
                dm.usage_context,
                dm.notes,
                dm.created_at,
                m.material_name,
                m.material_type,
                m.manufacturer,
                m.cost_per_unit,
                m.unit_of_measure as material_default_unit
            FROM drawing_materials dm
            JOIN material_standards m ON dm.material_id = m.material_id
            WHERE dm.drawing_id = %s
            ORDER BY m.material_name
        """
        materials = execute_query(query, (drawing_id,))
        return jsonify({'materials': materials})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/drawing-materials', methods=['POST'])
def add_material_to_drawing():
    """Add a material to a drawing"""
    try:
        data = request.get_json()
        
        drawing_id = data.get('drawing_id')
        material_id = data.get('material_id')
        quantity = data.get('quantity')
        unit_of_measure = data.get('unit_of_measure')
        usage_context = data.get('usage_context')
        notes = data.get('notes')
        
        if not drawing_id or not material_id:
            return jsonify({'error': 'drawing_id and material_id are required'}), 400
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO drawing_materials 
                    (drawing_id, material_id, quantity, unit_of_measure, usage_context, notes)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING assignment_id
                """, (
                    drawing_id,
                    material_id,
                    quantity,
                    unit_of_measure,
                    usage_context,
                    notes
                ))
                assignment_id = cur.fetchone()[0]
                conn.commit()
        
        cache.clear()
        return jsonify({'assignment_id': str(assignment_id)}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/drawing-materials/<assignment_id>', methods=['DELETE'])
def remove_material_from_drawing(assignment_id):
    """Remove a material assignment from a drawing"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM drawing_materials WHERE assignment_id = %s", (assignment_id,))
                conn.commit()
        
        cache.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# PROJECT STANDARDS ASSIGNMENT API ENDPOINTS
# ============================================================================

@app.route('/api/project-standards/<project_id>', methods=['GET'])
def get_project_standards(project_id):
    """Get all assigned standards for a project grouped by type"""
    try:
        query = """
            SELECT 
                psa.assignment_id,
                psa.project_id,
                psa.standard_type,
                psa.standard_id,
                psa.is_required,
                psa.notes,
                psa.assigned_date,
                CASE 
                    WHEN psa.standard_type = 'layer' THEN l.layer_name
                    WHEN psa.standard_type = 'block' THEN b.block_name
                    WHEN psa.standard_type = 'hatch' THEN hp.pattern_name
                    WHEN psa.standard_type = 'linetype' THEN lt.linetype_name
                    WHEN psa.standard_type = 'text_style' THEN ts.style_name
                    WHEN psa.standard_type = 'dimension_style' THEN ds.style_name
                    WHEN psa.standard_type = 'material' THEN ms.material_name
                    WHEN psa.standard_type = 'detail' THEN d.detail_name
                    WHEN psa.standard_type = 'standard_note' THEN LEFT(sn.note_text, 50)
                END as standard_name,
                CASE 
                    WHEN psa.standard_type = 'layer' THEN l.description
                    WHEN psa.standard_type = 'block' THEN b.description
                    WHEN psa.standard_type = 'hatch' THEN hp.description
                    WHEN psa.standard_type = 'linetype' THEN lt.description
                    WHEN psa.standard_type = 'text_style' THEN ts.description
                    WHEN psa.standard_type = 'dimension_style' THEN ds.description
                    WHEN psa.standard_type = 'material' THEN ms.description
                    WHEN psa.standard_type = 'detail' THEN d.description
                    WHEN psa.standard_type = 'standard_note' THEN sn.category
                END as standard_description
            FROM project_standard_assignments psa
            LEFT JOIN layers l ON psa.standard_type = 'layer' AND psa.standard_id = l.layer_id
            LEFT JOIN blocks b ON psa.standard_type = 'block' AND psa.standard_id = b.block_id
            LEFT JOIN hatch_patterns hp ON psa.standard_type = 'hatch' AND psa.standard_id = hp.hatch_id
            LEFT JOIN linetypes lt ON psa.standard_type = 'linetype' AND psa.standard_id = lt.linetype_id
            LEFT JOIN text_styles ts ON psa.standard_type = 'text_style' AND psa.standard_id = ts.style_id
            LEFT JOIN dimension_styles ds ON psa.standard_type = 'dimension_style' AND psa.standard_id = ds.dimension_style_id
            LEFT JOIN material_standards ms ON psa.standard_type = 'material' AND psa.standard_id = ms.material_id
            LEFT JOIN details d ON psa.standard_type = 'detail' AND psa.standard_id = d.detail_id
            LEFT JOIN standard_notes sn ON psa.standard_type = 'standard_note' AND psa.standard_id = sn.note_id
            WHERE psa.project_id = %s
            ORDER BY psa.standard_type, standard_name
        """
        standards = execute_query(query, (project_id,))
        
        grouped = {}
        for standard in standards:
            std_type = standard['standard_type']
            if std_type not in grouped:
                grouped[std_type] = []
            grouped[std_type].append(standard)
        
        return jsonify({'standards': grouped})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-standards', methods=['POST'])
def add_project_standard():
    """Add a standard to a project"""
    try:
        data = request.get_json()
        
        project_id = data.get('project_id')
        standard_type = data.get('standard_type')
        standard_id = data.get('standard_id')
        is_required = data.get('is_required', False)
        notes = data.get('notes')
        
        if not project_id or not standard_type or not standard_id:
            return jsonify({'error': 'project_id, standard_type, and standard_id are required'}), 400
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO project_standard_assignments 
                    (project_id, standard_type, standard_id, is_required, notes)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING assignment_id
                """, (
                    project_id,
                    standard_type,
                    standard_id,
                    is_required,
                    notes
                ))
                assignment_id = cur.fetchone()[0]
                conn.commit()
        
        cache.clear()
        return jsonify({'assignment_id': assignment_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-standards/<assignment_id>', methods=['DELETE'])
def remove_project_standard(assignment_id):
    """Remove a standard assignment from a project"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM project_standard_assignments WHERE assignment_id = %s", (assignment_id,))
                conn.commit()
        
        cache.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/standards-by-type/<standard_type>', methods=['GET'])
def get_standards_by_type(standard_type):
    """Get all available standards of a specific type"""
    try:
        type_mapping = {
            'layer': ('layers', 'layer_id', 'layer_name', 'description'),
            'block': ('blocks', 'block_id', 'block_name', 'description'),
            'hatch': ('hatch_patterns', 'hatch_id', 'pattern_name', 'description'),
            'linetype': ('linetypes', 'linetype_id', 'linetype_name', 'description'),
            'text_style': ('text_styles', 'style_id', 'style_name', 'description'),
            'dimension_style': ('dimension_styles', 'dimension_style_id', 'style_name', 'description'),
            'material': ('material_standards', 'material_id', 'material_name', 'description'),
            'detail': ('details', 'detail_id', 'detail_name', 'description'),
            'standard_note': ('standard_notes', 'note_id', 'note_text', 'category')
        }
        
        if standard_type not in type_mapping:
            return jsonify({'error': 'Invalid standard type'}), 400
        
        table, id_col, name_col, desc_col = type_mapping[standard_type]
        
        if standard_type == 'standard_note':
            query = f"""
                SELECT {id_col} as id, 
                       LEFT({name_col}, 100) as name, 
                       {desc_col} as description
                FROM {table}
                ORDER BY {name_col}
                LIMIT 500
            """
        else:
            query = f"""
                SELECT {id_col} as id, {name_col} as name, {desc_col} as description
                FROM {table}
                ORDER BY {name_col}
                LIMIT 500
            """
        
        standards = execute_query(query)
        return jsonify({'standards': standards})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-compliance/<project_id>', methods=['GET'])
def get_project_compliance(project_id):
    """Get compliance summary for a project"""
    try:
        type_mapping = {
            'layer': ('layers', 'layer_id', 'layer_name'),
            'block': ('blocks', 'block_id', 'block_name'),
            'hatch': ('hatch_patterns', 'hatch_id', 'pattern_name'),
            'linetype': ('linetypes', 'linetype_id', 'linetype_name'),
            'text_style': ('text_styles', 'style_id', 'style_name'),
            'dimension_style': ('dimension_styles', 'dimension_style_id', 'style_name'),
            'material': ('material_standards', 'material_id', 'material_name'),
            'detail': ('details', 'detail_id', 'detail_name'),
            'standard_note': ('standard_notes', 'note_id', 'note_title')
        }
        
        assigned_query = """
            SELECT standard_type, COUNT(*) as count
            FROM project_standard_assignments
            WHERE project_id = %s
            GROUP BY standard_type
        """
        assigned_by_type = execute_query(assigned_query, (project_id,))
        
        deviations_query = """
            SELECT 
                pso.override_id,
                pso.project_id,
                pso.drawing_id,
                pso.standard_type,
                pso.standard_id,
                pso.override_reason,
                pso.created_date,
                pso.created_by,
                pso.notes,
                d.drawing_name,
                'Standard ID: ' || pso.standard_id::text as standard_name
            FROM project_standard_overrides pso
            LEFT JOIN drawings d ON pso.drawing_id = d.drawing_id
            WHERE pso.project_id = %s
            ORDER BY pso.created_date DESC
        """
        deviations = execute_query(deviations_query, (project_id,))
        
        deviations_by_type_query = """
            SELECT standard_type, COUNT(*) as count
            FROM project_standard_overrides
            WHERE project_id = %s
            GROUP BY standard_type
        """
        deviations_by_type = execute_query(deviations_by_type_query, (project_id,))
        
        deviation_counts = {item['standard_type']: item['count'] for item in deviations_by_type}
        
        total_assigned = sum(item['count'] for item in assigned_by_type)
        total_deviations = len(deviations)
        total_used = total_assigned
        
        compliance_percentage = 0
        if total_assigned > 0:
            compliance_percentage = ((total_assigned - total_deviations) / total_assigned) * 100
        
        by_category = []
        for item in assigned_by_type:
            standard_type = item['standard_type']
            assigned_count = item['count']
            deviations_count = deviation_counts.get(standard_type, 0)
            
            by_category.append({
                'standard_type': standard_type,
                'assigned': assigned_count,
                'used': assigned_count,
                'deviations': deviations_count
            })
        
        return jsonify({
            'total_assigned': total_assigned,
            'total_used': total_used,
            'deviations_count': total_deviations,
            'compliance_percentage': compliance_percentage,
            'by_category': by_category,
            'deviations': deviations
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# SHEET SETS MANAGER API ENDPOINTS
# ============================================================================

@app.route('/api/data-manager/sheet-sets', methods=['GET'])
def get_data_manager_sheet_sets():
    """Get all sheet sets"""
    try:
        query = """
            SELECT set_id, project_id, set_name, set_number, phase, discipline,
                   issue_date, status, recipient, transmittal_notes, is_active,
                   usage_frequency, created_at, updated_at
            FROM sheet_sets
            WHERE is_active = true
            ORDER BY created_at DESC
        """
        sheet_sets = execute_query(query)
        return jsonify({'sheet_sets': sheet_sets})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/sheet-sets', methods=['POST'])
def create_data_manager_sheet_set():
    """Create a new sheet set"""
    try:
        data = request.get_json()
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO sheet_sets 
                    (project_id, set_name, set_number, phase, discipline,
                     issue_date, status, recipient, transmittal_notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING set_id
                """, (
                    data.get('project_id'),
                    data.get('set_name'),
                    data.get('set_number'),
                    data.get('phase'),
                    data.get('discipline'),
                    data.get('issue_date'),
                    data.get('status', 'draft'),
                    data.get('recipient'),
                    data.get('transmittal_notes')
                ))
                set_id = cur.fetchone()[0]
                conn.commit()
        
        cache.clear()
        return jsonify({'set_id': set_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/sheet-sets/<set_id>', methods=['PUT'])
def update_data_manager_sheet_set(set_id):
    """Update an existing sheet set"""
    try:
        data = request.get_json()
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE sheet_sets
                    SET project_id = %s, set_name = %s, set_number = %s, phase = %s,
                        discipline = %s, issue_date = %s, status = %s, recipient = %s,
                        transmittal_notes = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE set_id = %s
                """, (
                    data.get('project_id'),
                    data.get('set_name'),
                    data.get('set_number'),
                    data.get('phase'),
                    data.get('discipline'),
                    data.get('issue_date'),
                    data.get('status'),
                    data.get('recipient'),
                    data.get('transmittal_notes'),
                    set_id
                ))
                conn.commit()
        
        cache.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/sheet-sets/<set_id>', methods=['DELETE'])
def delete_data_manager_sheet_set(set_id):
    """Delete a sheet set"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM sheet_sets WHERE set_id = %s", (set_id,))
                conn.commit()
        
        cache.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# HATCH PATTERNS MANAGER API ENDPOINTS
# ============================================================================

@app.route('/api/data-manager/hatches', methods=['GET'])
def get_hatches():
    """Get all hatch patterns"""
    try:
        query = """
            SELECT hatch_id, pattern_name, pattern_type, pattern_definition,
                   description, usage_context
            FROM hatch_patterns
            ORDER BY pattern_type, pattern_name
        """
        hatches = execute_query(query)
        return jsonify({'hatches': hatches})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/hatches', methods=['POST'])
def create_hatch():
    """Create a new hatch pattern"""
    try:
        data = request.get_json()
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO hatch_patterns 
                    (pattern_name, pattern_type, pattern_definition, description, usage_context)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING hatch_id
                """, (
                    data.get('pattern_name'),
                    data.get('pattern_type'),
                    data.get('pattern_definition'),
                    data.get('description'),
                    data.get('usage_context')
                ))
                hatch_id = cur.fetchone()[0]
                conn.commit()
        
        cache.clear()
        return jsonify({'hatch_id': hatch_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/hatches/<hatch_id>', methods=['PUT'])
def update_hatch(hatch_id):
    """Update an existing hatch pattern"""
    try:
        data = request.get_json()
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE hatch_patterns
                    SET pattern_name = %s, pattern_type = %s, pattern_definition = %s,
                        description = %s, usage_context = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE hatch_id = %s
                """, (
                    data.get('pattern_name'),
                    data.get('pattern_type'),
                    data.get('pattern_definition'),
                    data.get('description'),
                    data.get('usage_context'),
                    hatch_id
                ))
                conn.commit()
        
        cache.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/hatches/<hatch_id>', methods=['DELETE'])
def delete_hatch(hatch_id):
    """Delete a hatch pattern"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM hatch_patterns WHERE hatch_id = %s", (hatch_id,))
                conn.commit()
        
        cache.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# LINETYPES MANAGER API ENDPOINTS
# ============================================================================

@app.route('/api/data-manager/linetypes', methods=['GET'])
def get_linetypes():
    """Get all linetypes"""
    try:
        query = """
            SELECT linetype_id, linetype_name, pattern_definition,
                   description, usage_context
            FROM linetypes
            ORDER BY linetype_name
        """
        linetypes = execute_query(query)
        return jsonify({'linetypes': linetypes})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/linetypes', methods=['POST'])
def create_linetype():
    """Create a new linetype"""
    try:
        data = request.get_json()
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO linetypes 
                    (linetype_name, pattern_definition, description, usage_context)
                    VALUES (%s, %s, %s, %s)
                    RETURNING linetype_id
                """, (
                    data.get('linetype_name'),
                    data.get('pattern_definition'),
                    data.get('description'),
                    data.get('usage_context')
                ))
                linetype_id = cur.fetchone()[0]
                conn.commit()
        
        cache.clear()
        return jsonify({'linetype_id': linetype_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/linetypes/<linetype_id>', methods=['PUT'])
def update_linetype(linetype_id):
    """Update an existing linetype"""
    try:
        data = request.get_json()
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE linetypes
                    SET linetype_name = %s, pattern_definition = %s,
                        description = %s, usage_context = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE linetype_id = %s
                """, (
                    data.get('linetype_name'),
                    data.get('pattern_definition'),
                    data.get('description'),
                    data.get('usage_context'),
                    linetype_id
                ))
                conn.commit()
        
        cache.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/linetypes/<linetype_id>', methods=['DELETE'])
def delete_linetype(linetype_id):
    """Delete a linetype"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM linetypes WHERE linetype_id = %s", (linetype_id,))
                conn.commit()
        
        cache.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# TEXT STYLES MANAGER API ENDPOINTS
# ============================================================================

@app.route('/api/data-manager/text-styles', methods=['GET'])
def get_text_styles():
    """Get all text styles"""
    try:
        query = """
            SELECT style_id, style_name, font_name, height, width_factor,
                   oblique_angle, description, usage_context, discipline
            FROM text_styles
            ORDER BY discipline, style_name
        """
        text_styles = execute_query(query)
        return jsonify({'text_styles': text_styles})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/text-styles', methods=['POST'])
def create_text_style():
    """Create a new text style"""
    try:
        data = request.get_json()
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO text_styles 
                    (style_name, font_name, height, width_factor, oblique_angle,
                     description, usage_context, discipline)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING style_id
                """, (
                    data.get('style_name'),
                    data.get('font_name'),
                    data.get('height'),
                    data.get('width_factor'),
                    data.get('oblique_angle'),
                    data.get('description'),
                    data.get('usage_context'),
                    data.get('discipline')
                ))
                style_id = cur.fetchone()[0]
                conn.commit()
        
        cache.clear()
        return jsonify({'style_id': style_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/text-styles/<style_id>', methods=['PUT'])
def update_text_style(style_id):
    """Update an existing text style"""
    try:
        data = request.get_json()
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE text_styles
                    SET style_name = %s, font_name = %s, height = %s,
                        width_factor = %s, oblique_angle = %s, description = %s,
                        usage_context = %s, discipline = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE style_id = %s
                """, (
                    data.get('style_name'),
                    data.get('font_name'),
                    data.get('height'),
                    data.get('width_factor'),
                    data.get('oblique_angle'),
                    data.get('description'),
                    data.get('usage_context'),
                    data.get('discipline'),
                    style_id
                ))
                conn.commit()
        
        cache.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/text-styles/<style_id>', methods=['DELETE'])
def delete_text_style(style_id):
    """Delete a text style"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM text_styles WHERE style_id = %s", (style_id,))
                conn.commit()
        
        cache.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# DIMENSION STYLES MANAGER API ENDPOINTS
# ============================================================================

@app.route('/api/data-manager/dimension-styles', methods=['GET'])
def get_dimension_styles():
    """Get all dimension styles"""
    try:
        query = """
            SELECT dimension_style_id, style_name, text_height, arrow_size,
                   extension_line_offset, dimension_line_color, text_color, description
            FROM dimension_styles
            ORDER BY style_name
        """
        dimension_styles = execute_query(query)
        return jsonify({'dimension_styles': dimension_styles})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/dimension-styles', methods=['POST'])
def create_dimension_style():
    """Create a new dimension style"""
    try:
        data = request.get_json()
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO dimension_styles 
                    (style_name, text_height, arrow_size, extension_line_offset,
                     dimension_line_color, text_color, description)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING dimension_style_id
                """, (
                    data.get('style_name'),
                    data.get('text_height'),
                    data.get('arrow_size'),
                    data.get('extension_line_offset'),
                    data.get('dimension_line_color'),
                    data.get('text_color'),
                    data.get('description')
                ))
                dimension_style_id = cur.fetchone()[0]
                conn.commit()
        
        cache.clear()
        return jsonify({'dimension_style_id': dimension_style_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/dimension-styles/<dimension_style_id>', methods=['PUT'])
def update_dimension_style(dimension_style_id):
    """Update an existing dimension style"""
    try:
        data = request.get_json()
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE dimension_styles
                    SET style_name = %s, text_height = %s, arrow_size = %s,
                        extension_line_offset = %s, dimension_line_color = %s,
                        text_color = %s, description = %s
                    WHERE dimension_style_id = %s
                """, (
                    data.get('style_name'),
                    data.get('text_height'),
                    data.get('arrow_size'),
                    data.get('extension_line_offset'),
                    data.get('dimension_line_color'),
                    data.get('text_color'),
                    data.get('description'),
                    dimension_style_id
                ))
                conn.commit()
        
        cache.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/dimension-styles/<dimension_style_id>', methods=['DELETE'])
def delete_dimension_style(dimension_style_id):
    """Delete a dimension style"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM dimension_styles WHERE dimension_style_id = %s", (dimension_style_id,))
                conn.commit()
        
        cache.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# USAGE TRACKING DASHBOARD API ENDPOINTS
# ============================================================================

@app.route('/api/usage/summary')
def get_usage_summary():
    """Get summary usage statistics"""
    try:
        query = """
            WITH stats AS (
                SELECT 
                    (SELECT COUNT(*) FROM drawings) as total_drawings,
                    (SELECT COUNT(DISTINCT layer_id) FROM drawing_layer_usage) as unique_layers,
                    (SELECT SUM(block_count) FROM drawings) as total_block_instances,
                    (SELECT ROUND(AVG(entity_count)) FROM drawings) as avg_entities_per_drawing
            )
            SELECT * FROM stats
        """
        result = execute_query(query)
        return jsonify(result[0] if result else {})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/usage/top-drawings')
def get_top_drawings():
    """Get most accessed drawings"""
    try:
        query = """
            SELECT 
                drawing_id,
                drawing_name,
                drawing_number,
                entity_count,
                layer_count,
                block_count,
                last_opened_at,
                last_modified_at
            FROM drawings
            WHERE last_opened_at IS NOT NULL
            ORDER BY last_opened_at DESC
            LIMIT 10
        """
        drawings = execute_query(query)
        return jsonify({'drawings': drawings})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/usage/top-layers')
def get_top_layers():
    """Get most used layers"""
    try:
        query = """
            SELECT 
                l.layer_name,
                ls.category,
                COUNT(DISTINCT dlu.drawing_id) as drawing_count,
                SUM(dlu.entity_count) as total_entities
            FROM drawing_layer_usage dlu
            LEFT JOIN layers l ON dlu.layer_id = l.layer_id
            LEFT JOIN layer_standards ls ON l.layer_standard_id = ls.layer_id
            WHERE l.layer_name IS NOT NULL
            GROUP BY l.layer_name, ls.category
            ORDER BY total_entities DESC
            LIMIT 10
        """
        layers = execute_query(query)
        return jsonify({'layers': layers})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/usage/top-notes')
def get_top_notes():
    """Get most used standard notes"""
    try:
        query = """
            SELECT 
                note_id,
                note_title,
                note_category,
                usage_frequency
            FROM standard_notes
            WHERE usage_frequency > 0
            ORDER BY usage_frequency DESC
            LIMIT 10
        """
        notes = execute_query(query)
        return jsonify({'notes': notes})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/usage/top-blocks')
def get_top_blocks():
    """Get most used blocks"""
    try:
        query = """
            SELECT 
                block_name,
                category,
                usage_frequency
            FROM block_definitions
            WHERE usage_frequency > 0
            ORDER BY usage_frequency DESC
            LIMIT 10
        """
        blocks = execute_query(query)
        return jsonify({'blocks': blocks})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/usage/recent-activity')
def get_usage_recent_activity():
    """Get recent drawing activity"""
    try:
        query = """
            SELECT 
                drawing_id,
                drawing_name,
                drawing_number,
                discipline,
                entity_count,
                last_modified_at,
                last_opened_at
            FROM drawings
            WHERE last_modified_at IS NOT NULL OR last_opened_at IS NOT NULL
            ORDER BY GREATEST(
                COALESCE(last_modified_at, '1970-01-01'::timestamp),
                COALESCE(last_opened_at, '1970-01-01'::timestamp)
            ) DESC
            LIMIT 20
        """
        activity = execute_query(query)
        return jsonify({'activity': activity})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# STANDARDS MAPPING DASHBOARD & API ENDPOINTS
# ============================================================================

@app.route('/standards-mapping-dashboard')
def standards_mapping_dashboard():
    """Render the Standards Mapping Dashboard page"""
    return render_template('standards_mapping_dashboard.html')

@app.route('/api/standards-mapping/stats')
def get_mapping_stats():
    """Get counts for all mapping types"""
    try:
        stats = {}
        
        stats['block_mappings'] = execute_query("SELECT COUNT(*) as count FROM block_name_mappings")[0]['count']
        stats['detail_mappings'] = execute_query("SELECT COUNT(*) as count FROM detail_name_mappings")[0]['count']
        stats['hatch_mappings'] = execute_query("SELECT COUNT(*) as count FROM hatch_pattern_name_mappings")[0]['count']
        stats['material_mappings'] = execute_query("SELECT COUNT(*) as count FROM material_name_mappings")[0]['count']
        stats['note_mappings'] = execute_query("SELECT COUNT(*) as count FROM note_name_mappings")[0]['count']
        
        stats['keynote_block_relationships'] = execute_query("SELECT COUNT(*) as count FROM project_keynote_block_mappings")[0]['count']
        stats['keynote_detail_relationships'] = execute_query("SELECT COUNT(*) as count FROM project_keynote_detail_mappings")[0]['count']
        stats['hatch_material_relationships'] = execute_query("SELECT COUNT(*) as count FROM project_hatch_material_mappings")[0]['count']
        stats['detail_material_relationships'] = execute_query("SELECT COUNT(*) as count FROM project_detail_material_mappings")[0]['count']
        stats['block_spec_relationships'] = execute_query("SELECT COUNT(*) as count FROM project_block_specification_mappings")[0]['count']
        stats['cross_references'] = execute_query("SELECT COUNT(*) as count FROM project_element_cross_references")[0]['count']
        
        stats['total_relationships'] = (
            stats['keynote_block_relationships'] + 
            stats['keynote_detail_relationships'] +
            stats['hatch_material_relationships'] +
            stats['detail_material_relationships'] +
            stats['block_spec_relationships'] +
            stats['cross_references']
        )
        
        return jsonify({'stats': stats})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/standards-mapping/block-mappings')
def get_block_name_mappings():
    """Get all block name mappings"""
    try:
        query = """
            SELECT mapping_id, canonical_name, dxf_alias, description,
                   import_direction, export_direction, client_id,
                   confidence_score, is_active
            FROM block_name_mappings
            WHERE is_active = TRUE
            ORDER BY canonical_name
        """
        mappings = execute_query(query)
        return jsonify({'mappings': mappings})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/standards-mapping/detail-mappings')
def get_detail_name_mappings():
    """Get all detail name mappings"""
    try:
        query = """
            SELECT mapping_id, canonical_name, dxf_alias, description,
                   import_direction, export_direction, client_id,
                   confidence_score, is_active
            FROM detail_name_mappings
            WHERE is_active = TRUE
            ORDER BY canonical_name
        """
        mappings = execute_query(query)
        return jsonify({'mappings': mappings})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/standards-mapping/hatch-mappings')
def get_hatch_name_mappings():
    """Get all hatch pattern name mappings"""
    try:
        query = """
            SELECT mapping_id, canonical_name, dxf_alias, description,
                   import_direction, export_direction, client_id,
                   confidence_score, is_active
            FROM hatch_pattern_name_mappings
            WHERE is_active = TRUE
            ORDER BY canonical_name
        """
        mappings = execute_query(query)
        return jsonify({'mappings': mappings})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/standards-mapping/material-mappings')
def get_material_name_mappings():
    """Get all material name mappings"""
    try:
        query = """
            SELECT mapping_id, canonical_name, dxf_alias, description,
                   import_direction, export_direction, client_id,
                   confidence_score, is_active
            FROM material_name_mappings
            WHERE is_active = TRUE
            ORDER BY canonical_name
        """
        mappings = execute_query(query)
        return jsonify({'mappings': mappings})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/standards-mapping/note-mappings')
def get_note_name_mappings():
    """Get all note name mappings"""
    try:
        query = """
            SELECT mapping_id, canonical_name, dxf_alias, description,
                   import_direction, export_direction, client_id,
                   confidence_score, is_active
            FROM note_name_mappings
            WHERE is_active = TRUE
            ORDER BY canonical_name
        """
        mappings = execute_query(query)
        return jsonify({'mappings': mappings})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# BLOCK NAME MAPPINGS CRUD MANAGER
# ============================================================================

@app.route('/data-manager/block-mappings')
def block_mappings_manager():
    """Render the Block Name Mappings Manager page"""
    return render_template('data_manager/block_mappings.html')

@app.route('/api/data-manager/block-mappings', methods=['GET'])
def get_block_mappings_crud():
    """Get all block mappings for CRUD interface"""
    try:
        query = """
            SELECT * FROM block_name_mappings
            ORDER BY canonical_name
        """
        mappings = execute_query(query)
        return jsonify({'mappings': mappings})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/block-mappings', methods=['POST'])
def create_block_mapping():
    """Create a new block mapping"""
    try:
        data = request.get_json()
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO block_name_mappings 
                    (canonical_name, dxf_alias, description, import_direction, 
                     export_direction, client_id, confidence_score)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING mapping_id
                """, (
                    data.get('canonical_name'),
                    data.get('dxf_alias'),
                    data.get('description'),
                    data.get('import_direction', True),
                    data.get('export_direction', True),
                    data.get('client_id'),
                    data.get('confidence_score', 1.0)
                ))
                mapping_id = cur.fetchone()[0]
                conn.commit()
        return jsonify({'mapping_id': mapping_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/block-mappings/<mapping_id>', methods=['PUT'])
def update_block_mapping(mapping_id):
    """Update an existing block mapping"""
    try:
        data = request.get_json()
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE block_name_mappings
                    SET canonical_name = %s, dxf_alias = %s, description = %s,
                        import_direction = %s, export_direction = %s, 
                        client_id = %s, confidence_score = %s
                    WHERE mapping_id = %s
                """, (
                    data.get('canonical_name'),
                    data.get('dxf_alias'),
                    data.get('description'),
                    data.get('import_direction', True),
                    data.get('export_direction', True),
                    data.get('client_id'),
                    data.get('confidence_score', 1.0),
                    mapping_id
                ))
                conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/block-mappings/<mapping_id>', methods=['DELETE'])
def delete_block_mapping(mapping_id):
    """Delete a block mapping"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM block_name_mappings WHERE mapping_id = %s", (mapping_id,))
                conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# DETAIL NAME MAPPINGS CRUD MANAGER
# ============================================================================

@app.route('/data-manager/detail-mappings')
def detail_mappings_manager():
    """Render the Detail Name Mappings Manager page"""
    return render_template('data_manager/detail_mappings.html')

@app.route('/api/data-manager/detail-mappings', methods=['GET'])
def get_detail_mappings_crud():
    """Get all detail mappings for CRUD interface"""
    try:
        query = """
            SELECT * FROM detail_name_mappings
            ORDER BY canonical_name
        """
        mappings = execute_query(query)
        return jsonify({'mappings': mappings})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/detail-mappings', methods=['POST'])
def create_detail_mapping():
    """Create a new detail mapping"""
    try:
        data = request.get_json()
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO detail_name_mappings 
                    (canonical_name, dxf_alias, description, import_direction, 
                     export_direction, client_id, confidence_score)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING mapping_id
                """, (
                    data.get('canonical_name'),
                    data.get('dxf_alias'),
                    data.get('description'),
                    data.get('import_direction', True),
                    data.get('export_direction', True),
                    data.get('client_id'),
                    data.get('confidence_score', 1.0)
                ))
                mapping_id = cur.fetchone()[0]
                conn.commit()
        return jsonify({'mapping_id': mapping_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/detail-mappings/<mapping_id>', methods=['PUT'])
def update_detail_mapping(mapping_id):
    """Update an existing detail mapping"""
    try:
        data = request.get_json()
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE detail_name_mappings
                    SET canonical_name = %s, dxf_alias = %s, description = %s,
                        import_direction = %s, export_direction = %s, 
                        client_id = %s, confidence_score = %s
                    WHERE mapping_id = %s
                """, (
                    data.get('canonical_name'),
                    data.get('dxf_alias'),
                    data.get('description'),
                    data.get('import_direction', True),
                    data.get('export_direction', True),
                    data.get('client_id'),
                    data.get('confidence_score', 1.0),
                    mapping_id
                ))
                conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/detail-mappings/<mapping_id>', methods=['DELETE'])
def delete_detail_mapping(mapping_id):
    """Delete a detail mapping"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM detail_name_mappings WHERE mapping_id = %s", (mapping_id,))
                conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# HATCH PATTERN NAME MAPPINGS CRUD MANAGER
# ============================================================================

@app.route('/data-manager/hatch-mappings')
def hatch_mappings_manager():
    """Render the Hatch Pattern Name Mappings Manager page"""
    return render_template('data_manager/hatch_mappings.html')

@app.route('/api/data-manager/hatch-mappings', methods=['GET'])
def get_hatch_mappings_crud():
    """Get all hatch pattern mappings for CRUD interface"""
    try:
        query = """
            SELECT * FROM hatch_pattern_name_mappings
            ORDER BY canonical_name
        """
        mappings = execute_query(query)
        return jsonify({'mappings': mappings})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/hatch-mappings', methods=['POST'])
def create_hatch_mapping():
    """Create a new hatch pattern mapping"""
    try:
        data = request.get_json()
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO hatch_pattern_name_mappings 
                    (canonical_name, dxf_alias, description, import_direction, 
                     export_direction, client_id, confidence_score)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING mapping_id
                """, (
                    data.get('canonical_name'),
                    data.get('dxf_alias'),
                    data.get('description'),
                    data.get('import_direction', True),
                    data.get('export_direction', True),
                    data.get('client_id'),
                    data.get('confidence_score', 1.0)
                ))
                mapping_id = cur.fetchone()[0]
                conn.commit()
        return jsonify({'mapping_id': mapping_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/hatch-mappings/<mapping_id>', methods=['PUT'])
def update_hatch_mapping(mapping_id):
    """Update an existing hatch pattern mapping"""
    try:
        data = request.get_json()
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE hatch_pattern_name_mappings
                    SET canonical_name = %s, dxf_alias = %s, description = %s,
                        import_direction = %s, export_direction = %s, 
                        client_id = %s, confidence_score = %s
                    WHERE mapping_id = %s
                """, (
                    data.get('canonical_name'),
                    data.get('dxf_alias'),
                    data.get('description'),
                    data.get('import_direction', True),
                    data.get('export_direction', True),
                    data.get('client_id'),
                    data.get('confidence_score', 1.0),
                    mapping_id
                ))
                conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/hatch-mappings/<mapping_id>', methods=['DELETE'])
def delete_hatch_mapping(mapping_id):
    """Delete a hatch pattern mapping"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM hatch_pattern_name_mappings WHERE mapping_id = %s", (mapping_id,))
                conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# MATERIAL NAME MAPPINGS CRUD MANAGER
# ============================================================================

@app.route('/data-manager/material-mappings')
def material_mappings_manager():
    """Render the Material Name Mappings Manager page"""
    return render_template('data_manager/material_mappings.html')

@app.route('/api/data-manager/material-mappings', methods=['GET'])
def get_material_mappings_crud():
    """Get all material name mappings for CRUD interface"""
    try:
        query = """
            SELECT * FROM material_name_mappings
            ORDER BY canonical_name
        """
        mappings = execute_query(query)
        return jsonify({'mappings': mappings})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/material-mappings', methods=['POST'])
def create_material_mapping():
    """Create a new material name mapping"""
    try:
        data = request.get_json()
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO material_name_mappings 
                    (canonical_name, dxf_alias, description, import_direction, 
                     export_direction, client_id, confidence_score)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING mapping_id
                """, (
                    data.get('canonical_name'),
                    data.get('dxf_alias'),
                    data.get('description'),
                    data.get('import_direction', True),
                    data.get('export_direction', True),
                    data.get('client_id'),
                    data.get('confidence_score', 1.0)
                ))
                mapping_id = cur.fetchone()[0]
                conn.commit()
        return jsonify({'mapping_id': mapping_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/material-mappings/<mapping_id>', methods=['PUT'])
def update_material_mapping(mapping_id):
    """Update an existing material name mapping"""
    try:
        data = request.get_json()
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE material_name_mappings
                    SET canonical_name = %s, dxf_alias = %s, description = %s,
                        import_direction = %s, export_direction = %s, 
                        client_id = %s, confidence_score = %s
                    WHERE mapping_id = %s
                """, (
                    data.get('canonical_name'),
                    data.get('dxf_alias'),
                    data.get('description'),
                    data.get('import_direction', True),
                    data.get('export_direction', True),
                    data.get('client_id'),
                    data.get('confidence_score', 1.0),
                    mapping_id
                ))
                conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/material-mappings/<mapping_id>', methods=['DELETE'])
def delete_material_mapping(mapping_id):
    """Delete a material name mapping"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM material_name_mappings WHERE mapping_id = %s", (mapping_id,))
                conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# NOTE NAME MAPPINGS CRUD MANAGER
# ============================================================================

@app.route('/data-manager/note-mappings')
def note_mappings_manager():
    """Render the Note Name Mappings Manager page"""
    return render_template('data_manager/note_mappings.html')

@app.route('/api/data-manager/note-mappings', methods=['GET'])
def get_note_mappings_crud():
    """Get all note name mappings for CRUD interface"""
    try:
        query = """
            SELECT * FROM note_name_mappings
            ORDER BY canonical_name
        """
        mappings = execute_query(query)
        return jsonify({'mappings': mappings})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/note-mappings', methods=['POST'])
def create_note_mapping():
    """Create a new note name mapping"""
    try:
        data = request.get_json()
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO note_name_mappings 
                    (canonical_name, dxf_alias, description, import_direction, 
                     export_direction, client_id, confidence_score)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING mapping_id
                """, (
                    data.get('canonical_name'),
                    data.get('dxf_alias'),
                    data.get('description'),
                    data.get('import_direction', True),
                    data.get('export_direction', True),
                    data.get('client_id'),
                    data.get('confidence_score', 1.0)
                ))
                mapping_id = cur.fetchone()[0]
                conn.commit()
        return jsonify({'mapping_id': mapping_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/note-mappings/<mapping_id>', methods=['PUT'])
def update_note_mapping(mapping_id):
    """Update an existing note name mapping"""
    try:
        data = request.get_json()
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE note_name_mappings
                    SET canonical_name = %s, dxf_alias = %s, description = %s,
                        import_direction = %s, export_direction = %s, 
                        client_id = %s, confidence_score = %s
                    WHERE mapping_id = %s
                """, (
                    data.get('canonical_name'),
                    data.get('dxf_alias'),
                    data.get('description'),
                    data.get('import_direction', True),
                    data.get('export_direction', True),
                    data.get('client_id'),
                    data.get('confidence_score', 1.0),
                    mapping_id
                ))
                conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-manager/note-mappings/<mapping_id>', methods=['DELETE'])
def delete_note_mapping(mapping_id):
    """Delete a note name mapping"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM note_name_mappings WHERE mapping_id = %s", (mapping_id,))
                conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# PROJECT CONTEXT MAPPING MANAGER
# ============================================================================

@app.route('/project-context-manager')
def project_context_manager():
    """Project Context Mapping Manager page"""
    return render_template('project_context_manager.html')

@app.route('/api/project-context/keynote-blocks', methods=['GET'])
def get_keynote_blocks():
    """Get keynote-block relationships for a project"""
    try:
        project_id = request.args.get('project_id')
        if not project_id:
            return jsonify({'error': 'project_id is required'}), 400
        
        query = """
            SELECT 
                kbm.mapping_id,
                kbm.project_id,
                kbm.note_id,
                kbm.keynote_number,
                kbm.block_id,
                kbm.relationship_type,
                kbm.usage_context,
                sn.note_text,
                sn.note_number,
                bd.block_name,
                bd.description as block_description
            FROM project_keynote_block_mappings kbm
            LEFT JOIN standard_notes sn ON kbm.note_id = sn.note_id
            LEFT JOIN block_definitions bd ON kbm.block_id = bd.block_id
            WHERE kbm.project_id = %s AND kbm.is_active = TRUE
            ORDER BY kbm.keynote_number, bd.block_name
        """
        mappings = execute_query(query, (project_id,))
        return jsonify({'mappings': mappings})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-context/keynote-blocks', methods=['POST'])
def create_keynote_block():
    """Create a new keynote-block relationship"""
    try:
        data = request.get_json()
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO project_keynote_block_mappings 
                    (project_id, note_id, keynote_number, block_id, relationship_type, usage_context)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING mapping_id
                """, (
                    data.get('project_id'),
                    data.get('note_id'),
                    data.get('keynote_number'),
                    data.get('block_id'),
                    data.get('relationship_type', 'references'),
                    data.get('usage_context')
                ))
                mapping_id = cur.fetchone()[0]
                conn.commit()
        
        return jsonify({'mapping_id': str(mapping_id)}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-context/keynote-blocks/<mapping_id>', methods=['GET'])
def get_keynote_block(mapping_id):
    """Get a single keynote-block relationship"""
    try:
        query = """
            SELECT * FROM project_keynote_block_mappings
            WHERE mapping_id = %s
        """
        result = execute_query(query, (mapping_id,))
        if not result:
            return jsonify({'error': 'Mapping not found'}), 404
        return jsonify(result[0])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-context/keynote-blocks/<mapping_id>', methods=['PUT'])
def update_keynote_block(mapping_id):
    """Update a keynote-block relationship"""
    try:
        data = request.get_json()
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE project_keynote_block_mappings
                    SET note_id = %s, keynote_number = %s, block_id = %s,
                        relationship_type = %s, usage_context = %s
                    WHERE mapping_id = %s
                """, (
                    data.get('note_id'),
                    data.get('keynote_number'),
                    data.get('block_id'),
                    data.get('relationship_type'),
                    data.get('usage_context'),
                    mapping_id
                ))
                conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-context/keynote-blocks/<mapping_id>', methods=['DELETE'])
def delete_keynote_block(mapping_id):
    """Delete a keynote-block relationship"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM project_keynote_block_mappings WHERE mapping_id = %s", (mapping_id,))
                conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-context/keynote-details', methods=['GET'])
def get_keynote_details():
    """Get keynote-detail relationships for a project"""
    try:
        project_id = request.args.get('project_id')
        if not project_id:
            return jsonify({'error': 'project_id is required'}), 400
        
        query = """
            SELECT 
                kdm.mapping_id,
                kdm.project_id,
                kdm.note_id,
                kdm.keynote_number,
                kdm.detail_id,
                kdm.detail_callout,
                kdm.sheet_number,
                kdm.usage_context,
                sn.note_text,
                sn.note_number,
                ds.detail_name,
                ds.detail_description
            FROM project_keynote_detail_mappings kdm
            LEFT JOIN standard_notes sn ON kdm.note_id = sn.note_id
            LEFT JOIN detail_standards ds ON kdm.detail_id = ds.detail_id
            WHERE kdm.project_id = %s AND kdm.is_active = TRUE
            ORDER BY kdm.keynote_number, ds.detail_name
        """
        mappings = execute_query(query, (project_id,))
        return jsonify({'mappings': mappings})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-context/keynote-details', methods=['POST'])
def create_keynote_detail():
    """Create a new keynote-detail relationship"""
    try:
        data = request.get_json()
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO project_keynote_detail_mappings 
                    (project_id, note_id, keynote_number, detail_id, detail_callout, sheet_number, usage_context)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING mapping_id
                """, (
                    data.get('project_id'),
                    data.get('note_id'),
                    data.get('keynote_number'),
                    data.get('detail_id'),
                    data.get('detail_callout'),
                    data.get('sheet_number'),
                    data.get('usage_context')
                ))
                mapping_id = cur.fetchone()[0]
                conn.commit()
        
        return jsonify({'mapping_id': str(mapping_id)}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-context/keynote-details/<mapping_id>', methods=['GET'])
def get_keynote_detail(mapping_id):
    """Get a single keynote-detail relationship"""
    try:
        query = """
            SELECT * FROM project_keynote_detail_mappings
            WHERE mapping_id = %s
        """
        result = execute_query(query, (mapping_id,))
        if not result:
            return jsonify({'error': 'Mapping not found'}), 404
        return jsonify(result[0])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-context/keynote-details/<mapping_id>', methods=['PUT'])
def update_keynote_detail(mapping_id):
    """Update a keynote-detail relationship"""
    try:
        data = request.get_json()
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE project_keynote_detail_mappings
                    SET note_id = %s, keynote_number = %s, detail_id = %s,
                        detail_callout = %s, sheet_number = %s, usage_context = %s
                    WHERE mapping_id = %s
                """, (
                    data.get('note_id'),
                    data.get('keynote_number'),
                    data.get('detail_id'),
                    data.get('detail_callout'),
                    data.get('sheet_number'),
                    data.get('usage_context'),
                    mapping_id
                ))
                conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-context/keynote-details/<mapping_id>', methods=['DELETE'])
def delete_keynote_detail(mapping_id):
    """Delete a keynote-detail relationship"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM project_keynote_detail_mappings WHERE mapping_id = %s", (mapping_id,))
                conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-context/hatch-materials', methods=['GET'])
def get_hatch_materials():
    """Get hatch-material relationships for a project"""
    try:
        project_id = request.args.get('project_id')
        if not project_id:
            return jsonify({'error': 'project_id is required'}), 400
        
        query = """
            SELECT 
                hmm.mapping_id,
                hmm.project_id,
                hmm.hatch_id,
                hmm.hatch_name,
                hmm.material_id,
                hmm.material_thickness,
                hmm.material_notes,
                hmm.is_legend_item,
                hp.pattern_name as hatch_name,
                hp.description as hatch_description,
                ms.material_name,
                ms.material_code
            FROM project_hatch_material_mappings hmm
            LEFT JOIN hatch_patterns hp ON hmm.hatch_id = hp.hatch_id
            LEFT JOIN material_standards ms ON hmm.material_id = ms.material_id
            WHERE hmm.project_id = %s AND hmm.is_active = TRUE
            ORDER BY ms.material_name, hp.pattern_name
        """
        mappings = execute_query(query, (project_id,))
        return jsonify({'mappings': mappings})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-context/hatch-materials', methods=['POST'])
def create_hatch_material():
    """Create a new hatch-material relationship"""
    try:
        data = request.get_json()
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO project_hatch_material_mappings 
                    (project_id, hatch_id, material_id, material_thickness, material_notes, is_legend_item)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING mapping_id
                """, (
                    data.get('project_id'),
                    data.get('hatch_id'),
                    data.get('material_id'),
                    data.get('material_thickness'),
                    data.get('material_notes'),
                    data.get('is_legend_item', True)
                ))
                mapping_id = cur.fetchone()[0]
                conn.commit()
        
        return jsonify({'mapping_id': str(mapping_id)}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-context/hatch-materials/<mapping_id>', methods=['GET'])
def get_hatch_material(mapping_id):
    """Get a single hatch-material relationship"""
    try:
        query = """
            SELECT * FROM project_hatch_material_mappings
            WHERE mapping_id = %s
        """
        result = execute_query(query, (mapping_id,))
        if not result:
            return jsonify({'error': 'Mapping not found'}), 404
        return jsonify(result[0])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-context/hatch-materials/<mapping_id>', methods=['PUT'])
def update_hatch_material(mapping_id):
    """Update a hatch-material relationship"""
    try:
        data = request.get_json()
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE project_hatch_material_mappings
                    SET hatch_id = %s, material_id = %s, material_thickness = %s,
                        material_notes = %s, is_legend_item = %s
                    WHERE mapping_id = %s
                """, (
                    data.get('hatch_id'),
                    data.get('material_id'),
                    data.get('material_thickness'),
                    data.get('material_notes'),
                    data.get('is_legend_item'),
                    mapping_id
                ))
                conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-context/hatch-materials/<mapping_id>', methods=['DELETE'])
def delete_hatch_material(mapping_id):
    """Delete a hatch-material relationship"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM project_hatch_material_mappings WHERE mapping_id = %s", (mapping_id,))
                conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-context/detail-materials', methods=['GET'])
def get_detail_materials():
    """Get detail-material relationships for a project"""
    try:
        project_id = request.args.get('project_id')
        if not project_id:
            return jsonify({'error': 'project_id is required'}), 400
        
        query = """
            SELECT 
                dmm.mapping_id,
                dmm.project_id,
                dmm.detail_id,
                dmm.material_id,
                dmm.material_role,
                dmm.material_layer_order,
                dmm.material_thickness,
                dmm.material_notes,
                ds.detail_name,
                ds.detail_description,
                ms.material_name,
                ms.material_code
            FROM project_detail_material_mappings dmm
            LEFT JOIN detail_standards ds ON dmm.detail_id = ds.detail_id
            LEFT JOIN material_standards ms ON dmm.material_id = ms.material_id
            WHERE dmm.project_id = %s AND dmm.is_active = TRUE
            ORDER BY ds.detail_name, dmm.material_layer_order
        """
        mappings = execute_query(query, (project_id,))
        return jsonify({'mappings': mappings})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-context/detail-materials', methods=['POST'])
def create_detail_material():
    """Create a new detail-material relationship"""
    try:
        data = request.get_json()
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO project_detail_material_mappings 
                    (project_id, detail_id, material_id, material_role, material_layer_order, 
                     material_thickness, material_notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING mapping_id
                """, (
                    data.get('project_id'),
                    data.get('detail_id'),
                    data.get('material_id'),
                    data.get('material_role', 'primary'),
                    data.get('material_layer_order'),
                    data.get('material_thickness'),
                    data.get('material_notes')
                ))
                mapping_id = cur.fetchone()[0]
                conn.commit()
        
        return jsonify({'mapping_id': str(mapping_id)}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-context/detail-materials/<mapping_id>', methods=['GET'])
def get_detail_material(mapping_id):
    """Get a single detail-material relationship"""
    try:
        query = """
            SELECT * FROM project_detail_material_mappings
            WHERE mapping_id = %s
        """
        result = execute_query(query, (mapping_id,))
        if not result:
            return jsonify({'error': 'Mapping not found'}), 404
        return jsonify(result[0])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-context/detail-materials/<mapping_id>', methods=['PUT'])
def update_detail_material(mapping_id):
    """Update a detail-material relationship"""
    try:
        data = request.get_json()
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE project_detail_material_mappings
                    SET detail_id = %s, material_id = %s, material_role = %s,
                        material_layer_order = %s, material_thickness = %s, material_notes = %s
                    WHERE mapping_id = %s
                """, (
                    data.get('detail_id'),
                    data.get('material_id'),
                    data.get('material_role'),
                    data.get('material_layer_order'),
                    data.get('material_thickness'),
                    data.get('material_notes'),
                    mapping_id
                ))
                conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-context/detail-materials/<mapping_id>', methods=['DELETE'])
def delete_detail_material(mapping_id):
    """Delete a detail-material relationship"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM project_detail_material_mappings WHERE mapping_id = %s", (mapping_id,))
                conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-context/block-specs', methods=['GET'])
def get_block_specs():
    """Get block-specification relationships for a project"""
    try:
        project_id = request.args.get('project_id')
        if not project_id:
            return jsonify({'error': 'project_id is required'}), 400
        
        query = """
            SELECT 
                bsm.mapping_id,
                bsm.project_id,
                bsm.block_id,
                bsm.spec_section,
                bsm.spec_description,
                bsm.manufacturer,
                bsm.model_number,
                bsm.product_url,
                bsm.jurisdiction,
                bd.block_name,
                bd.description as block_description
            FROM project_block_specification_mappings bsm
            LEFT JOIN block_definitions bd ON bsm.block_id = bd.block_id
            WHERE bsm.project_id = %s AND bsm.is_active = TRUE
            ORDER BY bd.block_name, bsm.spec_section
        """
        mappings = execute_query(query, (project_id,))
        return jsonify({'mappings': mappings})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-context/block-specs', methods=['POST'])
def create_block_spec():
    """Create a new block-specification relationship"""
    try:
        data = request.get_json()
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO project_block_specification_mappings 
                    (project_id, block_id, spec_section, spec_description, manufacturer, 
                     model_number, product_url, jurisdiction)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING mapping_id
                """, (
                    data.get('project_id'),
                    data.get('block_id'),
                    data.get('spec_section'),
                    data.get('spec_description'),
                    data.get('manufacturer'),
                    data.get('model_number'),
                    data.get('product_url'),
                    data.get('jurisdiction')
                ))
                mapping_id = cur.fetchone()[0]
                conn.commit()
        
        return jsonify({'mapping_id': str(mapping_id)}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-context/block-specs/<mapping_id>', methods=['GET'])
def get_block_spec(mapping_id):
    """Get a single block-specification relationship"""
    try:
        query = """
            SELECT * FROM project_block_specification_mappings
            WHERE mapping_id = %s
        """
        result = execute_query(query, (mapping_id,))
        if not result:
            return jsonify({'error': 'Mapping not found'}), 404
        return jsonify(result[0])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-context/block-specs/<mapping_id>', methods=['PUT'])
def update_block_spec(mapping_id):
    """Update a block-specification relationship"""
    try:
        data = request.get_json()
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE project_block_specification_mappings
                    SET block_id = %s, spec_section = %s, spec_description = %s,
                        manufacturer = %s, model_number = %s, product_url = %s, jurisdiction = %s
                    WHERE mapping_id = %s
                """, (
                    data.get('block_id'),
                    data.get('spec_section'),
                    data.get('spec_description'),
                    data.get('manufacturer'),
                    data.get('model_number'),
                    data.get('product_url'),
                    data.get('jurisdiction'),
                    mapping_id
                ))
                conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-context/block-specs/<mapping_id>', methods=['DELETE'])
def delete_block_spec(mapping_id):
    """Delete a block-specification relationship"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM project_block_specification_mappings WHERE mapping_id = %s", (mapping_id,))
                conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# STANDARDS DOCUMENTATION EXPORT
# ============================================================================

@app.route('/standards-export')
def standards_export_page():
    """Standards Documentation Export page"""
    return render_template('standards_export.html')

@app.route('/api/standards-export/generate', methods=['POST'])
def generate_standards_export():
    """Generate standards documentation export in requested format"""
    try:
        config = request.get_json()
        export_type = config.get('exportType')
        title = config.get('title', 'CAD Standards Documentation')
        description = config.get('description', '')
        name_mappings = config.get('nameMappings', {})
        relationships = config.get('relationships', {})
        
        # Collect data based on configuration
        data = {}
        
        # Get name mappings
        if name_mappings.get('blocks'):
            query = """
                SELECT 
                    bnm.project_id,
                    COALESCE(p.project_name, bnm.client_name, 'Global') as project_name,
                    bnm.dxf_alias as imported_name,
                    bnm.block_id,
                    bd.block_name as standard_name,
                    bd.description
                FROM block_name_mappings bnm
                LEFT JOIN projects p ON bnm.project_id = p.project_id
                LEFT JOIN block_definitions bd ON bnm.block_id = bd.block_id
                WHERE bnm.is_active = TRUE
                ORDER BY project_name, bnm.dxf_alias
            """
            data['block_mappings'] = execute_query(query)
        
        if name_mappings.get('details'):
            query = """
                SELECT 
                    dnm.project_id,
                    COALESCE(p.project_name, dnm.client_name, 'Global') as project_name,
                    dnm.dxf_alias as imported_name,
                    dnm.detail_id,
                    ds.detail_title as standard_name,
                    ds.description
                FROM detail_name_mappings dnm
                LEFT JOIN projects p ON dnm.project_id = p.project_id
                LEFT JOIN detail_standards ds ON dnm.detail_id = ds.detail_id
                WHERE dnm.is_active = TRUE
                ORDER BY project_name, dnm.dxf_alias
            """
            data['detail_mappings'] = execute_query(query)
        
        if name_mappings.get('hatches'):
            query = """
                SELECT 
                    hnm.project_id,
                    COALESCE(p.project_name, hnm.client_name, 'Global') as project_name,
                    hnm.dxf_alias as imported_name,
                    hnm.hatch_id,
                    hp.pattern_name as standard_name,
                    hp.description
                FROM hatch_pattern_name_mappings hnm
                LEFT JOIN projects p ON hnm.project_id = p.project_id
                LEFT JOIN hatch_patterns hp ON hnm.hatch_id = hp.hatch_id
                WHERE hnm.is_active = TRUE
                ORDER BY project_name, hnm.dxf_alias
            """
            data['hatch_mappings'] = execute_query(query)
        
        if name_mappings.get('materials'):
            query = """
                SELECT 
                    mnm.project_id,
                    COALESCE(p.project_name, mnm.client_name, 'Global') as project_name,
                    mnm.dxf_alias as imported_name,
                    mnm.material_id,
                    ms.material_name as standard_name,
                    ms.description
                FROM material_name_mappings mnm
                LEFT JOIN projects p ON mnm.project_id = p.project_id
                LEFT JOIN material_standards ms ON mnm.material_id = ms.material_id
                WHERE mnm.is_active = TRUE
                ORDER BY project_name, mnm.dxf_alias
            """
            data['material_mappings'] = execute_query(query)
        
        if name_mappings.get('notes'):
            query = """
                SELECT 
                    nnm.project_id,
                    COALESCE(p.project_name, nnm.client_name, 'Global') as project_name,
                    nnm.dxf_alias as imported_name,
                    nnm.note_id,
                    sn.note_text as standard_name,
                    sn.note_category as category
                FROM note_name_mappings nnm
                LEFT JOIN projects p ON nnm.project_id = p.project_id
                LEFT JOIN standard_notes sn ON nnm.note_id = sn.note_id
                WHERE nnm.is_active = TRUE
                ORDER BY project_name, nnm.dxf_alias
            """
            data['note_mappings'] = execute_query(query)
        
        # Get relationships
        if relationships.get('keynoteBlocks'):
            query = """
                SELECT 
                    pkbm.project_id,
                    p.project_name,
                    pkbm.keynote_number as keynote,
                    pkbm.block_id,
                    bd.block_name,
                    pkbm.usage_context as context_notes
                FROM project_keynote_block_mappings pkbm
                LEFT JOIN projects p ON pkbm.project_id = p.project_id
                LEFT JOIN block_definitions bd ON pkbm.block_id = bd.block_id
                WHERE pkbm.is_active = TRUE
                ORDER BY p.project_name, pkbm.keynote_number
            """
            data['keynote_block_relationships'] = execute_query(query)
        
        if relationships.get('keynoteDetails'):
            query = """
                SELECT 
                    pkdm.project_id,
                    p.project_name,
                    pkdm.keynote_number as keynote,
                    pkdm.detail_id,
                    ds.detail_title as detail_name,
                    pkdm.usage_context as context_notes
                FROM project_keynote_detail_mappings pkdm
                LEFT JOIN projects p ON pkdm.project_id = p.project_id
                LEFT JOIN detail_standards ds ON pkdm.detail_id = ds.detail_id
                WHERE pkdm.is_active = TRUE
                ORDER BY p.project_name, pkdm.keynote_number
            """
            data['keynote_detail_relationships'] = execute_query(query)
        
        if relationships.get('hatchMaterials'):
            query = """
                SELECT 
                    phmm.project_id,
                    p.project_name,
                    phmm.hatch_id,
                    hp.pattern_name,
                    phmm.material_id,
                    ms.material_name,
                    phmm.material_notes as context_notes
                FROM project_hatch_material_mappings phmm
                LEFT JOIN projects p ON phmm.project_id = p.project_id
                LEFT JOIN hatch_patterns hp ON phmm.hatch_id = hp.hatch_id
                LEFT JOIN material_standards ms ON phmm.material_id = ms.material_id
                WHERE phmm.is_active = TRUE
                ORDER BY p.project_name, hp.pattern_name
            """
            data['hatch_material_relationships'] = execute_query(query)
        
        if relationships.get('detailMaterials'):
            query = """
                SELECT 
                    pdmm.project_id,
                    p.project_name,
                    pdmm.detail_id,
                    ds.detail_title as detail_name,
                    pdmm.material_id,
                    ms.material_name,
                    pdmm.material_notes as context_notes
                FROM project_detail_material_mappings pdmm
                LEFT JOIN projects p ON pdmm.project_id = p.project_id
                LEFT JOIN detail_standards ds ON pdmm.detail_id = ds.detail_id
                LEFT JOIN material_standards ms ON pdmm.material_id = ms.material_id
                WHERE pdmm.is_active = TRUE
                ORDER BY p.project_name, ds.detail_title
            """
            data['detail_material_relationships'] = execute_query(query)
        
        if relationships.get('blockSpecs'):
            query = """
                SELECT 
                    pbsm.project_id,
                    p.project_name,
                    pbsm.block_id,
                    bd.block_name,
                    pbsm.spec_section,
                    pbsm.spec_description,
                    pbsm.manufacturer,
                    pbsm.model_number
                FROM project_block_specification_mappings pbsm
                LEFT JOIN projects p ON pbsm.project_id = p.project_id
                LEFT JOIN block_definitions bd ON pbsm.block_id = bd.block_id
                WHERE pbsm.is_active = TRUE
                ORDER BY p.project_name, bd.block_name
            """
            data['block_spec_relationships'] = execute_query(query)
        
        # Generate export based on type
        if export_type == 'excel':
            return generate_excel_export(data, title, description)
        elif export_type == 'csv':
            return generate_csv_export(data, title, description)
        elif export_type == 'html':
            return generate_html_export(data, title, description)
        elif export_type == 'pdf':
            return generate_pdf_export(data, title, description)
        else:
            return jsonify({'error': 'Invalid export type'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_excel_export(data, title, description):
    """Generate Excel workbook export"""
    wb = openpyxl.Workbook()
    
    # Remove default sheet
    wb.remove(wb.active)
    
    # Create Overview sheet
    ws_overview = wb.create_sheet("Overview")
    ws_overview.append(['Title', title])
    ws_overview.append(['Description', description])
    ws_overview.append(['Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    ws_overview.append([])
    ws_overview.append(['Statistics'])
    
    for key, items in data.items():
        ws_overview.append([key.replace('_', ' ').title(), len(items)])
    
    # Style overview
    for cell in ws_overview[1]:
        cell.font = Font(bold=True)
    for cell in ws_overview[5]:
        cell.font = Font(bold=True)
    
    # Create sheets for each data type
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="00B4D8", end_color="00B4D8", fill_type="solid")
    
    if 'block_mappings' in data:
        ws = wb.create_sheet("Block Mappings")
        ws.append(['Project', 'Imported Name', 'Standard Name', 'Description'])
        for row in ws[1]:
            row.font = header_font
            row.fill = header_fill
        for item in data['block_mappings']:
            ws.append([
                item.get('project_name', ''),
                item.get('imported_name', ''),
                item.get('standard_name', ''),
                item.get('description', '')
            ])
        for column in ws.columns:
            max_length = 0
            for cell in column:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            ws.column_dimensions[column[0].column_letter].width = min(max_length + 2, 50)
    
    if 'detail_mappings' in data:
        ws = wb.create_sheet("Detail Mappings")
        ws.append(['Project', 'Imported Name', 'Standard Name', 'Description'])
        for row in ws[1]:
            row.font = header_font
            row.fill = header_fill
        for item in data['detail_mappings']:
            ws.append([
                item.get('project_name', ''),
                item.get('imported_name', ''),
                item.get('standard_name', ''),
                item.get('description', '')
            ])
        for column in ws.columns:
            max_length = 0
            for cell in column:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            ws.column_dimensions[column[0].column_letter].width = min(max_length + 2, 50)
    
    if 'hatch_mappings' in data:
        ws = wb.create_sheet("Hatch Mappings")
        ws.append(['Project', 'Imported Name', 'Standard Name', 'Description'])
        for row in ws[1]:
            row.font = header_font
            row.fill = header_fill
        for item in data['hatch_mappings']:
            ws.append([
                item.get('project_name', ''),
                item.get('imported_name', ''),
                item.get('standard_name', ''),
                item.get('description', '')
            ])
        for column in ws.columns:
            max_length = 0
            for cell in column:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            ws.column_dimensions[column[0].column_letter].width = min(max_length + 2, 50)
    
    if 'material_mappings' in data:
        ws = wb.create_sheet("Material Mappings")
        ws.append(['Project', 'Imported Name', 'Standard Name', 'Description'])
        for row in ws[1]:
            row.font = header_font
            row.fill = header_fill
        for item in data['material_mappings']:
            ws.append([
                item.get('project_name', ''),
                item.get('imported_name', ''),
                item.get('standard_name', ''),
                item.get('description', '')
            ])
        for column in ws.columns:
            max_length = 0
            for cell in column:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            ws.column_dimensions[column[0].column_letter].width = min(max_length + 2, 50)
    
    if 'note_mappings' in data:
        ws = wb.create_sheet("Note Mappings")
        ws.append(['Project', 'Imported Name', 'Standard Note', 'Category'])
        for row in ws[1]:
            row.font = header_font
            row.fill = header_fill
        for item in data['note_mappings']:
            ws.append([
                item.get('project_name', ''),
                item.get('imported_name', ''),
                item.get('standard_name', ''),
                item.get('category', '')
            ])
        for column in ws.columns:
            max_length = 0
            for cell in column:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            ws.column_dimensions[column[0].column_letter].width = min(max_length + 2, 50)
    
    # Add relationship sheets
    if 'keynote_block_relationships' in data:
        ws = wb.create_sheet("Keynote-Block Relations")
        ws.append(['Project', 'Keynote', 'Block Name', 'Notes'])
        for row in ws[1]:
            row.font = header_font
            row.fill = header_fill
        for item in data['keynote_block_relationships']:
            ws.append([
                item.get('project_name', ''),
                item.get('keynote', ''),
                item.get('block_name', ''),
                item.get('context_notes', '')
            ])
    
    if 'keynote_detail_relationships' in data:
        ws = wb.create_sheet("Keynote-Detail Relations")
        ws.append(['Project', 'Keynote', 'Detail Name', 'Notes'])
        for row in ws[1]:
            row.font = header_font
            row.fill = header_fill
        for item in data['keynote_detail_relationships']:
            ws.append([
                item.get('project_name', ''),
                item.get('keynote', ''),
                item.get('detail_name', ''),
                item.get('context_notes', '')
            ])
    
    if 'hatch_material_relationships' in data:
        ws = wb.create_sheet("Hatch-Material Relations")
        ws.append(['Project', 'Hatch Pattern', 'Material', 'Notes'])
        for row in ws[1]:
            row.font = header_font
            row.fill = header_fill
        for item in data['hatch_material_relationships']:
            ws.append([
                item.get('project_name', ''),
                item.get('pattern_name', ''),
                item.get('material_name', ''),
                item.get('context_notes', '')
            ])
    
    if 'detail_material_relationships' in data:
        ws = wb.create_sheet("Detail-Material Relations")
        ws.append(['Project', 'Detail Name', 'Material', 'Notes'])
        for row in ws[1]:
            row.font = header_font
            row.fill = header_fill
        for item in data['detail_material_relationships']:
            ws.append([
                item.get('project_name', ''),
                item.get('detail_name', ''),
                item.get('material_name', ''),
                item.get('context_notes', '')
            ])
    
    if 'block_spec_relationships' in data:
        ws = wb.create_sheet("Block-Specification Relations")
        ws.append(['Project', 'Block Name', 'Spec Section', 'Description', 'Manufacturer', 'Model'])
        for row in ws[1]:
            row.font = header_font
            row.fill = header_fill
        for item in data['block_spec_relationships']:
            ws.append([
                item.get('project_name', ''),
                item.get('block_name', ''),
                item.get('spec_section', ''),
                item.get('spec_description', ''),
                item.get('manufacturer', ''),
                item.get('model_number', '')
            ])
    
    # Save to bytes
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'CAD_Standards_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

def generate_csv_export(data, title, description):
    """Generate CSV files in ZIP archive"""
    # Create temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        files_created = []
        
        # Create CSV for each data type
        if 'block_mappings' in data and data['block_mappings']:
            filepath = os.path.join(tmpdir, 'block_mappings.csv')
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Project', 'Imported Name', 'Standard Name', 'Description'])
                for item in data['block_mappings']:
                    writer.writerow([
                        item.get('project_name', ''),
                        item.get('imported_name', ''),
                        item.get('standard_name', ''),
                        item.get('description', '')
                    ])
            files_created.append(filepath)
        
        if 'detail_mappings' in data and data['detail_mappings']:
            filepath = os.path.join(tmpdir, 'detail_mappings.csv')
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Project', 'Imported Name', 'Standard Name', 'Description'])
                for item in data['detail_mappings']:
                    writer.writerow([
                        item.get('project_name', ''),
                        item.get('imported_name', ''),
                        item.get('standard_name', ''),
                        item.get('description', '')
                    ])
            files_created.append(filepath)
        
        if 'hatch_mappings' in data and data['hatch_mappings']:
            filepath = os.path.join(tmpdir, 'hatch_mappings.csv')
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Project', 'Imported Name', 'Standard Name', 'Description'])
                for item in data['hatch_mappings']:
                    writer.writerow([
                        item.get('project_name', ''),
                        item.get('imported_name', ''),
                        item.get('standard_name', ''),
                        item.get('description', '')
                    ])
            files_created.append(filepath)
        
        if 'material_mappings' in data and data['material_mappings']:
            filepath = os.path.join(tmpdir, 'material_mappings.csv')
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Project', 'Imported Name', 'Standard Name', 'Description'])
                for item in data['material_mappings']:
                    writer.writerow([
                        item.get('project_name', ''),
                        item.get('imported_name', ''),
                        item.get('standard_name', ''),
                        item.get('description', '')
                    ])
            files_created.append(filepath)
        
        if 'note_mappings' in data and data['note_mappings']:
            filepath = os.path.join(tmpdir, 'note_mappings.csv')
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Project', 'Imported Name', 'Standard Note', 'Category'])
                for item in data['note_mappings']:
                    writer.writerow([
                        item.get('project_name', ''),
                        item.get('imported_name', ''),
                        item.get('standard_name', ''),
                        item.get('category', '')
                    ])
            files_created.append(filepath)
        
        # Add metadata file
        metadata_path = os.path.join(tmpdir, 'README.txt')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            f.write(f"{title}\n")
            f.write("=" * len(title) + "\n\n")
            f.write(f"{description}\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        files_created.append(metadata_path)
        
        # Create ZIP file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for filepath in files_created:
                zip_file.write(filepath, os.path.basename(filepath))
        
        zip_buffer.seek(0)
        
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'CAD_Standards_{datetime.now().strftime("%Y%m%d")}.zip'
        )

def generate_html_export(data, title, description):
    """Generate standalone HTML export"""
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #001a33 0%, #003d66 100%);
            color: #e0e0e0;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(0, 40, 80, 0.6);
            border: 1px solid #00b4d8;
            border-radius: 8px;
            padding: 30px;
        }}
        h1 {{
            color: #00b4d8;
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
        }}
        .subtitle {{
            text-align: center;
            color: #90e0ef;
            margin-bottom: 30px;
        }}
        .section {{
            margin: 30px 0;
        }}
        h2 {{
            color: #00b4d8;
            border-bottom: 2px solid #00b4d8;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: rgba(0, 20, 40, 0.6);
        }}
        th {{
            background: #00b4d8;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: bold;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid rgba(0, 180, 216, 0.2);
        }}
        tr:hover {{
            background: rgba(0, 180, 216, 0.1);
        }}
        .empty {{
            text-align: center;
            padding: 20px;
            color: #90e0ef;
            font-style: italic;
        }}
        .metadata {{
            background: rgba(0, 60, 100, 0.4);
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 30px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <p class="subtitle">{description}</p>
        
        <div class="metadata">
            <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
"""
    
    # Add each data section
    if 'block_mappings' in data:
        html_content += '<div class="section"><h2>Block Name Mappings</h2>'
        if data['block_mappings']:
            html_content += '<table><thead><tr><th>Project</th><th>Imported Name</th><th>Standard Name</th><th>Description</th></tr></thead><tbody>'
            for item in data['block_mappings']:
                html_content += f"<tr><td>{item.get('project_name', '')}</td><td>{item.get('imported_name', '')}</td><td>{item.get('standard_name', '')}</td><td>{item.get('description', '')}</td></tr>"
            html_content += '</tbody></table>'
        else:
            html_content += '<p class="empty">No block mappings found</p>'
        html_content += '</div>'
    
    if 'detail_mappings' in data:
        html_content += '<div class="section"><h2>Detail Name Mappings</h2>'
        if data['detail_mappings']:
            html_content += '<table><thead><tr><th>Project</th><th>Imported Name</th><th>Standard Name</th><th>Description</th></tr></thead><tbody>'
            for item in data['detail_mappings']:
                html_content += f"<tr><td>{item.get('project_name', '')}</td><td>{item.get('imported_name', '')}</td><td>{item.get('standard_name', '')}</td><td>{item.get('description', '')}</td></tr>"
            html_content += '</tbody></table>'
        else:
            html_content += '<p class="empty">No detail mappings found</p>'
        html_content += '</div>'
    
    if 'hatch_mappings' in data:
        html_content += '<div class="section"><h2>Hatch Pattern Mappings</h2>'
        if data['hatch_mappings']:
            html_content += '<table><thead><tr><th>Project</th><th>Imported Name</th><th>Standard Name</th><th>Description</th></tr></thead><tbody>'
            for item in data['hatch_mappings']:
                html_content += f"<tr><td>{item.get('project_name', '')}</td><td>{item.get('imported_name', '')}</td><td>{item.get('standard_name', '')}</td><td>{item.get('description', '')}</td></tr>"
            html_content += '</tbody></table>'
        else:
            html_content += '<p class="empty">No hatch mappings found</p>'
        html_content += '</div>'
    
    if 'material_mappings' in data:
        html_content += '<div class="section"><h2>Material Name Mappings</h2>'
        if data['material_mappings']:
            html_content += '<table><thead><tr><th>Project</th><th>Imported Name</th><th>Standard Name</th><th>Description</th></tr></thead><tbody>'
            for item in data['material_mappings']:
                html_content += f"<tr><td>{item.get('project_name', '')}</td><td>{item.get('imported_name', '')}</td><td>{item.get('standard_name', '')}</td><td>{item.get('description', '')}</td></tr>"
            html_content += '</tbody></table>'
        else:
            html_content += '<p class="empty">No material mappings found</p>'
        html_content += '</div>'
    
    if 'note_mappings' in data:
        html_content += '<div class="section"><h2>Note/Keynote Mappings</h2>'
        if data['note_mappings']:
            html_content += '<table><thead><tr><th>Project</th><th>Imported Name</th><th>Standard Note</th><th>Category</th></tr></thead><tbody>'
            for item in data['note_mappings']:
                html_content += f"<tr><td>{item.get('project_name', '')}</td><td>{item.get('imported_name', '')}</td><td>{item.get('standard_name', '')}</td><td>{item.get('category', '')}</td></tr>"
            html_content += '</tbody></table>'
        else:
            html_content += '<p class="empty">No note mappings found</p>'
        html_content += '</div>'
    
    if 'keynote_block_relationships' in data:
        html_content += '<div class="section"><h2>Keynote → Block Relationships</h2>'
        if data['keynote_block_relationships']:
            html_content += '<table><thead><tr><th>Project</th><th>Keynote</th><th>Block Name</th><th>Notes</th></tr></thead><tbody>'
            for item in data['keynote_block_relationships']:
                html_content += f"<tr><td>{item.get('project_name', '')}</td><td>{item.get('keynote', '')}</td><td>{item.get('block_name', '')}</td><td>{item.get('context_notes', '')}</td></tr>"
            html_content += '</tbody></table>'
        else:
            html_content += '<p class="empty">No keynote-block relationships found</p>'
        html_content += '</div>'
    
    if 'keynote_detail_relationships' in data:
        html_content += '<div class="section"><h2>Keynote → Detail Relationships</h2>'
        if data['keynote_detail_relationships']:
            html_content += '<table><thead><tr><th>Project</th><th>Keynote</th><th>Detail Name</th><th>Notes</th></tr></thead><tbody>'
            for item in data['keynote_detail_relationships']:
                html_content += f"<tr><td>{item.get('project_name', '')}</td><td>{item.get('keynote', '')}</td><td>{item.get('detail_name', '')}</td><td>{item.get('context_notes', '')}</td></tr>"
            html_content += '</tbody></table>'
        else:
            html_content += '<p class="empty">No keynote-detail relationships found</p>'
        html_content += '</div>'
    
    if 'hatch_material_relationships' in data:
        html_content += '<div class="section"><h2>Hatch → Material Relationships</h2>'
        if data['hatch_material_relationships']:
            html_content += '<table><thead><tr><th>Project</th><th>Hatch Pattern</th><th>Material</th><th>Notes</th></tr></thead><tbody>'
            for item in data['hatch_material_relationships']:
                html_content += f"<tr><td>{item.get('project_name', '')}</td><td>{item.get('pattern_name', '')}</td><td>{item.get('material_name', '')}</td><td>{item.get('context_notes', '')}</td></tr>"
            html_content += '</tbody></table>'
        else:
            html_content += '<p class="empty">No hatch-material relationships found</p>'
        html_content += '</div>'
    
    if 'detail_material_relationships' in data:
        html_content += '<div class="section"><h2>Detail → Material Relationships</h2>'
        if data['detail_material_relationships']:
            html_content += '<table><thead><tr><th>Project</th><th>Detail Name</th><th>Material</th><th>Notes</th></tr></thead><tbody>'
            for item in data['detail_material_relationships']:
                html_content += f"<tr><td>{item.get('project_name', '')}</td><td>{item.get('detail_name', '')}</td><td>{item.get('material_name', '')}</td><td>{item.get('context_notes', '')}</td></tr>"
            html_content += '</tbody></table>'
        else:
            html_content += '<p class="empty">No detail-material relationships found</p>'
        html_content += '</div>'
    
    if 'block_spec_relationships' in data:
        html_content += '<div class="section"><h2>Block → Specification Relationships</h2>'
        if data['block_spec_relationships']:
            html_content += '<table><thead><tr><th>Project</th><th>Block Name</th><th>Spec Section</th><th>Description</th><th>Manufacturer</th><th>Model</th></tr></thead><tbody>'
            for item in data['block_spec_relationships']:
                html_content += f"<tr><td>{item.get('project_name', '')}</td><td>{item.get('block_name', '')}</td><td>{item.get('spec_section', '')}</td><td>{item.get('spec_description', '')}</td><td>{item.get('manufacturer', '')}</td><td>{item.get('model_number', '')}</td></tr>"
            html_content += '</tbody></table>'
        else:
            html_content += '<p class="empty">No block-specification relationships found</p>'
        html_content += '</div>'
    
    html_content += """
    </div>
</body>
</html>
"""
    
    # Return as file download
    return send_file(
        io.BytesIO(html_content.encode('utf-8')),
        mimetype='text/html',
        as_attachment=True,
        download_name=f'CAD_Standards_{datetime.now().strftime("%Y%m%d")}.html'
    )

def generate_pdf_export(data, title, description):
    """Generate PDF export from HTML"""
    # Generate HTML content first
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
</head>
<body>
    <h1>{title}</h1>
    <p>{description}</p>
    <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
"""
    
    # Add each data section
    if 'block_mappings' in data and data['block_mappings']:
        html_content += '<h2>Block Name Mappings</h2><table border="1" cellpadding="5" cellspacing="0" style="width:100%; border-collapse:collapse;"><thead><tr><th>Project</th><th>Imported Name</th><th>Standard Name</th><th>Description</th></tr></thead><tbody>'
        for item in data['block_mappings']:
            html_content += f"<tr><td>{item.get('project_name', '')}</td><td>{item.get('imported_name', '')}</td><td>{item.get('standard_name', '')}</td><td>{item.get('description', '')}</td></tr>"
        html_content += '</tbody></table>'
    
    if 'detail_mappings' in data and data['detail_mappings']:
        html_content += '<h2>Detail Name Mappings</h2><table border="1" cellpadding="5" cellspacing="0" style="width:100%; border-collapse:collapse;"><thead><tr><th>Project</th><th>Imported Name</th><th>Standard Name</th><th>Description</th></tr></thead><tbody>'
        for item in data['detail_mappings']:
            html_content += f"<tr><td>{item.get('project_name', '')}</td><td>{item.get('imported_name', '')}</td><td>{item.get('standard_name', '')}</td><td>{item.get('description', '')}</td></tr>"
        html_content += '</tbody></table>'
    
    if 'hatch_mappings' in data and data['hatch_mappings']:
        html_content += '<h2>Hatch Pattern Mappings</h2><table border="1" cellpadding="5" cellspacing="0" style="width:100%; border-collapse:collapse;"><thead><tr><th>Project</th><th>Imported Name</th><th>Standard Name</th><th>Description</th></tr></thead><tbody>'
        for item in data['hatch_mappings']:
            html_content += f"<tr><td>{item.get('project_name', '')}</td><td>{item.get('imported_name', '')}</td><td>{item.get('standard_name', '')}</td><td>{item.get('description', '')}</td></tr>"
        html_content += '</tbody></table>'
    
    if 'material_mappings' in data and data['material_mappings']:
        html_content += '<h2>Material Name Mappings</h2><table border="1" cellpadding="5" cellspacing="0" style="width:100%; border-collapse:collapse;"><thead><tr><th>Project</th><th>Imported Name</th><th>Standard Name</th><th>Description</th></tr></thead><tbody>'
        for item in data['material_mappings']:
            html_content += f"<tr><td>{item.get('project_name', '')}</td><td>{item.get('imported_name', '')}</td><td>{item.get('standard_name', '')}</td><td>{item.get('description', '')}</td></tr>"
        html_content += '</tbody></table>'
    
    if 'note_mappings' in data and data['note_mappings']:
        html_content += '<h2>Note/Keynote Mappings</h2><table border="1" cellpadding="5" cellspacing="0" style="width:100%; border-collapse:collapse;"><thead><tr><th>Project</th><th>Imported Name</th><th>Standard Note</th><th>Category</th></tr></thead><tbody>'
        for item in data['note_mappings']:
            html_content += f"<tr><td>{item.get('project_name', '')}</td><td>{item.get('imported_name', '')}</td><td>{item.get('standard_name', '')}</td><td>{item.get('category', '')}</td></tr>"
        html_content += '</tbody></table>'
    
    html_content += '</body></html>'
    
    # Convert to PDF using WeasyPrint
    pdf_bytes = HTML(string=html_content).write_pdf()
    
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'CAD_Standards_{datetime.now().strftime("%Y%m%d")}.pdf'
    )

# ============================================================================
# PROJECT ELEMENT CROSS-REFERENCES API ENDPOINTS
# ============================================================================

def validate_element_exists(element_type, element_id):
    """Validate that an element ID exists in the appropriate table for its type"""
    element_tables = {
        'keynote': ('standard_notes', 'note_id'),
        'block': ('block_definitions', 'block_id'),
        'detail': ('detail_standards', 'detail_id'),
        'hatch': ('hatch_patterns', 'hatch_id'),
        'material': ('material_standards', 'material_id')
    }
    
    if element_type not in element_tables:
        return False, f"Invalid element type: {element_type}"
    
    table_name, id_column = element_tables[element_type]
    
    try:
        query = f"SELECT 1 FROM {table_name} WHERE {id_column} = %s LIMIT 1"
        result = execute_query(query, (element_id,))
        if not result:
            return False, f"{element_type} with ID {element_id} not found in {table_name}"
        return True, None
    except Exception as e:
        return False, f"Validation error: {str(e)}"

@app.route('/api/project-context/cross-references', methods=['GET'])
def get_cross_references():
    """Get cross-reference relationships for a project"""
    try:
        project_id = request.args.get('project_id')
        if not project_id:
            return jsonify({'error': 'project_id is required'}), 400
        
        query = """
            SELECT 
                xref_id,
                project_id,
                source_element_type,
                source_element_id,
                source_element_name,
                target_element_type,
                target_element_id,
                target_element_name,
                relationship_type,
                relationship_strength,
                context_description,
                sheet_references,
                tags,
                attributes,
                is_active,
                created_at,
                updated_at
            FROM project_element_cross_references
            WHERE project_id = %s AND is_active = TRUE
            ORDER BY created_at DESC
        """
        mappings = execute_query(query, (project_id,))
        return jsonify({'mappings': mappings})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-context/cross-references', methods=['POST'])
def create_cross_reference():
    """Create a new cross-reference relationship"""
    try:
        data = request.get_json()
        
        # Validate source element
        source_valid, source_error = validate_element_exists(
            data.get('source_element_type'),
            data.get('source_element_id')
        )
        if not source_valid:
            return jsonify({'error': source_error}), 400
        
        # Validate target element
        target_valid, target_error = validate_element_exists(
            data.get('target_element_type'),
            data.get('target_element_id')
        )
        if not target_valid:
            return jsonify({'error': target_error}), 400
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO project_element_cross_references 
                    (project_id, source_element_type, source_element_id, source_element_name,
                     target_element_type, target_element_id, target_element_name,
                     relationship_type, relationship_strength, context_description,
                     sheet_references, tags)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING xref_id
                """, (
                    data.get('project_id'),
                    data.get('source_element_type'),
                    data.get('source_element_id'),
                    data.get('source_element_name'),
                    data.get('target_element_type'),
                    data.get('target_element_id'),
                    data.get('target_element_name'),
                    data.get('relationship_type'),
                    data.get('relationship_strength', 'normal'),
                    data.get('context_description'),
                    data.get('sheet_references', []),
                    data.get('tags', [])
                ))
                xref_id = cur.fetchone()[0]
                conn.commit()
        
        return jsonify({'xref_id': str(xref_id)}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-context/cross-references/<xref_id>', methods=['GET'])
def get_cross_reference(xref_id):
    """Get a single cross-reference relationship"""
    try:
        query = """
            SELECT * FROM project_element_cross_references
            WHERE xref_id = %s
        """
        result = execute_query(query, (xref_id,))
        if not result:
            return jsonify({'error': 'Cross-reference not found'}), 404
        return jsonify(result[0])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-context/cross-references/<xref_id>', methods=['PUT'])
def update_cross_reference(xref_id):
    """Update a cross-reference relationship"""
    try:
        data = request.get_json()
        
        # Validate source element
        source_valid, source_error = validate_element_exists(
            data.get('source_element_type'),
            data.get('source_element_id')
        )
        if not source_valid:
            return jsonify({'error': source_error}), 400
        
        # Validate target element
        target_valid, target_error = validate_element_exists(
            data.get('target_element_type'),
            data.get('target_element_id')
        )
        if not target_valid:
            return jsonify({'error': target_error}), 400
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE project_element_cross_references
                    SET source_element_type = %s, source_element_id = %s, source_element_name = %s,
                        target_element_type = %s, target_element_id = %s, target_element_name = %s,
                        relationship_type = %s, relationship_strength = %s, context_description = %s,
                        sheet_references = %s, tags = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE xref_id = %s
                """, (
                    data.get('source_element_type'),
                    data.get('source_element_id'),
                    data.get('source_element_name'),
                    data.get('target_element_type'),
                    data.get('target_element_id'),
                    data.get('target_element_name'),
                    data.get('relationship_type'),
                    data.get('relationship_strength'),
                    data.get('context_description'),
                    data.get('sheet_references', []),
                    data.get('tags', []),
                    xref_id
                ))
                conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-context/cross-references/<xref_id>', methods=['DELETE'])
def delete_cross_reference(xref_id):
    """Delete a cross-reference relationship"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM project_element_cross_references WHERE xref_id = %s", (xref_id,))
                conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/project-context/search-elements', methods=['GET'])
def search_elements():
    """Search for elements by type and query string (for typeahead)"""
    try:
        element_type = request.args.get('type')
        query_str = request.args.get('query', '')
        
        if not element_type:
            return jsonify({'error': 'type is required'}), 400
        
        results = []
        
        if element_type == 'keynote':
            query = """
                SELECT note_id as id, 
                       CONCAT(COALESCE(note_title, ''), ' - ', LEFT(note_text, 100)) as name,
                       note_title,
                       note_text
                FROM standard_notes
                WHERE (note_title ILIKE %s OR note_text ILIKE %s)
                ORDER BY note_title, note_text
                LIMIT 20
            """
            search_pattern = f'%{query_str}%'
            results = execute_query(query, (search_pattern, search_pattern))
            
        elif element_type == 'block':
            query = """
                SELECT block_id as id,
                       CONCAT(block_name, ' - ', COALESCE(description, '')) as name,
                       block_name,
                       description
                FROM block_definitions
                WHERE (block_name ILIKE %s OR description ILIKE %s)
                  AND is_active = TRUE
                ORDER BY block_name
                LIMIT 20
            """
            search_pattern = f'%{query_str}%'
            results = execute_query(query, (search_pattern, search_pattern))
            
        elif element_type == 'detail':
            query = """
                SELECT detail_id as id,
                       CONCAT(COALESCE(detail_number, ''), ' - ', COALESCE(detail_title, '')) as name,
                       detail_number,
                       detail_title,
                       description
                FROM detail_standards
                WHERE (detail_number ILIKE %s OR detail_title ILIKE %s OR description ILIKE %s)
                ORDER BY detail_number, detail_title
                LIMIT 20
            """
            search_pattern = f'%{query_str}%'
            results = execute_query(query, (search_pattern, search_pattern, search_pattern))
            
        elif element_type == 'hatch':
            query = """
                SELECT hatch_id as id,
                       CONCAT(pattern_name, ' - ', COALESCE(description, '')) as name,
                       pattern_name,
                       description
                FROM hatch_patterns
                WHERE (pattern_name ILIKE %s OR description ILIKE %s)
                  AND (is_active IS NULL OR is_active = TRUE)
                ORDER BY pattern_name
                LIMIT 20
            """
            search_pattern = f'%{query_str}%'
            results = execute_query(query, (search_pattern, search_pattern))
            
        elif element_type == 'material':
            query = """
                SELECT material_id as id,
                       CONCAT(material_name, ' - ', COALESCE(description, '')) as name,
                       material_name,
                       description
                FROM material_standards
                WHERE (material_name ILIKE %s OR description ILIKE %s)
                ORDER BY material_name
                LIMIT 20
            """
            search_pattern = f'%{query_str}%'
            results = execute_query(query, (search_pattern, search_pattern))
        else:
            return jsonify({'error': 'Invalid element type'}), 400
        
        return jsonify({'results': results})
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
    """Import DXF file into database - with optional pattern-based classification"""
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
        pattern_id = request.form.get('pattern_id')  # Optional import pattern
        
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join('/tmp', f'{uuid.uuid4()}_{filename}')
        file.save(temp_path)
        
        try:
            # If pattern_id is provided, use intelligent object creation
            # NOTE: Currently the DXFImporter uses its own pattern matching logic
            # The selected pattern_id serves as a hint but automatic detection is used
            use_intelligent = pattern_id is not None
            
            # Import DXF with intelligent object creation enabled
            importer = DXFImporter(DB_CONFIG, create_intelligent_objects=use_intelligent)
            stats = importer.import_dxf(
                temp_path,
                drawing_id,
                import_modelspace=import_modelspace,
                import_paperspace=import_paperspace
            )
            
            # Add pattern matching info if pattern was selected
            pattern_info = None
            if pattern_id and use_intelligent:
                # Get selected pattern details
                pattern_query = "SELECT client_name, source_pattern, confidence_score FROM import_mapping_patterns WHERE mapping_id = %s"
                pattern_result = execute_query(pattern_query, (pattern_id,))
                
                if pattern_result:
                    pattern = pattern_result[0]
                    # Get actual stats from import
                    total_layers = len(stats.get('layers', set()))
                    matched = stats.get('intelligent_objects_created', 0)
                    
                    pattern_info = {
                        'pattern_name': f"{pattern['client_name']} - {pattern['source_pattern']}",
                        'matched_count': matched,
                        'unmatched_count': max(0, total_layers - (1 if matched > 0 else 0)),
                        'avg_confidence': pattern['confidence_score'],
                        'note': 'Using automatic pattern detection with intelligent object creation'
                    }
            
            response_data = {
                'success': len(stats['errors']) == 0,
                'stats': stats
            }
            
            if pattern_info:
                response_data['pattern_info'] = pattern_info
            
            return jsonify(response_data)
        
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
    """Get available database layers (user's PostGIS data) - optionally filtered by CAD standards"""
    try:
        # Get filter parameters from query string
        disciplines = request.args.getlist('disciplines')
        categories = request.args.getlist('categories')
        phases = request.args.getlist('phases')
        
        has_filters = len(disciplines) > 0 or len(categories) > 0 or len(phases) > 0
        
        # Define the database layers that contain geospatial data
        db_layers = [
            {
                'id': 'survey_points',
                'name': 'Survey Points',
                'table': 'survey_points',
                'geom_column': 'geometry',
                'geom_type': 'Point',
                'enabled': True,
                'description': 'Survey control points and topo shots',
                'has_layer_name': True
            },
            {
                'id': 'utility_lines',
                'name': 'Utility Lines',
                'table': 'utility_lines',
                'geom_column': 'geometry',
                'geom_type': 'LineString',
                'enabled': True,
                'description': 'Water, sewer, storm, electric, gas lines',
                'has_layer_name': True
            },
            {
                'id': 'utility_structures',
                'name': 'Utility Structures',
                'table': 'utility_structures',
                'geom_column': 'geometry',
                'geom_type': 'Point',
                'enabled': True,
                'description': 'Manholes, valves, meters, structures',
                'has_layer_name': True
            },
            {
                'id': 'parcels',
                'name': 'Parcels',
                'table': 'parcels',
                'geom_column': 'geometry',
                'geom_type': 'Polygon',
                'enabled': True,
                'description': 'Property parcel boundaries',
                'has_layer_name': False
            },
            {
                'id': 'horizontal_alignments',
                'name': 'Alignments',
                'table': 'horizontal_alignments',
                'geom_column': 'geometry',
                'geom_type': 'LineString',
                'enabled': True,
                'description': 'Horizontal centerline alignments',
                'has_layer_name': True
            },
            {
                'id': 'surface_features',
                'name': 'Surface Features',
                'table': 'surface_features',
                'geom_column': 'geometry',
                'geom_type': 'Mixed',
                'enabled': True,
                'description': 'General site features (points, lines, polygons)',
                'has_layer_name': True
            },
            {
                'id': 'drawing_entities',
                'name': 'CAD Entities',
                'table': 'drawing_entities',
                'geom_column': 'geometry',
                'geom_type': 'Mixed',
                'enabled': True,
                'description': 'Lines, polylines, arcs, circles from CAD drawings',
                'has_layer_name': True
            }
        ]
        
        # Check which tables actually exist and have data
        available_layers = []
        for layer in db_layers:
            try:
                # Build count query with optional standards filter
                if has_filters and layer.get('has_layer_name'):
                    # Check if table has layer_name column and filter by standards
                    filter_conditions = []
                    if disciplines:
                        disc_pattern = '|'.join([f'^{d}-' for d in disciplines])
                        filter_conditions.append(f"layer_name ~ '{disc_pattern}'")
                    if categories:
                        cat_pattern = '|'.join([f'-{c}-' for c in categories])
                        filter_conditions.append(f"layer_name ~ '{cat_pattern}'")
                    if phases:
                        phase_pattern = '|'.join([f'-{p}-' for p in phases])
                        filter_conditions.append(f"layer_name ~ '{phase_pattern}'")
                    
                    where_clause = " OR ".join(filter_conditions) if filter_conditions else "1=1"
                    count_query = f"SELECT COUNT(*) as count FROM {layer['table']} WHERE {where_clause}"
                else:
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

# ============================================
# IMPORT TEMPLATE MANAGER API ENDPOINTS
# ============================================

@app.route('/api/import-templates', methods=['GET'])
def get_import_templates():
    """Get all import mapping patterns with full details"""
    try:
        query = """
            SELECT 
                m.mapping_id, m.client_name, m.source_pattern,
                m.regex_pattern, m.extraction_rules, m.confidence_score,
                m.is_active, m.created_at, m.updated_at,
                d.code as discipline_code, d.full_name as discipline_name,
                c.code as category_code, c.full_name as category_name,
                t.code as type_code, t.full_name as type_name
            FROM import_mapping_patterns m
            LEFT JOIN discipline_codes d ON m.target_discipline_id = d.discipline_id
            LEFT JOIN category_codes c ON m.target_category_id = c.category_id
            LEFT JOIN object_type_codes t ON m.target_type_id = t.type_id
            ORDER BY m.confidence_score DESC, m.client_name, m.source_pattern
        """
        patterns = execute_query(query)
        return jsonify({'patterns': patterns})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/import-templates/<int:mapping_id>', methods=['GET'])
def get_import_template(mapping_id):
    """Get a single import mapping pattern by ID"""
    try:
        query = """
            SELECT 
                m.mapping_id, m.client_name, m.source_pattern,
                m.regex_pattern, m.extraction_rules, m.confidence_score,
                m.is_active, m.created_at, m.updated_at,
                m.target_discipline_id, m.target_category_id, m.target_type_id,
                d.code as discipline_code, d.full_name as discipline_name,
                c.code as category_code, c.full_name as category_name,
                t.code as type_code, t.full_name as type_name
            FROM import_mapping_patterns m
            LEFT JOIN discipline_codes d ON m.target_discipline_id = d.discipline_id
            LEFT JOIN category_codes c ON m.target_category_id = c.category_id
            LEFT JOIN object_type_codes t ON m.target_type_id = t.type_id
            WHERE m.mapping_id = %s
        """
        result = execute_query(query, (mapping_id,))
        if result:
            return jsonify({'pattern': result[0]})
        else:
            return jsonify({'error': 'Pattern not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/import-templates', methods=['POST'])
def create_import_template():
    """Create a new import mapping pattern"""
    try:
        data = request.get_json()
        
        # Get IDs for vocabulary codes if provided
        discipline_id = None
        category_id = None
        type_id = None
        
        if data.get('discipline_code'):
            result = execute_query(
                "SELECT discipline_id FROM discipline_codes WHERE code = %s",
                (data['discipline_code'],)
            )
            if result:
                discipline_id = result[0]['discipline_id']
        
        if data.get('category_code') and discipline_id:
            result = execute_query(
                "SELECT category_id FROM category_codes WHERE code = %s AND discipline_id = %s",
                (data['category_code'], discipline_id)
            )
            if result:
                category_id = result[0]['category_id']
        
        if data.get('type_code') and category_id:
            result = execute_query(
                "SELECT type_id FROM object_type_codes WHERE code = %s AND category_id = %s",
                (data['type_code'], category_id)
            )
            if result:
                type_id = result[0]['type_id']
        
        query = """
            INSERT INTO import_mapping_patterns
            (client_name, source_pattern, regex_pattern, extraction_rules,
             target_discipline_id, target_category_id, target_type_id, confidence_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING mapping_id
        """
        
        params = (
            data['client_name'],
            data['source_pattern'],
            data['regex_pattern'],
            json.dumps(data.get('extraction_rules', {})),
            discipline_id,
            category_id,
            type_id,
            data.get('confidence_score', 80)
        )
        
        result = execute_query(query, params)
        if result:
            return jsonify({'mapping_id': result[0]['mapping_id'], 'message': 'Pattern created successfully'}), 201
        else:
            return jsonify({'error': 'Failed to create pattern'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/import-templates/<int:mapping_id>', methods=['PUT'])
def update_import_template(mapping_id):
    """Update an existing import mapping pattern"""
    try:
        data = request.get_json()
        
        # Get IDs for vocabulary codes if provided
        discipline_id = None
        category_id = None
        type_id = None
        
        if data.get('discipline_code'):
            result = execute_query(
                "SELECT discipline_id FROM discipline_codes WHERE code = %s",
                (data['discipline_code'],)
            )
            if result:
                discipline_id = result[0]['discipline_id']
        
        if data.get('category_code') and discipline_id:
            result = execute_query(
                "SELECT category_id FROM category_codes WHERE code = %s AND discipline_id = %s",
                (data['category_code'], discipline_id)
            )
            if result:
                category_id = result[0]['category_id']
        
        if data.get('type_code') and category_id:
            result = execute_query(
                "SELECT type_id FROM object_type_codes WHERE code = %s AND category_id = %s",
                (data['type_code'], category_id)
            )
            if result:
                type_id = result[0]['type_id']
        
        query = """
            UPDATE import_mapping_patterns
            SET client_name = %s,
                source_pattern = %s,
                regex_pattern = %s,
                extraction_rules = %s,
                target_discipline_id = %s,
                target_category_id = %s,
                target_type_id = %s,
                confidence_score = %s,
                is_active = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE mapping_id = %s
        """
        
        params = (
            data['client_name'],
            data['source_pattern'],
            data['regex_pattern'],
            json.dumps(data.get('extraction_rules', {})),
            discipline_id,
            category_id,
            type_id,
            data.get('confidence_score', 80),
            data.get('is_active', True),
            mapping_id
        )
        
        execute_query(query, params, fetch=False)
        return jsonify({'message': 'Pattern updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/import-templates/<int:mapping_id>', methods=['DELETE'])
def delete_import_template(mapping_id):
    """Delete an import mapping pattern"""
    try:
        query = "DELETE FROM import_mapping_patterns WHERE mapping_id = %s"
        execute_query(query, (mapping_id,), fetch=False)
        return jsonify({'message': 'Pattern deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/import-templates/test', methods=['POST'])
def test_import_template():
    """Test a regex pattern against layer names"""
    try:
        data = request.get_json()
        regex_pattern = data.get('regex_pattern')
        test_names = data.get('test_names', [])
        extraction_rules = data.get('extraction_rules', {})
        
        import re
        results = []
        
        for layer_name in test_names:
            try:
                match = re.match(regex_pattern, layer_name, re.IGNORECASE)
                if match:
                    groups = match.groupdict()
                    results.append({
                        'layer_name': layer_name,
                        'matched': True,
                        'groups': groups,
                        'full_match': match.group(0)
                    })
                else:
                    results.append({
                        'layer_name': layer_name,
                        'matched': False
                    })
            except re.error as e:
                return jsonify({'error': f'Invalid regex: {str(e)}'}), 400
        
        return jsonify({'results': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# BULK VOCABULARY EDITOR API ENDPOINTS
# ============================================

@app.route('/api/vocabulary/disciplines', methods=['POST'])
def create_discipline():
    """Create a new discipline code"""
    try:
        data = request.get_json()
        query = """
            INSERT INTO discipline_codes (code, full_name, description, sort_order)
            VALUES (%s, %s, %s, %s)
            RETURNING discipline_id
        """
        result = execute_query(query, (data['code'], data['full_name'], data.get('description'), data.get('sort_order', 100)))
        return jsonify({'discipline_id': result[0]['discipline_id'], 'message': 'Discipline created'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vocabulary/disciplines/<int:discipline_id>', methods=['PUT'])
def update_discipline(discipline_id):
    """Update a discipline code"""
    try:
        data = request.get_json()
        query = """
            UPDATE discipline_codes 
            SET code = %s, full_name = %s, description = %s, sort_order = %s, is_active = %s
            WHERE discipline_id = %s
        """
        execute_query(query, (data['code'], data['full_name'], data.get('description'), data.get('sort_order', 100), data.get('is_active', True), discipline_id), fetch=False)
        return jsonify({'message': 'Discipline updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vocabulary/disciplines/<int:discipline_id>', methods=['DELETE'])
def delete_discipline(discipline_id):
    """Delete a discipline code"""
    try:
        execute_query("DELETE FROM discipline_codes WHERE discipline_id = %s", (discipline_id,), fetch=False)
        return jsonify({'message': 'Discipline deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vocabulary/categories', methods=['POST'])
def create_category():
    """Create a new category code"""
    try:
        data = request.get_json()
        query = """
            INSERT INTO category_codes (discipline_id, code, full_name, description, sort_order)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING category_id
        """
        result = execute_query(query, (data['discipline_id'], data['code'], data['full_name'], data.get('description'), data.get('sort_order', 100)))
        return jsonify({'category_id': result[0]['category_id'], 'message': 'Category created'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vocabulary/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    """Update a category code"""
    try:
        data = request.get_json()
        query = """
            UPDATE category_codes 
            SET code = %s, full_name = %s, description = %s, sort_order = %s, is_active = %s
            WHERE category_id = %s
        """
        execute_query(query, (data['code'], data['full_name'], data.get('description'), data.get('sort_order', 100), data.get('is_active', True), category_id), fetch=False)
        return jsonify({'message': 'Category updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vocabulary/categories/<int:category_id>', methods={'DELETE'})
def delete_category(category_id):
    """Delete a category code"""
    try:
        execute_query("DELETE FROM category_codes WHERE category_id = %s", (category_id,), fetch=False)
        return jsonify({'message': 'Category deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vocabulary/object-types', methods=['POST'])
def create_object_type():
    """Create a new object type code"""
    try:
        data = request.get_json()
        query = """
            INSERT INTO object_type_codes (category_id, code, full_name, description, database_table, sort_order)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING type_id
        """
        result = execute_query(query, (data['category_id'], data['code'], data['full_name'], data.get('description'), data.get('database_table'), data.get('sort_order', 100)))
        return jsonify({'type_id': result[0]['type_id'], 'message': 'Object type created'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vocabulary/object-types/<int:type_id>', methods=['PUT'])
def update_object_type(type_id):
    """Update an object type code"""
    try:
        data = request.get_json()
        query = """
            UPDATE object_type_codes 
            SET code = %s, full_name = %s, description = %s, database_table = %s, sort_order = %s, is_active = %s
            WHERE type_id = %s
        """
        execute_query(query, (data['code'], data['full_name'], data.get('description'), data.get('database_table'), data.get('sort_order', 100), data.get('is_active', True), type_id), fetch=False)
        return jsonify({'message': 'Object type updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vocabulary/object-types/<int:type_id>', methods=['DELETE'])
def delete_object_type(type_id):
    """Delete an object type code"""
    try:
        execute_query("DELETE FROM object_type_codes WHERE type_id = %s", (type_id,), fetch=False)
        return jsonify({'message': 'Object type deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vocabulary/phases', methods=['POST'])
def create_phase():
    """Create a new phase code"""
    try:
        data = request.get_json()
        query = """
            INSERT INTO phase_codes (code, full_name, description, color_rgb, sort_order)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING phase_id
        """
        result = execute_query(query, (data['code'], data['full_name'], data.get('description'), data.get('color_rgb'), data.get('sort_order', 100)))
        return jsonify({'phase_id': result[0]['phase_id'], 'message': 'Phase created'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vocabulary/phases/<int:phase_id>', methods=['PUT'])
def update_phase(phase_id):
    """Update a phase code"""
    try:
        data = request.get_json()
        query = """
            UPDATE phase_codes 
            SET code = %s, full_name = %s, description = %s, color_rgb = %s, sort_order = %s, is_active = %s
            WHERE phase_id = %s
        """
        execute_query(query, (data['code'], data['full_name'], data.get('description'), data.get('color_rgb'), data.get('sort_order', 100), data.get('is_active', True), phase_id), fetch=False)
        return jsonify({'message': 'Phase updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vocabulary/phases/<int:phase_id>', methods=['DELETE'])
def delete_phase(phase_id):
    """Delete a phase code"""
    try:
        execute_query("DELETE FROM phase_codes WHERE phase_id = %s", (phase_id,), fetch=False)
        return jsonify({'message': 'Phase deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vocabulary/geometries', methods=['POST'])
def create_geometry():
    """Create a new geometry code"""
    try:
        data = request.get_json()
        query = """
            INSERT INTO geometry_codes (code, full_name, description, dxf_entity_types, sort_order)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING geometry_id
        """
        result = execute_query(query, (data['code'], data['full_name'], data.get('description'), data.get('dxf_entity_types'), data.get('sort_order', 100)))
        return jsonify({'geometry_id': result[0]['geometry_id'], 'message': 'Geometry created'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vocabulary/geometries/<int:geometry_id>', methods=['PUT'])
def update_geometry(geometry_id):
    """Update a geometry code"""
    try:
        data = request.get_json()
        query = """
            UPDATE geometry_codes 
            SET code = %s, full_name = %s, description = %s, dxf_entity_types = %s, sort_order = %s, is_active = %s
            WHERE geometry_id = %s
        """
        execute_query(query, (data['code'], data['full_name'], data.get('description'), data.get('dxf_entity_types'), data.get('sort_order', 100), data.get('is_active', True), geometry_id), fetch=False)
        return jsonify({'message': 'Geometry updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vocabulary/geometries/<int:geometry_id>', methods=['DELETE'])
def delete_geometry(geometry_id):
    """Delete a geometry code"""
    try:
        execute_query("DELETE FROM geometry_codes WHERE geometry_id = %s", (geometry_id,), fetch=False)
        return jsonify({'message': 'Geometry deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vocabulary/attributes')
def get_attributes():
    """Get all attribute codes"""
    try:
        query = """
            SELECT attribute_id, code, full_name, attribute_category, description, pattern, is_active
            FROM attribute_codes
            WHERE is_active = TRUE
            ORDER BY attribute_category, code
        """
        attributes = execute_query(query)
        return jsonify({'attributes': attributes})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vocabulary/attributes', methods=['POST'])
def create_attribute():
    """Create a new attribute code"""
    try:
        data = request.get_json()
        query = """
            INSERT INTO attribute_codes (code, full_name, attribute_category, description, pattern)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING attribute_id
        """
        result = execute_query(query, (data['code'], data['full_name'], data.get('attribute_category'), data.get('description'), data.get('pattern')))
        return jsonify({'attribute_id': result[0]['attribute_id'], 'message': 'Attribute created'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vocabulary/attributes/<int:attribute_id>', methods=['PUT'])
def update_attribute(attribute_id):
    """Update an attribute code"""
    try:
        data = request.get_json()
        query = """
            UPDATE attribute_codes 
            SET code = %s, full_name = %s, attribute_category = %s, description = %s, pattern = %s, is_active = %s
            WHERE attribute_id = %s
        """
        execute_query(query, (data['code'], data['full_name'], data.get('attribute_category'), data.get('description'), data.get('pattern'), data.get('is_active', True), attribute_id), fetch=False)
        return jsonify({'message': 'Attribute updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vocabulary/attributes/<int:attribute_id>', methods=['DELETE'])
def delete_attribute(attribute_id):
    """Delete an attribute code"""
    try:
        execute_query("DELETE FROM attribute_codes WHERE attribute_id = %s", (attribute_id,), fetch=False)
        return jsonify({'message': 'Attribute deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
