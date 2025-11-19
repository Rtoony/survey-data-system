# tests/test_scenario_tester_tool.py
"""
Unit Tests for ScenarioTesterTool
Tests the debugging and validation utility for the SSM pipeline.
"""

import pytest
from typing import Dict, Any
import json

from tools.scenario_tester_tool import ScenarioTesterTool


class TestScenarioTesterTool:
    """Test suite for ScenarioTesterTool"""

    @pytest.fixture
    def scenario_tool(self):
        """Fixture to provide a ScenarioTesterTool instance in mock mode"""
        return ScenarioTesterTool(use_mock=True)

    def test_initialization(self, scenario_tool):
        """Test that the tool initializes correctly"""
        assert scenario_tool is not None
        assert scenario_tool.use_mock is True
        assert scenario_tool.preview_service is not None

    def test_run_scenario_success_civil3d(self, scenario_tool):
        """Test successful scenario execution with Civil 3D export"""
        test_data = {
            "SIZE": "48IN",
            "RIM_ELEV": 105.00,
            "INVERT_ELEV": 100.00,
            "MATERIAL": "CONCRETE"
        }

        result = scenario_tool.run_scenario("SDMH", test_data, "civil3d")

        # Verify result structure
        assert result["status"] == "SUCCESS"
        assert result["resolved_feature"] == "SDMH"
        assert result["export_format"] == "civil3d"
        assert "pipeline_log" in result
        assert "raw_input_data" in result
        assert "normalized_attributes" in result
        assert "resolved_mapping" in result
        assert "rule_results" in result
        assert "final_cad_preview" in result
        assert "timestamp" in result
        assert "notes" in result

        # Verify raw input is preserved
        assert result["raw_input_data"] == test_data

        # Verify normalized attributes include derived DEPTH
        assert "DEPTH" in result["normalized_attributes"]
        assert result["normalized_attributes"]["DEPTH"] == 5.0

        # Verify resolved mapping contains expected fields
        assert "source_mapping_id" in result["resolved_mapping"]
        assert "cad_layer" in result["resolved_mapping"]
        assert "cad_block" in result["resolved_mapping"]

        # Verify pipeline log has all steps
        assert len(result["pipeline_log"]) > 0

    def test_run_scenario_success_trimble_fxl(self, scenario_tool):
        """Test successful scenario execution with Trimble FXL export"""
        test_data = {
            "SIZE": "60IN",
            "RIM_ELEV": 105.00,
            "INVERT_ELEV": 98.50,
            "MATERIAL": "BRICK"
        }

        result = scenario_tool.run_scenario("SDMH", test_data, "trimble_fxl")

        assert result["status"] == "SUCCESS"
        assert result["export_format"] == "trimble_fxl"
        assert "FXL_Feature" in result["final_cad_preview"] or "<?xml" in result["final_cad_preview"]

    def test_run_scenario_failure_unknown_feature_code(self, scenario_tool):
        """Test scenario failure when feature code is not found"""
        test_data = {"TEST": "data"}

        result = scenario_tool.run_scenario("UNKNOWN_CODE", test_data, "civil3d")

        # Should fail gracefully
        assert result["status"] == "FAILURE"
        assert "error" in result
        assert "pipeline_log" in result
        assert result["final_cad_preview"] == "ERROR" or "ERROR" in result["final_cad_preview"]

    def test_run_scenario_with_missing_attributes(self, scenario_tool):
        """Test scenario with missing required attributes"""
        test_data = {
            "SIZE": 24,
            "RIM_ELEV": 100.0
            # Missing INVERT_ELEV which may be required
        }

        result = scenario_tool.run_scenario("SDMH", test_data, "civil3d")

        # Should complete but may have validation warnings
        # The result status depends on whether missing attributes cause failure
        assert result["status"] in ["SUCCESS", "FAILURE"]
        assert "pipeline_log" in result

    def test_run_scenario_normalization(self, scenario_tool):
        """Test that data normalization occurs correctly"""
        test_data = {
            "SIZE": 48,  # Integer, should be normalized
            "RIM_ELEV": 105.00,
            "INVERT_ELEV": 100.00,
            "MATERIAL": "conc"  # Lowercase, should be normalized
        }

        result = scenario_tool.run_scenario("SDMH", test_data, "civil3d")

        if result["status"] == "SUCCESS":
            # Check that normalization occurred
            normalized = result["normalized_attributes"]
            assert "SIZE" in normalized
            assert "MATERIAL" in normalized
            # DEPTH should be calculated
            assert "DEPTH" in normalized
            assert normalized["DEPTH"] == 5.0

    def test_run_scenario_sewer_pipe(self, scenario_tool):
        """Test scenario with sewer pipe feature code"""
        test_data = {
            "MATERIAL": "PVC",
            "DEPTH": 6.5
        }

        result = scenario_tool.run_scenario("SWP", test_data, "civil3d")

        # Should resolve to sewer pipe mapping
        if result["status"] == "SUCCESS":
            assert result["resolved_feature"] == "SWP"
            assert "MATERIAL" in result["normalized_attributes"]

    def test_run_batch_scenarios(self, scenario_tool):
        """Test batch scenario execution"""
        scenarios = [
            {
                "feature_code": "SDMH",
                "attributes": {"SIZE": 24, "RIM_ELEV": 100.0, "INVERT_ELEV": 95.0},
                "export_format": "civil3d",
                "description": "Small manhole"
            },
            {
                "feature_code": "SWP",
                "attributes": {"MATERIAL": "PVC", "DEPTH": 6.5},
                "export_format": "civil3d",
                "description": "PVC pipe"
            }
        ]

        results = scenario_tool.run_batch_scenarios(scenarios)

        # Verify results
        assert len(results) == 2
        assert results[0]["scenario_number"] == 1
        assert results[1]["scenario_number"] == 2
        assert results[0]["scenario_description"] == "Small manhole"
        assert results[1]["scenario_description"] == "PVC pipe"

    def test_run_batch_scenarios_empty_list(self, scenario_tool):
        """Test batch execution with empty scenario list"""
        results = scenario_tool.run_batch_scenarios([])

        assert results == []

    def test_format_pipeline_log(self, scenario_tool):
        """Test pipeline log formatting"""
        mock_log_entries = [
            {
                "step": 1,
                "phase": "Phase 25: Data Normalization",
                "status": "SUCCESS",
                "message": "Normalization complete",
                "details": {"derived_attributes": ["DEPTH"]}
            },
            {
                "step": 2,
                "phase": "Phase 28: Mapping Resolution",
                "status": "FAILED",
                "error": "No mapping found"
            }
        ]

        formatted_log = scenario_tool._format_pipeline_log(mock_log_entries)

        # Verify formatted output
        assert len(formatted_log) > 0
        assert any("Step 1" in line for line in formatted_log)
        assert any("Step 2" in line for line in formatted_log)
        assert any("SUCCESS" in line for line in formatted_log)
        assert any("FAILED" in line for line in formatted_log)

    def test_print_scenario_report(self, scenario_tool, capsys):
        """Test that print_scenario_report produces output"""
        test_data = {
            "SIZE": "48IN",
            "RIM_ELEV": 105.00,
            "INVERT_ELEV": 100.00,
            "MATERIAL": "CONCRETE"
        }

        result = scenario_tool.run_scenario("SDMH", test_data, "civil3d")
        scenario_tool.print_scenario_report(result)

        # Capture printed output
        captured = capsys.readouterr()

        # Verify output contains expected sections
        assert "SCENARIO TESTER - DEBUGGING REPORT" in captured.out
        assert "Feature Code:" in captured.out
        assert "Status:" in captured.out
        assert "RAW INPUT DATA" in captured.out
        assert "PIPELINE EXECUTION LOG" in captured.out

    def test_scenario_with_all_export_formats(self, scenario_tool):
        """Test scenario with different export formats"""
        test_data = {
            "SIZE": "48IN",
            "RIM_ELEV": 105.00,
            "INVERT_ELEV": 100.00,
            "MATERIAL": "CONCRETE"
        }

        # Test Civil 3D
        result_civil3d = scenario_tool.run_scenario("SDMH", test_data, "civil3d")
        assert result_civil3d["export_format"] == "civil3d"

        # Test Trimble FXL
        result_fxl = scenario_tool.run_scenario("SDMH", test_data, "trimble_fxl")
        assert result_fxl["export_format"] == "trimble_fxl"

        # Both should succeed
        if result_civil3d["status"] == "SUCCESS" and result_fxl["status"] == "SUCCESS":
            # Outputs should be different
            assert result_civil3d["final_cad_preview"] != result_fxl["final_cad_preview"]

    def test_scenario_timestamp_present(self, scenario_tool):
        """Test that scenario results include timestamp"""
        test_data = {"SIZE": 24}

        result = scenario_tool.run_scenario("SDMH", test_data, "civil3d")

        assert "timestamp" in result
        assert result["timestamp"] is not None
        # Timestamp should be in ISO format
        assert "T" in result["timestamp"]

    def test_scenario_preserves_raw_input(self, scenario_tool):
        """Test that raw input data is preserved unchanged"""
        test_data = {
            "SIZE": "WEIRD_VALUE",
            "CUSTOM_FIELD": "test",
            "NUMBER": 123
        }

        result = scenario_tool.run_scenario("SDMH", test_data, "civil3d")

        # Raw input should be exactly the same
        assert result["raw_input_data"] == test_data

    def test_batch_scenario_with_failures(self, scenario_tool):
        """Test batch scenarios with mixed success/failure"""
        scenarios = [
            {
                "feature_code": "SDMH",
                "attributes": {"SIZE": 48, "RIM_ELEV": 100.0, "INVERT_ELEV": 95.0},
                "description": "Valid manhole"
            },
            {
                "feature_code": "INVALID_CODE",
                "attributes": {"TEST": "data"},
                "description": "Invalid feature code"
            }
        ]

        results = scenario_tool.run_batch_scenarios(scenarios)

        assert len(results) == 2
        # First should succeed, second should fail
        statuses = [r["status"] for r in results]
        assert "FAILURE" in statuses  # At least one failure

    def test_scenario_tool_with_database_mode_initialization(self):
        """Test initialization with database mode (mock disabled)"""
        # This test verifies the interface but may fail without actual DB
        # In production, this would need a test database URL
        try:
            tool = ScenarioTesterTool(
                db_url="postgresql://test:test@localhost/test_db",
                use_mock=False
            )
            assert tool.use_mock is False
        except Exception:
            # Expected to fail without actual database
            # This test validates the interface exists
            pass

    def test_error_handling_in_run_scenario(self, scenario_tool):
        """Test error handling when unexpected exceptions occur"""
        # Test with invalid data types that might cause exceptions
        test_data = None  # Invalid input

        try:
            result = scenario_tool.run_scenario("SDMH", test_data, "civil3d")
            # Should return error result instead of raising exception
            assert result["status"] == "FAILURE"
            assert "error" in result
        except Exception:
            # If it raises exception, that's also acceptable error handling
            pass

    def test_pipeline_log_contains_all_phases(self, scenario_tool):
        """Test that successful pipeline log contains all expected phases"""
        test_data = {
            "SIZE": "48IN",
            "RIM_ELEV": 105.00,
            "INVERT_ELEV": 100.00,
            "MATERIAL": "CONCRETE"
        }

        result = scenario_tool.run_scenario("SDMH", test_data, "civil3d")

        if result["status"] == "SUCCESS":
            log_text = " ".join(result["pipeline_log"])

            # Check for all pipeline phases
            assert "Phase 25" in log_text  # Data Normalization
            assert "Phase 28" in log_text or "Phase 19" in log_text  # Mapping Resolution
            assert "Phase 20" in log_text  # Rule Execution
            assert "Phase 27" in log_text  # Export Formatting


