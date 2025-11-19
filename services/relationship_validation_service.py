"""
Relationship Validation Service
Rule enforcement and violation detection for the relationship graph.

This service validates relationships against defined rules including:
- Cardinality constraints (min/max relationships)
- Required relationships
- Forbidden relationships
- Conditional relationships

References:
    - docs/PHASE_3_COMPREHENSIVE_ANALYSIS.md
    - database/create_project_relationship_sets.sql
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db, execute_query as db_execute_query
from tools.db_utils import execute_query
from typing import Dict, List, Optional, Any
import json
from datetime import datetime


class RelationshipValidationService:
    """Service for validating relationships against rules"""

    def __init__(self):
        pass

    # ============================================================================
    # RULE MANAGEMENT
    # ============================================================================

    def create_validation_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new validation rule for relationship edges.

        Args:
            rule_data: Dictionary with rule properties:
                - rule_name (required)
                - rule_type (required): 'cardinality', 'required', 'forbidden', 'conditional'
                - description
                - project_id (optional): If set, rule applies only to that project
                - source_entity_type
                - target_entity_type
                - relationship_type
                - rule_config (dict): Type-specific configuration
                - severity: 'info', 'warning', 'error', 'critical'
                - is_active: Default True

        Returns:
            Created rule data
        """
        query = """
            INSERT INTO relationship_validation_rules (
                rule_name, rule_type, description, project_id,
                source_entity_type, target_entity_type, relationship_type,
                rule_config, severity, is_active
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """

        params = (
            rule_data['rule_name'],
            rule_data['rule_type'],
            rule_data.get('description'),
            rule_data.get('project_id'),
            rule_data.get('source_entity_type'),
            rule_data.get('target_entity_type'),
            rule_data.get('relationship_type'),
            json.dumps(rule_data.get('rule_config', {})),
            rule_data.get('severity', 'warning'),
            rule_data.get('is_active', True)
        )

        results = execute_query(query, params)
        return results[0] if results else None

    def get_validation_rules(
        self,
        project_id: Optional[str] = None,
        rule_type: Optional[str] = None,
        is_active: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get validation rules.

        Args:
            project_id: Filter by project (includes global rules if None)
            rule_type: Filter by rule type
            is_active: Filter by active status

        Returns:
            List of validation rules
        """
        conditions = []
        params = []

        if project_id is not None:
            conditions.append("(project_id = %s OR project_id IS NULL)")
            params.append(project_id)

        if rule_type is not None:
            conditions.append("rule_type = %s")
            params.append(rule_type)

        if is_active is not None:
            conditions.append("is_active = %s")
            params.append(is_active)

        where_clause = " AND ".join(conditions) if conditions else "TRUE"

        query = f"""
            SELECT * FROM relationship_validation_rules
            WHERE {where_clause}
            ORDER BY severity DESC, rule_type, rule_name
        """

        return execute_query(query, tuple(params))

    # ============================================================================
    # VALIDATION EXECUTION
    # ============================================================================

    def validate_project_relationships(
        self,
        project_id: str,
        rule_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Run all validation rules on a project's relationships.

        Args:
            project_id: Project UUID
            rule_types: Optional list of rule types to check

        Returns:
            List of violations found
        """
        violations = []

        # Get applicable rules
        rules = self.get_validation_rules(project_id=project_id, is_active=True)

        if rule_types:
            rules = [r for r in rules if r['rule_type'] in rule_types]

        for rule in rules:
            try:
                if rule['rule_type'] == 'cardinality':
                    violations.extend(self._check_cardinality_rule(project_id, rule))
                elif rule['rule_type'] == 'required':
                    violations.extend(self._check_required_rule(project_id, rule))
                elif rule['rule_type'] == 'forbidden':
                    violations.extend(self._check_forbidden_rule(project_id, rule))
                elif rule['rule_type'] == 'conditional':
                    violations.extend(self._check_conditional_rule(project_id, rule))
            except Exception as e:
                # Log error but continue with other rules
                print(f"Error checking rule {rule['rule_name']}: {e}")

        return violations

    def _check_cardinality_rule(
        self,
        project_id: str,
        rule: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Check cardinality constraints (min/max number of relationships).

        Rule config should contain:
        - min_count: Minimum required relationships
        - max_count: Maximum allowed relationships (null = unlimited)
        """
        violations = []
        config = rule.get('rule_config', {})
        if isinstance(config, str):
            config = json.loads(config)

        min_count = config.get('min_count', 0)
        max_count = config.get('max_count')

        # Build query to count relationships per entity
        query = """
            SELECT
                source_entity_type,
                source_entity_id,
                COUNT(*) as relationship_count
            FROM relationship_edges
            WHERE project_id = %s
              AND is_active = TRUE
        """

        params = [project_id]

        if rule.get('source_entity_type'):
            query += " AND source_entity_type = %s"
            params.append(rule['source_entity_type'])

        if rule.get('target_entity_type'):
            query += " AND target_entity_type = %s"
            params.append(rule['target_entity_type'])

        if rule.get('relationship_type'):
            query += " AND relationship_type = %s"
            params.append(rule['relationship_type'])

        query += """
            GROUP BY source_entity_type, source_entity_id
            HAVING COUNT(*) < %s
        """
        params.append(min_count)

        if max_count is not None:
            query += " OR COUNT(*) > %s"
            params.append(max_count)

        results = execute_query(query, tuple(params))

        for result in results:
            count = result['relationship_count']
            if count < min_count:
                message = f"Entity has {count} relationships but requires at least {min_count}"
            else:
                message = f"Entity has {count} relationships but maximum allowed is {max_count}"

            violations.append({
                'rule_id': rule.get('rule_id'),
                'rule_name': rule['rule_name'],
                'violation_type': 'cardinality_violation',
                'severity': rule.get('severity', 'warning'),
                'entity_type': result['source_entity_type'],
                'entity_id': str(result['source_entity_id']),
                'message': message,
                'details': {
                    'actual_count': count,
                    'min_count': min_count,
                    'max_count': max_count
                }
            })

        return violations

    def _check_required_rule(
        self,
        project_id: str,
        rule: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Check that required relationships exist.

        Rule specifies that entities of source_entity_type MUST have
        a relationship of relationship_type to target_entity_type.
        """
        violations = []

        if not rule.get('source_entity_type') or not rule.get('relationship_type'):
            return violations  # Invalid rule configuration

        # Find entities that should have the relationship but don't
        # This is a simplified check - in practice you'd need to query the entity table
        # to get all entities of the source type, then check which ones lack the relationship

        query = """
            SELECT DISTINCT source_entity_id
            FROM relationship_edges
            WHERE project_id = %s
              AND source_entity_type = %s
              AND is_active = TRUE
        """

        all_entities_query = """
            SELECT source_entity_id
            FROM relationship_edges
            WHERE project_id = %s
              AND source_entity_type = %s
              AND is_active = TRUE

            EXCEPT

            SELECT DISTINCT source_entity_id
            FROM relationship_edges
            WHERE project_id = %s
              AND source_entity_type = %s
              AND relationship_type = %s
              AND is_active = TRUE
        """

        params = [
            project_id,
            rule['source_entity_type'],
            project_id,
            rule['source_entity_type'],
            rule['relationship_type']
        ]

        if rule.get('target_entity_type'):
            all_entities_query += " AND target_entity_type = %s"
            params.append(rule['target_entity_type'])

        results = execute_query(all_entities_query, tuple(params))

        for result in results:
            violations.append({
                'rule_id': rule.get('rule_id'),
                'rule_name': rule['rule_name'],
                'violation_type': 'missing_required_relationship',
                'severity': rule.get('severity', 'error'),
                'entity_type': rule['source_entity_type'],
                'entity_id': str(result['source_entity_id']),
                'message': f"Required relationship of type '{rule['relationship_type']}' is missing",
                'details': {
                    'required_relationship_type': rule['relationship_type'],
                    'required_target_type': rule.get('target_entity_type')
                }
            })

        return violations

    def _check_forbidden_rule(
        self,
        project_id: str,
        rule: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Check for forbidden relationships that should not exist.
        """
        violations = []

        query = """
            SELECT *
            FROM relationship_edges
            WHERE project_id = %s
              AND is_active = TRUE
        """

        params = [project_id]

        if rule.get('source_entity_type'):
            query += " AND source_entity_type = %s"
            params.append(rule['source_entity_type'])

        if rule.get('target_entity_type'):
            query += " AND target_entity_type = %s"
            params.append(rule['target_entity_type'])

        if rule.get('relationship_type'):
            query += " AND relationship_type = %s"
            params.append(rule['relationship_type'])

        results = execute_query(query, tuple(params))

        for result in results:
            violations.append({
                'rule_id': rule.get('rule_id'),
                'rule_name': rule['rule_name'],
                'violation_type': 'forbidden_relationship',
                'severity': rule.get('severity', 'error'),
                'entity_type': result['source_entity_type'],
                'entity_id': str(result['source_entity_id']),
                'edge_id': str(result['edge_id']),
                'message': f"Forbidden relationship of type '{result['relationship_type']}' exists",
                'details': {
                    'source_entity_type': result['source_entity_type'],
                    'source_entity_id': str(result['source_entity_id']),
                    'target_entity_type': result['target_entity_type'],
                    'target_entity_id': str(result['target_entity_id']),
                    'relationship_type': result['relationship_type']
                }
            })

        return violations

    def _check_conditional_rule(
        self,
        project_id: str,
        rule: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Check conditional relationships.

        Rule config should contain:
        - condition: SQL-like condition to evaluate
        - then_require: Required relationship if condition is true
        """
        violations = []

        # Conditional rules are complex and would require custom SQL execution
        # This is a placeholder for the structure
        config = rule.get('rule_config', {})
        if isinstance(config, str):
            config = json.loads(config)

        # In a full implementation, you would:
        # 1. Evaluate the condition
        # 2. For entities matching the condition, check the then_require relationship
        # 3. Report violations for entities matching condition but lacking required relationship

        return violations

    # ============================================================================
    # VIOLATION MANAGEMENT
    # ============================================================================

    def log_violation(
        self,
        project_id: str,
        violation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Log a relationship violation.

        Args:
            project_id: Project UUID
            violation_data: Dictionary with violation details

        Returns:
            Created violation record
        """
        query = """
            INSERT INTO relationship_validation_violations (
                project_id, rule_id, violation_type, severity,
                entity_type, entity_id, edge_id,
                violation_message, details, status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """

        params = (
            project_id,
            violation_data.get('rule_id'),
            violation_data['violation_type'],
            violation_data.get('severity', 'warning'),
            violation_data.get('entity_type'),
            violation_data.get('entity_id'),
            violation_data.get('edge_id'),
            violation_data['message'],
            json.dumps(violation_data.get('details', {})),
            'open'
        )

        results = execute_query(query, params)
        return results[0] if results else None

    def get_violations(
        self,
        project_id: str,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get relationship violations for a project.

        Args:
            project_id: Project UUID
            status: Filter by status ('open', 'acknowledged', 'resolved', 'ignored')
            severity: Filter by severity
            limit: Maximum results

        Returns:
            List of violations
        """
        conditions = ["project_id = %s"]
        params = [project_id]

        if status:
            conditions.append("status = %s")
            params.append(status)

        if severity:
            conditions.append("severity = %s")
            params.append(severity)

        where_clause = " AND ".join(conditions)

        query = f"""
            SELECT * FROM relationship_validation_violations
            WHERE {where_clause}
            ORDER BY severity DESC, detected_at DESC
            LIMIT %s
        """
        params.append(limit)

        return execute_query(query, tuple(params))

    def resolve_violation(
        self,
        violation_id: str,
        resolution_notes: Optional[str] = None,
        resolved_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Mark a violation as resolved"""
        query = """
            UPDATE relationship_validation_violations
            SET
                status = 'resolved',
                resolution_notes = %s,
                resolved_by = %s,
                resolved_at = CURRENT_TIMESTAMP
            WHERE violation_id = %s
            RETURNING *
        """

        results = execute_query(query, (resolution_notes, resolved_by, violation_id))
        return results[0] if results else None

    # ============================================================================
    # QUICK VALIDATION CHECKS
    # ============================================================================

    def check_entity_compliance(
        self,
        project_id: str,
        entity_type: str,
        entity_id: str
    ) -> Dict[str, Any]:
        """
        Check compliance for a specific entity.

        Returns:
            Dictionary with compliance status and any violations
        """
        violations = []

        # Get rules applicable to this entity type
        rules = self.get_validation_rules(project_id=project_id, is_active=True)
        applicable_rules = [
            r for r in rules
            if not r.get('source_entity_type') or r['source_entity_type'] == entity_type
        ]

        for rule in applicable_rules:
            # Check each rule type
            if rule['rule_type'] == 'cardinality':
                # Get relationship count
                count_query = """
                    SELECT COUNT(*) as count
                    FROM relationship_edges
                    WHERE project_id = %s
                      AND source_entity_type = %s
                      AND source_entity_id = %s
                      AND is_active = TRUE
                """
                params = [project_id, entity_type, entity_id]

                if rule.get('relationship_type'):
                    count_query += " AND relationship_type = %s"
                    params.append(rule['relationship_type'])

                result = execute_query(count_query, tuple(params))
                count = result[0]['count'] if result else 0

                config = rule.get('rule_config', {})
                if isinstance(config, str):
                    config = json.loads(config)

                min_count = config.get('min_count', 0)
                max_count = config.get('max_count')

                if count < min_count or (max_count and count > max_count):
                    violations.append({
                        'rule_name': rule['rule_name'],
                        'violation_type': 'cardinality_violation',
                        'severity': rule['severity'],
                        'message': f"Has {count} relationships, expected {min_count}-{max_count or 'unlimited'}"
                    })

        return {
            'entity_type': entity_type,
            'entity_id': entity_id,
            'is_compliant': len(violations) == 0,
            'violation_count': len(violations),
            'violations': violations
        }
