# tools/field_data_import_wizard.py
# Phase 26: Field Data Import Wizard
# Orchestrates the ingestion of raw field data files (CSV/TXT), applying
# normalization and validation before staging data for database commit.

from typing import Dict, Any, List
import logging
import csv
from io import StringIO
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Mocked Dependency (Phase 25) ---
class MockDataNormalizationService:
    """
    Mock service for data normalization to ensure stability.
    Simulates data cleanup and calculation (e.g., adding DEPTH).
    """
    def normalize_attributes(self, raw_attributes: Dict[str, Any]) -> Dict[str, Any]:
        """Simulates data cleanup and calculation (e.g., adding DEPTH)."""
        normalized = raw_attributes.copy()

        # Simple mock cleanup - handle both 'Material' and 'MATERIAL' keys
        material = normalized.get('Material', normalized.get('MATERIAL', 'Unknown'))
        normalized['Material'] = material.upper() if isinstance(material, str) else str(material).upper()

        # Mock error simulation for required field check
        # Check both key existence and value (empty strings should fail)
        elevation = normalized.get('Elevation', normalized.get('ELEVATION'))
        if not elevation or (isinstance(elevation, str) and elevation.strip() == ''):
            raise ValueError("Normalization Error: Required field 'ELEVATION' missing or empty.")

        return normalized

# --- Mock File Content ---
MOCK_FILE_CONTENT = """
PointID,Code,Elevation,Material
101,SDMH,102.50,conc
102,WV,98.15,di
103,TOC,105.00,asphalt
104,SDMH,,pvc
"""

# --- Main Import Service ---

class FieldDataImportWizard:
    """
    Orchestrates the ingestion of raw field data files (CSV/TXT), applying
    normalization and validation before staging data for database commit.
    """

    def __init__(self):
        self.normalizer = MockDataNormalizationService()
        logger.info("FieldDataImportWizard initialized. Ready to parse and clean.")

    def _parse_file_content(self, file_content_str: str, import_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Mocks reading the CSV/TXT content into dictionaries."""

        # Use StringIO to treat the string as a file
        data_io = StringIO(file_content_str.strip())

        # Assuming the first row is the header
        reader = csv.DictReader(data_io, skipinitialspace=True)

        return list(reader)

    def parse_and_normalize_file(self, file_content_str: str, import_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs the full ingestion pipeline: Parse -> Normalize -> Validate.

        Args:
            file_content_str: Raw CSV/TXT content as a string
            import_config: Configuration dict with settings like SRID, delimiter, etc.

        Returns:
            Dictionary containing:
                - success_count: Number of successfully normalized points
                - error_count: Number of points that failed normalization
                - normalized_data_staging: List of clean, ready-to-load data points
                - import_error_report: List of error details for failed points
        """
        logger.info("Starting file parsing and normalization pipeline.")

        raw_data_points = self._parse_file_content(file_content_str, import_config)

        normalized_data = []
        error_report = []

        for i, raw_point in enumerate(raw_data_points):
            point_id = raw_point.get('PointID', f"ROW_{i+1}")
            try:
                # 1. Normalize and Calculate (Phase 25 Integration)
                clean_point = self.normalizer.normalize_attributes(raw_point)

                # 2. Additional validation checks can happen here (e.g., data type constraints)

                normalized_data.append(clean_point)
                logger.debug(f"Point {point_id} successfully normalized.")

            except ValueError as e:
                # Capture normalization failures (e.g., missing required fields)
                error_report.append({
                    "id": point_id,
                    "status": "FAILED",
                    "reason": str(e),
                    "raw_data": raw_point
                })
                logger.warning(f"Point {point_id} failed normalization: {e}")

            except Exception as e:
                # Catch unexpected parsing/processing errors
                error_report.append({
                    "id": point_id,
                    "status": "ERROR",
                    "reason": f"Unexpected error: {e}"
                })

        logger.info(f"Pipeline complete. Success: {len(normalized_data)}, Errors: {len(error_report)}")

        return {
            "success_count": len(normalized_data),
            "error_count": len(error_report),
            "normalized_data_staging": normalized_data,
            "import_error_report": error_report
        }

# --- Example Execution ---
if __name__ == '__main__':
    service = FieldDataImportWizard()

    # Mock Import Configuration (e.g., Column mappings, SRID)
    mock_config = {"srid": 2227, "delimiter": ","}

    results = service.parse_and_normalize_file(MOCK_FILE_CONTENT, mock_config)

    print("\n--- IMPORT WIZARD REPORT ---")
    print(f"Total Successes: {results['success_count']}")
    print(f"Total Errors: {results['error_count']}")
    print("\nError Report (if any):")
    print(json.dumps(results['import_error_report'], indent=4))

    # Show the clean data ready for staging
    print("\nStaged Data Preview:")
    for point in results['normalized_data_staging']:
        print(f"  > ID {point['PointID']}: Code={point['Code']}, Mat={point['Material']}")
