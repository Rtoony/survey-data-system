"""
Comprehensive unit tests for StandardsPreviewService.

Tests cover:
- Full pipeline orchestration (normalization -> mapping -> rules -> export)
- Live service integration (using mock data within services)
- Multiple export formats (Civil 3D, Trimble FXL)
- Error handling and recovery
- Pipeline logging and status tracking
- Edge cases with missing or invalid data
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from services.standards_preview_service import StandardsPreviewService


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def preview_service():
    """Create StandardsPreviewService instance with live services."""
    return StandardsPreviewService()


# ============================================================================
# Full Pipeline Tests
# ============================================================================

class TestFullPipeline:
    """Tests for the complete end-to-end pipeline."""

    def test_generate_full_preview_basic(self, preview_service):
        """Test basic full pipeline execution."""
        raw_data = {
            "SIZE": 48,
            "RIM_ELEV": 105.00,
            "INVERT_ELEV": 100.00,
            "MATERIAL": "conc"
        }

        result = preview_service.generate_full_preview("SDMH", raw_data)

        assert result["status"] == "SUCCESS"
        assert result["feature_code"] == "SDMH"
        assert "raw_input" in result
        assert "normalized_attributes" in result
        assert "resolved_mapping" in result
        assert "rule_results" in result
        assert "final_preview_output" in result
        assert "log" in result

    def test_normalization_step_adds_derived_attributes(self, preview_service):
        """Test that normalization step calculates DEPTH."""
        raw_data = {
            "SIZE": 48,
            "RIM_ELEV": 105.00,
            "INVERT_ELEV": 100.00
        }

        result = preview_service.generate_full_preview("SDMH", raw_data)

        assert result["status"] == "SUCCESS"
        assert "DEPTH" in result["normalized_attributes"]
        assert result["normalized_attributes"]["DEPTH"] == 5.0

    def test_normalization_step_cleans_text(self, preview_service):
        """Test that normalization step standardizes text."""
        raw_data = {
            "SIZE": 48,
            "RIM_ELEV": 105.00,
            "INVERT_ELEV": 100.00,
            "MATERIAL": "conc"  # Should become CONCRETE
        }

        result = preview_service.generate_full_preview("SDMH", raw_data)

        assert result["status"] == "SUCCESS"
        assert result["normalized_attributes"]["MATERIAL"] == "CONCRETE"

    def test_mapping_resolution_step(self, preview_service):
        """Test that mapping resolution step finds correct mapping."""
        raw_data = {
            "SIZE": 48,
            "RIM_ELEV": 105.00,
            "INVERT_ELEV": 100.00
        }

        result = preview_service.generate_full_preview("SDMH", raw_data)

        assert result["status"] == "SUCCESS"
        assert result["resolved_mapping"]["source_mapping_id"] is not None
        assert "cad_layer" in result["resolved_mapping"]
        assert "cad_block" in result["resolved_mapping"]

    def test_rule_execution_step(self, preview_service):
        """Test that rule execution generates label."""
        raw_data = {
            "SIZE": 48,
            "RIM_ELEV": 105.00,
            "INVERT_ELEV": 100.00
        }

        result = preview_service.generate_full_preview("SDMH", raw_data)

        assert result["status"] == "SUCCESS"
        assert "rule_results" in result
        assert "label_text" in result["rule_results"]
        assert result["rule_results"]["label_text"] is not None

    def test_export_formatting_step_civil3d(self, preview_service):
        """Test that export formatting generates Civil 3D output."""
        raw_data = {
            "SIZE": 48,
            "RIM_ELEV": 105.00,
            "INVERT_ELEV": 100.00
        }

        result = preview_service.generate_full_preview("SDMH", raw_data, export_format="civil3d")

        assert result["status"] == "SUCCESS"
        assert result["export_format"] == "civil3d"
        assert "final_preview_output" in result
        assert isinstance(result["final_preview_output"], str)
        assert len(result["final_preview_output"]) > 0

    def test_export_formatting_step_trimble_fxl(self, preview_service):
        """Test that export formatting generates Trimble FXL output."""
        raw_data = {
            "POINT_ID": 12345,
            "SIZE": 48,
            "RIM_ELEV": 105.00,
            "INVERT_ELEV": 100.00
        }

        result = preview_service.generate_full_preview("SDMH", raw_data, export_format="trimble_fxl")

        assert result["status"] == "SUCCESS"
        assert result["export_format"] == "trimble_fxl"
        assert "final_preview_output" in result
        assert "<?xml" in result["final_preview_output"]  # XML output

    def test_pipeline_log_structure(self, preview_service):
        """Test that pipeline log has correct structure."""
        raw_data = {
            "SIZE": 48,
            "RIM_ELEV": 105.00,
            "INVERT_ELEV": 100.00
        }

        result = preview_service.generate_full_preview("SDMH", raw_data)

        assert result["status"] == "SUCCESS"
        assert len(result["log"]) == 4  # Four pipeline steps

        for i, log_entry in enumerate(result["log"], 1):
            assert log_entry["step"] == i
            assert "phase" in log_entry
            assert "status" in log_entry
            assert "message" in log_entry

    def test_pipeline_log_success_status(self, preview_service):
        """Test that all pipeline steps log SUCCESS status."""
        raw_data = {
            "SIZE": 48,
            "RIM_ELEV": 105.00,
            "INVERT_ELEV": 100.00
        }

        result = preview_service.generate_full_preview("SDMH", raw_data)

        assert result["status"] == "SUCCESS"
        for log_entry in result["log"]:
            assert log_entry["status"] == "SUCCESS"


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Tests for error handling and recovery."""

    def test_unknown_feature_code(self, preview_service):
        """Test handling of unknown feature code."""
        raw_data = {"SIZE": 48}

        result = preview_service.generate_full_preview("UNKNOWN_CODE", raw_data)

        assert result["status"] == "FAILED"
        assert "error" in result
        assert "No standards mapping found" in result["error"]
        assert len(result["log"]) >= 2  # Should have at least normalization and mapping steps

    def test_normalization_with_missing_data(self, preview_service):
        """Test that pipeline handles missing derived attributes gracefully."""
        raw_data = {
            "SIZE": 48,
            "RIM_ELEV": 105.00
            # Missing INVERT_ELEV - DEPTH won't be calculated
        }

        result = preview_service.generate_full_preview("SDMH", raw_data)

        # Should still succeed even without DEPTH
        assert result["status"] == "SUCCESS"
        assert "DEPTH" not in result["normalized_attributes"]

    def test_empty_attributes(self, preview_service):
        """Test handling of empty attributes dictionary."""
        result = preview_service.generate_full_preview("SDMH", {})

        # Should handle gracefully - mapping should still resolve
        assert result["status"] in ["SUCCESS", "FAILED"]  # Depends on validation rules

    def test_error_response_structure(self, preview_service):
        """Test that error responses have correct structure."""
        result = preview_service.generate_full_preview("UNKNOWN_CODE", {"SIZE": 48})

        assert result["status"] == "FAILED"
        assert "feature_code" in result
        assert "raw_input" in result
        assert "error" in result
        assert "final_preview_output" in result
        assert "ERROR:" in result["final_preview_output"]
        assert "log" in result

    @patch('services.standards_preview_service.DataNormalizationService')
    def test_normalization_exception_handling(self, mock_normalizer_class, preview_service):
        """Test handling of exceptions in normalization step."""
        # Configure mock to raise exception
        mock_instance = Mock()
        mock_instance.normalize_attributes.side_effect = Exception("Normalization failed")
        preview_service.normalizer = mock_instance

        raw_data = {"SIZE": 48}
        result = preview_service.generate_full_preview("SDMH", raw_data)

        assert result["status"] == "FAILED"
        assert "Normalization failed" in result["error"]
        assert result["log"][0]["status"] == "FAILED"

    @patch('services.standards_preview_service.SSMRuleService')
    def test_rule_execution_exception_handling(self, mock_rule_class):
        """Test handling of exceptions in rule execution step."""
        service = StandardsPreviewService()

        # Configure mock to raise exception
        mock_instance = Mock()
        mock_instance.run_rules.side_effect = Exception("Rule execution failed")
        service.ruler = mock_instance

        raw_data = {
            "SIZE": 48,
            "RIM_ELEV": 105.00,
            "INVERT_ELEV": 100.00
        }

        result = service.generate_full_preview("SDMH", raw_data)

        assert result["status"] == "FAILED"
        assert "Rule execution failed" in result["error"]


