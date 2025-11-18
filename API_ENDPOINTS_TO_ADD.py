"""
NEW API ENDPOINTS FOR SPEC-GEOMETRY LINKING SYSTEM
Add these to app.py after line 3115 (after existing spec endpoints)

First, add these imports after line 2983:
"""

# ADD THESE IMPORTS AFTER LINE 2983:
"""
from services.spec_linking_service import SpecLinkingService
from services.compliance_service import ComplianceService
from services.auto_linking_service import AutoLinkingService
from services.csi_masterformat_service import CSIMasterformatService

# Initialize new services
spec_linking_service = SpecLinkingService()
compliance_service = ComplianceService()
auto_linking_service = AutoLinkingService()
csi_service = CSIMasterformatService()
"""

# THEN ADD THESE ENDPOINTS AFTER LINE 3115:

# ============================================
# CSI MASTERFORMAT ENDPOINTS
# ============================================

@app.route('/api/csi-masterformat', methods=['GET'])
def get_csi_codes():
    """Get all CSI MasterFormat codes with optional filters"""
    try:
        filters = {
            'division': request.args.get('division', type=int),
            'level': request.args.get('level', type=int),
            'is_civil_engineering': request.args.get('civil', type=bool),
            'is_active': request.args.get('active', default=True, type=bool)
        }
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}

        codes = csi_service.get_all_codes(filters)
        return jsonify(codes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/csi-masterformat/<csi_code>', methods=['GET'])
def get_csi_code(csi_code):
    """Get a single CSI code"""
    try:
        code = csi_service.get_by_code(csi_code)
        if code:
            return jsonify(code)
        return jsonify({'error': 'CSI code not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/csi-masterformat/divisions', methods=['GET'])
def get_csi_divisions():
    """Get all CSI divisions"""
    try:
        civil_only = request.args.get('civil_only', default=False, type=bool)
        divisions = csi_service.get_divisions(civil_only)
        return jsonify(divisions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/csi-masterformat/<csi_code>/children', methods=['GET'])
def get_csi_children(csi_code):
    """Get children of a CSI code"""
    try:
        recursive = request.args.get('recursive', default=False, type=bool)

        if recursive:
            children = csi_service.get_children_recursive(csi_code)
        else:
            children = csi_service.get_children(csi_code)

        return jsonify(children)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/csi-masterformat/<csi_code>/breadcrumb', methods=['GET'])
def get_csi_breadcrumb(csi_code):
    """Get breadcrumb trail for a CSI code"""
    try:
        breadcrumb = csi_service.get_breadcrumb(csi_code)
        return jsonify(breadcrumb)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/csi-masterformat/<csi_code>/specs', methods=['GET'])
def get_csi_specs(csi_code):
    """Get all specs for a CSI code"""
    try:
        include_children = request.args.get('include_children', default=False, type=bool)
        specs = csi_service.get_specs_by_csi_code(csi_code, include_children)
        return jsonify(specs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/csi-masterformat/search', methods=['GET'])
def search_csi_codes():
    """Search CSI codes"""
    try:
        query = request.args.get('q', '')
        civil_only = request.args.get('civil_only', default=False, type=bool)

        if not query:
            return jsonify([])

        results = csi_service.search_codes(query, civil_only)
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/csi-masterformat/<csi_code>/statistics', methods=['GET'])
def get_csi_statistics(csi_code):
    """Get usage statistics for a CSI code"""
    try:
        stats = csi_service.get_usage_statistics(csi_code)
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# SPEC-GEOMETRY LINKING ENDPOINTS
# ============================================

@app.route('/api/spec-geometry-links', methods=['GET'])
def get_spec_geometry_links():
    """Get spec-geometry links with optional filters"""
    try:
        project_id = request.args.get('project_id')
        entity_id = request.args.get('entity_id')
        entity_type = request.args.get('entity_type')
        spec_id = request.args.get('spec_id')

        if entity_id and entity_type:
            links = spec_linking_service.get_links_by_entity(entity_id, entity_type)
        elif spec_id:
            links = spec_linking_service.get_entities_by_spec(spec_id, project_id)
        elif project_id:
            filters = {
                'compliance_status': request.args.get('compliance_status'),
                'link_type': request.args.get('link_type'),
                'entity_type': request.args.get('filter_entity_type'),
                'csi_code': request.args.get('csi_code')
            }
            filters = {k: v for k, v in filters.items() if v is not None}
            links = spec_linking_service.get_project_links(project_id, filters)
        else:
            return jsonify({'error': 'Must provide entity_id+entity_type, spec_id, or project_id'}), 400

        return jsonify(links)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/spec-geometry-links/<link_id>', methods=['GET'])
def get_spec_geometry_link(link_id):
    """Get a single spec-geometry link"""
    try:
        link = spec_linking_service.get_link_by_id(link_id)
        if link:
            return jsonify(link)
        return jsonify({'error': 'Link not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/spec-geometry-links', methods=['POST'])
def create_spec_geometry_link():
    """Create a new spec-geometry link"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400

        # Validate required fields
        required_fields = ['spec_library_id', 'entity_id', 'entity_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        link = spec_linking_service.create_link(data)
        return jsonify(link), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/spec-geometry-links/<link_id>', methods=['PUT'])
def update_spec_geometry_link(link_id):
    """Update a spec-geometry link"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400

        success = spec_linking_service.update_link(link_id, data)
        if success:
            return jsonify({'success': True})
        return jsonify({'error': 'Update failed'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/spec-geometry-links/<link_id>', methods=['DELETE'])
def delete_spec_geometry_link(link_id):
    """Delete a spec-geometry link"""
    try:
        soft_delete = request.args.get('soft', default=True, type=bool)
        success = spec_linking_service.delete_link(link_id, soft_delete)

        if success:
            return jsonify({'success': True})
        return jsonify({'error': 'Delete failed'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/spec-geometry-links/bulk', methods=['POST'])
def bulk_create_spec_links():
    """Create multiple spec-geometry links at once"""
    try:
        data = request.json
        if not data or not isinstance(data, list):
            return jsonify({'error': 'Request body must be an array of link objects'}), 400

        result = spec_linking_service.bulk_create_links(data)
        return jsonify(result), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/spec-geometry-links/statistics', methods=['GET'])
def get_link_statistics():
    """Get statistics about spec-geometry links"""
    try:
        project_id = request.args.get('project_id')
        stats = spec_linking_service.get_link_statistics(project_id)
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# COMPLIANCE ENDPOINTS
# ============================================

@app.route('/api/compliance/rules', methods=['GET'])
def get_compliance_rules():
    """Get all compliance rules with optional filters"""
    try:
        filters = {
            'is_active': request.args.get('active', type=bool),
            'rule_type': request.args.get('rule_type'),
            'csi_code': request.args.get('csi_code')
        }
        filters = {k: v for k, v in filters.items() if v is not None}

        rules = compliance_service.get_all_rules(filters)
        return jsonify(rules)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/compliance/rules/<rule_id>', methods=['GET'])
def get_compliance_rule(rule_id):
    """Get a single compliance rule"""
    try:
        rule = compliance_service.get_rule_by_id(rule_id)
        if rule:
            return jsonify(rule)
        return jsonify({'error': 'Rule not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/compliance/rules', methods=['POST'])
def create_compliance_rule():
    """Create a new compliance rule"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400

        # Validate required fields
        required_fields = ['rule_name', 'rule_type', 'rule_expression', 'error_message']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        rule = compliance_service.create_rule(data)
        return jsonify(rule), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/compliance/rules/<rule_id>', methods=['PUT'])
def update_compliance_rule(rule_id):
    """Update a compliance rule"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400

        success = compliance_service.update_rule(rule_id, data)
        if success:
            return jsonify({'success': True})
        return jsonify({'error': 'Update failed'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/compliance/rules/<rule_id>', methods=['DELETE'])
def delete_compliance_rule(rule_id):
    """Delete a compliance rule"""
    try:
        success = compliance_service.delete_rule(rule_id)
        if success:
            return jsonify({'success': True})
        return jsonify({'error': 'Delete failed'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/compliance/check', methods=['POST'])
def check_compliance():
    """Check compliance for a spec-geometry link"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400

        link_id = data.get('link_id')
        entity_properties = data.get('entity_properties', {})

        if not link_id:
            return jsonify({'error': 'Missing link_id'}), 400

        result = compliance_service.check_link_compliance(link_id, entity_properties)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/compliance/link/<link_id>/history', methods=['GET'])
def get_compliance_history(link_id):
    """Get compliance check history for a link"""
    try:
        limit = request.args.get('limit', default=10, type=int)
        history = compliance_service.get_compliance_history(link_id, limit)
        return jsonify(history)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects/<project_id>/compliance-summary', methods=['GET'])
def get_project_compliance_summary(project_id):
    """Get compliance summary for a project"""
    try:
        summary = compliance_service.get_project_compliance_summary(project_id)
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# AUTO-LINKING ENDPOINTS
# ============================================

@app.route('/api/auto-link/rules', methods=['GET'])
def get_auto_link_rules():
    """Get all auto-linking rules"""
    try:
        active_only = request.args.get('active', default=True, type=bool)
        rules = auto_linking_service.get_all_auto_link_rules(active_only)
        return jsonify(rules)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auto-link/rules/<rule_id>', methods=['GET'])
def get_auto_link_rule(rule_id):
    """Get a single auto-link rule"""
    try:
        rule = auto_linking_service.get_rule_by_id(rule_id)
        if rule:
            return jsonify(rule)
        return jsonify({'error': 'Rule not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auto-link/rules', methods=['POST'])
def create_auto_link_rule():
    """Create a new auto-link rule"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400

        # Validate required fields
        required_fields = ['rule_name', 'match_type', 'match_expression']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        if not data.get('target_spec_id') and not data.get('target_csi_code'):
            return jsonify({'error': 'Must provide either target_spec_id or target_csi_code'}), 400

        rule = auto_linking_service.create_auto_link_rule(data)
        return jsonify(rule), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auto-link/rules/<rule_id>', methods=['PUT'])
def update_auto_link_rule(rule_id):
    """Update an auto-link rule"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400

        success = auto_linking_service.update_auto_link_rule(rule_id, data)
        if success:
            return jsonify({'success': True})
        return jsonify({'error': 'Update failed'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auto-link/rules/<rule_id>', methods=['DELETE'])
def delete_auto_link_rule(rule_id):
    """Delete an auto-link rule"""
    try:
        success = auto_linking_service.delete_auto_link_rule(rule_id)
        if success:
            return jsonify({'success': True})
        return jsonify({'error': 'Delete failed'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auto-link/suggest', methods=['POST'])
def suggest_entity_links():
    """Generate link suggestions for an entity"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400

        entity_id = data.get('entity_id')
        entity_type = data.get('entity_type')
        entity_properties = data.get('entity_properties', {})
        project_id = data.get('project_id')

        if not entity_id or not entity_type:
            return jsonify({'error': 'Missing entity_id or entity_type'}), 400

        suggestions = auto_linking_service.suggest_links_for_entity(
            entity_id, entity_type, entity_properties, project_id
        )

        # Optionally save suggestions to database
        if request.args.get('save', default=False, type=bool):
            save_result = auto_linking_service.create_suggestions(suggestions)
            return jsonify({
                'suggestions': suggestions,
                'saved': save_result
            })

        return jsonify(suggestions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auto-link/suggestions', methods=['GET'])
def get_auto_link_suggestions():
    """Get pending auto-link suggestions"""
    try:
        project_id = request.args.get('project_id')
        entity_id = request.args.get('entity_id')

        suggestions = auto_linking_service.get_pending_suggestions(project_id, entity_id)
        return jsonify(suggestions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auto-link/suggestions/<suggestion_id>/apply', methods=['POST'])
def apply_auto_link_suggestion(suggestion_id):
    """Accept or reject an auto-link suggestion"""
    try:
        data = request.json or {}
        action = data.get('action', 'accepted')  # 'accepted' or 'rejected'
        user_id = data.get('user_id', 'system')

        if action not in ['accepted', 'rejected']:
            return jsonify({'error': 'Invalid action. Must be "accepted" or "rejected"'}), 400

        result = auto_linking_service.apply_suggestion(suggestion_id, user_id, action)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auto-link/project/<project_id>', methods=['POST'])
def auto_link_project(project_id):
    """Run auto-linking for an entire project"""
    try:
        data = request.json or {}
        entity_type = data.get('entity_type')
        auto_apply = data.get('auto_apply', False)

        result = auto_linking_service.auto_link_project_entities(
            project_id, entity_type, auto_apply
        )

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# ENTITY-SPEC CONVENIENCE ENDPOINTS
# ============================================

@app.route('/api/entities/<entity_id>/specs', methods=['GET'])
def get_entity_specs(entity_id):
    """Get all specs linked to an entity"""
    try:
        entity_type = request.args.get('entity_type')
        if not entity_type:
            return jsonify({'error': 'Missing entity_type parameter'}), 400

        links = spec_linking_service.get_links_by_entity(entity_id, entity_type)
        return jsonify(links)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/specs/<spec_id>/entities', methods=['GET'])
def get_spec_entities(spec_id):
    """Get all entities linked to a spec"""
    try:
        project_id = request.args.get('project_id')
        links = spec_linking_service.get_entities_by_spec(spec_id, project_id)
        return jsonify(links)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
