"""
Blocks Management Blueprint
Handles block definitions, mappings, and batch import operations
Extracted from app.py during Phase 13 refactoring
"""
from flask import Blueprint, render_template, jsonify, request, send_file, redirect, url_for
import csv
import io
import os
import tempfile
from typing import Dict, List, Any
from werkzeug.utils import secure_filename

from database import get_db, execute_query, DB_CONFIG
from app.extensions import cache

blocks_bp = Blueprint('blocks', __name__)

# ============================================================================
# PAGE ROUTES
# ============================================================================

@blocks_bp.route('/data-manager/blocks')
def blocks_manager():
    """Render the Blocks Manager page"""
    return render_template('data_manager/blocks.html')

@blocks_bp.route('/tools/batch-block-import')
def batch_block_import_tool_redirect():
    """Legacy redirect - Batch Block Import Tool"""
    return redirect(url_for('batch_cad_import_tool'))

@blocks_bp.route('/data-manager/block-mappings')
def block_mappings_manager():
    """Render the Block Name Mappings Manager page"""
    return render_template('data_manager/block_mappings.html')

# ============================================================================
# BLOCK DEFINITIONS CRUD API ENDPOINTS
# ============================================================================

@blocks_bp.route('/api/data-manager/blocks', methods=['GET'])
def get_blocks():
    """Get all blocks"""
    try:
        query = """
            SELECT block_id, block_name, block_type, category, description,
                   svg_content, preview_image_path
            FROM block_definitions
            ORDER BY category, block_name
        """
        blocks = execute_query(query)
        return jsonify({'blocks': blocks})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@blocks_bp.route('/api/data-manager/blocks', methods=['POST'])
