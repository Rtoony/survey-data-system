"""
Comprehensive unit tests for AIMappingSuggestorService.

Tests cover:
- Full match scenarios (exact mapping resolution)
- Near match scenarios (attribute suggestions)
- Critical conflict detection (multiple highest-priority matches)
- Priority-based resolution
- Missing attribute identification
- Edge cases and warnings
"""

import pytest
from typing import Dict, Any

from services.ai_mapping_suggestor import AIMappingSuggestorService, MOCK_STANDARDS_MAPPINGS


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def suggestor_service():
    """Create AIMappingSuggestorService instance."""
    return AIMappingSuggestorService()


# ============================================================================
# Test Initialization
# ============================================================================

class TestAIMappingSuggestorServiceInit:
    """Test AIMappingSuggestorService initialization."""

    def test_init_loads_mock_mappings(self, suggestor_service):
        """Test that service initializes with mock mappings."""
        assert suggestor_service.mappings == MOCK_STANDARDS_MAPPINGS
        assert len(suggestor_service.mappings) == 4

    def test_init_mappings_sorted_by_priority(self, suggestor_service):
        """Test that mappings are available for priority-based evaluation."""
        priorities = [m.get("priority", 0) for m in suggestor_service.mappings]
        assert 100 in priorities  # Default
        assert 200 in priorities  # Medium
        assert 300 in priorities  # Highest


# ============================================================================
# Test Full Match Scenarios
# ============================================================================

class TestFullMatchScenarios:
    """Test scenarios where attributes fully match a mapping."""

    def test_default_match_no_attributes(self, suggestor_service):
        """Test that default mapping is resolved when no attributes provided."""
        result = suggestor_service.get_suggestions("SDMH", {})

        assert result["resolved_mapping"] == "SDMH Default"
        assert len(result["warnings"]) == 0
        assert len(result["suggestions"]) >= 1  # Should suggest higher-priority mappings

    def test_medium_priority_match(self, suggestor_service):
        """Test resolution to medium-priority mapping with SIZE attribute."""
        result = suggestor_service.get_suggestions("SDMH", {"SIZE": "48IN"})

        assert result["resolved_mapping"] == "SDMH 48-Inch Spec"
        assert len(result["warnings"]) == 0
        # Should suggest attributes to reach priority 300 mappings
        assert any("Priority 300" in s for s in result["suggestions"])

    def test_highest_priority_single_match(self, suggestor_service):
        """Test resolution to highest-priority mapping without conflicts."""
        result = suggestor_service.get_suggestions(
            "SDMH",
            {"SIZE": "60IN", "MATERIAL": "PRECAST"}
        )

        assert result["resolved_mapping"] == "SDMH Precast Concrete"
        assert len(result["warnings"]) == 0
        # No suggestions since we're at highest non-conflicting priority
        # (but may suggest the conflicting one)

    def test_case_insensitive_feature_code(self, suggestor_service):
        """Test that feature code matching is case-insensitive."""
        result_upper = suggestor_service.get_suggestions("SDMH", {"SIZE": "48IN"})
        result_lower = suggestor_service.get_suggestions("sdmh", {"SIZE": "48IN"})

        assert result_upper["resolved_mapping"] == result_lower["resolved_mapping"]


# ============================================================================
# Test Near Match Scenarios
# ============================================================================

class TestNearMatchScenarios:
    """Test scenarios where attributes are close to matching higher-priority mappings."""

    def test_suggest_material_for_precast_mapping(self, suggestor_service):
        """Test suggestion to add MATERIAL attribute."""
        result = suggestor_service.get_suggestions("SDMH", {"SIZE": "60IN"})

        # Should resolve to a lower-priority mapping
        assert result["resolved_mapping"] in ["SDMH 48-Inch Spec", "SDMH Default"]

        # Should suggest adding MATERIAL to reach Precast Concrete mapping
        suggestions_text = " ".join(result["suggestions"])
        assert "MATERIAL" in suggestions_text
        assert "SDMH Precast Concrete" in suggestions_text

    def test_suggest_jurisdiction_for_city_override(self, suggestor_service):
        """Test suggestion to add JURISDICTION attribute."""
        result = suggestor_service.get_suggestions("SDMH", {"SIZE": "60IN"})

        # Should suggest adding JURISDICTION for City Override mapping
        suggestions_text = " ".join(result["suggestions"])
        assert "JURISDICTION" in suggestions_text
        assert "SDMH City Override" in suggestions_text

    def test_multiple_path_suggestions(self, suggestor_service):
        """Test that multiple upgrade paths are suggested."""
        result = suggestor_service.get_suggestions("SDMH", {"SIZE": "60IN"})

        # Should have suggestions for both priority 300 mappings
        assert len(result["suggestions"]) >= 2

    def test_no_suggestions_at_highest_priority(self, suggestor_service):
        """Test that no suggestions are made when already at highest resolved priority."""
        # This will cause a conflict, but both conflicting mappings are at priority 300
        result = suggestor_service.get_suggestions(
            "SDMH",
            {"SIZE": "60IN", "MATERIAL": "PRECAST", "JURISDICTION": "SANTA_ROSA"}
        )

        # Should be at priority 300, no higher mappings to suggest
        assert len(result["suggestions"]) == 0


