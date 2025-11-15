"""
Relationship Set Sync Checker
Implements sync checking logic for relationship sets (Checks #1-3).
SECURITY: Uses Entity Registry to prevent SQL injection vulnerabilities.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.db_utils import execute_query
from services.entity_registry import EntityRegistry
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
import re


class RelationshipSyncChecker:
    """Service for checking relationship set sync status and detecting violations"""
    
    # SECURITY: Regex pattern for valid SQL identifiers (column names)
    VALID_IDENTIFIER_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
    
    def __init__(self):
        self.registry = EntityRegistry()
        # Cache for table columns (table_name -> set of column names)
        self._column_cache = {}
    
    def _get_table_columns(self, table_name: str) -> set:
        """
        SECURITY: Get actual columns for a table from PostgreSQL information_schema.
        Caches results to avoid repeated queries.
        
        Returns:
            Set of valid column names for the table
        """
        if table_name not in self._column_cache:
            try:
                query = """
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = %s AND table_schema = 'public'
                """
                result = execute_query(query, (table_name,))
                self._column_cache[table_name] = {row['column_name'] for row in result}
            except Exception as e:
                print(f"Warning: Could not fetch columns for {table_name}: {e}")
                self._column_cache[table_name] = set()
        
        return self._column_cache[table_name]
    
    def _is_valid_column_name(self, name: str, table_name: str) -> bool:
        """
        SECURITY: Validate that a column name exists in the target table.
        
        Args:
            name: Column name to validate
            table_name: Table to check against
            
        Returns:
            True if column exists in table, False otherwise
        """
        # First check basic pattern
        if not self.VALID_IDENTIFIER_PATTERN.match(name):
            return False
        
        # Then check against actual table columns (whitelist)
        valid_columns = self._get_table_columns(table_name)
        return name in valid_columns
    
    # ============================================================================
    # CHECK #1: EXISTENCE CHECK
    # ============================================================================
    
    def check_existence(self, set_id: str) -> List[Dict]:
        """
        Check #1: Verify that all required members exist in the database.
        
        Detects:
        - Missing entities (entity_id specified but doesn't exist in entity_table)
        - Empty filtered queries (filter_conditions specified but returns no results)
        
        Returns:
            List of violations found
        """
        violations = []
        
        # Get all members for this set
        members_query = """
            SELECT * FROM project_relationship_members
            WHERE set_id = %s
        """
        members = execute_query(members_query, (set_id,))
        
        if not members:
            return violations
        
        for member in members:
            member_id = member['member_id']
            entity_type = member['entity_type']
            entity_table = member['entity_table']
            entity_id = member['entity_id']
            filter_conditions = member['filter_conditions']
            is_required = member['is_required']
            
            exists = False
            violation_details = {}
            
            # Validate table name to prevent SQL injection
            if not self.registry.validate_table_name(entity_table):
                violation_details = {
                    'check_type': 'invalid_table',
                    'entity_table': entity_table,
                    'error': f'Table {entity_table} not registered in entity registry'
                }
                exists = False
            else:
                # Get correct primary key from registry
                table_info = self.registry.get_table_info(entity_type)
                if not table_info:
                    violation_details = {
                        'check_type': 'unknown_entity_type',
                        'entity_type': entity_type,
                        'error': f'Entity type {entity_type} not registered'
                    }
                    exists = False
                else:
                    table_name, pk_column = table_info
                    
                    # Case 1: Specific entity_id provided
                    if entity_id:
                        check_query = f"""
                            SELECT COUNT(*) as count 
                            FROM {table_name} 
                            WHERE {pk_column} = %s
                        """
                        try:
                            result = execute_query(check_query, (entity_id,))
                            exists = result[0]['count'] > 0 if result else False
                            
                            if not exists:
                                violation_details = {
                                    'check_type': 'specific_entity',
                                    'entity_id': str(entity_id),
                                    'entity_table': entity_table,
                                    'primary_key': pk_column
                                }
                        except Exception as e:
                            violation_details = {
                                'check_type': 'specific_entity',
                                'entity_id': str(entity_id),
                                'entity_table': entity_table,
                                'error': str(e)
                            }
                    
                    # Case 2: Filter conditions provided (metadata-based query)
                    elif filter_conditions:
                        where_clauses = []
                        params = []
                        invalid_columns = []
                        
                        # Build WHERE clause safely
                        for key, value in filter_conditions.items():
                            # Extract operator suffix
                            if key.endswith('_gte'):
                                actual_key = key[:-4]
                                operator = '>='
                            elif key.endswith('_lte'):
                                actual_key = key[:-4]
                                operator = '<='
                            elif key.endswith('_gt'):
                                actual_key = key[:-3]
                                operator = '>'
                            elif key.endswith('_lt'):
                                actual_key = key[:-3]
                                operator = '<'
                            else:
                                actual_key = key
                                operator = '='
                            
                            # SECURITY: Validate column name against table schema (whitelist)
                            if not self._is_valid_column_name(actual_key, table_name):
                                invalid_columns.append(actual_key)
                                continue
                            
                            # Use parameterized query for values (no value injection)
                            where_clauses.append(f"{actual_key} {operator} %s")
                            params.append(value)
                        
                        # Check if any columns were invalid
                        if invalid_columns:
                            violation_details = {
                                'check_type': 'invalid_filter',
                                'error': f'Invalid column names in filter: {", ".join(invalid_columns)}',
                                'filter_conditions': filter_conditions
                            }
                            exists = False
                        elif not where_clauses:
                            # All conditions were invalid
                            violation_details = {
                                'check_type': 'empty_filter',
                                'error': 'No valid filter conditions',
                                'filter_conditions': filter_conditions
                            }
                            exists = False
                        else:
                            where_clause = " AND ".join(where_clauses)
                            check_query = f"""
                                SELECT COUNT(*) as count 
                                FROM {table_name} 
                                WHERE {where_clause}
                            """
                            
                            try:
                                result = execute_query(check_query, tuple(params))
                                exists = result[0]['count'] > 0 if result else False
                                
                                if not exists:
                                    violation_details = {
                                        'check_type': 'filtered_query',
                                        'filter_conditions': filter_conditions,
                                        'entity_table': entity_table,
                                        'where_clause': where_clause
                                    }
                            except Exception as e:
                                violation_details = {
                                    'check_type': 'filtered_query',
                                    'filter_conditions': filter_conditions,
                                    'entity_table': entity_table,
                                    'error': str(e)
                                }
            
            # Update member existence status
            try:
                update_query = """
                    UPDATE project_relationship_members
                    SET exists = %s, last_verified_at = CURRENT_TIMESTAMP
                    WHERE member_id = %s
                """
                execute_query(update_query, (exists, member_id))
            except Exception as e:
                # Log but don't fail the check
                print(f"Warning: Could not update member status: {e}")
            
            # Create violation if entity doesn't exist and is required
            if not exists and is_required:
                severity = 'error' if is_required else 'warning'
                violation_message = self._format_existence_violation_message(
                    entity_type, entity_id, filter_conditions, violation_details
                )
                
                violations.append({
                    'set_id': set_id,
                    'member_id': member_id,
                    'violation_type': 'missing_element',
                    'severity': severity,
                    'violation_message': violation_message,
                    'details': violation_details,
                    'entity_type': entity_type,
                    'entity_table': entity_table,
                    'entity_id': entity_id
                })
        
        return violations
    
    def _format_existence_violation_message(self, entity_type: str, entity_id: Optional[str], 
                                            filter_conditions: Optional[dict], 
                                            details: dict) -> str:
        """Format a human-readable message for existence violations"""
        error = details.get('error')
        if error:
            return f"Error checking {entity_type}: {error}"
        
        if entity_id:
            return f"Required {entity_type} with ID {entity_id} not found in database"
        elif filter_conditions:
            condition_str = ", ".join([f"{k}={v}" for k, v in filter_conditions.items()])
            return f"Required {entity_type} matching conditions ({condition_str}) not found"
        else:
            return f"Required {entity_type} not found"
    
    # ============================================================================
    # CHECK #2: LINK INTEGRITY CHECK
    # ============================================================================
    
    def check_link_integrity(self, set_id: str) -> List[Dict]:
        """
        Check #2: Detect broken relationships from branching or deletion.
        
        Detects:
        - Entities that were branched (original deleted, new copy created)
        - Entities that were deleted without replacement
        - Entities with mismatched parent references
        
        Returns:
            List of violations found
        """
        violations = []
        
        # Get members with specific entity IDs
        members_query = """
            SELECT * FROM project_relationship_members
            WHERE set_id = %s AND entity_id IS NOT NULL
        """
        members = execute_query(members_query, (set_id,))
        
        if not members:
            return violations
        
        for member in members:
            member_id = member['member_id']
            entity_type = member['entity_type']
            entity_table = member['entity_table']
            entity_id = member['entity_id']
            
            # Validate table and get primary key
            if not self.registry.validate_table_name(entity_table):
                continue
            
            table_info = self.registry.get_table_info(entity_type)
            if not table_info:
                continue
            
            table_name, pk_column = table_info
            
            # Check if entity exists
            check_query = f"""
                SELECT {pk_column}, created_at, updated_at 
                FROM {table_name} 
                WHERE {pk_column} = %s
            """
            
            try:
                result = execute_query(check_query, (entity_id,))
                
                if not result:
                    # Entity doesn't exist - check if there's a potential replacement
                    # Look for recently created entities of same type
                    replacement_query = f"""
                        SELECT {pk_column}, created_at
                        FROM {table_name}
                        WHERE created_at > (
                            SELECT created_at 
                            FROM project_relationship_members 
                            WHERE member_id = %s
                        )
                        ORDER BY created_at DESC
                        LIMIT 5
                    """
                    
                    try:
                        replacements = execute_query(replacement_query, (member_id,))
                    except:
                        replacements = []
                    
                    if replacements:
                        violation_message = (
                            f"{entity_type} (ID: {entity_id}) was deleted or branched. "
                            f"Found {len(replacements)} potential replacement(s) created since this relationship was established."
                        )
                        severity = 'warning'
                        details = {
                            'check_type': 'branched_or_deleted',
                            'original_id': str(entity_id),
                            'potential_replacements': [
                                {
                                    'id': str(r[pk_column]),
                                    'created_at': r['created_at'].isoformat() if r.get('created_at') else None
                                }
                                for r in replacements
                            ]
                        }
                    else:
                        violation_message = (
                            f"{entity_type} (ID: {entity_id}) was deleted "
                            f"and no replacement was found."
                        )
                        severity = 'error'
                        details = {
                            'check_type': 'deleted_no_replacement',
                            'original_id': str(entity_id)
                        }
                    
                    violations.append({
                        'set_id': set_id,
                        'member_id': member_id,
                        'violation_type': 'broken_link',
                        'severity': severity,
                        'violation_message': violation_message,
                        'details': details,
                        'entity_type': entity_type,
                        'entity_table': entity_table,
                        'entity_id': entity_id
                    })
                    
            except Exception as e:
                violations.append({
                    'set_id': set_id,
                    'member_id': member_id,
                    'violation_type': 'check_error',
                    'severity': 'warning',
                    'violation_message': f"Error checking link integrity for {entity_type}: {str(e)}",
                    'details': {'error': str(e)},
                    'entity_type': entity_type,
                    'entity_table': entity_table,
                    'entity_id': entity_id
                })
        
        return violations
    
    # ============================================================================
    # CHECK #3: METADATA CONSISTENCY CHECK
    # ============================================================================
    
    def check_metadata_consistency(self, set_id: str) -> List[Dict]:
        """
        Check #3: Verify that attributes match across related members.
        
        Uses rules defined in project_relationship_rules with rule_type='metadata_consistency'
        to check if specified attributes are consistent across all members.
        
        Example: All members should have material='PVC' or all should have matching revision_date.
        
        Returns:
            List of violations found
        """
        violations = []
        
        # Get all active metadata consistency rules for this set
        rules_query = """
            SELECT * FROM project_relationship_rules
            WHERE set_id = %s 
              AND rule_type = 'metadata_consistency'
              AND is_active = TRUE
        """
        rules = execute_query(rules_query, (set_id,))
        
        if not rules:
            return violations  # No rules to check
        
        # Get all members with entity IDs
        members_query = """
            SELECT * FROM project_relationship_members
            WHERE set_id = %s AND entity_id IS NOT NULL
        """
        members = execute_query(members_query, (set_id,))
        
        if len(members) < 2:
            return violations  # Need at least 2 members to check consistency
        
        # Check each rule
        for rule in rules:
            rule_id = rule['rule_id']
            check_attribute = rule['check_attribute']
            expected_value = rule['expected_value']
            operator = rule['operator'] or 'equals'
            severity = rule['severity'] or 'warning'
            
            # Collect attribute values from all members
            member_values = []
            
            for member in members:
                entity_table = member['entity_table']
                entity_id = member['entity_id']
                entity_type = member['entity_type']
                
                # Validate table
                if not self.registry.validate_table_name(entity_table):
                    continue
                
                table_info = self.registry.get_table_info(entity_type)
                if not table_info:
                    continue
                
                table_name, pk_column = table_info
                
                # Query for the attribute value
                try:
                    attr_query = f"""
                        SELECT {check_attribute} 
                        FROM {table_name} 
                        WHERE {pk_column} = %s
                    """
                    result = execute_query(attr_query, (entity_id,))
                    
                    if result:
                        attr_value = result[0].get(check_attribute)
                        member_values.append({
                            'member_id': member['member_id'],
                            'entity_type': entity_type,
                            'entity_id': str(entity_id),
                            'attribute_value': attr_value
                        })
                except Exception as e:
                    member_values.append({
                        'member_id': member['member_id'],
                        'entity_type': entity_type,
                        'entity_id': str(entity_id),
                        'attribute_value': None,
                        'error': str(e)
                    })
            
            # Check consistency based on operator
            if operator == 'equals' and expected_value:
                # All members should have the expected value
                mismatches = [
                    mv for mv in member_values 
                    if str(mv.get('attribute_value')) != str(expected_value)
                ]
                
                if mismatches:
                    violation_message = (
                        f"Metadata mismatch: {check_attribute} should be '{expected_value}' "
                        f"but {len(mismatches)} member(s) have different values"
                    )
                    violations.append({
                        'set_id': set_id,
                        'rule_id': rule_id,
                        'violation_type': 'metadata_mismatch',
                        'severity': severity,
                        'violation_message': violation_message,
                        'details': {
                            'check_attribute': check_attribute,
                            'expected_value': expected_value,
                            'mismatches': mismatches
                        }
                    })
            
            elif operator == 'all_match':
                # All members should have the same value (but we don't specify what it should be)
                unique_values = set(str(mv.get('attribute_value')) for mv in member_values)
                
                if len(unique_values) > 1:
                    violation_message = (
                        f"Metadata inconsistency: {check_attribute} has {len(unique_values)} different values across members"
                    )
                    violations.append({
                        'set_id': set_id,
                        'rule_id': rule_id,
                        'violation_type': 'metadata_mismatch',
                        'severity': severity,
                        'violation_message': violation_message,
                        'details': {
                            'check_attribute': check_attribute,
                            'unique_values': list(unique_values),
                            'member_values': member_values
                        }
                    })
        
        return violations
    
    # ============================================================================
    # MASTER CHECK FUNCTION
    # ============================================================================
    
    def run_all_checks(self, set_id: str, clear_existing: bool = True) -> Dict:
        """
        Run all sync checks for a relationship set.
        
        Args:
            set_id: Relationship set UUID
            clear_existing: If True, delete existing violations before running checks
            
        Returns:
            Summary of checks performed and violations found
        """
        # Clear existing violations if requested
        if clear_existing:
            try:
                clear_query = "DELETE FROM project_relationship_violations WHERE set_id = %s"
                execute_query(clear_query, (set_id,))
            except Exception as e:
                print(f"Warning: Could not clear existing violations: {e}")
        
        # Run all three checks
        existence_violations = self.check_existence(set_id)
        link_integrity_violations = self.check_link_integrity(set_id)
        metadata_violations = self.check_metadata_consistency(set_id)
        
        all_violations = existence_violations + link_integrity_violations + metadata_violations
        
        # Insert violations into database
        for violation in all_violations:
            try:
                insert_query = """
                    INSERT INTO project_relationship_violations (
                        set_id, rule_id, member_id, violation_type, severity,
                        violation_message, details, entity_type, entity_table, entity_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                execute_query(insert_query, (
                    violation.get('set_id'),
                    violation.get('rule_id'),
                    violation.get('member_id'),
                    violation['violation_type'],
                    violation['severity'],
                    violation['violation_message'],
                    json.dumps(violation.get('details', {})),
                    violation.get('entity_type'),
                    violation.get('entity_table'),
                    violation.get('entity_id')
                ))
            except Exception as e:
                print(f"Warning: Could not insert violation: {e}")
        
        # Return summary
        return {
            'set_id': set_id,
            'checks_performed': ['existence', 'link_integrity', 'metadata_consistency'],
            'total_violations': len(all_violations),
            'existence_violations': len(existence_violations),
            'link_integrity_violations': len(link_integrity_violations),
            'metadata_violations': len(metadata_violations),
            'violations_by_severity': self._count_by_severity(all_violations),
            'timestamp': datetime.now().isoformat()
        }
    
    def _count_by_severity(self, violations: List[Dict]) -> Dict[str, int]:
        """Count violations by severity level"""
        counts = {'critical': 0, 'error': 0, 'warning': 0, 'info': 0}
        for v in violations:
            severity = v.get('severity', 'warning')
            counts[severity] = counts.get(severity, 0) + 1
        return counts