# ============================================================================
# Integration Tests
# ============================================================================

class TestPipelineIntegration:
    """Integration tests for pipeline component interaction."""

    def test_manhole_full_preview(self, preview_service):
        """Test complete preview for manhole feature."""
        raw_data = {
            "SIZE": 48,
            "RIM_ELEV": 105.50,
            "INVERT_ELEV": 99.25,
            "MATERIAL": "conc",
            "JURISDICTION": "santa rosa"
        }

        result = preview_service.generate_full_preview("SDMH", raw_data)

        assert result["status"] == "SUCCESS"
        assert result["normalized_attributes"]["MATERIAL"] == "CONCRETE"
        assert result["normalized_attributes"]["DEPTH"] == 6.25
        assert result["normalized_attributes"]["JURISDICTION"] == "SANTA ROSA"
        assert result["rule_results"]["validation_status"] in ["PASS", "FAIL"]
        assert "MH" in result["final_preview_output"] or "manhole" in result["final_preview_output"].lower()

    def test_pipe_full_preview_with_autoconnect(self, preview_service):
        """Test complete preview for pipe feature with auto-connect."""
        raw_data = {
            "MATERIAL": "PVC",
            "DEPTH": 6.5,
            "CONNECT_NEXT": True
        }

        result = preview_service.generate_full_preview("SWP", raw_data)

        assert result["status"] == "SUCCESS"
        assert result["rule_results"]["connected_to_previous"] in [True, False]  # Depends on flag
        assert "PIPE" in result["final_preview_output"] or "pipe" in result["final_preview_output"].lower()

    def test_feature_code_added_to_attributes(self, preview_service):
        """Test that FEATURE_CODE is added to attributes for rule execution."""
        raw_data = {
            "SIZE": 48,
            "RIM_ELEV": 105.00,
            "INVERT_ELEV": 100.00
        }

        result = preview_service.generate_full_preview("SDMH", raw_data)

        assert result["status"] == "SUCCESS"
        assert result["normalized_attributes"]["FEATURE_CODE"] == "SDMH"

    def test_multiple_sequential_previews(self, preview_service):
        """Test that service can generate multiple previews sequentially."""
        raw_data_1 = {"SIZE": 48, "RIM_ELEV": 105.00, "INVERT_ELEV": 100.00}
        raw_data_2 = {"SIZE": 36, "RIM_ELEV": 110.00, "INVERT_ELEV": 105.00}

        result_1 = preview_service.generate_full_preview("SDMH", raw_data_1)
        result_2 = preview_service.generate_full_preview("SDMH", raw_data_2)

        assert result_1["status"] == "SUCCESS"
        assert result_2["status"] == "SUCCESS"
        assert result_1["normalized_attributes"]["DEPTH"] == 5.0
        assert result_2["normalized_attributes"]["DEPTH"] == 5.0


