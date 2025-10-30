"""
Example: Database Maintenance

This example shows how to run database maintenance tasks:
- Refresh materialized views
- Recompute quality scores
- VACUUM and ANALYZE
- Check index health
- Monitor database size
"""

import sys
from pathlib import Path

# Add tools to path
sys.path.append(str(Path(__file__).parent.parent))

from tools.maintenance.db_maintenance import DatabaseMaintenance


def main():
    maintenance = DatabaseMaintenance()
    
    # Run full maintenance routine
    results = maintenance.run_full_maintenance(include_vacuum_full=False)
    
    print()
    print("Maintenance Summary:")
    print("=" * 70)
    
    # Check results
    success_count = sum(1 for r in results.values() if isinstance(r, dict) and r.get('success'))
    print(f"Tasks completed successfully: {success_count}/{len(results)}")
    
    print()
    print("Log:")
    print("-" * 70)
    for log_entry in maintenance.maintenance_log[-10:]:
        print(log_entry)


def quick_refresh():
    """Quick refresh of materialized views and quality scores."""
    print("Quick Refresh Mode")
    print("=" * 70)
    print()
    
    maintenance = DatabaseMaintenance()
    
    # Refresh views
    print("1. Refreshing materialized views...")
    result = maintenance.refresh_all_materialized_views()
    if result['success']:
        print(f"   Done in {result['duration']:.2f}s")
    else:
        print(f"   ERROR: {result.get('error')}")
    
    print()
    
    # Recompute quality
    print("2. Recomputing quality scores...")
    result = maintenance.recompute_all_quality_scores()
    if result['success']:
        print(f"   Done in {result['duration']:.2f}s")
        stats = result.get('stats', {})
        print(f"   Total entities: {stats.get('total', 0)}")
        print(f"   Avg quality: {float(stats.get('avg_quality', 0)):.3f}")
    else:
        print(f"   ERROR: {result.get('error')}")
    
    print()
    print("Quick refresh complete!")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--quick':
        quick_refresh()
    else:
        main()
