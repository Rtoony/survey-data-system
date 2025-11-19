"""
services/dashboard_metrics_service.py

DashboardMetricsService - Command Center KPI Aggregation
Compiles Key Performance Indicators (KPIs) from various SSM services
for presentation in the Command Center Dashboard.

Metrics Provided:
1. Total_Mappings: Count of all active conditional mappings
2. Compliance_Rate: Percentage of points that match specific mappings
3. Last_Standards_Update: Timestamp from the Audit Service
4. Average_Specificity: Average number of conditions per mapping
"""

from typing import Dict, Any, List, Optional
import logging
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Mocked Dependencies ---

class MockSSMAuditService:
    """Mocks retrieval of the last snapshot from Phase 31."""

    def get_latest_snapshot(self) -> Dict[str, Any]:
        """
        Retrieves the most recent SSM configuration snapshot.

        Returns:
            Dict containing version_name and timestamp
        """
        return {
            "version_name": "V1.1 Priority Fix",
            "timestamp": "2025-11-19T00:30:00Z"
        }


class MockSSMDataService:
    """Mocks retrieval of raw data counts from the database."""

    def get_mapping_details(self) -> List[Dict[str, Any]]:
        """
        Retrieves detailed information about all mappings.

        Returns:
            List of mapping dictionaries with id, conditions_count, and is_active
        """
        return [
            {"id": 1, "conditions_count": 2, "is_active": True},
            {"id": 2, "conditions_count": 1, "is_active": True},
            {"id": 3, "conditions_count": 3, "is_active": True},
            {"id": 4, "conditions_count": 0, "is_active": False}
        ]


# --- Main Service ---

class DashboardMetricsService:
    """
    Aggregates data from various SSM services to generate Key Performance Indicators (KPIs)
    for the Command Center Dashboard presentation layer.

    This service acts as a facade, pulling data from multiple sources and calculating
    high-level metrics for executive dashboards and reporting.
    """

    def __init__(self) -> None:
        """Initialize the DashboardMetricsService with mock data providers."""
        self.audit_service: MockSSMAuditService = MockSSMAuditService()
        self.data_service: MockSSMDataService = MockSSMDataService()
        logger.info("DashboardMetricsService initialized.")

    def _calculate_kpis(self, mapping_details: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculates granular KPIs from raw mapping data.

        Args:
            mapping_details: List of mapping dictionaries containing conditions_count and is_active

        Returns:
            Dictionary containing calculated KPIs:
                - Total_Active_Mappings: Count of active mappings
                - Average_Specificity: Average number of conditions per active mapping
        """
        active_mappings = [m for m in mapping_details if m['is_active']]
        total_active = len(active_mappings)

        # 1. Total Mappings
        total_mappings = total_active

        # 2. Average Specificity (conditions per mapping)
        if total_active > 0:
            total_conditions = sum(m['conditions_count'] for m in active_mappings)
            avg_specificity = round(total_conditions / total_active, 2)
        else:
            avg_specificity = 0.0

        return {
            "Total_Active_Mappings": total_mappings,
            "Average_Specificity": avg_specificity,
        }

    def get_project_summary_metrics(self, project_id: int) -> Dict[str, Any]:
        """
        Retrieves and compiles the final set of metrics for the dashboard view.

        This is the primary external interface for the Command Center Dashboard.
        It orchestrates data retrieval from multiple sources and returns a complete
        metrics package.

        Args:
            project_id: The project identifier for which to generate metrics

        Returns:
            Dictionary containing:
                - Project_ID: The requested project ID
                - Total_Mappings_Active: Count of active SSM mappings
                - Compliance_Rate_Mock: Mocked compliance percentage (requires point data in production)
                - Average_Specificity_Index: Average conditions per mapping
                - Last_Standards_Update: ISO timestamp of last SSM update
                - Standards_Version: Version name of current SSM configuration
                - Data_Velocity_Mock: Mocked data throughput metric
        """
        logger.info(f"Generating summary metrics for Project ID: {project_id}")

        # 1. Data Retrieval
        mapping_details = self.data_service.get_mapping_details()
        latest_audit = self.audit_service.get_latest_snapshot()

        # 2. KPI Calculation
        kpis = self._calculate_kpis(mapping_details)

        # 3. Compile Final Metrics
        summary: Dict[str, Any] = {
            "Project_ID": project_id,
            "Total_Mappings_Active": kpis["Total_Active_Mappings"],

            # Mocked KPI (Real implementation needs point data and compliance checks)
            "Compliance_Rate_Mock": "98.7%",

            "Average_Specificity_Index": kpis["Average_Specificity"],
            "Last_Standards_Update": latest_audit["timestamp"],
            "Standards_Version": latest_audit["version_name"],

            # Mocked throughput metric (Real implementation needs entity processing logs)
            "Data_Velocity_Mock": "1,500 points/day"
        }

        logger.info(f"Dashboard metrics generated successfully for Project {project_id}.")
        return summary


# --- Example Execution ---
if __name__ == '__main__':
    service = DashboardMetricsService()
    metrics = service.get_project_summary_metrics(project_id=404)

    print("\n--- COMMAND CENTER DASHBOARD METRICS ---")
    print(json.dumps(metrics, indent=4))