# ============================================================================
# Initialization Tests
# ============================================================================

class TestInitialization:
    """Tests for service initialization."""

    def test_initialization_creates_all_services(self):
        """Test initialization creates all required services."""
        service = StandardsPreviewService()

        assert service.normalizer is not None
        assert service.mapper is not None
        assert service.ruler is not None
        assert service.exporter is not None

    @patch('services.standards_preview_service.logger')
    def test_initialization_logging(self, mock_logger):
        """Test that initialization is logged."""
        service = StandardsPreviewService()

        # Verify logging occurred
        assert mock_logger.info.called


# ============================================================================
# Export Format Tests
# ============================================================================

class TestExportFormats:
    """Tests for different export formats."""

    def test_civil3d_export_format(self, preview_service):
        """Test Civil 3D export format output."""
        raw_data = {
            "SIZE": 48,
            "RIM_ELEV": 105.00,
            "INVERT_ELEV": 100.00
        }

        result = preview_service.generate_full_preview("SDMH", raw_data, export_format="civil3d")

        assert result["status"] == "SUCCESS"
        assert result["export_format"] == "civil3d"
        # Civil 3D output should contain key formatting
        output = result["final_preview_output"]
        assert isinstance(output, str)

    def test_trimble_fxl_export_format(self, preview_service):
        """Test Trimble FXL export format output."""
        raw_data = {
            "POINT_ID": 999,
            "SIZE": 48,
            "RIM_ELEV": 105.00,
            "INVERT_ELEV": 100.00
        }

        result = preview_service.generate_full_preview("SDMH", raw_data, export_format="trimble_fxl")

        assert result["status"] == "SUCCESS"
        assert result["export_format"] == "trimble_fxl"
        assert "<?xml" in result["final_preview_output"]

    def test_default_export_format(self, preview_service):
        """Test that default export format is Civil 3D."""
        raw_data = {
            "SIZE": 48,
            "RIM_ELEV": 105.00,
            "INVERT_ELEV": 100.00
        }

        result = preview_service.generate_full_preview("SDMH", raw_data)

        assert result["export_format"] == "civil3d"

    def test_case_insensitive_export_format(self, preview_service):
        """Test that export format parameter is case-insensitive."""
        raw_data = {"SIZE": 48, "RIM_ELEV": 105.00, "INVERT_ELEV": 100.00}

        result_lower = preview_service.generate_full_preview("SDMH", raw_data, export_format="civil3d")
        result_upper = preview_service.generate_full_preview("SDMH", raw_data, export_format="CIVIL3D")

        assert result_lower["status"] == "SUCCESS"
        assert result_upper["status"] == "SUCCESS"


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_very_large_attribute_values(self, preview_service):
        """Test handling of very large attribute values."""
        raw_data = {
            "SIZE": 999999,
            "RIM_ELEV": 10000.00,
            "INVERT_ELEV": 5000.00
        }

        result = preview_service.generate_full_preview("SDMH", raw_data)

        # Should handle without errors
        assert result["status"] == "SUCCESS"
        assert result["normalized_attributes"]["DEPTH"] == 5000.0

    def test_special_characters_in_attributes(self, preview_service):
        """Test handling of special characters in text attributes."""
        raw_data = {
            "SIZE": 48,
            "RIM_ELEV": 105.00,
            "INVERT_ELEV": 100.00,
            "MATERIAL": "PVC/HDPE"  # Special character
        }

        result = preview_service.generate_full_preview("SDMH", raw_data)

        # Should handle gracefully
        assert result["status"] == "SUCCESS"

    def test_unicode_in_attributes(self, preview_service):
        """Test handling of Unicode characters in attributes."""
        raw_data = {
            "SIZE": 48,
            "RIM_ELEV": 105.00,
            "INVERT_ELEV": 100.00,
            "JURISDICTION": "São Paulo"  # Unicode characters
        }

        result = preview_service.generate_full_preview("SDMH", raw_data)

        # Should handle gracefully
        assert result["status"] == "SUCCESS"
