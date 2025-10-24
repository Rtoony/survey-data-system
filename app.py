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

# Load environment variables (works with both .env file and Replit secrets)
load_dotenv()

app = Flask(__name__)
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
    """Get database connection"""
    conn = psycopg2.connect(**DB_CONFIG)
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
        return jsonify(projects)
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
