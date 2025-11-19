"""
Unit tests for DataQualityScorecardService

Tests quality metric calculations including:
- Completeness scoring
- Missing elevation detection
- Quality status thresholds
- Edge case handling
"""

import unittest
import logging
from unittest.mock import patch
from services.data_quality_scorecard import DataQualityScorecardService


class TestDataQualityScorecardService(unittest.TestCase):
    """Test suite for DataQualityScorecardService quality metric calculations."""

    def setUp(self):
        """Initialize the service before each test."""
        self.service = DataQualityScorecardService()

    def test_service_initialization(self):
        """Test that the service initializes correctly."""
        self.assertIsNotNone(self.service)
        self.assertIsInstance(self.service, DataQualityScorecardService)

    def test_generate_scorecard_with_all_complete_points(self):
        """Test scorecard generation when all points are complete."""
        raw_data = [
            {"PointID": 1, "ELEVATION": 100.0, "MATERIAL": "CONC", "SIZE": 48},
            {"PointID": 2, "ELEVATION": 101.0, "MATERIAL": "PVC", "SIZE": 36},
            {"PointID": 3, "ELEVATION": 102.0, "MATERIAL": "STEEL", "SIZE": 24},
        ]
        required_fields = ["ELEVATION", "MATERIAL", "SIZE"]

        scorecard = self.service.generate_scorecard(raw_data, required_fields)

        # Verify completeness
        self.assertEqual(scorecard["Total_Points_Analyzed"], 3)
        self.assertEqual(scorecard["Completeness_Count"], 3)
        self.assertEqual(scorecard["Completeness_Score_Pct"], 100.0)
        self.assertEqual(scorecard["Missing_Elevation_Count"], 0)
        self.assertEqual(scorecard["Quality_Status"], "PASS")
        self.assertEqual(scorecard["Required_Fields_Tested"], required_fields)

    def test_generate_scorecard_with_partially_complete_points(self):
        """Test scorecard generation with a mix of complete and incomplete points."""
        raw_data = [
            {"PointID": 101, "ELEVATION": 100.0, "MATERIAL": "CONC", "SIZE": 48},
            {"PointID": 102, "ELEVATION": 101.0, "SIZE": 36},  # Missing MATERIAL
            {"PointID": 103, "MATERIAL": "PVC", "SIZE": 24},  # Missing ELEVATION
        ]
        required_fields = ["ELEVATION", "MATERIAL", "SIZE"]

        scorecard = self.service.generate_scorecard(raw_data, required_fields)

        # Verify metrics
        self.assertEqual(scorecard["Total_Points_Analyzed"], 3)
        self.assertEqual(scorecard["Completeness_Count"], 1)
        self.assertEqual(scorecard["Completeness_Score_Pct"], 33.33)
        self.assertEqual(scorecard["Missing_Elevation_Count"], 1)  # Point 103
        self.assertEqual(scorecard["Quality_Status"], "FLAGGED")

    def test_generate_scorecard_with_no_complete_points(self):
        """Test scorecard generation when no points are complete."""
        raw_data = [
            {"PointID": 1, "ELEVATION": 100.0},  # Missing MATERIAL, SIZE
            {"PointID": 2, "MATERIAL": "PVC"},  # Missing ELEVATION, SIZE
            {"PointID": 3, "SIZE": 48},  # Missing ELEVATION, MATERIAL
        ]
        required_fields = ["ELEVATION", "MATERIAL", "SIZE"]

        scorecard = self.service.generate_scorecard(raw_data, required_fields)

        # Verify zero completeness
        self.assertEqual(scorecard["Total_Points_Analyzed"], 3)
        self.assertEqual(scorecard["Completeness_Count"], 0)
        self.assertEqual(scorecard["Completeness_Score_Pct"], 0.0)
        self.assertEqual(scorecard["Missing_Elevation_Count"], 2)  # Points 2 and 3
        self.assertEqual(scorecard["Quality_Status"], "FLAGGED")

    def test_generate_scorecard_with_empty_data_list(self):
        """Test scorecard generation with an empty data list."""
        raw_data = []
        required_fields = ["ELEVATION", "MATERIAL", "SIZE"]

        scorecard = self.service.generate_scorecard(raw_data, required_fields)

        # Verify early return with informative message
        self.assertEqual(scorecard["status"], "SUCCESS")
        self.assertEqual(scorecard["message"], "No data points analyzed.")
        self.assertEqual(scorecard["Total_Points_Analyzed"], 0)

    def test_generate_scorecard_with_none_values(self):
        """Test scorecard handles None values as missing data."""
        raw_data = [
            {"PointID": 1, "ELEVATION": None, "MATERIAL": "CONC", "SIZE": 48},
            {"PointID": 2, "ELEVATION": 100.0, "MATERIAL": None, "SIZE": 36},
            {"PointID": 3, "ELEVATION": 101.0, "MATERIAL": "PVC", "SIZE": None},
        ]
        required_fields = ["ELEVATION", "MATERIAL", "SIZE"]

        scorecard = self.service.generate_scorecard(raw_data, required_fields)

        # All points have at least one None value, so none are complete
        self.assertEqual(scorecard["Total_Points_Analyzed"], 3)
        self.assertEqual(scorecard["Completeness_Count"], 0)
        self.assertEqual(scorecard["Completeness_Score_Pct"], 0.0)
        self.assertEqual(scorecard["Missing_Elevation_Count"], 1)  # Point 1
        self.assertEqual(scorecard["Quality_Status"], "FLAGGED")

    def test_generate_scorecard_with_empty_string_values(self):
        """Test scorecard handles empty strings as missing data."""
        raw_data = [
            {"PointID": 1, "ELEVATION": "", "MATERIAL": "CONC", "SIZE": 48},
            {"PointID": 2, "ELEVATION": 100.0, "MATERIAL": "", "SIZE": 36},
            {"PointID": 3, "ELEVATION": 101.0, "MATERIAL": "PVC", "SIZE": ""},
        ]
        required_fields = ["ELEVATION", "MATERIAL", "SIZE"]

        scorecard = self.service.generate_scorecard(raw_data, required_fields)

        # All points have at least one empty string, so none are complete
        self.assertEqual(scorecard["Total_Points_Analyzed"], 3)
        self.assertEqual(scorecard["Completeness_Count"], 0)
        self.assertEqual(scorecard["Completeness_Score_Pct"], 0.0)
        self.assertEqual(scorecard["Missing_Elevation_Count"], 1)  # Point 1
        self.assertEqual(scorecard["Quality_Status"], "FLAGGED")

    def test_generate_scorecard_missing_elevation_count_specific(self):
        """Test that Missing_Elevation_Count correctly counts only elevation missing."""
        raw_data = [
            {"PointID": 1, "ELEVATION": 100.0, "MATERIAL": "CONC"},  # Has elevation
            {"PointID": 2, "MATERIAL": "PVC"},  # Missing elevation
            {"PointID": 3, "ELEVATION": None, "MATERIAL": "STEEL"},  # Elevation is None
            {"PointID": 4, "ELEVATION": "", "MATERIAL": "CONC"},  # Elevation is empty
            {"PointID": 5, "ELEVATION": 102.0, "MATERIAL": "PVC"},  # Has elevation
        ]
        required_fields = ["ELEVATION", "MATERIAL"]

        scorecard = self.service.generate_scorecard(raw_data, required_fields)

        # Points 2, 3, 4 are missing elevation
        self.assertEqual(scorecard["Missing_Elevation_Count"], 3)

    def test_generate_scorecard_quality_status_pass_threshold(self):
        """Test Quality_Status is PASS when completeness > 95%."""
        # Create 100 points, 96 complete (96% completeness)
        raw_data = [
            {"PointID": i, "ELEVATION": 100.0 + i, "MATERIAL": "CONC", "SIZE": 48}
            for i in range(96)
        ]
        # Add 4 incomplete points (missing SIZE)
        raw_data.extend([
            {"PointID": i, "ELEVATION": 200.0 + i, "MATERIAL": "PVC"}
            for i in range(4)
        ])
        required_fields = ["ELEVATION", "MATERIAL", "SIZE"]

        scorecard = self.service.generate_scorecard(raw_data, required_fields)

        # 96/100 = 96% > 95%
        self.assertEqual(scorecard["Total_Points_Analyzed"], 100)
        self.assertEqual(scorecard["Completeness_Count"], 96)
        self.assertEqual(scorecard["Completeness_Score_Pct"], 96.0)
        self.assertEqual(scorecard["Quality_Status"], "PASS")

    def test_generate_scorecard_quality_status_flagged_at_threshold(self):
        """Test Quality_Status is FLAGGED when completeness exactly 95%."""
        # Create 100 points, 95 complete (95% completeness)
        raw_data = [
            {"PointID": i, "ELEVATION": 100.0 + i, "MATERIAL": "CONC", "SIZE": 48}
            for i in range(95)
        ]
        # Add 5 incomplete points
        raw_data.extend([
            {"PointID": i, "ELEVATION": 200.0 + i, "MATERIAL": "PVC"}
            for i in range(5)
        ])
        required_fields = ["ELEVATION", "MATERIAL", "SIZE"]

        scorecard = self.service.generate_scorecard(raw_data, required_fields)

        # 95/100 = 95% is NOT > 95%, so FLAGGED
        self.assertEqual(scorecard["Completeness_Score_Pct"], 95.0)
        self.assertEqual(scorecard["Quality_Status"], "FLAGGED")

    def test_generate_scorecard_completeness_score_rounding(self):
        """Test that Completeness_Score_Pct is properly rounded to 2 decimal places."""
        # Create 3 points, 1 complete (33.333...% completeness)
        raw_data = [
            {"PointID": 1, "ELEVATION": 100.0, "MATERIAL": "CONC", "SIZE": 48},
            {"PointID": 2, "ELEVATION": 101.0, "MATERIAL": "PVC"},  # Missing SIZE
            {"PointID": 3, "ELEVATION": 102.0, "SIZE": 36},  # Missing MATERIAL
        ]
        required_fields = ["ELEVATION", "MATERIAL", "SIZE"]

        scorecard = self.service.generate_scorecard(raw_data, required_fields)

        # Should round to 33.33
        self.assertEqual(scorecard["Completeness_Score_Pct"], 33.33)

    def test_generate_scorecard_positional_variance_present(self):
        """Test that Positional_Variance_Mock_FT is included and reasonable."""
        raw_data = [
            {"PointID": 1, "ELEVATION": 100.0, "MATERIAL": "CONC", "SIZE": 48},
        ]
        required_fields = ["ELEVATION", "MATERIAL", "SIZE"]

        scorecard = self.service.generate_scorecard(raw_data, required_fields)

        # Verify the mock variance is present and in expected range
        self.assertIn("Positional_Variance_Mock_FT", scorecard)
        variance = scorecard["Positional_Variance_Mock_FT"]
        self.assertIsInstance(variance, float)
        self.assertGreaterEqual(variance, 0.01)
        self.assertLessEqual(variance, 0.15)

    @patch('services.data_quality_scorecard.random.uniform')
    def test_generate_scorecard_positional_variance_deterministic(self, mock_random):
        """Test that positional variance uses the mocked random value correctly."""
        # Mock random.uniform to return a fixed value
        mock_random.return_value = 0.075

        raw_data = [
            {"PointID": 1, "ELEVATION": 100.0, "MATERIAL": "CONC", "SIZE": 48},
        ]
        required_fields = ["ELEVATION", "MATERIAL", "SIZE"]

        scorecard = self.service.generate_scorecard(raw_data, required_fields)

        # Should round to 3 decimal places
        self.assertEqual(scorecard["Positional_Variance_Mock_FT"], 0.075)

    def test_generate_scorecard_required_fields_tested(self):
        """Test that Required_Fields_Tested returns the input list unchanged."""
        required_fields = ["ELEVATION", "MATERIAL", "SIZE", "DEPTH"]
        raw_data = [
            {"PointID": 1, "ELEVATION": 100.0, "MATERIAL": "CONC", "SIZE": 48, "DEPTH": 10},
        ]

        scorecard = self.service.generate_scorecard(raw_data, required_fields)

        # Verify the required fields list is returned as-is
        self.assertEqual(scorecard["Required_Fields_Tested"], required_fields)
        self.assertEqual(len(scorecard["Required_Fields_Tested"]), 4)

    def test_generate_scorecard_with_single_point(self):
        """Test scorecard generation with a single data point."""
        raw_data = [
            {"PointID": 1, "ELEVATION": 100.0, "MATERIAL": "CONC", "SIZE": 48},
        ]
        required_fields = ["ELEVATION", "MATERIAL", "SIZE"]

        scorecard = self.service.generate_scorecard(raw_data, required_fields)

        self.assertEqual(scorecard["Total_Points_Analyzed"], 1)
        self.assertEqual(scorecard["Completeness_Count"], 1)
        self.assertEqual(scorecard["Completeness_Score_Pct"], 100.0)
        self.assertEqual(scorecard["Missing_Elevation_Count"], 0)
        self.assertEqual(scorecard["Quality_Status"], "PASS")

    def test_generate_scorecard_with_extra_fields(self):
        """Test scorecard when data points have extra fields beyond required."""
        raw_data = [
            {
                "PointID": 1,
                "ELEVATION": 100.0,
                "MATERIAL": "CONC",
                "SIZE": 48,
                "EXTRA_FIELD_1": "value1",
                "EXTRA_FIELD_2": "value2"
            },
        ]
        required_fields = ["ELEVATION", "MATERIAL", "SIZE"]

        scorecard = self.service.generate_scorecard(raw_data, required_fields)

        # Extra fields should not affect completeness
        self.assertEqual(scorecard["Completeness_Count"], 1)
        self.assertEqual(scorecard["Completeness_Score_Pct"], 100.0)

    def test_generate_scorecard_logging_initialization(self):
        """Test that service initialization logs appropriately."""
        logging.disable(logging.NOTSET)

        with self.assertLogs('services.data_quality_scorecard', level='INFO') as cm:
            test_service = DataQualityScorecardService()

        # Verify initialization log
        self.assertTrue(
            any("DataQualityScorecardService initialized" in log for log in cm.output),
            "Expected initialization log not found"
        )
        self.assertIsNotNone(test_service)

    def test_generate_scorecard_logging_analysis_start(self):
        """Test that generate_scorecard logs the analysis start."""
        logging.disable(logging.NOTSET)

        raw_data = [
            {"PointID": 1, "ELEVATION": 100.0, "MATERIAL": "CONC", "SIZE": 48},
        ]
        required_fields = ["ELEVATION", "MATERIAL", "SIZE"]

        with self.assertLogs('services.data_quality_scorecard', level='INFO') as cm:
            self.service.generate_scorecard(raw_data, required_fields)

        # Verify analysis start log
        self.assertTrue(
            any("Analyzing batch of 1 points against 3 required fields" in log for log in cm.output),
            "Expected analysis start log not found"
        )

    def test_generate_scorecard_logging_completion(self):
        """Test that generate_scorecard logs the completion with results."""
        logging.disable(logging.NOTSET)

        raw_data = [
            {"PointID": 1, "ELEVATION": 100.0, "MATERIAL": "CONC", "SIZE": 48},
            {"PointID": 2, "ELEVATION": 101.0, "SIZE": 36},  # Incomplete
        ]
        required_fields = ["ELEVATION", "MATERIAL", "SIZE"]

        with self.assertLogs('services.data_quality_scorecard', level='INFO') as cm:
            self.service.generate_scorecard(raw_data, required_fields)

        # Verify completion log with metrics
        self.assertTrue(
            any("Scorecard generated" in log and "Completeness: 50.0%" in log for log in cm.output),
            "Expected completion log with metrics not found"
        )

    def test_generate_scorecard_logging_empty_data_warning(self):
        """Test that generate_scorecard logs a warning for empty data."""
        logging.disable(logging.NOTSET)

        raw_data = []
        required_fields = ["ELEVATION", "MATERIAL", "SIZE"]

        with self.assertLogs('services.data_quality_scorecard', level='WARNING') as cm:
            self.service.generate_scorecard(raw_data, required_fields)

        # Verify warning log
        self.assertTrue(
            any("No data points provided for analysis" in log for log in cm.output),
            "Expected warning log for empty data not found"
        )

    def test_generate_scorecard_with_large_dataset(self):
        """Test scorecard generation with a large dataset for performance."""
        # Create 1000 points: 900 complete, 100 incomplete
        raw_data = [
            {"PointID": i, "ELEVATION": 100.0 + i, "MATERIAL": "CONC", "SIZE": 48}
            for i in range(900)
        ]
        raw_data.extend([
            {"PointID": i, "ELEVATION": 1000.0 + i, "SIZE": 36}  # Missing MATERIAL
            for i in range(100)
        ])
        required_fields = ["ELEVATION", "MATERIAL", "SIZE"]

        scorecard = self.service.generate_scorecard(raw_data, required_fields)

        # Verify correct calculation with large dataset
        self.assertEqual(scorecard["Total_Points_Analyzed"], 1000)
        self.assertEqual(scorecard["Completeness_Count"], 900)
        self.assertEqual(scorecard["Completeness_Score_Pct"], 90.0)
        self.assertEqual(scorecard["Quality_Status"], "FLAGGED")  # 90% < 95%

    def test_generate_scorecard_with_zero_elevation_value(self):
        """Test that zero elevation is treated as valid (not missing)."""
        raw_data = [
            {"PointID": 1, "ELEVATION": 0.0, "MATERIAL": "CONC", "SIZE": 48},  # Zero is valid
            {"PointID": 2, "ELEVATION": 100.0, "MATERIAL": "PVC", "SIZE": 36},
        ]
        required_fields = ["ELEVATION", "MATERIAL", "SIZE"]

        scorecard = self.service.generate_scorecard(raw_data, required_fields)

        # Zero elevation should NOT be counted as missing
        self.assertEqual(scorecard["Total_Points_Analyzed"], 2)
        self.assertEqual(scorecard["Completeness_Count"], 2)
        self.assertEqual(scorecard["Missing_Elevation_Count"], 0)
        self.assertEqual(scorecard["Completeness_Score_Pct"], 100.0)


