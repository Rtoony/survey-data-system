"""
Comprehensive unit tests for ExportTemplateService.

Tests cover:
- Label substitution with various placeholder scenarios
- Trimble FXL XML generation and structure validation
- Civil 3D Description Key generation and formatting
- Edge cases with missing or invalid data
- XML structure validation
- Label template processing
"""

import pytest
import xml.etree.ElementTree as ET
from unittest.mock import patch
from typing import Dict, Any

from services.export_template_service import ExportTemplateService


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def export_service():
    """Create ExportTemplateService instance."""
    return ExportTemplateService()


@pytest.fixture
def complete_mapping():
    """Complete resolved SSM mapping with all fields."""
    return {
        "source_mapping_id": 301,
        "cad_layer": "C-SSWR-MH-48IN",
        "cad_block": "MH-48-CONC-BLOCK",
        "cad_label_style": "MH-${SIZE} / INV: ${INVERT_ELEV}"
    }


@pytest.fixture
def complete_attributes():
    """Complete feature attributes dictionary."""
    return {
        "POINT_ID": 12345,
        "FEATURE_CODE": "SDMH",
        "SIZE": "48IN",
        "RIM_ELEV": 105.50,
        "INVERT_ELEV": 99.25,
        "DEPTH": 6.25,
        "MATERIAL": "CONCRETE"
    }


# ============================================================================
# Label Substitution Tests
# ============================================================================

class TestLabelSubstitution:
    """Tests for label template placeholder substitution."""

    def test_single_placeholder_substitution(self, export_service):
        """Test substitution of a single placeholder."""
        template = "MH-${SIZE}"
        attributes = {"SIZE": "48IN"}

        result = export_service._substitute_labels(template, attributes)

        assert result == "MH-48IN"

    def test_multiple_placeholder_substitution(self, export_service):
        """Test substitution of multiple placeholders."""
        template = "MH-${SIZE} / INV: ${INVERT_ELEV}"
        attributes = {"SIZE": "48IN", "INVERT_ELEV": 99.25}

        result = export_service._substitute_labels(template, attributes)

        assert result == "MH-48IN / INV: 99.25"

    def test_lowercase_attribute_key_uppercase_placeholder(self, export_service):
        """Test that lowercase attribute keys match uppercase placeholders."""
        template = "Type: ${TYPE}"
        attributes = {"type": "sanitary"}  # lowercase key

        result = export_service._substitute_labels(template, attributes)

        assert result == "Type: sanitary"

    def test_numeric_value_substitution(self, export_service):
        """Test substitution with numeric values (converted to strings)."""
        template = "Depth: ${DEPTH}ft"
        attributes = {"DEPTH": 6.25}

        result = export_service._substitute_labels(template, attributes)

        assert result == "Depth: 6.25ft"

    def test_integer_value_substitution(self, export_service):
        """Test substitution with integer values."""
        template = "ID: ${POINT_ID}"
        attributes = {"POINT_ID": 12345}

        result = export_service._substitute_labels(template, attributes)

        assert result == "ID: 12345"

    def test_unresolved_placeholder_cleanup(self, export_service):
        """Test that unresolved placeholders are cleaned up."""
        template = "MH-${SIZE} / INV: ${INVERT_ELEV} / Unknown: ${UNKNOWN}"
        attributes = {"SIZE": "48IN", "INVERT_ELEV": 99.25}

        result = export_service._substitute_labels(template, attributes)

        # Should stop at first unresolved placeholder
        assert result == "MH-48IN / INV: 99.25 / Unknown:"
        assert "${UNKNOWN}" not in result

    def test_no_placeholders(self, export_service):
        """Test template with no placeholders."""
        template = "Static Label Text"
        attributes = {"SIZE": "48IN"}

        result = export_service._substitute_labels(template, attributes)

        assert result == "Static Label Text"

    def test_empty_template(self, export_service):
        """Test substitution with empty template."""
        template = ""
        attributes = {"SIZE": "48IN"}

        result = export_service._substitute_labels(template, attributes)

        assert result == ""

    def test_empty_attributes(self, export_service):
        """Test substitution with empty attributes."""
        template = "MH-${SIZE}"
        attributes = {}

        result = export_service._substitute_labels(template, attributes)

        # Unresolved placeholder should be cleaned
        assert "${SIZE}" not in result

    def test_all_attributes_substituted(self, export_service, complete_attributes):
        """Test substitution with all available attributes."""
        template = "${FEATURE_CODE}-${SIZE}-${MATERIAL}-${DEPTH}"

        result = export_service._substitute_labels(template, complete_attributes)

        assert result == "SDMH-48IN-CONCRETE-6.25"

    def test_boolean_value_substitution(self, export_service):
        """Test substitution with boolean values."""
        template = "Active: ${IS_ACTIVE}"
        attributes = {"IS_ACTIVE": True}

        result = export_service._substitute_labels(template, attributes)

        assert result == "Active: True"


