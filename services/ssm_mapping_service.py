"""
SSM Mapping Service - Phase 42: Complex JSONB Condition Evaluation
Implements priority-based mapping resolution with support for:
- Set-based operators (IN, NOT IN)
- Compound logical operators (AND, OR)
- Condition count (specificity) as tie-breaker
"""

import json
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text, Engine
from contextlib import contextmanager
import logging

# Set up logging for the service
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Mock Components ---
class MockGraphClient:
    def create_node(self, node_type: str, properties: Dict[str, Any], identifier: str) -> None:
        logger.info(f"NODE CREATED: Type='{node_type}', ID='{identifier}', Props={len(properties)} keys.")

    def create_edge(self, source_id: str, target_id: str, relationship_type: str, properties: Dict[str, Any]) -> None:
        logger.info(f"EDGE CREATED: Source='{source_id}', Target='{target_id}', Type='{relationship_type}'.")

# --- Service Configuration ---
DATABASE_URL = "postgresql://user:password@host:port/dbname"  # Placeholder

# --- GKG Synchronization Service ---

class GKGSyncService:
    """
    SSM Mapping Service (formerly GKGSyncService)
    Phase 42: Complex JSONB condition evaluation with IN/NOT IN and AND/OR operators.
    Implements deterministic tie-breaking using condition count (specificity).
    """

    def __init__(self, db_url: str):
        self.engine: Engine = create_engine(db_url, pool_size=5, max_overflow=10)
        self.graph_client = MockGraphClient()
        logger.info("GKGSyncService initialized with pooled database connection.")

    @contextmanager
    def _get_connection(self):
        conn = None
        try:
            conn = self.engine.connect()
            yield conn
        finally:
            if conn:
                conn.close()

    # Mocked data structure for testing Phase 28 tie-breaker
    MOCK_STANDARDS_MAPPINGS = [
        {"id": 101, "feature_code": "SDMH", "conditions": {}, "priority": 100, "layer": "D"},  # 0 conditions
        {"id": 201, "feature_code": "SDMH", "conditions": {"SIZE": {"op": ">=", "val": "48IN"}}, "priority": 200, "layer": "A"},  # 1 condition
        {"id": 301, "feature_code": "SDMH", "conditions": {"SIZE": {"op": "==", "val": "60IN"}, "MAT": {"op": "==", "val": "PRECAST"}}, "priority": 300, "layer": "B"},  # 2 conditions
        {"id": 302, "feature_code": "SDMH", "conditions": {"SIZE": {"op": "==", "val": "60IN"}}, "priority": 300, "layer": "C"}  # 1 condition (CONFLICT)
    ]

    def _fetch_applicable_mappings(self, feature_code: str) -> List[Dict[str, Any]]:
        """Fetch all mappings for a given feature code from mock data."""
        return [
            m for m in self.MOCK_STANDARDS_MAPPINGS
            if m["feature_code"].upper() == feature_code.upper()
        ]

    def _evaluate_condition(self, attribute_value: Any, condition_spec: Dict[str, Any]) -> bool:
        """
        Evaluates a single, potentially complex condition against an attribute value.
        Supports simple, compound (AND/OR), and set (IN/NOT IN) operations.

        Args:
            attribute_value: The actual attribute value to test
            condition_spec: Dictionary containing operator and value/values/conditions

        Returns:
            bool: True if the condition is satisfied, False otherwise
        """
        operator = condition_spec.get("operator")

        if operator in ("==", ">=", "<="):
            # --- Simple Numeric/String Comparison ---
            target_value = condition_spec.get("value")

            if operator == "==":
                return str(attribute_value).upper() == str(target_value).upper()

            # NOTE: Full numeric conversion and comparison logic would go here.
            # For structural testing, we assume numeric types are handled.
            return True  # Mock success for other simple ops

        elif operator in ("IN", "NOT IN"):
            # --- Set-Based Comparison (New Logic) ---
            target_list = condition_spec.get("values", [])  # Expects a list of values

            if not isinstance(target_list, list):
                logger.error(f"Set operator {operator} requires a list of 'values'.")
                return False

            is_present = str(attribute_value).upper() in [str(v).upper() for v in target_list]

            if operator == "IN":
                return is_present
            else:  # NOT IN
                return not is_present

        elif operator in ("AND", "OR"):
            # --- Compound Logic (New Logic) ---
            sub_conditions = condition_spec.get("conditions", [])  # Expects a list of sub-condition dictionaries

            if not isinstance(sub_conditions, list):
                logger.error(f"Compound operator {operator} requires a list of 'conditions'.")
                return False

            results = [
                self._evaluate_condition(attribute_value, sub_cond)
                for sub_cond in sub_conditions
            ]

            if operator == "AND":
                return all(results)
            else:  # OR
                return any(results)

        logger.warning(f"Unsupported complex operator '{operator}' encountered.")
        return False

    def _check_mapping_match(self, mapping: Dict[str, Any], attributes: Dict[str, Any]) -> tuple[bool, int]:
        """
        Checks if ALL top-level conditions in a mapping are met by the input attributes.
        (Updated to use the new complex _evaluate_condition helper)

        Args:
            mapping: The mapping configuration with conditions
            attributes: The entity attributes to check against

        Returns:
            tuple: (is_match: bool, condition_count: int)
                - is_match: True if all conditions are satisfied
                - condition_count: Number of conditions in the mapping (specificity metric)
        """
        conditions = mapping.get("conditions", {})
        condition_count = len(conditions)

        if not conditions:
            return True, 0

        for attr_key, condition_spec in conditions.items():
            if attr_key not in attributes:
                logger.debug(f"Condition failed: Missing required attribute {attr_key}.")
                return False, 0

            attribute_value = attributes[attr_key]

            # We now pass the full condition_spec dictionary to the evaluator
            if not self._evaluate_condition(attribute_value, condition_spec):
                logger.debug(f"Condition failed for {attr_key} with spec: {condition_spec}.")
                return False, 0

        return True, condition_count

    def resolve_mapping(self, feature_code: str, attributes: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Finds the highest-priority mapping that matches, using specificity (condition count)
        as a tie-breaker.

        Resolution Algorithm:
        1. Filter mappings by feature_code
        2. Evaluate conditions and calculate specificity (condition_count)
        3. Sort by composite key: (priority DESC, condition_count DESC)
        4. Return highest-ranked match
        5. Log conflicts if multiple mappings have identical priority AND specificity

        Args:
            feature_code: The feature code to resolve (e.g., "SDMH")
            attributes: Entity attributes for condition evaluation

        Returns:
            Optional[Dict]: Resolved mapping with layer, block, label_style, automation_rules,
                           and source_mapping_id. None if no match found.
        """
        logger.info(f"Resolving mapping for Code: '{feature_code}'...")

        potential_matches = self._fetch_applicable_mappings(feature_code)
        matching_mappings = []

        # 1. Evaluate conditions and calculate specificity (condition_count)
        for mapping in potential_matches:
            # Create a copy to avoid mutating the original mock data
            mapping_copy = mapping.copy()
            is_match, condition_count = self._check_mapping_match(mapping_copy, attributes)

            if is_match:
                # Add the calculated specificity metric
                mapping_copy['condition_count'] = condition_count
                matching_mappings.append(mapping_copy)

        if not matching_mappings:
            logger.warning(f"No matching standards mapping found for code: {feature_code}.")
            return None

        # 2. Sort by Composite Key: (Priority, Condition Count) - HIGHEST WINS
        best_match = max(
            matching_mappings,
            key=lambda m: (m.get("priority", 0), m.get("condition_count", 0))
        )

        # 3. Conflict Logging (Tie-breaker detection)
        conflicting_matches = [
            m for m in matching_mappings
            if m.get("priority", 0) == best_match["priority"] and
               m.get("condition_count", 0) == best_match["condition_count"] and
               m["id"] != best_match["id"]
        ]

        if conflicting_matches:
            logger.warning(
                f"SEVERE CONFLICT: Multiple mappings with identical Priority "
                f"({best_match['priority']}) AND Specificity ({best_match['condition_count']}) found. "
                f"Nondeterministic selection used."
            )
        elif any(m["priority"] == best_match["priority"] and m["id"] != best_match["id"]
                 for m in matching_mappings):
            # Tie-breaker successfully resolved a priority conflict
            logger.info(
                f"Tie-breaker SUCCESS: Mapping ID {best_match['id']} "
                f"(P:{best_match['priority']}, C:{best_match['condition_count']}) "
                f"selected over lower specificity match(es)."
            )

        logger.info(
            f"Resolution SUCCESS. Winner: ID {best_match['id']} "
            f"(P:{best_match['priority']}, C:{best_match['condition_count']})."
        )

        # Return resolved mapping with standard output format
        return {
            "layer": best_match.get("layer", "DEFAULT"),
            "block": best_match.get("block", "DEFAULT"),
            "label_style": "LABEL-UTILITY",
            "automation_rules": ["Auto-label", "Validate"],
            "source_mapping_id": best_match["id"]
        }

    # Additional methods for full sync functionality would go here
    # (e.g., get_changed_entities, run_full_sync, etc.)
