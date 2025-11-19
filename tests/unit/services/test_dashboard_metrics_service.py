"""
Unit tests for DashboardMetricsService
Tests KPI calculation and metrics aggregation for the Command Center Dashboard.
"""

import unittest
import logging
from unittest.mock import MagicMock, patch
from services.dashboard_metrics_service import (
    DashboardMetricsService,
    MockSSMAuditService,
    MockSSMDataService
)


class TestDashboardMetricsService(unittest.TestCase):
    """Test suite for DashboardMetricsService KPI calculations."""

    def setUp(self):
        """Initialize the service before each test."""
        self.service = DashboardMetricsService()

    def test_service_initialization(self):
        """Test that the service initializes correctly with mock dependencies."""
        self.assertIsNotNone(self.service.audit_service)
        self.assertIsNotNone(self.service.data_service)
        self.assertIsInstance(self.service.audit_service, MockSSMAuditService)
        self.assertIsInstance(self.service.data_service, MockSSMDataService)

    def test_calculate_kpis_with_active_mappings(self):
        """Test KPI calculation with active mappings."""
        mapping_details = [
            {"id": 1, "conditions_count": 2, "is_active": True},
            {"id": 2, "conditions_count": 1, "is_active": True},
            {"id": 3, "conditions_count": 3, "is_active": True},
        ]

        kpis = self.service._calculate_kpis(mapping_details)

        # Verify Total_Active_Mappings
        self.assertEqual(kpis["Total_Active_Mappings"], 3)

        # Verify Average_Specificity: (2 + 1 + 3) / 3 = 2.0
        self.assertEqual(kpis["Average_Specificity"], 2.0)

    def test_calculate_kpis_with_inactive_mappings(self):
        """Test that inactive mappings are excluded from KPI calculations."""
        mapping_details = [
            {"id": 1, "conditions_count": 2, "is_active": True},
            {"id": 2, "conditions_count": 1, "is_active": True},
            {"id": 3, "conditions_count": 5, "is_active": False},  # Inactive - should be excluded
            {"id": 4, "conditions_count": 10, "is_active": False}  # Inactive - should be excluded
        ]

        kpis = self.service._calculate_kpis(mapping_details)

        # Verify only active mappings are counted
        self.assertEqual(kpis["Total_Active_Mappings"], 2)

        # Verify Average_Specificity: (2 + 1) / 2 = 1.5
        self.assertEqual(kpis["Average_Specificity"], 1.5)

    def test_calculate_kpis_with_no_active_mappings(self):
        """Test KPI calculation when there are no active mappings."""
        mapping_details = [
            {"id": 1, "conditions_count": 5, "is_active": False},
            {"id": 2, "conditions_count": 3, "is_active": False},
        ]

        kpis = self.service._calculate_kpis(mapping_details)

        # Verify zero active mappings
        self.assertEqual(kpis["Total_Active_Mappings"], 0)

        # Verify Average_Specificity is 0.0 when no active mappings
        self.assertEqual(kpis["Average_Specificity"], 0.0)

    def test_calculate_kpis_with_empty_list(self):
        """Test KPI calculation with an empty mapping list."""
        mapping_details = []

        kpis = self.service._calculate_kpis(mapping_details)

        self.assertEqual(kpis["Total_Active_Mappings"], 0)
        self.assertEqual(kpis["Average_Specificity"], 0.0)

    def test_calculate_kpis_average_rounding(self):
        """Test that Average_Specificity is properly rounded to 2 decimal places."""
        mapping_details = [
            {"id": 1, "conditions_count": 1, "is_active": True},
            {"id": 2, "conditions_count": 1, "is_active": True},
            {"id": 3, "conditions_count": 1, "is_active": True},
        ]

        kpis = self.service._calculate_kpis(mapping_details)

        # 3 / 3 = 1.0
        self.assertEqual(kpis["Average_Specificity"], 1.0)

        # Test with uneven division
        mapping_details_uneven = [
            {"id": 1, "conditions_count": 2, "is_active": True},
            {"id": 2, "conditions_count": 3, "is_active": True},
            {"id": 3, "conditions_count": 3, "is_active": True},
        ]

        kpis_uneven = self.service._calculate_kpis(mapping_details_uneven)

        # (2 + 3 + 3) / 3 = 2.666... -> 2.67 (rounded to 2 decimals)
        self.assertEqual(kpis_uneven["Average_Specificity"], 2.67)

    def test_get_project_summary_metrics_structure(self):
        """Test that get_project_summary_metrics returns the expected structure."""
        project_id = 404
        metrics = self.service.get_project_summary_metrics(project_id)

        # Verify all required fields are present
        required_fields = [
            "Project_ID",
            "Total_Mappings_Active",
            "Compliance_Rate_Mock",
            "Average_Specificity_Index",
            "Last_Standards_Update",
            "Standards_Version",
            "Data_Velocity_Mock"
        ]

        for field in required_fields:
            self.assertIn(field, metrics, f"Missing required field: {field}")

        # Verify Project_ID matches input
        self.assertEqual(metrics["Project_ID"], project_id)

    def test_get_project_summary_metrics_values(self):
        """Test that get_project_summary_metrics returns correct calculated values."""
        project_id = 100
        metrics = self.service.get_project_summary_metrics(project_id)

        # Based on MockSSMDataService data (3 active mappings with 2, 1, 3 conditions)
        self.assertEqual(metrics["Total_Mappings_Active"], 3)

        # Average: (2 + 1 + 3) / 3 = 2.0
        self.assertEqual(metrics["Average_Specificity_Index"], 2.0)

        # Verify mocked values are present
        self.assertEqual(metrics["Compliance_Rate_Mock"], "98.7%")
        self.assertEqual(metrics["Data_Velocity_Mock"], "1,500 points/day")

    def test_get_project_summary_metrics_audit_integration(self):
        """Test that get_project_summary_metrics correctly integrates audit service data."""
        project_id = 200
        metrics = self.service.get_project_summary_metrics(project_id)

        # Verify audit data is included (from MockSSMAuditService)
        self.assertEqual(metrics["Standards_Version"], "V1.1 Priority Fix")
        self.assertEqual(metrics["Last_Standards_Update"], "2025-11-19T00:30:00Z")

    def test_get_project_summary_metrics_logging(self):
        """Test that get_project_summary_metrics logs appropriately."""
        logging.disable(logging.NOTSET)

        project_id = 300

        with self.assertLogs('services.dashboard_metrics_service', level='INFO') as cm:
            self.service.get_project_summary_metrics(project_id)

        # Verify metrics generation log
        self.assertTrue(
            any(f"Generating summary metrics for Project ID: {project_id}" in log for log in cm.output),
            "Expected metrics generation log not found"
        )

        # Verify success log
        self.assertTrue(
            any(f"Dashboard metrics generated successfully for Project {project_id}" in log for log in cm.output),
            "Expected success log not found"
        )

    def test_service_initialization_logging(self):
        """Test that service initialization logs appropriately."""
        logging.disable(logging.NOTSET)

        with self.assertLogs('services.dashboard_metrics_service', level='INFO') as cm:
            # Create a new instance within the logging context
            test_service = DashboardMetricsService()

        # Verify initialization log
        self.assertTrue(
            any("DashboardMetricsService initialized" in log for log in cm.output),
            "Expected initialization log not found"
        )
        self.assertIsNotNone(test_service)


