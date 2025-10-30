"""
Example: Build Graph Relationships

This example shows how to automatically detect and create
spatial, engineering, and semantic relationships for GraphRAG.
"""

import sys
from pathlib import Path

# Add tools to path
sys.path.append(str(Path(__file__).parent.parent))

from tools.relationships.graph_builder import GraphBuilder
from tools.db_utils import get_entity_stats


def main():
    print("ACAD-GIS Relationship Building Example")
    print("=" * 70)
    print()
    
    builder = GraphBuilder()
    
    # Example 1: Build utility network relationships
    print("1. Building Utility Network Relationships")
    print("-" * 70)
    
    stats = builder.build_utility_network_graph()
    
    print(f"  Spatial relationships: {stats['spatial_relationships']}")
    print(f"  Engineering relationships: {stats['engineering_relationships']}")
    if stats['errors']:
        print(f"  Errors: {len(stats['errors'])}")
    
    print()
    
    # Example 2: Build survey network relationships
    print("2. Building Survey Network Relationships")
    print("-" * 70)
    
    stats = builder.build_survey_network_graph()
    
    print(f"  Spatial relationships: {stats['spatial_relationships']}")
    print(f"  Engineering relationships: {stats['engineering_relationships']}")
    
    print()
    
    # Example 3: Create semantic relationships from embeddings
    print("3. Building Semantic Relationships (Embedding Similarity)")
    print("-" * 70)
    print("This will find similar entities based on vector embeddings...")
    
    count = builder.create_semantic_relationships(
        similarity_threshold=0.80,
        limit_per_entity=5
    )
    
    print(f"  Semantic relationships created: {count}")
    
    print()
    
    # Example 4: Custom spatial relationships
    print("4. Custom Spatial Relationship Example")
    print("-" * 70)
    print("Finding parcels that contain utility structures...")
    
    count = builder.create_spatial_relationships(
        source_table='parcels',
        target_table='utility_structures',
        relationship_type='contains'
    )
    
    print(f"  Parcel-to-structure relationships: {count}")
    
    print()
    
    # Show relationship statistics
    print("5. Relationship Statistics")
    print("-" * 70)
    
    entity_stats = get_entity_stats()
    print(f"  Total entities: {entity_stats['total_entities']}")
    print(f"  Total relationships: {entity_stats['relationships']}")
    
    print()
    print("=" * 70)
    print("Relationship building complete!")
    print()
    print("Next steps:")
    print("  1. Test GraphRAG queries:")
    print("     SELECT * FROM find_related_entities('entity-uuid', 2)")
    print("  2. Test similarity search:")
    print("     SELECT * FROM find_similar_entities('entity-uuid', 0.8, 20)")
    print("  3. Refresh materialized views: python examples/maintenance_example.py")


def build_complete_graph():
    """Build all relationships for the entire database."""
    print("Building COMPLETE knowledge graph...")
    print("This will create spatial, engineering, and semantic relationships.")
    print()
    
    builder = GraphBuilder()
    stats = builder.build_complete_graph()
    
    print()
    print("Complete graph statistics:")
    print(f"  Spatial: {stats['spatial_relationships']}")
    print(f"  Engineering: {stats['engineering_relationships']}")
    print(f"  Semantic: {stats['semantic_relationships']}")
    print(f"  Total: {stats['spatial_relationships'] + stats['engineering_relationships'] + stats['semantic_relationships']}")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--complete':
        build_complete_graph()
    else:
        main()
