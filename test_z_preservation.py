"""
Round-trip validation test for Z value preservation.
Tests that elevation data survives import -> database -> export cycles.
"""

import ezdxf
import tempfile
import os
from dxf_importer import DXFImporter
from dxf_exporter import DXFExporter
import psycopg2
from datetime import datetime

def create_test_dxf_with_elevations(output_path: str):
    """Create a test DXF file with known elevation values."""
    print("Creating test DXF with 3D geometry...")
    
    doc = ezdxf.new('R2018')
    msp = doc.modelspace()
    
    # Add a 3D polyline with varying elevations (simulating a utility line with slope)
    test_line_coords = [
        (1000.0, 2000.0, 100.0),  # Start at elevation 100
        (1050.0, 2000.0, 99.5),   # Slope down
        (1100.0, 2000.0, 99.0),   # Continue slope
        (1150.0, 2000.0, 98.5),   # Continue slope
        (1200.0, 2000.0, 98.0)    # End at elevation 98
    ]
    msp.add_polyline3d(test_line_coords, dxfattribs={'layer': 'TEST-PIPE'})
    
    # Add 3D points (survey points)
    survey_points = [
        (1000.0, 2100.0, 105.25),
        (1100.0, 2100.0, 104.75),
        (1200.0, 2100.0, 103.50)
    ]
    for pt in survey_points:
        msp.add_point(pt, dxfattribs={'layer': 'TEST-TOPO'})
    
    # Add 3D face (terrain surface)
    face_points = [
        (900.0, 1900.0, 102.0),
        (1300.0, 1900.0, 101.5),
        (1300.0, 2200.0, 100.0),
        (900.0, 2200.0, 100.5)
    ]
    msp.add_3dface(face_points, dxfattribs={'layer': 'TEST-SURFACE'})
    
    # Add a line with elevation
    msp.add_line(
        start=(1000.0, 2050.0, 101.0),
        end=(1200.0, 2050.0, 100.0),
        dxfattribs={'layer': 'TEST-LINE'}
    )
    
    # CRITICAL TEST: Add flat geometry at Z=0 (must preserve Z dimension even when zero)
    flat_pad_coords = [
        (1300.0, 2000.0, 0.0),
        (1400.0, 2000.0, 0.0),
        (1400.0, 2100.0, 0.0),
        (1300.0, 2100.0, 0.0)
    ]
    msp.add_polyline3d(flat_pad_coords + [flat_pad_coords[0]], dxfattribs={'layer': 'TEST-FLAT-PAD'})
    
    # Point at Z=0
    msp.add_point((1350.0, 2050.0, 0.0), dxfattribs={'layer': 'TEST-POINT-ZERO'})
    
    doc.saveas(output_path)
    print(f"Test DXF created: {output_path}")
    
    return {
        'polyline': test_line_coords,
        'points': survey_points,
        'face': face_points,
        'line': [(1000.0, 2050.0, 101.0), (1200.0, 2050.0, 100.0)],
        'flat_pad': flat_pad_coords,
        'zero_point': [(1350.0, 2050.0, 0.0)]
    }


def extract_coords_from_dxf(dxf_path: str):
    """Extract coordinates from a DXF file for comparison."""
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    
    extracted = {
        'polylines': [],
        'points': [],
        'faces': [],
        'lines': [],
        'flat_geometries': []  # Track geometries at Z=0 to ensure preserved
    }
    
    for entity in msp:
        if entity.dxftype() == 'POLYLINE':
            coords = [(v.dxf.location.x, v.dxf.location.y, v.dxf.location.z) 
                     for v in entity.vertices]
            extracted['polylines'].append(coords)
            # Track if this is a flat geometry at Z=0
            if coords and all(abs(c[2]) < 0.001 for c in coords):
                extracted['flat_geometries'].append(('polyline', coords))
        elif entity.dxftype() == 'POINT':
            loc = entity.dxf.location
            coord = (loc.x, loc.y, loc.z)
            extracted['points'].append(coord)
            # Track if this is a point at Z=0
            if abs(coord[2]) < 0.001:
                extracted['flat_geometries'].append(('point', [coord]))
        elif entity.dxftype() == '3DFACE':
            pts = [entity.dxf.vtx0, entity.dxf.vtx1, entity.dxf.vtx2, entity.dxf.vtx3]
            coords = [(p.x, p.y, p.z) for p in pts]
            extracted['faces'].append(coords)
        elif entity.dxftype() == 'LINE':
            start = entity.dxf.start
            end = entity.dxf.end
            extracted['lines'].append([
                (start.x, start.y, start.z),
                (end.x, end.y, end.z)
            ])
    
    return extracted


