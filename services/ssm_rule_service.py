# services/ssm_rule_service.py
from typing import Dict, Any, List
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SSMRuleService:
    """
    Executes automated behaviors defined by the resolved standards mapping.
    Handles Auto-labeling, Auto-connecting, and Validation checks.
    """

    def __init__(self):
        logger.info("SSMRuleService initialized.")

    def _execute_auto_label(self, attributes: Dict[str, Any], template: str) -> str:
        """Generates a label string from a template and point attributes."""

        # Simple string interpolation based on template format: ${ATTRIBUTE}
        final_label = template
        for key, value in attributes.items():
            placeholder = f"${{{key.upper()}}}"
            final_label = final_label.replace(placeholder, str(value))

        logger.info(f"AutoLabel executed. Generated label: '{final_label.replace('\\n', ' | ')}'")
        return final_label

    def _execute_auto_connect(self, attributes: Dict[str, Any]) -> bool:
        """
        Simulates logic for connecting the current point to the previous one
        (e.g., forming a pipe segment or polyline).
        """
        if attributes.get('CONNECT_NEXT', False) is True:
            # In a real system, this would query the last processed point's geometry
            logger.info("AutoConnect executed: Flag 'CONNECT_NEXT' found. Logic to connect pipe segment triggered.")
            return True
        logger.debug("AutoConnect not triggered.")
        return False

    def _execute_validation(self, attributes: Dict[str, Any], required_fields: List[str]) -> bool:
        """
        Checks if critical attributes are present for the feature.
        """
        missing = [field for field in required_fields if attributes.get(field) is None]

        if missing:
            logger.error(f"Validation FAILED. Missing required attributes: {', '.join(missing)}")
            return False

        logger.info("Validation PASSED: All required attributes are present.")
        return True

    def run_rules(self,
                  feature_code: str,
                  attributes: Dict[str, Any],
                  resolved_mapping: Dict[str, Any]) -> Dict[str, Any]:
        """
        The main execution loop for automation rules.
        """
        logger.info(f"Starting Rule Execution for {feature_code} (Mapping ID: {resolved_mapping.get('source_mapping_id')})")

        # Mocked Rules fetched from the resolved mapping, typically prioritizing order matters
        # The mapping tells the system which ruleset to run.
        ruleset = resolved_mapping.get("automation_ruleset", {})

        # 1. Prepare output structure
        actions_performed = {
            "label_text": None,
            "connected_to_previous": False,
            "validation_status": "PASS",
            "log": []
        }

        # --- Rule 1: Validation (usually runs first) ---
        required = ruleset.get("required_attributes", ["SIZE", "RIM_ELEV"])
        if not self._execute_validation(attributes, required):
            actions_performed["validation_status"] = "FAIL"

        # --- Rule 2: Auto-Connect ---
        if ruleset.get("enable_auto_connect", True):
            actions_performed["connected_to_previous"] = self._execute_auto_connect(attributes)

        # --- Rule 3: Auto-Label ---
        label_template = ruleset.get("label_template", "Feature: ${FEATURE_CODE}\nRIM: ${RIM_ELEV}")
        # Inject the feature code into attributes for the label template
        attributes['FEATURE_CODE'] = feature_code
        actions_performed["label_text"] = self._execute_auto_label(attributes, label_template)

        actions_performed["log"].append(f"Rules executed successfully for {feature_code}.")
        return actions_performed

# --- Example Execution (for testing the service) ---
if __name__ == '__main__':
    service = SSMRuleService()

    # 1. Mock a resolved mapping (normally from SSMMappingService)
    mock_mapping = {
        "source_mapping_id": 301,
        "layer": "C-UTIL-SD-MH-SPECIAL",
        "block": "SD-MH-60-PC",
        "automation_ruleset": {
            "required_attributes": ["SIZE", "RIM_ELEV", "INVERT_ELEV"],
            "enable_auto_connect": False, # Manholes don't auto-connect pipes
            "label_template": "MH-${SIZE}\nRIM: ${RIM_ELEV}\nINV: ${INVERT_ELEV}"
        }
    }

    # 2. Mock input data (Field data)
    input_data = {
        "SIZE": "60IN",
        "RIM_ELEV": 105.00,
        "INVERT_ELEV": 96.00,
        "MATERIAL": "PRECAST",
        "CONNECT_NEXT": False # Pipe feature would have this set to True
    }

    print("\n--- TEST CASE: SDMH Rules Execution ---")
    results = service.run_rules("SDMH", input_data, mock_mapping)
    print(json.dumps(results, indent=4))

    print("\n--- TEST CASE: Pipe Feature (Requires Auto-Connect) ---")
    mock_pipe_mapping = {
        "source_mapping_id": 402,
        "automation_ruleset": {
            "required_attributes": ["DEPTH", "TYPE"],
            "enable_auto_connect": True,
            "label_template": "PIPE: ${TYPE} @ ${DEPTH}FT"
        }
    }
    pipe_data = {
        "DEPTH": 4.5,
        "TYPE": "PVC",
        "CONNECT_NEXT": True
    }
    results_pipe = service.run_rules("SWP", pipe_data, mock_pipe_mapping)
    print(json.dumps(results_pipe, indent=4))
