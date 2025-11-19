"""
Unit tests for ChangeImpactAnalyzerService
Tests standards change impact analysis and risk assessment functionality.
"""

import unittest
import json
import logging
from unittest.mock import MagicMock, patch, call
from services.change_impact_analyzer import (
    ChangeImpactAnalyzerService,
    MockGKGSyncService
)


class TestMockGKGSyncService(unittest.TestCase):
    """Test suite for MockGKGSyncService resolution logic."""

    def setUp(self):
        """Initialize the mock service before each test."""
        self.mock_service = MockGKGSyncService()

    def test_resolve_mapping_small_feature_baseline(self):
        """Test resolution for small feature without override (baseline behavior)."""
        result = self.mock_service.resolve_mapping(
            feature_code="SDMH",
            attributes={"SIZE": 30}
        )

        self.assertEqual(result["source_mapping_id"], 100)
        self.assertEqual(result["layer"], "DEFAULT_LAYER")
        self.assertEqual(result["priority"], 100)

    def test_resolve_mapping_large_feature_baseline(self):
        """Test resolution for large feature without override (baseline behavior)."""
        result = self.mock_service.resolve_mapping(
            feature_code="SDMH",
            attributes={"SIZE": 60}
        )

        self.assertEqual(result["source_mapping_id"], 300)
        self.assertEqual(result["layer"], "OLD_LAYER_LARGE")
        self.assertEqual(result["priority"], 300)

    def test_resolve_mapping_large_feature_with_override(self):
        """Test resolution for large feature with proposed override applied."""
        proposed_override = {
            "id": 500,
            "priority": 9999
        }

        result = self.mock_service.resolve_mapping(
            feature_code="SDMH",
            attributes={"SIZE": 60},
            proposed_override=proposed_override
        )

        self.assertEqual(result["source_mapping_id"], 500)
        self.assertEqual(result["layer"], "NEW_LAYER")
        self.assertEqual(result["priority"], 9999)

    def test_resolve_mapping_small_feature_with_override_not_applied(self):
        """Test that override does not apply to small features (SIZE <= 40)."""
        proposed_override = {
            "id": 500,
            "priority": 9999
        }

        result = self.mock_service.resolve_mapping(
            feature_code="SDMH",
            attributes={"SIZE": 30},
            proposed_override=proposed_override
        )

        # Override should not apply, should get default layer
        self.assertEqual(result["source_mapping_id"], 100)
        self.assertEqual(result["layer"], "DEFAULT_LAYER")

    def test_resolve_mapping_boundary_condition_size_40(self):
        """Test resolution at boundary condition (SIZE = 40, not > 40)."""
        result = self.mock_service.resolve_mapping(
            feature_code="SDMH",
            attributes={"SIZE": 40}
        )

        # SIZE must be > 40, so 40 should use default layer
        self.assertEqual(result["source_mapping_id"], 100)
        self.assertEqual(result["layer"], "DEFAULT_LAYER")

    def test_resolve_mapping_boundary_condition_size_41(self):
        """Test resolution just above boundary (SIZE = 41, which is > 40)."""
        result = self.mock_service.resolve_mapping(
            feature_code="SDMH",
            attributes={"SIZE": 41}
        )

        # SIZE = 41 > 40, should use large layer
        self.assertEqual(result["source_mapping_id"], 300)
        self.assertEqual(result["layer"], "OLD_LAYER_LARGE")


