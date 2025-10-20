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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