class TestDataQualityScorecardServiceIntegration(unittest.TestCase):
    """Integration tests for complete workflow scenarios."""

    def test_real_world_scenario_mixed_quality_data(self):
        """Test a realistic scenario with mixed quality field data."""
        service = DataQualityScorecardService()

        # Simulate real field data collection with various issues
        raw_data = [
            # Good points (complete)
            {"PointID": "MH-001", "ELEVATION": 100.0, "MATERIAL": "CONC", "SIZE": 48, "DEPTH": 8.5},
            {"PointID": "MH-002", "ELEVATION": 101.2, "MATERIAL": "BRICK", "SIZE": 60, "DEPTH": 10.0},
            {"PointID": "MH-003", "ELEVATION": 99.8, "MATERIAL": "CONC", "SIZE": 48, "DEPTH": 7.0},

            # Points with issues
            {"PointID": "MH-004", "ELEVATION": 102.5, "MATERIAL": "CONC", "SIZE": 48},  # Missing DEPTH
            {"PointID": "MH-005", "MATERIAL": "PVC", "SIZE": 24, "DEPTH": 6.0},  # Missing ELEVATION (critical!)
            {"PointID": "MH-006", "ELEVATION": 98.3, "SIZE": 36, "DEPTH": 9.5},  # Missing MATERIAL
        ]

        required_fields = ["ELEVATION", "MATERIAL", "SIZE", "DEPTH"]

        scorecard = service.generate_scorecard(raw_data, required_fields)

        # Verify realistic results
        self.assertEqual(scorecard["Total_Points_Analyzed"], 6)
        self.assertEqual(scorecard["Completeness_Count"], 3)  # Only first 3 are complete
        self.assertEqual(scorecard["Completeness_Score_Pct"], 50.0)
        self.assertEqual(scorecard["Missing_Elevation_Count"], 1)  # MH-005
        self.assertEqual(scorecard["Quality_Status"], "FLAGGED")
        self.assertIn("Positional_Variance_Mock_FT", scorecard)


if __name__ == '__main__':
    unittest.main()
