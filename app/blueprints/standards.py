"""
Standards Blueprint
Handles all routes related to Standards, Vocabulary, and Attribute Codes
"""

from flask import Blueprint, render_template, jsonify, request
from app.extensions import cache
from database import execute_query

# Create Blueprint
standards_bp = Blueprint('standards', __name__)

# ============================================
# HELPER FUNCTIONS
# ============================================

def invalidate_classifier_cache():
    """Reload LayerClassifierV3 cache after vocabulary changes"""
    try:
        from standards.layer_classifier_v3 import LayerClassifierV3
        classifier = LayerClassifierV3()
        classifier.reload_codes()
    except Exception as e:
        print(f"Warning: Failed to reload classifier cache: {e}")

# ============================================
# PAGE ROUTES - Standards Management Pages
# ============================================

@standards_bp.route('/standards/layers')
def standards_layers():
    """Layer standards page"""
    return render_template('standards/layers.html')

@standards_bp.route('/standards/blocks')
def standards_blocks():
    """Block/symbol standards page"""
    return render_template('standards/blocks.html')

@standards_bp.route('/standards/colors')
def standards_colors():
    """Color standards page"""
    return render_template('standards/colors.html')

@standards_bp.route('/standards/linetypes')
def standards_linetypes():
    """Linetype standards page"""
    return render_template('standards/linetypes.html')

@standards_bp.route('/standards/text')
def standards_text():
    """Text style standards page"""
    return render_template('standards/text.html')

@standards_bp.route('/standards/hatches')
def standards_hatches():
    """Hatch pattern standards page"""
    return render_template('standards/hatches.html')

@standards_bp.route('/standards/details')
def standards_details():
    """Detail standards page"""
    return render_template('standards/details.html')

@standards_bp.route('/standards/abbreviations')
def standards_abbreviations():
    """Abbreviation standards page"""
    return render_template('standards/abbreviations.html')

@standards_bp.route('/standards/materials')
def standards_materials():
    """Material standards page"""
    return render_template('standards/materials.html')

@standards_bp.route('/standards/vocabulary')
def standards_vocabulary():
    """CAD Standards Vocabulary browser page"""
    return render_template('standards/vocabulary.html')

@standards_bp.route('/standards/layer-vocabulary')
def standards_layer_vocabulary():
    """CAD Layer Vocabulary - layer naming classification system"""
    return render_template('standards/layer-vocabulary.html')

@standards_bp.route('/standards/reference-data')
def standards_reference_data():
    """Reference Data Hub - system configuration and reference tables"""
    return render_template('standards/reference-data.html')

@standards_bp.route('/standards/reference')
def standards_reference():
    """CAD Standards Layer Reference - visual layer examples"""
    return render_template('standards/reference.html')

@standards_bp.route('/standards/sheets')
def standards_sheets():
    """Sheet template standards page"""
    return render_template('standards/sheets.html')

@standards_bp.route('/standards/plotstyles')
def standards_plotstyles():
    """Plot style standards page"""
    return render_template('standards/plotstyles.html')

@standards_bp.route('/standards/viewports')
def standards_viewports():
    """Viewport standards page"""
    return render_template('standards/viewports.html')

@standards_bp.route('/standards/annotations')
def standards_annotations():
    """Annotation standards page"""
    return render_template('standards/annotations.html')

@standards_bp.route('/standards/categories')
def standards_categories():
    """Symbol categories page"""
    return render_template('standards/categories.html')

@standards_bp.route('/standards/codes')
def standards_codes():
    """Code references page"""
    return render_template('standards/codes.html')

@standards_bp.route('/standards/notes')
def standards_notes():
    """Standard notes page"""
    return render_template('standards/notes.html')

@standards_bp.route('/standards/scales')
def standards_scales():
    """Drawing scale standards page"""
    return render_template('standards/scales.html')

@standards_bp.route('/standards/import-manager')
def standards_import_manager():
    """Import Template Manager page"""
    return render_template('standards/import_manager.html')

@standards_bp.route('/standards/bulk-editor')
def standards_bulk_editor():
    """Bulk Standards Editor page"""
    return render_template('standards/bulk_editor.html')

@standards_bp.route('/standards/specifications')
def standards_specifications():
    """Specifications Library - browse and manage organizational spec library"""
    return render_template('standards/specifications.html')

@standards_bp.route('/standards/spec-geometry-links')
def standards_spec_geometry_links():
    """Spec-Geometry Link Visualizer - view and manage spec-entity relationships"""
    return render_template('standards/spec_geometry_viewer.html')

@standards_bp.route('/standards/layer-generator')
def layer_generator():
    """Render the CAD Layer Generator page"""
    return render_template('layer_generator.html')

# ============================================
# API ENDPOINTS - Standards Data
# ============================================

@standards_bp.route('/api/standards/overview')
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

@standards_bp.route('/api/standards/layers')
@cache.cached(timeout=600)  # Cache for 10 minutes
def get_layer_standards():
    """Get all layer standards"""
    try:
        query = """
            SELECT
                layer_id,
                layer_name,
                discipline,
                category,
                color,
                color_rgb,
                aci_color,
                linetype,
                lineweight,
                description,
                usage_notes,
                tags,
                is_active,
                is_deprecated
            FROM layer_standards
            WHERE is_active = true OR is_active IS NULL
            ORDER BY discipline, category, layer_name
        """
        layers = execute_query(query)
        return jsonify(layers)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@standards_bp.route('/api/standards/blocks')
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
                description,
                has_attributes,
                is_dynamic,
                tags,
                dxf_file_path,
                preview_image_path,
                is_active
            FROM block_definitions
            WHERE is_active = true OR is_active IS NULL
            ORDER BY category, block_name
        """
        blocks = execute_query(query)
        return jsonify(blocks)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@standards_bp.route('/api/standards/colors')
@cache.cached(timeout=600)  # Cache for 10 minutes
def get_color_standards():
    """Get all color standards"""
    try:
        query = """
            SELECT
                color_id,
                color_name,
                aci_number,
                rgb_value,
                hex_value,
                cmyk_value,
                usage_context,
                description,
                discipline,
                is_active
            FROM color_standards
            WHERE is_active = true OR is_active IS NULL
            ORDER BY aci_number
        """
        colors = execute_query(query)
        return jsonify(colors)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@standards_bp.route('/api/standards/linetypes')
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

@standards_bp.route('/api/standards/text')
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
                description,
                usage_context,
                discipline,
                is_active
            FROM text_styles
            WHERE is_active = true OR is_active IS NULL
            ORDER BY style_name
        """
        text_styles = execute_query(query)
        return jsonify(text_styles)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@standards_bp.route('/api/standards/hatches')
