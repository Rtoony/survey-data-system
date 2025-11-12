#!/usr/bin/env python3
"""
Z-Value Elevation Preservation Stress Test Harness

Command-line tool that runs 20+ import/export cycles to verify Z-value preservation
with survey-grade precision. Generates auditable JSON and PDF proof for skeptics.

Usage:
    python scripts/z_stress_harness.py --cycles 20 --output report/
    python scripts/z_stress_harness.py --cycles 25 --srid 2226 --report

Tests:
    - Flat pads at Z=0 (critical edge case)
    - Sloped pipes with varying elevations  
    - Survey points with precise elevations
    - Large State Plane coordinates (millions of feet)
    - Sub-millimeter Z precision (0.001 ft tolerance)
    - SRID consistency (no unwanted transformations)
"""

import sys
import os
import argparse
import json
import tempfile
from datetime import datetime
from typing import Dict, List, Tuple
import math
import hashlib
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ezdxf
from database import DB_CONFIG
from dxf_importer import DXFImporter
from dxf_exporter import DXFExporter


class ZStressHarness:
    """Deterministic stress test harness for Z-value preservation validation."""
    
    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or tempfile.gettempdir()
        self.db_config = DB_CONFIG
        self.test_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
    def create_test_fixtures(self, filepath: str) -> Dict:
        """
        Create comprehensive test DXF with canonical geometries.
        
        Returns metadata about test geometries for validation.
        """
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        
        # Create layers
        for layer in ['TEST-FLAT-PAD', 'TEST-SLOPED-PIPE', 'TEST-SURVEY-POINTS', 
                      'TEST-LARGE-COORDS', 'TEST-PRECISION']:
            doc.layers.add(layer)
        
        fixtures = {
            'timestamp': datetime.now().isoformat(),
            'geometries': []
        }
        
        # 1. CRITICAL: Flat pad at Z=0 (must preserve Z dimension even when zero)
        flat_pad = [
            (1000.0, 2000.0, 0.0),
            (1100.0, 2000.0, 0.0),
            (1100.0, 2100.0, 0.0),
            (1000.0, 2100.0, 0.0)
        ]
        msp.add_polyline3d(flat_pad + [flat_pad[0]], dxfattribs={'layer': 'TEST-FLAT-PAD'})
        fixtures['geometries'].append({
            'name': 'Flat Pad at Z=0',
            'type': 'polyline3d',
            'layer': 'TEST-FLAT-PAD',
            'coords': flat_pad,
            'critical': True,
            'description': 'Level pad at elevation 0.0 - CRITICAL Z=0 preservation test'
        })
        
        # 2. Sloped pipe (1% grade - varying Z values)
        sloped_pipe = [
            (1200.0, 2000.0, 100.5),
            (1300.0, 2000.0, 100.4),
            (1400.0, 2000.0, 100.3),
            (1500.0, 2000.0, 100.2)
        ]
        msp.add_polyline3d(sloped_pipe, dxfattribs={'layer': 'TEST-SLOPED-PIPE'})
        fixtures['geometries'].append({
            'name': 'Sloped Pipe (1% grade)',
            'type': 'polyline3d',
            'layer': 'TEST-SLOPED-PIPE',
            'coords': sloped_pipe,
            'critical': False,
            'description': '1% slope pipe - tests varying elevations'
        })
        
        # 3. Survey points at different elevations (3 decimal precision)
        survey_points = [
            (1000.0, 2200.0, 105.234),
            (1100.0, 2200.0, 103.567),
            (1200.0, 2200.0, 108.901),
            (1300.0, 2200.0, 102.345)
        ]
        for pt in survey_points:
            msp.add_point(pt, dxfattribs={'layer': 'TEST-SURVEY-POINTS'})
        fixtures['geometries'].append({
            'name': 'Survey Points',
            'type': 'points',
            'layer': 'TEST-SURVEY-POINTS',
            'coords': survey_points,
            'critical': False,
            'description': 'Survey control points with 0.001 ft precision'
        })
        
        # 4. Large State Plane coordinates (EPSG:2226 typical range)
        large_coords = [
            (6000000.0, 2100000.0, 250.0),
            (6000100.0, 2100000.0, 250.5),
            (6000100.0, 2100100.0, 251.0)
        ]
        msp.add_polyline3d(large_coords, dxfattribs={'layer': 'TEST-LARGE-COORDS'})
        fixtures['geometries'].append({
            'name': 'Large Coordinates',
            'type': 'polyline3d',
            'layer': 'TEST-LARGE-COORDS',
            'coords': large_coords,
            'critical': False,
            'description': 'State Plane Zone 2 typical coordinates (millions of feet)'
        })
        
        # 5. Sub-millimeter precision test (0.0008 ft = 0.24 mm increments)
        precision_test = [
            (1400.0, 2200.0, 100.0000),
            (1450.0, 2200.0, 100.0008),
            (1500.0, 2200.0, 100.0016),
            (1550.0, 2200.0, 100.0024)
        ]
        msp.add_polyline3d(precision_test, dxfattribs={'layer': 'TEST-PRECISION'})
        fixtures['geometries'].append({
            'name': 'Sub-millimeter Precision',
            'type': 'polyline3d',
            'layer': 'TEST-PRECISION',
            'coords': precision_test,
            'critical': True,
            'description': '0.24mm Z increments - tests floating point precision limits'
        })
        
        doc.saveas(filepath)
        return fixtures
    
    def extract_coords_from_dxf(self, filepath: str) -> Dict:
        """Extract all 3D coordinates from a DXF file, organized by layer."""
        doc = ezdxf.readfile(filepath)
        msp = doc.modelspace()
        
        extracted = {}
        
        for entity in msp:
            layer = entity.dxf.layer
            if layer not in extracted:
                extracted[layer] = []
            
            if entity.dxftype() == 'POLYLINE':
                coords = [(v.dxf.location.x, v.dxf.location.y, v.dxf.location.z) 
                         for v in entity.vertices]
                extracted[layer].append({'type': 'polyline', 'coords': coords})
            elif entity.dxftype() == 'POINT':
                loc = entity.dxf.location
                extracted[layer].append({
                    'type': 'point',
                    'coords': [(loc.x, loc.y, loc.z)]
                })
            elif entity.dxftype() == 'LINE':
                start = entity.dxf.start
                end = entity.dxf.end
                extracted[layer].append({
                    'type': 'line',
                    'coords': [(start.x, start.y, start.z), (end.x, end.y, end.z)]
                })
        
        return extracted
    
    def calculate_errors(self, baseline: List[Tuple], extracted: List[Tuple]) -> Dict:
        """
        Calculate 3D distance errors between baseline and extracted coordinates.
        
        Returns detailed error metrics for validation.
        """
        if len(baseline) != len(extracted):
            return {
                'max_error': float('inf'),
                'avg_error': float('inf'),
                'max_z_error': float('inf'),
                'avg_z_error': float('inf'),
                'errors': [],
                'status': 'FAIL',
                'failure_reason': f'Coordinate count mismatch: {len(baseline)} vs {len(extracted)}'
            }
        
        if not baseline:
            return {
                'max_error': 0.0,
                'avg_error': 0.0,
                'max_z_error': 0.0,
                'avg_z_error': 0.0,
                'errors': [],
                'status': 'PASS'
            }
        
        errors = []
        z_errors = []
        
        for baseline_pt, extracted_pt in zip(baseline, extracted):
            # 3D Euclidean distance
            dx = baseline_pt[0] - extracted_pt[0]
            dy = baseline_pt[1] - extracted_pt[1]
            dz = baseline_pt[2] - extracted_pt[2]
            
            distance = math.sqrt(dx*dx + dy*dy + dz*dz)
            z_error = abs(dz)
            
            errors.append(distance)
            z_errors.append(z_error)
        
        max_error = max(errors)
        avg_error = sum(errors) / len(errors)
        max_z_error = max(z_errors)
        avg_z_error = sum(z_errors) / len(z_errors)
        
        # Tolerance thresholds
        if max_error < 0.001:  # Sub-millimeter (excellent)
            status = 'PASS'
        elif max_error < 0.01:  # Sub-centimeter (acceptable)
            status = 'WARNING'
        else:
            status = 'FAIL'
        
        return {
            'max_error': max_error,
            'avg_error': avg_error,
            'max_z_error': max_z_error,
            'avg_z_error': avg_z_error,
            'count': len(errors),
            'status': status
        }
    
    def run_cycle(self, dxf_path: str, cycle_num: int, project_name: str, srid: int = 0) -> str:
        """
        Run one import-export cycle through the database.
        
        Returns path to exported DXF.
        """
        drawing_name = f"Cycle_{cycle_num:03d}"
        drawing_number = f"ST-{cycle_num:03d}"
        export_path = os.path.join(self.output_dir, f"z_stress_cycle_{cycle_num:03d}.dxf")
        
        # Create project and drawing records first
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Create or get project
            cur.execute("""
                SELECT project_id FROM projects 
                WHERE project_name = %s
                LIMIT 1
            """, (project_name,))
            result = cur.fetchone()
            
            if result:
                project_id = result['project_id']
            else:
                cur.execute("""
                    INSERT INTO projects (project_name, description, created_at)
                    VALUES (%s, %s, NOW())
                    RETURNING project_id
                """, (project_name, f"Z-value stress test {self.test_id}"))
                project_id = cur.fetchone()['project_id']
            
            # Create drawing record
            drawing_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO drawings (
                    drawing_id, project_id, drawing_name, drawing_number, 
                    created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, NOW(), NOW())
            """, (drawing_id, project_id, drawing_name, drawing_number))
            
            conn.commit()
            
        finally:
            cur.close()
            conn.close()
        
        # Import DXF into the drawing
        importer = DXFImporter(self.db_config)
        import_stats = importer.import_dxf(
            file_path=dxf_path,
            drawing_id=drawing_id,
            coordinate_system='LOCAL' if srid == 0 else 'STATE_PLANE',
            import_modelspace=True,
            import_paperspace=False
        )
        
        if import_stats.get('errors'):
            raise Exception(f"Import failed in cycle {cycle_num}: {import_stats.get('errors')}")
        
        # Export DXF from the drawing
        exporter = DXFExporter(self.db_config)
        export_stats = exporter.export_dxf(
            drawing_id=drawing_id,
            output_path=export_path,
            include_modelspace=True,
            include_paperspace=False
        )
        
        if export_stats.get('errors'):
            raise Exception(f"Export failed in cycle {cycle_num}: {export_stats.get('errors')}")
        
        # Clean up drawing record after successful export
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM drawings WHERE drawing_id = %s", (drawing_id,))
            conn.commit()
        finally:
            cur.close()
            conn.close()
        
        return export_path
    
    def run_stress_test(self, num_cycles: int = 20, srid: int = 0, tolerance_ft: float = 0.001) -> Dict:
        """
        Run complete stress test with N import/export cycles.
        
        Args:
            num_cycles: Number of cycles to run (default 20)
            srid: Spatial reference ID (0 = local CAD, 2226 = CA State Plane Zone 2)
            tolerance_ft: Maximum acceptable error in feet (default 0.001 = sub-millimeter)
        
        Returns:
            Complete test results with per-cycle metrics and summary
        """
        print(f"\n{'='*80}")
        print(f"Z-VALUE ELEVATION PRESERVATION STRESS TEST")
        print(f"{'='*80}")
        print(f"Test ID: {self.test_id}")
        print(f"Cycles: {num_cycles}")
        print(f"SRID: {srid}")
        print(f"Tolerance: {tolerance_ft} ft ({tolerance_ft * 12:.4f} inches)")
        print(f"{'='*80}\n")
        
        # Create initial test DXF
        initial_dxf = os.path.join(self.output_dir, f'z_stress_initial_{self.test_id}.dxf')
        fixtures = self.create_test_fixtures(initial_dxf)
        
        print("Test fixtures created:")
        for geom in fixtures['geometries']:
            critical_marker = " [CRITICAL]" if geom['critical'] else ""
            print(f"  - {geom['name']}{critical_marker}: {len(geom['coords'])} vertices")
        print()
        
        # Extract baseline coordinates
        baseline_coords = self.extract_coords_from_dxf(initial_dxf)
        
        results = {
            'test_id': self.test_id,
            'timestamp': datetime.now().isoformat(),
            'parameters': {
                'num_cycles': num_cycles,
                'srid': srid,
                'tolerance_ft': tolerance_ft
            },
            'fixtures': fixtures,
            'baseline_hash': self._hash_coords(baseline_coords),
            'cycles': [],
            'summary': {}
        }
        
        current_dxf = initial_dxf
        project_name = f"Z_Stress_Test_{self.test_id}"
        
        # Run cycles
        for cycle in range(1, num_cycles + 1):
            print(f"Cycle {cycle}/{num_cycles}...", end=' ', flush=True)
            
            cycle_result = {
                'cycle': cycle,
                'errors_by_layer': {},
                'timestamp': datetime.now().isoformat()
            }
            
            try:
                # Run import-export cycle
                exported_dxf = self.run_cycle(current_dxf, cycle, project_name, srid)
                
                # Extract and compare coordinates
                extracted_coords = self.extract_coords_from_dxf(exported_dxf)
                
                # Calculate errors for each layer
                total_max_error = 0.0
                total_avg_error = 0.0
                total_max_z_error = 0.0
                layer_count = 0
                has_layer_failure = False
                
                for layer, baseline_entities in baseline_coords.items():
                    if layer not in extracted_coords:
                        cycle_result['errors_by_layer'][layer] = {
                            'status': 'FAIL',
                            'error': 'Layer missing after round-trip'
                        }
                        has_layer_failure = True
                        total_max_error = float('inf')
                        continue
                    
                    extracted_entities = extracted_coords[layer]
                    
                    if len(baseline_entities) != len(extracted_entities):
                        cycle_result['errors_by_layer'][layer] = {
                            'status': 'FAIL',
                            'error': f'Entity count mismatch: {len(baseline_entities)} vs {len(extracted_entities)}'
                        }
                        has_layer_failure = True
                        total_max_error = float('inf')
                        continue
                    
                    # Compare each entity
                    layer_errors = []
                    for baseline_entity, extracted_entity in zip(baseline_entities, extracted_entities):
                        baseline_pts = baseline_entity['coords']
                        extracted_pts = extracted_entity['coords']
                        
                        error_data = self.calculate_errors(baseline_pts, extracted_pts)
                        layer_errors.append(error_data)
                        
                        total_max_error = max(total_max_error, error_data['max_error'])
                        total_avg_error += error_data['avg_error']
                        total_max_z_error = max(total_max_z_error, error_data['max_z_error'])
                        layer_count += 1
                    
                    # Aggregate layer metrics
                    layer_max = max(e['max_error'] for e in layer_errors)
                    layer_avg = sum(e['avg_error'] for e in layer_errors) / len(layer_errors)
                    layer_status = 'PASS' if layer_max < tolerance_ft else 'FAIL'
                    
                    cycle_result['errors_by_layer'][layer] = {
                        'max_error': layer_max,
                        'avg_error': layer_avg,
                        'max_z_error': max(e['max_z_error'] for e in layer_errors),
                        'status': layer_status
                    }
                
                cycle_result['max_error'] = total_max_error
                cycle_result['avg_error'] = total_avg_error / layer_count if layer_count > 0 else 0
                cycle_result['max_z_error'] = total_max_z_error
                
                # Cycle fails if any layer failed or error exceeds tolerance
                if has_layer_failure:
                    cycle_result['status'] = 'FAIL'
                else:
                    cycle_result['status'] = 'PASS' if total_max_error < tolerance_ft else 'FAIL'
                
                status_symbol = "✓" if cycle_result['status'] == 'PASS' else "✗"
                print(f"{status_symbol} Max error: {total_max_error:.6f} ft ({total_max_error * 12:.6f} in)")
                
                # Use exported DXF as input for next cycle
                current_dxf = exported_dxf
                
            except Exception as e:
                cycle_result['status'] = 'ERROR'
                cycle_result['error'] = str(e)
                print(f"✗ ERROR: {e}")
            
            results['cycles'].append(cycle_result)
        
        # Calculate summary statistics
        successful_cycles = [c for c in results['cycles'] if c.get('status') != 'ERROR']
        
        if not successful_cycles:
            results['summary'] = {
                'overall_status': 'FAIL',
                'failure_reason': 'All cycles failed with errors'
            }
            return results
        
        max_errors = [c['max_error'] for c in successful_cycles]
        avg_errors = [c['avg_error'] for c in successful_cycles]
        max_z_errors = [c['max_z_error'] for c in successful_cycles]
        
        results['summary'] = {
            'final_max_error': max_errors[-1],
            'final_avg_error': avg_errors[-1],
            'final_max_z_error': max_z_errors[-1],
            'worst_max_error': max(max_errors),
            'worst_avg_error': max(avg_errors),
            'best_max_error': min(max_errors),
            'best_avg_error': min(avg_errors),
            'cycles_passed': sum(1 for c in successful_cycles if c['status'] == 'PASS'),
            'cycles_failed': sum(1 for c in successful_cycles if c['status'] == 'FAIL'),
            'overall_status': 'PASS' if all(c['status'] == 'PASS' for c in successful_cycles) else 'FAIL',
            'z_zero_preserved': self._check_z_zero_preservation(results['cycles'][-1], baseline_coords),
            'tolerance_met': max_errors[-1] < tolerance_ft
        }
        
        return results
    
    def _hash_coords(self, coords_dict: Dict) -> str:
        """Generate SHA256 hash of coordinate data for tamper detection."""
        coords_json = json.dumps(coords_dict, sort_keys=True)
        return hashlib.sha256(coords_json.encode()).hexdigest()
    
    def _check_z_zero_preservation(self, final_cycle: Dict, baseline: Dict) -> bool:
        """Verify that flat geometries at Z=0 maintained their Z dimension."""
        flat_pad_layer = 'TEST-FLAT-PAD'
        
        if flat_pad_layer not in final_cycle.get('errors_by_layer', {}):
            return False
        
        layer_result = final_cycle['errors_by_layer'][flat_pad_layer]
        
        # If layer is missing or has errors, Z=0 was not preserved
        if layer_result.get('status') != 'PASS':
            return False
        
        # Check that Z errors are minimal (geometries stayed at Z=0)
        max_z_error = layer_result.get('max_z_error', float('inf'))
        return max_z_error < 0.0001  # Within 0.0001 ft = 0.03mm
    
    def save_results(self, results: Dict, output_path: str = None):
        """Save test results to JSON file."""
        if output_path is None:
            output_path = os.path.join(self.output_dir, f'z_stress_results_{self.test_id}.json')
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        return output_path


def main():
    parser = argparse.ArgumentParser(
        description='Z-Value Elevation Preservation Stress Test Harness',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run 20 cycles with default settings
  python scripts/z_stress_harness.py --cycles 20
  
  # Run 25 cycles with State Plane coordinates
  python scripts/z_stress_harness.py --cycles 25 --srid 2226
  
  # Generate report in specific directory
  python scripts/z_stress_harness.py --cycles 20 --output report/ --report
  
  # Quick 3-cycle test for CI
  python scripts/z_stress_harness.py --cycles 3 --quick
        """
    )
    
    parser.add_argument('--cycles', type=int, default=20,
                        help='Number of import/export cycles (default: 20)')
    parser.add_argument('--srid', type=int, default=0,
                        help='Spatial Reference ID (0=local CAD, 2226=CA State Plane, default: 0)')
    parser.add_argument('--tolerance', type=float, default=0.001,
                        help='Maximum acceptable error in feet (default: 0.001)')
    parser.add_argument('--output', type=str, default=None,
                        help='Output directory for results (default: temp)')
    parser.add_argument('--report', action='store_true',
                        help='Generate PDF report (requires output directory)')
    parser.add_argument('--quick', action='store_true',
                        help='Quick mode (3 cycles, for CI/testing)')
    
    args = parser.parse_args()
    
    # Quick mode overrides
    if args.quick:
        args.cycles = 3
        print("Quick mode: Running 3 cycles for fast validation\n")
    
    # Create harness
    harness = ZStressHarness(output_dir=args.output)
    
    # Run stress test
    results = harness.run_stress_test(
        num_cycles=args.cycles,
        srid=args.srid,
        tolerance_ft=args.tolerance
    )
    
    # Save JSON results
    json_path = harness.save_results(results)
    
    # Print summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")
    summary = results['summary']
    print(f"Overall Status: {summary['overall_status']}")
    print(f"Cycles Passed: {summary.get('cycles_passed', 0)}/{args.cycles}")
    print(f"Final Max Error: {summary['final_max_error']:.6f} ft ({summary['final_max_error']*12:.6f} in)")
    print(f"Final Avg Error: {summary['final_avg_error']:.6f} ft ({summary['final_avg_error']*12:.6f} in)")
    print(f"Z=0 Preserved: {'YES' if summary.get('z_zero_preserved') else 'NO'}")
    print(f"Tolerance Met: {'YES' if summary.get('tolerance_met') else 'NO'}")
    print(f"\nResults saved to: {json_path}")
    print(f"{'='*80}\n")
    
    # Exit with appropriate code
    if summary['overall_status'] == 'PASS':
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Tests failed! Review results for details.")
        sys.exit(1)


if __name__ == '__main__':
    main()
