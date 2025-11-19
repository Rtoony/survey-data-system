# tests/test_sheet_note_manager.py
import pytest
from services.sheet_note_manager import SheetNoteManager, MOCK_STANDARD_NOTES


class TestSheetNoteManager:
    """Test suite for SheetNoteManager"""

    @pytest.fixture
    def service(self):
        """Fixture to create a SheetNoteManager instance"""
        return SheetNoteManager()

    def test_service_initialization(self, service):
        """Test that the service initializes correctly"""
        assert service is not None
        assert isinstance(service, SheetNoteManager)
        assert service.notes == MOCK_STANDARD_NOTES
        assert len(service.notes) == 4

    def test_get_notes_by_single_tag_stormwater(self, service):
        """Test retrieving notes with a single tag: STORMWATER"""
        result = service.get_notes_by_requirement(["STORMWATER"])

        assert result["count"] == 2
        assert "SW_COMPLIANCE" in result["note_block"]
        assert "EROSION_CONTROL" in result["note_block"]
        assert "NPDES Permit" in result["note_block"]
        assert "Erosion and Sediment Control" in result["note_block"]

    def test_get_notes_by_single_tag_ada(self, service):
        """Test retrieving notes with a single tag: ADA"""
        result = service.get_notes_by_requirement(["ADA"])

        assert result["count"] == 1
        assert "ADA_RAMP_DESIGN" in result["note_block"]
        assert "Accessibility ramps" in result["note_block"]
        assert "CBC and ADA standards" in result["note_block"]

    def test_get_notes_by_single_tag_utility(self, service):
        """Test retrieving notes with a single tag: UTILITY"""
        result = service.get_notes_by_requirement(["UTILITY"])

        assert result["count"] == 1
        assert "UTILITY_TRENCHING" in result["note_block"]
        assert "Utility trenches" in result["note_block"]
        assert "ASTM D1557" in result["note_block"]

    def test_get_notes_by_multiple_tags(self, service):
        """Test retrieving notes with multiple tags"""
        result = service.get_notes_by_requirement(["STORMWATER", "ENVIRONMENTAL"])

        # Should match both SW_COMPLIANCE (STORMWATER) and EROSION_CONTROL (STORMWATER, ENVIRONMENTAL)
        assert result["count"] == 2
        assert "SW_COMPLIANCE" in result["note_block"]
        assert "EROSION_CONTROL" in result["note_block"]

    def test_get_notes_by_multiple_tags_civil_design(self, service):
        """Test retrieving notes with CIVIL_DESIGN tag"""
        result = service.get_notes_by_requirement(["CIVIL_DESIGN"])

        assert result["count"] == 1
        assert "ADA_RAMP_DESIGN" in result["note_block"]

    def test_get_notes_by_tag_compliance(self, service):
        """Test retrieving notes with COMPLIANCE tag"""
        result = service.get_notes_by_requirement(["COMPLIANCE"])

        assert result["count"] == 1
        assert "SW_COMPLIANCE" in result["note_block"]

    def test_get_notes_case_insensitive_tags(self, service):
        """Test that tag matching is case-insensitive"""
        result_upper = service.get_notes_by_requirement(["STORMWATER"])
        result_lower = service.get_notes_by_requirement(["stormwater"])
        result_mixed = service.get_notes_by_requirement(["StOrMwAtEr"])

        assert result_upper["count"] == result_lower["count"] == result_mixed["count"]
        assert result_upper["note_block"] == result_lower["note_block"] == result_mixed["note_block"]

    def test_get_notes_no_matching_tags(self, service):
        """Test retrieving notes when no tags match"""
        result = service.get_notes_by_requirement(["NONEXISTENT_TAG"])

        assert result["count"] == 0
        assert result["note_block"] == ""

    def test_get_notes_empty_tag_list(self, service):
        """Test retrieving notes with an empty tag list"""
        result = service.get_notes_by_requirement([])

        assert result["count"] == 0
        assert result["note_block"] == ""

    def test_get_notes_duplicate_tags(self, service):
        """Test that duplicate tags in the requirement list are handled correctly"""
        result = service.get_notes_by_requirement(["STORMWATER", "STORMWATER", "stormwater"])

        # Should still return 2 notes (SW_COMPLIANCE and EROSION_CONTROL)
        assert result["count"] == 2

    def test_get_notes_formatted_output(self, service):
        """Test that the note block is properly formatted with numbering"""
        result = service.get_notes_by_requirement(["UTILITY"])

        # Check formatting: numbered list with reference ID
        assert result["note_block"].startswith("1. ")
        assert "[Ref: UTILITY_TRENCHING]" in result["note_block"]

    def test_get_notes_multiple_results_formatted(self, service):
        """Test that multiple notes are properly numbered"""
        result = service.get_notes_by_requirement(["STORMWATER"])

        lines = result["note_block"].split("\n")
        assert len(lines) == 2
        assert lines[0].startswith("1. ")
        assert lines[1].startswith("2. ")

    def test_link_note_to_entity_success(self, service):
        """Test successfully linking a valid note to an entity"""
        result = service.link_note_to_entity("SW_COMPLIANCE", "SSM_FEATURE_001")

        assert result is True

    def test_link_note_to_entity_valid_note_ids(self, service):
        """Test linking all valid note IDs"""
        valid_note_ids = ["SW_COMPLIANCE", "ADA_RAMP_DESIGN", "UTILITY_TRENCHING", "EROSION_CONTROL"]

        for note_id in valid_note_ids:
            result = service.link_note_to_entity(note_id, f"ENTITY_{note_id}")
            assert result is True

    def test_link_note_to_entity_invalid_note_id(self, service):
        """Test linking a non-existent note ID returns False"""
        result = service.link_note_to_entity("NONEXISTENT_NOTE", "SSM_FEATURE_001")

        assert result is False

    def test_link_note_to_entity_empty_note_id(self, service):
        """Test linking with an empty note ID"""
        result = service.link_note_to_entity("", "SSM_FEATURE_001")

        assert result is False

    def test_link_note_to_entity_various_entity_ids(self, service):
        """Test that linking works with various entity ID formats"""
        entity_ids = [
            "SSM_FEATURE_001",
            "SSM_FEATURE_TOC_123",
            "SDMH_MAPPING_301",
            "12345",
            "entity_with_underscores_and_numbers_999"
        ]

        for entity_id in entity_ids:
            result = service.link_note_to_entity("SW_COMPLIANCE", entity_id)
            assert result is True

    def test_all_mock_notes_have_required_fields(self, service):
        """Test that all mock notes have the required 'text' and 'tags' fields"""
        for note_id, note_data in service.notes.items():
            assert "text" in note_data, f"Note {note_id} missing 'text' field"
            assert "tags" in note_data, f"Note {note_id} missing 'tags' field"
            assert isinstance(note_data["text"], str), f"Note {note_id} 'text' is not a string"
            assert isinstance(note_data["tags"], list), f"Note {note_id} 'tags' is not a list"
            assert len(note_data["text"]) > 0, f"Note {note_id} 'text' is empty"
            assert len(note_data["tags"]) > 0, f"Note {note_id} has no tags"

    def test_get_notes_tag_intersection_logic(self, service):
        """Test that notes are returned when ANY required tag matches (intersection logic)"""
        # EROSION_CONTROL has tags: ["STORMWATER", "ENVIRONMENTAL"]
        # Requesting ["ENVIRONMENTAL"] should match it
        result = service.get_notes_by_requirement(["ENVIRONMENTAL"])

        assert result["count"] == 1
        assert "EROSION_CONTROL" in result["note_block"]

    def test_get_notes_combined_tags_coverage(self, service):
        """Test retrieving notes with a combination that covers all notes"""
        result = service.get_notes_by_requirement([
            "STORMWATER",
            "ADA",
            "UTILITY",
            "CONSTRUCTION"
        ])

        # Should match all 4 notes
        assert result["count"] == 4
        assert "SW_COMPLIANCE" in result["note_block"]
        assert "ADA_RAMP_DESIGN" in result["note_block"]
        assert "UTILITY_TRENCHING" in result["note_block"]
        assert "EROSION_CONTROL" in result["note_block"]

    def test_get_notes_preserves_note_content(self, service):
        """Test that the full note text is preserved in the output"""
        result = service.get_notes_by_requirement(["COMPLIANCE"])

        expected_text = "All post-construction stormwater facilities shall be maintained per NPDES Permit requirements."
        assert expected_text in result["note_block"]

    def test_note_block_empty_when_no_matches(self, service):
        """Test that note_block is an empty string when count is 0"""
        result = service.get_notes_by_requirement(["INVALID_TAG"])

        assert result["count"] == 0
        assert result["note_block"] == ""
        assert isinstance(result["note_block"], str)
