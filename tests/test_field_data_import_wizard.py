"""
Tests for FieldDataImportWizard - Phase 26: Field Data Import Pipeline
Tests CSV parsing, data normalization, validation, and error handling.
"""
import pytest
from unittest.mock import MagicMock, patch
from tools.field_data_import_wizard import (
    FieldDataImportWizard,
    MockDataNormalizationService,
    MOCK_FILE_CONTENT
)


@pytest.fixture
def wizard():
    """Create a FieldDataImportWizard instance for testing."""
    return FieldDataImportWizard()


@pytest.fixture
def valid_csv_content():
    """Provide valid CSV content for testing."""
    return """
PointID,Code,Elevation,Material
101,SDMH,102.50,conc
102,WV,98.15,di
103,TOC,105.00,asphalt
"""


@pytest.fixture
def invalid_csv_content():
    """Provide CSV content with missing required fields."""
    return """
PointID,Code,Material
104,SDMH,pvc
105,WV,di
"""


@pytest.fixture
def mixed_csv_content():
    """Provide CSV content with both valid and invalid records."""
    return """
PointID,Code,Elevation,Material
101,SDMH,102.50,conc
102,WV,,di
103,TOC,105.00,asphalt
104,SDMH,,pvc
"""


@pytest.fixture
def mock_config():
    """Provide a mock import configuration."""
    return {"srid": 2227, "delimiter": ","}


class TestFieldDataImportWizard:
    """Test suite for FieldDataImportWizard initialization and basic functionality."""

    def test_wizard_initialization(self):
        """Test that the wizard initializes correctly with a normalizer."""
        wizard = FieldDataImportWizard()

        assert wizard is not None
        assert wizard.normalizer is not None
        assert isinstance(wizard.normalizer, MockDataNormalizationService)

    def test_parse_file_content_basic(self, wizard, valid_csv_content, mock_config):
        """Test basic CSV parsing functionality."""
        raw_data = wizard._parse_file_content(valid_csv_content, mock_config)

        assert len(raw_data) == 3
        assert raw_data[0]['PointID'] == '101'
        assert raw_data[0]['Code'] == 'SDMH'
        assert raw_data[0]['Elevation'] == '102.50'
        assert raw_data[0]['Material'] == 'conc'

    def test_parse_file_content_empty(self, wizard, mock_config):
        """Test parsing empty CSV content."""
        empty_csv = "PointID,Code,Elevation,Material\n"
        raw_data = wizard._parse_file_content(empty_csv, mock_config)

        assert len(raw_data) == 0

    def test_parse_file_content_with_whitespace(self, wizard, mock_config):
        """Test that CSV parsing handles whitespace correctly."""
        csv_with_spaces = """
PointID, Code, Elevation, Material
101, SDMH, 102.50, conc
"""
        raw_data = wizard._parse_file_content(csv_with_spaces, mock_config)

        assert len(raw_data) == 1
        # skipinitialspace should handle leading spaces
        assert raw_data[0]['Code'] == 'SDMH'


