"""
Survey Codes Blueprint
Handles survey code management, parsing, validation, and batch processing
Extracted from app.py during Phase 13 refactoring
"""
from flask import Blueprint, render_template, jsonify, request, send_file, make_response, Response
from typing import Dict, List, Any, Optional
import csv
import io
import os
import uuid
from werkzeug.utils import secure_filename
from database import get_db, execute_query
from app.extensions import cache

survey_codes_bp = Blueprint('survey_codes', __name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_db_config() -> Dict[str, str]:
    """
    Build database configuration dictionary for legacy parser classes.
    This recreates the DB_CONFIG format that parser classes expect.
    """
    return {
        'host': os.getenv('PGHOST') or os.getenv('DB_HOST'),
        'port': os.getenv('PGPORT') or os.getenv('DB_PORT', '5432'),
        'database': os.getenv('PGDATABASE') or os.getenv('DB_NAME', 'postgres'),
        'user': os.getenv('PGUSER') or os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('PGPASSWORD') or os.getenv('DB_PASSWORD')
    }

# ============================================================================
# PAGE ROUTES
# ============================================================================

@survey_codes_bp.route('/tools/survey-codes')
def survey_codes_manager():
    """Survey Code Library Manager - CRUD interface for field survey codes"""
    return render_template('tools/survey_codes.html')

@survey_codes_bp.route('/tools/survey-code-tester')
def survey_code_tester():
    """Survey Code Testing Interface - Test parsing, preview CAD output, simulate field shots"""
    return render_template('tools/survey_code_tester.html')

# ============================================================================
# SURVEY CODE LIBRARY API
# ============================================================================

@survey_codes_bp.route('/api/survey-codes')
def get_survey_codes():
    """Get all survey codes with optional filtering"""
    try:
        discipline = request.args.get('discipline')
        category = request.args.get('category')
        connectivity = request.args.get('connectivity')
        category_group = request.args.get('category_group')
        favorites_only = request.args.get('favorites_only') == 'true'
        search = request.args.get('search', '').strip()

        where_clauses = ['is_active = TRUE']
        params = []

        if discipline:
            where_clauses.append('discipline_code = %s')
            params.append(discipline)

        if category:
            where_clauses.append('category_code = %s')
            params.append(category)

        if connectivity:
            where_clauses.append('connectivity_type = %s')
            params.append(connectivity)

        if category_group:
            where_clauses.append('category_group = %s')
            params.append(category_group)

        if favorites_only:
            where_clauses.append('is_favorite = TRUE')

        if search:
            where_clauses.append('(code ILIKE %s OR display_name ILIKE %s OR description ILIKE %s)')
            search_pattern = f'%{search}%'
            params.extend([search_pattern, search_pattern, search_pattern])

        where_sql = ' AND '.join(where_clauses)

        query = f"""
            SELECT code_id, code, display_name, description, discipline_code, category_code,
                   feature_type, icon_name, connectivity_type, geometry_output, auto_connect,
                   create_block, block_name, available_attributes, default_attributes,
                   required_attributes, layer_template, default_phase, category_group,
                   sort_order, is_favorite, usage_count, last_used_at, quality_score,
                   tags, attributes, created_at, updated_at
            FROM survey_code_library
            WHERE {where_sql}
            ORDER BY is_favorite DESC, sort_order, display_name
        """

        codes = execute_query(query, tuple(params))
        return jsonify({'survey_codes': codes, 'count': len(codes)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@survey_codes_bp.route('/api/survey-codes/<uuid:code_id>')
def get_survey_code_detail(code_id):
    """Get a specific survey code"""
    try:
        query = """
            SELECT code_id, code, display_name, description, discipline_code, category_code,
                   feature_type, icon_name, connectivity_type, geometry_output, auto_connect,
                   create_block, block_name, available_attributes, default_attributes,
                   required_attributes, layer_template, default_phase, category_group,
                   sort_order, is_favorite, usage_count, last_used_at, quality_score,
                   tags, attributes, created_at, updated_at
            FROM survey_code_library
            WHERE code_id = %s
        """
        result = execute_query(query, (str(code_id),))

        if not result:
            return jsonify({'error': 'Survey code not found'}), 404

        return jsonify(result[0])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@survey_codes_bp.route('/api/survey-codes', methods=['POST'])
def create_survey_code():
    """Create a new survey code"""
    try:
        data = request.get_json()

        if not data.get('code') or not data.get('display_name'):
            return jsonify({'error': 'code and display_name are required'}), 400

        if not data.get('feature_type'):
            return jsonify({'error': 'feature_type is required'}), 400

        check_query = "SELECT code_id FROM survey_code_library WHERE code = %s"
        existing = execute_query(check_query, (data['code'].strip(),))
        if existing:
            return jsonify({'error': f'Code {data["code"]} already exists'}), 409

        query = """
            INSERT INTO survey_code_library (
                code, display_name, description, discipline_code, category_code, feature_type,
                icon_name, connectivity_type, geometry_output, auto_connect, create_block,
                block_name, available_attributes, default_attributes, required_attributes,
                layer_template, default_phase, category_group, sort_order, is_favorite,
                tags, attributes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING code_id, code, display_name, connectivity_type, is_favorite, created_at
        """

        result = execute_query(query, (
            data['code'].strip().upper(),
            data['display_name'].strip(),
            data.get('description', '').strip() or None,
            data.get('discipline_code', '').strip() or None,
            data.get('category_code', '').strip() or None,
            data['feature_type'].strip(),
            data.get('icon_name', '').strip() or None,
            data.get('connectivity_type', 'POINT'),
            data.get('geometry_output', '').strip() or None,
            data.get('auto_connect', False),
            data.get('create_block', False),
            data.get('block_name', '').strip() or None,
            data.get('available_attributes', []),
            data.get('default_attributes', {}),
            data.get('required_attributes', []),
            data.get('layer_template', '').strip() or None,
            data.get('default_phase', 'EXIST'),
            data.get('category_group', '').strip() or None,
            data.get('sort_order', 0),
            data.get('is_favorite', False),
            data.get('tags', []),
            data.get('attributes', {})
        ))

        return jsonify({
            'survey_code': result[0],
            'message': f'Survey code {data["code"]} created successfully'
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@survey_codes_bp.route('/api/survey-codes/<uuid:code_id>', methods=['PUT'])
def update_survey_code(code_id):
    """Update a survey code"""
    try:
        data = request.get_json()

        if not data.get('code') or not data.get('display_name'):
            return jsonify({'error': 'code and display_name are required'}), 400

        check_query = """
            SELECT code_id FROM survey_code_library
            WHERE code = %s AND code_id != %s
        """
        existing = execute_query(check_query, (data['code'].strip(), str(code_id)))
        if existing:
            return jsonify({'error': f'Code {data["code"]} already exists'}), 409

        query = """
            UPDATE survey_code_library
            SET code = %s, display_name = %s, description = %s, discipline_code = %s,
                category_code = %s, feature_type = %s, icon_name = %s, connectivity_type = %s,
                geometry_output = %s, auto_connect = %s, create_block = %s, block_name = %s,
                available_attributes = %s, default_attributes = %s, required_attributes = %s,
                layer_template = %s, default_phase = %s, category_group = %s, sort_order = %s,
                is_favorite = %s, tags = %s, attributes = %s, updated_at = CURRENT_TIMESTAMP
            WHERE code_id = %s
            RETURNING code_id, code, display_name, connectivity_type, is_favorite, updated_at
        """

        result = execute_query(query, (
            data['code'].strip().upper(),
            data['display_name'].strip(),
            data.get('description', '').strip() or None,
            data.get('discipline_code', '').strip() or None,
            data.get('category_code', '').strip() or None,
            data['feature_type'].strip(),
            data.get('icon_name', '').strip() or None,
            data.get('connectivity_type', 'POINT'),
            data.get('geometry_output', '').strip() or None,
            data.get('auto_connect', False),
            data.get('create_block', False),
            data.get('block_name', '').strip() or None,
            data.get('available_attributes', []),
            data.get('default_attributes', {}),
            data.get('required_attributes', []),
            data.get('layer_template', '').strip() or None,
            data.get('default_phase', 'EXIST'),
            data.get('category_group', '').strip() or None,
            data.get('sort_order', 0),
            data.get('is_favorite', False),
            data.get('tags', []),
            data.get('attributes', {}),
            str(code_id)
        ))

        if not result:
            return jsonify({'error': 'Survey code not found'}), 404

        return jsonify({
            'survey_code': result[0],
            'message': 'Survey code updated successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@survey_codes_bp.route('/api/survey-codes/<uuid:code_id>', methods=['DELETE'])
def delete_survey_code(code_id):
    """Delete a survey code (soft delete)"""
    try:
        query = "UPDATE survey_code_library SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP WHERE code_id = %s RETURNING code_id, code"
        result = execute_query(query, (str(code_id),))

        if not result:
            return jsonify({'error': 'Survey code not found'}), 404

        return jsonify({
            'message': f'Survey code {result[0]["code"]} deactivated successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@survey_codes_bp.route('/api/survey-codes/<uuid:code_id>/favorite', methods=['POST'])
def toggle_survey_code_favorite(code_id):
    """Toggle favorite status of a survey code"""
    try:
        data = request.get_json()
        is_favorite = data.get('is_favorite', False)

        query = """
            UPDATE survey_code_library
            SET is_favorite = %s, updated_at = CURRENT_TIMESTAMP
            WHERE code_id = %s
            RETURNING code_id, code, display_name, is_favorite
        """

        result = execute_query(query, (is_favorite, str(code_id)))

        if not result:
            return jsonify({'error': 'Survey code not found'}), 404

        return jsonify({
            'survey_code': result[0],
            'message': f'Survey code favorite status updated'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@survey_codes_bp.route('/api/survey-codes/export')
def export_survey_codes_csv():
    """Export survey codes to CSV for data collector import"""
    try:
        query = """
            SELECT code, display_name, description, discipline_code, category_code,
                   feature_type, connectivity_type, geometry_output, category_group,
                   auto_connect, create_block, block_name, layer_template, default_phase,
                   is_favorite, usage_count
            FROM survey_code_library
            WHERE is_active = TRUE
            ORDER BY is_favorite DESC, category_group, sort_order, display_name
        """

        codes = execute_query(query)

        # Create CSV in memory
        si = io.StringIO()
        writer = csv.writer(si)

        # Write header
        writer.writerow([
            'Code', 'Display Name', 'Description', 'Discipline', 'Category',
            'Feature Type', 'Connectivity', 'Geometry', 'Group',
            'Auto-Connect', 'Create Block', 'Block Name', 'Layer Template', 'Phase',
            'Favorite', 'Usage Count'
        ])

        # Write data rows
        for code in codes:
            writer.writerow([
                code.get('code', ''),
                code.get('display_name', ''),
                code.get('description', ''),
                code.get('discipline_code', ''),
                code.get('category_code', ''),
                code.get('feature_type', ''),
                code.get('connectivity_type', ''),
                code.get('geometry_output', ''),
                code.get('category_group', ''),
                'Yes' if code.get('auto_connect') else 'No',
                'Yes' if code.get('create_block') else 'No',
                code.get('block_name', ''),
                code.get('layer_template', ''),
                code.get('default_phase', ''),
                'Yes' if code.get('is_favorite') else 'No',
                code.get('usage_count', 0)
            ])

        # Create response
        output = make_response(si.getvalue())
        output.headers['Content-Type'] = 'text/csv'
        output.headers['Content-Disposition'] = 'attachment; filename=survey_codes_library.csv'

        return output
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# SURVEY CODE TESTING/PARSING API
# ============================================================================

@survey_codes_bp.route('/api/survey-codes/parse', methods=['POST'])
def parse_survey_code():
    """Parse a single survey code and return all properties"""
    from survey_code_parser import SurveyCodeParser

    try:
        data = request.get_json()
        code = data.get('code', '').strip()
        phase = data.get('phase')

        if not code:
            return jsonify({'error': 'code is required'}), 400

        parser = SurveyCodeParser(_get_db_config())
        parsed = parser.parse_code(code)

        if parsed.get('valid'):
            layer_name = parser.resolve_layer_name(parsed, phase)
            parsed['layer_name'] = layer_name

        return jsonify(parsed)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@survey_codes_bp.route('/api/survey-codes/simulate', methods=['POST'])
def simulate_field_sequence():
    """Simulate a sequence of field shots and determine connectivity"""
    from survey_code_parser import SurveyCodeParser

    try:
        data = request.get_json()
        shots = data.get('shots', [])

        if not shots:
            return jsonify({'error': 'shots array is required'}), 400

        parser = SurveyCodeParser(_get_db_config())
        result = parser.simulate_field_sequence(shots)

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# BATCH VALIDATION
# ============================================================================

# In-memory cache for batch validation results
batch_results_cache: Dict[str, Dict[str, Any]] = {}

def process_batch_validation(codes: List[str]) -> Dict[str, Any]:
    """Shared helper for batch validation logic"""
    from survey_code_parser import SurveyCodeParser

    parser = SurveyCodeParser(_get_db_config())
    result = parser.batch_validate(codes)

    results_token = str(uuid.uuid4())
    batch_results_cache[results_token] = result

    result['results_token'] = results_token
    return result

@survey_codes_bp.route('/api/survey-codes/batch-validate', methods=['POST'])
def batch_validate_codes():
    """Validate multiple codes at once (manual entry)"""
    try:
        data = request.get_json()
        codes = data.get('codes', [])

        if not codes:
            return jsonify({'error': 'codes array is required'}), 400

        if len(codes) > 5000:
            return jsonify({'error': 'Maximum 5,000 codes allowed per batch'}), 400

        result = process_batch_validation(codes)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@survey_codes_bp.route('/api/survey-codes/batch-validate-upload', methods=['POST'])
def batch_validate_upload():
    """Validate codes from uploaded CSV file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']

        if not file or not file.filename:
            return jsonify({'error': 'No file uploaded'}), 400

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not file.filename.endswith(('.csv', '.txt')):
            return jsonify({'error': 'File must be CSV or TXT format'}), 400

        content = file.read()

        if len(content) > 2 * 1024 * 1024:
            return jsonify({'error': 'File size exceeds 2 MB limit'}), 400

        content_str = content.decode('utf-8-sig')

        reader = csv.reader(io.StringIO(content_str))
        codes = []

        for row_num, row in enumerate(reader, start=1):
            if row and row[0].strip():
                code = row[0].strip()
                if not code.startswith('#'):
                    codes.append(code)

            if len(codes) > 5000:
                return jsonify({'error': 'File contains more than 5,000 codes'}), 400

        if not codes:
            return jsonify({'error': 'No valid codes found in file'}), 400

        result = process_batch_validation(codes)
        result['filename'] = secure_filename(file.filename)
        result['codes_extracted'] = len(codes)

        return jsonify(result)
    except UnicodeDecodeError:
        return jsonify({'error': 'File encoding error. Please use UTF-8 encoded CSV'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@survey_codes_bp.route('/api/survey-codes/batch-validate-download/<token>')
def batch_validate_download(token):
    """Download batch validation results as CSV"""
    try:
        if token not in batch_results_cache:
            return jsonify({'error': 'Results not found or expired'}), 404

        data = batch_results_cache[token]

        si = io.StringIO()
        writer = csv.writer(si, quoting=csv.QUOTE_MINIMAL)

        writer.writerow(['Code', 'Valid', 'Display Name', 'Error Message'])

        for result in data.get('results', []):
            if result.get('valid'):
                writer.writerow([
                    result.get('code', ''),
                    'TRUE',
                    result.get('display_name', '').replace('\n', ' ').replace('\r', ''),
                    ''
                ])
            else:
                error_msg = result.get('error', '').replace('\n', ' ').replace('\r', '')
                code_from_error = error_msg.split('"')[1] if '"' in error_msg else 'Unknown'
                writer.writerow([
                    code_from_error,
                    'FALSE',
                    '',
                    error_msg
                ])

        output = make_response(si.getvalue())
        output.headers['Content-Type'] = 'text/csv'
        output.headers['Content-Disposition'] = 'attachment; filename=batch_validation_results.csv'

        return output
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@survey_codes_bp.route('/api/survey-codes/connectivity-rules')
def get_connectivity_rules():
    """Get documentation for connectivity types"""
    from survey_code_parser import SurveyCodeParser

    try:
        parser = SurveyCodeParser(_get_db_config())
        rules = parser.get_connectivity_rules()
        return jsonify(rules)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
