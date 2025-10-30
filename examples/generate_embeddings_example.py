"""
Example: Generate Embeddings for CAD Standards

This example shows how to generate vector embeddings for your standards
using OpenAI's embedding API.
"""

import sys
import os
from pathlib import Path

# Add tools to path
sys.path.append(str(Path(__file__).parent.parent))

from tools.embeddings.embedding_generator import EmbeddingGenerator
from tools.db_utils import get_entity_stats


def main():
    print("ACAD-GIS Embedding Generation Example")
    print("=" * 70)
    print()
    
    # Check API key
    if not os.environ.get('OPENAI_API_KEY'):
        print("ERROR: OPENAI_API_KEY environment variable not set")
        print()
        print("To set your API key:")
        print("  1. Get your API key from https://platform.openai.com/api-keys")
        print("  2. Set it in your environment:")
        print("     export OPENAI_API_KEY='your-key-here'")
        print("  3. Or add it to .env file:")
        print("     OPENAI_API_KEY=your-key-here")
        return
    
    # Initialize generator
    print("Initializing embedding generator...")
    generator = EmbeddingGenerator(
        provider='openai',
        model='text-embedding-3-small'
    )
    print(f"Using model: {generator.model}")
    print(f"Model ID: {generator.model_id}")
    print(f"Dimensions: {generator.dimensions}")
    print()
    
    # Example 1: Generate embeddings for layer standards
    print("1. Generating Embeddings for Layer Standards")
    print("-" * 70)
    
    stats = generator.generate_for_table(
        table_name='layer_standards',
        text_columns=['name', 'description', 'category', 'discipline'],
        where_clause='WHERE entity_id IS NOT NULL LIMIT 10'
    )
    
    print(f"  Generated: {stats['generated']}")
    print(f"  API calls: {stats['api_calls']}")
    print(f"  Tokens used: {stats['tokens_used']}")
    if stats['errors']:
        print(f"  Errors: {len(stats['errors'])}")
        for error in stats['errors'][:3]:
            print(f"    - {error}")
    
    print()
    
    # Example 2: Generate embeddings for blocks
    print("2. Generating Embeddings for Block Definitions")
    print("-" * 70)
    
    stats = generator.generate_for_table(
        table_name='block_definitions',
        text_columns=['name', 'description', 'category'],
        where_clause='WHERE entity_id IS NOT NULL LIMIT 10'
    )
    
    print(f"  Generated: {stats['generated']}")
    print(f"  API calls: {stats['api_calls']}")
    print(f"  Tokens used: {stats['tokens_used']}")
    
    print()
    
    # Example 3: Generate embeddings for details
    print("3. Generating Embeddings for Detail Standards")
    print("-" * 70)
    
    stats = generator.generate_for_table(
        table_name='detail_standards',
        text_columns=['detail_number', 'title', 'description', 'category'],
        where_clause='WHERE entity_id IS NOT NULL LIMIT 10'
    )
    
    print(f"  Generated: {stats['generated']}")
    print(f"  API calls: {stats['api_calls']}")
    print(f"  Tokens used: {stats['tokens_used']}")
    
    print()
    
    # Show entity statistics
    print("4. Entity & Embedding Statistics")
    print("-" * 70)
    
    entity_stats = get_entity_stats()
    print(f"  Total entities: {entity_stats['total_entities']}")
    
    embeddings = entity_stats.get('embeddings', {})
    print(f"  Total embeddings: {embeddings.get('total', 0)}")
    print(f"  Current embeddings: {embeddings.get('current', 0)}")
    
    quality = entity_stats['quality']
    if quality.get('avg_quality'):
        print(f"  Average quality score: {float(quality['avg_quality']):.3f}")
    
    print()
    print("=" * 70)
    print("Embedding generation complete!")
    print()
    print("Next steps:")
    print("  1. Test semantic search:")
    print("     SELECT * FROM hybrid_search('water utility', NULL::vector, NULL, 0.5, 10)")
    print("  2. Build relationships: python examples/build_relationships_example.py")
    print("  3. Test GraphRAG: python examples/graphrag_query_example.py")


def generate_all_embeddings():
    """Generate embeddings for all standards tables."""
    print("Generating embeddings for ALL standards...")
    print("This may take a while and will use OpenAI API credits.")
    print()
    
    generator = EmbeddingGenerator(provider='openai', model='text-embedding-3-small')
    
    tables = [
        ('layer_standards', ['name', 'description', 'category', 'discipline']),
        ('block_definitions', ['name', 'description', 'category']),
        ('detail_standards', ['detail_number', 'title', 'description', 'category']),
        ('abbreviation_standards', ['abbreviation', 'full_text', 'description']),
        ('material_standards', ['name', 'description', 'specification']),
        ('category_standards', ['name', 'description', 'parent_category']),
        ('annotation_standards', ['name', 'description', 'usage_context'])
    ]
    
    total_stats = {
        'generated': 0,
        'api_calls': 0,
        'tokens_used': 0,
        'errors': []
    }
    
    for table_name, text_columns in tables:
        print(f"Processing {table_name}...")
        stats = generator.generate_for_table(
            table_name=table_name,
            text_columns=text_columns,
            where_clause='WHERE entity_id IS NOT NULL'
        )
        
        total_stats['generated'] += stats['generated']
        total_stats['api_calls'] += stats['api_calls']
        total_stats['tokens_used'] += stats['tokens_used']
        total_stats['errors'].extend(stats['errors'])
        
        print(f"  Generated: {stats['generated']}, Tokens: {stats['tokens_used']}")
        print()
    
    print("=" * 70)
    print("Complete!")
    print(f"Total generated: {total_stats['generated']}")
    print(f"Total API calls: {total_stats['api_calls']}")
    print(f"Total tokens: {total_stats['tokens_used']}")
    print(f"Errors: {len(total_stats['errors'])}")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--all':
        generate_all_embeddings()
    else:
        main()
