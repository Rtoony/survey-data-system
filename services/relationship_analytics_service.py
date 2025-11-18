"""
Relationship Analytics Service
Analytics and metrics for the relationship graph.

This service provides analytics capabilities including:
- Relationship density and coverage metrics
- Missing relationship detection
- Entity connection analysis
- Project comparison
- Trend analysis

References:
    - docs/PHASE_3_COMPREHENSIVE_ANALYSIS.md
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.db_utils import execute_query
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict


class RelationshipAnalyticsService:
    """Service for analyzing relationship graph metrics"""

    def __init__(self):
        pass

    # ============================================================================
    # DENSITY & COVERAGE METRICS
    # ============================================================================

    def get_relationship_density(self, project_id: str) -> Dict[str, Any]:
        """
        Calculate relationship density metrics for a project.

        Returns:
            Dictionary with density metrics
        """
        query = """
            WITH entity_counts AS (
                SELECT COUNT(DISTINCT entity_id) as n
                FROM (
                    SELECT source_entity_id as entity_id FROM relationship_edges WHERE project_id = %s AND is_active = TRUE
                    UNION
                    SELECT target_entity_id as entity_id FROM relationship_edges WHERE project_id = %s AND is_active = TRUE
                ) entities
            ),
            edge_counts AS (
                SELECT COUNT(*) as m
                FROM relationship_edges
                WHERE project_id = %s AND is_active = TRUE
            )
            SELECT
                n as node_count,
                m as edge_count,
                CASE
                    WHEN n > 1 THEN m::float / (n * (n - 1))
                    ELSE 0
                END as density,
                CASE
                    WHEN n > 0 THEN m::float / n
                    ELSE 0
                END as avg_degree
            FROM entity_counts, edge_counts
        """

        result = execute_query(query, (project_id, project_id, project_id))

        if result:
            return {
                'node_count': result[0]['node_count'],
                'edge_count': result[0]['edge_count'],
                'density': float(result[0]['density']),
                'average_degree': float(result[0]['avg_degree']),
                'interpretation': self._interpret_density(float(result[0]['density']))
            }

        return {
            'node_count': 0,
            'edge_count': 0,
            'density': 0.0,
            'average_degree': 0.0,
            'interpretation': 'No relationships found'
        }

    def _interpret_density(self, density: float) -> str:
        """Provide interpretation of density metric"""
        if density < 0.1:
            return 'Sparse - Most entities are isolated or have few connections'
        elif density < 0.3:
            return 'Moderate - Reasonable connectivity between entities'
        elif density < 0.6:
            return 'Dense - Entities are well-connected'
        else:
            return 'Very Dense - Highly interconnected graph'

    def get_relationship_coverage(self, project_id: str) -> Dict[str, Any]:
        """
        Calculate relationship coverage metrics.

        Returns:
            Dictionary with coverage statistics by entity type
        """
        # Get total entities by type (entities that have at least one relationship)
        query = """
            SELECT
                entity_type,
                COUNT(DISTINCT entity_id) as connected_count
            FROM (
                SELECT source_entity_type as entity_type, source_entity_id as entity_id
                FROM relationship_edges
                WHERE project_id = %s AND is_active = TRUE
                UNION
                SELECT target_entity_type as entity_type, target_entity_id as entity_id
                FROM relationship_edges
                WHERE project_id = %s AND is_active = TRUE
            ) entities
            GROUP BY entity_type
            ORDER BY entity_type
        """

        results = execute_query(query, (project_id, project_id))

        coverage = []
        total_connected = 0

        for row in results:
            total_connected += row['connected_count']
            coverage.append({
                'entity_type': row['entity_type'],
                'connected_count': row['connected_count'],
                # Note: To get total_count and coverage_percentage, we'd need to query each entity table
                # This is a simplified version showing only connected entities
            })

        return {
            'total_connected_entities': total_connected,
            'by_type': coverage
        }

    # ============================================================================
    # MISSING RELATIONSHIPS
    # ============================================================================

    def find_missing_relationships(
        self,
        project_id: str,
        entity_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find entities that likely should have relationships but don't.

        This uses validation rules to identify missing required relationships.

        Args:
            project_id: Project UUID
            entity_type: Optional entity type filter

        Returns:
            List of entities missing expected relationships
        """
        # Get required relationship rules
        query = """
            SELECT * FROM relationship_validation_rules
            WHERE (project_id = %s OR project_id IS NULL)
              AND rule_type IN ('required', 'cardinality')
              AND is_active = TRUE
        """

        params = [project_id]

        if entity_type:
            query += " AND source_entity_type = %s"
            params.append(entity_type)

        rules = execute_query(query, tuple(params))

        missing = []

        for rule in rules:
            # Find entities missing this relationship
            # This is a simplified check - full implementation would query entity tables
            if rule['rule_type'] == 'required':
                check_query = """
                    SELECT DISTINCT source_entity_id as entity_id, source_entity_type as entity_type
                    FROM relationship_edges
                    WHERE project_id = %s
                      AND source_entity_type = %s
                      AND is_active = TRUE

                    EXCEPT

                    SELECT DISTINCT source_entity_id as entity_id, source_entity_type as entity_type
                    FROM relationship_edges
                    WHERE project_id = %s
                      AND source_entity_type = %s
                      AND relationship_type = %s
                      AND is_active = TRUE
                """

                check_params = [
                    project_id,
                    rule['source_entity_type'],
                    project_id,
                    rule['source_entity_type'],
                    rule['relationship_type']
                ]

                results = execute_query(check_query, tuple(check_params))

                for result in results:
                    missing.append({
                        'entity_type': result['entity_type'],
                        'entity_id': str(result['entity_id']),
                        'missing_relationship_type': rule['relationship_type'],
                        'expected_target_type': rule.get('target_entity_type'),
                        'rule_name': rule['rule_name'],
                        'severity': rule['severity']
                    })

        return missing

    # ============================================================================
    # CONNECTION ANALYSIS
    # ============================================================================

    def get_most_connected_entities(
        self,
        project_id: str,
        limit: int = 10,
        entity_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get the most highly connected entities (hub nodes).

        Args:
            project_id: Project UUID
            limit: Maximum results to return
            entity_type: Optional entity type filter

        Returns:
            List of entities sorted by connection count
        """
        query = """
            SELECT * FROM vw_entity_relationship_counts
            WHERE project_id = %s
        """

        params = [project_id]

        if entity_type:
            query += " AND entity_type = %s"
            params.append(entity_type)

        query += " ORDER BY total_connections DESC LIMIT %s"
        params.append(limit)

        return execute_query(query, tuple(params))

    def get_least_connected_entities(
        self,
        project_id: str,
        limit: int = 10,
        entity_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get the least connected entities (potential orphans or isolated nodes).

        Args:
            project_id: Project UUID
            limit: Maximum results to return
            entity_type: Optional entity type filter

        Returns:
            List of entities sorted by connection count (ascending)
        """
        query = """
            SELECT * FROM vw_entity_relationship_counts
            WHERE project_id = %s
        """

        params = [project_id]

        if entity_type:
            query += " AND entity_type = %s"
            params.append(entity_type)

        query += " ORDER BY total_connections ASC, entity_type, entity_id LIMIT %s"
        params.append(limit)

        return execute_query(query, tuple(params))

    # ============================================================================
    # RELATIONSHIP TYPE ANALYSIS
    # ============================================================================

    def get_relationship_type_distribution(
        self,
        project_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get distribution of relationship types in a project.

        Args:
            project_id: Project UUID

        Returns:
            List of relationship types with counts and percentages
        """
        query = """
            WITH total AS (
                SELECT COUNT(*) as total_count
                FROM relationship_edges
                WHERE project_id = %s AND is_active = TRUE
            )
            SELECT
                relationship_type,
                COUNT(*) as count,
                COUNT(*)::float / total.total_count * 100 as percentage,
                AVG(relationship_strength) as avg_strength
            FROM relationship_edges, total
            WHERE project_id = %s AND is_active = TRUE
            GROUP BY relationship_type, total.total_count
            ORDER BY count DESC
        """

        return execute_query(query, (project_id, project_id))

    def get_entity_type_interactions(
        self,
        project_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get matrix of entity type interactions (which types connect to which).

        Args:
            project_id: Project UUID

        Returns:
            List of entity type pairs with connection counts
        """
        query = """
            SELECT
                source_entity_type,
                target_entity_type,
                COUNT(*) as connection_count,
                COUNT(DISTINCT relationship_type) as unique_relationship_types,
                AVG(relationship_strength) as avg_strength
            FROM relationship_edges
            WHERE project_id = %s AND is_active = TRUE
            GROUP BY source_entity_type, target_entity_type
            ORDER BY connection_count DESC
        """

        return execute_query(query, (project_id,))

    # ============================================================================
    # PROJECT COMPARISON
    # ============================================================================

    def compare_projects(
        self,
        project_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Compare relationship metrics across multiple projects.

        Args:
            project_ids: List of project UUIDs to compare

        Returns:
            Dictionary with comparative metrics
        """
        comparisons = []

        for project_id in project_ids:
            # Get basic metrics
            density = self.get_relationship_density(project_id)

            # Get relationship type distribution
            type_dist = self.get_relationship_type_distribution(project_id)

            # Get project info
            project_info = execute_query(
                "SELECT project_id, project_name FROM projects WHERE project_id = %s",
                (project_id,)
            )

            comparisons.append({
                'project_id': project_id,
                'project_name': project_info[0]['project_name'] if project_info else 'Unknown',
                'metrics': density,
                'relationship_types': len(type_dist),
                'type_distribution': type_dist
            })

        return {
            'projects': comparisons,
            'comparison_count': len(comparisons)
        }

    # ============================================================================
    # HEALTH METRICS
    # ============================================================================

    def get_project_health_score(self, project_id: str) -> Dict[str, Any]:
        """
        Calculate overall health score for project relationships.

        Args:
            project_id: Project UUID

        Returns:
            Dictionary with health score and contributing factors
        """
        # Get various metrics
        density_data = self.get_relationship_density(project_id)

        # Get violation count
        violation_query = """
            SELECT
                COUNT(*) as total_violations,
                COUNT(*) FILTER (WHERE severity = 'critical') as critical_violations,
                COUNT(*) FILTER (WHERE severity = 'error') as error_violations,
                COUNT(*) FILTER (WHERE status = 'open') as open_violations
            FROM relationship_validation_violations
            WHERE project_id = %s
        """
        violations = execute_query(violation_query, (project_id,))

        # Calculate health score (0-100)
        score = 100.0

        if violations:
            # Deduct for violations
            critical_count = violations[0]['critical_violations'] or 0
            error_count = violations[0]['error_violations'] or 0
            open_count = violations[0]['open_violations'] or 0

            score -= (critical_count * 20)  # -20 per critical
            score -= (error_count * 10)     # -10 per error
            score -= (open_count * 2)       # -2 per open violation

        # Adjust for density (very sparse or very dense both reduce score)
        density = density_data['density']
        if density < 0.05:
            score -= 20  # Too sparse
        elif density > 0.8:
            score -= 10  # Too dense

        score = max(0, min(100, score))  # Clamp to 0-100

        # Determine grade
        if score >= 90:
            grade = 'A'
            status = 'Excellent'
        elif score >= 80:
            grade = 'B'
            status = 'Good'
        elif score >= 70:
            grade = 'C'
            status = 'Fair'
        elif score >= 60:
            grade = 'D'
            status = 'Poor'
        else:
            grade = 'F'
            status = 'Critical'

        return {
            'health_score': round(score, 2),
            'grade': grade,
            'status': status,
            'metrics': {
                'density': density,
                'node_count': density_data['node_count'],
                'edge_count': density_data['edge_count'],
                'violations': violations[0] if violations else {}
            },
            'recommendations': self._generate_recommendations(score, density_data, violations[0] if violations else {})
        }

    def _generate_recommendations(
        self,
        score: float,
        density_data: Dict,
        violations: Dict
    ) -> List[str]:
        """Generate recommendations based on metrics"""
        recommendations = []

        if score < 70:
            recommendations.append("Review and resolve open violations to improve relationship quality")

        if density_data['density'] < 0.05:
            recommendations.append("Relationship density is very low - consider adding more entity connections")

        if density_data['density'] > 0.8:
            recommendations.append("Relationship density is very high - review if all connections are necessary")

        if violations.get('critical_violations', 0) > 0:
            recommendations.append("Address critical violations immediately")

        if violations.get('open_violations', 0) > 10:
            recommendations.append("Large number of open violations - prioritize resolution")

        if not recommendations:
            recommendations.append("Relationship graph is healthy - continue monitoring")

        return recommendations

    # ============================================================================
    # STATISTICS SUMMARY
    # ============================================================================

    def get_comprehensive_summary(self, project_id: str) -> Dict[str, Any]:
        """
        Get comprehensive summary of all relationship metrics.

        Args:
            project_id: Project UUID

        Returns:
            Dictionary with all major metrics
        """
        return {
            'density': self.get_relationship_density(project_id),
            'coverage': self.get_relationship_coverage(project_id),
            'type_distribution': self.get_relationship_type_distribution(project_id),
            'entity_interactions': self.get_entity_type_interactions(project_id),
            'most_connected': self.get_most_connected_entities(project_id, limit=5),
            'least_connected': self.get_least_connected_entities(project_id, limit=5),
            'health': self.get_project_health_score(project_id)
        }
