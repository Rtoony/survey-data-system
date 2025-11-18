"""
Compliance Service
Handles compliance rule evaluation and validation for spec-geometry links
"""

import uuid
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
from db import get_db, execute_query


class ComplianceService:
    """Service for managing and executing compliance rules"""

    @staticmethod
    def create_rule(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new compliance rule

        Args:
            data: Rule definition containing:
                - rule_name (required)
                - rule_type (required)
                - rule_expression (required, JSONB)
                - severity (default: 'warning')
                - error_message (required)
                - csi_code, spec_standard_id, spec_library_id (optional)
                - entity_types (optional array)
                - auto_check (default: True)

        Returns:
            Created rule record
        """
        rule_id = uuid.uuid4()
        rule_code = data.get('rule_code') or f"RULE_{str(rule_id)[:8].upper()}"

        query = """
            INSERT INTO compliance_rules (
                rule_id, rule_name, rule_code, csi_code, spec_standard_id,
                spec_library_id, rule_type, rule_expression, entity_types,
                layer_patterns, severity, error_message, help_text,
                auto_check, check_on_link, check_on_update, is_active,
                priority, created_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """

        params = (
            rule_id,
            data['rule_name'],
            rule_code,
            data.get('csi_code'),
            data.get('spec_standard_id'),
            data.get('spec_library_id'),
            data['rule_type'],
            json.dumps(data['rule_expression']),
            data.get('entity_types'),
            data.get('layer_patterns'),
            data.get('severity', 'warning'),
            data['error_message'],
            data.get('help_text'),
            data.get('auto_check', True),
            data.get('check_on_link', True),
            data.get('check_on_update', True),
            data.get('is_active', True),
            data.get('priority', 100),
            data.get('created_by')
        )

        result = execute_query(query, params)
        return result[0] if result else None

    @staticmethod
    def get_rule_by_id(rule_id: str) -> Optional[Dict[str, Any]]:
        """Get a single rule by ID"""
        query = """
            SELECT
                r.*,
                cm.csi_title,
                ss.standard_name
            FROM compliance_rules r
            LEFT JOIN csi_masterformat cm ON r.csi_code = cm.csi_code
            LEFT JOIN spec_standards ss ON r.spec_standard_id = ss.spec_standard_id
            WHERE r.rule_id = %s
        """

        result = execute_query(query, (rule_id,))
        return result[0] if result else None

    @staticmethod
    def get_applicable_rules(entity_type: str, spec_id: Optional[str] = None, csi_code: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all rules applicable to an entity

        Args:
            entity_type: Type of entity (e.g., 'pipe', 'manhole')
            spec_id: Optional specific spec filter
            csi_code: Optional CSI code filter

        Returns:
            List of applicable rules
        """
        where_clauses = ["r.is_active = TRUE"]
        params = []

        # Entity type filter
        where_clauses.append("(%s = ANY(r.entity_types) OR r.entity_types IS NULL)")
        params.append(entity_type)

        # Spec filter
        if spec_id:
            where_clauses.append("(r.spec_library_id = %s OR r.spec_library_id IS NULL)")
            params.append(spec_id)

        # CSI code filter
        if csi_code:
            where_clauses.append("(r.csi_code = %s OR r.csi_code IS NULL)")
            params.append(csi_code)

        where_sql = " AND ".join(where_clauses)

        query = f"""
            SELECT
                r.*,
                cm.csi_title,
                ss.standard_name
            FROM compliance_rules r
            LEFT JOIN csi_masterformat cm ON r.csi_code = cm.csi_code
            LEFT JOIN spec_standards ss ON r.spec_standard_id = ss.spec_standard_id
            WHERE {where_sql}
            ORDER BY r.priority ASC, r.severity DESC
        """

        return execute_query(query, tuple(params))

    @staticmethod
    def evaluate_rule(rule: Dict[str, Any], entity_properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a single rule against entity properties

        Args:
            rule: Rule definition from database
            entity_properties: Dictionary of entity properties

        Returns:
            Dict with: passes (bool), violations (list), message (str)
        """
        rule_type = rule['rule_type']
        rule_expr = rule['rule_expression']

        if isinstance(rule_expr, str):
            rule_expr = json.loads(rule_expr)

        violations = []
        passes = True

        try:
            if rule_type == 'dimension_check':
                passes, violations = ComplianceService._evaluate_dimension_check(rule_expr, entity_properties)

            elif rule_type == 'property_match':
                passes, violations = ComplianceService._evaluate_property_match(rule_expr, entity_properties)

            elif rule_type == 'material_validation':
                passes, violations = ComplianceService._evaluate_material_validation(rule_expr, entity_properties)

            elif rule_type == 'attribute_required':
                passes, violations = ComplianceService._evaluate_attribute_required(rule_expr, entity_properties)

            elif rule_type == 'range_validation':
                passes, violations = ComplianceService._evaluate_range_validation(rule_expr, entity_properties)

            elif rule_type == 'pattern_match':
                passes, violations = ComplianceService._evaluate_pattern_match(rule_expr, entity_properties)

            else:
                passes = False
                violations = [f"Unknown rule type: {rule_type}"]

        except Exception as e:
            passes = False
            violations = [f"Rule evaluation error: {str(e)}"]

        return {
            'passes': passes,
            'violations': violations,
            'rule_id': rule['rule_id'],
            'rule_name': rule['rule_name'],
            'severity': rule['severity'],
            'message': rule['error_message'] if not passes else "Compliant"
        }

    @staticmethod
    def _evaluate_dimension_check(rule_expr: Dict, properties: Dict) -> tuple:
        """Evaluate dimensional requirements"""
        violations = []
        conditions = rule_expr.get('conditions', [])

        for condition in conditions:
            prop_name = condition['property']
            operator = condition['operator']
            expected_value = condition['value']
            actual_value = properties.get(prop_name)

            if actual_value is None:
                violations.append(f"Missing property: {prop_name}")
                continue

            # Convert to float for numeric comparison
            try:
                actual_value = float(actual_value)
                expected_value = float(expected_value)
            except (ValueError, TypeError):
                violations.append(f"Invalid numeric value for {prop_name}")
                continue

            # Evaluate operator
            if operator == '>=':
                if not (actual_value >= expected_value):
                    violations.append(f"{prop_name} ({actual_value}) must be >= {expected_value}")
            elif operator == '<=':
                if not (actual_value <= expected_value):
                    violations.append(f"{prop_name} ({actual_value}) must be <= {expected_value}")
            elif operator == '==':
                if not (actual_value == expected_value):
                    violations.append(f"{prop_name} ({actual_value}) must equal {expected_value}")
            elif operator == '>':
                if not (actual_value > expected_value):
                    violations.append(f"{prop_name} ({actual_value}) must be > {expected_value}")
            elif operator == '<':
                if not (actual_value < expected_value):
                    violations.append(f"{prop_name} ({actual_value}) must be < {expected_value}")

        return (len(violations) == 0, violations)

    @staticmethod
    def _evaluate_property_match(rule_expr: Dict, properties: Dict) -> tuple:
        """Evaluate property matching requirements"""
        violations = []
        required_properties = rule_expr.get('required_properties', {})

        for prop_name, expected_value in required_properties.items():
            actual_value = properties.get(prop_name)

            if actual_value is None:
                violations.append(f"Missing required property: {prop_name}")
            elif actual_value != expected_value:
                violations.append(f"{prop_name} is '{actual_value}', expected '{expected_value}'")

        return (len(violations) == 0, violations)

    @staticmethod
    def _evaluate_material_validation(rule_expr: Dict, properties: Dict) -> tuple:
        """Validate material specifications"""
        violations = []
        allowed_materials = rule_expr.get('allowed_materials', [])
        material_property = rule_expr.get('material_property', 'material')

        actual_material = properties.get(material_property)

        if not actual_material:
            violations.append(f"Material property '{material_property}' not found")
        elif allowed_materials and actual_material not in allowed_materials:
            violations.append(f"Material '{actual_material}' not in allowed list: {', '.join(allowed_materials)}")

        return (len(violations) == 0, violations)

    @staticmethod
    def _evaluate_attribute_required(rule_expr: Dict, properties: Dict) -> tuple:
        """Check for required attributes"""
        violations = []
        required_attrs = rule_expr.get('required_attributes', [])

        for attr in required_attrs:
            if attr not in properties or properties[attr] is None or properties[attr] == '':
                violations.append(f"Required attribute missing or empty: {attr}")

        return (len(violations) == 0, violations)

    @staticmethod
    def _evaluate_range_validation(rule_expr: Dict, properties: Dict) -> tuple:
        """Validate value is within allowed range"""
        violations = []
        prop_name = rule_expr.get('property')
        min_value = rule_expr.get('min_value')
        max_value = rule_expr.get('max_value')

        actual_value = properties.get(prop_name)

        if actual_value is None:
            violations.append(f"Property '{prop_name}' not found")
            return (False, violations)

        try:
            actual_value = float(actual_value)

            if min_value is not None and actual_value < float(min_value):
                violations.append(f"{prop_name} ({actual_value}) below minimum ({min_value})")

            if max_value is not None and actual_value > float(max_value):
                violations.append(f"{prop_name} ({actual_value}) above maximum ({max_value})")

        except (ValueError, TypeError):
            violations.append(f"Invalid numeric value for {prop_name}")

        return (len(violations) == 0, violations)

    @staticmethod
    def _evaluate_pattern_match(rule_expr: Dict, properties: Dict) -> tuple:
        """Validate property matches pattern (regex)"""
        import re

        violations = []
        prop_name = rule_expr.get('property')
        pattern = rule_expr.get('pattern')

        actual_value = properties.get(prop_name)

        if actual_value is None:
            violations.append(f"Property '{prop_name}' not found")
        elif not re.match(pattern, str(actual_value)):
            violations.append(f"{prop_name} ('{actual_value}') does not match pattern: {pattern}")

        return (len(violations) == 0, violations)

    @staticmethod
    def check_link_compliance(link_id: str, entity_properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check compliance for a specific spec-geometry link

        Args:
            link_id: UUID of the link
            entity_properties: Dictionary of entity properties to validate

        Returns:
            Compliance check result with status and violations
        """
        # Get the link details
        link = execute_query("""
            SELECT l.*, s.csi_code, s.spec_standard_id
            FROM spec_geometry_links l
            INNER JOIN spec_library s ON l.spec_library_id = s.spec_library_id
            WHERE l.link_id = %s
        """, (link_id,))

        if not link:
            return {'error': 'Link not found'}

        link = link[0]

        # Get applicable rules
        rules = ComplianceService.get_applicable_rules(
            entity_type=link['entity_type'],
            spec_id=link['spec_library_id'],
            csi_code=link.get('csi_code')
        )

        # Evaluate all rules
        results = []
        overall_passes = True
        highest_severity = 'info'

        for rule in rules:
            result = ComplianceService.evaluate_rule(rule, entity_properties)
            results.append(result)

            if not result['passes']:
                overall_passes = False

                # Track highest severity
                if result['severity'] == 'error':
                    highest_severity = 'error'
                elif result['severity'] == 'warning' and highest_severity != 'error':
                    highest_severity = 'warning'

        # Determine compliance status
        if overall_passes:
            compliance_status = 'compliant'
        elif highest_severity == 'error':
            compliance_status = 'violation'
        else:
            compliance_status = 'warning'

        # Update the link
        update_query = """
            UPDATE spec_geometry_links
            SET compliance_status = %s,
                last_checked = NOW(),
                compliance_data = %s
            WHERE link_id = %s
        """

        execute_query(update_query, (
            compliance_status,
            json.dumps({'rules_checked': len(rules), 'results': results}),
            link_id
        ))

        return {
            'link_id': link_id,
            'compliance_status': compliance_status,
            'overall_passes': overall_passes,
            'rules_evaluated': len(rules),
            'violations': [r for r in results if not r['passes']],
            'all_results': results
        }

    @staticmethod
    def get_compliance_history(link_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get compliance check history for a link"""
        query = """
            SELECT *
            FROM compliance_history
            WHERE link_id = %s
            ORDER BY checked_at DESC
            LIMIT %s
        """

        return execute_query(query, (link_id, limit))

    @staticmethod
    def get_project_compliance_summary(project_id: str) -> Dict[str, Any]:
        """Get compliance summary for entire project"""
        # Use the database function we created
        query = "SELECT * FROM get_project_compliance_percentage(%s)"
        result = execute_query(query, (project_id,))

        if not result:
            return {
                'total_links': 0,
                'compliant_count': 0,
                'warning_count': 0,
                'violation_count': 0,
                'pending_count': 0,
                'compliance_percentage': 0
            }

        return result[0]

    @staticmethod
    def update_rule(rule_id: str, data: Dict[str, Any]) -> bool:
        """Update an existing compliance rule"""
        allowed_fields = [
            'rule_name', 'rule_expression', 'severity', 'error_message',
            'help_text', 'auto_check', 'check_on_link', 'check_on_update',
            'is_active', 'priority', 'entity_types', 'layer_patterns', 'updated_by'
        ]

        update_fields = []
        params = []

        for field in allowed_fields:
            if field in data:
                if field == 'rule_expression':
                    update_fields.append(f"{field} = %s::jsonb")
                    params.append(json.dumps(data[field]))
                else:
                    update_fields.append(f"{field} = %s")
                    params.append(data[field])

        if not update_fields:
            return False

        update_fields.append("updated_at = NOW()")
        params.append(rule_id)

        query = f"""
            UPDATE compliance_rules
            SET {', '.join(update_fields)}
            WHERE rule_id = %s
            RETURNING rule_id
        """

        result = execute_query(query, tuple(params))
        return len(result) > 0

    @staticmethod
    def delete_rule(rule_id: str) -> bool:
        """Delete a compliance rule"""
        query = "DELETE FROM compliance_rules WHERE rule_id = %s RETURNING rule_id"
        result = execute_query(query, (rule_id,))
        return len(result) > 0

    @staticmethod
    def get_all_rules(filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all compliance rules with optional filters"""
        filters = filters or {}

        where_clauses = []
        params = []

        if filters.get('is_active') is not None:
            where_clauses.append("is_active = %s")
            params.append(filters['is_active'])

        if filters.get('rule_type'):
            where_clauses.append("rule_type = %s")
            params.append(filters['rule_type'])

        if filters.get('csi_code'):
            where_clauses.append("csi_code = %s")
            params.append(filters['csi_code'])

        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        query = f"""
            SELECT
                r.*,
                cm.csi_title,
                ss.standard_name
            FROM compliance_rules r
            LEFT JOIN csi_masterformat cm ON r.csi_code = cm.csi_code
            LEFT JOIN spec_standards ss ON r.spec_standard_id = ss.spec_standard_id
            {where_sql}
            ORDER BY r.priority ASC, r.rule_name
        """

        return execute_query(query, tuple(params) if params else None)
