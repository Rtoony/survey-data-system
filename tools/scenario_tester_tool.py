# tools/scenario_tester_tool.py
"""
Scenario Tester Tool
A debugging and validation utility that runs raw data through the entire SSM pipeline
and returns a verbose log detailing the resolution steps taken by the system.

This tool is designed for:
- "What If" scenario testing
- Debugging standards resolution logic
- Validating pipeline behavior with various inputs
- Testing edge cases and error handling
"""

from typing import Dict, Any, List, Optional
import logging
import json
from datetime import datetime

from services.standards_preview_service import StandardsPreviewService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ScenarioTesterTool:
    """
    A debugging and validation utility that runs raw data through the entire SSM pipeline
    and returns a verbose log detailing the resolution steps taken by the system.

    Pipeline Flow:
    1. Data Normalization (Phase 25) - Clean text, calculate derived attributes
    2. Mapping Resolution (Phase 28) - Find best matching standards mapping
    3. Rule Execution (Phase 20) - Generate labels, apply automation rules
    4. Export Formatting (Phase 27) - Format final output for CAD systems
    """

    def __init__(self, db_url: Optional[str] = None, use_mock: bool = True):
        """
        Initialize the Scenario Tester with pipeline dependencies.

        Args:
            db_url: Database URL for mapping service (if not using mock mode)
            use_mock: If True, uses mock data instead of database queries
        """
        # The Scenario Tester relies entirely on the Standards Preview Service (Phase 29)
        self.preview_service = StandardsPreviewService(db_url=db_url, use_mock=use_mock)
        self.use_mock = use_mock
        logger.info("ScenarioTesterTool initialized. Ready to debug pipelines.")

    def run_scenario(
        self,
        feature_code: str,
        raw_attributes: Dict[str, Any],
        export_format: str = "civil3d"
    ) -> Dict[str, Any]:
        """
        Runs a full end-to-end scenario and captures the log of the decision-making process.

        This is the core function for debugging the standards resolution process.
        It executes the entire pipeline and returns detailed logs for analysis.

        Args:
            feature_code: The survey feature code (e.g., "SDMH", "SSMH", "SWP")
            raw_attributes: Raw field-collected attributes (may have typos, missing derived values)
            export_format: Output format - "civil3d" or "trimble_fxl"

        Returns:
            Dictionary containing:
                - status: "SUCCESS" or "FAILURE"
                - resolved_feature: The feature code that was processed
                - pipeline_log: Detailed step-by-step execution log
                - raw_input_data: Original attributes provided
                - final_cad_preview: The generated CAD output
                - normalized_attributes: Cleaned/calculated attributes (if successful)
                - resolved_mapping: The standards mapping used (if successful)
                - rule_results: Automation rule execution results (if successful)
                - export_format: The export format used
                - timestamp: When the scenario was executed
                - notes: Additional context about the scenario execution
        """
        logger.info(f"--- STARTING 'WHAT IF' SCENARIO: {feature_code} ---")

        execution_timestamp = datetime.now().isoformat()

        # Execute the full pipeline via the orchestrator (Phase 29)
        try:
            full_result = self.preview_service.generate_full_preview(
                feature_code,
                raw_attributes,
                export_format
            )

            # Build verbose output for debugging
            if full_result.get("status") == "SUCCESS":
                verbose_output = {
                    "status": "SUCCESS",
                    "resolved_feature": feature_code,
                    "pipeline_log": self._format_pipeline_log(full_result.get("log", [])),
                    "raw_input_data": raw_attributes,
                    "normalized_attributes": full_result.get("normalized_attributes", {}),
                    "resolved_mapping": full_result.get("resolved_mapping", {}),
                    "rule_results": full_result.get("rule_results", {}),
                    "final_cad_preview": full_result.get("final_preview_output", "N/A"),
                    "export_format": export_format,
                    "timestamp": execution_timestamp,
                    "notes": f"Scenario run successfully. Export format: {export_format}. "
                            f"Mode: {'MOCK' if self.use_mock else 'DATABASE'}."
                }
                logger.info("Scenario completed successfully.")
            else:
                # Pipeline failed at some step
                verbose_output = {
                    "status": "FAILURE",
                    "resolved_feature": feature_code,
                    "pipeline_log": self._format_pipeline_log(full_result.get("log", [])),
                    "raw_input_data": raw_attributes,
                    "final_cad_preview": full_result.get("final_preview_output", "ERROR"),
                    "export_format": export_format,
                    "timestamp": execution_timestamp,
                    "error": full_result.get("error", "Unknown error occurred"),
                    "notes": "Pipeline failed during execution. Review pipeline_log for details."
                }
                logger.warning(f"Scenario failed: {full_result.get('error', 'Unknown error')}")

            return verbose_output

        except Exception as e:
            logger.error(f"Scenario failed with exception: {e}")
            return {
                "status": "FAILURE",
                "resolved_feature": feature_code,
                "pipeline_log": [f"EXCEPTION: Scenario failed before completion - {str(e)}"],
                "raw_input_data": raw_attributes,
                "final_cad_preview": "ERROR",
                "export_format": export_format,
                "timestamp": execution_timestamp,
                "error": str(e),
                "notes": "Scenario encountered an unexpected exception. Review error message and raw data."
            }

    def run_batch_scenarios(
        self,
        scenarios: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Runs multiple scenarios in batch for comprehensive testing.

        Args:
            scenarios: List of scenario dictionaries, each containing:
                - feature_code: The survey feature code
                - attributes: Raw attributes dictionary
                - export_format: (Optional) Export format, defaults to "civil3d"
                - description: (Optional) Description of the test scenario

        Returns:
            List of results from each scenario execution
        """
        logger.info(f"=== STARTING BATCH SCENARIO TEST: {len(scenarios)} scenarios ===")

        results = []
        for idx, scenario in enumerate(scenarios, 1):
            scenario_desc = scenario.get('description', f'Scenario {idx}')
            logger.info(f"\n--- Running Scenario {idx}/{len(scenarios)}: {scenario_desc} ---")

            result = self.run_scenario(
                feature_code=scenario['feature_code'],
                raw_attributes=scenario['attributes'],
                export_format=scenario.get('export_format', 'civil3d')
            )

            result['scenario_description'] = scenario_desc
            result['scenario_number'] = idx
            results.append(result)

        logger.info(f"=== BATCH SCENARIO TEST COMPLETE: {len(results)} scenarios executed ===")
        return results

    def _format_pipeline_log(self, log_entries: List[Dict[str, Any]]) -> List[str]:
        """
        Formats the pipeline log into human-readable strings for debugging.

        Args:
            log_entries: Raw log entries from the pipeline

        Returns:
            List of formatted log strings
        """
        formatted_log = []

        for entry in log_entries:
            step = entry.get('step', '?')
            phase = entry.get('phase', 'Unknown Phase')
            status = entry.get('status', 'UNKNOWN')
            message = entry.get('message', entry.get('error', 'No message'))

            status_icon = {
                'SUCCESS': '✓',
                'FAILED': '✗',
                'NOT_FOUND': '⚠',
                'VALIDATION_FAILED': '⚠'
            }.get(status, '•')

            log_line = f"{status_icon} Step {step}: {phase} - {status}"
            formatted_log.append(log_line)
            formatted_log.append(f"  Message: {message}")

            if 'details' in entry:
                formatted_log.append(f"  Details: {json.dumps(entry['details'], indent=4)}")

            if 'error' in entry and status in ['FAILED', 'NOT_FOUND']:
                formatted_log.append(f"  Error: {entry['error']}")

        return formatted_log

    def print_scenario_report(self, result: Dict[str, Any]) -> None:
        """
        Prints a formatted report of a scenario execution for console output.

        Args:
            result: The result dictionary from run_scenario()
        """
        print("\n" + "="*80)
        print("SCENARIO TESTER - DEBUGGING REPORT")
        print("="*80)

        print(f"\nFeature Code: {result.get('resolved_feature', 'N/A')}")
        print(f"Status: {result.get('status', 'UNKNOWN')}")
        print(f"Export Format: {result.get('export_format', 'N/A')}")
        print(f"Timestamp: {result.get('timestamp', 'N/A')}")

        if result.get('scenario_description'):
            print(f"Description: {result['scenario_description']}")

        print("\n--- RAW INPUT DATA ---")
        print(json.dumps(result.get('raw_input_data', {}), indent=2))

        print("\n--- PIPELINE EXECUTION LOG ---")
        for log_line in result.get('pipeline_log', []):
            print(log_line)

        if result.get('status') == 'SUCCESS':
            print("\n--- NORMALIZED ATTRIBUTES ---")
            print(json.dumps(result.get('normalized_attributes', {}), indent=2))

            print("\n--- RESOLVED MAPPING ---")
            mapping = result.get('resolved_mapping', {})
            print(f"  Mapping ID: {mapping.get('source_mapping_id', 'N/A')}")
            print(f"  Layer: {mapping.get('cad_layer', 'N/A')}")
            print(f"  Block: {mapping.get('cad_block', 'N/A')}")

            print("\n--- FINAL CAD OUTPUT ---")
            print(result.get('final_cad_preview', 'N/A'))
        else:
            print("\n--- ERROR ---")
            print(f"Error: {result.get('error', 'Unknown error')}")
            print(f"CAD Preview: {result.get('final_cad_preview', 'N/A')}")

        print("\n--- NOTES ---")
        print(result.get('notes', 'No additional notes'))

        print("\n" + "="*80)


# --- Example Execution (Demonstrates utility) ---
if __name__ == '__main__':
    # Initialize tool in mock mode (no database required for testing)
    tool = ScenarioTesterTool(use_mock=True)

    print("\n" + "="*80)
    print("SCENARIO TESTER TOOL - EXAMPLE EXECUTIONS")
    print("="*80)

    # SCENARIO 1: Basic Storm Drain Manhole
    print("\n--- SCENARIO 1: Basic Storm Drain Manhole ---")
    test_data_1 = {
        "SIZE": "48IN",
        "RIM_ELEV": 105.00,
        "INVERT_ELEV": 100.00,
        "MATERIAL": "CONCRETE"
    }

    result_1 = tool.run_scenario("SDMH", test_data_1, "civil3d")
    tool.print_scenario_report(result_1)

    # SCENARIO 2: Large Manhole with Special Conditions
    print("\n--- SCENARIO 2: Large Manhole (60IN) with County Jurisdiction ---")
    test_data_2 = {
        "SIZE": "60IN",
        "RIM_ELEV": 105.00,
        "INVERT_ELEV": 98.50,
        "MATERIAL": "BRICK",
        "JURISDICTION": "COUNTY"
    }

    result_2 = tool.run_scenario("SDMH", test_data_2, "trimble_fxl")
    tool.print_scenario_report(result_2)

    # SCENARIO 3: Batch Testing
    print("\n--- SCENARIO 3: Batch Testing Multiple Cases ---")
    batch_scenarios = [
        {
            "feature_code": "SDMH",
            "attributes": {"SIZE": 24, "RIM_ELEV": 100.0},
            "export_format": "civil3d",
            "description": "Small 24-inch manhole"
        },
        {
            "feature_code": "SWP",
            "attributes": {"MATERIAL": "PVC", "DEPTH": 6.5},
            "export_format": "civil3d",
            "description": "PVC sewer pipe"
        },
        {
            "feature_code": "UNKNOWN",
            "attributes": {"TEST": "data"},
            "export_format": "civil3d",
            "description": "Unknown feature code (should fail)"
        }
    ]

    batch_results = tool.run_batch_scenarios(batch_scenarios)

    print("\n=== BATCH TEST SUMMARY ===")
    for result in batch_results:
        status_icon = "✓" if result['status'] == 'SUCCESS' else "✗"
        print(f"{status_icon} Scenario {result['scenario_number']}: "
              f"{result['scenario_description']} - {result['status']}")

    print("\n" + "="*80)
    print("ALL EXAMPLE SCENARIOS COMPLETE")
    print("="*80)
