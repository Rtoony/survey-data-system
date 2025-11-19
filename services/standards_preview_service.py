# services/standards_preview_service.py
"""
Standards Preview Service
Orchestrates the entire SSM pipeline to generate real-time CAD output previews.
Integrates: Data Normalization (Phase 25) -> Mapping Resolution (Phase 28) ->
            Rule Execution (Phase 20) -> Export Formatting (Phase 27)
"""

from typing import Dict, Any, List, Optional
import logging
import json
import textwrap

from services.data_normalization_service import DataNormalizationService
from services.ssm_mapping_service import GKGSyncService
from services.ssm_rule_service import SSMRuleService
from services.export_template_service import ExportTemplateService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class StandardsPreviewService:
    """
    Orchestrates the entire SSM pipeline to generate a real-time preview
    of the final CAD output based on raw input data.

    Pipeline Flow:
    1. Data Normalization - Clean text, calculate derived attributes (DEPTH, etc.)
    2. Mapping Resolution - Find best matching standards mapping by priority/specificity
    3. Rule Execution - Generate labels, apply automation rules
    4. Export Formatting - Format final output for Civil 3D or Trimble FXL
    """

    def __init__(self, db_url: Optional[str] = None, use_mock: bool = True):
        """
        Initialize the preview service with pipeline dependencies.

        Args:
            db_url: Database URL for mapping service (if not using mock mode)
            use_mock: If True, uses mock data instead of database queries
        """
        self.use_mock = use_mock

        # Initialize pipeline services
        self.normalizer = DataNormalizationService()

        if use_mock:
            # Use mock mapping service for preview without database
            self.mapper = MockMappingService()
        else:
            # Use real mapping service with database
            if not db_url:
                raise ValueError("Database URL required when not using mock mode")
            self.mapper = GKGSyncService(db_url)

        self.ruler = SSMRuleService()
        self.exporter = ExportTemplateService()

        logger.info(f"StandardsPreviewService initialized (mock_mode={use_mock})")

    def generate_full_preview(
        self,
        feature_code: str,
        raw_attributes: Dict[str, Any],
        export_format: str = "civil3d"
    ) -> Dict[str, Any]:
        """
        Executes the full SSM pipeline: Clean -> Map -> Rule -> Export.

        Args:
            feature_code: The survey feature code (e.g., "SDMH", "SSMH", "SWP")
            raw_attributes: Raw field-collected attributes (may have typos, missing derived values)
            export_format: Output format - "civil3d" or "trimble_fxl"

        Returns:
            Dictionary containing:
                - feature_code: Input feature code
                - raw_input: Original attributes
                - normalized_attributes: Cleaned/calculated attributes
                - resolved_mapping: The standards mapping used
                - rule_results: Automation rule execution results
                - final_preview_output: Formatted CAD output string
                - log: Step-by-step pipeline execution log
        """
        pipeline_log = []
        logger.info(f"=== Starting Standards Preview for {feature_code} ===")

        # STEP 1: Data Normalization (Phase 25)
        try:
            normalized_attrs = self.normalizer.normalize_attributes(raw_attributes)
            pipeline_log.append({
                "step": 1,
                "phase": "Phase 25: Data Normalization",
                "status": "SUCCESS",
                "message": f"Cleaned text attributes and calculated derived values (e.g., DEPTH)",
                "details": {
                    "derived_attributes": [k for k in normalized_attrs.keys() if k not in raw_attributes]
                }
            })
            logger.info(f"✓ Step 1: Normalization complete. Derived: {normalized_attrs.keys() - raw_attributes.keys()}")
        except Exception as e:
            logger.error(f"✗ Step 1 FAILED: {e}")
            pipeline_log.append({
                "step": 1,
                "phase": "Phase 25: Data Normalization",
                "status": "FAILED",
                "error": str(e)
            })
            return self._build_error_response(feature_code, raw_attributes, pipeline_log, str(e))

        # STEP 2: Mapping Resolution (Phase 19/28)
        try:
            resolved_mapping = self.mapper.resolve_mapping(feature_code, normalized_attrs)

            if not resolved_mapping:
                error_msg = f"No standards mapping found for feature code: {feature_code}"
                logger.warning(f"✗ Step 2: {error_msg}")
                pipeline_log.append({
                    "step": 2,
                    "phase": "Phase 28: Mapping Resolution",
                    "status": "NOT_FOUND",
                    "message": error_msg
                })
                return self._build_error_response(feature_code, raw_attributes, pipeline_log, error_msg)

            pipeline_log.append({
                "step": 2,
                "phase": "Phase 28: Mapping Resolution",
                "status": "SUCCESS",
                "message": f"Resolved to Mapping ID {resolved_mapping.get('source_mapping_id')} "
                          f"using priority/specificity tie-breaker",
                "details": {
                    "mapping_id": resolved_mapping.get('source_mapping_id'),
                    "layer": resolved_mapping.get('layer') or resolved_mapping.get('cad_layer'),
                    "block": resolved_mapping.get('block') or resolved_mapping.get('cad_block')
                }
            })
            logger.info(f"✓ Step 2: Mapping resolved (ID: {resolved_mapping.get('source_mapping_id')})")
        except Exception as e:
            logger.error(f"✗ Step 2 FAILED: {e}")
            pipeline_log.append({
                "step": 2,
                "phase": "Phase 28: Mapping Resolution",
                "status": "FAILED",
                "error": str(e)
            })
            return self._build_error_response(feature_code, raw_attributes, pipeline_log, str(e))

        # STEP 3: Rule Execution (Phase 20)
        try:
            # Add feature code to attributes for rule execution
            normalized_attrs['FEATURE_CODE'] = feature_code

            rule_results = self.ruler.run_rules(feature_code, normalized_attrs, resolved_mapping)

            pipeline_log.append({
                "step": 3,
                "phase": "Phase 20: Rule Execution",
                "status": "SUCCESS" if rule_results.get('validation_status') == 'PASS' else "VALIDATION_FAILED",
                "message": f"Executed automation rules. Label generated: '{rule_results.get('label_text')}'",
                "details": {
                    "label": rule_results.get('label_text'),
                    "validation": rule_results.get('validation_status'),
                    "auto_connect": rule_results.get('connected_to_previous')
                }
            })
            logger.info(f"✓ Step 3: Rules executed. Label: '{rule_results.get('label_text')}'")
        except Exception as e:
            logger.error(f"✗ Step 3 FAILED: {e}")
            pipeline_log.append({
                "step": 3,
                "phase": "Phase 20: Rule Execution",
                "status": "FAILED",
                "error": str(e)
            })
            return self._build_error_response(feature_code, raw_attributes, pipeline_log, str(e))

        # STEP 4: Export Generation (Phase 27)
        try:
            # Prepare attributes for export (include feature code and point ID if available)
            export_attrs = normalized_attrs.copy()

            if export_format.lower() == "trimble_fxl":
                preview_output = self.exporter.generate_trimble_fxl(resolved_mapping, export_attrs)
                format_name = "Trimble FXL"
            else:  # default to civil3d
                preview_output = self.exporter.generate_civil3d_desc_key(resolved_mapping, export_attrs)
                format_name = "Civil 3D Description Key"

            pipeline_log.append({
                "step": 4,
                "phase": "Phase 27: Export Formatting",
                "status": "SUCCESS",
                "message": f"Generated {format_name} output",
                "details": {
                    "format": export_format,
                    "source_mapping": resolved_mapping.get('source_mapping_id')
                }
            })
            logger.info(f"✓ Step 4: Export generated ({format_name})")
        except Exception as e:
            logger.error(f"✗ Step 4 FAILED: {e}")
            pipeline_log.append({
                "step": 4,
                "phase": "Phase 27: Export Formatting",
                "status": "FAILED",
                "error": str(e)
            })
            return self._build_error_response(feature_code, raw_attributes, pipeline_log, str(e))

        # Build successful response
        logger.info(f"=== Standards Preview Complete for {feature_code} ===")
        return {
            "status": "SUCCESS",
            "feature_code": feature_code,
            "raw_input": raw_attributes,
            "normalized_attributes": normalized_attrs,
            "resolved_mapping": resolved_mapping,
            "rule_results": rule_results,
            "final_preview_output": preview_output,
            "export_format": export_format,
            "log": pipeline_log
        }

    def _build_error_response(
        self,
        feature_code: str,
        raw_attributes: Dict[str, Any],
        pipeline_log: List[Dict[str, Any]],
        error_message: str
    ) -> Dict[str, Any]:
        """Build an error response when pipeline fails."""
        return {
            "status": "FAILED",
            "feature_code": feature_code,
            "raw_input": raw_attributes,
            "error": error_message,
            "final_preview_output": f"ERROR: {error_message}",
            "log": pipeline_log
        }


