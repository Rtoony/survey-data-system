"""
Comprehensive unit tests for DataNormalizationService.

Tests cover:
- Text normalization and standardization
- Material abbreviation expansion
- Case conversion and whitespace handling
- Derived attribute calculations (DEPTH)
- Edge cases with missing or invalid data
- Type conversion handling
"""

import pytest
from unittest.mock import patch, MagicMock
from typing import Dict, Any

from services.data_normalization_service import DataNormalizationService


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_db_connection():
    """Mock database connection for testing."""
    # Create a mock result that simulates database rows
    mock_result = MagicMock()

    # Simulate rows returned from ssm_standards_lookup table
    class MockRow:
        def __init__(self, raw_value, standardized_value):
            self.raw_value = raw_value
            self.standardized_value = standardized_value

    mock_rows = [
        MockRow("CONC", "CONCRETE"),
        MockRow("PVC", "PVC"),
        MockRow("BRICK", "BRICK"),
        MockRow("STEEL", "STEEL"),
        MockRow("DI", "DUCTILE_IRON"),
        MockRow("CI", "CAST_IRON"),
    ]

    mock_result.fetchall.return_value = mock_rows

    # Create a mock connection
    mock_conn = MagicMock()
    mock_conn.execute.return_value = mock_result
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)

    return mock_conn

@pytest.fixture
def normalization_service(mock_db_connection):
    """Create DataNormalizationService instance with mocked database."""
    with patch('services.data_normalization_service.get_db') as mock_get_db:
        mock_get_db.return_value = mock_db_connection
        service = DataNormalizationService()
    return service


# ============================================================================
# Text Normalization Tests
# ============================================================================

class TestTextNormalization:
    """Tests for text attribute cleaning and standardization."""

    def test_material_abbreviation_expansion(self, normalization_service):
        """Test that material abbreviations are expanded correctly."""
        raw_attributes = {
            "MATERIAL": "conc",
            "SIZE": 48.0
        }

        result = normalization_service.normalize_attributes(raw_attributes)

        assert result["MATERIAL"] == "CONCRETE"
        assert result["SIZE"] == 48.0  # Unchanged

    def test_multiple_material_abbreviations(self, normalization_service):
        """Test various material abbreviation expansions."""
        test_cases = [
            ("pvc", "PVC"),
            ("di", "DUCTILE_IRON"),
            ("ci", "CAST_IRON"),
            ("brick", "BRICK"),
            ("steel", "STEEL"),
        ]

        for input_material, expected_output in test_cases:
            result = normalization_service.normalize_attributes({"MATERIAL": input_material})
            assert result["MATERIAL"] == expected_output, f"Failed for {input_material}"

    def test_uppercase_conversion(self, normalization_service):
        """Test that string attributes are converted to uppercase."""
        raw_attributes = {
            "TYPE": "sanitary",
            "OWNER": "city of santa rosa",
            "JURISDICTION": "county"
        }

        result = normalization_service.normalize_attributes(raw_attributes)

        assert result["TYPE"] == "SANITARY"
        assert result["OWNER"] == "CITY OF SANTA ROSA"
        assert result["JURISDICTION"] == "COUNTY"

    def test_whitespace_trimming(self, normalization_service):
        """Test that leading and trailing whitespace is removed."""
        raw_attributes = {
            "MATERIAL": "  conc  ",
            "JURISDICTION": " santa rosa ",
            "OWNER": "  city  "
        }

        result = normalization_service.normalize_attributes(raw_attributes)

        assert result["MATERIAL"] == "CONCRETE"
        assert result["JURISDICTION"] == "SANTA ROSA"
        assert result["OWNER"] == "CITY"

    def test_unknown_material_preserved(self, normalization_service):
        """Test that unknown materials are uppercased but not changed."""
        raw_attributes = {
            "MATERIAL": "fiberglass"
        }

        result = normalization_service.normalize_attributes(raw_attributes)

        assert result["MATERIAL"] == "FIBERGLASS"

    def test_non_string_attributes_unchanged(self, normalization_service):
        """Test that non-string attributes are not processed as strings."""
        raw_attributes = {
            "MATERIAL": 12345,  # Numeric material (invalid, but shouldn't crash)
            "SIZE": 48.0,
            "TYPE": None
        }

        # Should handle gracefully without crashing
        result = normalization_service.normalize_attributes(raw_attributes)

        assert result["MATERIAL"] == 12345  # Unchanged
        assert result["SIZE"] == 48.0
        assert result["TYPE"] is None


# ============================================================================
# Derived Attribute Calculation Tests
# ============================================================================