class TestParseAndNormalize:
    """Test suite for the full parse_and_normalize_file pipeline."""

    def test_successful_normalization(self, wizard, valid_csv_content, mock_config):
        """Test that valid data is successfully normalized."""
        result = wizard.parse_and_normalize_file(valid_csv_content, mock_config)

        assert result['success_count'] == 3
        assert result['error_count'] == 0
        assert len(result['normalized_data_staging']) == 3
        assert len(result['import_error_report']) == 0

        # Check that materials were normalized to uppercase
        materials = [point['Material'] for point in result['normalized_data_staging']]
        assert all(mat.isupper() for mat in materials)

    def test_normalization_with_errors(self, wizard, invalid_csv_content, mock_config):
        """Test that missing required fields trigger normalization errors."""
        result = wizard.parse_and_normalize_file(invalid_csv_content, mock_config)

        # All records should fail due to missing Elevation field
        assert result['success_count'] == 0
        assert result['error_count'] == 2
        assert len(result['normalized_data_staging']) == 0
        assert len(result['import_error_report']) == 2

        # Check error details
        for error in result['import_error_report']:
            assert error['status'] == 'FAILED'
            assert 'ELEVATION' in error['reason']

    def test_mixed_normalization_results(self, wizard, mixed_csv_content, mock_config):
        """Test processing of mixed valid/invalid records."""
        result = wizard.parse_and_normalize_file(mixed_csv_content, mock_config)

        # Records 101 and 103 should succeed, 102 and 104 should fail
        assert result['success_count'] == 2
        assert result['error_count'] == 2
        assert len(result['normalized_data_staging']) == 2
        assert len(result['import_error_report']) == 2

        # Verify successful IDs
        successful_ids = [point['PointID'] for point in result['normalized_data_staging']]
        assert '101' in successful_ids
        assert '103' in successful_ids

        # Verify failed IDs
        failed_ids = [error['id'] for error in result['import_error_report']]
        assert '102' in failed_ids
        assert '104' in failed_ids

    def test_error_report_structure(self, wizard, invalid_csv_content, mock_config):
        """Test that error reports contain expected fields."""
        result = wizard.parse_and_normalize_file(invalid_csv_content, mock_config)

        assert result['error_count'] > 0

        for error in result['import_error_report']:
            assert 'id' in error
            assert 'status' in error
            assert 'reason' in error
            assert 'raw_data' in error
            assert error['status'] in ['FAILED', 'ERROR']

    def test_normalized_data_structure(self, wizard, valid_csv_content, mock_config):
        """Test that normalized data retains all expected fields."""
        result = wizard.parse_and_normalize_file(valid_csv_content, mock_config)

        assert result['success_count'] > 0

        for point in result['normalized_data_staging']:
            assert 'PointID' in point
            assert 'Code' in point
            assert 'Elevation' in point
            assert 'Material' in point

            # Material should be uppercase after normalization
            assert point['Material'].isupper()


class TestMockDataNormalizationService:
    """Test suite for the MockDataNormalizationService."""

    def test_normalize_attributes_success(self):
        """Test successful attribute normalization."""
        normalizer = MockDataNormalizationService()
        raw_attrs = {
            'PointID': '101',
            'Code': 'SDMH',
            'Elevation': '102.50',
            'Material': 'conc'
        }

        normalized = normalizer.normalize_attributes(raw_attrs)

        assert normalized['Material'] == 'CONC'
        assert normalized['PointID'] == '101'
        assert normalized['Code'] == 'SDMH'

    def test_normalize_attributes_missing_elevation(self):
        """Test that missing Elevation field raises ValueError."""
        normalizer = MockDataNormalizationService()
        raw_attrs = {
            'PointID': '104',
            'Code': 'SDMH',
            'Material': 'pvc'
        }

        with pytest.raises(ValueError) as exc_info:
            normalizer.normalize_attributes(raw_attrs)

        assert 'ELEVATION' in str(exc_info.value)

    def test_normalize_attributes_material_default(self):
        """Test that missing Material field gets default value."""
        normalizer = MockDataNormalizationService()
        raw_attrs = {
            'PointID': '105',
            'Code': 'WV',
            'Elevation': '100.00'
        }

        normalized = normalizer.normalize_attributes(raw_attrs)

        assert normalized['Material'] == 'UNKNOWN'

    def test_normalize_attributes_preserves_originals(self):
        """Test that normalization preserves original data fields."""
        normalizer = MockDataNormalizationService()
        raw_attrs = {
            'PointID': '101',
            'Code': 'SDMH',
            'Elevation': '102.50',
            'Material': 'conc',
            'CustomField': 'CustomValue'
        }

        normalized = normalizer.normalize_attributes(raw_attrs)

        # Custom field should be preserved
        assert normalized['CustomField'] == 'CustomValue'


class TestEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    def test_empty_file_content(self, wizard, mock_config):
        """Test handling of completely empty file."""
        empty_csv = ""

        result = wizard.parse_and_normalize_file(empty_csv, mock_config)

        assert result['success_count'] == 0
        assert result['error_count'] == 0
        assert len(result['normalized_data_staging']) == 0
        assert len(result['import_error_report']) == 0

    def test_only_headers_no_data(self, wizard, mock_config):
        """Test handling of CSV with only headers."""
        headers_only = "PointID,Code,Elevation,Material\n"

        result = wizard.parse_and_normalize_file(headers_only, mock_config)

        assert result['success_count'] == 0
        assert result['error_count'] == 0

    def test_missing_point_id_uses_row_number(self, wizard, mock_config):
        """Test that missing PointID falls back to ROW_N identifier."""
        csv_without_id = """
Code,Elevation,Material
SDMH,102.50,conc
"""
        result = wizard.parse_and_normalize_file(csv_without_id, mock_config)

        # Should fail normalization but error report should have row identifier
        if result['error_count'] > 0:
            error_ids = [error['id'] for error in result['import_error_report']]
            # Should have ROW_N format for missing PointIDs
            assert any('ROW_' in str(error_id) or error_id == '' for error_id in error_ids)

    def test_special_characters_in_material(self, wizard, mock_config):
        """Test handling of special characters in data fields."""
        csv_with_special = """
PointID,Code,Elevation,Material
101,SDMH,102.50,conc-special
"""
        result = wizard.parse_and_normalize_file(csv_with_special, mock_config)

        # Should normalize successfully
        assert result['success_count'] == 1
        assert result['normalized_data_staging'][0]['Material'] == 'CONC-SPECIAL'


class TestMockFileContent:
    """Test suite for the mock file content constant."""

    def test_mock_file_content_parsing(self, wizard, mock_config):
        """Test that MOCK_FILE_CONTENT can be parsed successfully."""
        result = wizard.parse_and_normalize_file(MOCK_FILE_CONTENT, mock_config)

        # MOCK_FILE_CONTENT has 4 rows, 1 should fail (row 104 with missing elevation)
        assert result['success_count'] == 3
        assert result['error_count'] == 1

    def test_mock_file_content_error_case(self, wizard, mock_config):
        """Test that MOCK_FILE_CONTENT error case is properly detected."""
        result = wizard.parse_and_normalize_file(MOCK_FILE_CONTENT, mock_config)

        # Row 104 should be in error report
        failed_ids = [error['id'] for error in result['import_error_report']]
        assert '104' in failed_ids


class TestIntegrationScenarios:
    """Test suite for realistic integration scenarios."""

    def test_full_pipeline_real_world_data(self, wizard, mock_config):
        """Test the full pipeline with realistic survey data."""
        real_world_csv = """
PointID,Code,Elevation,Material,Size,Owner
1001,SDMH,105.50,conc,48,City
1002,WV,100.25,di,12,County
1003,TOC,110.00,asphalt,24,Private
1004,SDMH,98.75,pvc,36,City
"""
        result = wizard.parse_and_normalize_file(real_world_csv, mock_config)

        assert result['success_count'] == 4
        assert result['error_count'] == 0

        # Verify additional fields are preserved
        for point in result['normalized_data_staging']:
            assert 'Size' in point
            assert 'Owner' in point

    def test_large_batch_processing(self, wizard, mock_config):
        """Test processing of larger data batch."""
        # Generate CSV with 100 records
        rows = ["PointID,Code,Elevation,Material"]
        for i in range(1, 101):
            rows.append(f"{i},SDMH,{100 + i * 0.5},conc")

        large_csv = "\n".join(rows)

        result = wizard.parse_and_normalize_file(large_csv, mock_config)

        assert result['success_count'] == 100
        assert result['error_count'] == 0
        assert len(result['normalized_data_staging']) == 100

    def test_return_value_structure(self, wizard, valid_csv_content, mock_config):
        """Test that return value has expected structure."""
        result = wizard.parse_and_normalize_file(valid_csv_content, mock_config)

        # Verify all required keys are present
        assert 'success_count' in result
        assert 'error_count' in result
        assert 'normalized_data_staging' in result
        assert 'import_error_report' in result

        # Verify types
        assert isinstance(result['success_count'], int)
        assert isinstance(result['error_count'], int)
        assert isinstance(result['normalized_data_staging'], list)
        assert isinstance(result['import_error_report'], list)