# ============================================================================
# Trimble FXL Generation Tests
# ============================================================================

class TestTrimbleFXLGeneration:
    """Tests for Trimble FXL XML generation."""

    def test_fxl_generation_complete_data(self, export_service, complete_mapping, complete_attributes):
        """Test FXL generation with complete data."""
        result = export_service.generate_trimble_fxl(complete_mapping, complete_attributes)

        # Should be valid XML
        assert '<?xml version' in result
        assert '<FXL_Feature' in result
        assert '</FXL_Feature>' in result

        # Parse to verify structure
        # Remove XML declaration for parsing
        xml_content = result.split('?>')[1].strip()
        root = ET.fromstring(xml_content)

        assert root.tag == "FXL_Feature"
        assert root.get("Code") == "SDMH"

    def test_fxl_contains_cad_layer(self, export_service, complete_mapping, complete_attributes):
        """Test that FXL contains CAD layer information."""
        result = export_service.generate_trimble_fxl(complete_mapping, complete_attributes)

        xml_content = result.split('?>')[1].strip()
        root = ET.fromstring(xml_content)

        cad_layer = root.find("CAD_Layer")
        assert cad_layer is not None
        assert cad_layer.text == "C-SSWR-MH-48IN"

    def test_fxl_contains_cad_block(self, export_service, complete_mapping, complete_attributes):
        """Test that FXL contains CAD block information."""
        result = export_service.generate_trimble_fxl(complete_mapping, complete_attributes)

        xml_content = result.split('?>')[1].strip()
        root = ET.fromstring(xml_content)

        cad_block = root.find("CAD_Block")
        assert cad_block is not None
        assert cad_block.text == "MH-48-CONC-BLOCK"

    def test_fxl_contains_point_data(self, export_service, complete_mapping, complete_attributes):
        """Test that FXL contains point data with correct ID."""
        result = export_service.generate_trimble_fxl(complete_mapping, complete_attributes)

        xml_content = result.split('?>')[1].strip()
        root = ET.fromstring(xml_content)

        point_data = root.find("PointData")
        assert point_data is not None
        assert point_data.get("ID") == "12345"

    def test_fxl_contains_position(self, export_service, complete_mapping, complete_attributes):
        """Test that FXL contains position data."""
        result = export_service.generate_trimble_fxl(complete_mapping, complete_attributes)

        xml_content = result.split('?>')[1].strip()
        root = ET.fromstring(xml_content)

        point_data = root.find("PointData")
        position = point_data.find("Position")
        assert position is not None
        assert "X=" in position.text
        assert "Y=" in position.text
        assert "Z=" in position.text

    def test_fxl_contains_annotation_with_substitution(self, export_service, complete_mapping, complete_attributes):
        """Test that FXL contains annotation with label substitution."""
        result = export_service.generate_trimble_fxl(complete_mapping, complete_attributes)

        xml_content = result.split('?>')[1].strip()
        root = ET.fromstring(xml_content)

        annotation = root.find("Annotation")
        assert annotation is not None
        # Template: "MH-${SIZE} / INV: ${INVERT_ELEV}"
        # Should become: "MH-48IN / INV: 99.25"
        assert annotation.text == "MH-48IN / INV: 99.25"

    def test_fxl_missing_point_id_uses_default(self, export_service, complete_mapping):
        """Test that missing POINT_ID uses default value 999."""
        attributes = {"FEATURE_CODE": "SDMH"}  # No POINT_ID

        result = export_service.generate_trimble_fxl(complete_mapping, attributes)

        xml_content = result.split('?>')[1].strip()
        root = ET.fromstring(xml_content)

        point_data = root.find("PointData")
        assert point_data.get("ID") == "999"

    def test_fxl_missing_feature_code_uses_default(self, export_service, complete_mapping):
        """Test that missing FEATURE_CODE uses default value 'UNKNOWN'."""
        attributes = {"POINT_ID": 12345}  # No FEATURE_CODE

        result = export_service.generate_trimble_fxl(complete_mapping, attributes)

        xml_content = result.split('?>')[1].strip()
        root = ET.fromstring(xml_content)

        assert root.get("Code") == "UNKNOWN"

    def test_fxl_missing_cad_layer_uses_default(self, export_service, complete_attributes):
        """Test that missing cad_layer uses default value."""
        mapping = {"cad_block": "BLOCK-1", "cad_label_style": "Label"}

        result = export_service.generate_trimble_fxl(mapping, complete_attributes)

        xml_content = result.split('?>')[1].strip()
        root = ET.fromstring(xml_content)

        cad_layer = root.find("CAD_Layer")
        assert cad_layer.text == "C-NONE"

    def test_fxl_missing_cad_block_uses_default(self, export_service, complete_attributes):
        """Test that missing cad_block uses default value."""
        mapping = {"cad_layer": "C-LAYER", "cad_label_style": "Label"}

        result = export_service.generate_trimble_fxl(mapping, complete_attributes)

        xml_content = result.split('?>')[1].strip()
        root = ET.fromstring(xml_content)

        cad_block = root.find("CAD_Block")
        assert cad_block.text == "BLOCK-NONE"

    def test_fxl_missing_label_style_uses_default(self, export_service, complete_attributes):
        """Test that missing cad_label_style uses default value."""
        mapping = {"cad_layer": "C-LAYER", "cad_block": "BLOCK-1"}

        result = export_service.generate_trimble_fxl(mapping, complete_attributes)

        xml_content = result.split('?>')[1].strip()
        root = ET.fromstring(xml_content)

        annotation = root.find("Annotation")
        assert annotation.text == "No Label Defined"

    def test_fxl_xml_is_pretty_printed(self, export_service, complete_mapping, complete_attributes):
        """Test that FXL XML is pretty-printed with indentation."""
        result = export_service.generate_trimble_fxl(complete_mapping, complete_attributes)

        # Pretty-printed XML should have indentation
        assert '  ' in result  # Contains spaces for indentation
        assert '\n' in result   # Contains newlines

    @patch('services.export_template_service.logger')
    def test_fxl_generation_logs_success(self, mock_logger, export_service, complete_mapping, complete_attributes):
        """Test that FXL generation logs success message."""
        export_service.generate_trimble_fxl(complete_mapping, complete_attributes)

        # Check that logging occurred
        assert mock_logger.info.called
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Generated FXL for Point 12345" in call for call in info_calls)
        assert any("SDMH" in call for call in info_calls)


