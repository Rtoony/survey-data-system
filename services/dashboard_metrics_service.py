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
from sqlalchemy.sql import select, func, and_
from database import get_db, execute_query
from data.ssm_schema import ssm_mappings
from services.ssm_audit_service import SSMAuditService
import logging
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Main Service ---

class DashboardMetricsService:
    """
    Aggregates data from various SSM services to generate Key Performance Indicators (KPIs)
    for the Command Center Dashboard presentation layer.

    This service acts as a facade, pulling data from multiple sources and calculating
    high-level metrics for executive dashboards and reporting.
    """

    def __init__(self) -> None:
        """Initialize the DashboardMetricsService with live database dependencies."""
        self.audit_service: SSMAuditService = SSMAuditService()
        logger.info("DashboardMetricsService initialized with live dependencies.")

    def _fetch_mapping_statistics(self, conn) -> Dict[str, Any]:
        """
        Calculates total active mappings and average specificity directly from the database.

        Args:
            conn: SQLAlchemy database connection

        Returns:
            Dictionary containing calculated statistics:
                - Total_Active_Mappings: Count of active mappings
                - Average_Specificity: Average number of conditions per active mapping
        """
        # 1. Calculate Total Active Mappings
        total_active_stmt = select(func.count()).where(ssm_mappings.c.is_active == True)
        total_active = conn.execute(total_active_stmt).scalar()

        # 2. Calculate Average Specificity (Average Condition Count)
        # Fetch all active mappings to calculate condition counts (JSONB array length)
        # NOTE: A PostgreSQL-specific query could calculate this directly using jsonb_array_length
        active_mappings_stmt = select(ssm_mappings.c.conditions).where(ssm_mappings.c.is_active == True)
        active_mappings = conn.execute(active_mappings_stmt).fetchall()

        total_conditions = sum(len(m.conditions) if m.conditions else 0 for m in active_mappings)
        avg_specificity = round(total_conditions / total_active, 2) if total_active > 0 else 0.0

        logger.info(f"Fetched mapping statistics: {total_active} active mappings, avg specificity: {avg_specificity}")

        return {
            "Total_Active_Mappings": total_active,
            "Average_Specificity": avg_specificity,
        }

    def get_project_summary_metrics(self, project_id: int) -> Dict[str, Any]:
        """
        Retrieves and compiles the final set of metrics for the dashboard view using live data.

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

        # 1. Data Retrieval from Live Database
        with get_db() as conn:
            mapping_statistics = self._fetch_mapping_statistics(conn)

        # 2. Data Retrieval from Audit Service (Live Dependency)
        latest_audit = self.audit_service.get_latest_snapshot()

        # 3. Compile Final Metrics
        summary: Dict[str, Any] = {
            "Project_ID": project_id,
            "Total_Mappings_Active": mapping_statistics["Total_Active_Mappings"],

            # Mocked KPI (Real implementation needs point data and compliance checks)
            "Compliance_Rate_Mock": "98.7%",

            "Average_Specificity_Index": mapping_statistics["Average_Specificity"],
            "Last_Standards_Update": latest_audit.get("timestamp"),
            "Standards_Version": latest_audit.get("version_name"),

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
