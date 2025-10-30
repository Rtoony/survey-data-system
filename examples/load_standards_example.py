"""
Example: Load CAD Standards from JSON Files

This example shows how to load layer standards, blocks, and details
from JSON files into your AI-optimized database.
"""

import sys
import json
from pathlib import Path

# Add tools to path
sys.path.append(str(Path(__file__).parent.parent))

from tools.ingestion.standards_loader import StandardsLoader
from tools.db_utils import get_entity_stats


def main():
    print("ACAD-GIS Standards Loading Example")
    print("=" * 70)
    print()
    
    loader = StandardsLoader()
    
    # Example 1: Load layers from Python dict
    print("1. Loading Layer Standards")
    print("-" * 70)
    
    layer_data = [
        {
            'name': 'C-TOPO-MAJR',
            'description': 'Major topographic contours (5-foot intervals)',
            'color_name': 'Brown',
            'linetype_name': 'Continuous',
            'lineweight': 0.35,
            'is_plottable': True,
            'category': 'Civil',
            'discipline': 'Site'
        },
        {
            'name': 'C-TOPO-MINR',
            'description': 'Minor topographic contours (1-foot intervals)',
            'color_name': 'Light Brown',
            'linetype_name': 'Continuous',
            'lineweight': 0.18,
            'is_plottable': True,
            'category': 'Civil',
            'discipline': 'Site'
        },
        {
            'name': 'C-UTIL-WATR',
            'description': 'Water utility lines',
            'color_name': 'Blue',
            'linetype_name': 'Dashed',
            'lineweight': 0.50,
            'is_plottable': True,
            'category': 'Civil',
            'discipline': 'Utilities'
        },
        {
            'name': 'A-WALL',
            'description': 'Architectural walls',
            'color_name': 'Black',
            'linetype_name': 'Continuous',
            'lineweight': 0.70,
            'is_plottable': True,
            'category': 'Architecture',
            'discipline': 'Building'
        }
    ]
    
    stats = loader.load_layers(layer_data)
    print(f"  Inserted: {stats['inserted']}")
    print(f"  Updated: {stats['updated']}")
    if stats['errors']:
        print(f"  Errors: {len(stats['errors'])}")
        for error in stats['errors'][:3]:
            print(f"    - {error}")
    
    print()
    
    # Example 2: Load blocks
    print("2. Loading Block Definitions")
    print("-" * 70)
    
    block_data = [
        {
            'name': 'TREE-DECIDUOUS',
            'description': 'Deciduous tree symbol (plan view)',
            'category': 'Landscape',
            'file_path': '/blocks/landscape/tree_deciduous.dwg',
            'insertion_units': 'Feet'
        },
        {
            'name': 'TREE-CONIFER',
            'description': 'Conifer tree symbol (plan view)',
            'category': 'Landscape',
            'file_path': '/blocks/landscape/tree_conifer.dwg',
            'insertion_units': 'Feet'
        },
        {
            'name': 'MANHOLE-SEWER',
            'description': 'Sewer manhole symbol',
            'category': 'Utilities',
            'file_path': '/blocks/utilities/manhole_sewer.dwg',
            'insertion_units': 'Feet'
        }
    ]
    
    stats = loader.load_blocks(block_data)
    print(f"  Inserted: {stats['inserted']}")
    print(f"  Updated: {stats['updated']}")
    if stats['errors']:
        print(f"  Errors: {len(stats['errors'])}")
    
    print()
    
    # Example 3: Load details
    print("3. Loading Detail Standards")
    print("-" * 70)
    
    detail_data = [
        {
            'detail_number': 'C-101',
            'title': 'Curb and Gutter Detail',
            'description': 'Standard curb and gutter section for residential streets',
            'category': 'Civil',
            'discipline': 'Roadway',
            'file_path': '/details/civil/C-101_curb_gutter.dwg',
            'scale': '1:1',
            'sheet_size': '11x17'
        },
        {
            'detail_number': 'C-102',
            'title': 'Catch Basin Detail',
            'description': 'Type 1 catch basin with grate',
            'category': 'Civil',
            'discipline': 'Storm Drain',
            'file_path': '/details/civil/C-102_catch_basin.dwg',
            'scale': '1:10',
            'sheet_size': '11x17'
        }
    ]
    
    stats = loader.load_details(detail_data)
    print(f"  Inserted: {stats['inserted']}")
    print(f"  Updated: {stats['updated']}")
    if stats['errors']:
        print(f"  Errors: {len(stats['errors'])}")
    
    print()
    
    # Show entity statistics
    print("4. Entity Statistics")
    print("-" * 70)
    
    entity_stats = get_entity_stats()
    print(f"  Total entities: {entity_stats['total_entities']}")
    print(f"  Entities by type:")
    for entity_type, count in entity_stats['entities_by_type'].items():
        print(f"    - {entity_type}: {count}")
    
    quality = entity_stats['quality']
    if quality.get('avg_quality'):
        print(f"  Average quality score: {float(quality['avg_quality']):.3f}")
    
    print()
    print("=" * 70)
    print("Standards loading complete!")
    print()
    print("Next steps:")
    print("  1. Generate embeddings: python examples/generate_embeddings_example.py")
    print("  2. Build relationships: python examples/build_relationships_example.py")
    print("  3. Validate data: python examples/validate_data_example.py")


if __name__ == '__main__':
    main()
