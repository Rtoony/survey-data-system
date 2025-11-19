# services/specification_manager.py
from typing import Dict, Any, List, Optional
import logging
import json
import uuid

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Mock Data Storage ---
MOCK_SPECIFICATIONS = {
    "15400-DI": {
        "title": "Ductile Iron Pipe Installation",
        "active": True,
        "required_attributes": ["PIPE_CLASS", "PRESSURE_RATING"],
        "mapping_overrides": {
            "feature_code": "WL",
            "conditions": {"SIZE": {"operator": ">", "value": "12IN"}},
            "material_override": "DUCTILE_IRON",
            "priority_boost": 500 # Adds a boost to any DI mapping
        }
    },
    "15401-PVC": {
        "title": "PVC Pipe and Fittings",
        "active": True,
        "required_attributes": ["PIPE_CLASS"],
        "mapping_overrides": {
            "feature_code": "WL",
            "conditions": {"SIZE": {"operator": "<=", "value": "12IN"}},
            "material_override": "PVC",
            "priority_boost": 500
        }
    }
}

# --- Main Service ---

class SpecificationManager:
    """
    Manages master construction specifications and generates high-priority
    SSM mapping overrides based on active project specifications.
    """

    def __init__(self):
        self.specs = MOCK_SPECIFICATIONS
        logger.info("SpecificationManager initialized with master specifications.")

    def get_spec_requirements(self, spec_number: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the full requirements and overrides defined by a specification section.
        """
        spec = self.specs.get(spec_number)

        if not spec or not spec.get("active"):
            logger.warning(f"Specification '{spec_number}' not found or is inactive.")
            return None

        logger.info(f"Retrieved active specification: {spec['title']}.")
        return spec

    def generate_spec_mapping_override(self, spec_number: str) -> Optional[Dict[str, Any]]:
        """
        Generates a high-priority SSM mapping entry that the mapping engine can consume,
        based on the constraints of the active specification.
        """
        spec = self.get_spec_requirements(spec_number)

        if not spec or not spec.get("mapping_overrides"):
            return None

        overrides = spec["mapping_overrides"]

        # Structure the output to look like a Project Override mapping (P=9999 level)
        override_mapping = {
            "id": f"SPEC_{spec_number}",
            "feature_code": overrides["feature_code"],
            "conditions": overrides["conditions"],
            "priority": 9500, # High priority just below Project Override (P=9999)

            # The core material constraint enforced by the specification
            "enforced_attribute": {"MATERIAL": overrides["material_override"]},

            "layer": f"SPEC-{spec_number}-{overrides['material_override']}",
            "block": f"SPEC-{spec_number}-{overrides['material_override']}-BLOCK",
            "source": f"SPECIFICATION_SECTION_{spec_number}"
        }

        logger.info(f"GENERATED: Specification mapping override for {spec_number}.")
        return override_mapping

# --- Example Execution ---
if __name__ == '__main__':
    manager = SpecificationManager()

    # TEST 1: Retrieve and generate a mapping override for a known specification
    spec_num = "15400-DI"
    print(f"\n--- TEST CASE 1: Processing Specification {spec_num} ---")

    requirements = manager.get_spec_requirements(spec_num)
    print(f"Required Attributes: {requirements['required_attributes']}")

    mapping_override = manager.generate_spec_mapping_override(spec_num)
    print("\nGenerated Mapping Override:")
    print(json.dumps(mapping_override, indent=4))

    # TEST 2: Process an unknown specification
    print(f"\n--- TEST CASE 2: Processing Specification 9999-VOID ---")
    mapping_void = manager.generate_spec_mapping_override("9999-VOID")
    print(f"Result: {mapping_void}")
