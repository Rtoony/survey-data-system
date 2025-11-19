"""
Details Management Blueprint
Handles detail standards, mappings, and import/export operations
Extracted from app.py during Phase 13 refactoring
"""
from flask import Blueprint, render_template, jsonify, request, send_file
import csv
import io
from typing import Tuple, Any, Dict, List, Optional

from database import get_db, execute_query
from app.extensions import cache

details_bp = Blueprint('details', __name__)

# ============================================================================
# DETAILS MANAGER PAGE ROUTE
# ============================================================================

@details_bp.route('/data-manager/details')
def details_manager() -> str:
    """Render the Details Manager page"""
    return render_template('data_manager/details.html')

# ============================================================================
# DETAILS MANAGER API ENDPOINTS
# ============================================================================

@details_bp.route('/api/data-manager/details', methods=['GET'])
def get_details() -> Tuple[Any, int]:
    """Get all details"""
    try:
        query = """
            SELECT detail_id, detail_number, detail_title, detail_category,
                   description, usage_context
            FROM detail_standards
            ORDER BY detail_category, detail_number
        """
        details = execute_query(query)
        return jsonify({'details': details})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@details_bp.route('/api/data-manager/details', methods=['POST'])
def create_detail() -> Tuple[Any, int]:
    """Create a new detail"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400

        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO detail_standards
                    (detail_number, detail_title, detail_category, description, usage_context)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING detail_id
                """, (
                    data.get('detail_number'),
                    data.get('detail_title'),
                    data.get('detail_category'),
                    data.get('description'),
                    data.get('usage_context')
                ))
                detail_id = cur.fetchone()[0]
                conn.commit()

        cache.clear()
        return jsonify({'detail_id': detail_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@details_bp.route('/api/data-manager/details/<detail_id>', methods=['PUT'])
def update_detail(detail_id: str) -> Tuple[Any, int]:
    """Update an existing detail"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400

        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE detail_standards
                    SET detail_number = %s, detail_title = %s, detail_category = %s,
                        description = %s, usage_context = %s
                    WHERE detail_id = %s
                """, (
                    data.get('detail_number'),
                    data.get('detail_title'),
                    data.get('detail_category'),
                    data.get('description'),
                    data.get('usage_context'),
                    detail_id
                ))
                conn.commit()

        cache.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@details_bp.route('/api/data-manager/details/<detail_id>', methods=['DELETE'])
def delete_detail(detail_id: str) -> Tuple[Any, int]:
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

@details_bp.route('/api/data-manager/details/import-csv', methods=['POST'])
def import_details_csv() -> Tuple[Any, int]:
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
                            SET detail_title = %s, detail_category = %s, description = %s
                            WHERE detail_id = %s
                        """, (detail_title, category, description, existing[0]))
                        updated_count += 1
                    else:
                        # Insert new record
                        cur.execute("""
                            INSERT INTO detail_standards (detail_number, detail_title, detail_category, description)
                            VALUES (%s, %s, %s, %s)
                        """, (detail_number, detail_title, category, description))
                        imported_count += 1

                conn.commit()

        cache.clear()
        return jsonify({
            'imported': imported_count,
            'updated': updated_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@details_bp.route('/api/data-manager/details/export-csv', methods=['GET'])
def export_details_csv() -> Any:
    """Export details to CSV file"""
    try:
        query = """
            SELECT detail_number, detail_title, detail_category, description
            FROM detail_standards
            ORDER BY detail_category, detail_number
        """
        data = execute_query(query)

        # Create CSV in memory
        output = io.StringIO()
        if data:
            fieldnames = ['Detail_Number', 'Detail_Title', 'Category', 'Description']
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()

            for row in data:
                writer.writerow({
                    'Detail_Number': row.get('detail_number', ''),
                    'Detail_Title': row.get('detail_title', ''),
                    'Category': row.get('detail_category', ''),
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
# DETAIL NAME MAPPINGS CRUD MANAGER
# ============================================================================

@details_bp.route('/data-manager/detail-mappings')
def detail_mappings_manager() -> str:
    """Render the Detail Name Mappings Manager page"""
    return render_template('data_manager/detail_mappings.html')

@details_bp.route('/api/data-manager/detail-mappings', methods=['GET'])
def get_detail_mappings_crud() -> Tuple[Any, int]:
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

@details_bp.route('/api/data-manager/detail-mappings', methods=['POST'])
def create_detail_mapping() -> Tuple[Any, int]:
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

@details_bp.route('/api/data-manager/detail-mappings/<mapping_id>', methods=['PUT'])
def update_detail_mapping(mapping_id: str) -> Tuple[Any, int]:
    """Update an existing detail mapping"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400
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

@details_bp.route('/api/data-manager/detail-mappings/<mapping_id>', methods=['DELETE'])
def delete_detail_mapping(mapping_id: str) -> Tuple[Any, int]:
    """Delete a detail mapping"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM detail_name_mappings WHERE mapping_id = %s", (mapping_id,))
                conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
