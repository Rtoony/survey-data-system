# tests/unit/tools/test_field_data_import_wizard.py
import sys
import os
import unittest

# Add project root to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from tools.field_data_import_wizard import FieldDataImportWizard, MOCK_FILE_CONTENT


class TestImportWizard(unittest.TestCase):
    def setUp(self):
        """Initialize the service before each test."""
        self.wizard = FieldDataImportWizard()

    def test_successful_parsing_and_normalization(self):
        """Verify success count and check for clean data structure."""
        # Modify MOCK_FILE_CONTENT to remove the known error case (row 104) for clean test
        # We ensure the data for the valid rows (101, 102, 103) is used
        clean_content = "\n".join(MOCK_FILE_CONTENT.strip().split('\n')[:-1])

        results = self.wizard.parse_and_normalize_file(clean_content, {})

        # Expect 3 successful points and 0 errors
        self.assertEqual(results['success_count'], 3)
        self.assertEqual(results['error_count'], 0)
        self.assertEqual(len(results['normalized_data_staging']), 3)

        # Verify normalization applied (e.g., material is uppercase)
        self.assertEqual(results['normalized_data_staging'][0]['Material'], 'CONC')

    def test_normalization_error_handling(self):
        """Verify error count increases and specific error message is logged/returned when a row fails normalization."""
        # Test case with the error row (ID 104 is missing elevation)
        results = self.wizard.parse_and_normalize_file(MOCK_FILE_CONTENT, {})

        # Expect 3 successful points and 1 error (due to row 104)
        self.assertEqual(results['success_count'], 3)
        self.assertEqual(results['error_count'], 1)

        # Verify the error report structure and message content
        self.assertEqual(results['import_error_report'][0]['id'], '104')
        self.assertIn('Required field', results['import_error_report'][0]['reason'])

    def test_empty_file_handling(self):
        """Verify success and error counts are zero for empty input."""
        empty_content = ""
        results = self.wizard.parse_and_normalize_file(empty_content, {})
        self.assertEqual(results['success_count'], 0)
        self.assertEqual(results['error_count'], 0)

    def test_material_uppercase_cleanup(self):
        """Verify normalization correctly applies uppercase (e.g., 'conc' -> 'CONC')."""
        # Test a direct row to ensure material is uppercased by the mock normalization
        test_content = "PointID,Code,Elevation,Material\n900,SDMH,100.00,asphalt"
        results = self.wizard.parse_and_normalize_file(test_content, {})

        # The mock normalization service must return 'ASPHALT'
        self.assertEqual(results['normalized_data_staging'][0]['Material'], 'ASPHALT')


if __name__ == '__main__':
    unittest.main()
