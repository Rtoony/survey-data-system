"""
Comprehensive test suite for DXF coordinate preservation.
Tests the complete import → database → export pipeline for survey-grade accuracy.
"""

import os
import sys
from dxf_importer import DXFImporter
from dxf_exporter import DXFExporter
from dxf_coordinate_validator import CoordinateValidator
import tempfile
import shutil


def get_db_config():
    """Get database configuration from environment."""
    return {
        'host': os.getenv('DB_HOST'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }


def test_coordinate_preservation(original_dxf_path: str, test_name: str, tolerance_ft: float = 0.001):
    """
    Test complete round-trip coordinate preservation.

    Args:
        original_dxf_path: Path to original DXF file
        test_name: Name for this test (used for project names)
        tolerance_ft: Maximum acceptable error in feet (default 0.001 ft = 0.012 inches)

    Returns:
        dict: Test results with pass/fail status
    """
    import psycopg2
    import uuid

    print(f"\n{'='*80}")
    print(f" COORDINATE PRESERVATION TEST: {test_name}")
    print(f"{'='*80}\n")

    db_config = get_db_config()
    temp_dir = tempfile.mkdtemp()

    try:
        # Step 0: Create a test project
        print("STEP 0: Creating test project...")
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        project_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO projects (project_id, project_name, project_number)
            VALUES (%s, %s, %s)
        """, (project_id, f"Test Project - {test_name}", f"TEST-{test_name}"))
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ Project created: {project_id}")

        # Step 1: Import DXF to database
        print("\nSTEP 1: Importing DXF to database...")
        importer = DXFImporter(db_config)

        import_stats = importer.import_dxf(
            file_path=original_dxf_path,
            project_id=project_id,
            coordinate_system='LOCAL',
            import_modelspace=True
        )

        if import_stats.get('errors'):
            print("❌ Import failed!")
            for error in import_stats['errors']:
                print(f"  ERROR: {error}")
            return {'passed': False, 'stage': 'import', 'errors': import_stats['errors']}

        print(f"✅ Import successful!")
        print(f"   Project ID: {project_id}")
        print(f"   Entities: {import_stats.get('entities', 0)}")
        print(f"   Layers: {import_stats.get('layers', 0)}")

        # Step 2: Export from database back to DXF
        print("\nSTEP 2: Exporting from database to DXF...")
        exporter = DXFExporter(db_config)
        exported_dxf_path = os.path.join(temp_dir, f"{test_name}_exported.dxf")

        export_stats = exporter.export_dxf(
            project_id=project_id,
            output_path=exported_dxf_path,
            dxf_version='AC1027',
            include_modelspace=True
        )
        
        if export_stats.get('errors'):
            print("❌ Export failed!")
            for error in export_stats['errors']:
                print(f"  ERROR: {error}")
            return {'passed': False, 'stage': 'export', 'errors': export_stats['errors']}
        
        print(f"✅ Export successful!")
        print(f"   Entities: {export_stats.get('entities', 0)}")
        print(f"   Text: {export_stats.get('text', 0)}")
        print(f"   Layers: {export_stats.get('layers', 0)}")
        print(f"   File: {exported_dxf_path}")
        
        # Step 3: Validate coordinate preservation
        print("\nSTEP 3: Validating coordinate preservation...")
        validator = CoordinateValidator(tolerance_ft=tolerance_ft)
        
        try:
            report = validator.validate_round_trip(original_dxf_path, exported_dxf_path)
            validator.print_report(report)
            
            return {
                'passed': report['passed'],
                'stage': 'complete',
                'project_id': project_id,
                'import_stats': import_stats,
                'export_stats': export_stats,
                'validation_report': report
            }
            
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            import traceback
            traceback.print_exc()
            return {'passed': False, 'stage': 'validation', 'errors': [str(e)]}
    
    finally:
        # Cleanup temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)


def run_test_suite():
    """
    Run comprehensive test suite with multiple DXF files.
    """
    print("\n" + "="*80)
    print(" DXF COORDINATE PRESERVATION TEST SUITE")
    print("="*80)
    print("\nThis test suite validates that coordinates are preserved through the")
    print("complete import → database → export pipeline with survey-grade accuracy.")
    print("\nTolerance: 0.001 ft (0.012 inches)")
    print("="*80)
    
    # Find test DXF files
    test_files = []
    
    # Look in common directories
    search_paths = [
        '/tmp/dxf_uploads',
        '/workspace/test_data',
        '/workspace/dxf_samples',
        '.'
    ]
    
    for search_path in search_paths:
        if os.path.exists(search_path):
            for file in os.listdir(search_path):
                if file.endswith('.dxf'):
                    test_files.append(os.path.join(search_path, file))
    
    if not test_files:
        print("\n⚠️  No DXF test files found in standard locations.")
        print("Please upload DXF files to /tmp/dxf_uploads/ or current directory.")
        return
    
    print(f"\nFound {len(test_files)} DXF file(s) to test:\n")
    for i, file in enumerate(test_files, 1):
        print(f"  {i}. {os.path.basename(file)}")
    
    # Run tests
    results = []
    for i, dxf_file in enumerate(test_files, 1):
        test_name = os.path.splitext(os.path.basename(dxf_file))[0]
        result = test_coordinate_preservation(dxf_file, f"Test_{i}_{test_name}")
        results.append({
            'file': os.path.basename(dxf_file),
            'result': result
        })
    
    # Summary
    print("\n" + "="*80)
    print(" TEST SUITE SUMMARY")
    print("="*80 + "\n")
    
    passed = sum(1 for r in results if r['result'].get('passed'))
    failed = len(results) - passed
    
    print(f"Total tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}\n")
    
    for test in results:
        status = "✅ PASS" if test['result'].get('passed') else "❌ FAIL"
        stage = test['result'].get('stage', 'unknown')
        print(f"{status} - {test['file']} (stage: {stage})")
    
    print("\n" + "="*80)
    if failed == 0:
        print("🎉 ALL TESTS PASSED - COORDINATE PRESERVATION VALIDATED")
        print("System is ready for market with survey-grade accuracy.")
    else:
        print("⚠️  SOME TESTS FAILED - REQUIRES INVESTIGATION")
        print("Review errors above before deployment.")
    print("="*80 + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test specific file
        dxf_file = sys.argv[1]
        test_name = os.path.splitext(os.path.basename(dxf_file))[0]
        tolerance = float(sys.argv[2]) if len(sys.argv) > 2 else 0.001
        
        result = test_coordinate_preservation(dxf_file, test_name, tolerance)
        sys.exit(0 if result.get('passed') else 1)
    else:
        # Run full test suite
        run_test_suite()
