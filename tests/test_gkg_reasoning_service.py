# tests/test_gkg_reasoning_service.py
import pytest
from services.gkg_reasoning_service import GKGReasoningService


class TestGKGReasoningService:
    """Test suite for GKGReasoningService"""

    @pytest.fixture
    def service(self):
        """Fixture to create a GKGReasoningService instance"""
        return GKGReasoningService()

    def test_service_initialization(self, service):
        """Test that the service initializes correctly"""
        assert service is not None
        assert isinstance(service, GKGReasoningService)

    def test_gkg_rule_1_wetland_proximity(self, service):
        """Test GKG Rule 1: SDMH near wetland (y > 2050000)"""
        feature_code = "SDMH"
        coordinates = {'x': 6510000.0, 'y': 2060000.0}

        result = service.get_contextual_attributes(feature_code, coordinates)

        assert "ENVIRONMENTAL_REVIEW" in result
        assert result["ENVIRONMENTAL_REVIEW"] is True
        assert "REVIEW_TYPE" in result
        assert result["REVIEW_TYPE"] == "WETLAND_BUFFER"

    def test_gkg_rule_2_historic_zone(self, service):
        """Test GKG Rule 2: Feature in historic zone (x < 6520000)"""
        feature_code = "TEST"
        coordinates = {'x': 6510000.0, 'y': 2000000.0}

        result = service.get_contextual_attributes(feature_code, coordinates)

        assert "HISTORIC_DESIGNATION" in result
        assert result["HISTORIC_DESIGNATION"] == "ZONE_A"
        assert "DESIGN_REVIEW_REQUIRED" in result
        assert result["DESIGN_REVIEW_REQUIRED"] is True

    def test_gkg_rule_3_water_valve_pressure_zone(self, service):
        """Test GKG Rule 3: Water valve pressure zone"""
        feature_code = "WV"
        coordinates = {'x': 6600000.0, 'y': 2000000.0}

        result = service.get_contextual_attributes(feature_code, coordinates)

        assert "PRESSURE_ZONE" in result
        assert result["PRESSURE_ZONE"] == "HIGH_RES_ZONE_C"

    def test_multiple_rules_triggered(self, service):
        """Test scenario where multiple GKG rules are triggered simultaneously"""
        feature_code = "SDMH"
        coordinates = {'x': 6510000.0, 'y': 2060000.0}  # Triggers both Rule 1 and Rule 2

        result = service.get_contextual_attributes(feature_code, coordinates)

        # Should have wetland attributes from Rule 1
        assert "ENVIRONMENTAL_REVIEW" in result
        assert result["ENVIRONMENTAL_REVIEW"] is True
        assert "REVIEW_TYPE" in result

        # Should have historic zone attributes from Rule 2
        assert "HISTORIC_DESIGNATION" in result
        assert result["HISTORIC_DESIGNATION"] == "ZONE_A"
        assert "DESIGN_REVIEW_REQUIRED" in result

    def test_no_rules_triggered(self, service):
        """Test scenario where no GKG rules are triggered"""
        feature_code = "TEST"
        coordinates = {'x': 6600000.0, 'y': 2000000.0}  # Outside all rule boundaries

        result = service.get_contextual_attributes(feature_code, coordinates)

        assert result == {}

    def test_case_insensitive_feature_code(self, service):
        """Test that feature codes are case-insensitive"""
        # Test lowercase 'wv'
        result_lower = service.get_contextual_attributes("wv", {'x': 6600000.0, 'y': 2000000.0})
        assert "PRESSURE_ZONE" in result_lower

        # Test uppercase 'WV'
        result_upper = service.get_contextual_attributes("WV", {'x': 6600000.0, 'y': 2000000.0})
        assert "PRESSURE_ZONE" in result_upper

        # Both should return the same result
        assert result_lower == result_upper

    def test_missing_coordinate_keys(self, service):
        """Test handling of missing coordinate keys using default values"""
        feature_code = "TEST"

        # Missing 'x' key (defaults to 0, should trigger historic rule since 0 < 6520000)
        result_missing_x = service.get_contextual_attributes(feature_code, {'y': 2000000.0})
        assert "HISTORIC_DESIGNATION" in result_missing_x

        # Missing 'y' key (defaults to 0, should not trigger wetland rule since 0 < 2050000)
        result_missing_y = service.get_contextual_attributes("SDMH", {'x': 6510000.0})
        assert "ENVIRONMENTAL_REVIEW" not in result_missing_y

    def test_edge_case_boundary_values(self, service):
        """Test edge cases at rule boundaries"""
        # Exactly at wetland boundary (y = 2050000)
        result_at_boundary = service.get_contextual_attributes(
            "SDMH",
            {'x': 6510000.0, 'y': 2050000.0}
        )
        assert "ENVIRONMENTAL_REVIEW" not in result_at_boundary  # Should not trigger (needs y > 2050000)

        # Just above wetland boundary (y = 2050001)
        result_above_boundary = service.get_contextual_attributes(
            "SDMH",
            {'x': 6510000.0, 'y': 2050001.0}
        )
        assert "ENVIRONMENTAL_REVIEW" in result_above_boundary  # Should trigger

        # Exactly at historic boundary (x = 6520000)
        result_historic_boundary = service.get_contextual_attributes(
            "TEST",
            {'x': 6520000.0, 'y': 2000000.0}
        )
        assert "HISTORIC_DESIGNATION" not in result_historic_boundary  # Should not trigger (needs x < 6520000)

        # Just below historic boundary (x = 6519999)
        result_historic_below = service.get_contextual_attributes(
            "TEST",
            {'x': 6519999.0, 'y': 2000000.0}
        )
        assert "HISTORIC_DESIGNATION" in result_historic_below  # Should trigger