@cache.cached(timeout=600)  # Cache for 10 minutes
def get_hatch_standards():
    """Get all hatch pattern standards"""
    try:
        query = """
            SELECT
                hatch_id,
                pattern_name,
                pattern_type,
                pattern_definition,
                description,
                usage_context,
                pat_file_path,
                preview_image_path,
                is_active
            FROM hatch_patterns
            WHERE is_active = true OR is_active IS NULL
            ORDER BY pattern_name
        """
        hatches = execute_query(query)
        return jsonify(hatches)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@standards_bp.route('/api/standards/details')
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

@standards_bp.route('/api/standards/abbreviations')
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

@standards_bp.route('/api/standards/materials')
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

@standards_bp.route('/api/standards/sheets')
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

@standards_bp.route('/api/standards/plotstyles')
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

@standards_bp.route('/api/standards/viewports')
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

@standards_bp.route('/api/standards/annotations')
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

@standards_bp.route('/api/standards/categories')
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

@standards_bp.route('/api/standards/codes')
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

@standards_bp.route('/api/standards/notes')
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

@standards_bp.route('/api/standards/scales')
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
# ATTRIBUTE CODES API ENDPOINTS
# ============================================

@standards_bp.route('/api/standards/attributes', methods=['GET'])
def get_attribute_codes():
    """Get all attribute codes"""
    try:
        query = """
            SELECT attribute_id, code, full_name, attribute_category, attribute_type,
                   description, pattern, is_locked, is_active, sort_order, created_at, updated_at
            FROM attribute_codes
            WHERE is_active = TRUE
            ORDER BY attribute_category, sort_order, code
        """
        attributes = execute_query(query)
        return jsonify({'attributes': attributes})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@standards_bp.route('/api/standards/attributes', methods=['POST'])