class TestDerivedCalculations:
    """Tests for derived attribute calculations."""

    def test_depth_calculation_basic(self, normalization_service):
        """Test basic DEPTH calculation from RIM_ELEV and INVERT_ELEV."""
        raw_attributes = {
            "RIM_ELEV": 105.50,
            "INVERT_ELEV": 99.25
        }

        result = normalization_service.normalize_attributes(raw_attributes)

        assert "DEPTH" in result
        assert result["DEPTH"] == 6.25  # 105.50 - 99.25

    def test_depth_calculation_rounding(self, normalization_service):
        """Test that DEPTH is rounded to 2 decimal places."""
        raw_attributes = {
            "RIM_ELEV": 100.123456,
            "INVERT_ELEV": 95.456789
        }

        result = normalization_service.normalize_attributes(raw_attributes)

        assert "DEPTH" in result
        assert result["DEPTH"] == 4.67  # Rounded to 2 decimals

    def test_depth_calculation_with_integer_values(self, normalization_service):
        """Test DEPTH calculation with integer elevation values."""
        raw_attributes = {
            "RIM_ELEV": 100,
            "INVERT_ELEV": 95
        }

        result = normalization_service.normalize_attributes(raw_attributes)

        assert "DEPTH" in result
        assert result["DEPTH"] == 5.0

    def test_depth_calculation_with_string_numbers(self, normalization_service):
        """Test that string-formatted numbers are converted for calculation."""
        raw_attributes = {
            "RIM_ELEV": "105.50",
            "INVERT_ELEV": "99.25"
        }

        result = normalization_service.normalize_attributes(raw_attributes)

        assert "DEPTH" in result
        assert result["DEPTH"] == 6.25

    def test_depth_not_calculated_missing_rim(self, normalization_service):
        """Test that DEPTH is not calculated when RIM_ELEV is missing."""
        raw_attributes = {
            "INVERT_ELEV": 99.25,
            "SIZE": 48.0
        }

        result = normalization_service.normalize_attributes(raw_attributes)

        assert "DEPTH" not in result

    def test_depth_not_calculated_missing_invert(self, normalization_service):
        """Test that DEPTH is not calculated when INVERT_ELEV is missing."""
        raw_attributes = {
            "RIM_ELEV": 105.50,
            "SIZE": 48.0
        }

        result = normalization_service.normalize_attributes(raw_attributes)

        assert "DEPTH" not in result

    def test_depth_not_calculated_invalid_rim(self, normalization_service):
        """Test that DEPTH is not calculated when RIM_ELEV is invalid."""
        raw_attributes = {
            "RIM_ELEV": "N/A",
            "INVERT_ELEV": 99.25
        }

        result = normalization_service.normalize_attributes(raw_attributes)

        assert "DEPTH" not in result

    def test_depth_not_calculated_invalid_invert(self, normalization_service):
        """Test that DEPTH is not calculated when INVERT_ELEV is invalid."""
        raw_attributes = {
            "RIM_ELEV": 105.50,
            "INVERT_ELEV": "unknown"
        }

        result = normalization_service.normalize_attributes(raw_attributes)

        assert "DEPTH" not in result

    def test_depth_not_calculated_none_values(self, normalization_service):
        """Test that DEPTH is not calculated when elevations are None."""
        raw_attributes = {
            "RIM_ELEV": None,
            "INVERT_ELEV": None
        }

        result = normalization_service.normalize_attributes(raw_attributes)

        assert "DEPTH" not in result


# ============================================================================
# Integration Tests
# ============================================================================

