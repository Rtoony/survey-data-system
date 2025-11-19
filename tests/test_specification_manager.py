"""
Tests for services/specification_manager.py
"""
import pytest
from typing import Dict, Any, Optional
from services.specification_manager import SpecificationManager, MOCK_SPECIFICATIONS


class TestSpecificationManager:
    """Test suite for SpecificationManager class."""

    @pytest.fixture
    def manager(self) -> SpecificationManager:
        """Fixture to create a fresh SpecificationManager instance."""
        return SpecificationManager()

    def test_initialization(self, manager: SpecificationManager) -> None:
        """Test that SpecificationManager initializes correctly."""
        assert manager.specs == MOCK_SPECIFICATIONS
        assert len(manager.specs) > 0

    def test_get_spec_requirements_valid_spec(self, manager: SpecificationManager) -> None:
        """Test retrieving requirements for a valid, active specification."""
        spec_number = "15400-DI"
        result = manager.get_spec_requirements(spec_number)

        assert result is not None
        assert result["title"] == "Ductile Iron Pipe Installation"
        assert result["active"] is True
        assert "PIPE_CLASS" in result["required_attributes"]
        assert "PRESSURE_RATING" in result["required_attributes"]
        assert "mapping_overrides" in result

    def test_get_spec_requirements_pvc_spec(self, manager: SpecificationManager) -> None:
        """Test retrieving requirements for PVC specification."""
        spec_number = "15401-PVC"
        result = manager.get_spec_requirements(spec_number)

        assert result is not None
        assert result["title"] == "PVC Pipe and Fittings"
        assert result["active"] is True
        assert "PIPE_CLASS" in result["required_attributes"]
        assert result["mapping_overrides"]["material_override"] == "PVC"

    def test_get_spec_requirements_nonexistent_spec(self, manager: SpecificationManager) -> None:
        """Test retrieving requirements for a non-existent specification."""
        spec_number = "9999-VOID"
        result = manager.get_spec_requirements(spec_number)

        assert result is None

    def test_get_spec_requirements_inactive_spec(self, manager: SpecificationManager) -> None:
        """Test retrieving requirements for an inactive specification."""
        # Add an inactive spec temporarily
        manager.specs["INACTIVE-TEST"] = {
            "title": "Inactive Test Spec",
            "active": False,
            "required_attributes": ["TEST_ATTR"]
        }

        result = manager.get_spec_requirements("INACTIVE-TEST")
        assert result is None

    def test_generate_spec_mapping_override_ductile_iron(self, manager: SpecificationManager) -> None:
        """Test generating mapping override for Ductile Iron specification."""
        spec_number = "15400-DI"
        result = manager.generate_spec_mapping_override(spec_number)

        assert result is not None
        assert result["id"] == "SPEC_15400-DI"
        assert result["feature_code"] == "WL"
        assert result["priority"] == 9500
        assert result["enforced_attribute"]["MATERIAL"] == "DUCTILE_IRON"
        assert result["layer"] == "SPEC-15400-DI-DUCTILE_IRON"
        assert result["block"] == "SPEC-15400-DI-DUCTILE_IRON-BLOCK"
        assert result["source"] == "SPECIFICATION_SECTION_15400-DI"

    def test_generate_spec_mapping_override_pvc(self, manager: SpecificationManager) -> None:
        """Test generating mapping override for PVC specification."""
        spec_number = "15401-PVC"
        result = manager.generate_spec_mapping_override(spec_number)

        assert result is not None
        assert result["id"] == "SPEC_15401-PVC"
        assert result["feature_code"] == "WL"
        assert result["priority"] == 9500
        assert result["enforced_attribute"]["MATERIAL"] == "PVC"
        assert result["layer"] == "SPEC-15401-PVC-PVC"
        assert result["block"] == "SPEC-15401-PVC-PVC-BLOCK"

    def test_generate_spec_mapping_override_conditions(self, manager: SpecificationManager) -> None:
        """Test that conditions are properly included in the mapping override."""
        spec_number = "15400-DI"
        result = manager.generate_spec_mapping_override(spec_number)

        assert result is not None
        assert "conditions" in result
        assert "SIZE" in result["conditions"]
        assert result["conditions"]["SIZE"]["operator"] == ">"
        assert result["conditions"]["SIZE"]["value"] == "12IN"

    def test_generate_spec_mapping_override_nonexistent(self, manager: SpecificationManager) -> None:
        """Test generating mapping override for non-existent specification."""
        spec_number = "9999-VOID"
        result = manager.generate_spec_mapping_override(spec_number)

        assert result is None

    def test_generate_spec_mapping_override_no_overrides(self, manager: SpecificationManager) -> None:
        """Test generating mapping override for spec without mapping_overrides."""
        # Add a spec without mapping_overrides
        manager.specs["NO-OVERRIDE"] = {
            "title": "No Override Spec",
            "active": True,
            "required_attributes": ["TEST_ATTR"]
        }

        result = manager.generate_spec_mapping_override("NO-OVERRIDE")
        assert result is None

    def test_mock_specifications_structure(self) -> None:
        """Test that MOCK_SPECIFICATIONS has the expected structure."""
        assert "15400-DI" in MOCK_SPECIFICATIONS
        assert "15401-PVC" in MOCK_SPECIFICATIONS

        for spec_key, spec_data in MOCK_SPECIFICATIONS.items():
            assert "title" in spec_data
            assert "active" in spec_data
            assert "required_attributes" in spec_data
            assert isinstance(spec_data["required_attributes"], list)

            if "mapping_overrides" in spec_data:
                overrides = spec_data["mapping_overrides"]
                assert "feature_code" in overrides
                assert "conditions" in overrides
                assert "material_override" in overrides
                assert "priority_boost" in overrides

    def test_mapping_override_priority_level(self, manager: SpecificationManager) -> None:
        """Test that mapping overrides have correct priority level (9500)."""
        for spec_number in ["15400-DI", "15401-PVC"]:
            result = manager.generate_spec_mapping_override(spec_number)
            assert result is not None
            assert result["priority"] == 9500, f"Priority should be 9500 for {spec_number}"

    def test_enforced_attribute_structure(self, manager: SpecificationManager) -> None:
        """Test that enforced_attribute is properly structured in the override."""
        spec_number = "15400-DI"
        result = manager.generate_spec_mapping_override(spec_number)

        assert result is not None
        assert "enforced_attribute" in result
        assert isinstance(result["enforced_attribute"], dict)
        assert "MATERIAL" in result["enforced_attribute"]
