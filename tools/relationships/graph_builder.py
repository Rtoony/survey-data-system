"""
Relationship Graph Builder Module

Automatically detect and create spatial, engineering, and semantic relationships
between entities for GraphRAG traversal.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

sys.path.append(str(Path(__file__).parent.parent))

from db_utils import execute_query, execute_many, generate_uuid


class GraphBuilder:
    """Build knowledge graph relationships for GraphRAG."""
    
    def __init__(self):
        self.stats = {
            'spatial_relationships': 0,
            'engineering_relationships': 0,
            'semantic_relationships': 0,
            'errors': []
        }
    
    def create_spatial_relationships(
        self,
        source_table: str,
        target_table: str,
        relationship_type: str,
        distance_threshold: float = 10.0,
        source_id_col: str = 'entity_id',
        target_id_col: str = 'entity_id',
        geometry_col: str = 'geometry'
    ) -> int:
        """
        Create spatial relationships between two tables.
        
        Args:
            source_table: Source table name
            target_table: Target table name
            relationship_type: 'adjacent_to', 'contains', 'within', 'intersects'
            distance_threshold: Maximum distance for relationship (in map units)
            source_id_col: Entity ID column in source table
            target_id_col: Entity ID column in target table
            geometry_col: Geometry column name (default: 'geometry')
            
        Returns:
            Number of relationships created
        """
        # Build spatial query based on relationship type
        spatial_conditions = {
            'adjacent_to': f'ST_DWithin(s.{geometry_col}, t.{geometry_col}, {distance_threshold})',
            'contains': f'ST_Contains(s.{geometry_col}, t.{geometry_col})',
            'within': f'ST_Within(s.{geometry_col}, t.{geometry_col})',
            'intersects': f'ST_Intersects(s.{geometry_col}, t.{geometry_col})'
        }
        
        if relationship_type not in spatial_conditions:
            raise ValueError(f"Unknown relationship type: {relationship_type}")
        
        condition = spatial_conditions[relationship_type]
        
        # Find spatial relationships
        query = f"""
            INSERT INTO entity_relationships (
                relationship_id, subject_entity_id, object_entity_id,
                relationship_type, predicate, spatial_relationship, confidence_score
            )
            SELECT 
                gen_random_uuid(),
                s.{source_id_col},
                t.{target_id_col},
                %s,
                %s,
                true,
                0.95
            FROM {source_table} s
            JOIN {target_table} t ON {condition}
            WHERE s.{source_id_col} IS NOT NULL 
              AND t.{target_id_col} IS NOT NULL
              AND s.{source_id_col} != t.{target_id_col}
            ON CONFLICT DO NOTHING
        """
        
        try:
            execute_query(query, ('spatial', relationship_type), fetch=False)
            
            # Count new relationships
            count_query = """
                SELECT COUNT(*) as count FROM entity_relationships
                WHERE relationship_type = 'spatial' AND predicate = %s
            """
            result = execute_query(count_query, (relationship_type,))
            count = result[0]['count'] if result else 0
            
            self.stats['spatial_relationships'] += count
            return count
            
        except Exception as e:
            self.stats['errors'].append(f"Spatial relationship error: {str(e)}")
            return 0
    
    def create_engineering_relationships(
        self,
        relationship_rules: List[Dict[str, Any]]
    ) -> int:
        """
        Create engineering relationships based on domain logic.
        
        Args:
            relationship_rules: List of dicts with:
                - source_table: Source table
                - target_table: Target table
                - predicate: Relationship name (e.g., 'upstream_of', 'serves')
                - join_condition: SQL join condition
                
        Example:
            [{
                'source_table': 'utility_lines',
                'target_table': 'utility_structures',
                'predicate': 'connects_to',
                'join_condition': 'source.end_structure_id = target.structure_id'
            }]
            
        Returns:
            Number of relationships created
        """
        count = 0
        
        for rule in relationship_rules:
            try:
                source_table = rule['source_table']
                target_table = rule['target_table']
                predicate = rule['predicate']
                join_condition = rule['join_condition']
                
                query = f"""
                    INSERT INTO entity_relationships (
                        relationship_id, subject_entity_id, object_entity_id,
                        relationship_type, predicate, engineering_relationship, confidence_score
                    )
                    SELECT 
                        gen_random_uuid(),
                        source.entity_id,
                        target.entity_id,
                        'engineering',
                        %s,
                        true,
                        0.9
                    FROM {source_table} source
                    JOIN {target_table} target ON {join_condition}
                    WHERE source.entity_id IS NOT NULL 
                      AND target.entity_id IS NOT NULL
                      AND source.entity_id != target.entity_id
                    ON CONFLICT DO NOTHING
                """
                
                execute_query(query, (predicate,), fetch=False)
                
                self.stats['engineering_relationships'] += 1
                count += 1
                
            except Exception as e:
                self.stats['errors'].append(f"Engineering relationship error for {rule.get('predicate')}: {str(e)}")
        
        return count
    
    def create_semantic_relationships(
        self,
        similarity_threshold: float = 0.85,
        entity_types: Optional[List[str]] = None,
        limit_per_entity: int = 10
    ) -> int:
        """
        Create semantic relationships based on embedding similarity.
        
        Args:
            similarity_threshold: Minimum cosine similarity (0-1)
            entity_types: Optional filter for entity types
            limit_per_entity: Maximum similar entities per source entity
            
        Returns:
            Number of relationships created
        """
        # Build entity type filter
        type_filter = ""
        if entity_types:
            type_list = "','".join(entity_types)
            type_filter = f"AND se1.entity_type IN ('{type_list}')"
        
        query = f"""
            INSERT INTO entity_relationships (
                relationship_id, subject_entity_id, object_entity_id,
                relationship_type, predicate, spatial_relationship, confidence_score, attributes
            )
            SELECT 
                gen_random_uuid(),
                ee1.entity_id,
                ee2.entity_id,
                'semantic',
                'similar_to',
                false,
                (1 - (ee1.embedding <=> ee2.embedding))::numeric(4,3),
                jsonb_build_object('similarity_score', 1 - (ee1.embedding <=> ee2.embedding))
            FROM entity_embeddings ee1
            JOIN entity_embeddings ee2 ON ee1.entity_id != ee2.entity_id
            JOIN standards_entities se1 ON ee1.entity_id = se1.entity_id
            WHERE ee1.is_current = true 
              AND ee2.is_current = true
              AND 1 - (ee1.embedding <=> ee2.embedding) > %s
              {type_filter}
            AND ee1.entity_id NOT IN (
                SELECT subject_entity_id FROM entity_relationships
                WHERE object_entity_id = ee2.entity_id AND predicate = 'similar_to'
            )
            ORDER BY ee1.entity_id, (ee1.embedding <=> ee2.embedding)
            LIMIT %s
            ON CONFLICT DO NOTHING
        """
        
        try:
            # Calculate total limit (limit_per_entity * rough entity count estimate)
            total_limit = limit_per_entity * 1000
            execute_query(query, (similarity_threshold, total_limit), fetch=False)
            
            # Count new relationships
            count_query = """
                SELECT COUNT(*) as count FROM entity_relationships
                WHERE relationship_type = 'semantic'
            """
            result = execute_query(count_query)
            count = result[0]['count'] if result else 0
            
            self.stats['semantic_relationships'] = count
            return count
            
        except Exception as e:
            self.stats['errors'].append(f"Semantic relationship error: {str(e)}")
            return 0
    
    def build_utility_network_graph(self) -> Dict[str, Any]:
        """Build complete utility network graph relationships."""
        print("Building utility network relationships...")
        
        # 1. Utility lines connect to structures
        print("  - Lines to structures...")
        self.create_spatial_relationships(
            'utility_lines',
            'utility_structures',
            'adjacent_to',
            distance_threshold=5.0
        )
        
        # 2. Service connections to lines
        print("  - Services to lines...")
        self.create_spatial_relationships(
            'utility_service_connections',
            'utility_lines',
            'adjacent_to',
            distance_threshold=2.0
        )
        
        # 3. Parcels contain utilities
        print("  - Utilities within parcels...")
        self.create_spatial_relationships(
            'parcels',
            'utility_lines',
            'contains'
        )
        
        return self.stats
    
    def build_survey_network_graph(self) -> Dict[str, Any]:
        """Build survey control network relationships."""
        print("Building survey network relationships...")
        
        # Survey points within control networks
        print("  - Points to control networks...")
        
        # This would use the control_point_membership table
        engineering_rules = [{
            'source_table': 'survey_points',
            'target_table': 'survey_control_network',
            'predicate': 'member_of',
            'join_condition': """
                EXISTS(
                    SELECT 1 FROM control_point_membership m
                    WHERE m.point_id = source.point_id AND m.network_id = target.network_id
                )
            """
        }]
        
        self.create_engineering_relationships(engineering_rules)
        
        return self.stats
    
    def build_complete_graph(self) -> Dict[str, Any]:
        """Build all relationship types for the entire database."""
        print("Building complete knowledge graph...")
        print("=" * 60)
        
        self.build_utility_network_graph()
        self.build_survey_network_graph()
        
        print()
        print("Building semantic relationships from embeddings...")
        self.create_semantic_relationships(similarity_threshold=0.80, limit_per_entity=5)
        
        print()
        print("Graph Building Complete!")
        print("=" * 60)
        print(f"Spatial relationships: {self.stats['spatial_relationships']}")
        print(f"Engineering relationships: {self.stats['engineering_relationships']}")
        print(f"Semantic relationships: {self.stats['semantic_relationships']}")
        
        if self.stats['errors']:
            print(f"\nErrors: {len(self.stats['errors'])}")
            for error in self.stats['errors'][:5]:
                print(f"  - {error}")
        
        return self.stats


if __name__ == '__main__':
    # Example usage
    builder = GraphBuilder()
    
    print("Graph Builder Example")
    print("=" * 50)
    
    # Build relationships for utility network
    stats = builder.build_utility_network_graph()
    
    print()
    print("Results:")
    print(f"  Spatial: {stats['spatial_relationships']}")
    print(f"  Engineering: {stats['engineering_relationships']}")
    print(f"  Errors: {len(stats['errors'])}")
