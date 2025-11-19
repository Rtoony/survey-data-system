# services/gkg_sync_service.py (Refactored for Omega 2)
import json
from typing import List, Dict, Any, Optional
from database import get_db, execute_query  # Use central database helpers
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Mock Components (Retain existing structure) ---
class MockGraphClient:
    def create_node(self, node_type: str, properties: Dict[str, Any], identifier: str) -> None:
        logger.info(f"NODE CREATED: Type='{node_type}', ID='{identifier}', Props={len(properties)} keys.")

    def create_edge(self, source_id: str, target_id: str, relationship_type: str, properties: Dict[str, Any]) -> None:
        logger.info(f"EDGE CREATED: Source='{source_id}', Target='{target_id}', Type='{relationship_type}'.")

# --- GKG Synchronization Service (SSM Mapping Orchestrator) ---

class GKGSyncService:
    # Mocked data structure for testing (Must match structure from Phase 28/29)
    MOCK_STANDARDS_MAPPINGS = [
        {"id": 101, "feature_code": "SDMH", "conditions": {}, "priority": 100, "layer": "D"},
        {"id": 301, "feature_code": "SDMH", "conditions": {"SIZE": {"op": "==", "val": "60IN"}, "MAT": {"op": "==", "val": "PRECAST"}}, "priority": 300, "layer": "B"},
    ]

    def __init__(self):
        self.graph_client = MockGraphClient()
        logger.info("GKGSyncService initialized. Using centralized DB connection management.")

    # --- Utility Methods (Placeholder/Mocked) ---
    def _fetch_applicable_mappings(self, feature_code: str) -> List[Dict[str, Any]]:
        """
        Refactored: Mocks fetching data via a central connection pattern.

        MOCK ONLY: We continue to use the internal MOCK_STANDARDS_MAPPINGS
        until the full refactor is ready to hit the live database.

        NOTE: A real implementation would use the following pattern:
        from sqlalchemy.sql import select
        from data.ssm_schema import ssm_mappings
        with get_db() as conn:
            results = conn.execute(select(ssm_mappings)...).fetchall()
        """
        return [
            m for m in self.MOCK_STANDARDS_MAPPINGS
            if m["feature_code"].upper() == feature_code.upper()
        ]

    def _check_mapping_match(self, mapping: Dict[str, Any], attributes: Dict[str, Any]) -> tuple[bool, int]:
        # Mocked match: assume match is True, specificity is condition count
        return True, len(mapping.get("conditions", {}))

    # ** NEW METHOD FOR PHASE 33 **
    def _fetch_project_overrides(self, project_id: int) -> List[Dict[str, Any]]:
        """
        Mocks fetching client- or project-specific standards that supersede all others.
        """
        if project_id == 100:
            logger.info(f"PROJECT OVERRIDE FOUND: Project {project_id} mandates custom standards.")
            return [
                {
                    "id": 9000,
                    "feature_code": "SDMH",
                    "conditions": {"SIZE": {"op": "==", "val": "48IN"}},
                    "priority": 9999,  # Guaranteed winner
                    "layer": "CLIENT-48IN-MH",
                    "block": "CLIENT-SPEC-MH-48"
                }
            ]
        return []

    # ** MODIFIED RESOLUTION LOGIC FOR PHASE 33 **
    def resolve_mapping(self, feature_code: str, attributes: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Finds the highest-priority mapping that matches, incorporating Project Overrides.
        """
        logger.info(f"Resolving mapping for Code: '{feature_code}'...")

        # 1. Fetch Project Overrides (Highest Priority Layer)
        MOCK_PROJECT_ID = 100
        project_overrides = self._fetch_project_overrides(MOCK_PROJECT_ID)

        # 2. Fetch Global/Standard Mappings (Lower Priority Layers)
        global_matches = self._fetch_applicable_mappings(feature_code)

        # 3. Combine all potential matches. Order doesn't strictly matter here
        # because the priority score (9999) ensures overrides win the max() function.
        potential_matches = project_overrides + global_matches

        if project_overrides:
            logger.info(f"Project Override Layer applied: {len(project_overrides)} mapping(s) inserted at P=9999.")

        matching_mappings = []

        # 4. Evaluate conditions and calculate specificity (condition_count)
        for mapping in potential_matches:
            mapping_copy = mapping.copy()
            is_match, condition_count = self._check_mapping_match(mapping_copy, attributes)

            if is_match:
                mapping_copy['condition_count'] = condition_count
                matching_mappings.append(mapping_copy)

        if not matching_mappings:
            logger.warning(f"No matching standards mapping found for code: {feature_code}.")
            return None

        # 5. Determine the deterministic winner: Sort by (Priority, Condition Count)
        # P=9999 from project_overrides will ensure it wins if it's in the list.
        best_match = max(matching_mappings, key=lambda m: (m.get("priority", 0), m.get("condition_count", 0)))

        logger.info(f"Resolution SUCCESS. Final Winner (P={best_match['priority']}, C={best_match.get('condition_count', 0)}): ID {best_match['id']}.")

        return {
            "layer": best_match['layer'] if 'layer' in best_match else "DEFAULT",
            "block": best_match['block'] if 'block' in best_match else "DEFAULT",
            "source_mapping_id": best_match['id']
        }