# --- Mock Mapping Service (for preview mode without database) ---

class MockMappingService:
    """
    Lightweight mock of GKGSyncService for preview functionality
    without requiring database connection.
    """

    # Mock standards mappings for common feature codes
    MOCK_STANDARDS_MAPPINGS = [
        {
            "id": 101,
            "feature_code": "SDMH",
            "conditions": {},
            "priority": 100,
            "cad_layer": "C-SSWR-MH-DEFAULT",
            "cad_block": "MH-DEFAULT",
            "cad_label_style": "MH-${SIZE}",
            "automation_ruleset": {
                "required_attributes": ["SIZE", "RIM_ELEV"],
                "enable_auto_connect": False,
                "label_template": "MH-${SIZE}\nRIM: ${RIM_ELEV}\nINV: ${INVERT_ELEV}"
            }
        },
        {
            "id": 201,
            "feature_code": "SDMH",
            "conditions": {"SIZE": {"op": ">=", "val": "48"}},
            "priority": 200,
            "cad_layer": "C-SSWR-MH-48IN",
            "cad_block": "MH-48-BLOCK",
            "cad_label_style": "MH-${SIZE} / INV: ${INVERT_ELEV}",
            "automation_ruleset": {
                "required_attributes": ["SIZE", "RIM_ELEV", "INVERT_ELEV"],
                "enable_auto_connect": False,
                "label_template": "MH-${SIZE}\nINV: ${INVERT_ELEV}\nDEPTH: ${DEPTH}ft"
            }
        },
        {
            "id": 301,
            "feature_code": "SDMH",
            "conditions": {
                "SIZE": {"op": "==", "val": "48"},
                "MATERIAL": {"op": "==", "val": "CONCRETE"}
            },
            "priority": 300,
            "cad_layer": "C-SSWR-MH-48IN-CONC",
            "cad_block": "MH-48-CONC-BLOCK",
            "cad_label_style": "MH-${SIZE} / INV: ${INVERT_ELEV} / D:${DEPTH}ft",
            "automation_ruleset": {
                "required_attributes": ["SIZE", "RIM_ELEV", "INVERT_ELEV"],
                "enable_auto_connect": False,
                "label_template": "MH-${SIZE} / INV: ${INVERT_ELEV} / D:${DEPTH}ft"
            }
        },
        {
            "id": 401,
            "feature_code": "SWP",
            "conditions": {},
            "priority": 100,
            "cad_layer": "C-SSWR-PIPE",
            "cad_block": "PIPE-SYMBOL",
            "cad_label_style": "PIPE-${MATERIAL}",
            "automation_ruleset": {
                "required_attributes": ["MATERIAL"],
                "enable_auto_connect": True,
                "label_template": "PIPE: ${MATERIAL} @ ${DEPTH}ft"
            }
        }
    ]

    def resolve_mapping(self, feature_code: str, attributes: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Mock implementation of mapping resolution.
        Simulates Phase 28 priority/specificity algorithm.
        """
        logger.info(f"MockMappingService: Resolving mapping for '{feature_code}'")

        # Filter by feature code
        candidates = [
            m for m in self.MOCK_STANDARDS_MAPPINGS
            if m["feature_code"].upper() == feature_code.upper()
        ]

        if not candidates:
            logger.warning(f"No mock mappings found for code: {feature_code}")
            return None

        # Simple condition matching (simplified for mock)
        matching = []
        for mapping in candidates:
            conditions = mapping.get("conditions", {})
            condition_count = len(conditions)

            # For mock, assume all conditions match if feature code matches
            # In production, this would evaluate each condition
            mapping_with_specificity = mapping.copy()
            mapping_with_specificity['condition_count'] = condition_count
            matching.append(mapping_with_specificity)

        # Sort by priority DESC, then condition_count DESC
        best_match = max(
            matching,
            key=lambda m: (m.get("priority", 0), m.get("condition_count", 0))
        )

        logger.info(
            f"MockMappingService: Resolved to ID {best_match['id']} "
            f"(P:{best_match['priority']}, C:{best_match['condition_count']})"
        )

        # Return in expected format
        return {
            "source_mapping_id": best_match["id"],
            "cad_layer": best_match.get("cad_layer"),
            "cad_block": best_match.get("cad_block"),
            "cad_label_style": best_match.get("cad_label_style"),
            "layer": best_match.get("cad_layer"),  # Alias for compatibility
            "block": best_match.get("cad_block"),  # Alias for compatibility
            "automation_ruleset": best_match.get("automation_ruleset", {})
        }


# --- Example Execution ---
if __name__ == '__main__':
    # Initialize service in mock mode (no database required)
    service = StandardsPreviewService(use_mock=True)

    print("\n" + "="*80)
    print("SSM STANDARDS PREVIEW SERVICE - TEST EXECUTION")
    print("="*80)

    # TEST CASE 1: Storm Drain Manhole with typical field data
    print("\n--- TEST CASE 1: Storm Drain Manhole (SDMH) ---")
    test_raw_data_1 = {
        "SIZE": 48,  # Will be normalized
        "RIM_ELEV": 105.00,
        "INVERT_ELEV": 100.00,
        "MATERIAL": "conc"  # Lowercase, will be normalized to CONCRETE
    }

    result_1 = service.generate_full_preview("SDMH", test_raw_data_1, export_format="civil3d")

    print(f"\nStatus: {result_1['status']}")
    print("\n--- Pipeline Execution Log ---")
    for step in result_1['log']:
        status_icon = "✓" if step['status'] == "SUCCESS" else "✗"
        print(f"{status_icon} Step {step['step']}: {step['phase']}")
        print(f"  Status: {step['status']}")
        print(f"  {step['message']}")
        if 'details' in step:
            print(f"  Details: {json.dumps(step['details'], indent=4)}")

    print("\n--- Final CAD Output ---")
    print(result_1['final_preview_output'])

    # TEST CASE 2: Sewer Pipe (Auto-connect enabled)
    print("\n" + "="*80)
    print("--- TEST CASE 2: Sewer Pipe (SWP) with Auto-Connect ---")
    test_raw_data_2 = {
        "MATERIAL": "PVC",
        "DEPTH": 6.5,
        "CONNECT_NEXT": True
    }

    result_2 = service.generate_full_preview("SWP", test_raw_data_2, export_format="civil3d")

    print(f"\nStatus: {result_2['status']}")
    print(f"Auto-Connect Triggered: {result_2.get('rule_results', {}).get('connected_to_previous', False)}")
    print("\n--- Final CAD Output ---")
    print(result_2['final_preview_output'])

    # TEST CASE 3: Trimble FXL Export Format
    print("\n" + "="*80)
    print("--- TEST CASE 3: Trimble FXL Export Format ---")
    test_raw_data_3 = {
        "POINT_ID": 12345,
        "SIZE": 48,
        "RIM_ELEV": 105.00,
        "INVERT_ELEV": 100.00,
        "MATERIAL": "CONCRETE"
    }

    result_3 = service.generate_full_preview("SDMH", test_raw_data_3, export_format="trimble_fxl")

    print(f"\nStatus: {result_3['status']}")
    print("--- Trimble FXL Output ---")
    print(result_3['final_preview_output'])

    # TEST CASE 4: Error Handling - Unknown Feature Code
    print("\n" + "="*80)
    print("--- TEST CASE 4: Error Handling (Unknown Feature Code) ---")
    result_4 = service.generate_full_preview("UNKNOWN_CODE", {"SIZE": 24})

    print(f"\nStatus: {result_4['status']}")
    print(f"Error: {result_4.get('error', 'N/A')}")
    print("\n--- Pipeline Log (Partial) ---")
    for step in result_4['log']:
        print(f"  Step {step['step']}: {step['status']} - {step.get('message', step.get('error'))}")

    print("\n" + "="*80)
    print("ALL TESTS COMPLETE")
    print("="*80)
