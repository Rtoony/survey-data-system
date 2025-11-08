"""
Initialize Complete CAD Standards System
Runs all necessary setup steps for the revolutionary database-driven CAD standards.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.db_utils import execute_query, get_cursor


def run_migration(migration_file):
    """Run a SQL migration file"""
    print(f"\n{'='*60}")
    print(f"Running migration: {migration_file}")
    print('='*60)
    
    try:
        with open(migration_file, 'r') as f:
            sql = f.read()
        
        # Execute the migration
        with get_cursor(dict_cursor=False) as cursor:
            cursor.execute(sql)
        
        print("✓ Migration completed successfully")
        return True
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def load_standards_data():
    """Load core standards vocabulary data"""
    print(f"\n{'='*60}")
    print("Loading Standards Vocabulary Data")
    print('='*60)
    
    try:
        from standards.load_standards_data import load_all_standards
        load_all_standards()
        print("✓ Standards data loaded successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to load standards data: {e}")
        import traceback
        traceback.print_exc()
        return False


def load_import_mappings():
    """Load common import mapping patterns"""
    print(f"\n{'='*60}")
    print("Loading Import Mapping Patterns")
    print('='*60)
    
    try:
        from standards.load_import_mappings import load_common_patterns
        success = load_common_patterns()
        if success:
            print("✓ Import mappings loaded successfully")
        return success
    except Exception as e:
        print(f"✗ Failed to load import mappings: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_installation():
    """Verify the installation by checking data counts"""
    print(f"\n{'='*60}")
    print("Verifying Installation")
    print('='*60)
    
    try:
        tables = [
            'discipline_codes',
            'category_codes',
            'object_type_codes',
            'attribute_codes',
            'phase_codes',
            'geometry_codes',
            'import_mapping_patterns'
        ]
        
        for table in tables:
            result = execute_query(f"SELECT COUNT(*) as count FROM {table}")
            count = result[0]['count'] if result else 0
            status = "✓" if count > 0 else "⚠"
            print(f"{status} {table}: {count} records")
        
        print("\n✓ Verification complete")
        return True
    except Exception as e:
        print(f"✗ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main initialization routine"""
    print("\n" + "="*60)
    print("CAD STANDARDS SYSTEM INITIALIZATION")
    print("Database-Optimized Revolutionary CAD Naming System")
    print("="*60)
    
    steps = [
        ("Create database schema", lambda: run_migration('migrations/create_standards_schema.sql')),
        ("Load standards vocabulary", load_standards_data),
        ("Load import mappings", load_import_mappings),
        ("Verify installation", verify_installation),
    ]
    
    results = []
    for step_name, step_func in steps:
        print(f"\nStep: {step_name}")
        success = step_func()
        results.append((step_name, success))
        
        if not success:
            print(f"\n⚠ Warning: {step_name} failed, but continuing...")
    
    # Summary
    print("\n" + "="*60)
    print("INSTALLATION SUMMARY")
    print("="*60)
    
    for step_name, success in results:
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"{status}: {step_name}")
    
    all_success = all(success for _, success in results)
    
    if all_success:
        print("\n🎉 All steps completed successfully!")
        print("\nYour CAD Standards System is ready to use:")
        print("  - Import DXF files with any client layer format")
        print("  - System auto-converts to standard naming")
        print("  - Export DXF with standard or client-specific layers")
        print("\nNext steps:")
        print("  1. Visit /standards/vocabulary to browse the vocabulary")
        print("  2. Import a DXF file to test the system")
        print("  3. Add custom import mappings for your clients")
        return 0
    else:
        print("\n⚠ Some steps failed - review the errors above")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
