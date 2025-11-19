# services/ai_mapping_suggestor.py

from typing import Dict, Any, List, Optional
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Reusing the mock data structure from Phase 19 for consistency
MOCK_STANDARDS_MAPPINGS = [
    # 1. Default/Low Priority (Always matches)
    {"id": 100, "feature_code": "SDMH", "name": "SDMH Default", "conditions": {}, "priority": 100},
    # 2. Medium Priority (Requires SIZE)
    {"id": 200, "feature_code": "SDMH", "name": "SDMH 48-Inch Spec", "conditions": {"SIZE": {"operator": ">=", "value": "48IN"}}, "priority": 200},
    # 3. Highest Priority (Requires SIZE and MATERIAL)
    {"id": 300, "feature_code": "SDMH", "name": "SDMH Precast Concrete", "conditions": {"SIZE": {"operator": "==", "value": "60IN"}, "MATERIAL": {"operator": "==", "value": "PRECAST"}}, "priority": 300},
    # 4. Conflicting Highest Priority (Requires SIZE and JURISDICTION)
    {"id": 301, "feature_code": "SDMH", "name": "SDMH City Override (Conflict)", "conditions": {"SIZE": {"operator": "==", "value": "60IN"}, "JURISDICTION": {"operator": "==", "value": "SANTA_ROSA"}}, "priority": 300}
]

# Helper function (simplified from Phase 19)
def _check_condition(attr_value, operator, target_value) -> bool:
    """Simplified condition check for suggestion logic (assuming equality for simplicity)."""
    if operator == "==":
        return str(attr_value).upper() == str(target_value).upper()
    # Assume >=, <=, etc. pass if attribute is present and roughly comparable
    return attr_value is not None

class AIMappingSuggestorService:
    """
    AI-powered tool that analyzes input attributes against conditional mappings
    to provide suggestions, warnings, and required field hints.
    """

    def __init__(self):
        self.mappings = MOCK_STANDARDS_MAPPINGS
        logger.info("AIMappingSuggestorService initialized.")

    def get_suggestions(self, feature_code: str, current_attributes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Provides intelligent feedback based on attribute completeness and mapping priority.
        """
        logger.info(f"Analyzing {feature_code} with {len(current_attributes)} attributes for suggestions.")

        applicable_mappings = sorted(
            [m for m in self.mappings if m["feature_code"].upper() == feature_code.upper()],
            key=lambda m: m.get("priority", 0),
            reverse=True # Highest priority first
        )

        suggestions = {
            "resolved_mapping": None,
            "warnings": [],
            "suggestions": []
        }

        full_matches = []
        near_matches = {} # Maps mapping ID to required missing attributes

        # 1. Iterate and classify mappings
        for mapping in applicable_mappings:
            is_match = True
            missing_attrs = []

            for attr_key, condition_spec in mapping.get("conditions", {}).items():
                if attr_key not in current_attributes or current_attributes[attr_key] is None:
                    # Missing Attribute
                    is_match = False
                    missing_attrs.append(attr_key)
                    continue

                # Check if the existing attribute FAILS the condition (e.g., SIZE is 24IN but condition is >= 48IN)
                # NOTE: For simplicity, we only track MISSING here; a true implementation would check for failed conditions too.
                # if not _check_condition(current_attributes[attr_key], condition_spec['operator'], condition_spec['value']):
                #     is_match = False

            if is_match:
                full_matches.append(mapping)
            elif missing_attrs:
                # If it failed only because of missing attributes (and existing ones didn't fail a condition)
                near_matches[mapping["id"]] = {"name": mapping["name"], "priority": mapping["priority"], "missing": missing_attrs}

        # 2. Resolve final output
        if full_matches:
            # The actual resolved mapping is the one with the highest priority
            resolved = max(full_matches, key=lambda m: m["priority"])
            suggestions["resolved_mapping"] = resolved["name"]

            # Check for conflict warning
            top_priority = resolved["priority"]
            conflicting_matches = [m for m in full_matches if m["priority"] == top_priority and m["id"] != resolved["id"]]

            if conflicting_matches:
                suggestions["warnings"].append(f"CRITICAL CONFLICT: Multiple mappings ({resolved['name']} and others) match with the same priority ({top_priority}). Standards resolution is nondeterministic.")

        # 3. Suggest attributes for higher-priority near matches
        current_resolved_priority = full_matches[0]["priority"] if full_matches else 0

        for mid, data in near_matches.items():
            if data["priority"] > current_resolved_priority:
                suggestions["suggestions"].append(
                    f"To reach the high-priority mapping '{data['name']}' (Priority {data['priority']}), add the following attribute(s): {', '.join(data['missing'])}"
                )

        if not full_matches and not near_matches:
             suggestions["warnings"].append("No applicable default or specific mappings were found for this feature code.")

        return suggestions

# --- Example Execution (for testing the service) ---
if __name__ == '__main__':
    service = AIMappingSuggestorService()

    # 1. CASE: NEAR MATCH and DEFAULT MATCH (Should suggest attributes)
    print("\n--- TEST CASE 1: Suggest Missing Attributes ---")
    test_attrs_1 = {"SIZE": "60IN"} # Matches 100/200, needs MATERIAL/JURISDICTION for 300/301
    result_1 = service.get_suggestions("SDMH", test_attrs_1)
    print(json.dumps(result_1, indent=4))

    # 2. CASE: CRITICAL CONFLICT (Should match 300 and 301 simultaneously)
    print("\n--- TEST CASE 2: Critical Conflict Warning ---")
    test_attrs_2 = {"SIZE": "60IN", "MATERIAL": "PRECAST", "JURISDICTION": "SANTA_ROSA"}
    result_2 = service.get_suggestions("SDMH", test_attrs_2)
    print(json.dumps(result_2, indent=4))

    # 3. CASE: FULL MATCH (Should resolve to the highest single match)
    print("\n--- TEST CASE 3: Full Match - No Conflict/Suggestion ---")
    test_attrs_3 = {"SIZE": "48IN"}
    result_3 = service.get_suggestions("SDMH", test_attrs_3)
    print(json.dumps(result_3, indent=4))
