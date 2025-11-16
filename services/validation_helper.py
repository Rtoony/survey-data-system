"""
Validation Helper Service
Provides functions for running validation rules and calculating data quality scores
"""

from database import get_db, execute_query
from datetime import datetime
import uuid


class ValidationHelper:
    """Helper class for validation operations"""

    def __init__(self):
        pass

    def run_validation_rule(self, rule, entity_ids=None, project_id=None):
        """
        Execute a validation rule and store results

        Args:
            rule: Dictionary containing rule details (id, sql_check_query, etc.)
            entity_ids: Optional list of specific entity IDs to validate
            project_id: Optional project ID to scope validation

        Returns:
            Dictionary with validation summary
        """
        try:
            # Build the SQL query
            check_query = rule['sql_check_query']

            # Add filters if provided
            if entity_ids:
                check_query = check_query.replace(' AND is_active = TRUE',
                                                  f" AND id = ANY(ARRAY{entity_ids}::UUID[]) AND is_active = TRUE")
            elif project_id:
                if 'WHERE' in check_query:
                    check_query = check_query.replace('WHERE', f"WHERE project_id = '{project_id}' AND")
                else:
                    check_query += f" WHERE project_id = '{project_id}'"

            # Execute validation query
            failing_entities = execute_query(check_query)

            # Store results in validation_results table
            with get_db() as conn:
                with conn.cursor() as cur:
                    # First, mark previous results for this rule as resolved if they passed
                    cur.execute("""
                        UPDATE validation_results
                        SET resolved_at = NOW()
                        WHERE rule_id = %s
                        AND status = 'fail'
                        AND resolved_at IS NULL
                        AND entity_id NOT IN %s
                    """, (rule['id'], tuple([e['id'] for e in failing_entities]) if failing_entities else ('00000000-0000-0000-0000-000000000000',)))

                    # Insert new failure records
                    for entity in failing_entities:
                        cur.execute("""
                            INSERT INTO validation_results
                            (rule_id, entity_type, entity_id, status, error_message, detected_at)
                            VALUES (%s, %s, %s, 'fail', %s, NOW())
                            ON CONFLICT DO NOTHING
                        """, (
                            rule['id'],
                            rule['entity_type'],
                            entity['id'],
                            f"Failed validation: {rule['rule_name']}"
                        ))

                    conn.commit()

            return {
                'rule_id': rule['id'],
                'rule_name': rule['rule_name'],
                'total_checked': len(failing_entities) if not entity_ids else len(entity_ids),
                'failures': len(failing_entities),
                'severity': rule['severity'],
                'status': 'completed'
            }

        except Exception as e:
            return {
                'rule_id': rule.get('id'),
                'rule_name': rule.get('rule_name', 'Unknown'),
                'status': 'error',
                'error': str(e)
            }

    def apply_auto_fix(self, validation_result_id, user_id=None):
        """
        Apply automatic fix for a validation result

        Args:
            validation_result_id: UUID of the validation result
            user_id: Optional user ID performing the fix

        Returns:
            Dictionary with fix status
        """
        try:
            # Get validation result and rule
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT vr.*, r.auto_fix_query, r.rule_name
                        FROM validation_results vr
                        JOIN validation_rules r ON vr.rule_id = r.id
                        WHERE vr.id = %s
                    """, (validation_result_id,))

                    result = cur.fetchone()

                    if not result:
                        return {'status': 'error', 'message': 'Validation result not found'}

                    if not result[7]:  # auto_fix_query column
                        return {'status': 'error', 'message': 'No auto-fix available for this rule'}

                    # Execute auto-fix query
                    auto_fix_query = result[7].replace('%(entity_id)s', f"'{result[3]}'")  # entity_id
                    cur.execute(auto_fix_query)

                    # Mark as resolved and auto-fixed
                    cur.execute("""
                        UPDATE validation_results
                        SET resolved_at = NOW(),
                            resolved_by_user_id = %s,
                            auto_fixed = TRUE,
                            status = 'pass'
                        WHERE id = %s
                    """, (user_id, validation_result_id))

                    conn.commit()

                    return {
                        'status': 'success',
                        'message': f'Auto-fix applied for {result[8]}',  # rule_name
                        'validation_result_id': validation_result_id
                    }

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def calculate_data_quality_score(self, project_id=None, entity_type=None):
        """
        Calculate overall data quality score based on validation results

        Args:
            project_id: Optional project ID to scope calculation
            entity_type: Optional entity type to scope calculation

        Returns:
            Float between 0-100 representing quality score
        """
        try:
            # Build query to get all active rules
            rules_query = "SELECT * FROM validation_rules WHERE is_active = TRUE"
            if entity_type:
                rules_query += f" AND entity_type = '{entity_type}'"

            rules = execute_query(rules_query)

            if not rules:
                return 100.0  # No rules defined = perfect score

            total_weight = 0
            weighted_passes = 0

            # Weight by severity
            severity_weights = {
                'error': 3,
                'warning': 2,
                'info': 1
            }

            for rule in rules:
                weight = severity_weights.get(rule['severity'], 1)

                # Count total entities that should pass this rule
                count_query = self._build_count_query(rule, project_id)
                total_entities = execute_query(count_query)
                total_count = total_entities[0]['count'] if total_entities else 0

                if total_count == 0:
                    continue

                # Count failures
                failures_query = f"""
                    SELECT COUNT(*) as count
                    FROM validation_results
                    WHERE rule_id = '{rule['id']}'
                    AND status = 'fail'
                    AND resolved_at IS NULL
                """

                if project_id:
                    # This is a simplification - in production you'd join to entity tables
                    pass

                failures = execute_query(failures_query)
                failure_count = failures[0]['count'] if failures else 0

                # Calculate pass rate for this rule
                pass_rate = (total_count - failure_count) / total_count if total_count > 0 else 1.0

                # Add to weighted totals
                total_weight += weight
                weighted_passes += (pass_rate * weight)

            # Calculate final score
            if total_weight == 0:
                return 100.0

            score = (weighted_passes / total_weight) * 100
            return round(score, 2)

        except Exception as e:
            print(f"Error calculating quality score: {str(e)}")
            return 0.0

    def _build_count_query(self, rule, project_id=None):
        """Build query to count total entities for a rule"""
        entity_type = rule['entity_type']

        query = f"SELECT COUNT(*) as count FROM {entity_type} WHERE is_active = TRUE"

        if project_id:
            query += f" AND project_id = '{project_id}'"

        return query

    def batch_resolve_issues(self, validation_result_ids, user_id=None):
        """
        Mark multiple validation results as resolved

        Args:
            validation_result_ids: List of validation result UUIDs
            user_id: Optional user ID performing the resolution

        Returns:
            Dictionary with resolution summary
        """
        try:
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE validation_results
                        SET resolved_at = NOW(),
                            resolved_by_user_id = %s,
                            status = 'pass'
                        WHERE id = ANY(%s::UUID[])
                        AND resolved_at IS NULL
                    """, (user_id, validation_result_ids))

                    resolved_count = cur.rowcount
                    conn.commit()

                    return {
                        'status': 'success',
                        'resolved_count': resolved_count
                    }

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def get_validation_summary(self, project_id=None, entity_type=None):
        """
        Get summary of validation results

        Args:
            project_id: Optional project ID filter
            entity_type: Optional entity type filter

        Returns:
            Dictionary with validation summary statistics
        """
        try:
            # Build base query
            query = """
                SELECT
                    vr.status,
                    r.severity,
                    r.rule_type,
                    COUNT(*) as count
                FROM validation_results vr
                JOIN validation_rules r ON vr.rule_id = r.id
                WHERE vr.resolved_at IS NULL
            """

            params = []

            if entity_type:
                query += " AND vr.entity_type = %s"
                params.append(entity_type)

            query += " GROUP BY vr.status, r.severity, r.rule_type"

            results = execute_query(query, params)

            # Aggregate results
            summary = {
                'total_issues': 0,
                'by_severity': {'error': 0, 'warning': 0, 'info': 0},
                'by_type': {},
                'by_status': {'pass': 0, 'fail': 0}
            }

            for row in results:
                summary['total_issues'] += row['count']
                summary['by_severity'][row['severity']] = summary['by_severity'].get(row['severity'], 0) + row['count']
                summary['by_type'][row['rule_type']] = summary['by_type'].get(row['rule_type'], 0) + row['count']
                summary['by_status'][row['status']] = summary['by_status'].get(row['status'], 0) + row['count']

            # Calculate quality score
            summary['quality_score'] = self.calculate_data_quality_score(project_id, entity_type)

            return summary

        except Exception as e:
            return {'error': str(e)}


# Convenience functions
def run_validation_rule(rule, entity_ids=None, project_id=None):
    """Run a validation rule"""
    helper = ValidationHelper()
    return helper.run_validation_rule(rule, entity_ids, project_id)


def apply_auto_fix(validation_result_id, user_id=None):
    """Apply auto-fix to a validation result"""
    helper = ValidationHelper()
    return helper.apply_auto_fix(validation_result_id, user_id)


def calculate_data_quality_score(project_id=None, entity_type=None):
    """Calculate data quality score"""
    helper = ValidationHelper()
    return helper.calculate_data_quality_score(project_id, entity_type)


def get_validation_summary(project_id=None, entity_type=None):
    """Get validation summary"""
    helper = ValidationHelper()
    return helper.get_validation_summary(project_id, entity_type)
