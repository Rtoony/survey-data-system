"""
Auto-Linking Service
Handles automatic spec-to-entity linking based on patterns and rules
"""

import uuid
import json
import re
from typing import List, Dict, Optional, Any
from db import get_db, execute_query
from services.spec_linking_service import SpecLinkingService


class AutoLinkingService:
    """Service for automatic specification linking based on patterns"""

    @staticmethod
    def create_auto_link_rule(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new auto-linking rule

        Args:
            data: Rule definition containing:
                - rule_name (required)
                - match_type (required)
                - match_expression (required, JSONB)
                - target_spec_id or target_csi_code (required)
                - link_type (default: 'governs')
                - confidence_threshold (default: 0.8)

        Returns:
            Created rule record
        """
        rule_id = uuid.uuid4()
        rule_code = data.get('rule_code') or f"AUTO_{str(rule_id)[:8].upper()}"

        query = """
            INSERT INTO auto_link_rules (
                rule_id, rule_name, rule_code, description, priority,
                match_type, match_expression, entity_types, layer_patterns,
                property_conditions, target_spec_id, target_csi_code,
                link_type, confidence_threshold, is_active, auto_apply,
                require_review, apply_to_all_projects, project_ids, created_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """

        params = (
            rule_id,
            data['rule_name'],
            rule_code,
            data.get('description'),
            data.get('priority', 100),
            data['match_type'],
            json.dumps(data['match_expression']),
            data.get('entity_types'),
            data.get('layer_patterns'),
            json.dumps(data.get('property_conditions')) if data.get('property_conditions') else None,
            data.get('target_spec_id'),
            data.get('target_csi_code'),
            data.get('link_type', 'governs'),
            data.get('confidence_threshold', 0.8),
            data.get('is_active', True),
            data.get('auto_apply', False),
            data.get('require_review', True),
            data.get('apply_to_all_projects', True),
            data.get('project_ids'),
            data.get('created_by')
        )

        result = execute_query(query, params)
        return result[0] if result else None

    @staticmethod
    def get_rule_by_id(rule_id: str) -> Optional[Dict[str, Any]]:
        """Get a single auto-link rule by ID"""
        query = """
            SELECT
                r.*,
                s.spec_number,
                s.spec_title,
                cm.csi_title
            FROM auto_link_rules r
            LEFT JOIN spec_library s ON r.target_spec_id = s.spec_library_id
            LEFT JOIN csi_masterformat cm ON r.target_csi_code = cm.csi_code
            WHERE r.rule_id = %s
        """

        result = execute_query(query, (rule_id,))
        return result[0] if result else None

    @staticmethod
    def get_applicable_rules(entity_type: str, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all active auto-link rules applicable to an entity type

        Args:
            entity_type: Type of entity
            project_id: Optional project filter

        Returns:
            List of applicable rules ordered by priority
        """
        where_clauses = ["r.is_active = TRUE"]
        params = []

        # Entity type filter
        where_clauses.append("(%s = ANY(r.entity_types) OR r.entity_types IS NULL)")
        params.append(entity_type)

        # Project scope filter
        if project_id:
            where_clauses.append("""
                (r.apply_to_all_projects = TRUE OR
                 %s = ANY(r.project_ids))
            """)
            params.append(project_id)

        where_sql = " AND ".join(where_clauses)

        query = f"""
            SELECT
                r.*,
                s.spec_number,
                s.spec_title,
                s.spec_library_id,
                cm.csi_title
            FROM auto_link_rules r
            LEFT JOIN spec_library s ON r.target_spec_id = s.spec_library_id
            LEFT JOIN csi_masterformat cm ON r.target_csi_code = cm.csi_code
            WHERE {where_sql}
            ORDER BY r.priority ASC
        """

        return execute_query(query, tuple(params))

    @staticmethod
    def evaluate_rule_match(rule: Dict[str, Any], entity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate if an entity matches an auto-link rule

        Args:
            rule: Auto-link rule from database
            entity: Entity properties

        Returns:
            Dict with: matches (bool), confidence (float), reason (str)
        """
        match_type = rule['match_type']
        match_expr = rule['match_expression']

        if isinstance(match_expr, str):
            match_expr = json.loads(match_expr)

        try:
            if match_type == 'layer_pattern':
                return AutoLinkingService._match_layer_pattern(rule, match_expr, entity)

            elif match_type == 'property_match':
                return AutoLinkingService._match_property(rule, match_expr, entity)

            elif match_type == 'entity_classification':
                return AutoLinkingService._match_classification(rule, match_expr, entity)

            elif match_type == 'spatial_proximity':
                return AutoLinkingService._match_spatial(rule, match_expr, entity)

            elif match_type == 'hybrid':
                return AutoLinkingService._match_hybrid(rule, match_expr, entity)

            else:
                return {
                    'matches': False,
                    'confidence': 0.0,
                    'reason': f"Unknown match type: {match_type}"
                }

        except Exception as e:
            return {
                'matches': False,
                'confidence': 0.0,
                'reason': f"Rule evaluation error: {str(e)}"
            }

    @staticmethod
    def _match_layer_pattern(rule: Dict, expr: Dict, entity: Dict) -> Dict:
        """Match based on layer name pattern (regex)"""
        pattern = expr.get('pattern')
        layer_name = entity.get('layer') or entity.get('layer_name')

        if not pattern or not layer_name:
            return {
                'matches': False,
                'confidence': 0.0,
                'reason': 'Missing pattern or layer name'
            }

        # Check if layer name matches pattern
        if re.match(pattern, layer_name, re.IGNORECASE):
            # Higher confidence for exact matches vs partial
            confidence = 0.95 if re.fullmatch(pattern, layer_name, re.IGNORECASE) else 0.85

            return {
                'matches': True,
                'confidence': confidence,
                'reason': f"Layer '{layer_name}' matches pattern '{pattern}'"
            }

        return {
            'matches': False,
            'confidence': 0.0,
            'reason': f"Layer '{layer_name}' does not match pattern '{pattern}'"
        }

    @staticmethod
    def _match_property(rule: Dict, expr: Dict, entity: Dict) -> Dict:
        """Match based on entity properties"""
        required_props = expr.get('properties', {})
        matches = []
        total_checks = len(required_props)

        if total_checks == 0:
            return {'matches': False, 'confidence': 0.0, 'reason': 'No properties to match'}

        for prop_name, expected_value in required_props.items():
            actual_value = entity.get(prop_name)

            if actual_value is None:
                matches.append(False)
            elif isinstance(expected_value, list):
                # Allow multiple valid values
                matches.append(actual_value in expected_value)
            else:
                matches.append(str(actual_value).lower() == str(expected_value).lower())

        match_count = sum(matches)
        confidence = match_count / total_checks

        threshold = rule.get('confidence_threshold', 0.8)

        return {
            'matches': confidence >= threshold,
            'confidence': confidence,
            'reason': f"Matched {match_count}/{total_checks} required properties"
        }

    @staticmethod
    def _match_classification(rule: Dict, expr: Dict, entity: Dict) -> Dict:
        """Match based on entity classification"""
        required_class = expr.get('classification')
        entity_class = entity.get('classification') or entity.get('entity_class')

        if not required_class:
            return {'matches': False, 'confidence': 0.0, 'reason': 'No classification specified'}

        if entity_class == required_class:
            return {
                'matches': True,
                'confidence': 0.9,
                'reason': f"Classification matches: {required_class}"
            }

        return {
            'matches': False,
            'confidence': 0.0,
            'reason': f"Classification '{entity_class}' does not match '{required_class}'"
        }

    @staticmethod
    def _match_spatial(rule: Dict, expr: Dict, entity: Dict) -> Dict:
        """Match based on spatial proximity (placeholder for future implementation)"""
        # TODO: Implement spatial matching using PostGIS
        return {
            'matches': False,
            'confidence': 0.0,
            'reason': 'Spatial matching not yet implemented'
        }

    @staticmethod
    def _match_hybrid(rule: Dict, expr: Dict, entity: Dict) -> Dict:
        """Combine multiple matching strategies"""
        strategies = expr.get('strategies', [])
        weights = expr.get('weights', [1.0] * len(strategies))

        if not strategies:
            return {'matches': False, 'confidence': 0.0, 'reason': 'No strategies defined'}

        total_confidence = 0.0
        total_weight = sum(weights)
        reasons = []

        for strategy, weight in zip(strategies, weights):
            result = AutoLinkingService.evaluate_rule_match(
                {**rule, 'match_type': strategy['type'], 'match_expression': strategy['expression']},
                entity
            )

            weighted_confidence = result['confidence'] * weight
            total_confidence += weighted_confidence
            reasons.append(f"{strategy['type']}: {result['confidence']:.2f}")

        final_confidence = total_confidence / total_weight if total_weight > 0 else 0.0
        threshold = rule.get('confidence_threshold', 0.8)

        return {
            'matches': final_confidence >= threshold,
            'confidence': final_confidence,
            'reason': f"Hybrid match: {', '.join(reasons)}"
        }

    @staticmethod
    def suggest_links_for_entity(entity_id: str, entity_type: str, entity_properties: Dict[str, Any],
                                   project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Generate spec link suggestions for a single entity

        Args:
            entity_id: Entity UUID
            entity_type: Type of entity
            entity_properties: Dictionary of entity properties
            project_id: Optional project context

        Returns:
            List of suggested links with confidence scores
        """
        # Get applicable rules
        rules = AutoLinkingService.get_applicable_rules(entity_type, project_id)

        suggestions = []

        for rule in rules:
            # Evaluate the match
            match_result = AutoLinkingService.evaluate_rule_match(rule, entity_properties)

            if match_result['matches']:
                # Determine target spec
                target_spec_id = rule.get('target_spec_id')

                if not target_spec_id and rule.get('target_csi_code'):
                    # Find specs matching the CSI code
                    specs = execute_query("""
                        SELECT spec_library_id FROM spec_library
                        WHERE csi_code = %s AND is_active = TRUE
                        LIMIT 1
                    """, (rule['target_csi_code'],))

                    if specs:
                        target_spec_id = specs[0]['spec_library_id']

                if target_spec_id:
                    suggestions.append({
                        'entity_id': entity_id,
                        'entity_type': entity_type,
                        'suggested_spec_id': target_spec_id,
                        'project_id': project_id,
                        'link_type': rule['link_type'],
                        'confidence_score': match_result['confidence'],
                        'suggestion_source': 'auto_link_rule',
                        'source_rule_id': rule['rule_id'],
                        'reasoning': match_result['reason'],
                        'rule_name': rule['rule_name']
                    })

        # Sort by confidence
        suggestions.sort(key=lambda x: x['confidence_score'], reverse=True)

        return suggestions

    @staticmethod
    def create_suggestions(suggestions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Save link suggestions to database

        Args:
            suggestions: List of suggestion dictionaries

        Returns:
            Summary of created suggestions
        """
        created_count = 0
        duplicate_count = 0

        with get_db() as conn:
            with conn.cursor() as cur:
                for suggestion in suggestions:
                    # Check for existing suggestion
                    check_query = """
                        SELECT suggestion_id FROM spec_link_suggestions
                        WHERE entity_id = %s
                            AND entity_type = %s
                            AND suggested_spec_id = %s
                            AND status = 'pending'
                    """

                    cur.execute(check_query, (
                        suggestion['entity_id'],
                        suggestion['entity_type'],
                        suggestion['suggested_spec_id']
                    ))

                    if cur.fetchone():
                        duplicate_count += 1
                        continue

                    # Create suggestion
                    insert_query = """
                        INSERT INTO spec_link_suggestions (
                            suggestion_id, entity_id, entity_type, suggested_spec_id,
                            project_id, link_type, confidence_score, suggestion_source,
                            source_rule_id, reasoning
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """

                    cur.execute(insert_query, (
                        uuid.uuid4(),
                        suggestion['entity_id'],
                        suggestion['entity_type'],
                        suggestion['suggested_spec_id'],
                        suggestion.get('project_id'),
                        suggestion.get('link_type', 'governs'),
                        suggestion['confidence_score'],
                        suggestion.get('suggestion_source', 'auto_link_rule'),
                        suggestion.get('source_rule_id'),
                        suggestion.get('reasoning')
                    ))

                    created_count += 1

                conn.commit()

        return {
            'created': created_count,
            'duplicates': duplicate_count
        }

    @staticmethod
    def apply_suggestion(suggestion_id: str, user_id: str, action: str = 'accepted') -> Dict[str, Any]:
        """
        Apply (accept/reject) a link suggestion

        Args:
            suggestion_id: UUID of suggestion
            user_id: User making the decision
            action: 'accepted', 'rejected', or 'modified'

        Returns:
            Result of the action
        """
        # Get the suggestion
        suggestion = execute_query("""
            SELECT * FROM spec_link_suggestions WHERE suggestion_id = %s
        """, (suggestion_id,))

        if not suggestion:
            return {'error': 'Suggestion not found'}

        suggestion = suggestion[0]

        if action == 'accepted':
            # Create the actual link
            link_result = SpecLinkingService.create_link({
                'spec_library_id': suggestion['suggested_spec_id'],
                'entity_id': suggestion['entity_id'],
                'entity_type': suggestion['entity_type'],
                'project_id': suggestion['project_id'],
                'link_type': suggestion['link_type'],
                'linked_by': user_id,
                'auto_linked': True,
                'auto_link_rule_id': suggestion['source_rule_id'],
                'link_confidence': suggestion['confidence_score']
            })

            # Update suggestion status
            execute_query("""
                UPDATE spec_link_suggestions
                SET status = 'accepted',
                    user_action = %s,
                    reviewed_by = %s,
                    reviewed_at = NOW()
                WHERE suggestion_id = %s
            """, (action, user_id, suggestion_id))

            # Update rule statistics
            if suggestion.get('source_rule_id'):
                execute_query("""
                    UPDATE auto_link_rules
                    SET times_applied = times_applied + 1,
                        times_successful = times_successful + 1,
                        last_applied = NOW()
                    WHERE rule_id = %s
                """, (suggestion['source_rule_id'],))

            return {
                'success': True,
                'link_created': True,
                'link_id': link_result['link_id'] if link_result else None
            }

        elif action == 'rejected':
            # Mark suggestion as rejected
            execute_query("""
                UPDATE spec_link_suggestions
                SET status = 'rejected',
                    user_action = %s,
                    reviewed_by = %s,
                    reviewed_at = NOW()
                WHERE suggestion_id = %s
            """, (action, user_id, suggestion_id))

            # Update rule statistics
            if suggestion.get('source_rule_id'):
                execute_query("""
                    UPDATE auto_link_rules
                    SET times_applied = times_applied + 1,
                        last_applied = NOW()
                    WHERE rule_id = %s
                """, (suggestion['source_rule_id'],))

            return {
                'success': True,
                'link_created': False
            }

        return {'error': 'Invalid action'}

    @staticmethod
    def auto_link_project_entities(project_id: str, entity_type: Optional[str] = None,
                                    auto_apply: bool = False) -> Dict[str, Any]:
        """
        Generate auto-link suggestions for all entities in a project

        Args:
            project_id: Project UUID
            entity_type: Optional filter for specific entity type
            auto_apply: If True, automatically create links (only for rules with auto_apply=True)

        Returns:
            Summary of suggestions generated and links created
        """
        # TODO: This is a placeholder - actual implementation would query
        # entity tables dynamically based on entity_type

        return {
            'message': 'Project auto-linking not yet fully implemented',
            'suggestions_created': 0,
            'links_created': 0
        }

    @staticmethod
    def get_pending_suggestions(project_id: Optional[str] = None, entity_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all pending link suggestions"""
        where_clauses = ["status = 'pending'"]
        params = []

        if project_id:
            where_clauses.append("project_id = %s")
            params.append(project_id)

        if entity_id:
            where_clauses.append("entity_id = %s")
            params.append(entity_id)

        where_sql = " AND ".join(where_clauses)

        query = f"""
            SELECT
                s.*,
                spec.spec_number,
                spec.spec_title,
                ss.standard_name,
                r.rule_name
            FROM spec_link_suggestions s
            INNER JOIN spec_library spec ON s.suggested_spec_id = spec.spec_library_id
            LEFT JOIN spec_standards ss ON spec.spec_standard_id = ss.spec_standard_id
            LEFT JOIN auto_link_rules r ON s.source_rule_id = r.rule_id
            WHERE {where_sql}
            ORDER BY s.confidence_score DESC, s.created_at DESC
        """

        return execute_query(query, tuple(params) if params else None)

    @staticmethod
    def get_all_auto_link_rules(active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all auto-link rules"""
        where_clause = "WHERE is_active = TRUE" if active_only else ""

        query = f"""
            SELECT
                r.*,
                s.spec_number,
                s.spec_title,
                cm.csi_title
            FROM auto_link_rules r
            LEFT JOIN spec_library s ON r.target_spec_id = s.spec_library_id
            LEFT JOIN csi_masterformat cm ON r.target_csi_code = cm.csi_code
            {where_clause}
            ORDER BY r.priority ASC, r.rule_name
        """

        return execute_query(query)

    @staticmethod
    def update_auto_link_rule(rule_id: str, data: Dict[str, Any]) -> bool:
        """Update an auto-link rule"""
        allowed_fields = [
            'rule_name', 'description', 'priority', 'match_expression',
            'entity_types', 'layer_patterns', 'property_conditions',
            'target_spec_id', 'target_csi_code', 'link_type',
            'confidence_threshold', 'is_active', 'auto_apply',
            'require_review', 'apply_to_all_projects', 'project_ids',
            'updated_by'
        ]

        update_fields = []
        params = []

        for field in allowed_fields:
            if field in data:
                if field in ['match_expression', 'property_conditions']:
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
            UPDATE auto_link_rules
            SET {', '.join(update_fields)}
            WHERE rule_id = %s
            RETURNING rule_id
        """

        result = execute_query(query, tuple(params))
        return len(result) > 0

    @staticmethod
    def delete_auto_link_rule(rule_id: str) -> bool:
        """Delete an auto-link rule"""
        query = "DELETE FROM auto_link_rules WHERE rule_id = %s RETURNING rule_id"
        result = execute_query(query, (rule_id,))
        return len(result) > 0
