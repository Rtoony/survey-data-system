"""
Unit tests for SSM Mapping Service (GKGSyncService)
Tests priority-based mapping resolution with deterministic tie-breaking using condition count (specificity).
"""

import unittest
import logging
from unittest.mock import MagicMock, patch
from services.ssm_mapping_service import GKGSyncService, MockGraphClient

# Mocked attributes for testing
TEST_ATTRIBUTES = {
    "SIZE": "60IN",
    "MAT": "PRECAST",
    "OTHER_ATTR": 100
}

# The service uses MOCK_STANDARDS_MAPPINGS internally, which includes:
# ID 301: P300, 2 conditions (Expected Winner in tie-breaker scenario)
# ID 302: P300, 1 condition (Tie-breaker Loser)
# ID 201: P200, 1 condition
# ID 101: P100, 0 conditions (Default fallback)


class TestMappingResolution(unittest.TestCase):
    """Test suite for SSM mapping resolution logic."""

    def setUp(self):
        """Initialize the service with a mocked database engine."""
        # Mock create_engine to avoid database connection issues
        with patch('services.ssm_mapping_service.create_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine
            self.service = GKGSyncService("postgresql://test:test@localhost:5432/testdb")

        # Mock the connection method to avoid actual DB access
        self.service._get_connection = MagicMock()

    def test_highest_priority_wins(self):
        """
        Test Case 1: Highest priority wins when there is a clear priority difference.
        Expected: ID 301 (P300, 2 conditions) should win over ID 201 (P200, 1 condition).
        """
        result = self.service.resolve_mapping("SDMH", TEST_ATTRIBUTES)
        self.assertIsNotNone(result)
        self.assertEqual(result['source_mapping_id'], 301)
        self.assertEqual(result['layer'], 'B')  # P300, 2 conditions

    def test_tie_breaker_specificity_wins(self):
        """
        Test Case 2 (CRITICAL): Priority is equal (301 vs 302), specificity determines the winner.
        Expected: ID 301 (P300, 2 conditions) should beat ID 302 (P300, 1 condition).
        Verification: Check that "Tie-breaker SUCCESS" was logged.
        """
        # Enable logging for this test
        logging.disable(logging.NOTSET)

        with self.assertLogs('services.ssm_mapping_service', level='INFO') as cm:
            result = self.service.resolve_mapping("SDMH", TEST_ATTRIBUTES)

        self.assertIsNotNone(result)
        self.assertEqual(result['source_mapping_id'], 301)
        self.assertEqual(result['layer'], 'B')

        # Verify the Tie-breaker success was logged
        self.assertTrue(
            any("Tie-breaker SUCCESS" in log for log in cm.output),
            "Expected 'Tie-breaker SUCCESS' log message not found"
        )

    def test_severe_conflict_logging(self):
        """
        Test Case 3: Verify SEVERE CONFLICT warning when two mappings have identical
        Priority AND Specificity (nondeterministic selection).
        """
        # Enable logging for this test
        logging.disable(logging.NOTSET)

        # Create a mock map list with a true conflict for the test
        conflict_list = [
            {
                "id": 500,
                "feature_code": "SDMH",
                "conditions": {"A": 1, "B": 2},
                "priority": 500,
                "layer": "Conflict1"
            },  # 2 conditions
            {
                "id": 501,
                "feature_code": "SDMH",
                "conditions": {"C": 3, "D": 4},
                "priority": 500,
                "layer": "Conflict2"
            }   # 2 conditions (CONFLICT)
        ]
        self.service.MOCK_STANDARDS_MAPPINGS = conflict_list

        with self.assertLogs('services.ssm_mapping_service', level='WARNING') as cm:
            result = self.service.resolve_mapping("SDMH", TEST_ATTRIBUTES)

        # Verify a Severe Conflict warning was logged
        self.assertTrue(
            any("SEVERE CONFLICT" in log for log in cm.output),
            "Expected 'SEVERE CONFLICT' warning not found"
        )
        # The system still returns a result, but it's nondeterministic (arbitrary max() selection)
        self.assertIn(result['source_mapping_id'], [500, 501])

    def test_no_match(self):
        """
        Test Case 4: Verify None is returned when no mappings match the feature code.
        """
        result = self.service.resolve_mapping("WV", TEST_ATTRIBUTES)
        self.assertIsNone(result)

    def test_default_mapping_fallback(self):
        """
        Test Case 5: Verify P100 (0 conditions) wins if it's the only match.
        This tests that mappings with no conditions (defaults) work correctly.
        """
        # Create a mock map list with only a default mapping
        fallback_list = [
            {
                "id": 101,
                "feature_code": "SDMH",
                "conditions": {},
                "priority": 100,
                "layer": "D"
            },  # Default (0 conditions)
        ]
        self.service.MOCK_STANDARDS_MAPPINGS = fallback_list

        result = self.service.resolve_mapping("SDMH", TEST_ATTRIBUTES)
        self.assertIsNotNone(result)
        self.assertEqual(result['source_mapping_id'], 101)
        self.assertEqual(result['layer'], 'D')

    def test_multiple_priorities_correct_order(self):
        """
        Test Case 6: Verify that when multiple priorities exist, the highest wins.
        Setup: P400 > P300 > P200 > P100
        Expected: P400 mapping should win.
        """
        multi_priority_list = [
            {"id": 1, "feature_code": "SDMH", "conditions": {}, "priority": 100, "layer": "L1"},
            {"id": 2, "feature_code": "SDMH", "conditions": {}, "priority": 200, "layer": "L2"},
            {"id": 3, "feature_code": "SDMH", "conditions": {}, "priority": 400, "layer": "L4"},
            {"id": 4, "feature_code": "SDMH", "conditions": {}, "priority": 300, "layer": "L3"},
        ]
        self.service.MOCK_STANDARDS_MAPPINGS = multi_priority_list

        result = self.service.resolve_mapping("SDMH", TEST_ATTRIBUTES)
        self.assertIsNotNone(result)
        self.assertEqual(result['source_mapping_id'], 3)
        self.assertEqual(result['layer'], 'L4')

    def test_result_structure(self):
        """
        Test Case 7: Verify the returned mapping has the expected structure.
        """
        result = self.service.resolve_mapping("SDMH", TEST_ATTRIBUTES)
        self.assertIsNotNone(result)

        # Verify all required fields are present
        self.assertIn('layer', result)
        self.assertIn('block', result)
        self.assertIn('label_style', result)
        self.assertIn('automation_rules', result)
        self.assertIn('source_mapping_id', result)

        # Verify default values
        self.assertEqual(result['label_style'], 'LABEL-UTILITY')
        self.assertEqual(result['automation_rules'], ['Auto-label', 'Validate'])


class TestMappingServiceInitialization(unittest.TestCase):
    """Test suite for service initialization and configuration."""

    @patch('services.ssm_mapping_service.create_engine')
    def test_service_initialization(self, mock_create_engine):
        """Verify service initializes correctly with database URL."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        service = GKGSyncService("postgresql://test:test@localhost:5432/testdb")
        self.assertIsNotNone(service.engine)
        self.assertIsNotNone(service.graph_client)
        self.assertIsInstance(service.graph_client, MockGraphClient)

    @patch('services.ssm_mapping_service.create_engine')
    def test_mock_data_structure(self, mock_create_engine):
        """Verify the mock standards mappings have the expected structure."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        service = GKGSyncService("postgresql://test:test@localhost:5432/testdb")
        self.assertIsInstance(service.MOCK_STANDARDS_MAPPINGS, list)
        self.assertGreater(len(service.MOCK_STANDARDS_MAPPINGS), 0)

        # Verify each mapping has required fields
        for mapping in service.MOCK_STANDARDS_MAPPINGS:
            self.assertIn('id', mapping)
            self.assertIn('feature_code', mapping)
            self.assertIn('conditions', mapping)
            self.assertIn('priority', mapping)
            self.assertIn('layer', mapping)


if __name__ == '__main__':
    unittest.main()
