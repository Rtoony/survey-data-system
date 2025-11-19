"""
SSM Mapping Service - Phase 28: Deterministic Tie-Breaking
Implements priority-based mapping resolution with condition count (specificity) as tie-breaker.
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
    Phase 28: Implements deterministic tie-breaking using condition count (specificity).
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

    def _check_mapping_match(self, mapping: Dict[str, Any], attributes: Dict[str, Any]) -> tuple[bool, int]:
        """
        Checks if ALL conditions in a mapping are met.

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

        # NOTE: Full condition evaluation logic is omitted here but assumed to pass for all entries
        # where feature_code matches, as per the previous prompt's instruction to focus on tie-breaking.
        # In a real implementation, this would evaluate each condition's operator (==, >=, etc.)
        # against the corresponding attribute value.
        is_match = True

        return is_match, condition_count

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
