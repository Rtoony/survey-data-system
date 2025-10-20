"""
ACAD-GIS Schema Explorer & Data Manager
A companion tool for viewing and managing your Supabase database
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from contextlib import contextmanager

# Load environment variables (works with both .env file and Replit secrets)
load_dotenv()

app = Flask(__name__)
CORS(app)

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

# ============================================
# CAD STANDARDS API ENDPOINTS
# ============================================

@app.route('/api/standards/overview')
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
