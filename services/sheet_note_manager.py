# services/sheet_note_manager.py
from typing import Dict, Any, List, Optional
import logging
import json
import uuid

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Mock Data Storage ---
MOCK_STANDARD_NOTES = {
    "SW_COMPLIANCE": {
        "text": "All post-construction stormwater facilities shall be maintained per NPDES Permit requirements.",
        "tags": ["STORMWATER", "COMPLIANCE"]
    },
    "ADA_RAMP_DESIGN": {
        "text": "Accessibility ramps shall comply with current CBC and ADA standards, including slope, landing, and railing specifications.",
        "tags": ["ADA", "CIVIL_DESIGN"]
    },
    "UTILITY_TRENCHING": {
        "text": "Utility trenches shall be backfilled and compacted to 95% relative density per ASTM D1557.",
        "tags": ["UTILITY", "CONSTRUCTION"]
    },
    "EROSION_CONTROL": {
        "text": "Erosion and Sediment Control measures shall be implemented prior to and maintained during all phases of construction.",
        "tags": ["STORMWATER", "ENVIRONMENTAL"]
    }
}

# --- Main Service ---

class SheetNoteManager:
    """
    Manages the library of standard engineering and compliance notes,
    linking them to project requirements and specific SSM entities.
    """

    def __init__(self):
        self.notes = MOCK_STANDARD_NOTES
        logger.info("SheetNoteManager initialized with standard compliance notes.")

    def get_notes_by_requirement(self, requirement_tags: List[str]) -> Dict[str, Any]:
        """
        Retrieves notes matching a list of required tags and returns them as a formatted block.
        """
        matching_notes = []
        unique_tags = {tag.upper() for tag in requirement_tags}

        for note_id, note_data in self.notes.items():
            # Check if any of the required tags overlap with the note's tags
            note_tags_upper = {t.upper() for t in note_data.get("tags", [])}

            if note_tags_upper.intersection(unique_tags):
                matching_notes.append({
                    "id": note_id,
                    "text": note_data["text"]
                })

        # Format the output into a numbered list
        formatted_notes = []
        for i, note in enumerate(matching_notes):
            formatted_notes.append(f"{i+1}. {note['text']} [Ref: {note['id']}]")

        logger.info(f"Retrieved {len(matching_notes)} notes matching requirements: {unique_tags}.")

        return {
            "count": len(matching_notes),
            "note_block": "\n".join(formatted_notes)
        }

    def link_note_to_entity(self, note_id: str, entity_id: str) -> bool:
        """
        Mocks the action of creating a relational link in the database
        (e.g., between the SW_COMPLIANCE note and SDMH Mapping ID 301).
        """
        if note_id not in self.notes:
            logger.warning(f"Link failed: Note ID '{note_id}' not found.")
            return False

        # In a real system, this would be an INSERT into a note_entity_links table.
        logger.info(f"MOCK LINK SUCCESS: Note '{note_id}' successfully linked to SSM Entity ID {entity_id}.")
        return True

# --- Example Execution ---
if __name__ == '__main__':
    service = SheetNoteManager()

    # TEST 1: Retrieve notes for stormwater compliance
    print("\n--- TEST CASE 1: Stormwater Compliance Notes ---")
    results_sw = service.get_notes_by_requirement(["STORMWATER", "ENVIRONMENTAL"])
    print(f"Notes Found: {results_sw['count']}")
    print("\n--- Compliance Note Block ---")
    print(results_sw['note_block'])

    # TEST 2: Link a note to a specific feature (Mocking success)
    print("\n--- TEST CASE 2: Linking Note to Entity ---")
    link_success = service.link_note_to_entity("ADA_RAMP_DESIGN", "SSM_FEATURE_TOC_123")
    print(f"Link Status: {link_success}")