def compare_elevations(original, exported, tolerance=0.01):
    """Compare elevation data between original and exported DXF."""
    print("\n=== Comparing Elevations ===")
    
    errors = []
    
    # CRITICAL: Check flat geometries at Z=0 are preserved
    print("\nFlat Geometries at Z=0 (Critical Test):")
    orig_flat_count = len(original.get('flat_geometries', []))
    exp_flat_count = len(exported.get('flat_geometries', []))
    if orig_flat_count != exp_flat_count:
        errors.append(f"CRITICAL: Flat geometry count mismatch (Z=0 data lost!): {orig_flat_count} vs {exp_flat_count}")
    else:
        print(f"  ✓ All {orig_flat_count} flat (Z=0) geometries preserved")
    
    # Compare polylines
    print("\nPolylines:")
    if len(original['polylines']) != len(exported['polylines']):
        errors.append(f"Polyline count mismatch: {len(original['polylines'])} vs {len(exported['polylines'])}")
    else:
        for i, (orig_pl, exp_pl) in enumerate(zip(original['polylines'], exported['polylines'])):
            if len(orig_pl) != len(exp_pl):
                errors.append(f"Polyline {i} vertex count mismatch: {len(orig_pl)} vs {len(exp_pl)}")
                continue
            
            for j, (orig_pt, exp_pt) in enumerate(zip(orig_pl, exp_pl)):
                z_diff = abs(orig_pt[2] - exp_pt[2])
                if z_diff > tolerance:
                    errors.append(f"Polyline {i} vertex {j} Z mismatch: {orig_pt[2]} vs {exp_pt[2]} (diff: {z_diff})")
                else:
                    print(f"  ✓ Polyline {i} vertex {j}: Z={orig_pt[2]:.2f} -> {exp_pt[2]:.2f} (diff: {z_diff:.4f})")
    
    # Compare points
    print("\nPoints:")
    if len(original['points']) != len(exported['points']):
        errors.append(f"Point count mismatch: {len(original['points'])} vs {len(exported['points'])}")
    else:
        for i, (orig_pt, exp_pt) in enumerate(zip(sorted(original['points']), sorted(exported['points']))):
            z_diff = abs(orig_pt[2] - exp_pt[2])
            if z_diff > tolerance:
                errors.append(f"Point {i} Z mismatch: {orig_pt[2]} vs {exp_pt[2]} (diff: {z_diff})")
            else:
                print(f"  ✓ Point {i}: Z={orig_pt[2]:.2f} -> {exp_pt[2]:.2f} (diff: {z_diff:.4f})")
    
    # Compare faces
    print("\n3D Faces:")
    if len(original['faces']) != len(exported['faces']):
        errors.append(f"Face count mismatch: {len(original['faces'])} vs {len(exported['faces'])}")
    else:
        for i, (orig_face, exp_face) in enumerate(zip(original['faces'], exported['faces'])):
            for j, (orig_pt, exp_pt) in enumerate(zip(orig_face, exp_face)):
                z_diff = abs(orig_pt[2] - exp_pt[2])
                if z_diff > tolerance:
                    errors.append(f"Face {i} vertex {j} Z mismatch: {orig_pt[2]} vs {exp_pt[2]} (diff: {z_diff})")
                else:
                    print(f"  ✓ Face {i} vertex {j}: Z={orig_pt[2]:.2f} -> {exp_pt[2]:.2f} (diff: {z_diff:.4f})")
    
    # Compare lines
    print("\nLines:")
    if len(original['lines']) != len(exported['lines']):
        errors.append(f"Line count mismatch: {len(original['lines'])} vs {len(exported['lines'])}")
    else:
        for i, (orig_line, exp_line) in enumerate(zip(original['lines'], exported['lines'])):
            for j, (orig_pt, exp_pt) in enumerate(zip(orig_line, exp_line)):
                z_diff = abs(orig_pt[2] - exp_pt[2])
                if z_diff > tolerance:
                    errors.append(f"Line {i} point {j} Z mismatch: {orig_pt[2]} vs {exp_pt[2]} (diff: {z_diff})")
                else:
                    print(f"  ✓ Line {i} point {j}: Z={orig_pt[2]:.2f} -> {exp_pt[2]:.2f} (diff: {z_diff:.4f})")
    
    return errors