class TestChangeImpactAnalyzerService(unittest.TestCase):
    """Test suite for ChangeImpactAnalyzerService impact analysis."""

    def setUp(self):
        """Initialize the service before each test."""
        self.service = ChangeImpactAnalyzerService()

    def test_service_initialization(self):
        """Test that the service initializes correctly with mock dependencies."""
        self.assertIsNotNone(self.service.mapping_service)
        self.assertIsInstance(self.service.mapping_service, MockGKGSyncService)

    def test_mock_fetch_historical_data(self):
        """Test that mock historical data is fetched correctly."""
        project_id = 123
        data = self.service._mock_fetch_historical_data(project_id)

        self.assertEqual(len(data), 5)
        self.assertTrue(all('id' in point for point in data))
        self.assertTrue(all('feature_code' in point for point in data))
        self.assertTrue(all('SIZE' in point for point in data))
        self.assertTrue(all(point['project_id'] == project_id for point in data))

    def test_mock_historical_data_size_distribution(self):
        """Test that mock data includes both large and small features."""
        data = self.service._mock_fetch_historical_data(123)

        large_features = [p for p in data if p['SIZE'] > 40]
        small_features = [p for p in data if p['SIZE'] <= 40]

        self.assertEqual(len(large_features), 3)  # 60, 48, 72
        self.assertEqual(len(small_features), 2)  # 36, 30

    def test_analyze_change_impact_high_impact(self):
        """Test impact analysis with a rule that affects large features (critical impact at 60%)."""
        proposed_conditions = json.dumps({"SIZE": {"operator": ">", "value": 40}})

        report = self.service.analyze_change_impact(
            proposed_mapping_id=500,
            proposed_conditions_json=proposed_conditions,
            project_id=404
        )

        # Verify basic report structure
        self.assertEqual(report["Project_ID"], 404)
        self.assertEqual(report["Total_Points_Tested"], 5)
        self.assertEqual(report["Proposed_Mapping_ID"], 500)
        self.assertEqual(report["Analysis_Status"], "COMPLETED")

        # Verify impact: 3 large features should be affected (SIZE > 40)
        self.assertEqual(report["Affected_Points_Count"], 3)
        self.assertEqual(report["Unaffected_Points_Count"], 2)
        self.assertEqual(report["Risk_Score_Percent"], 60.0)

        # Verify recommendation based on risk score (60% is CRITICAL RISK threshold)
        self.assertIn("CRITICAL RISK", report["Recommendation"])

        # Verify impact report details
        self.assertEqual(len(report["Impact_Report"]), 3)
        for affected in report["Impact_Report"]:
            self.assertIn("point_id", affected)
            self.assertIn("old_mapping_id", affected)
            self.assertIn("new_mapping_id", affected)
            self.assertIn("old_layer", affected)
            self.assertIn("new_layer", affected)
            self.assertEqual(affected["new_mapping_id"], 500)
            self.assertEqual(affected["new_layer"], "NEW_LAYER")

    def test_analyze_change_impact_no_impact(self):
        """Test impact analysis with a rule that affects no features (zero impact)."""
        # Create a proposed mapping that won't match any features
        # Since our mock only has SDMH with SIZE values, and override only applies to SIZE > 40,
        # we can simulate zero impact by making override not apply
        # Let's mock the service to always return baseline

        with patch.object(self.service, '_mock_fetch_historical_data') as mock_fetch:
            # Use only small features
            mock_fetch.return_value = [
                {"id": 1, "feature_code": "SDMH", "SIZE": 30, "project_id": 123},
                {"id": 2, "feature_code": "SDMH", "SIZE": 36, "project_id": 123}
            ]

            proposed_conditions = json.dumps({"SIZE": {"operator": ">", "value": 40}})

            report = self.service.analyze_change_impact(
                proposed_mapping_id=500,
                proposed_conditions_json=proposed_conditions,
                project_id=123
            )

            # No features should be affected
            self.assertEqual(report["Affected_Points_Count"], 0)
            self.assertEqual(report["Unaffected_Points_Count"], 2)
            self.assertEqual(report["Risk_Score_Percent"], 0.0)
            self.assertIn("SAFE", report["Recommendation"])
            self.assertEqual(len(report["Impact_Report"]), 0)

    def test_analyze_change_impact_partial_impact(self):
        """Test impact analysis with moderate/partial impact."""
        with patch.object(self.service, '_mock_fetch_historical_data') as mock_fetch:
            # Use mix: 2 large, 8 small -> 20% impact
            mock_fetch.return_value = [
                {"id": i, "feature_code": "SDMH", "SIZE": 60 if i <= 2 else 30, "project_id": 123}
                for i in range(1, 11)
            ]

            proposed_conditions = json.dumps({"SIZE": {"operator": ">", "value": 40}})

            report = self.service.analyze_change_impact(
                proposed_mapping_id=500,
                proposed_conditions_json=proposed_conditions,
                project_id=123
            )

            # 2 out of 10 features affected = 20%
            self.assertEqual(report["Affected_Points_Count"], 2)
            self.assertEqual(report["Unaffected_Points_Count"], 8)
            self.assertEqual(report["Risk_Score_Percent"], 20.0)
            self.assertIn("MODERATE RISK", report["Recommendation"])

    def test_analyze_change_impact_invalid_json(self):
        """Test handling of invalid JSON in proposed conditions."""
        invalid_json = "{ this is not valid JSON }"

        report = self.service.analyze_change_impact(
            proposed_mapping_id=500,
            proposed_conditions_json=invalid_json,
            project_id=123
        )

        # Should return error report
        self.assertIn("Error", report)
        self.assertIn("Invalid JSON format", report["Error"])
        self.assertIn("Details", report)

    def test_analyze_change_impact_empty_dataset(self):
        """Test impact analysis with empty historical dataset."""
        with patch.object(self.service, '_mock_fetch_historical_data') as mock_fetch:
            mock_fetch.return_value = []

            proposed_conditions = json.dumps({"SIZE": {"operator": ">", "value": 40}})

            report = self.service.analyze_change_impact(
                proposed_mapping_id=500,
                proposed_conditions_json=proposed_conditions,
                project_id=999
            )

            # No data to analyze
            self.assertEqual(report["Total_Points_Tested"], 0)
            self.assertEqual(report["Affected_Points_Count"], 0)
            self.assertEqual(report["Risk_Score_Percent"], 0.0)

    def test_generate_recommendation_safe(self):
        """Test recommendation generation for zero risk."""
        recommendation = self.service._generate_recommendation(0.0)
        self.assertIn("SAFE", recommendation)
        self.assertIn("No impact", recommendation)

    def test_generate_recommendation_low_risk(self):
        """Test recommendation generation for low risk (< 10%)."""
        recommendation = self.service._generate_recommendation(5.0)
        self.assertIn("LOW RISK", recommendation)

    def test_generate_recommendation_moderate_risk(self):
        """Test recommendation generation for moderate risk (10-30%)."""
        recommendation = self.service._generate_recommendation(20.0)
        self.assertIn("MODERATE RISK", recommendation)

    def test_generate_recommendation_high_risk(self):
        """Test recommendation generation for high risk (30-60%)."""
        recommendation = self.service._generate_recommendation(45.0)
        self.assertIn("HIGH RISK", recommendation)

    def test_generate_recommendation_critical_risk(self):
        """Test recommendation generation for critical risk (>= 60%)."""
        recommendation = self.service._generate_recommendation(80.0)
        self.assertIn("CRITICAL RISK", recommendation)

    def test_generate_recommendation_boundary_conditions(self):
        """Test recommendation generation at boundary values."""
        # Test at exact boundaries
        self.assertIn("LOW RISK", self.service._generate_recommendation(9.99))
        self.assertIn("MODERATE RISK", self.service._generate_recommendation(10.0))
        self.assertIn("MODERATE RISK", self.service._generate_recommendation(29.99))
        self.assertIn("HIGH RISK", self.service._generate_recommendation(30.0))
        self.assertIn("HIGH RISK", self.service._generate_recommendation(59.99))
        self.assertIn("CRITICAL RISK", self.service._generate_recommendation(60.0))

    def test_impact_report_includes_attributes(self):
        """Test that impact report includes point attributes for traceability."""
        proposed_conditions = json.dumps({"SIZE": {"operator": ">", "value": 40}})

        report = self.service.analyze_change_impact(
            proposed_mapping_id=500,
            proposed_conditions_json=proposed_conditions,
            project_id=404
        )

        # Check that affected points include attributes
        for affected in report["Impact_Report"]:
            self.assertIn("attributes", affected)
            self.assertIsInstance(affected["attributes"], dict)
            # Attributes should include SIZE but not id/project_id/feature_code
            self.assertIn("SIZE", affected["attributes"])

    def test_analyze_change_impact_report_structure(self):
        """Test that the impact report has all required fields."""
        proposed_conditions = json.dumps({"SIZE": {"operator": ">", "value": 40}})

        report = self.service.analyze_change_impact(
            proposed_mapping_id=500,
            proposed_conditions_json=proposed_conditions,
            project_id=404
        )

        # Verify all expected keys are present
        required_keys = [
            "Project_ID",
            "Total_Points_Tested",
            "Affected_Points_Count",
            "Unaffected_Points_Count",
            "Risk_Score_Percent",
            "Proposed_Mapping_ID",
            "Proposed_Conditions",
            "Impact_Report",
            "Analysis_Status",
            "Recommendation"
        ]

        for key in required_keys:
            self.assertIn(key, report, f"Missing required key: {key}")

    @patch('services.change_impact_analyzer.logger')
    def test_logging_during_analysis(self, mock_logger):
        """Test that appropriate logging occurs during impact analysis."""
        proposed_conditions = json.dumps({"SIZE": {"operator": ">", "value": 40}})

        self.service.analyze_change_impact(
            proposed_mapping_id=500,
            proposed_conditions_json=proposed_conditions,
            project_id=404
        )

        # Verify that info-level logging occurred
        self.assertTrue(mock_logger.info.called)
        # Check for specific log messages
        log_messages = [call[0][0] for call in mock_logger.info.call_args_list]
        self.assertTrue(any("Starting impact analysis" in msg for msg in log_messages))
        self.assertTrue(any("complete" in msg for msg in log_messages))


if __name__ == '__main__':
    unittest.main()
