"""
ACAD-GIS Schema Explorer & Data Manager
A companion tool for viewing and managing your Supabase database
"""

from flask import Flask, render_template, jsonify, request, send_file
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
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'postgres'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD'),
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
        project_name = data.get('project_name')
        client_name = data.get('client_name')

        if not project_name:
            return jsonify({'error': 'project_name is required'}), 400

        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO projects (project_name, client_name)
                    VALUES (%s, %s)
                    RETURNING project_id, project_name, client_name, created_at
                    """,
                    (project_name, client_name)
                )
                result = cur.fetchone()
                conn.commit()
                
                return jsonify({
                    'project_id': str(result[0]),
                    'project_name': result[1],
                    'client_name': result[2],
                    'created_at': result[3].isoformat() if result[3] else None
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

@app.route('/api/drawings')
def get_drawings():
    """Get all drawings"""
    try:
        query = """
            SELECT 
                d.*,
                p.project_name,
                p.project_number,
                CASE 
                    WHEN d.dxf_content IS NOT NULL THEN true 
                    ELSE false 
                END as has_content
            FROM drawings d
            LEFT JOIN projects p ON d.project_id = p.project_id
            ORDER BY d.created_at DESC
            LIMIT 500
        """
        drawings = execute_query(query)
        return jsonify(drawings)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/drawings', methods=['POST'])
def create_drawing():
    """Create a new drawing"""
    try:
        data = request.get_json()
        drawing_name = data.get('drawing_name')
        drawing_number = data.get('drawing_number')
        project_id = data.get('project_id')
        cad_units = data.get('cad_units', 'Feet')
        scale_factor = data.get('scale_factor', 1.0)

        if not drawing_name:
            return jsonify({'error': 'drawing_name is required'}), 400

        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO drawings (drawing_name, drawing_number, project_id, cad_units, scale_factor)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING drawing_id, drawing_name, drawing_number, project_id, created_at
                    """,
                    (drawing_name, drawing_number, project_id if project_id else None, cad_units, scale_factor)
                )
                result = cur.fetchone()
                conn.commit()
                
                return jsonify({
                    'drawing_id': str(result[0]),
                    'drawing_name': result[1],
                    'drawing_number': result[2],
                    'project_id': str(result[3]) if result[3] else None,
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
            'linetypes': 'linetype_standards',
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
                pattern,
                dxf_pattern,
                scale_factor,
                usage_context
            FROM linetype_standards
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
    """Get export job history"""
    try:
        query = """
            SELECT 
                ej.export_job_id,
                ej.drawing_id,
                d.drawing_name,
                ej.export_format,
                ej.dxf_version,
                ej.status,
                ej.metrics,
                ej.started_at,
                ej.completed_at
            FROM export_jobs ej
            LEFT JOIN drawings d ON ej.drawing_id = d.drawing_id
            ORDER BY ej.started_at DESC
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
    """Map Viewer Page"""
    return render_template('map_viewer_simple.html')

@app.route('/map-test')
def map_test_page():
    """Simple Map Test Page (no base template)"""
    return render_template('map_viewer_simple.html')

@app.route('/api/map-viewer/layers')
def get_gis_layers():
    """Get available GIS layers"""
    try:
        query = "SELECT * FROM gis_layers WHERE enabled = true ORDER BY name"
        layers = execute_query(query)
        return jsonify({'layers': layers})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/map-viewer/projects')
def get_map_projects():
    """Get all projects with spatial data for map display"""
    try:
        # Query all drawings with their projects
        query = """
            SELECT 
                d.drawing_id,
                d.drawing_name,
                d.drawing_number,
                d.is_georeferenced,
                d.drawing_epsg_code,
                d.drawing_coordinate_system,
                d.created_at,
                p.project_id,
                p.project_name,
                p.client_name
            FROM drawings d
            JOIN projects p ON d.project_id = p.project_id
            ORDER BY d.created_at DESC
        """
        
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                drawings = cur.fetchall()
        
        features = []
        for drawing in drawings:
            # Get block inserts to calculate bounds
            insert_query = """
                SELECT insert_x, insert_y 
                FROM block_inserts 
                WHERE drawing_id = %s 
                LIMIT 10000
            """
            with get_db() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(insert_query, (drawing['drawing_id'],))
                    inserts = cur.fetchall()
            
            if not inserts:
                continue
                
            # Calculate bounds
            min_x = min_y = float('inf')
            max_x = max_y = float('-inf')
            
            for insert in inserts:
                if insert['insert_x'] is not None:
                    min_x = min(min_x, insert['insert_x'])
                    max_x = max(max_x, insert['insert_x'])
                if insert['insert_y'] is not None:
                    min_y = min(min_y, insert['insert_y'])
                    max_y = max(max_y, insert['insert_y'])
            
            # Skip if no valid coordinates
            if min_x == float('inf'):
                continue
            
            # Create GeoJSON feature (assume EPSG:2226 for now)
            # Convert State Plane to WGS84 for Leaflet display
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [[
                        [min_x, min_y],
                        [max_x, min_y],
                        [max_x, max_y],
                        [min_x, max_y],
                        [min_x, min_y]
                    ]]
                },
                'properties': {
                    'drawing_id': str(drawing['drawing_id']),
                    'drawing_name': drawing['drawing_name'],
                    'drawing_number': drawing['drawing_number'],
                    'project_id': str(drawing['project_id']),
                    'project_name': drawing['project_name'],
                    'client_name': drawing['client_name'],
                    'epsg_code': drawing['drawing_epsg_code'] or 'EPSG:2226',
                    'is_georeferenced': drawing['is_georeferenced'],
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
        return jsonify({'error': str(e)}), 500

@app.route('/api/map-export/create', methods=['POST'])
def create_export_job():
    """Create a new export job"""
    try:
        params = request.json
        print(f"Received export request with params: {params}")
        job_id = str(uuid.uuid4())
        
        # Insert job record - let database generate ID
        query = """
            INSERT INTO public.export_jobs (status, params, created_at)
            VALUES ('pending', %s::jsonb, NOW())
            RETURNING id, status, created_at
        """
        print(f"Attempting to insert job")
        try:
            with get_db() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    print(f"Executing query: {query}")
                    print(f"With params: {json.dumps(params)[:200]}")
                    cur.execute(query, (json.dumps(params),))
                    result = dict(cur.fetchone())
            job_id = str(result['id'])
            print(f"Job created successfully with id: {job_id}")
        except Exception as e:
            print(f"Database insert error: {e}")
            raise
        
        # Process export in background thread
        def process_export():
            try:
                # Update status to processing
                with get_db() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "UPDATE export_jobs SET status = 'processing' WHERE id = %s",
                            (job_id,)
                        )
                
                # Create export package
                export_result = map_export.create_export_package(job_id, params)
                
                update_query = """
                    UPDATE export_jobs
                    SET status = %s,
                        download_url = %s,
                        file_size_mb = %s,
                        error_message = %s,
                        expires_at = %s
                    WHERE id = %s
                """
                with get_db() as conn:
                    with conn.cursor() as cur:
                        cur.execute(update_query, (
                            export_result['status'],
                            export_result.get('download_url'),
                            export_result.get('file_size_mb'),
                            export_result.get('error_message'),
                            export_result.get('expires_at'),
                            job_id
                        ))
            except Exception as e:
                print(f"Export processing error: {e}")
                with get_db() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "UPDATE export_jobs SET status = 'failed', error_message = %s WHERE id = %s",
                            (str(e), job_id)
                        )
        
        thread = threading.Thread(target=process_export)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'job_id': str(result['id']),
            'status': result['status'],
            'created_at': result['created_at'].isoformat()
        })
        
    except Exception as e:
        print(f"ERROR in create_export_job: {e}")
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
            FROM export_jobs
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
