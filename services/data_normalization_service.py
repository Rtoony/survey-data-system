# services/data_normalization_service.py
from typing import Dict, Any
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataNormalizationService:
    """
    Cleans, standardizes, and performs derived calculations on raw survey attributes
    to prepare them for the conditional mapping engine.
    """

    # Mock lookup for common standardization and conversions
    STANDARD_LOOKUP = {
        "CONC": "CONCRETE",
        "PVC": "PVC",
        "BRICK": "BRICK",
        "STEEL": "STEEL",
        "DI": "DUCTILE_IRON",
        "CI": "CAST_IRON"
    }

    # Attributes that should be aggressively converted to uppercase strings for matching
    STRING_MATCH_KEYS = ["MATERIAL", "TYPE", "OWNER", "JURISDICTION"]

    def __init__(self):
        logger.info("DataNormalizationService initialized.")

    def _clean_text_attributes(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """Performs standardization and case conversion on specific string attributes."""

        for key in self.STRING_MATCH_KEYS:
            if key in attributes and isinstance(attributes[key], str):
                raw_value = attributes[key].strip().upper()

                # Check for common typos/abbreviations
                attributes[key] = self.STANDARD_LOOKUP.get(raw_value, raw_value)

        return attributes

    def _calculate_derived_attributes(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates secondary attributes like DEPTH, SLOPE, etc., and adds them to the dictionary."""

        # Calculation 1: Manhole/Inlet Depth
        rim = attributes.get('RIM_ELEV')
        invert = attributes.get('INVERT_ELEV')

        # Ensure values are float/numeric for calculation
        try:
            float_rim = float(rim)
            float_invert = float(invert)

            # Derived Calculation: Depth
            depth = round(float_rim - float_invert, 2)
            attributes['DEPTH'] = depth
            logger.info(f"Derived DEPTH calculated: {depth} (RIM: {rim} - INV: {invert})")

        except (ValueError, TypeError):
            # One or both values are missing or not numeric; calculation skipped
            pass

        # NOTE: Future logic would include unit conversion and slope calculation here.

        return attributes

    def normalize_attributes(self, raw_attributes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs the full pipeline to clean, convert, and calculate attributes.
        """
        logger.info("Starting attribute normalization and derived calculation.")

        # Deep copy to ensure raw_attributes remain untouched if needed
        clean_attributes = raw_attributes.copy()

        # Step 1: Clean and standardize text
        clean_attributes = self._clean_text_attributes(clean_attributes)

        # Step 2: Calculate derived attributes
        clean_attributes = self._calculate_derived_attributes(clean_attributes)

        logger.info("Normalization complete.")
        return clean_attributes


# --- Example Execution (for testing the service) ---
if __name__ == '__main__':
    service = DataNormalizationService()

    print("\n--- TEST CASE 1: Raw SDMH Data (Needs Text Cleanup and Depth Calculation) ---")
    raw_data_1 = {
        "SIZE": 48.0,
        "RIM_ELEV": 105.50,
        "INVERT_ELEV": 99.25,
        "MATERIAL": "conc",  # Lowercase typo
        "JURISDICTION": "santa rosa " # Trailing space
    }

    normalized_1 = service.normalize_attributes(raw_data_1)
    print(f"Original Material: '{raw_data_1['MATERIAL']}'")
    print(f"Normalized Material: '{normalized_1['MATERIAL']}'")
    print(f"Derived DEPTH: {normalized_1.get('DEPTH')}")
    print(f"Normalized Jurisdiction: '{normalized_1.get('JURISDICTION')}'")

    print("\n--- TEST CASE 2: Missing Data (Calculation Skipped) ---")
    raw_data_2 = {
        "SIZE": 36.0,
        "RIM_ELEV": 102.0,
        "INVERT_ELEV": "N/A", # Non-numeric invert
        "MATERIAL": "pv c",
    }
    normalized_2 = service.normalize_attributes(raw_data_2)
    print(f"Normalized Material: '{normalized_2['MATERIAL']}'")
    print(f"Derived DEPTH Present: {'DEPTH' in normalized_2}")
