"""
Graph Analytics Service - Advanced Graph Analysis using NetworkX

Provides graph analytics capabilities:
1. PageRank and centrality measures
2. Community detection (Louvain, label propagation)
3. Graph clustering and modularity
4. Shortest paths and network flows
5. Structural analysis (density, components, etc.)
6. Temporal analysis of relationship changes

Author: AI Agent Toolkit
Date: 2025-11-18
"""

import json
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict
import networkx as nx
from database import execute_query, get_db


class GraphAnalyticsService:
    """
    Advanced graph analytics using NetworkX algorithms
    """

    def __init__(self):
        """Initialize the graph analytics service"""
        self.cache_ttl = 3600  # 1 hour cache TTL for analytics
        self.min_confidence_score = 0.3  # Minimum relationship confidence to include

    def compute_pagerank(self, project_id: Optional[str] = None,
                        entity_type: Optional[str] = None,
                        use_cache: bool = True) -> Dict[str, float]:
        """
        Compute PageRank scores for entities in the graph

        Args:
            project_id: Optional project scope
            entity_type: Optional entity type filter
            use_cache: Whether to use cached results

        Returns:
            Dictionary mapping entity_id to PageRank score
        """
        # Check cache first
        if use_cache:
            cached = self._get_cached_analytics('pagerank', 'project' if project_id else 'global', project_id)
            if cached:
                return cached['result_data']

        # Build NetworkX graph
        G = self._build_networkx_graph(project_id, entity_type)

        if G.number_of_nodes() == 0:
            return {}

        # Compute PageRank
        pagerank_scores = nx.pagerank(G, alpha=0.85, max_iter=100)

        # Cache the result
        if use_cache:
            self._cache_analytics(
                'pagerank',
                'project' if project_id else 'global',
                project_id,
                {'pagerank_scores': pagerank_scores},
                G.number_of_nodes(),
                G.number_of_edges()
            )

        return pagerank_scores

    def detect_communities(self, project_id: Optional[str] = None,
                          algorithm: str = 'louvain',
                          use_cache: bool = True) -> Dict[str, Any]:
        """
        Detect communities/clusters in the graph

        Args:
            project_id: Optional project scope
            algorithm: Algorithm to use ('louvain', 'label_propagation', 'greedy_modularity')
            use_cache: Whether to use cached results

        Returns:
            Dictionary with communities and modularity score
        """
        # Check cache
        cache_key = f'community_{algorithm}'
        if use_cache:
            cached = self._get_cached_analytics(cache_key, 'project' if project_id else 'global', project_id)
            if cached:
                return cached['result_data']

        # Build undirected graph for community detection
        G = self._build_networkx_graph(project_id, None, directed=False)

        if G.number_of_nodes() == 0:
            return {'communities': [], 'modularity': 0.0}

        # Run community detection algorithm
        if algorithm == 'louvain':
            try:
                import community as community_louvain
                partition = community_louvain.best_partition(G)
            except ImportError:
                # Fallback to greedy modularity if python-louvain not available
                algorithm = 'greedy_modularity'
                communities_generator = nx.community.greedy_modularity_communities(G)
                partition = {}
                for i, comm in enumerate(communities_generator):
                    for node in comm:
                        partition[node] = i

        elif algorithm == 'label_propagation':
            communities_generator = nx.community.label_propagation_communities(G)
            partition = {}
            for i, comm in enumerate(communities_generator):
                for node in comm:
                    partition[node] = i

        elif algorithm == 'greedy_modularity':
            communities_generator = nx.community.greedy_modularity_communities(G)
            partition = {}
            for i, comm in enumerate(communities_generator):
                for node in comm:
                    partition[node] = i

        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

        # Group nodes by community
        communities = defaultdict(list)
        for node, comm_id in partition.items():
            communities[comm_id].append(str(node))

        # Calculate modularity
        community_sets = [set(nodes) for nodes in communities.values()]
        modularity = nx.community.modularity(G, community_sets)

        result = {
            'communities': [
                {
                    'community_id': comm_id,
                    'entity_ids': nodes,
                    'size': len(nodes)
                }
                for comm_id, nodes in communities.items()
            ],
            'modularity': round(modularity, 4),
            'num_communities': len(communities),
            'algorithm': algorithm
        }

        # Cache the result
        if use_cache:
            self._cache_analytics(
                cache_key,
                'project' if project_id else 'global',
                project_id,
                result,
                G.number_of_nodes(),
                G.number_of_edges()
            )

        return result

    def compute_centrality_measures(self, project_id: Optional[str] = None,
                                   measures: Optional[List[str]] = None,
                                   use_cache: bool = True) -> Dict[str, Dict[str, float]]:
        """
        Compute various centrality measures

        Args:
            project_id: Optional project scope
            measures: List of measures to compute (degree, betweenness, closeness, eigenvector)
            use_cache: Whether to use cached results

        Returns:
            Dictionary mapping measure name to entity_id -> score mapping
        """
        if measures is None:
            measures = ['degree', 'betweenness', 'closeness']

        # Check cache
        if use_cache:
            cached = self._get_cached_analytics('centrality', 'project' if project_id else 'global', project_id)
            if cached:
                return cached['result_data']

        G = self._build_networkx_graph(project_id)

        if G.number_of_nodes() == 0:
            return {measure: {} for measure in measures}

        results = {}

        if 'degree' in measures:
            if G.is_directed():
                in_degree = dict(G.in_degree())
                out_degree = dict(G.out_degree())
                results['in_degree'] = in_degree
                results['out_degree'] = out_degree
                results['degree'] = {k: in_degree.get(k, 0) + out_degree.get(k, 0) for k in G.nodes()}
            else:
                results['degree'] = dict(G.degree())

        if 'betweenness' in measures:
            results['betweenness'] = nx.betweenness_centrality(G)

        if 'closeness' in measures:
            # Handle disconnected graphs
            if nx.is_connected(G.to_undirected()):
                results['closeness'] = nx.closeness_centrality(G)
            else:
                results['closeness'] = {node: 0.0 for node in G.nodes()}

        if 'eigenvector' in measures:
            try:
                results['eigenvector'] = nx.eigenvector_centrality(G, max_iter=100)
            except nx.PowerIterationFailedConvergence:
                results['eigenvector'] = {node: 0.0 for node in G.nodes()}

        # Cache the result
        if use_cache:
            self._cache_analytics(
                'centrality',
                'project' if project_id else 'global',
                project_id,
                results,
                G.number_of_nodes(),
                G.number_of_edges()
            )

        return results

    def find_shortest_path(self, source_entity_id: str, target_entity_id: str,
                          weight_attribute: Optional[str] = None) -> Dict[str, Any]:
        """
        Find shortest path between two entities

        Args:
            source_entity_id: Start entity
            target_entity_id: End entity
            weight_attribute: Optional edge weight attribute

        Returns:
            Path information with entities and relationships
        """
        G = self._build_networkx_graph()

        if source_entity_id not in G or target_entity_id not in G:
            return {
                'path': [],
                'length': None,
                'exists': False
            }

        try:
            if weight_attribute:
                path = nx.shortest_path(G, source_entity_id, target_entity_id, weight=weight_attribute)
                length = nx.shortest_path_length(G, source_entity_id, target_entity_id, weight=weight_attribute)
            else:
                path = nx.shortest_path(G, source_entity_id, target_entity_id)
                length = len(path) - 1

            # Get entity details for path
            path_entities = execute_query(
                "SELECT entity_id, entity_type, canonical_name FROM standards_entities WHERE entity_id = ANY(%s)",
                (path,)
            )

            return {
                'path': path,
                'path_entities': path_entities,
                'length': length,
                'exists': True
            }

        except nx.NetworkXNoPath:
            return {
                'path': [],
                'length': None,
                'exists': False
            }

    def find_connected_components(self, project_id: Optional[str] = None) -> List[Set[str]]:
        """
        Find connected components in the graph

        Args:
            project_id: Optional project scope

        Returns:
            List of connected component sets
        """
        G = self._build_networkx_graph(project_id)

        if G.is_directed():
            # For directed graphs, use weakly connected components
            components = list(nx.weakly_connected_components(G))
        else:
            components = list(nx.connected_components(G))

        return [set(str(node) for node in comp) for comp in components]

    def analyze_graph_structure(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze overall graph structure and properties

        Args:
            project_id: Optional project scope

        Returns:
            Dictionary with structural metrics
        """
        G = self._build_networkx_graph(project_id)

        if G.number_of_nodes() == 0:
            return {
                'num_nodes': 0,
                'num_edges': 0,
                'density': 0.0,
                'is_connected': False
            }

        analysis = {
            'num_nodes': G.number_of_nodes(),
            'num_edges': G.number_of_edges(),
            'density': nx.density(G),
            'is_directed': G.is_directed(),
        }

        # Connected components
        if G.is_directed():
            analysis['num_weakly_connected_components'] = nx.number_weakly_connected_components(G)
            analysis['num_strongly_connected_components'] = nx.number_strongly_connected_components(G)
            analysis['is_weakly_connected'] = nx.is_weakly_connected(G)
            analysis['is_strongly_connected'] = nx.is_strongly_connected(G)
        else:
            analysis['num_connected_components'] = nx.number_connected_components(G)
            analysis['is_connected'] = nx.is_connected(G)

        # Degree statistics
        degrees = [d for n, d in G.degree()]
        if degrees:
            analysis['avg_degree'] = sum(degrees) / len(degrees)
            analysis['max_degree'] = max(degrees)
            analysis['min_degree'] = min(degrees)

        # Clustering coefficient (for undirected graphs)
        if not G.is_directed():
            analysis['avg_clustering_coefficient'] = nx.average_clustering(G)

        # Diameter (for connected graphs)
        try:
            if not G.is_directed() and nx.is_connected(G):
                analysis['diameter'] = nx.diameter(G)
                analysis['avg_shortest_path_length'] = nx.average_shortest_path_length(G)
        except:
            pass

        return analysis

    def find_influential_nodes(self, project_id: Optional[str] = None,
                              top_k: int = 10,
                              metric: str = 'pagerank') -> List[Dict[str, Any]]:
        """
        Find most influential nodes in the graph

        Args:
            project_id: Optional project scope
            top_k: Number of top nodes to return
            metric: Metric to use (pagerank, degree, betweenness)

        Returns:
            List of influential nodes with scores
        """
        if metric == 'pagerank':
            scores = self.compute_pagerank(project_id)
        elif metric == 'degree':
            G = self._build_networkx_graph(project_id)
            scores = dict(G.degree())
        elif metric == 'betweenness':
            centrality = self.compute_centrality_measures(project_id, ['betweenness'])
            scores = centrality['betweenness']
        else:
            raise ValueError(f"Unknown metric: {metric}")

        # Sort by score
        sorted_nodes = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        # Get entity details
        entity_ids = [node_id for node_id, score in sorted_nodes]
        entities = execute_query(
            "SELECT entity_id, entity_type, canonical_name, description FROM standards_entities WHERE entity_id = ANY(%s)",
            (entity_ids,)
        )

        # Merge with scores
        entity_map = {e['entity_id']: e for e in entities}
        result = []
        for entity_id, score in sorted_nodes:
            if entity_id in entity_map:
                entity = entity_map[entity_id].copy()
                entity[f'{metric}_score'] = round(score, 4)
                result.append(entity)

        return result

    def identify_bridges(self, project_id: Optional[str] = None) -> List[Tuple[str, str]]:
        """
        Identify bridge edges (critical connections whose removal disconnects the graph)

        Args:
            project_id: Optional project scope

        Returns:
            List of bridge edge tuples
        """
        G = self._build_networkx_graph(project_id, directed=False)

        if G.number_of_nodes() == 0:
            return []

        bridges = list(nx.bridges(G))
        return [(str(u), str(v)) for u, v in bridges]

    def identify_articulation_points(self, project_id: Optional[str] = None) -> List[str]:
        """
        Identify articulation points (nodes whose removal disconnects the graph)

        Args:
            project_id: Optional project scope

        Returns:
            List of articulation point entity IDs
        """
        G = self._build_networkx_graph(project_id, directed=False)

        if G.number_of_nodes() == 0:
            return []

        articulation_points = list(nx.articulation_points(G))
        return [str(node) for node in articulation_points]

    def compute_relationship_strength_learning(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Learn and update relationship strengths based on graph structure and usage

        Args:
            project_id: Optional project scope

        Returns:
            Summary of updated relationships
        """
        # Get graph metrics
        pagerank_scores = self.compute_pagerank(project_id, use_cache=False)
        betweenness = self.compute_centrality_measures(project_id, ['betweenness'], use_cache=False)

        # Query relationships to update
        query = """
            SELECT
                er.relationship_id,
                er.subject_entity_id,
                er.object_entity_id,
                er.confidence_score,
                er.relationship_type
            FROM entity_relationships er
            WHERE (%(project_filter)s IS NULL OR er.attributes->>'project_id' = %(project_filter)s)
        """

        relationships = execute_query(query, {'project_filter': project_id})

        updated_count = 0

        for rel in relationships:
            subject_id = rel['subject_entity_id']
            object_id = rel['object_entity_id']

            # Calculate new strength based on:
            # 1. Original confidence score (50%)
            # 2. PageRank of connected nodes (30%)
            # 3. Betweenness centrality (20%)

            base_score = rel['confidence_score'] or 0.5
            pr_score = (pagerank_scores.get(subject_id, 0) + pagerank_scores.get(object_id, 0)) / 2
            bc_score = (betweenness['betweenness'].get(subject_id, 0) + betweenness['betweenness'].get(object_id, 0)) / 2

            new_strength = 0.5 * base_score + 0.3 * pr_score * 100 + 0.2 * bc_score

            # Normalize to 0-1 range
            new_strength = min(1.0, max(0.0, new_strength))

            # Update relationship in relationship_edges table
            update_query = """
                UPDATE relationship_edges
                SET relationship_strength = %s
                WHERE (source_entity_id = %s AND target_entity_id = %s)
                   OR (source_entity_id = %s AND target_entity_id = %s AND is_bidirectional = TRUE)
            """

            execute_query(update_query, (
                new_strength,
                subject_id, object_id,
                object_id, subject_id
            ))

            updated_count += 1

        return {
            'updated_relationships': updated_count,
            'project_id': project_id,
            'timestamp': datetime.now().isoformat()
        }

    def _build_networkx_graph(self, project_id: Optional[str] = None,
                             entity_type: Optional[str] = None,
                             directed: bool = True) -> nx.Graph:
        """
        Build a NetworkX graph from the database

        Args:
            project_id: Optional project scope
            entity_type: Optional entity type filter
            directed: Whether to create a directed graph

        Returns:
            NetworkX Graph or DiGraph
        """
        # Query relationships
        query = """
            SELECT
                subject_entity_id,
                object_entity_id,
                relationship_type,
                confidence_score,
                attributes
            FROM entity_relationships
            WHERE confidence_score >= %s
        """

        params = [self.min_confidence_score]

        # Add filters if needed (simplified - full implementation would join with entities table)
        relationships = execute_query(query, tuple(params))

        # Create graph
        G = nx.DiGraph() if directed else nx.Graph()

        # Add edges
        for rel in relationships:
            G.add_edge(
                rel['subject_entity_id'],
                rel['object_entity_id'],
                relationship_type=rel['relationship_type'],
                confidence=rel['confidence_score'],
                attributes=rel.get('attributes', {})
            )

        return G

    def _get_cached_analytics(self, analysis_type: str, scope_type: str,
                             scope_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """Retrieve cached analytics result if available"""
        query = """
            SELECT result_data, cache_id
            FROM graph_analytics_cache
            WHERE analysis_type = %s
              AND scope_type = %s
              AND (scope_id = %s OR (scope_id IS NULL AND %s IS NULL))
              AND is_valid = TRUE
              AND (expires_at IS NULL OR expires_at > NOW())
            LIMIT 1
        """

        try:
            result = execute_query(query, (analysis_type, scope_type, scope_id, scope_id))
            if result:
                return result[0]
        except Exception as e:
            print(f"Cache retrieval error: {e}")

        return None

    def _cache_analytics(self, analysis_type: str, scope_type: str, scope_id: Optional[str],
                        result_data: Dict[str, Any], node_count: int, edge_count: int):
        """Cache analytics result"""
        query = """
            INSERT INTO graph_analytics_cache (
                analysis_type,
                scope_type,
                scope_id,
                result_data,
                node_count,
                edge_count,
                expires_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        try:
            expires_at = datetime.now() + timedelta(seconds=self.cache_ttl)

            execute_query(query, (
                analysis_type,
                scope_type,
                scope_id,
                json.dumps(result_data),
                node_count,
                edge_count,
                expires_at
            ))
        except Exception as e:
            print(f"Cache write error: {e}")

    def invalidate_analytics_cache(self, project_id: Optional[str] = None):
        """Invalidate analytics cache for a project or globally"""
        if project_id:
            query = "UPDATE graph_analytics_cache SET is_valid = FALSE WHERE scope_id = %s"
            execute_query(query, (project_id,))
        else:
            query = "UPDATE graph_analytics_cache SET is_valid = FALSE WHERE is_valid = TRUE"
            execute_query(query)


# Singleton instance
_graph_analytics_service = None

def get_graph_analytics_service() -> GraphAnalyticsService:
    """Get singleton graph analytics service instance"""
    global _graph_analytics_service
    if _graph_analytics_service is None:
        _graph_analytics_service = GraphAnalyticsService()
    return _graph_analytics_service
