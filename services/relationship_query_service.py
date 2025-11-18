"""
Relationship Query Service
Graph traversal and querying operations for the relationship graph.

This service provides advanced querying capabilities including:
- Graph traversal (BFS/DFS)
- Path finding
- Subgraph extraction
- Orphan detection
- Cycle detection

References:
    - docs/PHASE_3_COMPREHENSIVE_ANALYSIS.md
    - database/migrations/022_create_relationship_edges.sql
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.db_utils import execute_query
from typing import Dict, List, Optional, Any, Set, Tuple
from collections import deque, defaultdict


class RelationshipQueryService:
    """Service for querying and traversing the relationship graph"""

    def __init__(self):
        pass

    # ============================================================================
    # BASIC QUERIES
    # ============================================================================

    def get_related_entities(
        self,
        entity_type: str,
        entity_id: str,
        project_id: Optional[str] = None,
        relationship_type: Optional[str] = None,
        direction: str = 'both'
    ) -> List[Dict[str, Any]]:
        """
        Get all entities directly related to a given entity.

        Args:
            entity_type: Type of the entity
            entity_id: UUID of the entity
            project_id: Optional project filter
            relationship_type: Optional relationship type filter
            direction: 'outgoing', 'incoming', or 'both'

        Returns:
            List of related entities with relationship details
        """
        query = """
            SELECT * FROM get_related_entities(%s, %s, %s, %s)
        """

        params = (entity_type, entity_id, relationship_type, direction)

        results = execute_query(query, params)

        # If project_id is specified, filter results
        if project_id:
            # Get edge details to filter by project
            filtered_results = []
            for result in results:
                edge_query = "SELECT project_id FROM relationship_edges WHERE edge_id = %s"
                edge_data = execute_query(edge_query, (result['edge_id'],))
                if edge_data and str(edge_data[0]['project_id']) == str(project_id):
                    filtered_results.append(result)
            return filtered_results

        return results

    def get_entity_subgraph(
        self,
        entity_type: str,
        entity_id: str,
        project_id: str,
        depth: int = 2,
        relationship_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Extract a subgraph centered on an entity up to a given depth.

        Args:
            entity_type: Type of the entity
            entity_id: UUID of the entity
            project_id: Project UUID
            depth: Maximum traversal depth
            relationship_types: Optional list of relationship types to include

        Returns:
            Dictionary with 'nodes' and 'edges' representing the subgraph
        """
        nodes = {}
        edges = []
        visited = set()
        queue = deque([(entity_type, entity_id, 0)])  # (type, id, current_depth)

        # Add root node
        nodes[f"{entity_type}:{entity_id}"] = {
            'entity_type': entity_type,
            'entity_id': entity_id,
            'depth': 0
        }
        visited.add(f"{entity_type}:{entity_id}")

        while queue:
            curr_type, curr_id, curr_depth = queue.popleft()

            if curr_depth >= depth:
                continue

            # Get all edges from this node
            edge_query = """
                SELECT * FROM relationship_edges
                WHERE project_id = %s
                  AND is_active = TRUE
                  AND (
                    (source_entity_type = %s AND source_entity_id = %s)
                    OR
                    (target_entity_type = %s AND target_entity_id = %s AND is_bidirectional = TRUE)
                  )
            """
            params = [project_id, curr_type, str(curr_id), curr_type, str(curr_id)]

            if relationship_types:
                edge_query += " AND relationship_type = ANY(%s)"
                params.append(relationship_types)

            edge_results = execute_query(edge_query, tuple(params))

            for edge in edge_results:
                # Determine the connected node
                if edge['source_entity_type'] == curr_type and str(edge['source_entity_id']) == str(curr_id):
                    connected_type = edge['target_entity_type']
                    connected_id = edge['target_entity_id']
                    direction = 'outgoing'
                else:
                    connected_type = edge['source_entity_type']
                    connected_id = edge['source_entity_id']
                    direction = 'incoming'

                node_key = f"{connected_type}:{connected_id}"

                # Add edge to results
                edges.append({
                    'edge_id': edge['edge_id'],
                    'source_entity_type': edge['source_entity_type'],
                    'source_entity_id': edge['source_entity_id'],
                    'target_entity_type': edge['target_entity_type'],
                    'target_entity_id': edge['target_entity_id'],
                    'relationship_type': edge['relationship_type'],
                    'relationship_strength': edge['relationship_strength'],
                    'direction': direction
                })

                # Add connected node if not visited
                if node_key not in visited:
                    visited.add(node_key)
                    nodes[node_key] = {
                        'entity_type': connected_type,
                        'entity_id': str(connected_id),
                        'depth': curr_depth + 1
                    }
                    queue.append((connected_type, str(connected_id), curr_depth + 1))

        return {
            'nodes': list(nodes.values()),
            'edges': edges,
            'node_count': len(nodes),
            'edge_count': len(edges)
        }

    # ============================================================================
    # PATH FINDING
    # ============================================================================

    def find_path(
        self,
        project_id: str,
        source_entity_type: str,
        source_entity_id: str,
        target_entity_type: str,
        target_entity_id: str,
        max_depth: int = 5
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Find shortest path between two entities using BFS.

        Args:
            project_id: Project UUID
            source_entity_type: Type of source entity
            source_entity_id: UUID of source entity
            target_entity_type: Type of target entity
            target_entity_id: UUID of target entity
            max_depth: Maximum path length to search

        Returns:
            List of edges forming the path, or None if no path found
        """
        source_key = f"{source_entity_type}:{source_entity_id}"
        target_key = f"{target_entity_type}:{target_entity_id}"

        if source_key == target_key:
            return []  # Same entity

        visited = set([source_key])
        queue = deque([(source_key, [])])  # (node_key, path)

        while queue:
            curr_key, path = queue.popleft()

            if len(path) >= max_depth:
                continue

            curr_type, curr_id = curr_key.split(':', 1)

            # Get edges from current node
            edge_query = """
                SELECT * FROM relationship_edges
                WHERE project_id = %s
                  AND is_active = TRUE
                  AND (
                    (source_entity_type = %s AND source_entity_id = %s)
                    OR
                    (target_entity_type = %s AND target_entity_id = %s AND is_bidirectional = TRUE)
                  )
            """
            edges = execute_query(edge_query, (project_id, curr_type, curr_id, curr_type, curr_id))

            for edge in edges:
                # Determine next node
                if edge['source_entity_type'] == curr_type and str(edge['source_entity_id']) == str(curr_id):
                    next_type = edge['target_entity_type']
                    next_id = edge['target_entity_id']
                else:
                    next_type = edge['source_entity_type']
                    next_id = edge['source_entity_id']

                next_key = f"{next_type}:{next_id}"

                if next_key == target_key:
                    # Found path!
                    return path + [edge]

                if next_key not in visited:
                    visited.add(next_key)
                    queue.append((next_key, path + [edge]))

        return None  # No path found

    def find_all_paths(
        self,
        project_id: str,
        source_entity_type: str,
        source_entity_id: str,
        target_entity_type: str,
        target_entity_id: str,
        max_depth: int = 4,
        max_paths: int = 10
    ) -> List[List[Dict[str, Any]]]:
        """
        Find all paths between two entities up to max_depth.

        Args:
            project_id: Project UUID
            source_entity_type: Type of source entity
            source_entity_id: UUID of source entity
            target_entity_type: Type of target entity
            target_entity_id: UUID of target entity
            max_depth: Maximum path length
            max_paths: Maximum number of paths to return

        Returns:
            List of paths (each path is a list of edges)
        """
        source_key = f"{source_entity_type}:{source_entity_id}"
        target_key = f"{target_entity_type}:{target_entity_id}"

        if source_key == target_key:
            return [[]]  # Same entity

        paths = []

        def dfs(curr_key: str, path: List[Dict], visited: Set[str]):
            if len(paths) >= max_paths or len(path) >= max_depth:
                return

            if curr_key == target_key:
                paths.append(list(path))
                return

            curr_type, curr_id = curr_key.split(':', 1)
            visited.add(curr_key)

            # Get edges from current node
            edge_query = """
                SELECT * FROM relationship_edges
                WHERE project_id = %s
                  AND is_active = TRUE
                  AND (
                    (source_entity_type = %s AND source_entity_id = %s)
                    OR
                    (target_entity_type = %s AND target_entity_id = %s AND is_bidirectional = TRUE)
                  )
            """
            edges = execute_query(edge_query, (project_id, curr_type, curr_id, curr_type, curr_id))

            for edge in edges:
                # Determine next node
                if edge['source_entity_type'] == curr_type and str(edge['source_entity_id']) == str(curr_id):
                    next_type = edge['target_entity_type']
                    next_id = edge['target_entity_id']
                else:
                    next_type = edge['source_entity_type']
                    next_id = edge['source_entity_id']

                next_key = f"{next_type}:{next_id}"

                if next_key not in visited:
                    dfs(next_key, path + [edge], visited.copy())

        dfs(source_key, [], set())
        return paths

    # ============================================================================
    # GRAPH ANALYSIS
    # ============================================================================

    def find_orphans(
        self,
        project_id: str,
        entity_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find entities with no relationships (orphaned nodes).

        Note: This returns entities that HAVE relationships in the graph.
        To find truly orphaned entities, you'd need to query entity tables
        and compare against this result.

        Args:
            project_id: Project UUID
            entity_type: Optional entity type filter

        Returns:
            List of entity references that appear in the relationship graph
        """
        query = """
            SELECT DISTINCT entity_type, entity_id
            FROM (
                SELECT source_entity_type as entity_type, source_entity_id as entity_id
                FROM relationship_edges
                WHERE project_id = %s AND is_active = TRUE
                UNION
                SELECT target_entity_type as entity_type, target_entity_id as entity_id
                FROM relationship_edges
                WHERE project_id = %s AND is_active = TRUE
            ) entities
        """

        params = [project_id, project_id]

        if entity_type:
            query += " WHERE entity_type = %s"
            params.append(entity_type)

        query += " ORDER BY entity_type, entity_id"

        return execute_query(query, tuple(params))

    def detect_cycles(self, project_id: str) -> List[List[Dict[str, Any]]]:
        """
        Detect cycles in the relationship graph.

        Args:
            project_id: Project UUID

        Returns:
            List of cycles (each cycle is a list of edges forming a loop)
        """
        # Get all edges for the project
        edges_query = """
            SELECT * FROM relationship_edges
            WHERE project_id = %s AND is_active = TRUE
            ORDER BY source_entity_type, source_entity_id
        """
        all_edges = execute_query(edges_query, (project_id,))

        # Build adjacency list
        graph = defaultdict(list)
        edge_map = {}

        for edge in all_edges:
            source_key = f"{edge['source_entity_type']}:{edge['source_entity_id']}"
            target_key = f"{edge['target_entity_type']}:{edge['target_entity_id']}"
            graph[source_key].append(target_key)
            edge_map[(source_key, target_key)] = edge

            # Add reverse edge if bidirectional
            if edge['is_bidirectional']:
                graph[target_key].append(source_key)
                edge_map[(target_key, source_key)] = edge

        # DFS-based cycle detection
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs_cycle(node: str, path: List[str]):
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph[node]:
                if neighbor not in visited:
                    if dfs_cycle(neighbor, path + [node]):
                        return True
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor) if neighbor in path else 0
                    cycle_path = path[cycle_start:] + [node, neighbor]

                    # Convert path to edges
                    cycle_edges = []
                    for i in range(len(cycle_path) - 1):
                        edge_key = (cycle_path[i], cycle_path[i + 1])
                        if edge_key in edge_map:
                            cycle_edges.append(edge_map[edge_key])

                    if cycle_edges and cycle_edges not in cycles:
                        cycles.append(cycle_edges)

            rec_stack.remove(node)
            return False

        # Check all nodes
        for node in graph.keys():
            if node not in visited:
                dfs_cycle(node, [])

        return cycles

    def get_entity_connections_count(
        self,
        project_id: str,
        entity_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get connection counts for entities (node degree).

        Args:
            project_id: Project UUID
            entity_type: Optional entity type filter

        Returns:
            List of entities with their incoming, outgoing, and total connection counts
        """
        query = """
            SELECT * FROM vw_entity_relationship_counts
            WHERE project_id = %s
        """

        params = [project_id]

        if entity_type:
            query += " AND entity_type = %s"
            params.append(entity_type)

        query += " ORDER BY total_connections DESC, entity_type, entity_id"

        return execute_query(query, tuple(params))

    def get_most_connected_entities(
        self,
        project_id: str,
        limit: int = 10,
        entity_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get the most highly connected entities (highest node degree).

        Args:
            project_id: Project UUID
            limit: Maximum results to return
            entity_type: Optional entity type filter

        Returns:
            List of entities sorted by connection count (descending)
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

    # ============================================================================
    # STATISTICS & ANALYTICS
    # ============================================================================

    def get_relationship_summary(self, project_id: str) -> Dict[str, Any]:
        """
        Get summary statistics for all relationships in a project.

        Args:
            project_id: Project UUID

        Returns:
            Dictionary with various relationship statistics
        """
        # Get counts by relationship type
        type_summary = execute_query(
            "SELECT * FROM vw_relationship_summary_by_type WHERE project_id = %s",
            (project_id,)
        )

        # Get overall counts
        overall = execute_query(
            """
            SELECT
                COUNT(*) as total_edges,
                COUNT(DISTINCT source_entity_id) + COUNT(DISTINCT target_entity_id) as total_entities,
                COUNT(DISTINCT relationship_type) as unique_relationship_types,
                AVG(relationship_strength) as avg_strength,
                COUNT(*) FILTER (WHERE is_bidirectional = TRUE) as bidirectional_count
            FROM relationship_edges
            WHERE project_id = %s AND is_active = TRUE
            """,
            (project_id,)
        )

        return {
            'overall': overall[0] if overall else {},
            'by_type': type_summary
        }

    def get_relationship_density(self, project_id: str) -> float:
        """
        Calculate relationship density for a project.
        Density = actual_edges / possible_edges

        Args:
            project_id: Project UUID

        Returns:
            Density value between 0.0 and 1.0
        """
        result = execute_query(
            """
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
                CASE
                    WHEN n > 1 THEN m::float / (n * (n - 1))
                    ELSE 0
                END as density
            FROM entity_counts, edge_counts
            """,
            (project_id, project_id, project_id)
        )

        return result[0]['density'] if result else 0.0