def create_attribute_code():
    """Create a new attribute code"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body must be JSON'}), 400

        # Validate required fields
        if 'code' not in data:
            return jsonify({'error': 'Missing required field: code'}), 400
        if 'full_name' not in data:
            return jsonify({'error': 'Missing required field: full_name'}), 400

        query = """
            INSERT INTO attribute_codes (code, full_name, attribute_category, attribute_type, description, pattern, is_locked, sort_order, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING attribute_id, code, full_name, attribute_category, attribute_type, description, pattern, is_locked, sort_order, is_active
        """
        code = data['code']
        full_name = data['full_name']
        attribute_type = data.get('attribute_type', '')
        result = execute_query(query, (
            code.strip().upper() if code else None,
            full_name.strip() if full_name else None,
            data.get('attribute_category', 'other'),
            attribute_type.strip() if attribute_type else None,
            data.get('description', ''),
            data.get('pattern', ''),
            data.get('is_locked', False),
            data.get('sort_order', 100),
            data.get('is_active', True)
        ))
        cache.clear()
        return jsonify({'success': True, 'attribute': result[0] if result else None}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@standards_bp.route('/api/standards/attributes/<int:attribute_id>', methods=['PUT'])
def update_attribute_code(attribute_id):
    """Update an attribute code"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body must be JSON'}), 400

        # Validate required fields
        if 'code' not in data:
            return jsonify({'error': 'Missing required field: code'}), 400
        if 'full_name' not in data:
            return jsonify({'error': 'Missing required field: full_name'}), 400

        query = """
            UPDATE attribute_codes
            SET code = %s, full_name = %s, attribute_category = %s, attribute_type = %s,
                description = %s, pattern = %s, is_locked = %s, sort_order = %s, is_active = %s, updated_at = CURRENT_TIMESTAMP
            WHERE attribute_id = %s
            RETURNING attribute_id, code, full_name, attribute_category, attribute_type, description, pattern, is_locked, sort_order, is_active
        """
        code = data['code']
        full_name = data['full_name']
        attribute_type = data.get('attribute_type', '')
        result = execute_query(query, (
            code.strip().upper() if code else None,
            full_name.strip() if full_name else None,
            data.get('attribute_category', 'other'),
            attribute_type.strip() if attribute_type else None,
            data.get('description', ''),
            data.get('pattern', ''),
            data.get('is_locked', False),
            data.get('sort_order', 100),
            data.get('is_active', True),
            attribute_id
        ))
        cache.clear()
        return jsonify({'success': True, 'attribute': result[0] if result else None})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@standards_bp.route('/api/standards/attributes/<int:attribute_id>', methods=['DELETE'])
def delete_attribute_code(attribute_id):
    """Soft delete an attribute code (only if not locked)"""
    try:
        # Check if attribute is locked
        check_query = "SELECT is_locked FROM attribute_codes WHERE attribute_id = %s"
        result = execute_query(check_query, (attribute_id,))

        if not result:
            return jsonify({'success': False, 'error': 'Attribute code not found'}), 404

        if result[0].get('is_locked', False):
            return jsonify({'success': False, 'error': 'Cannot delete locked attribute code'}), 403

        query = """
            UPDATE attribute_codes
            SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE attribute_id = %s
        """
        execute_query(query, (attribute_id,))
        cache.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# ATTRIBUTE APPLICABILITY API ENDPOINTS
# ============================================

@standards_bp.route('/api/standards/attribute-applicability', methods=['GET'])
def get_attribute_applicability():
    """Get attribute applicability rules with full details"""
    try:
        category_id = request.args.get('category_id', type=int)
        type_id = request.args.get('type_id', type=int)

        query = """
            SELECT
                aa.applicability_id,
                aa.category_id,
                c.code as category_code,
                c.full_name as category_name,
                aa.type_id,
                ot.code as type_code,
                ot.full_name as type_name,
                aa.attribute_id,
                a.code as attribute_code,
                a.full_name as attribute_name,
                a.attribute_category,
                aa.is_required,
                aa.sort_order,
                aa.notes,
                aa.is_active
            FROM attribute_applicability aa
            JOIN category_codes c ON aa.category_id = c.category_id
            LEFT JOIN object_type_codes ot ON aa.type_id = ot.type_id
            JOIN attribute_codes a ON aa.attribute_id = a.attribute_id
            WHERE aa.is_active = TRUE
        """

        params = []
        if category_id:
            query += " AND aa.category_id = %s"
            params.append(category_id)
        if type_id:
            query += " AND aa.type_id = %s"
            params.append(type_id)

        query += " ORDER BY c.code, ot.code NULLS FIRST, aa.sort_order, a.code"

        rules = execute_query(query, tuple(params) if params else None)
        return jsonify({'rules': rules})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@standards_bp.route('/api/standards/attribute-applicability', methods=['POST'])
def create_attribute_applicability():
    """Create a new attribute applicability rule"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body must be JSON'}), 400

        # Validate required fields
        if 'category_id' not in data:
            return jsonify({'error': 'Missing required field: category_id'}), 400
        if 'attribute_id' not in data:
            return jsonify({'error': 'Missing required field: attribute_id'}), 400

        query = """
            INSERT INTO attribute_applicability
            (category_id, type_id, attribute_id, is_required, sort_order, notes, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING applicability_id
        """
        result = execute_query(query, (
            data['category_id'],
            data.get('type_id'),  # Can be NULL
            data['attribute_id'],
            data.get('is_required', False),
            data.get('sort_order', 0),
            data.get('notes', ''),
            data.get('is_active', True)
        ))
        cache.clear()
        return jsonify({'success': True, 'applicability_id': result[0]['applicability_id'] if result else None}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@standards_bp.route('/api/standards/attribute-applicability/<int:applicability_id>', methods=['PUT'])
def update_attribute_applicability(applicability_id):
    """Update an attribute applicability rule"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body must be JSON'}), 400

        if not data.get('category_id') or not data.get('attribute_id'):
            return jsonify({'error': 'category_id and attribute_id are required'}), 400

        type_id = data.get('type_id')
        if type_id == '' or type_id is None:
            type_id = None

        query = """
            UPDATE attribute_applicability
            SET category_id = %s, type_id = %s, attribute_id = %s, is_required = %s,
                sort_order = %s, notes = %s, is_active = %s
            WHERE applicability_id = %s
            RETURNING applicability_id
        """
        result = execute_query(query, (
            data['category_id'],
            type_id,
            data['attribute_id'],
            data.get('is_required', False),
            data.get('sort_order', 0),
            data.get('notes', ''),
            data.get('is_active', True),
            applicability_id
        ))
        cache.clear()
        if result:
            return jsonify({'success': True, 'applicability_id': result[0]['applicability_id']})
        else:
            return jsonify({'error': 'Applicability rule not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@standards_bp.route('/api/standards/attribute-applicability/<int:applicability_id>', methods=['DELETE'])
def delete_attribute_applicability(applicability_id):
    """Delete an attribute applicability rule"""
    try:
        query = "DELETE FROM attribute_applicability WHERE applicability_id = %s"
        execute_query(query, (applicability_id,))
        cache.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# VOCABULARY LOOKUP API ENDPOINTS (for reclassification wizard)
# ============================================

@standards_bp.route('/api/vocabulary/disciplines', methods=['GET'])
def get_disciplines():
    """Get all discipline codes"""
    try:
        query = """
            SELECT discipline_id, code, full_name, description, sort_order
            FROM discipline_codes
            WHERE is_active = TRUE
            ORDER BY sort_order, code
        """
        disciplines = execute_query(query)
        return jsonify({'disciplines': disciplines})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@standards_bp.route('/api/vocabulary/types', methods=['GET'])
def get_types_by_category():
    """Get object types filtered by category"""
    try:
        category_id = request.args.get('category_id', type=int)

        if category_id:
            query = """
                SELECT type_id, category_id, code, full_name, description, database_table, sort_order
                FROM object_type_codes
                WHERE is_active = TRUE AND category_id = %s
                ORDER BY sort_order, code
            """
            types = execute_query(query, (category_id,))
        else:
            query = """
                SELECT type_id, category_id, code, full_name, description, database_table, sort_order
                FROM object_type_codes
                WHERE is_active = TRUE
                ORDER BY sort_order, code
            """
            types = execute_query(query)

        return jsonify({'types': types})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@standards_bp.route('/api/vocabulary/attributes', methods=['GET'])
def get_attributes_by_category_type():
    """Get applicable attributes filtered by category and type"""
    try:
        category_id = request.args.get('category_id', type=int)
        type_id = request.args.get('type_id', type=int)

        if category_id:
            query = """
                SELECT DISTINCT
                    a.attribute_id, a.code, a.full_name, a.attribute_category,
                    aa.is_required, aa.sort_order
                FROM attribute_codes a
                JOIN attribute_applicability aa ON a.attribute_id = aa.attribute_id
                WHERE a.is_active = TRUE
                  AND aa.is_active = TRUE
                  AND aa.category_id = %s
            """
            params = [category_id]

            if type_id:
                query += " AND (aa.type_id = %s OR aa.type_id IS NULL)"
                params.append(type_id)
            else:
                query += " AND aa.type_id IS NULL"

            query += " ORDER BY aa.sort_order, a.attribute_category, a.code"
            attributes = execute_query(query, tuple(params))
        else:
            query = """
                SELECT attribute_id, code, full_name, attribute_category
                FROM attribute_codes
                WHERE is_active = TRUE
                ORDER BY attribute_category, code
            """
            attributes = execute_query(query)

        return jsonify({'attributes': attributes})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@standards_bp.route('/api/vocabulary/phases', methods=['GET'])
def get_phase_codes_vocab():
    """Get all phase codes"""
    try:
        query = """
            SELECT phase_id, code, full_name, description, color_rgb, sort_order
            FROM phase_codes
            WHERE is_active = TRUE
            ORDER BY sort_order, code
        """
        phases = execute_query(query)
        return jsonify({'phases': phases})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@standards_bp.route('/api/vocabulary/geometries', methods=['GET'])
def get_geometry_codes_vocab():
    """Get all geometry codes"""
    try:
        query = """
            SELECT geometry_id, code, full_name, description, dxf_entity_types, sort_order
            FROM geometry_codes
            WHERE is_active = TRUE
            ORDER BY sort_order, code
        """
        geometries = execute_query(query)
        return jsonify({'geometries': geometries})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# VOCABULARY MANAGEMENT ENDPOINTS (full CRUD)
# ============================================

@standards_bp.route('/api/vocabulary/disciplines')
def get_vocabulary_disciplines():
    """Get all discipline codes (legacy vocabulary table)"""
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

@standards_bp.route('/api/vocabulary/categories')
def get_vocabulary_categories():
    """Get all category codes with discipline info (legacy vocabulary table)"""
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

@standards_bp.route('/api/vocabulary/object-types')
def get_object_types():
    """Get all object type codes"""
    try:
        category_id = request.args.get('category_id')

        query = """
            SELECT t.type_id, t.category_id, t.code, t.full_name, t.description, t.database_table,
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

@standards_bp.route('/api/vocabulary/phases')
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

@standards_bp.route('/api/vocabulary/geometries')
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

@standards_bp.route('/api/vocabulary/layer-patterns')
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

@standards_bp.route('/api/vocabulary/import-mappings')
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

@standards_bp.route('/api/vocabulary/layer-examples')
def get_layer_examples():
    """Generate curated layer name examples covering all geometry types"""
    try:
        # Curated catalog of examples ensuring all 8 geometry types are represented
        # Format: (discipline, category, object_type, phase, geometry, description, db_table)
        catalog = [
            # === LN (Lines) - Pipes, Alignments, Contours, Boundaries ===
            ('CIV', 'STOR', 'STORM', 'NEW', 'LN', 'New storm drain pipe', 'utility_lines'),
            ('CIV', 'STOR', 'SANIT', 'EXIST', 'LN', 'Existing sanitary sewer', 'utility_lines'),
            ('CIV', 'ROAD', 'WATER', 'PROP', 'LN', 'Proposed water main', 'utility_lines'),
            ('CIV', 'ROAD', 'RECYC', 'NEW', 'LN', 'New recycled water pipe', 'utility_lines'),
            ('CIV', 'ROAD', 'CNTR', 'EXIST', 'LN', 'Existing road centerline', 'alignments'),
            ('CIV', 'GRAD', 'CNTR', 'EXIST', 'LN', 'Existing contour line', 'contours'),
            ('SURV', 'BNDY', 'BNDY', 'EXIST', 'LN', 'Existing property boundary', 'boundaries'),
            ('SURV', 'TOPO', 'BREAK', 'EXIST', 'LN', 'Breakline', 'breaklines'),

            # === PT (Points) - Structures, Monuments, Trees ===
            ('CIV', 'STOR', 'MH', 'NEW', 'PT', 'New manhole', 'utility_structures'),
            ('CIV', 'STOR', 'CB', 'EXIST', 'PT', 'Existing catch basin', 'utility_structures'),
            ('CIV', 'STOR', 'INLET', 'PROP', 'PT', 'Proposed inlet', 'utility_structures'),
            ('CIV', 'ROAD', 'HYDRA', 'NEW', 'PT', 'New fire hydrant', 'utility_structures'),
            ('CIV', 'ROAD', 'VALVE', 'EXIST', 'PT', 'Existing water valve', 'utility_structures'),
            ('SURV', 'CTRL', 'BENCH', 'EXIST', 'PT', 'Survey benchmark', 'survey_points'),
            ('SURV', 'CTRL', 'MONUMENT', 'EXIST', 'PT', 'Survey monument', 'survey_points'),
            ('SURV', 'TOPO', 'SHOT', 'EXIST', 'PT', 'Topographic shot', 'survey_points'),
            ('LAND', 'TREE', 'OAK', 'EXIST', 'PT', 'Existing oak tree', 'site_trees'),
            ('LAND', 'TREE', 'PINE', 'PROP', 'PT', 'Proposed pine tree', 'site_trees'),

            # === PG (Polygons) - Areas, Basins, Buildings ===
            ('CIV', 'STOR', 'BASIN', 'NEW', 'PG', 'New detention basin', 'bmps'),
            ('CIV', 'STOR', 'BIORT', 'PROP', 'PG', 'Proposed bioretention area', 'bmps'),
            ('CIV', 'STOR', 'SWALE', 'NEW', 'PG', 'New bioswale', 'bmps'),
            ('CIV', 'STOR', 'POND', 'EXIST', 'PG', 'Existing retention pond', 'ponds'),
            ('CIV', 'GRAD', 'EG', 'EXIST', 'PG', 'Existing grade surface', 'surfaces'),
            ('CIV', 'GRAD', 'FG', 'PROP', 'PG', 'Proposed finished grade', 'surfaces'),
            ('CIV', 'ADA', 'RAMP', 'NEW', 'PG', 'New ADA ramp', 'ada_features'),
            ('SURV', 'BLDG', 'FOOT', 'EXIST', 'PG', 'Building footprint', 'buildings'),
            ('LAND', 'PLNT', 'SHRUB', 'PROP', 'PG', 'Proposed shrub bed', 'planting_areas'),

            # === TX (Text) - Labels, Callouts, Notes ===
            ('ANNO', 'NOTE', 'GEN', 'NEW', 'TX', 'General note', 'drawing_entities'),
            ('ANNO', 'LABL', 'SPOT', 'EXIST', 'TX', 'Spot elevation label', 'drawing_entities'),
            ('ANNO', 'LABL', 'PIPE', 'NEW', 'TX', 'Pipe size label', 'drawing_entities'),
            ('ANNO', 'CALL', 'DET', 'NEW', 'TX', 'Detail callout', 'drawing_entities'),
            ('SURV', 'TOPO', 'ELEV', 'EXIST', 'TX', 'Elevation text', 'drawing_entities'),

            # === 3D (3D Objects) - Surfaces, Terrain Models ===
            ('CIV', 'GRAD', 'DTM', 'EXIST', '3D', 'Digital terrain model', 'surfaces'),
            ('CIV', 'GRAD', 'TIN', 'PROP', '3D', 'Proposed TIN surface', 'surfaces'),
            ('SURV', 'TOPO', '3DSURF', 'EXIST', '3D', '3D survey surface', 'surfaces'),

            # === BK (Blocks) - Symbols, Fixtures ===
            ('CIV', 'UTIL', 'SYM', 'NEW', 'BK', 'Utility symbol block', 'blocks'),
            ('LAND', 'PLNT', 'SYM', 'PROP', 'BK', 'Plant symbol block', 'blocks'),
            ('ANNO', 'SYM', 'NORTH', 'NEW', 'BK', 'North arrow symbol', 'blocks'),
            ('ANNO', 'SYM', 'TITLE', 'NEW', 'BK', 'Title block', 'blocks'),

            # === HT (Hatches) - Fill Patterns ===
            ('CIV', 'UTIL', 'FILL', 'NEW', 'HT', 'Utility trench hatch', 'drawing_entities'),
            ('CIV', 'GRAD', 'FILL', 'PROP', 'HT', 'Grading fill pattern', 'drawing_entities'),
            ('LAND', 'PLNT', 'FILL', 'PROP', 'HT', 'Planting area hatch', 'drawing_entities'),

            # === DIM (Dimensions) - Measurements ===
            ('ANNO', 'DIM', 'LIN', 'NEW', 'DIM', 'Linear dimension', 'drawing_entities'),
            ('ANNO', 'DIM', 'RAD', 'NEW', 'DIM', 'Radius dimension', 'drawing_entities'),
            ('ANNO', 'DIM', 'ANGLE', 'NEW', 'DIM', 'Angular dimension', 'drawing_entities'),
        ]

        # Get metadata from database for enrichment
        phases_query = """
            SELECT code, full_name, color_rgb FROM phase_codes
            WHERE is_active = TRUE
        """
        phases_data = {p['code']: p for p in execute_query(phases_query)}

        geometries_query = """
            SELECT code, full_name, dxf_entity_types FROM geometry_codes
            WHERE is_active = TRUE
        """
        geometries_data = {g['code']: g for g in execute_query(geometries_query)}

        disciplines_query = """
            SELECT code, full_name FROM discipline_codes
            WHERE is_active = TRUE
        """
        disciplines_data = {d['code']: d for d in execute_query(disciplines_query)}

        categories_query = """
            SELECT c.code, c.full_name, d.code as discipline_code
            FROM category_codes c
            JOIN discipline_codes d ON c.discipline_id = d.discipline_id
            WHERE c.is_active = TRUE
        """
        categories_data = {}
        for c in execute_query(categories_query):
            key = f"{c['discipline_code']}-{c['code']}"
            categories_data[key] = c

        object_types_query = """
            SELECT t.code, t.full_name, c.code as category_code, d.code as discipline_code
            FROM object_type_codes t
            JOIN category_codes c ON t.category_id = c.category_id
            JOIN discipline_codes d ON c.discipline_id = d.discipline_id
            WHERE t.is_active = TRUE
        """
        object_types_data = {}
        for t in execute_query(object_types_query):
            key = f"{t['discipline_code']}-{t['category_code']}-{t['code']}"
            object_types_data[key] = t

        # Build enriched examples from catalog
        examples = []
        for disc, cat, obj, phase, geom, description, db_table in catalog:
            # Build layer name using standard pattern
            layer_name = f"{disc}-{cat}-{obj}-{phase}-{geom}"

            # Enrich with metadata
            phase_info = phases_data.get(phase, {})
            geom_info = geometries_data.get(geom, {})
            disc_info = disciplines_data.get(disc, {})
            cat_key = f"{disc}-{cat}"
            cat_info = categories_data.get(cat_key, {})
            obj_key = f"{disc}-{cat}-{obj}"
            obj_info = object_types_data.get(obj_key, {})

            examples.append({
                'layer_name': layer_name,
                'description': description,
                'object_type': obj_info.get('full_name', obj),
                'object_code': obj,
                'discipline': disc_info.get('full_name', disc),
                'discipline_code': disc,
                'category': cat_info.get('full_name', cat),
                'category_code': cat,
                'phase': phase_info.get('full_name', phase),
                'phase_code': phase,
                'phase_color': phase_info.get('color_rgb'),
                'geometry': geom_info.get('full_name', geom),
                'geometry_code': geom,
                'dxf_types': geom_info.get('dxf_entity_types', ''),
                'database_table': db_table
            })

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

# ===== DISCIPLINES CRUD =====

@standards_bp.route('/api/vocabulary/disciplines', methods=['POST'])
def create_vocabulary_discipline():
    """Create a new discipline code with validation"""
    try:
        data = request.get_json()

        if not data.get('code') or not data.get('full_name'):
            return jsonify({'error': 'Code and full_name are required'}), 400

        code = data['code'].upper().strip()
        if len(code) > 20:
            return jsonify({'error': 'Code must be 20 characters or less'}), 400

        check_query = "SELECT discipline_id FROM discipline_codes WHERE UPPER(code) = %s"
        existing = execute_query(check_query, (code,))
        if existing:
            return jsonify({'error': f'Discipline code {code} already exists'}), 409

        query = """
            INSERT INTO discipline_codes (code, full_name, description, sort_order, is_active)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING discipline_id
        """
        result = execute_query(query, (
            code,
            data['full_name'].strip(),
            data.get('description', '').strip() or None,
            data.get('sort_order', 100),
            data.get('is_active', True)
        ))

        invalidate_classifier_cache()

        return jsonify({
            'discipline_id': result[0]['discipline_id'],
            'message': f'Discipline {code} created successfully'
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@standards_bp.route('/api/vocabulary/disciplines/<int:discipline_id>', methods=['PUT'])
def update_vocabulary_discipline(discipline_id):
    """Update a discipline code with validation"""
    try:
        data = request.get_json()

        if not data.get('code') or not data.get('full_name'):
            return jsonify({'error': 'Code and full_name are required'}), 400

        code = data['code'].upper().strip()
        if len(code) > 20:
            return jsonify({'error': 'Code must be 20 characters or less'}), 400

        check_query = """
            SELECT discipline_id FROM discipline_codes
            WHERE UPPER(code) = %s AND discipline_id != %s
        """
        existing = execute_query(check_query, (code, discipline_id))
        if existing:
            return jsonify({'error': f'Discipline code {code} already exists'}), 409

        query = """
            UPDATE discipline_codes
            SET code = %s, full_name = %s, description = %s, sort_order = %s, is_active = %s
            WHERE discipline_id = %s
            RETURNING discipline_id
        """
        result = execute_query(query, (
            code,
            data['full_name'].strip(),
            data.get('description', '').strip() or None,
            data.get('sort_order', 100),
            data.get('is_active', True),
            discipline_id
        ))

        if not result:
            return jsonify({'error': 'Discipline not found'}), 404

        invalidate_classifier_cache()

        return jsonify({'message': f'Discipline {code} updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@standards_bp.route('/api/vocabulary/disciplines/<int:discipline_id>', methods=['DELETE'])
def delete_vocabulary_discipline(discipline_id):
    """Delete a discipline code with dependency checking"""
    try:
        exists_query = "SELECT discipline_id FROM discipline_codes WHERE discipline_id = %s"
        exists = execute_query(exists_query, (discipline_id,))
        if not exists:
            return jsonify({'error': 'Discipline not found'}), 404

        dep_query = """
            SELECT COUNT(*) as count FROM category_codes WHERE discipline_id = %s
        """
        deps = execute_query(dep_query, (discipline_id,))
        if deps[0]['count'] > 0:
            return jsonify({'error': f'Cannot delete discipline: {deps[0]["count"]} categories depend on it'}), 409

        execute_query("DELETE FROM discipline_codes WHERE discipline_id = %s", (discipline_id,))

        invalidate_classifier_cache()

        return jsonify({'message': 'Discipline deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== CATEGORIES CRUD =====

@standards_bp.route('/api/vocabulary/categories', methods=['POST'])
def create_vocabulary_category():
    """Create a new category code with validation"""
    try:
        data = request.get_json()

        if not data.get('code') or not data.get('full_name') or not data.get('discipline_id'):
            return jsonify({'error': 'Code, full_name, and discipline_id are required'}), 400

        code = data['code'].upper().strip()
        if len(code) > 20:
            return jsonify({'error': 'Code must be 20 characters or less'}), 400

        disc_query = "SELECT discipline_id FROM discipline_codes WHERE discipline_id = %s"
        disc_exists = execute_query(disc_query, (data['discipline_id'],))
        if not disc_exists:
            return jsonify({'error': 'Invalid discipline_id'}), 400

        check_query = """
            SELECT category_id FROM category_codes
            WHERE UPPER(code) = %s AND discipline_id = %s
        """
        existing = execute_query(check_query, (code, data['discipline_id']))
        if existing:
            return jsonify({'error': f'Category code {code} already exists for this discipline'}), 409

        query = """
            INSERT INTO category_codes (discipline_id, code, full_name, description, sort_order, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING category_id
        """
        result = execute_query(query, (
            data['discipline_id'],
            code,
            data['full_name'].strip(),
            data.get('description', '').strip() or None,
            data.get('sort_order', 100),
            data.get('is_active', True)
        ))

        invalidate_classifier_cache()

        return jsonify({
            'category_id': result[0]['category_id'],
            'message': f'Category {code} created successfully'
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@standards_bp.route('/api/vocabulary/categories/<int:category_id>', methods=['PUT'])
def update_vocabulary_category(category_id):
    """Update a category code with validation"""
    try:
        data = request.get_json()

        if not data.get('code') or not data.get('full_name'):
            return jsonify({'error': 'Code and full_name are required'}), 400

        code = data['code'].upper().strip()
        if len(code) > 20:
            return jsonify({'error': 'Code must be 20 characters or less'}), 400

        current_query = "SELECT discipline_id FROM category_codes WHERE category_id = %s"
        current = execute_query(current_query, (category_id,))
        if not current:
            return jsonify({'error': 'Category not found'}), 404

        check_query = """
            SELECT category_id FROM category_codes
            WHERE UPPER(code) = %s AND discipline_id = %s AND category_id != %s
        """
        existing = execute_query(check_query, (code, current[0]['discipline_id'], category_id))
        if existing:
            return jsonify({'error': f'Category code {code} already exists for this discipline'}), 409

        query = """
            UPDATE category_codes
            SET code = %s, full_name = %s, description = %s, sort_order = %s, is_active = %s
            WHERE category_id = %s
            RETURNING category_id
        """
        result = execute_query(query, (
            code,
            data['full_name'].strip(),
            data.get('description', '').strip() or None,
            data.get('sort_order', 100),
            data.get('is_active', True),
            category_id
        ))

        if not result:
            return jsonify({'error': 'Category not found'}), 404

        invalidate_classifier_cache()

        return jsonify({'message': f'Category {code} updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@standards_bp.route('/api/vocabulary/categories/<int:category_id>', methods=['DELETE'])
def delete_vocabulary_category(category_id):
    """Delete a category code with dependency checking"""
    try:
        exists_query = "SELECT category_id FROM category_codes WHERE category_id = %s"
        exists = execute_query(exists_query, (category_id,))
        if not exists:
            return jsonify({'error': 'Category not found'}), 404

        dep_query = """
            SELECT COUNT(*) as count FROM object_type_codes WHERE category_id = %s
        """
        deps = execute_query(dep_query, (category_id,))
        if deps[0]['count'] > 0:
            return jsonify({'error': f'Cannot delete category: {deps[0]["count"]} object types depend on it'}), 409

        execute_query("DELETE FROM category_codes WHERE category_id = %s", (category_id,))

        invalidate_classifier_cache()

        return jsonify({'message': 'Category deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== OBJECT TYPES CRUD =====

@standards_bp.route('/api/vocabulary/object-types', methods=['POST'])
def create_object_type():
    """Create a new object type code with validation"""
    try:
        data = request.get_json()

        if not data.get('code') or not data.get('full_name') or not data.get('category_id'):
            return jsonify({'error': 'Code, full_name, and category_id are required'}), 400

        code = data['code'].upper().strip()
        if len(code) > 20:
            return jsonify({'error': 'Code must be 20 characters or less'}), 400

        cat_query = "SELECT category_id FROM category_codes WHERE category_id = %s"
        cat_exists = execute_query(cat_query, (data['category_id'],))
        if not cat_exists:
            return jsonify({'error': 'Invalid category_id'}), 400

        check_query = """
            SELECT type_id FROM object_type_codes
            WHERE UPPER(code) = %s AND category_id = %s
        """
        existing = execute_query(check_query, (code, data['category_id']))
        if existing:
            return jsonify({'error': f'Object type code {code} already exists for this category'}), 409

        database_table = data.get('database_table', '').strip() or None
        if database_table:
            registry_check = "SELECT registry_id FROM entity_registry WHERE table_name = %s AND is_active = TRUE"
            registry_entry = execute_query(registry_check, (database_table,))
            if not registry_entry:
                return jsonify({'error': f'Database table {database_table} is not registered in entity registry. Please register it first.'}), 400

        query = """
            INSERT INTO object_type_codes (category_id, code, full_name, description, database_table, sort_order, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING type_id
        """
        result = execute_query(query, (
            data['category_id'],
            code,
            data['full_name'].strip(),
            data.get('description', '').strip() or None,
            database_table,
            data.get('sort_order', 100),
            data.get('is_active', True)
        ))

        invalidate_classifier_cache()

        return jsonify({
            'type_id': result[0]['type_id'],
            'message': f'Object type {code} created successfully'
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@standards_bp.route('/api/vocabulary/object-types/<int:type_id>', methods=['PUT'])
def update_object_type(type_id):
    """Update an object type code with validation"""
    try:
        data = request.get_json()

        if not data.get('code') or not data.get('full_name'):
            return jsonify({'error': 'Code and full_name are required'}), 400

        code = data['code'].upper().strip()
        if len(code) > 20:
            return jsonify({'error': 'Code must be 20 characters or less'}), 400

        current_query = "SELECT category_id FROM object_type_codes WHERE type_id = %s"
        current = execute_query(current_query, (type_id,))
        if not current:
            return jsonify({'error': 'Object type not found'}), 404

        check_query = """
            SELECT type_id FROM object_type_codes
            WHERE UPPER(code) = %s AND category_id = %s AND type_id != %s
        """
        existing = execute_query(check_query, (code, current[0]['category_id'], type_id))
        if existing:
            return jsonify({'error': f'Object type code {code} already exists for this category'}), 409

        database_table = data.get('database_table', '').strip() or None
        if database_table:
            registry_check = "SELECT registry_id FROM entity_registry WHERE table_name = %s AND is_active = TRUE"
            registry_entry = execute_query(registry_check, (database_table,))
            if not registry_entry:
                return jsonify({'error': f'Database table {database_table} is not registered in entity registry. Please register it first.'}), 400

        query = """
            UPDATE object_type_codes
            SET code = %s, full_name = %s, description = %s, database_table = %s, sort_order = %s, is_active = %s
            WHERE type_id = %s
            RETURNING type_id
        """
        result = execute_query(query, (
            code,
            data['full_name'].strip(),
            data.get('description', '').strip() or None,
            database_table,
            data.get('sort_order', 100),
            data.get('is_active', True),
            type_id
        ))

        if not result:
            return jsonify({'error': 'Object type not found'}), 404

        invalidate_classifier_cache()

        return jsonify({'message': f'Object type {code} updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@standards_bp.route('/api/vocabulary/object-types/<int:type_id>', methods=['DELETE'])
def delete_object_type(type_id):
    """Delete an object type code (soft delete - mark inactive)"""
    try:
        query = "UPDATE object_type_codes SET is_active = FALSE WHERE type_id = %s RETURNING type_id"
        result = execute_query(query, (type_id,))

        if not result:
            return jsonify({'error': 'Object type not found'}), 404

        invalidate_classifier_cache()

        return jsonify({'message': 'Object type deactivated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== PHASES CRUD =====

@standards_bp.route('/api/vocabulary/phases', methods=['POST'])
def create_phase():
    """Create a new phase code with validation"""
    try:
        data = request.get_json()

        if not data.get('code') or not data.get('full_name'):
            return jsonify({'error': 'Code and full_name are required'}), 400

        code = data['code'].upper().strip()
        if len(code) > 20:
            return jsonify({'error': 'Code must be 20 characters or less'}), 400

        check_query = "SELECT phase_id FROM phase_codes WHERE UPPER(code) = %s"
        existing = execute_query(check_query, (code,))
        if existing:
            return jsonify({'error': f'Phase code {code} already exists'}), 409

        query = """
            INSERT INTO phase_codes (code, full_name, description, color_rgb, sort_order, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING phase_id
        """
        result = execute_query(query, (
            code,
            data['full_name'].strip(),
            data.get('description', '').strip() or None,
            data.get('color_rgb', '').strip() or None,
            data.get('sort_order', 100),
            data.get('is_active', True)
        ))

        invalidate_classifier_cache()

        return jsonify({
            'phase_id': result[0]['phase_id'],
            'message': f'Phase {code} created successfully'
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@standards_bp.route('/api/vocabulary/phases/<int:phase_id>', methods=['PUT'])
def update_phase(phase_id):
    """Update a phase code with validation"""
    try:
        data = request.get_json()

        if not data.get('code') or not data.get('full_name'):
            return jsonify({'error': 'Code and full_name are required'}), 400

        code = data['code'].upper().strip()
        if len(code) > 20:
            return jsonify({'error': 'Code must be 20 characters or less'}), 400

        check_query = """
            SELECT phase_id FROM phase_codes
            WHERE UPPER(code) = %s AND phase_id != %s
        """
        existing = execute_query(check_query, (code, phase_id))
        if existing:
            return jsonify({'error': f'Phase code {code} already exists'}), 409

        query = """
            UPDATE phase_codes
            SET code = %s, full_name = %s, description = %s, color_rgb = %s, sort_order = %s, is_active = %s
            WHERE phase_id = %s
            RETURNING phase_id
        """
        result = execute_query(query, (
            code,
            data['full_name'].strip(),
            data.get('description', '').strip() or None,
            data.get('color_rgb', '').strip() or None,
            data.get('sort_order', 100),
            data.get('is_active', True),
            phase_id
        ))

        if not result:
            return jsonify({'error': 'Phase not found'}), 404

        invalidate_classifier_cache()

        return jsonify({'message': f'Phase {code} updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@standards_bp.route('/api/vocabulary/phases/<int:phase_id>', methods=['DELETE'])
def delete_phase(phase_id):
    """Delete a phase code (soft delete - mark inactive)"""
    try:
        query = "UPDATE phase_codes SET is_active = FALSE WHERE phase_id = %s RETURNING phase_id"
        result = execute_query(query, (phase_id,))

        if not result:
            return jsonify({'error': 'Phase not found'}), 404

        invalidate_classifier_cache()

        return jsonify({'message': 'Phase deactivated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== GEOMETRIES CRUD =====

@standards_bp.route('/api/vocabulary/geometries', methods=['POST'])
def create_geometry():
    """Create a new geometry code with validation"""
    try:
        data = request.get_json()

        if not data.get('code') or not data.get('full_name'):
            return jsonify({'error': 'Code and full_name are required'}), 400

        code = data['code'].upper().strip()
        if len(code) > 20:
            return jsonify({'error': 'Code must be 20 characters or less'}), 400

        check_query = "SELECT geometry_id FROM geometry_codes WHERE UPPER(code) = %s"
        existing = execute_query(check_query, (code,))
        if existing:
            return jsonify({'error': f'Geometry code {code} already exists'}), 409

        query = """
            INSERT INTO geometry_codes (code, full_name, description, dxf_entity_types, sort_order, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING geometry_id
        """
        result = execute_query(query, (
            code,
            data['full_name'].strip(),
            data.get('description', '').strip() or None,
            data.get('dxf_entity_types', '').strip() or None,
            data.get('sort_order', 100),
            data.get('is_active', True)
        ))

        invalidate_classifier_cache()

        return jsonify({
            'geometry_id': result[0]['geometry_id'],
            'message': f'Geometry {code} created successfully'
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@standards_bp.route('/api/vocabulary/geometries/<int:geometry_id>', methods=['PUT'])
def update_geometry(geometry_id):
    """Update a geometry code with validation"""
    try:
        data = request.get_json()

        if not data.get('code') or not data.get('full_name'):
            return jsonify({'error': 'Code and full_name are required'}), 400

        code = data['code'].upper().strip()
        if len(code) > 20:
            return jsonify({'error': 'Code must be 20 characters or less'}), 400

        check_query = """
            SELECT geometry_id FROM geometry_codes
            WHERE UPPER(code) = %s AND geometry_id != %s
        """
        existing = execute_query(check_query, (code, geometry_id))
        if existing:
            return jsonify({'error': f'Geometry code {code} already exists'}), 409

        query = """
            UPDATE geometry_codes
            SET code = %s, full_name = %s, description = %s, dxf_entity_types = %s, sort_order = %s, is_active = %s
            WHERE geometry_id = %s
            RETURNING geometry_id
        """
        result = execute_query(query, (
            code,
            data['full_name'].strip(),
            data.get('description', '').strip() or None,
            data.get('dxf_entity_types', '').strip() or None,
            data.get('sort_order', 100),
            data.get('is_active', True),
            geometry_id
        ))

        if not result:
            return jsonify({'error': 'Geometry not found'}), 404

        invalidate_classifier_cache()

        return jsonify({'message': f'Geometry {code} updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@standards_bp.route('/api/vocabulary/geometries/<int:geometry_id>', methods=['DELETE'])
def delete_geometry(geometry_id):
    """Delete a geometry code (soft delete - mark inactive)"""
    try:
        query = "UPDATE geometry_codes SET is_active = FALSE WHERE geometry_id = %s RETURNING geometry_id"
        result = execute_query(query, (geometry_id,))

        if not result:
            return jsonify({'error': 'Geometry not found'}), 404

        invalidate_classifier_cache()

        return jsonify({'message': 'Geometry deactivated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== VOCABULARY ATTRIBUTES CRUD (Alternative endpoints) =====

@standards_bp.route('/api/vocabulary/attributes')
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

@standards_bp.route('/api/vocabulary/attributes', methods=['POST'])
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

@standards_bp.route('/api/vocabulary/attributes/<int:attribute_id>', methods=['PUT'])
def update_attribute(attribute_id):
    """Update an attribute code"""
    try:
        data = request.get_json()
        query = """
            UPDATE attribute_codes
            SET code = %s, full_name = %s, attribute_category = %s, description = %s, pattern = %s, is_active = %s
            WHERE attribute_id = %s
        """
        execute_query(query, (data['code'], data['full_name'], data.get('attribute_category'), data.get('description'), data.get('pattern'), data.get('is_active', True), attribute_id))
        return jsonify({'message': 'Attribute updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@standards_bp.route('/api/vocabulary/attributes/<int:attribute_id>', methods=['DELETE'])
def delete_attribute(attribute_id):
    """Delete an attribute code"""
    try:
        execute_query("DELETE FROM attribute_codes WHERE attribute_id = %s", (attribute_id,))
        return jsonify({'message': 'Attribute deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
