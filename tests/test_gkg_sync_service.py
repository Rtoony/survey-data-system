"""
Tests for GKGSyncService - Phase 33: Project Override Layer
"""
import pytest
from unittest.mock import MagicMock, patch
from services.gkg_sync_service import GKGSyncService


@pytest.fixture
def mock_db_url():
    """Provide a mock database URL for testing."""
    return "postgresql://test:test@localhost:5432/test_db"


@pytest.fixture
def gkg_service(mock_db_url):
    """Create a GKGSyncService instance with mocked database."""
    with patch('services.gkg_sync_service.create_engine'):
        service = GKGSyncService(mock_db_url)
        return service


class TestProjectOverrideLayer:
    """Test suite for Phase 33: Project Override Layer functionality."""

    def test_fetch_project_overrides_for_project_100(self, gkg_service):
        """Test that project 100 returns expected override mappings."""
        overrides = gkg_service._fetch_project_overrides(100)

        assert len(overrides) == 1
        assert overrides[0]["id"] == 9000
        assert overrides[0]["feature_code"] == "SDMH"
        assert overrides[0]["priority"] == 9999
        assert overrides[0]["layer"] == "CLIENT-48IN-MH"
        assert overrides[0]["block"] == "CLIENT-SPEC-MH-48"

    def test_fetch_project_overrides_for_other_projects(self, gkg_service):
        """Test that other projects return no overrides."""
        overrides = gkg_service._fetch_project_overrides(200)
        assert len(overrides) == 0

        overrides = gkg_service._fetch_project_overrides(999)
        assert len(overrides) == 0

    def test_resolve_mapping_with_project_override(self, gkg_service):
        """Test that project overrides (P=9999) take precedence over global mappings."""
        # This should trigger the project override for project_id=100
        result = gkg_service.resolve_mapping("SDMH", {"SIZE": "48IN"})

        assert result is not None
        assert result["source_mapping_id"] == 9000
        assert result["layer"] == "CLIENT-48IN-MH"
        assert result["block"] == "CLIENT-SPEC-MH-48"

    def test_resolve_mapping_without_override(self, gkg_service):
        """Test that global mappings work when no override applies."""
        # Mock the project override to return empty
        with patch.object(gkg_service, '_fetch_project_overrides', return_value=[]):
            result = gkg_service.resolve_mapping("SDMH", {"SIZE": "60IN"})

            assert result is not None
            # Should return one of the global mappings (101 or 301)
            assert result["source_mapping_id"] in [101, 301]

    def test_resolve_mapping_priority_and_specificity(self, gkg_service):
        """Test that priority and condition count (specificity) determine the winner."""
        # When no override applies, the mapping with higher priority should win
        with patch.object(gkg_service, '_fetch_project_overrides', return_value=[]):
            result = gkg_service.resolve_mapping("SDMH", {"SIZE": "60IN", "MAT": "PRECAST"})

            assert result is not None
            # Mapping 301 has priority=300 and 2 conditions, should beat 101 (priority=100, 0 conditions)
            assert result["source_mapping_id"] == 301
            assert result["layer"] == "B"

    def test_resolve_mapping_no_matches(self, gkg_service):
        """Test behavior when no mappings match the feature code."""
        with patch.object(gkg_service, '_fetch_project_overrides', return_value=[]):
            with patch.object(gkg_service, '_fetch_applicable_mappings', return_value=[]):
                result = gkg_service.resolve_mapping("UNKNOWN_CODE", {})

                assert result is None

    def test_resolve_mapping_combines_override_and_global(self, gkg_service):
        """Test that both override and global mappings are considered."""
        # The service should combine project overrides + global mappings
        # and the override with P=9999 should win

        # Verify that both layers are fetched
        with patch.object(gkg_service, '_fetch_project_overrides') as mock_overrides:
            with patch.object(gkg_service, '_fetch_applicable_mappings') as mock_global:
                mock_overrides.return_value = [
                    {
                        "id": 9000,
                        "feature_code": "SDMH",
                        "conditions": {"SIZE": {"op": "==", "val": "48IN"}},
                        "priority": 9999,
                        "layer": "CLIENT-48IN-MH",
                        "block": "CLIENT-SPEC-MH-48"
                    }
                ]
                mock_global.return_value = [
                    {"id": 101, "feature_code": "SDMH", "conditions": {}, "priority": 100, "layer": "D"}
                ]

                result = gkg_service.resolve_mapping("SDMH", {"SIZE": "48IN"})

                # Both methods should have been called
                mock_overrides.assert_called_once()
                mock_global.assert_called_once_with("SDMH")

                # Override should win due to higher priority
                assert result["source_mapping_id"] == 9000


class TestMappingResolution:
    """Test suite for general mapping resolution logic."""

    def test_fetch_applicable_mappings(self, gkg_service):
        """Test fetching mappings by feature code."""
        mappings = gkg_service._fetch_applicable_mappings("SDMH")
        assert len(mappings) == 2
        assert all(m["feature_code"] == "SDMH" for m in mappings)

    def test_fetch_applicable_mappings_case_insensitive(self, gkg_service):
        """Test that feature code matching is case-insensitive."""
        mappings_upper = gkg_service._fetch_applicable_mappings("SDMH")
        mappings_lower = gkg_service._fetch_applicable_mappings("sdmh")

        assert len(mappings_upper) == len(mappings_lower)

    def test_check_mapping_match(self, gkg_service):
        """Test the condition matching logic."""
        mapping = {"conditions": {"SIZE": {"op": "==", "val": "60IN"}}}
        attributes = {"SIZE": "60IN"}

        is_match, condition_count = gkg_service._check_mapping_match(mapping, attributes)

        # Based on the mocked implementation, it should return True and condition count
        assert is_match is True
        assert condition_count == 1


class TestServiceInitialization:
    """Test suite for service initialization."""

    def test_service_initialization(self, mock_db_url):
        """Test that the service initializes correctly."""
        with patch('services.gkg_sync_service.create_engine') as mock_engine:
            service = GKGSyncService(mock_db_url)

            # Verify engine was created with correct parameters
            mock_engine.assert_called_once_with(
                mock_db_url,
                pool_size=5,
                max_overflow=10
            )

            # Verify graph client was initialized
            assert service.graph_client is not None

    def test_get_connection_context_manager(self, gkg_service):
        """Test that connection context manager works correctly."""
        mock_conn = MagicMock()
        gkg_service.engine.connect = MagicMock(return_value=mock_conn)

        with gkg_service._get_connection() as conn:
            assert conn == mock_conn

        # Verify connection was closed
        mock_conn.close.assert_called_once()
