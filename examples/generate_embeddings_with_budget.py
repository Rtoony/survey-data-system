"""
Example: Generate Embeddings with $100 Budget Control

This example demonstrates the cost control features:
- Dry run mode to preview costs
- $100 hard budget cap
- Warnings at $50, $75, $90
- Cost tracking and reporting
"""

import sys
import os
from pathlib import Path

# Add tools to path
sys.path.append(str(Path(__file__).parent.parent))

from tools.embeddings.embedding_generator import EmbeddingGenerator


def main():
    print("=" * 70)
    print("ACAD-GIS Embedding Generation with Cost Controls")
    print("Budget Cap: $100.00")
    print("=" * 70)
    print()
    
    # Check API key
    if not os.environ.get('OPENAI_API_KEY'):
        print("❌ ERROR: OPENAI_API_KEY environment variable not set")
        print()
        print("To set your API key:")
        print("  export OPENAI_API_KEY='your-key-here'")
        print()
        return
    
    # STEP 1: DRY RUN - Preview costs without spending money
    print("STEP 1: Dry Run - Preview Costs (No API calls)")
    print("-" * 70)
    
    try:
        generator_preview = EmbeddingGenerator(
            provider='openai',
            model='text-embedding-3-small',
            budget_cap=100.0,  # $100 hard cap
            dry_run=True  # Preview mode - no actual API calls
        )
        
        print(f"Current budget status:")
        print(f"  Spent so far: ${generator_preview.cumulative_cost:.2f}")
        print(f"  Budget cap: ${generator_preview.budget_cap:.2f}")
        print(f"  Remaining: ${generator_preview.stats['budget_remaining']:.2f}")
        print()
        
        # Preview cost for first 100 layers
        print("Previewing cost for layer_standards (first 100 entities)...")
        preview_stats = generator_preview.generate_for_table(
            table_name='layer_standards',
            text_columns=['name', 'description'],
            where_clause='WHERE entity_id IS NOT NULL LIMIT 100'
        )
        
        # Show dry run results
        if preview_stats['estimated_cost'] > 0:
            proceed = input("\n✓ Preview complete. Proceed with actual generation? (yes/no): ")
            if proceed.lower() != 'yes':
                print("Operation cancelled by user.")
                return
        else:
            print("No entities found to process.")
            return
        
    except ValueError as e:
        print(f"❌ Budget Error: {e}")
        return
    
    print("\n" + "=" * 70)
    print("STEP 2: Generate Embeddings with Budget Enforcement")
    print("-" * 70)
    print()
    
    try:
        # Initialize generator with cost controls (actual mode)
        generator = EmbeddingGenerator(
            provider='openai',
            model='text-embedding-3-small',
            budget_cap=100.0,  # Hard cap at $100
            dry_run=False  # Actual generation
        )
        
        print(f"Generator initialized:")
        print(f"  Model: {generator.model}")
        print(f"  Budget cap: ${generator.budget_cap:.2f}")
        print(f"  Current spent: ${generator.cumulative_cost:.2f}")
        print(f"  Remaining: ${generator.stats['budget_remaining']:.2f}")
        print()
        
        # Generate embeddings for layer standards
        print("Generating embeddings for layer_standards...")
        print()
        
        stats = generator.generate_for_table(
            table_name='layer_standards',
            text_columns=['name', 'description'],
            where_clause='WHERE entity_id IS NOT NULL LIMIT 100'
        )
        
        # Print results
        print("\n" + "=" * 70)
        print("RESULTS")
        print("=" * 70)
        print(f"✓ Embeddings generated: {stats['generated']}")
        print(f"✓ API calls made: {stats['api_calls']}")
        print(f"✓ Tokens used: {stats['tokens_used']:,}")
        print(f"✓ Cost this session: ${stats['estimated_cost']:.4f}")
        print()
        print(f"Budget Status:")
        print(f"  Total spent: ${stats['cumulative_cost']:.2f}")
        print(f"  Budget cap: $100.00")
        print(f"  Remaining: ${stats['budget_remaining']:.2f}")
        print(f"  Used: {(stats['cumulative_cost'] / 100.0) * 100:.1f}%")
        
        if stats['errors']:
            print(f"\n⚠️  Errors: {len(stats['errors'])}")
            for error in stats['errors'][:5]:
                print(f"  - {error}")
        
        print("\n" + "=" * 70)
        print("✓ Complete! Cost tracking saved to database.")
        print("=" * 70)
        
    except ValueError as e:
        # Budget cap exceeded
        print(f"\n❌ Operation stopped: {e}")
        print()
        print("Options:")
        print("  1. Increase budget_cap parameter")
        print("  2. Process fewer entities")
        print("  3. Reset cost tracking (if starting new budget period)")
        return


def reset_costs():
    """Helper function to reset cost tracking (use carefully!)"""
    print("=" * 70)
    print("RESET COST TRACKING")
    print("=" * 70)
    print()
    print("⚠️  WARNING: This will reset the cumulative cost counter to $0.00")
    print("Only use this when starting a new budget period or after reconciliation.")
    print()
    
    confirm = input("Are you sure you want to reset? (type 'RESET' to confirm): ")
    if confirm != 'RESET':
        print("Cancelled.")
        return
    
    generator = EmbeddingGenerator(
        provider='openai',
        model='text-embedding-3-small',
        budget_cap=100.0
    )
    
    generator.reset_cost_tracking()
    print()
    print("✓ Cost tracking has been reset to $0.00")


def show_budget_status():
    """Show current budget status without generating embeddings"""
    print("=" * 70)
    print("BUDGET STATUS")
    print("=" * 70)
    print()
    
    generator = EmbeddingGenerator(
        provider='openai',
        model='text-embedding-3-small',
        budget_cap=100.0,
        dry_run=True
    )
    
    summary = generator.get_cost_summary()
    
    print(f"Model: {summary['model']}")
    print(f"Budget cap: ${summary['budget_cap']:.2f}")
    print(f"Cumulative spent: ${summary['cumulative_cost']:.2f}")
    print(f"Budget remaining: ${summary['budget_remaining']:.2f}")
    print(f"Budget used: {summary['budget_used_percent']:.1f}%")
    print()
    
    # Show warning if approaching cap
    if summary['budget_used_percent'] >= 90:
        print("🛑 WARNING: Approaching budget cap!")
    elif summary['budget_used_percent'] >= 75:
        print("⚠️  WARNING: 75% of budget used")
    elif summary['budget_used_percent'] >= 50:
        print("ℹ️  INFO: 50% of budget used")


if __name__ == '__main__':
    import sys
    
    # Support command-line operations
    if len(sys.argv) > 1:
        if sys.argv[1] == 'status':
            show_budget_status()
        elif sys.argv[1] == 'reset':
            reset_costs()
        else:
            print("Usage:")
            print("  python generate_embeddings_with_budget.py          # Generate with preview")
            print("  python generate_embeddings_with_budget.py status   # Show budget status")
            print("  python generate_embeddings_with_budget.py reset    # Reset cost tracking")
    else:
        main()
