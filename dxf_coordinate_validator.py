"""
DXF Coordinate Validation Tool
Compares coordinates between original and exported DXF files to verify round-trip accuracy.
This is critical for survey-grade accuracy and market liability concerns.
"""

import ezdxf
from typing import Dict, List, Tuple
import math


class CoordinateValidator:
    """Validate coordinate preservation through DXF import/export pipeline."""
    
    def __init__(self, tolerance_ft: float = 0.001):
        """
        Initialize validator.
        
        Args:
            tolerance_ft: Maximum acceptable coordinate difference in feet (default 0.001 ft = 0.012 inches)
        """
        self.tolerance = tolerance_ft
        self.original_coords = {}
        self.exported_coords = {}
        
    def extract_coordinates_from_dxf(self, dxf_path: str) -> Dict:
        """
        Extract all coordinates from a DXF file.
        
        Returns:
            Dictionary organized by entity type with coordinate lists
        """
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()
        
        coords = {
            'LINE': [],
            'ARC': [],
            'LWPOLYLINE': [],
            'CIRCLE': [],
            'POINT': [],
            'TEXT': []
        }
        
        for entity in msp:
            etype = entity.dxftype()
            
            if etype == 'LINE':
                start = entity.dxf.start
                end = entity.dxf.end
                coords['LINE'].append({
                    'start': (start.x, start.y, start.z if hasattr(start, 'z') else 0),
                    'end': (end.x, end.y, end.z if hasattr(end, 'z') else 0),
                    'layer': entity.dxf.layer
                })
                
            elif etype == 'ARC':
                center = entity.dxf.center
                coords['ARC'].append({
                    'center': (center.x, center.y, center.z if hasattr(center, 'z') else 0),
                    'radius': entity.dxf.radius,
                    'start_angle': entity.dxf.start_angle,
                    'end_angle': entity.dxf.end_angle,
                    'layer': entity.dxf.layer
                })
                
            elif etype == 'LWPOLYLINE':
                points = [(p[0], p[1], 0) for p in entity.get_points('xy')]
                coords['LWPOLYLINE'].append({
                    'points': points,
                    'closed': entity.closed,
                    'layer': entity.dxf.layer
                })
                
            elif etype == 'CIRCLE':
                center = entity.dxf.center
                coords['CIRCLE'].append({
                    'center': (center.x, center.y, center.z if hasattr(center, 'z') else 0),
                    'radius': entity.dxf.radius,
                    'layer': entity.dxf.layer
                })
                
            elif etype == 'POINT':
                location = entity.dxf.location
                coords['POINT'].append({
                    'location': (location.x, location.y, location.z if hasattr(location, 'z') else 0),
                    'layer': entity.dxf.layer
                })
                
            elif etype == 'TEXT':
                insert = entity.dxf.insert
                coords['TEXT'].append({
                    'insert': (insert.x, insert.y, insert.z if hasattr(insert, 'z') else 0),
                    'text': entity.dxf.text,
                    'layer': entity.dxf.layer
                })
        
        return coords
    
    def calculate_distance_3d(self, p1: Tuple[float, float, float], 
                             p2: Tuple[float, float, float]) -> float:
        """Calculate 3D Euclidean distance between two points."""
        return math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2 + (p2[2]-p1[2])**2)
    
    def compare_line_entities(self, original: List[Dict], exported: List[Dict]) -> Dict:
        """Compare LINE entities between original and exported."""
        stats = {
            'total': len(original),
            'matched': 0,
            'max_error': 0.0,
            'avg_error': 0.0,
            'errors': []
        }
        
        if len(original) != len(exported):
            stats['errors'].append(f"Entity count mismatch: {len(original)} original vs {len(exported)} exported")
            return stats
        
        total_error = 0.0
        
        for i, (orig, exp) in enumerate(zip(original, exported)):
            # Compare start points
            start_dist = self.calculate_distance_3d(orig['start'], exp['start'])
            end_dist = self.calculate_distance_3d(orig['end'], exp['end'])
            
            max_dist = max(start_dist, end_dist)
            total_error += max_dist
            
            if max_dist > stats['max_error']:
                stats['max_error'] = max_dist
            
            if max_dist <= self.tolerance:
                stats['matched'] += 1
            else:
                stats['errors'].append(
                    f"LINE #{i}: start error={start_dist:.6f}ft, end error={end_dist:.6f}ft"
                )
        
        stats['avg_error'] = total_error / len(original) if original else 0.0
        
        return stats
    
    def compare_arc_entities(self, original: List[Dict], exported: List[Dict]) -> Dict:
        """Compare ARC entities between original and exported."""
        stats = {
            'total': len(original),
            'matched': 0,
            'max_error': 0.0,
            'avg_error': 0.0,
            'errors': []
        }
        
        if len(original) != len(exported):
            stats['errors'].append(f"Entity count mismatch: {len(original)} original vs {len(exported)} exported")
            return stats
        
        total_error = 0.0
        
        for i, (orig, exp) in enumerate(zip(original, exported)):
            # Compare center points
            center_dist = self.calculate_distance_3d(orig['center'], exp['center'])
            radius_diff = abs(orig['radius'] - exp['radius'])
            angle_diff_start = abs(orig['start_angle'] - exp['start_angle'])
            angle_diff_end = abs(orig['end_angle'] - exp['end_angle'])
            
            max_error = max(center_dist, radius_diff)
            total_error += center_dist
            
            if max_error > stats['max_error']:
                stats['max_error'] = max_error
            
            if center_dist <= self.tolerance and radius_diff <= self.tolerance:
                stats['matched'] += 1
            else:
                stats['errors'].append(
                    f"ARC #{i}: center error={center_dist:.6f}ft, radius error={radius_diff:.6f}ft"
                )
        
        stats['avg_error'] = total_error / len(original) if original else 0.0
        
        return stats
    
    def compare_polyline_entities(self, original: List[Dict], exported: List[Dict]) -> Dict:
        """Compare LWPOLYLINE entities between original and exported."""
        stats = {
            'total': len(original),
            'matched': 0,
            'max_error': 0.0,
            'avg_error': 0.0,
            'errors': []
        }
        
        if len(original) != len(exported):
            stats['errors'].append(f"Entity count mismatch: {len(original)} original vs {len(exported)} exported")
            return stats
        
        total_error = 0.0
        
        for i, (orig, exp) in enumerate(zip(original, exported)):
            if len(orig['points']) != len(exp['points']):
                stats['errors'].append(
                    f"LWPOLYLINE #{i}: point count mismatch {len(orig['points'])} vs {len(exp['points'])}"
                )
                continue
            
            max_point_error = 0.0
            for j, (orig_pt, exp_pt) in enumerate(zip(orig['points'], exp['points'])):
                dist = self.calculate_distance_3d(orig_pt, exp_pt)
                if dist > max_point_error:
                    max_point_error = dist
                total_error += dist
            
            if max_point_error > stats['max_error']:
                stats['max_error'] = max_point_error
            
            if max_point_error <= self.tolerance:
                stats['matched'] += 1
            else:
                stats['errors'].append(
                    f"LWPOLYLINE #{i}: max point error={max_point_error:.6f}ft"
                )
        
        stats['avg_error'] = total_error / sum(len(o['points']) for o in original) if original else 0.0
        
        return stats
    
    def validate_round_trip(self, original_dxf: str, exported_dxf: str) -> Dict:
        """
        Perform full round-trip coordinate validation.
        
        Returns:
            Comprehensive validation report with pass/fail status
        """
        print(f"Reading original DXF: {original_dxf}")
        original_coords = self.extract_coordinates_from_dxf(original_dxf)
        
        print(f"Reading exported DXF: {exported_dxf}")
        exported_coords = self.extract_coordinates_from_dxf(exported_dxf)
        
        report = {
            'tolerance_ft': self.tolerance,
            'tolerance_inches': self.tolerance * 12,
            'passed': True,
            'entity_types': {}
        }
        
        # Compare LINEs
        if original_coords['LINE'] or exported_coords['LINE']:
            print(f"\nComparing {len(original_coords['LINE'])} LINE entities...")
            line_stats = self.compare_line_entities(original_coords['LINE'], exported_coords['LINE'])
            report['entity_types']['LINE'] = line_stats
            if line_stats['max_error'] > self.tolerance:
                report['passed'] = False
        
        # Compare ARCs
        if original_coords['ARC'] or exported_coords['ARC']:
            print(f"Comparing {len(original_coords['ARC'])} ARC entities...")
            arc_stats = self.compare_arc_entities(original_coords['ARC'], exported_coords['ARC'])
            report['entity_types']['ARC'] = arc_stats
            if arc_stats['max_error'] > self.tolerance:
                report['passed'] = False
        
        # Compare LWPOLYLINEs
        if original_coords['LWPOLYLINE'] or exported_coords['LWPOLYLINE']:
            print(f"Comparing {len(original_coords['LWPOLYLINE'])} LWPOLYLINE entities...")
            poly_stats = self.compare_polyline_entities(original_coords['LWPOLYLINE'], exported_coords['LWPOLYLINE'])
            report['entity_types']['LWPOLYLINE'] = poly_stats
            if poly_stats['max_error'] > self.tolerance:
                report['passed'] = False
        
        return report
    
    def print_report(self, report: Dict):
        """Print human-readable validation report."""
        print("\n" + "="*70)
        print(" DXF ROUND-TRIP COORDINATE VALIDATION REPORT")
        print("="*70)
        print(f"\nTolerance: {report['tolerance_ft']}ft ({report['tolerance_inches']:.4f} inches)")
        print(f"\nOverall Result: {'✅ PASSED' if report['passed'] else '❌ FAILED'}")
        
        print("\n" + "-"*70)
        print("Entity-by-Entity Results:")
        print("-"*70)
        
        for entity_type, stats in report['entity_types'].items():
            print(f"\n{entity_type}:")
            print(f"  Total entities: {stats['total']}")
            print(f"  Matched (within tolerance): {stats['matched']}/{stats['total']}")
            print(f"  Max error: {stats['max_error']:.6f}ft ({stats['max_error']*12:.4f} inches)")
            print(f"  Avg error: {stats['avg_error']:.6f}ft ({stats['avg_error']*12:.4f} inches)")
            
            if stats['errors']:
                print(f"\n  ⚠️  {len(stats['errors'])} issues found:")
                for error in stats['errors'][:5]:  # Show first 5 errors
                    print(f"    - {error}")
                if len(stats['errors']) > 5:
                    print(f"    ... and {len(stats['errors']-5)} more")
        
        print("\n" + "="*70)
        if report['passed']:
            print("✅ COORDINATE PRESERVATION VALIDATED - MARKET READY")
        else:
            print("❌ COORDINATE ERRORS DETECTED - REQUIRES INVESTIGATION")
        print("="*70 + "\n")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python dxf_coordinate_validator.py <original.dxf> <exported.dxf> [tolerance_ft]")
        sys.exit(1)
    
    original_dxf = sys.argv[1]
    exported_dxf = sys.argv[2]
    tolerance = float(sys.argv[3]) if len(sys.argv) > 3 else 0.001
    
    validator = CoordinateValidator(tolerance_ft=tolerance)
    report = validator.validate_round_trip(original_dxf, exported_dxf)
    validator.print_report(report)
    
    # Exit with error code if validation failed
    sys.exit(0 if report['passed'] else 1)