# ============================================================================
# Civil 3D Description Key Generation Tests
# ============================================================================

class TestCivil3DDescriptionKey:
    """Tests for Civil 3D Description Key generation."""

    def test_desc_key_generation_complete_data(self, export_service, complete_mapping, complete_attributes):
        """Test description key generation with complete data."""
        result = export_service.generate_civil3d_desc_key(complete_mapping, complete_attributes)

        # Should contain standard Civil 3D format
        assert "; --- Civil 3D Description Key Entry ---" in result
        assert 'CODE="SDMH"' in result
        assert 'LAYER="C-SSWR-MH-48IN"' in result
        assert 'BLOCK NAME="MH-48-CONC-BLOCK"' in result

    def test_desc_key_contains_feature_code(self, export_service, complete_mapping, complete_attributes):
        """Test that description key contains feature code."""
        result = export_service.generate_civil3d_desc_key(complete_mapping, complete_attributes)

        assert 'CODE="SDMH"' in result

    def test_desc_key_contains_cad_layer(self, export_service, complete_mapping, complete_attributes):
        """Test that description key contains CAD layer."""
        result = export_service.generate_civil3d_desc_key(complete_mapping, complete_attributes)

        assert 'LAYER="C-SSWR-MH-48IN"' in result

    def test_desc_key_contains_cad_block(self, export_service, complete_mapping, complete_attributes):
        """Test that description key contains CAD block."""
        result = export_service.generate_civil3d_desc_key(complete_mapping, complete_attributes)

        assert 'BLOCK NAME="MH-48-CONC-BLOCK"' in result

    def test_desc_key_contains_label_style(self, export_service, complete_mapping, complete_attributes):
        """Test that description key contains label style."""
        result = export_service.generate_civil3d_desc_key(complete_mapping, complete_attributes)

        assert 'POINT LABEL STYLE="MH-${SIZE} / INV: ${INVERT_ELEV}"' in result

    def test_desc_key_contains_label_preview(self, export_service, complete_mapping, complete_attributes):
        """Test that description key contains label preview with substitution."""
        result = export_service.generate_civil3d_desc_key(complete_mapping, complete_attributes)

        # Template: "MH-${SIZE} / INV: ${INVERT_ELEV}"
        # Should become: "MH-48IN / INV: 99.25"
        assert 'LABEL_PREVIEW="MH-48IN / INV: 99.25"' in result

    def test_desc_key_contains_source_mapping_id(self, export_service, complete_mapping, complete_attributes):
        """Test that description key contains source mapping ID."""
        result = export_service.generate_civil3d_desc_key(complete_mapping, complete_attributes)

        assert '; Source: SSM Mapping ID 301' in result

    def test_desc_key_missing_feature_code_uses_default(self, export_service, complete_mapping):
        """Test that missing FEATURE_CODE uses default value."""
        attributes = {"POINT_ID": 12345}  # No FEATURE_CODE

        result = export_service.generate_civil3d_desc_key(complete_mapping, attributes)

        assert 'CODE="UNKNOWN"' in result

    def test_desc_key_missing_cad_layer_uses_default(self, export_service, complete_attributes):
        """Test that missing cad_layer uses default value."""
        mapping = {"cad_block": "BLOCK-1", "cad_label_style": "Label"}

        result = export_service.generate_civil3d_desc_key(mapping, complete_attributes)

        assert 'LAYER="C-NONE"' in result

    def test_desc_key_missing_cad_block_uses_default(self, export_service, complete_attributes):
        """Test that missing cad_block uses default value."""
        mapping = {"cad_layer": "C-LAYER", "cad_label_style": "Label"}

        result = export_service.generate_civil3d_desc_key(mapping, complete_attributes)

        assert 'BLOCK NAME="BLOCK-NONE"' in result

    def test_desc_key_missing_label_style_uses_default(self, export_service, complete_attributes):
        """Test that missing cad_label_style uses default value."""
        mapping = {"cad_layer": "C-LAYER", "cad_block": "BLOCK-1"}

        result = export_service.generate_civil3d_desc_key(mapping, complete_attributes)

        assert 'POINT LABEL STYLE="UTILITY-DEFAULT"' in result
        assert 'LABEL_PREVIEW="N/A"' in result

    def test_desc_key_missing_source_mapping_id(self, export_service, complete_attributes):
        """Test that missing source_mapping_id uses N/A."""
        mapping = {"cad_layer": "C-LAYER", "cad_block": "BLOCK-1", "cad_label_style": "Label"}

        result = export_service.generate_civil3d_desc_key(mapping, complete_attributes)

        assert '; Source: SSM Mapping ID N/A' in result

    def test_desc_key_contains_standard_sections(self, export_service, complete_mapping, complete_attributes):
        """Test that description key contains all standard sections."""
        result = export_service.generate_civil3d_desc_key(complete_mapping, complete_attributes)

        # Should contain all standard fields
        assert 'POINT STYLE="STANDARD"' in result
        assert 'TEXT HEIGHT=0.10' in result
        assert '-------------------------------------------' in result

    @patch('services.export_template_service.logger')
    def test_desc_key_generation_logs_success(self, mock_logger, export_service, complete_mapping, complete_attributes):
        """Test that description key generation logs success message."""
        export_service.generate_civil3d_desc_key(complete_mapping, complete_attributes)

        # Check that logging occurred
        assert mock_logger.info.called
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Generated Civil 3D Key for code SDMH" in call for call in info_calls)
        assert any("C-SSWR-MH-48IN" in call for call in info_calls)


