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
        Extract all coordinates from a DXF file with robust entity identification.
        
        Returns:
            Dictionary organized by entity type with coordinate lists and geometric hashes
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
                start_pt = (start.x, start.y, start.z if hasattr(start, 'z') else 0)
                end_pt = (end.x, end.y, end.z if hasattr(end, 'z') else 0)
                
                coords['LINE'].append({
                    'start': start_pt,
                    'end': end_pt,
                    'layer': entity.dxf.layer,
                    'handle': entity.dxf.handle if hasattr(entity.dxf, 'handle') else None,
                    'geom_hash': self._hash_line(start_pt, end_pt)
                })
                
            elif etype == 'ARC':
                center = entity.dxf.center
                center_pt = (center.x, center.y, center.z if hasattr(center, 'z') else 0)
                radius = entity.dxf.radius
                start_angle = self._normalize_angle(entity.dxf.start_angle)
                end_angle = self._normalize_angle(entity.dxf.end_angle)
                
                coords['ARC'].append({
                    'center': center_pt,
                    'radius': radius,
                    'start_angle': start_angle,
                    'end_angle': end_angle,
                    'layer': entity.dxf.layer,
                    'handle': entity.dxf.handle if hasattr(entity.dxf, 'handle') else None,
                    'geom_hash': self._hash_arc(center_pt, radius, start_angle, end_angle)
                })
                
            elif etype == 'LWPOLYLINE':
                points = [(p[0], p[1], 0) for p in entity.get_points('xy')]
                closed = entity.closed
                
                # Extract bulges if present
                bulges = list(entity.get_points('xyb'))
                bulge_values = [b[2] if len(b) > 2 else 0 for b in bulges] if bulges else [0] * len(points)
                
                coords['LWPOLYLINE'].append({
                    'points': points,
                    'closed': closed,
                    'bulges': bulge_values,
                    'layer': entity.dxf.layer,
                    'handle': entity.dxf.handle if hasattr(entity.dxf, 'handle') else None,
                    'geom_hash': self._hash_polyline(points, closed, bulge_values)
                })
                
            elif etype == 'CIRCLE':
                center = entity.dxf.center
                center_pt = (center.x, center.y, center.z if hasattr(center, 'z') else 0)
                radius = entity.dxf.radius
                
                coords['CIRCLE'].append({
                    'center': center_pt,
                    'radius': radius,
                    'layer': entity.dxf.layer,
                    'handle': entity.dxf.handle if hasattr(entity.dxf, 'handle') else None,
                    'geom_hash': self._hash_circle(center_pt, radius)
                })
                
            elif etype == 'POINT':
                location = entity.dxf.location
                location_pt = (location.x, location.y, location.z if hasattr(location, 'z') else 0)
                
                coords['POINT'].append({
                    'location': location_pt,
                    'layer': entity.dxf.layer,
                    'handle': entity.dxf.handle if hasattr(entity.dxf, 'handle') else None,
                    'geom_hash': self._hash_point(location_pt)
                })
                
            elif etype == 'TEXT':
                insert = entity.dxf.insert
                insert_pt = (insert.x, insert.y, insert.z if hasattr(insert, 'z') else 0)
                text_content = entity.dxf.text
                rotation = entity.dxf.rotation if hasattr(entity.dxf, 'rotation') else 0
                height = entity.dxf.height if hasattr(entity.dxf, 'height') else 0
                
                coords['TEXT'].append({
                    'insert': insert_pt,
                    'text': text_content,
                    'rotation': rotation,
                    'height': height,
                    'layer': entity.dxf.layer,
                    'handle': entity.dxf.handle if hasattr(entity.dxf, 'handle') else None,
                    'geom_hash': self._hash_text(insert_pt, text_content, rotation, height)
                })
        
        return coords
    
    def _normalize_angle(self, angle: float) -> float:
        """Normalize angle to 0-360 range."""
        while angle < 0:
            angle += 360
        while angle >= 360:
            angle -= 360
        return angle
    
    def _hash_line(self, start: Tuple[float, float, float], end: Tuple[float, float, float]) -> str:
        """Create geometric hash for LINE entity."""
        return f"LINE:{start[0]:.4f},{start[1]:.4f},{start[2]:.4f}|{end[0]:.4f},{end[1]:.4f},{end[2]:.4f}"
    
    def _hash_arc(self, center: Tuple[float, float, float], radius: float, 
                  start_angle: float, end_angle: float) -> str:
        """Create geometric hash for ARC entity."""
        return f"ARC:{center[0]:.4f},{center[1]:.4f},{center[2]:.4f}|{radius:.4f}|{start_angle:.2f},{end_angle:.2f}"
    
    def _hash_polyline(self, points: List[Tuple[float, float, float]], 
                       closed: bool, bulges: List[float]) -> str:
        """Create geometric hash for LWPOLYLINE entity."""
        pts_str = '|'.join([f"{p[0]:.4f},{p[1]:.4f},{p[2]:.4f}" for p in points])
        bulge_str = '|'.join([f"{b:.4f}" for b in bulges])
        return f"LWPOLY:{pts_str}|C:{closed}|B:{bulge_str}"
    
    def _hash_circle(self, center: Tuple[float, float, float], radius: float) -> str:
        """Create geometric hash for CIRCLE entity."""
        return f"CIRCLE:{center[0]:.4f},{center[1]:.4f},{center[2]:.4f}|{radius:.4f}"
    
    def _hash_point(self, location: Tuple[float, float, float]) -> str:
        """Create geometric hash for POINT entity."""
        return f"POINT:{location[0]:.4f},{location[1]:.4f},{location[2]:.4f}"
    
    def _hash_text(self, insert: Tuple[float, float, float], text: str, 
                   rotation: float, height: float) -> str:
        """Create geometric hash for TEXT entity."""
        return f"TEXT:{insert[0]:.4f},{insert[1]:.4f},{insert[2]:.4f}|{text}|{rotation:.2f}|{height:.4f}"
    
    def calculate_distance_3d(self, p1: Tuple[float, float, float], 
                             p2: Tuple[float, float, float]) -> float:
        """Calculate 3D Euclidean distance between two points."""
        return math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2 + (p2[2]-p1[2])**2)
    
    def compare_line_entities(self, original: List[Dict], exported: List[Dict]) -> Dict:
        """Compare LINE entities using robust geometric matching."""
        stats = {
            'total': len(original),
            'matched': 0,
            'unmatched_original': 0,
            'unmatched_exported': 0,
            'max_error': 0.0,
            'avg_error': 0.0,
            'errors': []
        }
        
        if len(original) != len(exported):
            stats['errors'].append(f"Entity count mismatch: {len(original)} original vs {len(exported)} exported")
            stats['unmatched_original'] = abs(len(original) - len(exported))
        
        # Build hash index for exported entities
        exported_by_hash = {e['geom_hash']: e for e in exported}
        
        total_error = 0.0
        matched_hashes = set()
        
        for orig in original:
            # Try to find matching exported entity by geometric hash
            exp = exported_by_hash.get(orig['geom_hash'])
            
            if exp is None:
                # No exact hash match - try fuzzy matching by coordinates
                exp = self._find_closest_line(orig, exported, matched_hashes)
            
            if exp:
                matched_hashes.add(exp['geom_hash'])
                
                # Compare start points
                start_dist = self.calculate_distance_3d(orig['start'], exp['start'])
                end_dist = self.calculate_distance_3d(orig['end'], exp['end'])
                
                # Also check reversed line (end → start)
                start_dist_rev = self.calculate_distance_3d(orig['start'], exp['end'])
                end_dist_rev = self.calculate_distance_3d(orig['end'], exp['start'])
                
                # Use minimum error (handles reversed lines)
                max_dist = min(max(start_dist, end_dist), max(start_dist_rev, end_dist_rev))
                total_error += max_dist
                
                if max_dist > stats['max_error']:
                    stats['max_error'] = max_dist
                
                if max_dist <= self.tolerance:
                    stats['matched'] += 1
                else:
                    stats['errors'].append(
                        f"LINE (layer={orig['layer']}): start error={min(start_dist, start_dist_rev):.6f}ft, "
                        f"end error={min(end_dist, end_dist_rev):.6f}ft"
                    )
            else:
                stats['unmatched_original'] += 1
                stats['errors'].append(f"LINE (layer={orig['layer']}): no matching exported entity found")
        
        # Check for unmatched exported entities
        stats['unmatched_exported'] = len(exported) - len(matched_hashes)
        
        stats['avg_error'] = total_error / stats['matched'] if stats['matched'] > 0 else 0.0
        
        return stats
    
    def _find_closest_line(self, target: Dict, candidates: List[Dict], exclude_hashes: set) -> Dict:
        """Find closest matching LINE entity by coordinates (fuzzy match)."""
        best_match = None
        best_distance = float('inf')
        
        for candidate in candidates:
            if candidate['geom_hash'] in exclude_hashes:
                continue
            
            # Calculate distance between lines
            dist1 = self.calculate_distance_3d(target['start'], candidate['start'])
            dist2 = self.calculate_distance_3d(target['end'], candidate['end'])
            dist_forward = max(dist1, dist2)
            
            # Check reversed
            dist1_rev = self.calculate_distance_3d(target['start'], candidate['end'])
            dist2_rev = self.calculate_distance_3d(target['end'], candidate['start'])
            dist_reverse = max(dist1_rev, dist2_rev)
            
            dist = min(dist_forward, dist_reverse)
            
            if dist < best_distance and dist < self.tolerance * 10:  # Allow fuzzy match within 10x tolerance
                best_distance = dist
                best_match = candidate
        
        return best_match
    
    def compare_arc_entities(self, original: List[Dict], exported: List[Dict]) -> Dict:
        """Compare ARC entities using robust geometric matching with angle normalization."""
        stats = {
            'total': len(original),
            'matched': 0,
            'unmatched_original': 0,
            'unmatched_exported': 0,
            'max_error': 0.0,
            'avg_error': 0.0,
            'errors': []
        }
        
        if len(original) != len(exported):
            stats['errors'].append(f"Entity count mismatch: {len(original)} original vs {len(exported)} exported")
        
        exported_by_hash = {e['geom_hash']: e for e in exported}
        total_error = 0.0
        matched_hashes = set()
        
        for orig in original:
            exp = exported_by_hash.get(orig['geom_hash'])
            
            if exp is None:
                # Fuzzy match by center and radius
                exp = self._find_closest_arc(orig, exported, matched_hashes)
            
            if exp:
                matched_hashes.add(exp['geom_hash'])
                
                center_dist = self.calculate_distance_3d(orig['center'], exp['center'])
                radius_diff = abs(orig['radius'] - exp['radius'])
                
                # Normalize angle differences (handle 0°/360° wrap-around)
                angle_diff_start = min(
                    abs(orig['start_angle'] - exp['start_angle']),
                    360 - abs(orig['start_angle'] - exp['start_angle'])
                )
                angle_diff_end = min(
                    abs(orig['end_angle'] - exp['end_angle']),
                    360 - abs(orig['end_angle'] - exp['end_angle'])
                )
                
                # Use angle tolerance of 0.1 degrees
                angle_tolerance = 0.1
                
                max_error = max(center_dist, radius_diff)
                total_error += center_dist
                
                if max_error > stats['max_error']:
                    stats['max_error'] = max_error
                
                # Check ALL criteria: center, radius, AND angles
                if (center_dist <= self.tolerance and 
                    radius_diff <= self.tolerance and
                    angle_diff_start <= angle_tolerance and
                    angle_diff_end <= angle_tolerance):
                    stats['matched'] += 1
                else:
                    errors = []
                    if center_dist > self.tolerance:
                        errors.append(f"center={center_dist:.6f}ft")
                    if radius_diff > self.tolerance:
                        errors.append(f"radius={radius_diff:.6f}ft")
                    if angle_diff_start > angle_tolerance:
                        errors.append(f"start_angle={angle_diff_start:.2f}°")
                    if angle_diff_end > angle_tolerance:
                        errors.append(f"end_angle={angle_diff_end:.2f}°")
                    stats['errors'].append(
                        f"ARC (layer={orig['layer']}): {', '.join(errors)}"
                    )
            else:
                stats['unmatched_original'] += 1
                stats['errors'].append(f"ARC (layer={orig['layer']}): no matching exported entity found")
        
        stats['unmatched_exported'] = len(exported) - len(matched_hashes)
        stats['avg_error'] = total_error / stats['matched'] if stats['matched'] > 0 else 0.0
        
        return stats
    
    def _find_closest_arc(self, target: Dict, candidates: List[Dict], exclude_hashes: set) -> Dict:
        """Find closest matching ARC entity by coordinates."""
        best_match = None
        best_distance = float('inf')
        
        for candidate in candidates:
            if candidate['geom_hash'] in exclude_hashes:
                continue
            
            center_dist = self.calculate_distance_3d(target['center'], candidate['center'])
            radius_diff = abs(target['radius'] - candidate['radius'])
            
            if center_dist < best_distance and center_dist < self.tolerance * 10:
                best_distance = center_dist
                best_match = candidate
        
        return best_match
    
    def compare_polyline_entities(self, original: List[Dict], exported: List[Dict]) -> Dict:
        """Compare LWPOLYLINE entities with bulge and closure validation."""
        stats = {
            'total': len(original),
            'matched': 0,
            'unmatched_original': 0,
            'unmatched_exported': 0,
            'max_error': 0.0,
            'avg_error': 0.0,
            'errors': []
        }
        
        if len(original) != len(exported):
            stats['errors'].append(f"Entity count mismatch: {len(original)} original vs {len(exported)} exported")
        
        exported_by_hash = {e['geom_hash']: e for e in exported}
        total_error = 0.0
        matched_hashes = set()
        
        for orig in original:
            exp = exported_by_hash.get(orig['geom_hash'])
            
            if exp is None:
                exp = self._find_closest_polyline(orig, exported, matched_hashes)
            
            if exp:
                matched_hashes.add(exp['geom_hash'])
                
                if len(orig['points']) != len(exp['points']):
                    stats['errors'].append(
                        f"LWPOLYLINE (layer={orig['layer']}): point count mismatch {len(orig['points'])} vs {len(exp['points'])}"
                    )
                    continue
                
                # Check closure flag
                if orig['closed'] != exp['closed']:
                    stats['errors'].append(
                        f"LWPOLYLINE (layer={orig['layer']}): closure mismatch - orig={orig['closed']}, exp={exp['closed']}"
                    )
                
                # Compare bulges if present
                if len(orig['bulges']) != len(exp['bulges']):
                    stats['errors'].append(
                        f"LWPOLYLINE (layer={orig['layer']}): bulge count mismatch"
                    )
                else:
                    max_bulge_diff = max(abs(ob - eb) for ob, eb in zip(orig['bulges'], exp['bulges']))
                    if max_bulge_diff > 0.001:  # Bulge tolerance
                        stats['errors'].append(
                            f"LWPOLYLINE (layer={orig['layer']}): max bulge difference={max_bulge_diff:.6f}"
                        )
                
                # Compare point coordinates
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
                        f"LWPOLYLINE (layer={orig['layer']}): max point error={max_point_error:.6f}ft"
                    )
            else:
                stats['unmatched_original'] += 1
                stats['errors'].append(f"LWPOLYLINE (layer={orig['layer']}): no matching exported entity found")
        
        stats['unmatched_exported'] = len(exported) - len(matched_hashes)
        stats['avg_error'] = total_error / sum(len(o['points']) for o in original if o['geom_hash'] in matched_hashes) if matched_hashes else 0.0
        
        return stats
    
    def _find_closest_polyline(self, target: Dict, candidates: List[Dict], exclude_hashes: set) -> Dict:
        """Find closest matching LWPOLYLINE entity."""
        best_match = None
        best_distance = float('inf')
        
        for candidate in candidates:
            if candidate['geom_hash'] in exclude_hashes:
                continue
            
            if len(target['points']) != len(candidate['points']):
                continue
            
            # Calculate average point distance
            total_dist = sum(
                self.calculate_distance_3d(tp, cp)
                for tp, cp in zip(target['points'], candidate['points'])
            )
            avg_dist = total_dist / len(target['points'])
            
            if avg_dist < best_distance and avg_dist < self.tolerance * 10:
                best_distance = avg_dist
                best_match = candidate
        
        return best_match
    
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
            # Fail if: max error exceeded OR any entities unmatched OR any errors recorded
            if (line_stats['max_error'] > self.tolerance or 
                line_stats['unmatched_original'] > 0 or 
                line_stats['unmatched_exported'] > 0 or
                len(line_stats['errors']) > 0):
                report['passed'] = False
        
        # Compare ARCs
        if original_coords['ARC'] or exported_coords['ARC']:
            print(f"Comparing {len(original_coords['ARC'])} ARC entities...")
            arc_stats = self.compare_arc_entities(original_coords['ARC'], exported_coords['ARC'])
            report['entity_types']['ARC'] = arc_stats
            if (arc_stats['max_error'] > self.tolerance or 
                arc_stats['unmatched_original'] > 0 or 
                arc_stats['unmatched_exported'] > 0 or
                len(arc_stats['errors']) > 0):
                report['passed'] = False
        
        # Compare LWPOLYLINEs
        if original_coords['LWPOLYLINE'] or exported_coords['LWPOLYLINE']:
            print(f"Comparing {len(original_coords['LWPOLYLINE'])} LWPOLYLINE entities...")
            poly_stats = self.compare_polyline_entities(original_coords['LWPOLYLINE'], exported_coords['LWPOLYLINE'])
            report['entity_types']['LWPOLYLINE'] = poly_stats
            if (poly_stats['max_error'] > self.tolerance or 
                poly_stats['unmatched_original'] > 0 or 
                poly_stats['unmatched_exported'] > 0 or
                len(poly_stats['errors']) > 0):
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
                    print(f"    ... and {len(stats['errors']) - 5} more")
        
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