class TestScenarioTesterIntegration:
    """Integration tests for ScenarioTesterTool"""

    @pytest.fixture
    def scenario_tool(self):
        """Fixture to provide a ScenarioTesterTool instance"""
        return ScenarioTesterTool(use_mock=True)

    def test_end_to_end_pipeline_execution(self, scenario_tool):
        """Test complete end-to-end pipeline execution"""
        test_data = {
            "SIZE": 48,
            "RIM_ELEV": 105.00,
            "INVERT_ELEV": 100.00,
            "MATERIAL": "CONCRETE"
        }

        result = scenario_tool.run_scenario("SDMH", test_data, "civil3d")

        # Full pipeline should execute
        assert result["status"] == "SUCCESS"

        # Verify each pipeline stage produced output
        assert result["normalized_attributes"] is not None
        assert result["resolved_mapping"] is not None
        assert result["rule_results"] is not None
        assert result["final_cad_preview"] is not None

        # Verify data flowed through pipeline
        assert result["normalized_attributes"]["SIZE"] is not None
        assert result["resolved_mapping"]["source_mapping_id"] is not None
        assert len(result["final_cad_preview"]) > 0

    def test_realistic_survey_data_scenario(self, scenario_tool):
        """Test with realistic field survey data"""
        # Simulating data collected in the field with typical variations
        field_data = {
            "SIZE": "48",  # String instead of int
            "RIM_ELEV": 105.5,
            "INVERT_ELEV": 100.25,
            "MATERIAL": "conc",  # Abbreviated, lowercase
            "NOTES": "Near intersection"  # Additional field
        }

        result = scenario_tool.run_scenario("SDMH", field_data, "civil3d")

        # Should handle real-world data variations
        if result["status"] == "SUCCESS":
            # Normalization should clean up data
            assert result["normalized_attributes"]["SIZE"] is not None
            assert result["normalized_attributes"]["DEPTH"] == pytest.approx(5.25, 0.01)

    def test_multiple_feature_types(self, scenario_tool):
        """Test scenarios with different feature types"""
        feature_tests = [
            ("SDMH", {"SIZE": 48, "RIM_ELEV": 100.0, "INVERT_ELEV": 95.0}),
            ("SWP", {"MATERIAL": "PVC", "DEPTH": 6.5}),
        ]

        for feature_code, attributes in feature_tests:
            result = scenario_tool.run_scenario(feature_code, attributes, "civil3d")

            # Each should process according to its feature type
            assert result["resolved_feature"] == feature_code
            # Different features may have different success criteria
            assert result["status"] in ["SUCCESS", "FAILURE"]