def run_roundtrip_test():
    """Execute the full round-trip test."""
    print("=" * 70)
    print("DXF Z-VALUE PRESERVATION ROUND-TRIP TEST")
    print("=" * 70)
    
    # Database configuration (adjust as needed)
    db_config = {
        'host': os.getenv('PGHOST', 'localhost'),
        'port': os.getenv('PGPORT', '5432'),
        'database': os.getenv('PGDATABASE', 'civil_cad'),
        'user': os.getenv('PGUSER', 'postgres'),
        'password': os.getenv('PGPASSWORD', '')
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Step 0: Create test project
        print("\nCreating test project...")
        import psycopg2
        import uuid
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        project_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO projects (project_id, project_name, project_number)
            VALUES (%s, %s, %s)
        """, (project_id, "Z-Preservation Test Project", "TEST-Z-PRES"))
        conn.commit()
        cur.close()
        conn.close()
        print(f"Test project created: {project_id}")

        # Step 1: Create test DXF
        original_dxf = os.path.join(tmpdir, 'test_3d_original.dxf')
        expected_coords = create_test_dxf_with_elevations(original_dxf)

        # Extract coordinates from original
        print("\nExtracting coordinates from original DXF...")
        original_extracted = extract_coords_from_dxf(original_dxf)

        # Step 2: Import to database
        print("\nImporting to database...")
        importer = DXFImporter(db_config)
        try:
            import_result = importer.import_dxf(
                file_path=original_dxf,
                project_id=project_id,
                coordinate_system='LOCAL',
                import_modelspace=True
            )
            print(f"Import successful. Project ID: {project_id}")
            print(f"Imported: {import_result.get('entities', 0)} entities")
        except Exception as e:
            print(f"Import failed: {e}")
            return False

        # Step 3: Export from database
        print("\nExporting from database...")
        exported_dxf = os.path.join(tmpdir, 'test_3d_exported.dxf')
        exporter = DXFExporter(db_config, use_standards=False)
        try:
            export_result = exporter.export_dxf(
                project_id=project_id,
                output_path=exported_dxf,
                dxf_version='R2018'
            )
            print(f"Export successful: {export_result}")
        except Exception as e:
            print(f"Export failed: {e}")
            return False
        
        # Step 4: Extract coordinates from exported DXF
        print("\nExtracting coordinates from exported DXF...")
        exported_extracted = extract_coords_from_dxf(exported_dxf)
        
        # Step 5: Compare
        errors = compare_elevations(original_extracted, exported_extracted)
        
        # Step 6: Report results
        print("\n" + "=" * 70)
        if not errors:
            print("✓ SUCCESS: All Z values preserved through round-trip!")
            print("=" * 70)
            return True
        else:
            print("✗ FAILURES DETECTED:")
            for error in errors:
                print(f"  - {error}")
            print("=" * 70)
            return False


if __name__ == '__main__':
    success = run_roundtrip_test()
    exit(0 if success else 1)
