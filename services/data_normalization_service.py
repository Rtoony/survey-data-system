# services/data_normalization_service.py (Refactored for Omega 4)
from typing import Dict, Any, List
from sqlalchemy.sql import select
from database import get_db, execute_query
from data.ssm_schema import ssm_standards_lookup
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataNormalizationService:
    """
    Cleans, standardizes, and performs derived calculations on raw survey attributes.
    Now uses live database tables for standardization lookups.
    """

    # Attributes that should be aggressively converted to uppercase strings for matching
    STRING_MATCH_KEYS = ["MATERIAL", "TYPE", "OWNER", "JURISDICTION"]

    def __init__(self):
        # Placeholder dictionary for the Standardization Tables
        self.standard_lookup: Dict[str, str] = {}
        self.__load_lookup_tables()
        logger.info("DataNormalizationService initialized. Lookups loaded via centralized DB.")

    def __load_lookup_tables(self):
        """
        Refactored: Loads the standardization dictionary from a live database table
        (ssm_standards_lookup) during service initialization.
        """
        try:
            # Query the database for standardization lookups
            with get_db() as conn:
                logger.info("Loading standardization lookups from ssm.ssm_standards_lookup.")
                query = select(
                    ssm_standards_lookup.c.raw_value,
                    ssm_standards_lookup.c.standardized_value
                )
                result = conn.execute(query)
                rows = result.fetchall()

                # Build the lookup dictionary from database results
                for row in rows:
                    raw_value = row.raw_value.strip().upper()
                    standardized_value = row.standardized_value.strip().upper()
                    self.standard_lookup[raw_value] = standardized_value

                logger.info(f"Loaded {len(self.standard_lookup)} standardization lookups from database.")

        except Exception as e:
            logger.warning(f"Could not load standardization lookups from DB: {e}")
            logger.warning("Falling back to minimal hardcoded lookup table.")
            # Ensure the service can still function with a minimal/empty lookup if DB fails
            # MOCK DATA REMAINS until live DB integration is finalized
            self.standard_lookup = {
                "CONC": "CONCRETE",
                "PVC": "PVC",
                "BRICK": "BRICK",
                "STEEL": "STEEL",
                "DI": "DUCTILE_IRON",
                "CI": "CAST_IRON"
            }

    def _clean_text_attributes(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """Performs standardization and case conversion on specific string attributes."""

        for key in self.STRING_MATCH_KEYS:
            if key in attributes and isinstance(attributes[key], str):
                raw_value = attributes[key].strip().upper()

                # Use the live-loaded lookup table
                attributes[key] = self.standard_lookup.get(raw_value, raw_value)

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
