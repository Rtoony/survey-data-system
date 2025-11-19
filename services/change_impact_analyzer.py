"""
services/change_impact_analyzer.py

ChangeImpactAnalyzerService - Standards Change Risk Assessment
Analyzes the potential impact of proposed changes to standards mappings
on historical or ongoing project data. Critical for risk management and
change control in the Standards Specification Module (SSM).

Key Features:
1. Simulates resolution engine on historical data
2. Compares baseline vs. proposed mapping outcomes
3. Generates detailed impact reports with risk scores
4. Identifies affected points and layer changes
"""

from typing import Dict, Any, List, Optional
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# --- Mocked Dependencies ---

class MockGKGSyncService:
    """
    Mocks the core mapping resolution logic (Phase 33/28).
    Simulates the GKGSyncService.resolve_mapping() behavior for testing impact analysis.
    """

    def resolve_mapping(
        self,
        feature_code: str,
        attributes: Dict[str, Any],
        proposed_override: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Mock resolution: returns a mapping result based on attribute conditions.

        Args:
            feature_code: The feature code to resolve (e.g., "SDMH")
            attributes: Dictionary of point attributes (e.g., {"SIZE": 60, "MAT": "PRECAST"})
            proposed_override: Optional proposed mapping to test for impact analysis

        Returns:
            Dictionary containing resolved mapping ID and layer assignment
        """
        is_large = attributes.get('SIZE', 0) > 40

        if proposed_override and is_large:
            # Simulate the new rule winning for large features
            return {
                "source_mapping_id": proposed_override['id'],
                "layer": "NEW_LAYER",
                "priority": proposed_override.get('priority', 9999)
            }
        elif is_large:
            # Simulate the baseline rule winning for large features
            return {
                "source_mapping_id": 300,
                "layer": "OLD_LAYER_LARGE",
                "priority": 300
            }
        else:
            # Default rule for small features
            return {
                "source_mapping_id": 100,
                "layer": "DEFAULT_LAYER",
                "priority": 100
            }


# --- Main Service ---

class ChangeImpactAnalyzerService:
    """
    Analyzes the potential impact of a proposed change to standards mappings
    on historical or ongoing project data. Critical for risk management and
    change control workflows in the SSM.

    This service enables:
    - Pre-deployment validation of mapping changes
    - Risk assessment before applying new standards
    - Impact quantification on existing project data
    - Change management audit trails
    """

    def __init__(self) -> None:
        """
        Initialize the ChangeImpactAnalyzerService with mock mapping resolution.
        In production, this would integrate with the actual GKGSyncService.
        """
        self.mapping_service = MockGKGSyncService()
        logger.info("ChangeImpactAnalyzerService initialized. Ready for risk assessment.")

    def _mock_fetch_historical_data(self, project_id: int) -> List[Dict[str, Any]]:
        """
        Simulates retrieving historical data points that will be tested for impact.
        In production, this would query the actual project database.

        Args:
            project_id: The project ID to fetch historical data for

        Returns:
            List of feature dictionaries with attributes to be tested
        """
        logger.info(f"Fetching mock historical data for project {project_id}...")
        return [
            {"id": 1, "feature_code": "SDMH", "SIZE": 60, "project_id": project_id},   # Large (Expected impact)
            {"id": 2, "feature_code": "SDMH", "SIZE": 36, "project_id": project_id},   # Small (No expected impact)
            {"id": 3, "feature_code": "SDMH", "SIZE": 48, "project_id": project_id},   # Large (Expected impact)
            {"id": 4, "feature_code": "SDMH", "SIZE": 72, "project_id": project_id},   # Large (Expected impact)
            {"id": 5, "feature_code": "SDMH", "SIZE": 30, "project_id": project_id}    # Small (No expected impact)
        ]

    def analyze_change_impact(
        self,
        proposed_mapping_id: int,
        proposed_conditions_json: str,
        project_id: int = 123
    ) -> Dict[str, Any]:
        """
        Reruns the mapping resolution pipeline on historical data using the proposed new rule.
        Compares baseline (current) vs. proposed (new) resolution outcomes to assess impact.

        Args:
            proposed_mapping_id: The ID of the proposed new mapping rule
            proposed_conditions_json: JSON string of conditions for the new mapping
            project_id: The project ID to analyze (defaults to 123 for testing)

        Returns:
            Dictionary containing:
                - Total_Points_Tested: Number of data points analyzed
                - Affected_Points_Count: Number of points with changed mappings
                - Risk_Score_Percent: Percentage of points affected
                - Proposed_Mapping_ID: The ID of the proposed mapping
                - Impact_Report: Detailed list of affected points with before/after states
        """
        logger.info(
            f"Starting impact analysis for Project {project_id} "
            f"using proposed mapping ID {proposed_mapping_id}."
        )

        # Fetch historical data points to test
        raw_data_points = self._mock_fetch_historical_data(project_id)
        affected_points = []

        # Parse and prepare the proposed mapping structure
        try:
            conditions_dict = json.loads(proposed_conditions_json)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse proposed conditions JSON: {e}")
            return {
                "Error": "Invalid JSON format for proposed_conditions_json",
                "Details": str(e)
            }

        proposed_mapping = {
            "id": proposed_mapping_id,
            "conditions": conditions_dict,
            "priority": 9999  # High priority to ensure it's considered in resolution
        }

        # Analyze each historical point for impact
        for point in raw_data_points:
            # Step 1: Get Baseline (Current/Old) Resolution
            baseline_result = self.mapping_service.resolve_mapping(
                point['feature_code'],
                point
            )

            # Step 2: Get Proposed (New) Resolution with the proposed override
            proposed_result = self.mapping_service.resolve_mapping(
                point['feature_code'],
                point,
                proposed_mapping
            )

            # Step 3: Compare results - track points with different mapping IDs
            if proposed_result['source_mapping_id'] != baseline_result['source_mapping_id']:
                affected_points.append({
                    "point_id": point['id'],
                    "feature_code": point['feature_code'],
                    "attributes": {k: v for k, v in point.items() if k not in ['id', 'project_id', 'feature_code']},
                    "old_mapping_id": baseline_result['source_mapping_id'],
                    "old_layer": baseline_result['layer'],
                    "new_mapping_id": proposed_result['source_mapping_id'],
                    "new_layer": proposed_result['layer']
                })
                logger.debug(
                    f"Point {point['id']}: Mapping changed from "
                    f"{baseline_result['source_mapping_id']} ({baseline_result['layer']}) -> "
                    f"{proposed_result['source_mapping_id']} ({proposed_result['layer']})"
                )

        # Calculate impact metrics
        total_points = len(raw_data_points)
        affected_count = len(affected_points)
        risk_score = round((affected_count / total_points) * 100, 2) if total_points > 0 else 0.0

        # Compile the impact report
        report = {
            "Project_ID": project_id,
            "Total_Points_Tested": total_points,
            "Affected_Points_Count": affected_count,
            "Unaffected_Points_Count": total_points - affected_count,
            "Risk_Score_Percent": risk_score,
            "Proposed_Mapping_ID": proposed_mapping_id,
            "Proposed_Conditions": conditions_dict,
            "Impact_Report": affected_points,
            "Analysis_Status": "COMPLETED",
            "Recommendation": self._generate_recommendation(risk_score)
        }

        logger.info(
            f"Impact analysis complete. Affected: {affected_count}/{total_points} points "
            f"(Risk: {risk_score}%). Recommendation: {report['Recommendation']}"
        )

        return report

    def _generate_recommendation(self, risk_score: float) -> str:
        """
        Generates a recommendation based on the calculated risk score.

        Args:
            risk_score: The percentage of points affected by the change

        Returns:
            A recommendation string for change management decision-making
        """
        if risk_score == 0:
            return "SAFE - No impact detected. Proceed with deployment."
        elif risk_score < 10:
            return "LOW RISK - Minimal impact. Review affected points, then proceed."
        elif risk_score < 30:
            return "MODERATE RISK - Significant impact. Stakeholder review recommended."
        elif risk_score < 60:
            return "HIGH RISK - Major impact. Detailed validation required before deployment."
        else:
            return "CRITICAL RISK - Extensive impact. Consider phased rollout or additional testing."


# --- Example Execution ---
if __name__ == '__main__':
    service = ChangeImpactAnalyzerService()

    # Simulate a new rule (ID 500) that makes a change only for large items (SIZE > 40)
    proposed_conditions = json.dumps({"SIZE": {"operator": ">", "value": 40}})

    impact_report = service.analyze_change_impact(
        proposed_mapping_id=500,
        proposed_conditions_json=proposed_conditions,
        project_id=404
    )

    print("\n" + "=" * 60)
    print("STANDARDS CHANGE IMPACT ANALYSIS REPORT")
    print("=" * 60)
    print(json.dumps(impact_report, indent=4))
    print("=" * 60)
