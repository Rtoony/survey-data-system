"""
Project Relationship Set Service
Business logic for managing project relationship sets and dependency tracking.
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


class RelationshipSetService:
    """Service for managing project relationship sets"""
    
    # SECURITY: Regex pattern for valid SQL identifiers (column names in filters)
    VALID_IDENTIFIER_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
    # Valid operator suffixes
    VALID_SUFFIXES = ['_gte', '_lte', '_gt', '_lt']
    
    def __init__(self):
        self.registry = EntityRegistry()
    
    def _get_table_columns(self, table_name: str) -> set:
        """
        SECURITY: Get actual columns for a table from PostgreSQL information_schema.
        
        Returns:
            Set of valid column names for the table
        """
        try:
            query = """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = %s AND table_schema = 'public'
            """
            result = execute_query(query, (table_name,))
            return {row['column_name'] for row in result}
        except Exception as e:
            raise ValueError(f"Could not fetch columns for {table_name}: {e}")
    
    def _validate_filter_conditions(self, filter_conditions: dict, table_name: str) -> None:
        """
        SECURITY: Validate filter condition column names against actual table schema.
        Prevents SQL injection via crafted filter keys.
        
        Args:
            filter_conditions: Filter dict with column names and values
            table_name: Target table to validate against
            
        Raises:
            ValueError: If any column name is invalid or doesn't exist in table
        """
        if not filter_conditions:
            return
        
        # Get actual columns from database schema
        valid_columns = self._get_table_columns(table_name)
        
        invalid_columns = []
        for key in filter_conditions.keys():
            # Strip operator suffixes
            actual_key = key
            has_valid_suffix = False
            for suffix in self.VALID_SUFFIXES:
                if key.endswith(suffix):
                    actual_key = key[:-len(suffix)]
                    has_valid_suffix = True
                    break
            
            # Validate basic pattern
            if not self.VALID_IDENTIFIER_PATTERN.match(actual_key):
                invalid_columns.append(f"{key} (invalid identifier pattern)")
                continue
            
            # Check against table schema (WHITELIST)
            if actual_key not in valid_columns:
                invalid_columns.append(f"{key} (column not found in {table_name})")
                continue
            
            # If suffix was used, verify it's valid
            if key != actual_key and not has_valid_suffix:
                invalid_columns.append(f"{key} (invalid operator suffix)")
        
        if invalid_columns:
            raise ValueError(
                f"Invalid column names in filter_conditions: {', '.join(invalid_columns)}. "
                f"Columns must exist in table '{table_name}' and use valid suffixes: {', '.join(self.VALID_SUFFIXES)}"
            )
    
    # ============================================================================
    # RELATIONSHIP SET OPERATIONS
    # ============================================================================
    
    def get_sets_by_project(self, project_id: str, include_templates: bool = False) -> List[Dict]:
        """
        Get all relationship sets for a project.
        
        Args:
            project_id: Project UUID
            include_templates: If True, also include template sets
            
        Returns:
            List of relationship set summaries
        """
        query = """
            SELECT * FROM vw_relationship_set_summary
            WHERE project_id = %s OR (is_template = TRUE AND %s = TRUE)
            ORDER BY 
                is_template DESC,
                sync_status = 'out_of_sync' DESC,
                sync_status = 'incomplete' DESC,
                set_name
        """
        return execute_query(query, (project_id, include_templates))
    
    def get_set_detail(self, set_id: str) -> Optional[Dict]:
        """Get detailed information about a relationship set"""
        query = "SELECT * FROM project_relationship_sets WHERE set_id = %s"
        results = execute_query(query, (set_id,))
        return results[0] if results else None
    
    def create_set(self, data: Dict) -> Dict:
        """
        Create a new relationship set.
        
        Args:
            data: Dictionary with set properties
                - project_id (required unless is_template=True)
                - set_name (required)
                - set_code (optional)
                - description (optional)
                - category (optional)
                - tags (optional)
                - is_template (optional, default False)
                - requires_all_members (optional, default True)
                - created_by (optional)
                
        Returns:
            Created set data
        """
        query = """
            INSERT INTO project_relationship_sets (
                project_id, set_name, set_code, description, category, 
                tags, is_template, requires_all_members, created_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        
        params = (
            data.get('project_id'),
            data['set_name'],
            data.get('set_code'),
            data.get('description'),
            data.get('category'),
            data.get('tags', []),
            data.get('is_template', False),
            data.get('requires_all_members', True),
            data.get('created_by')
        )
        
        results = execute_query(query, params)
        return results[0] if results else None
    
    def update_set(self, set_id: str, data: Dict) -> Dict:
        """Update an existing relationship set"""
        query = """
            UPDATE project_relationship_sets
            SET 
                set_name = COALESCE(%s, set_name),
                set_code = COALESCE(%s, set_code),
                description = COALESCE(%s, description),
                category = COALESCE(%s, category),
                tags = COALESCE(%s, tags),
                status = COALESCE(%s, status),
                requires_all_members = COALESCE(%s, requires_all_members),
                updated_at = CURRENT_TIMESTAMP
            WHERE set_id = %s
            RETURNING *
        """
        
        params = (
            data.get('set_name'),
            data.get('set_code'),
            data.get('description'),
            data.get('category'),
            data.get('tags'),
            data.get('status'),
            data.get('requires_all_members'),
            set_id
        )
        
        results = execute_query(query, params)
        return results[0] if results else None
    
    def delete_set(self, set_id: str) -> bool:
        """Delete a relationship set (cascades to members, rules, violations)"""
        query = "DELETE FROM project_relationship_sets WHERE set_id = %s"
        execute_query(query, (set_id,))
        return True
    
    def apply_template(self, template_id: str, project_id: str) -> Dict:
        """
        Apply a template relationship set to a project.
        Creates a new set based on the template.
        """
        # Get template
        template = self.get_set_detail(template_id)
        if not template or not template['is_template']:
            raise ValueError("Invalid template ID")
        
        # Create new set from template
        new_set_data = {
            'project_id': project_id,
            'set_name': template['set_name'],
            'set_code': template['set_code'],
            'description': template['description'],
            'category': template['category'],
            'tags': template['tags'],
            'requires_all_members': template['requires_all_members'],
            'template_id': template_id
        }
        
        new_set = self.create_set(new_set_data)
        
        # Copy members from template
        template_members = self.get_members(template_id)
        for member in template_members:
            member_data = {
                'set_id': new_set['set_id'],
                'entity_type': member['entity_type'],
                'entity_table': member['entity_table'],
                'filter_conditions': member['filter_conditions'],
                'member_role': member['member_role'],
                'is_required': member['is_required'],
                'display_order': member['display_order'],
                'notes': member['notes']
            }
            self.add_member(member_data)
        
        # Copy rules from template
        template_rules = self.get_rules(template_id)
        for rule in template_rules:
            rule_data = {
                'set_id': new_set['set_id'],
                'rule_type': rule['rule_type'],
                'rule_name': rule['rule_name'],
                'description': rule['description'],
                'check_attribute': rule['check_attribute'],
                'expected_value': rule['expected_value'],
                'operator': rule['operator'],
                'rule_config': rule['rule_config'],
                'severity': rule['severity']
            }
            self.add_rule(rule_data)
        
        return new_set
    
    # ============================================================================
    # MEMBER OPERATIONS
    # ============================================================================
    
    def get_members(self, set_id: str) -> List[Dict]:
        """Get all members of a relationship set"""
        query = """
            SELECT * FROM project_relationship_members
            WHERE set_id = %s
            ORDER BY display_order, created_at
        """
        return execute_query(query, (set_id,))
    
    def add_member(self, data: Dict) -> Dict:
        """
        Add a member to a relationship set.
        
        Args:
            data: Dictionary with member properties
                - set_id (required)
                - entity_type (required)
                - entity_table (required)
                - entity_id (optional)
                - filter_conditions (optional JSONB)
                - member_role (optional)
                - is_required (optional, default True)
                - display_order (optional)
                - notes (optional)
                
        Raises:
            ValueError: If entity_type is not registered or entity_table is invalid
        """
        entity_type = data['entity_type']
        entity_table = data['entity_table']
        
        # SECURITY: Validate entity type and table
        if not self.registry.is_valid_entity_type(entity_type):
            raise ValueError(f"Invalid entity_type '{entity_type}'. Must be one of: {', '.join(self.registry.get_all_entity_types())}")
        
        if not self.registry.validate_table_name(entity_table):
            raise ValueError(f"Invalid entity_table '{entity_table}'. Not in entity registry.")
        
        # Verify entity_type matches entity_table
        expected_table = self.registry.get_table_name(entity_type)
        if expected_table != entity_table:
            raise ValueError(f"Entity type '{entity_type}' should use table '{expected_table}', not '{entity_table}'")
        
        # SECURITY: Validate filter_conditions against table schema (whitelist)
        if data.get('filter_conditions'):
            self._validate_filter_conditions(data['filter_conditions'], entity_table)
        
        query = """
            INSERT INTO project_relationship_members (
                set_id, entity_type, entity_table, entity_id,
                filter_conditions, member_role, is_required, 
                display_order, notes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        
        params = (
            data['set_id'],
            entity_type,
            entity_table,
            data.get('entity_id'),
            json.dumps(data.get('filter_conditions')) if data.get('filter_conditions') else None,
            data.get('member_role'),
            data.get('is_required', True),
            data.get('display_order', 0),
            data.get('notes')
        )
        
        results = execute_query(query, params)
        return results[0] if results else None
    
    def update_member(self, member_id: str, data: Dict) -> Dict:
        """Update a relationship set member"""
        query = """
            UPDATE project_relationship_members
            SET 
                member_role = COALESCE(%s, member_role),
                is_required = COALESCE(%s, is_required),
                display_order = COALESCE(%s, display_order),
                notes = COALESCE(%s, notes),
                updated_at = CURRENT_TIMESTAMP
            WHERE member_id = %s
            RETURNING *
        """
        
        params = (
            data.get('member_role'),
            data.get('is_required'),
            data.get('display_order'),
            data.get('notes'),
            member_id
        )
        
        results = execute_query(query, params)
        return results[0] if results else None
    
    def remove_member(self, member_id: str) -> bool:
        """Remove a member from a relationship set"""
        query = "DELETE FROM project_relationship_members WHERE member_id = %s"
        execute_query(query, (member_id,))
        return True
    
    # ============================================================================
    # RULE OPERATIONS
    # ============================================================================
    
    def get_rules(self, set_id: str) -> List[Dict]:
        """Get all rules for a relationship set"""
        query = """
            SELECT * FROM project_relationship_rules
            WHERE set_id = %s
            ORDER BY rule_type, created_at
        """
        return execute_query(query, (set_id,))
    
    def add_rule(self, data: Dict) -> Dict:
        """
        Add a rule to a relationship set.
        
        Args:
            data: Dictionary with rule properties
                - set_id (required)
                - rule_type (required): 'existence', 'link_integrity', 'metadata_consistency'
                - rule_name (required)
                - description (optional)
                - check_attribute (optional)
                - expected_value (optional)
                - operator (optional)
                - rule_config (optional JSONB)
                - severity (optional, default 'warning')
        """
        query = """
            INSERT INTO project_relationship_rules (
                set_id, rule_type, rule_name, description,
                check_attribute, expected_value, operator,
                rule_config, severity
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        
        params = (
            data['set_id'],
            data['rule_type'],
            data['rule_name'],
            data.get('description'),
            data.get('check_attribute'),
            data.get('expected_value'),
            data.get('operator'),
            json.dumps(data.get('rule_config')) if data.get('rule_config') else None,
            data.get('severity', 'warning')
        )
        
        results = execute_query(query, params)
        return results[0] if results else None
    
    def update_rule(self, rule_id: str, data: Dict) -> Dict:
        """Update a relationship set rule"""
        query = """
            UPDATE project_relationship_rules
            SET 
                rule_name = COALESCE(%s, rule_name),
                description = COALESCE(%s, description),
                check_attribute = COALESCE(%s, check_attribute),
                expected_value = COALESCE(%s, expected_value),
                operator = COALESCE(%s, operator),
                severity = COALESCE(%s, severity),
                is_active = COALESCE(%s, is_active),
                updated_at = CURRENT_TIMESTAMP
            WHERE rule_id = %s
            RETURNING *
        """
        
        params = (
            data.get('rule_name'),
            data.get('description'),
            data.get('check_attribute'),
            data.get('expected_value'),
            data.get('operator'),
            data.get('severity'),
            data.get('is_active'),
            rule_id
        )
        
        results = execute_query(query, params)
        return results[0] if results else None
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule from a relationship set"""
        query = "DELETE FROM project_relationship_rules WHERE rule_id = %s"
        execute_query(query, (rule_id,))
        return True
    
    # ============================================================================
    # VIOLATION OPERATIONS
    # ============================================================================
    
    def get_violations(self, set_id: str, status: Optional[str] = None) -> List[Dict]:
        """
        Get violations for a relationship set.
        
        Args:
            set_id: Relationship set UUID
            status: Optional status filter ('open', 'acknowledged', 'resolved', 'ignored')
        """
        if status:
            query = """
                SELECT * FROM project_relationship_violations
                WHERE set_id = %s AND status = %s
                ORDER BY severity DESC, detected_at DESC
            """
            return execute_query(query, (set_id, status))
        else:
            query = """
                SELECT * FROM project_relationship_violations
                WHERE set_id = %s
                ORDER BY status = 'open' DESC, severity DESC, detected_at DESC
            """
            return execute_query(query, (set_id,))
    
    def resolve_violation(self, violation_id: str, resolution_notes: Optional[str] = None, 
                         resolved_by: Optional[str] = None) -> Dict:
        """Mark a violation as resolved"""
        query = """
            UPDATE project_relationship_violations
            SET 
                status = 'resolved',
                resolution_notes = %s,
                resolved_by = %s,
                resolved_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE violation_id = %s
            RETURNING *
        """
        results = execute_query(query, (resolution_notes, resolved_by, violation_id))
        return results[0] if results else None
    
    def acknowledge_violation(self, violation_id: str) -> Dict:
        """Mark a violation as acknowledged (user has seen it)"""
        query = """
            UPDATE project_relationship_violations
            SET 
                status = 'acknowledged',
                updated_at = CURRENT_TIMESTAMP
            WHERE violation_id = %s
            RETURNING *
        """
        results = execute_query(query, (violation_id,))
        return results[0] if results else None