def create_block():
    """Create a new block"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400

        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO block_definitions
                    (block_name, category, block_type, description)
                    VALUES (%s, %s, %s, %s)
                    RETURNING block_id
                """, (
                    data.get('block_name'),
                    data.get('category'),
                    data.get('block_type'),
                    data.get('description')
                ))
                block_id = cur.fetchone()[0]
                conn.commit()

        cache.clear()
        return jsonify({'block_id': block_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@blocks_bp.route('/api/data-manager/blocks/<block_id>', methods=['PUT'])
def update_block(block_id: str):
    """Update an existing block"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400

        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE block_definitions
                    SET block_name = %s, category = %s, block_type = %s, description = %s
                    WHERE block_id = %s
                """, (
                    data.get('block_name'),
                    data.get('category'),
                    data.get('block_type'),
                    data.get('description'),
                    block_id
                ))
                conn.commit()

        cache.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@blocks_bp.route('/api/data-manager/blocks/<block_id>', methods=['DELETE'])
def delete_block(block_id: str):
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

@blocks_bp.route('/api/data-manager/blocks/import-csv', methods=['POST'])
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
                    # CSV: Block_Name, Category, Block_Type, Description
                    # DB: block_name, category, block_type, description

                    block_name = row.get('Block_Name', '').strip()
                    category = row.get('Category', '').strip()
                    block_type = row.get('Block_Type', '').strip()
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
                            SET category = %s, block_type = %s, description = %s
                            WHERE block_id = %s
                        """, (category, block_type, description, existing[0]))
                        updated_count += 1
                    else:
                        # Insert new record
                        cur.execute("""
                            INSERT INTO block_definitions (block_name, category, block_type, description)
                            VALUES (%s, %s, %s, %s)
                        """, (block_name, category, block_type, description))
                        imported_count += 1

                conn.commit()

        cache.clear()
        return jsonify({
            'imported': imported_count,
            'updated': updated_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@blocks_bp.route('/api/data-manager/blocks/export-csv', methods=['GET'])
def export_blocks_csv():
    """Export blocks to CSV file"""
    try:
        query = """
            SELECT block_name, category, block_type, description
            FROM block_definitions
            ORDER BY category, block_name
        """
        data = execute_query(query)

        # Create CSV in memory
        output = io.StringIO()
        if data:
            fieldnames = ['Block_Name', 'Category', 'Block_Type', 'Description']
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()

            for row in data:
                writer.writerow({
                    'Block_Name': row.get('block_name', ''),
                    'Category': row.get('category', ''),
                    'Block_Type': row.get('block_type', ''),
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
# BATCH BLOCK IMPORT FROM DXF FILES
# ============================================================================

@blocks_bp.route('/api/batch-block-import/extract-from-dxf', methods=['POST'])
def extract_blocks_from_dxf():
    """Extract block definitions from uploaded DXF files"""
    try:
        if 'files[]' not in request.files:
            return jsonify({'error': 'No files provided'}), 400

        files = request.files.getlist('files[]')
        if not files or len(files) == 0:
            return jsonify({'error': 'No files selected'}), 400

        import ezdxf
        from batch_block_extractor import BatchBlockExtractor

        extractor = BatchBlockExtractor(DB_CONFIG)
        extracted_blocks = []
        errors = []

        for file in files:
            if not file or not file.filename:
                continue

            if file.filename == '':
                continue

            if not file.filename.lower().endswith('.dxf'):
                errors.append(f"{file.filename}: Not a DXF file")
                continue

            try:
                temp_path = os.path.join(tempfile.gettempdir(), secure_filename(file.filename))
                file.save(temp_path)

                blocks = extractor.extract_blocks_from_file(temp_path, file.filename)
                extracted_blocks.extend(blocks)

                os.remove(temp_path)

            except Exception as e:
                errors.append(f"{file.filename}: {str(e)}")

        return jsonify({
            'blocks': extracted_blocks,
            'total_files': len(files),
            'total_blocks': len(extracted_blocks),
            'errors': errors,
            'valid_categories': extractor.get_valid_categories()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@blocks_bp.route('/api/batch-block-import/save-blocks', methods=['POST'])
def save_extracted_blocks():
    """Save extracted blocks to the database"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400

        blocks = data.get('blocks', [])

        if not blocks:
            return jsonify({'error': 'No blocks provided'}), 400

        imported_count = 0
        updated_count = 0
        skipped_count = 0

        with get_db() as conn:
            with conn.cursor() as cur:
                for block in blocks:
                    action = block.get('action', 'skip')
                    if action == 'skip':
                        skipped_count += 1
                        continue

                    block_name = block.get('name')
                    category = block.get('category', '')
                    description = block.get('description', '')
                    svg_content = block.get('svg_preview', '')

                    cur.execute("""
                        SELECT block_id FROM block_definitions
                        WHERE LOWER(block_name) = LOWER(%s)
                    """, (block_name,))

                    existing = cur.fetchone()

                    if action == 'update' and existing:
                        cur.execute("""
                            UPDATE block_definitions
                            SET category = %s, description = %s, svg_content = %s,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE block_id = %s
                        """, (category, description, svg_content, existing[0]))
                        updated_count += 1

                    elif action == 'import' and not existing:
                        cur.execute("""
                            INSERT INTO block_definitions
                            (block_name, category, description, svg_content, is_active)
                            VALUES (%s, %s, %s, %s, TRUE)
                        """, (block_name, category, description, svg_content))
                        imported_count += 1
                    else:
                        skipped_count += 1

                conn.commit()

        cache.clear()
        return jsonify({
            'imported': imported_count,
            'updated': updated_count,
            'skipped': skipped_count
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# UNIFIED BATCH CAD IMPORT ROUTES (Blocks, Details, Hatches, Linetypes)
# ============================================================================

@blocks_bp.route('/api/batch-cad-import/extract', methods=['POST'])
def extract_cad_elements():
    """Extract CAD elements (blocks, details, hatches, linetypes) from uploaded DXF files"""
    try:
        import_type = request.form.get('import_type', 'blocks')

        if 'files[]' not in request.files:
            return jsonify({'error': 'No files provided'}), 400

        files = request.files.getlist('files[]')
        if not files or len(files) == 0:
            return jsonify({'error': 'No files selected'}), 400

        from batch_cad_extractor import BatchCADExtractor

        extractor = BatchCADExtractor(DB_CONFIG)
        extracted_elements = []
        errors = []

        for file in files:
            if not file or not file.filename:
                continue

            if file.filename == '':
                continue

            if not file.filename.lower().endswith('.dxf'):
                errors.append(f"{file.filename}: Not a DXF file")
                continue

            try:
                temp_path = os.path.join(tempfile.gettempdir(), secure_filename(file.filename))
                file.save(temp_path)

                elements = extractor.extract_from_file(temp_path, file.filename, import_type)
                extracted_elements.extend(elements)

                os.remove(temp_path)

            except Exception as e:
                errors.append(f"{file.filename}: {str(e)}")

        metadata = extractor.get_metadata(import_type)

        return jsonify({
            'elements': extracted_elements,
            'total_files': len(files),
            'total_elements': len(extracted_elements),
            'errors': errors,
            'import_type': import_type,
            'metadata': metadata
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@blocks_bp.route('/api/batch-cad-import/save', methods=['POST'])
def save_cad_elements():
    """Save extracted CAD elements to appropriate database tables"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400

        import_type = data.get('import_type', 'blocks')
        elements = data.get('elements', [])

        if not elements:
            return jsonify({'error': 'No elements provided'}), 400

        # Dispatch to appropriate save handler
        save_handlers = {
            'blocks': _save_blocks,
            'details': _save_details,
            'hatches': _save_hatches,
            'linetypes': _save_linetypes
        }

        if import_type not in save_handlers:
            return jsonify({'error': f'Invalid import type: {import_type}'}), 400

        result = save_handlers[import_type](elements)
        cache.clear()
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# HELPER FUNCTIONS FOR BATCH CAD IMPORT
# ============================================================================

def _save_blocks(elements: List[Dict[str, Any]]) -> Dict[str, int]:
    """Save blocks to block_definitions table"""
    imported_count = 0
    updated_count = 0
    skipped_count = 0

    with get_db() as conn:
        with conn.cursor() as cur:
            for elem in elements:
                action = elem.get('action', 'skip')
                if action == 'skip':
                    skipped_count += 1
                    continue

                name = elem.get('name')
                category = elem.get('category', '')
                description = elem.get('description', '')
                svg_content = elem.get('svg_preview', '')

                cur.execute("""
                    SELECT block_id FROM block_definitions
                    WHERE LOWER(block_name) = LOWER(%s)
                """, (name,))

                existing = cur.fetchone()

                if action == 'update' and existing:
                    cur.execute("""
                        UPDATE block_definitions
                        SET category = %s, description = %s, svg_content = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE block_id = %s
                    """, (category, description, svg_content, existing[0]))
                    updated_count += 1

                elif action == 'import' and not existing:
                    cur.execute("""
                        INSERT INTO block_definitions
                        (block_name, category, description, svg_content, is_active)
                        VALUES (%s, %s, %s, %s, TRUE)
                    """, (name, category, description, svg_content))
                    imported_count += 1
                else:
                    skipped_count += 1

            conn.commit()

    return {
        'imported': imported_count,
        'updated': updated_count,
        'skipped': skipped_count
    }

def _save_details(elements: List[Dict[str, Any]]) -> Dict[str, int]:
    """Save details to detail_standards table"""
    imported_count = 0
    updated_count = 0
    skipped_count = 0

    with get_db() as conn:
        with conn.cursor() as cur:
            for elem in elements:
                action = elem.get('action', 'skip')
                if action == 'skip':
                    skipped_count += 1
                    continue

                name = elem.get('name')
                detail_category = elem.get('detail_category', '')
                discipline = elem.get('discipline', '')
                description = elem.get('description', '')
                svg_content = elem.get('svg_preview', '')

                cur.execute("""
                    SELECT detail_id FROM detail_standards
                    WHERE LOWER(detail_number) = LOWER(%s)
                """, (name,))

                existing = cur.fetchone()

                if action == 'update' and existing:
                    cur.execute("""
                        UPDATE detail_standards
                        SET detail_category = %s, discipline = %s,
                            description = %s, svg_content = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE detail_id = %s
                    """, (detail_category, discipline, description, svg_content, existing[0]))
                    updated_count += 1

                elif action == 'import' and not existing:
                    cur.execute("""
                        INSERT INTO detail_standards
                        (detail_number, detail_category, discipline, description, svg_content)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (name, detail_category, discipline, description, svg_content))
                    imported_count += 1
                else:
                    skipped_count += 1

            conn.commit()

    return {
        'imported': imported_count,
        'updated': updated_count,
        'skipped': skipped_count
    }

def _save_hatches(elements: List[Dict[str, Any]]) -> Dict[str, int]:
    """Save hatches to hatch_patterns table"""
    imported_count = 0
    updated_count = 0
    skipped_count = 0

    with get_db() as conn:
        with conn.cursor() as cur:
            for elem in elements:
                action = elem.get('action', 'skip')
                if action == 'skip':
                    skipped_count += 1
                    continue

                name = elem.get('name')
                pattern_type = elem.get('pattern_type', 'User-defined')
                description = elem.get('description', '')

                cur.execute("""
                    SELECT hatch_id FROM hatch_patterns
                    WHERE LOWER(pattern_name) = LOWER(%s)
                """, (name,))

                existing = cur.fetchone()

                if action == 'update' and existing:
                    cur.execute("""
                        UPDATE hatch_patterns
                        SET pattern_type = %s, description = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE hatch_id = %s
                    """, (pattern_type, description, existing[0]))
                    updated_count += 1

                elif action == 'import' and not existing:
                    cur.execute("""
                        INSERT INTO hatch_patterns
                        (pattern_name, pattern_type, description, is_active)
                        VALUES (%s, %s, %s, TRUE)
                    """, (name, pattern_type, description))
                    imported_count += 1
                else:
                    skipped_count += 1

            conn.commit()

    return {
        'imported': imported_count,
        'updated': updated_count,
        'skipped': skipped_count
    }

def _save_linetypes(elements: List[Dict[str, Any]]) -> Dict[str, int]:
    """Save linetypes to linetypes table"""
    imported_count = 0
    updated_count = 0
    skipped_count = 0

    with get_db() as conn:
        with conn.cursor() as cur:
            for elem in elements:
                action = elem.get('action', 'skip')
                if action == 'skip':
                    skipped_count += 1
                    continue

                name = elem.get('name')
                description = elem.get('description', '')
                pattern_definition = elem.get('pattern_definition', '')

                cur.execute("""
                    SELECT linetype_id FROM linetypes
                    WHERE LOWER(linetype_name) = LOWER(%s)
                """, (name,))

                existing = cur.fetchone()

                if action == 'update' and existing:
                    cur.execute("""
                        UPDATE linetypes
                        SET description = %s, pattern_definition = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE linetype_id = %s
                    """, (description, pattern_definition, existing[0]))
                    updated_count += 1

                elif action == 'import' and not existing:
                    cur.execute("""
                        INSERT INTO linetypes
                        (linetype_name, description, pattern_definition, is_active)
                        VALUES (%s, %s, %s, TRUE)
                    """, (name, description, pattern_definition))
                    imported_count += 1
                else:
                    skipped_count += 1

            conn.commit()

    return {
        'imported': imported_count,
        'updated': updated_count,
        'skipped': skipped_count
    }

# ============================================================================
# BLOCK NAME MAPPINGS CRUD MANAGER
# ============================================================================

@blocks_bp.route('/api/data-manager/block-mappings', methods=['GET'])
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

@blocks_bp.route('/api/data-manager/block-mappings', methods=['POST'])
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

@blocks_bp.route('/api/data-manager/block-mappings/<mapping_id>', methods=['PUT'])
def update_block_mapping(mapping_id: str):
    """Update an existing block mapping"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400
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

@blocks_bp.route('/api/data-manager/block-mappings/<mapping_id>', methods=['DELETE'])
def delete_block_mapping(mapping_id: str):
    """Delete a block mapping"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM block_name_mappings WHERE mapping_id = %s", (mapping_id,))
                conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