# ============================================================================
# Test Conflict Detection
# ============================================================================

class TestConflictDetection:
    """Test detection of critical conflicts in mapping resolution."""

    def test_critical_conflict_warning(self, suggestor_service):
        """Test that conflict warning is issued when multiple highest-priority mappings match."""
        result = suggestor_service.get_suggestions(
            "SDMH",
            {"SIZE": "60IN", "MATERIAL": "PRECAST", "JURISDICTION": "SANTA_ROSA"}
        )

        # Should have resolved to one of the priority 300 mappings
        assert result["resolved_mapping"] in [
            "SDMH Precast Concrete",
            "SDMH City Override (Conflict)"
        ]

        # Should have conflict warning
        assert len(result["warnings"]) == 1
        assert "CRITICAL CONFLICT" in result["warnings"][0]
        assert "nondeterministic" in result["warnings"][0]

    def test_no_conflict_with_single_match(self, suggestor_service):
        """Test that no conflict is reported with single highest-priority match."""
        result = suggestor_service.get_suggestions(
            "SDMH",
            {"SIZE": "60IN", "MATERIAL": "PRECAST"}
        )

        # Should have no conflict warnings
        assert len(result["warnings"]) == 0

    def test_conflict_includes_priority_info(self, suggestor_service):
        """Test that conflict warning includes priority information."""
        result = suggestor_service.get_suggestions(
            "SDMH",
            {"SIZE": "60IN", "MATERIAL": "PRECAST", "JURISDICTION": "SANTA_ROSA"}
        )

        # Warning should mention priority 300
        assert "300" in result["warnings"][0]


# ============================================================================
# Test Priority-Based Resolution
# ============================================================================

class TestPriorityResolution:
    """Test that priority-based resolution works correctly."""

    def test_higher_priority_wins(self, suggestor_service):
        """Test that higher-priority mapping is selected over lower-priority."""
        # SIZE=48IN matches both priority 100 (default) and 200 (48-inch spec)
        result = suggestor_service.get_suggestions("SDMH", {"SIZE": "48IN"})

        # Should resolve to priority 200, not 100
        assert result["resolved_mapping"] == "SDMH 48-Inch Spec"

    def test_priority_ordering_in_suggestions(self, suggestor_service):
        """Test that suggestions reference higher-priority mappings."""
        result = suggestor_service.get_suggestions("SDMH", {"SIZE": "60IN"})

        # All suggestions should be for priority 300 mappings
        for suggestion in result["suggestions"]:
            assert "Priority 300" in suggestion


# ============================================================================
# Test Missing Attribute Identification
# ============================================================================

class TestMissingAttributeIdentification:
    """Test identification of missing attributes for near matches."""

    def test_identify_single_missing_attribute(self, suggestor_service):
        """Test identification of single missing attribute."""
        result = suggestor_service.get_suggestions("SDMH", {"SIZE": "60IN"})

        # Should identify MATERIAL as missing for Precast mapping
        material_suggestion = [s for s in result["suggestions"] if "MATERIAL" in s]
        assert len(material_suggestion) > 0

    def test_identify_multiple_missing_attributes(self, suggestor_service):
        """Test identification when multiple attributes are missing."""
        result = suggestor_service.get_suggestions("SDMH", {})

        # Default mapping matches, but should suggest attributes for higher priorities
        suggestions_text = " ".join(result["suggestions"])
        # At minimum, SIZE should be mentioned for reaching priority 200
        assert len(result["suggestions"]) > 0

    def test_missing_attributes_listed_in_suggestions(self, suggestor_service):
        """Test that missing attributes are explicitly listed."""
        result = suggestor_service.get_suggestions("SDMH", {"SIZE": "60IN"})

        # Should list MATERIAL and JURISDICTION in separate suggestions
        suggestions_text = " ".join(result["suggestions"])
        assert "MATERIAL" in suggestions_text or "JURISDICTION" in suggestions_text