class TestNormalizationIntegration:
    """Integration tests for the full normalization pipeline."""

    def test_full_normalization_pipeline(self, normalization_service):
        """Test complete normalization with all features."""
        raw_attributes = {
            "SIZE": 48.0,
            "RIM_ELEV": 105.50,
            "INVERT_ELEV": 99.25,
            "MATERIAL": "conc",
            "JURISDICTION": "santa rosa ",
            "TYPE": "sanitary",
            "OWNER": "city"
        }

        result = normalization_service.normalize_attributes(raw_attributes)

        # Check text normalization
        assert result["MATERIAL"] == "CONCRETE"
        assert result["JURISDICTION"] == "SANTA ROSA"
        assert result["TYPE"] == "SANITARY"
        assert result["OWNER"] == "CITY"

        # Check derived calculation
        assert result["DEPTH"] == 6.25

        # Check original attributes preserved
        assert result["SIZE"] == 48.0
        assert result["RIM_ELEV"] == 105.50
        assert result["INVERT_ELEV"] == 99.25

    def test_partial_data_normalization(self, normalization_service):
        """Test normalization with partial data (some missing)."""
        raw_attributes = {
            "SIZE": 36.0,
            "RIM_ELEV": 102.0,
            "INVERT_ELEV": "N/A",
            "MATERIAL": "pvc"
        }

        result = normalization_service.normalize_attributes(raw_attributes)

        # Text normalization should still work
        assert result["MATERIAL"] == "PVC"

        # DEPTH should not be calculated
        assert "DEPTH" not in result

        # Original attributes preserved
        assert result["SIZE"] == 36.0

    def test_empty_attributes(self, normalization_service):
        """Test normalization with empty dictionary."""
        raw_attributes = {}

        result = normalization_service.normalize_attributes(raw_attributes)

        assert result == {}

    def test_original_attributes_not_modified(self, normalization_service):
        """Test that the original attributes dictionary is not modified."""
        raw_attributes = {
            "MATERIAL": "conc",
            "RIM_ELEV": 105.50,
            "INVERT_ELEV": 99.25
        }

        original_copy = raw_attributes.copy()
        result = normalization_service.normalize_attributes(raw_attributes)

        # Original should remain unchanged
        assert raw_attributes == original_copy

        # Result should have normalized values
        assert result["MATERIAL"] == "CONCRETE"
        assert result["DEPTH"] == 6.25

    def test_all_string_match_keys_normalized(self, normalization_service):
        """Test that all STRING_MATCH_KEYS are properly normalized."""
        raw_attributes = {
            "MATERIAL": "  conc  ",
            "TYPE": "storm",
            "OWNER": " public ",
            "JURISDICTION": "county"
        }

        result = normalization_service.normalize_attributes(raw_attributes)

        assert result["MATERIAL"] == "CONCRETE"
        assert result["TYPE"] == "STORM"
        assert result["OWNER"] == "PUBLIC"
        assert result["JURISDICTION"] == "COUNTY"


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_negative_depth_calculation(self, normalization_service):
        """Test DEPTH calculation when invert is higher than rim (unusual but possible)."""
        raw_attributes = {
            "RIM_ELEV": 95.0,
            "INVERT_ELEV": 100.0
        }

        result = normalization_service.normalize_attributes(raw_attributes)

        # Should still calculate (negative depth indicates data issue)
        assert result["DEPTH"] == -5.0

    def test_zero_depth_calculation(self, normalization_service):
        """Test DEPTH calculation when rim equals invert."""
        raw_attributes = {
            "RIM_ELEV": 100.0,
            "INVERT_ELEV": 100.0
        }

        result = normalization_service.normalize_attributes(raw_attributes)

        assert result["DEPTH"] == 0.0

    def test_very_large_depth_values(self, normalization_service):
        """Test DEPTH calculation with very large elevation values."""
        raw_attributes = {
            "RIM_ELEV": 10000.0,
            "INVERT_ELEV": 5000.0
        }

        result = normalization_service.normalize_attributes(raw_attributes)

        assert result["DEPTH"] == 5000.0

    def test_very_small_depth_values(self, normalization_service):
        """Test DEPTH calculation with very small elevation differences."""
        raw_attributes = {
            "RIM_ELEV": 100.001,
            "INVERT_ELEV": 100.000
        }

        result = normalization_service.normalize_attributes(raw_attributes)

        assert result["DEPTH"] == 0.0  # Rounds to 0.00

    @patch('services.data_normalization_service.logger')
    @patch('services.data_normalization_service.get_db')
    def test_logging_on_initialization(self, mock_get_db, mock_logger, mock_db_connection):
        """Test that initialization is logged."""
        mock_get_db.return_value = mock_db_connection
        # Create a new instance to trigger the log
        service = DataNormalizationService()
        # Logger should have been called (already called in fixture too)
        assert mock_logger.info.called

    @patch('services.data_normalization_service.logger')
    @patch('services.data_normalization_service.get_db')
    def test_logging_on_normalization(self, mock_get_db, mock_logger, mock_db_connection):
        """Test that normalization process is logged."""
        mock_get_db.return_value = mock_db_connection
        service = DataNormalizationService()
        mock_logger.reset_mock()

        raw_attributes = {
            "RIM_ELEV": 105.50,
            "INVERT_ELEV": 99.25
        }

        service.normalize_attributes(raw_attributes)

        # Check that logging occurred
        assert mock_logger.info.called
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Starting attribute normalization" in call for call in info_calls)
        assert any("Normalization complete" in call for call in info_calls)

    @patch('services.data_normalization_service.get_db')
    def test_database_loading_success(self, mock_get_db, mock_db_connection):
        """Test that standardization lookups are loaded from database on initialization."""
        mock_get_db.return_value = mock_db_connection
        service = DataNormalizationService()

        # Verify lookups were loaded
        assert len(service.standard_lookup) > 0
        assert service.standard_lookup["CONC"] == "CONCRETE"
        assert service.standard_lookup["DI"] == "DUCTILE_IRON"

    @patch('services.data_normalization_service.logger')
    @patch('services.data_normalization_service.get_db')
    def test_database_loading_fallback(self, mock_get_db, mock_logger):
        """Test that service falls back to hardcoded lookups if database fails."""
        # Simulate database connection failure
        mock_get_db.side_effect = Exception("Database connection failed")

        service = DataNormalizationService()

        # Verify warning was logged
        warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
        assert any("Could not load standardization lookups from DB" in call for call in warning_calls)
        assert any("Falling back to minimal hardcoded lookup table" in call for call in warning_calls)

        # Verify fallback lookups are available
        assert len(service.standard_lookup) > 0
        assert service.standard_lookup["CONC"] == "CONCRETE"

        # Verify the service still works with fallback data
        raw_attributes = {"MATERIAL": "conc"}
        result = service.normalize_attributes(raw_attributes)
        assert result["MATERIAL"] == "CONCRETE"