# ============================================================================
# Integration Tests
# ============================================================================

class TestExportIntegration:
    """Integration tests for export template generation."""

    def test_generate_both_formats(self, export_service, complete_mapping, complete_attributes):
        """Test generating both FXL and Civil 3D formats for the same data."""
        fxl_result = export_service.generate_trimble_fxl(complete_mapping, complete_attributes)
        c3d_result = export_service.generate_civil3d_desc_key(complete_mapping, complete_attributes)

        # Both should be generated successfully
        assert fxl_result is not None
        assert c3d_result is not None

        # Both should contain the same feature code
        assert "SDMH" in fxl_result
        assert "SDMH" in c3d_result

        # Both should have the same label substitution result
        expected_label = "MH-48IN / INV: 99.25"
        assert expected_label in fxl_result
        assert expected_label in c3d_result

    def test_water_valve_export(self, export_service):
        """Test export for a water valve feature."""
        mapping = {
            "source_mapping_id": 401,
            "cad_layer": "C-WATR-VALVE-8IN",
            "cad_block": "VALVE-8-GATE",
            "cad_label_style": "WV-${SIZE}"
        }

        attributes = {
            "POINT_ID": 9001,
            "FEATURE_CODE": "WV",
            "SIZE": "8IN",
            "TYPE": "GATE",
            "OWNER": "CITY"
        }

        fxl_result = export_service.generate_trimble_fxl(mapping, attributes)
        c3d_result = export_service.generate_civil3d_desc_key(mapping, attributes)

        # Verify FXL
        assert "WV" in fxl_result
        assert "WV-8IN" in fxl_result

        # Verify Civil 3D
        assert 'CODE="WV"' in c3d_result
        assert 'LABEL_PREVIEW="WV-8IN"' in c3d_result

    def test_storm_inlet_export(self, export_service):
        """Test export for a storm inlet feature."""
        mapping = {
            "source_mapping_id": 501,
            "cad_layer": "C-STRM-INLET-CB",
            "cad_block": "INLET-CB-BLOCK",
            "cad_label_style": "INLET-${TYPE}"
        }

        attributes = {
            "POINT_ID": 7777,
            "FEATURE_CODE": "SI",
            "TYPE": "CURB",
            "RIM_ELEV": 102.5
        }

        fxl_result = export_service.generate_trimble_fxl(mapping, attributes)
        c3d_result = export_service.generate_civil3d_desc_key(mapping, attributes)

        # Verify FXL
        assert "SI" in fxl_result
        assert "INLET-CURB" in fxl_result

        # Verify Civil 3D
        assert 'CODE="SI"' in c3d_result
        assert 'LABEL_PREVIEW="INLET-CURB"' in c3d_result

    def test_minimal_data_export(self, export_service):
        """Test export with minimal data (only required fields)."""
        mapping = {}  # All defaults
        attributes = {}  # All defaults

        fxl_result = export_service.generate_trimble_fxl(mapping, attributes)
        c3d_result = export_service.generate_civil3d_desc_key(mapping, attributes)

        # Should still generate valid output with defaults
        assert fxl_result is not None
        assert c3d_result is not None
        assert "UNKNOWN" in fxl_result
        assert "UNKNOWN" in c3d_result


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_mapping_and_attributes(self, export_service):
        """Test with completely empty mapping and attributes."""
        result_fxl = export_service.generate_trimble_fxl({}, {})
        result_c3d = export_service.generate_civil3d_desc_key({}, {})

        # Should not crash, should use defaults
        assert result_fxl is not None
        assert result_c3d is not None

    def test_none_values_in_attributes(self, export_service, complete_mapping):
        """Test with None values in attributes."""
        attributes = {
            "POINT_ID": None,
            "FEATURE_CODE": None,
            "SIZE": None
        }

        result_fxl = export_service.generate_trimble_fxl(complete_mapping, attributes)
        result_c3d = export_service.generate_civil3d_desc_key(complete_mapping, attributes)

        # Should handle None gracefully
        assert result_fxl is not None
        assert result_c3d is not None

    def test_special_characters_in_label(self, export_service):
        """Test label substitution with special characters."""
        mapping = {
            "cad_layer": "C-LAYER",
            "cad_block": "BLOCK",
            "cad_label_style": "Type: ${TYPE} & Size: ${SIZE}"
        }

        attributes = {
            "POINT_ID": 1,
            "FEATURE_CODE": "TEST",
            "TYPE": "Special/Type",
            "SIZE": "12\"x18\""
        }

        result_fxl = export_service.generate_trimble_fxl(mapping, attributes)
        result_c3d = export_service.generate_civil3d_desc_key(mapping, attributes)

        # Should handle special characters
        assert "Special/Type" in result_fxl
        assert "Special/Type" in result_c3d

    def test_very_long_label_template(self, export_service):
        """Test with very long label template."""
        mapping = {
            "cad_layer": "C-LAYER",
            "cad_block": "BLOCK",
            "cad_label_style": "Feature: ${CODE} | Size: ${SIZE} | Material: ${MATERIAL} | Depth: ${DEPTH} | Owner: ${OWNER}"
        }

        attributes = {
            "POINT_ID": 1,
            "FEATURE_CODE": "SDMH",
            "CODE": "SDMH",
            "SIZE": "48IN",
            "MATERIAL": "CONCRETE",
            "DEPTH": 6.25,
            "OWNER": "CITY"
        }

        result = export_service._substitute_labels(mapping["cad_label_style"], attributes)

        # Should handle long templates
        assert "Feature: SDMH" in result
        assert "Size: 48IN" in result
        assert "Material: CONCRETE" in result

    @patch('services.export_template_service.logger')
    def test_logging_on_initialization(self, mock_logger):
        """Test that initialization is logged."""
        service = ExportTemplateService()

        # Logger should have been called
        assert mock_logger.info.called
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("ExportTemplateService initialized" in call for call in info_calls)

    def test_unicode_characters_in_attributes(self, export_service):
        """Test handling of unicode characters in attributes."""
        mapping = {
            "cad_layer": "C-LAYER",
            "cad_block": "BLOCK",
            "cad_label_style": "Location: ${LOCATION}"
        }

        attributes = {
            "POINT_ID": 1,
            "FEATURE_CODE": "TEST",
            "LOCATION": "Montréal"
        }

        result = export_service._substitute_labels(mapping["cad_label_style"], attributes)

        # Should handle unicode characters
        assert "Montréal" in result