class TestMockSSMAuditService(unittest.TestCase):
    """Test suite for MockSSMAuditService."""

    def setUp(self):
        """Initialize the mock audit service."""
        self.audit_service = MockSSMAuditService()

    def test_get_latest_snapshot_structure(self):
        """Test that get_latest_snapshot returns the expected structure."""
        snapshot = self.audit_service.get_latest_snapshot()

        self.assertIn("version_name", snapshot)
        self.assertIn("timestamp", snapshot)

    def test_get_latest_snapshot_values(self):
        """Test that get_latest_snapshot returns expected values."""
        snapshot = self.audit_service.get_latest_snapshot()

        self.assertEqual(snapshot["version_name"], "V1.1 Priority Fix")
        self.assertEqual(snapshot["timestamp"], "2025-11-19T00:30:00Z")


class TestMockSSMDataService(unittest.TestCase):
    """Test suite for MockSSMDataService."""

    def setUp(self):
        """Initialize the mock data service."""
        self.data_service = MockSSMDataService()

    def test_get_mapping_details_structure(self):
        """Test that get_mapping_details returns the expected structure."""
        mappings = self.data_service.get_mapping_details()

        self.assertIsInstance(mappings, list)
        self.assertGreater(len(mappings), 0)

        # Verify each mapping has required fields
        for mapping in mappings:
            self.assertIn("id", mapping)
            self.assertIn("conditions_count", mapping)
            self.assertIn("is_active", mapping)

    def test_get_mapping_details_count(self):
        """Test that get_mapping_details returns the expected number of mappings."""
        mappings = self.data_service.get_mapping_details()

        # Mock data has 4 mappings
        self.assertEqual(len(mappings), 4)

    def test_get_mapping_details_active_count(self):
        """Test the count of active mappings in mock data."""
        mappings = self.data_service.get_mapping_details()
        active_count = sum(1 for m in mappings if m["is_active"])

        # Mock data has 3 active mappings
        self.assertEqual(active_count, 3)


class TestDashboardMetricsServiceIntegration(unittest.TestCase):
    """Integration tests for DashboardMetricsService with mocked dependencies."""

    def test_full_workflow_with_custom_mocks(self):
        """Test the complete workflow with custom mock data."""
        service = DashboardMetricsService()

        # Replace mock services with custom test data
        custom_audit = MockSSMAuditService()
        custom_data = MockSSMDataService()

        service.audit_service = custom_audit
        service.data_service = custom_data

        # Execute full workflow
        metrics = service.get_project_summary_metrics(project_id=999)

        # Verify complete result
        self.assertIsInstance(metrics, dict)
        self.assertEqual(metrics["Project_ID"], 999)
        self.assertIsInstance(metrics["Total_Mappings_Active"], int)
        self.assertIsInstance(metrics["Average_Specificity_Index"], float)

    @patch.object(MockSSMDataService, 'get_mapping_details')
    @patch.object(MockSSMAuditService, 'get_latest_snapshot')
    def test_service_with_patched_dependencies(self, mock_snapshot, mock_mappings):
        """Test service behavior with fully patched dependencies."""
        # Setup custom return values
        mock_snapshot.return_value = {
            "version_name": "Test Version",
            "timestamp": "2025-01-01T00:00:00Z"
        }

        mock_mappings.return_value = [
            {"id": 10, "conditions_count": 5, "is_active": True},
            {"id": 20, "conditions_count": 3, "is_active": True},
        ]

        service = DashboardMetricsService()
        metrics = service.get_project_summary_metrics(project_id=123)

        # Verify mocked values are used
        self.assertEqual(metrics["Total_Mappings_Active"], 2)
        self.assertEqual(metrics["Average_Specificity_Index"], 4.0)  # (5 + 3) / 2
        self.assertEqual(metrics["Standards_Version"], "Test Version")
        self.assertEqual(metrics["Last_Standards_Update"], "2025-01-01T00:00:00Z")


if __name__ == '__main__':
    unittest.main()