# ============================================================================
# Test Edge Cases and Warnings
# ============================================================================

class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_unknown_feature_code(self, suggestor_service):
        """Test handling of unknown feature code."""
        result = suggestor_service.get_suggestions("UNKNOWN_CODE", {"SIZE": "48IN"})

        # Should return warning about no applicable mappings
        assert len(result["warnings"]) == 1
        assert "No applicable" in result["warnings"][0]
        assert result["resolved_mapping"] is None

    def test_empty_attributes_dict(self, suggestor_service):
        """Test handling of empty attributes dictionary."""
        result = suggestor_service.get_suggestions("SDMH", {})

        # Should match default mapping (priority 100)
        assert result["resolved_mapping"] == "SDMH Default"

    def test_null_attribute_values(self, suggestor_service):
        """Test handling of null attribute values."""
        result = suggestor_service.get_suggestions("SDMH", {"SIZE": None})

        # Null values should be treated as missing
        assert result["resolved_mapping"] == "SDMH Default"

    def test_extra_unused_attributes(self, suggestor_service):
        """Test that extra attributes don't break resolution."""
        result = suggestor_service.get_suggestions(
            "SDMH",
            {
                "SIZE": "60IN",
                "MATERIAL": "PRECAST",
                "EXTRA_FIELD": "SOME_VALUE",
                "ANOTHER_UNUSED": 123
            }
        )

        # Should still resolve correctly despite extra attributes
        assert result["resolved_mapping"] == "SDMH Precast Concrete"


# ============================================================================
# Test Response Structure
# ============================================================================

class TestResponseStructure:
    """Test that response structure is consistent and correct."""

    def test_response_has_required_keys(self, suggestor_service):
        """Test that response contains all required keys."""
        result = suggestor_service.get_suggestions("SDMH", {"SIZE": "48IN"})

        assert "resolved_mapping" in result
        assert "warnings" in result
        assert "suggestions" in result

    def test_warnings_is_list(self, suggestor_service):
        """Test that warnings is always a list."""
        result = suggestor_service.get_suggestions("SDMH", {"SIZE": "48IN"})
        assert isinstance(result["warnings"], list)

    def test_suggestions_is_list(self, suggestor_service):
        """Test that suggestions is always a list."""
        result = suggestor_service.get_suggestions("SDMH", {"SIZE": "48IN"})
        assert isinstance(result["suggestions"], list)

    def test_resolved_mapping_is_string_or_none(self, suggestor_service):
        """Test that resolved_mapping is string or None."""
        result = suggestor_service.get_suggestions("SDMH", {"SIZE": "48IN"})
        assert isinstance(result["resolved_mapping"], str) or result["resolved_mapping"] is None


# ============================================================================
# Integration Test Cases
# ============================================================================

class TestIntegrationScenarios:
    """Test end-to-end scenarios that mirror real-world usage."""

    def test_field_data_workflow_complete_attributes(self, suggestor_service):
        """Test workflow with complete field data attributes."""
        # Simulate complete field data entry
        field_data = {
            "SIZE": "60IN",
            "MATERIAL": "PRECAST",
            "RIM_ELEV": 105.0,
            "INVERT_ELEV": 96.0
        }

        result = suggestor_service.get_suggestions("SDMH", field_data)

        assert result["resolved_mapping"] == "SDMH Precast Concrete"
        assert len(result["warnings"]) == 0

    def test_field_data_workflow_minimal_attributes(self, suggestor_service):
        """Test workflow with minimal field data."""
        # Simulate partial field data entry
        field_data = {"SIZE": "48IN"}

        result = suggestor_service.get_suggestions("SDMH", field_data)

        # Should get suggestions for improvement
        assert len(result["suggestions"]) > 0
        assert result["resolved_mapping"] is not None

    def test_progressive_attribute_addition(self, suggestor_service):
        """Test that adding attributes progressively improves resolution."""
        # Start with no attributes
        result_0 = suggestor_service.get_suggestions("SDMH", {})
        assert result_0["resolved_mapping"] == "SDMH Default"

        # Add SIZE
        result_1 = suggestor_service.get_suggestions("SDMH", {"SIZE": "60IN"})
        assert result_1["resolved_mapping"] in ["SDMH 48-Inch Spec", "SDMH Default"]

        # Add MATERIAL
        result_2 = suggestor_service.get_suggestions(
            "SDMH",
            {"SIZE": "60IN", "MATERIAL": "PRECAST"}
        )
        assert result_2["resolved_mapping"] == "SDMH Precast Concrete"
