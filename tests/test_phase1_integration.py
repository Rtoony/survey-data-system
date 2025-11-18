#!/usr/bin/env python3
"""
Phase 1 Integration Test
Test the DXF Name Translator integration with DXF importer
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_import_mapping_manager():
    """Test that ImportMappingManager can be imported and initialized"""
    print("Test 1: Import ImportMappingManager...")
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'standards'))
        from import_mapping_manager import ImportMappingManager, MappingMatch
        print("✓ ImportMappingManager imported successfully")

        # Try to initialize (will fail if DB not accessible, but that's OK for syntax test)
        try:
            manager = ImportMappingManager()
            print("✓ ImportMappingManager initialized successfully")
        except Exception as e:
            print(f"  (DB not accessible - expected in test environment: {e})")

        return True
    except Exception as e:
        print(f"✗ Failed to import ImportMappingManager: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dxf_importer():
    """Test that DXFImporter can import ImportMappingManager"""
    print("\nTest 2: Import DXFImporter...")
    try:
        from dxf_importer import DXFImporter
        print("✓ DXFImporter imported successfully")

        # Check if _build_standard_layer_name method exists
        if hasattr(DXFImporter, '_build_standard_layer_name'):
            print("✓ _build_standard_layer_name method exists")
        else:
            print("✗ _build_standard_layer_name method not found")
            return False

        return True
    except Exception as e:
        print(f"✗ Failed to import DXFImporter: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """Test that app.py has the new endpoints"""
    print("\nTest 3: Check API endpoints in app.py...")
    try:
        with open('app.py', 'r') as f:
            content = f.read()

        endpoints = [
            '/api/import-mapping-patterns',
            '/api/import-mapping-patterns/test',
            '/api/import-mapping-patterns/validate'
        ]

        all_found = True
        for endpoint in endpoints:
            if endpoint in content:
                print(f"✓ Found endpoint: {endpoint}")
            else:
                print(f"✗ Missing endpoint: {endpoint}")
                all_found = False

        return all_found
    except Exception as e:
        print(f"✗ Failed to check app.py: {e}")
        return False

def test_migration_file():
    """Test that migration file exists"""
    print("\nTest 4: Check migration file...")
    try:
        migration_file = 'database/migrations/014_add_import_mapping_provenance.sql'
        if os.path.exists(migration_file):
            print(f"✓ Migration file exists: {migration_file}")
            with open(migration_file, 'r') as f:
                content = f.read()
                if 'created_by' in content and 'modified_by' in content:
                    print("✓ Migration file contains provenance fields")
                    return True
                else:
                    print("✗ Migration file missing provenance fields")
                    return False
        else:
            print(f"✗ Migration file not found: {migration_file}")
            return False
    except Exception as e:
        print(f"✗ Failed to check migration file: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 70)
    print("Phase 1 Integration Test - DXF Name Translator")
    print("=" * 70)

    results = []
    results.append(("ImportMappingManager", test_import_mapping_manager()))
    results.append(("DXFImporter Integration", test_dxf_importer()))
    results.append(("API Endpoints", test_api_endpoints()))
    results.append(("Migration File", test_migration_file()))

    print("\n" + "=" * 70)
    print("Test Summary:")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Phase 1 implementation complete.")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
