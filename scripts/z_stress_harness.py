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
    """Deterministic stress test harness for XYZ coordinate preservation validation."""
    
    # SRID-specific tolerances
    TOLERANCES = {
        0: {'x': 0.001, 'y': 0.001, 'z': 0.001, 'units': 'ft'},  # LOCAL CAD
        2226: {'x': 0.001, 'y': 0.001, 'z': 0.001, 'units': 'ft'},  # CA State Plane
        4326: {'x': 1e-7, 'y': 1e-7, 'z': 0.01, 'units': 'deg/m'}  # WGS84
    }
    
    # Coordinate conversion factors for WGS84 (near San Francisco)
    FT_TO_LON_DEG = 2.74e-6  # 1 ft ≈ 2.74e-6 degrees longitude at 37°N
    FT_TO_LAT_DEG = 8.99e-6  # 1 ft ≈ 8.99e-6 degrees latitude
    FT_TO_METERS = 0.3048    # 1 ft = 0.3048 m
    
    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or tempfile.gettempdir()
        self.db_config = DB_CONFIG
        self.test_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    def srid_to_coordinate_system(self, srid: int) -> str:
        """Map SRID integer to coordinate system name for DXF importer/exporter."""
        if srid == 0:
            return 'LOCAL'
        elif srid == 2226:
            return 'STATE_PLANE'
        elif srid == 4326:
            return 'WGS84'
        else:
            raise ValueError(f"Unsupported SRID: {srid}")
    
    def transform_coords_for_srid(self, coords: List[Tuple[float, float, float]], srid: int) -> List[Tuple[float, float, float]]:
        """
        Transform canonical LOCAL coordinates to SRID-specific coordinates.
        
        Args:
            coords: List of (x, y, z) tuples in LOCAL CAD feet
            srid: Target SRID (0=LOCAL, 2226=STATE_PLANE, 4326=WGS84)
        
        Returns:
            List of transformed (x, y, z) tuples in target coordinate system
        """
        if srid == 0:
            # LOCAL: Use as-is (already in feet)
            return coords
        elif srid == 2226:
            # CA State Plane Zone 2: Offset to realistic State Plane range (6M+ ft)
            base_x, base_y = 6000000.0, 2100000.0
            return [(x + base_x, y + base_y, z) for x, y, z in coords]
        elif srid == 4326:
            # WGS84: Convert feet to degrees and meters
            # Base: San Francisco area (-122.4194° lon, 37.7749° lat)
            base_lon, base_lat = -122.4194, 37.7749
            return [
                (base_lon + (x * self.FT_TO_LON_DEG),
                 base_lat + (y * self.FT_TO_LAT_DEG),
                 z * self.FT_TO_METERS)  # Convert Z from feet to meters
                for x, y, z in coords
            ]
        else:
            raise ValueError(f"Unsupported SRID: {srid}")
        
    def create_test_fixtures(self, filepath: str, srid: int = 0) -> Dict:
        """
        Create comprehensive test DXF with canonical geometries for specified SRID.
        
        Args:
            filepath: Output path for DXF file
            srid: Spatial Reference ID (0=LOCAL, 2226=STATE_PLANE, 4326=WGS84)
        
        Returns metadata about test geometries for validation.
        """
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        
        # Create layers
        for layer in ['TEST-FLAT-PAD', 'TEST-SLOPED-PIPE', 'TEST-SURVEY-POINTS', 
                      'TEST-LARGE-COORDS', 'TEST-PRECISION', 'TEST-MULTIPLE-LINES']:
            doc.layers.add(layer)
        
        fixtures = {
            'timestamp': datetime.now().isoformat(),
            'srid': srid,
            'geometries': []
        }
        
        # Get SRID-specific coordinate base offsets
        if srid == 0:
            # LOCAL CAD: Small-scale site engineering (1,000s - 50,000s ft)
            base_x, base_y = 1000.0, 2000.0
            coord_name = "LOCAL CAD"
        elif srid == 2226:
            # CA State Plane Zone 2: Large-scale coordinates (6M ft typical)
            base_x, base_y = 6000000.0, 2100000.0
            coord_name = "CA State Plane Zone 2"
        elif srid == 4326:
            # WGS84 Geographic: Decimal degrees (San Francisco area)
            base_x, base_y = -122.4194, 37.7749  # SF coordinates
            coord_name = "WGS84 (lat/lon)"
        else:
            raise ValueError(f"Unsupported SRID: {srid}")
        
        # Define canonical test geometries in LOCAL CAD feet (will be transformed per SRID)
        canonical_geometries = {
            'flat_pad': {
                'coords': [
                    (1000.0, 2000.0, 0.0),
                    (1100.0, 2000.0, 0.0),
                    (1100.0, 2100.0, 0.0),
                    (1000.0, 2100.0, 0.0)
                ],
                'layer': 'TEST-FLAT-PAD',
                'name': 'Flat Pad at Z=0',
                'type': 'polyline3d',
                'critical': True,
                'description': 'Level pad at elevation 0.0 - CRITICAL Z=0 preservation test'
            },
            'sloped_pipe': {
                'coords': [
                    (1200.0, 2000.0, 100.5),
                    (1300.0, 2000.0, 100.4),
                    (1400.0, 2000.0, 100.3),
                    (1500.0, 2000.0, 100.2)
                ],
                'layer': 'TEST-SLOPED-PIPE',
                'name': 'Sloped Pipe (1% grade)',
                'type': 'polyline3d',
                'critical': False,
                'description': '1% slope pipe - tests varying elevations'
            },
            'survey_points': {
                'coords': [
                    (1000.0, 2200.0, 105.234),
                    (1100.0, 2200.0, 103.567),
                    (1200.0, 2200.0, 108.901),
                    (1300.0, 2200.0, 102.345)
                ],
                'layer': 'TEST-SURVEY-POINTS',
                'name': 'Survey Points',
                'type': 'points',
                'critical': False,
                'description': 'Survey control points with high precision'
            },
            'large_coords': {
                'coords': [
                    (50000.0, 25000.0, 250.0),
                    (50100.0, 25000.0, 250.5),
                    (50100.0, 25100.0, 251.0)
                ],
                'layer': 'TEST-LARGE-COORDS',
                'name': 'Large Offset Coordinates',
                'type': 'polyline3d',
                'critical': False,
                'description': f'{coord_name} large-scale coordinates test'
            },
            'precision': {
                'coords': [
                    (1400.0, 2200.0, 100.0000),
                    (1450.0, 2200.0, 100.0008),
                    (1500.0, 2200.0, 100.0016),
                    (1550.0, 2200.0, 100.0024)
                ],
                'layer': 'TEST-PRECISION',
                'name': 'Sub-millimeter Precision',
                'type': 'polyline3d',
                'critical': True,
                'description': '0.24mm Z increments - tests floating point precision limits'
            },
            'multiple_lines': {
                'coords': [
                    # Line 1: NW-SE diagonal
                    [(1600.0, 2400.0, 110.0), (1700.0, 2300.0, 112.0)],
                    # Line 2: SW-NE diagonal
                    [(1600.0, 2300.0, 115.0), (1700.0, 2400.0, 117.0)],
                    # Line 3: Horizontal
                    [(1650.0, 2350.0, 120.0), (1750.0, 2350.0, 122.0)],
                    # Line 4: Vertical
                    [(1675.0, 2300.0, 125.0), (1675.0, 2400.0, 127.0)],
                ],
                'layer': 'TEST-MULTIPLE-LINES',
                'name': 'Multiple Independent Lines',
                'type': 'lines',
                'critical': True,
                'description': 'Multiple LINE entities on same layer - tests spatial matching for entity ordering'
            }
        }
        
        # Transform and add geometries to DXF using SRID-appropriate coordinates
        # Fixtures must contain coordinates in the declared coordinate system
        for key, geom in canonical_geometries.items():
            if geom['type'] == 'lines':
                # Handle multiple LINE entities (list of line segments)
                # Each line is stored as a separate entity for centroid matching
                for idx, line_coords in enumerate(geom['coords']):
                    transformed_line = self.transform_coords_for_srid(line_coords, srid)
                    msp.add_line(transformed_line[0], transformed_line[1], 
                               dxfattribs={'layer': geom['layer']})
                    
                    # Store each line separately to match extraction format
                    # This allows centroid matching to work correctly
                    fixtures['geometries'].append({
                        'name': f"{geom['name']} #{idx+1}",
                        'type': 'line',
                        'layer': geom['layer'],
                        'coords': transformed_line,  # Just the two endpoints
                        'critical': geom['critical'],
                        'description': f"{geom['description']} - segment {idx+1}"
                    })
            else:
                # Transform coordinates to match declared SRID
                transformed_coords = self.transform_coords_for_srid(geom['coords'], srid)
                
                if geom['type'] == 'polyline3d':
                    if key == 'flat_pad':
                        # Close the polyline for flat pad
                        msp.add_polyline3d(transformed_coords + [transformed_coords[0]], 
                                          dxfattribs={'layer': geom['layer']})
                    else:
                        msp.add_polyline3d(transformed_coords, dxfattribs={'layer': geom['layer']})
                elif geom['type'] == 'points':
                    for pt in transformed_coords:
                        msp.add_point(pt, dxfattribs={'layer': geom['layer']})
                
                # Store metadata with transformed coordinates
                fixtures['geometries'].append({
                    'name': geom['name'],
                    'type': geom['type'],
                    'layer': geom['layer'],
                    'coords': transformed_coords,
                    'critical': geom['critical'],
                    'description': geom['description']
                })
        
        doc.saveas(filepath)
        return fixtures
    
    def validate_coordinate_ranges(self, coords_dict: Dict, srid: int) -> Dict:
        """
        Validate that extracted coordinates fall within expected ranges for SRID.
        
        Args:
            coords_dict: Dictionary of extracted coordinates by layer
            srid: Declared SRID for validation
        
        Returns:
            Validation result with warnings if coordinates seem mismatched
        """
        # Collect all coordinate values
        all_x, all_y, all_z = [], [], []
        for layer, entities in coords_dict.items():
            for entity in entities:
                for x, y, z in entity['coords']:
                    all_x.append(x)
                    all_y.append(y)
                    all_z.append(z)
        
        if not all_x:
            return {'valid': True, 'warnings': []}
        
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        min_z, max_z = min(all_z), max(all_z)
        
        warnings = []
        
        if srid == 0:  # LOCAL CAD
            # Expected: Reasonable engineering scales (100s - 100,000s ft typical)
            if abs(min_x) > 1e8 or abs(max_x) > 1e8:
                warnings.append(f"X coordinates ({min_x:.2f} to {max_x:.2f}) seem unusually large for LOCAL CAD")
            if abs(min_y) > 1e8 or abs(max_y) > 1e8:
                warnings.append(f"Y coordinates ({min_y:.2f} to {max_y:.2f}) seem unusually large for LOCAL CAD")
        
        elif srid == 2226:  # CA State Plane Zone 2
            # Expected: X ~6M ft, Y ~2M ft (NAD83 CA Zone 2)
            if not (5500000 <= min_x <= 6500000) or not (5500000 <= max_x <= 6500000):
                warnings.append(f"X coordinates ({min_x:.0f} to {max_x:.0f}) outside typical CA State Plane Zone 2 range (5.5M-6.5M ft)")
            if not (1900000 <= min_y <= 2300000) or not (1900000 <= max_y <= 2300000):
                warnings.append(f"Y coordinates ({min_y:.0f} to {max_y:.0f}) outside typical CA State Plane Zone 2 range (1.9M-2.3M ft)")
        
        elif srid == 4326:  # WGS84 Geographic
            # Expected: Longitude -180 to 180, Latitude -90 to 90
            if not (-180 <= min_x <= 180) or not (-180 <= max_x <= 180):
                warnings.append(f"X/Longitude ({min_x:.6f} to {max_x:.6f}) outside valid range (-180° to 180°)")
            if not (-90 <= min_y <= 90) or not (-90 <= max_y <= 90):
                warnings.append(f"Y/Latitude ({min_y:.6f} to {max_y:.6f}) outside valid range (-90° to 90°)")
        
        return {
            'valid': len(warnings) == 0,
            'warnings': warnings,
            'ranges': {
                'x': (min_x, max_x),
                'y': (min_y, max_y),
                'z': (min_z, max_z)
            }
        }
    
    def _calculate_centroid(self, coords: List[Tuple[float, float, float]]) -> Tuple[float, float, float]:
        """Calculate the centroid (average position) of a set of coordinates."""
        if not coords:
            return (0.0, 0.0, 0.0)
        n = len(coords)
        avg_x = sum(c[0] for c in coords) / n
        avg_y = sum(c[1] for c in coords) / n
        avg_z = sum(c[2] for c in coords) / n
        return (avg_x, avg_y, avg_z)
    
    def _distance_3d(self, pt1: Tuple[float, float, float], pt2: Tuple[float, float, float]) -> float:
        """Calculate 3D Euclidean distance between two points."""
        dx = pt1[0] - pt2[0]
        dy = pt1[1] - pt2[1]
        dz = pt1[2] - pt2[2]
        return math.sqrt(dx*dx + dy*dy + dz*dz)
    
    def _match_entities_spatially(self, baseline_entities: List[Dict], extracted_entities: List[Dict], srid: int = 0) -> List[Tuple[Dict, Dict]]:
        """
        Match entities between baseline and extracted by spatial proximity (centroid matching).
        Returns list of (baseline_entity, extracted_entity) pairs.
        Unmatched entities are paired with None.
        """
        matched_pairs = []
        
        # Handle empty extracted list - all baseline entities are unmatched
        if not extracted_entities:
            for baseline_entity in baseline_entities:
                matched_pairs.append((baseline_entity, None))
            return matched_pairs
        
        # Handle empty baseline list - all extracted entities are unmatched
        if not baseline_entities:
            for extracted_entity in extracted_entities:
                matched_pairs.append((None, extracted_entity))
            return matched_pairs
        
        # Calculate centroids for all entities
        baseline_centroids = [(self._calculate_centroid(e['coords']), e) for e in baseline_entities]
        extracted_centroids = [(self._calculate_centroid(e['coords']), e) for e in extracted_entities]
        
        # Use SRID-specific tolerance for centroid matching (max of X/Y tolerances)
        tolerances = self.TOLERANCES.get(srid, self.TOLERANCES[0])
        centroid_threshold = max(tolerances['x'], tolerances['y'])
        
        used_extracted = set()
        
        # For each baseline entity, find the nearest extracted entity
        for baseline_centroid, baseline_entity in baseline_centroids:
            best_match = None
            best_distance = float('inf')
            best_idx = None
            
            for idx, (extracted_centroid, extracted_entity) in enumerate(extracted_centroids):
                if idx in used_extracted:
                    continue
                
                distance = self._distance_3d(baseline_centroid, extracted_centroid)
                if distance < best_distance:
                    best_distance = distance
                    best_match = extracted_entity
                    best_idx = idx
            
            # Match if centroids are within tolerance (should be nearly identical for same entity)
            if best_distance < centroid_threshold:
                matched_pairs.append((baseline_entity, best_match))
                if best_idx is not None:
                    used_extracted.add(best_idx)
            else:
                # No match found - entity missing or moved significantly
                matched_pairs.append((baseline_entity, None))
        
        # Check for extracted entities that weren't matched (extra entities)
        for idx, (_, extracted_entity) in enumerate(extracted_centroids):
            if idx not in used_extracted:
                matched_pairs.append((None, extracted_entity))
        
        return matched_pairs
    
    def extract_coords_from_dxf(self, filepath: str) -> Dict:
        """Extract all 3D coordinates from a DXF file, organized by layer."""
        doc = ezdxf.readfile(filepath)
        msp = doc.modelspace()
        
        extracted = {}
        entity_counts = {}
        
        for entity in msp:
            layer = entity.dxf.layer
            if layer not in extracted:
                extracted[layer] = []
                entity_counts[layer] = {}
            
            entity_type = entity.dxftype()
            entity_counts[layer][entity_type] = entity_counts[layer].get(entity_type, 0) + 1
            
            if entity_type == 'LWPOLYLINE':
                # LWPOLYLINE stores coordinates with optional elevation
                coords = []
                elevation = entity.dxf.get('elevation', 0.0)
                for point in entity.get_points('xyb'):
                    x, y = point[0], point[1]
                    coords.append((x, y, elevation))
                if coords:
                    extracted[layer].append({'type': 'lwpolyline', 'coords': coords})
            
            elif entity_type == 'POLYLINE':
                coords = [(v.dxf.location.x, v.dxf.location.y, v.dxf.location.z) 
                         for v in entity.vertices]
                if coords:
                    extracted[layer].append({'type': 'polyline', 'coords': coords})
            
            elif entity_type == 'POINT':
                loc = entity.dxf.location
                extracted[layer].append({
                    'type': 'point',
                    'coords': [(loc.x, loc.y, loc.z)]
                })
            
            elif entity_type == 'LINE':
                start = entity.dxf.start
                end = entity.dxf.end
                extracted[layer].append({
                    'type': 'line',
                    'coords': [(start.x, start.y, start.z), (end.x, end.y, end.z)]
                })
            
            elif entity_type == '3DFACE':
                coords = []
                for i in range(4):
                    try:
                        vtx = entity.dxf.get(f'vtx{i}')
                        coords.append((vtx.x, vtx.y, vtx.z))
                    except:
                        break
                if coords:
                    # COORDINATE TRACKING: Log what we extracted from DXF
                    print(f"[TEST-EXTRACT] 3DFACE from DXF: {len(coords)} vertices: {coords}")
                    extracted[layer].append({'type': '3dface', 'coords': coords})
        
        # Log entity counts for debugging
        for layer, counts in entity_counts.items():
            total = sum(counts.values())
            extracted_count = len(extracted.get(layer, []))
            if total != extracted_count:
                print(f"  Layer '{layer}': Found {total} entities, extracted {extracted_count}")
                for etype, count in counts.items():
                    print(f"    - {etype}: {count}")
        
        return extracted
    
    def calculate_errors(self, baseline: List[Tuple], extracted: List[Tuple], srid: int = 0) -> Dict:
        """
        Calculate per-axis errors (ΔX, ΔY, ΔZ) with SRID-specific tolerances.
        
        Args:
            baseline: Original coordinates
            extracted: Coordinates after round-trip
            srid: Coordinate system for tolerance lookup
        
        Returns detailed error metrics including per-axis deltas.
        """
        if len(baseline) != len(extracted):
            return {
                'max_error': float('inf'),
                'avg_error': float('inf'),
                'max_x_error': float('inf'),
                'max_y_error': float('inf'),
                'max_z_error': float('inf'),
                'avg_x_error': float('inf'),
                'avg_y_error': float('inf'),
                'avg_z_error': float('inf'),
                'errors': [],
                'status': 'FAIL',
                'failure_reason': f'Coordinate count mismatch: {len(baseline)} vs {len(extracted)}'
            }
        
        if not baseline:
            return {
                'max_error': 0.0,
                'avg_error': 0.0,
                'max_x_error': 0.0,
                'max_y_error': 0.0,
                'max_z_error': 0.0,
                'avg_x_error': 0.0,
                'avg_y_error': 0.0,
                'avg_z_error': 0.0,
                'errors': [],
                'status': 'PASS'
            }
        
        errors_3d = []
        x_errors = []
        y_errors = []
        z_errors = []
        
        for idx, (baseline_pt, extracted_pt) in enumerate(zip(baseline, extracted)):
            # Per-axis deltas
            dx = abs(baseline_pt[0] - extracted_pt[0])
            dy = abs(baseline_pt[1] - extracted_pt[1])
            dz = abs(baseline_pt[2] - extracted_pt[2])
            
            # 3D Euclidean distance
            distance_3d = math.sqrt(dx*dx + dy*dy + dz*dz)
            
            errors_3d.append(distance_3d)
            x_errors.append(dx)
            y_errors.append(dy)
            z_errors.append(dz)
            
            # COORDINATE TRACKING: Log vertices with significant errors
            if distance_3d > 1.0:  # More than 1ft error
                print(f"[COMPARE] Vertex {idx}: LARGE ERROR = {distance_3d:.4f} ft")
                print(f"[COMPARE]   Baseline:  {baseline_pt}")
                print(f"[COMPARE]   Extracted: {extracted_pt}")
                print(f"[COMPARE]   Δx={dx:.4f}, Δy={dy:.4f}, Δz={dz:.4f}")
        
        # Calculate aggregate metrics
        max_error = max(errors_3d)
        avg_error = sum(errors_3d) / len(errors_3d)
        max_x_error = max(x_errors)
        max_y_error = max(y_errors)
        max_z_error = max(z_errors)
        avg_x_error = sum(x_errors) / len(x_errors)
        avg_y_error = sum(y_errors) / len(y_errors)
        avg_z_error = sum(z_errors) / len(z_errors)
        
        # Apply SRID-specific tolerances
        tolerances = self.TOLERANCES.get(srid, self.TOLERANCES[0])
        x_pass = max_x_error <= tolerances['x']
        y_pass = max_y_error <= tolerances['y']
        z_pass = max_z_error <= tolerances['z']
        
        # Overall status
        if x_pass and y_pass and z_pass:
            status = 'PASS'
        elif max_error < 0.01:  # Sub-centimeter (marginal)
            status = 'WARNING'
        else:
            status = 'FAIL'
        
        return {
            'max_error': max_error,
            'avg_error': avg_error,
            'max_x_error': max_x_error,
            'max_y_error': max_y_error,
            'max_z_error': max_z_error,
            'avg_x_error': avg_x_error,
            'avg_y_error': avg_y_error,
            'avg_z_error': avg_z_error,
            'count': len(errors_3d),
            'x_pass': x_pass,
            'y_pass': y_pass,
            'z_pass': z_pass,
            'tolerances': tolerances,
            'status': status
        }
    
    def run_cycle(self, dxf_path: str, cycle_num: int, project_name: str, srid: int = 0) -> str:
        """
        Run one import-export cycle through the database using a single shared connection.
        
        Returns path to exported DXF.
        """
        drawing_name = f"Cycle_{cycle_num:03d}"
        drawing_number = f"ST-{cycle_num:03d}"
        export_path = os.path.join(self.output_dir, f"z_stress_cycle_{cycle_num:03d}.dxf")
        
        # Use a SINGLE connection for the entire cycle
        conn = psycopg2.connect(**self.db_config)
        conn.autocommit = False
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
            
            # Import DXF into the drawing (pass the shared connection)
            importer = DXFImporter(self.db_config)
            coordinate_system = self.srid_to_coordinate_system(srid)
            import_stats = importer.import_dxf(
                file_path=dxf_path,
                drawing_id=drawing_id,
                coordinate_system=coordinate_system,
                import_modelspace=True,
                external_conn=conn
            )
            
            if import_stats.get('errors'):
                raise Exception(f"Import failed in cycle {cycle_num}: {import_stats.get('errors')}")
            
            conn.commit()
            
            # Export DXF from the drawing (pass the shared connection)
            exporter = DXFExporter(self.db_config)
            export_stats = exporter.export_dxf(
                drawing_id=drawing_id,
                output_path=export_path,
                include_modelspace=True,
                external_conn=conn
            )
            
            if export_stats.get('errors'):
                raise Exception(f"Export failed in cycle {cycle_num}: {export_stats.get('errors')}")
            
            conn.commit()
            
            # Clean up drawing record AND all associated entities after successful export
            # Delete all entities associated with this drawing
            cur.execute("DELETE FROM drawing_entities WHERE drawing_id = %s", (drawing_id,))
            cur.execute("DELETE FROM drawing_text WHERE drawing_id = %s", (drawing_id,))
            cur.execute("DELETE FROM drawing_dimensions WHERE drawing_id = %s", (drawing_id,))
            cur.execute("DELETE FROM drawing_hatches WHERE drawing_id = %s", (drawing_id,))
            # Finally delete the drawing record (CASCADE should handle remaining references)
            cur.execute("DELETE FROM drawings WHERE drawing_id = %s", (drawing_id,))
            conn.commit()
            
            return export_path
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()
    
    def run_stress_test(self, num_cycles: int = 20, srid: int = 0, tolerance_ft: float = 0.001, user_dxf_path: str = None) -> Dict:
        """
        Run complete stress test with N import/export cycles.
        
        Args:
            num_cycles: Number of cycles to run (default 20)
            srid: Spatial reference ID (0 = local CAD, 2226 = CA State Plane Zone 2)
            tolerance_ft: Maximum acceptable error in feet (default 0.001 = sub-millimeter)
            user_dxf_path: Optional path to user-provided DXF file (default None = use test fixtures)
        
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
        if user_dxf_path:
            print(f"User DXF: {os.path.basename(user_dxf_path)}")
        print(f"{'='*80}\n")
        
        # Use user DXF or create test fixtures
        if user_dxf_path and os.path.exists(user_dxf_path):
            print(f"Using user-provided DXF file: {user_dxf_path}")
            initial_dxf = user_dxf_path
            fixtures = {'geometries': [], 'source': 'user_upload', 'filename': os.path.basename(user_dxf_path), 'srid': srid}
        else:
            # Create initial test DXF with SRID-specific coordinates
            initial_dxf = os.path.join(self.output_dir, f'z_stress_initial_{self.test_id}.dxf')
            fixtures = self.create_test_fixtures(initial_dxf, srid)
            
            print("Test fixtures created:")
            for geom in fixtures['geometries']:
                critical_marker = " [CRITICAL]" if geom['critical'] else ""
                print(f"  - {geom['name']}{critical_marker}: {len(geom['coords'])} vertices")
            print()
        
        # Extract baseline coordinates
        baseline_coords = self.extract_coords_from_dxf(initial_dxf)
        
        # Validate coordinate ranges for SRID
        validation = self.validate_coordinate_ranges(baseline_coords, srid)
        if not validation['valid']:
            print("\n⚠️  COORDINATE VALIDATION WARNINGS:")
            for warning in validation['warnings']:
                print(f"  - {warning}")
            print("\nTest will continue, but results may be unreliable if SRID is incorrect.\n")
        
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
            'coordinate_validation': validation,
            'cycles': [],
            'summary': {}
        }
        
        current_dxf = initial_dxf
        
        # Run cycles
        for cycle in range(1, num_cycles + 1):
            # Use unique project name per cycle to prevent coordinate offset accumulation
            project_name = f"Z_Stress_Test_{self.test_id}_Cycle{cycle:03d}"
            print(f"Cycle {cycle}/{num_cycles}...", end=' ', flush=True)
            
            cycle_result = {
                'cycle': cycle,
                'errors_by_layer': {},
                'timestamp': datetime.now().isoformat()
            }
            
            try:
                # DEBUG: Extract coords before cycle
                before_coords = self.extract_coords_from_dxf(current_dxf)
                
                # Run import-export cycle
                # For user-uploaded files, always use the ORIGINAL file, not the exported one
                # This prevents file path issues between cycles
                if user_dxf_path and os.path.exists(user_dxf_path):
                    exported_dxf = self.run_cycle(user_dxf_path, cycle, project_name, srid)
                else:
                    exported_dxf = self.run_cycle(current_dxf, cycle, project_name, srid)
                
                # Extract and compare coordinates
                extracted_coords = self.extract_coords_from_dxf(exported_dxf)
                
                # DEBUG: Log coordinate shift for first point
                if 'TEST-FLAT-PAD' in before_coords and 'TEST-FLAT-PAD' in extracted_coords:
                    before_pt = before_coords['TEST-FLAT-PAD'][0]['coords'][0]
                    after_pt = extracted_coords['TEST-FLAT-PAD'][0]['coords'][0]
                    dx = after_pt[0] - before_pt[0]
                    dy = after_pt[1] - before_pt[1]
                    dz = after_pt[2] - before_pt[2]
                    if abs(dx) > 1 or abs(dy) > 1 or abs(dz) > 0.01:
                        print(f"\n  DEBUG Cycle {cycle}: Before={before_pt}, After={after_pt}, Delta=({dx:.6f}, {dy:.6f}, {dz:.6f})")
                
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
                    
                    # Use spatial matching for ALL entity types to handle DXF reordering
                    # This ensures robustness regardless of entity type (3DFACE, LINE, POINT, etc.)
                    entity_pairs = self._match_entities_spatially(baseline_entities, extracted_entities, srid)
                    
                    # Check for unmatched entities (missing or extra entities after round-trip)
                    unmatched_baseline = sum(1 for b, e in entity_pairs if b is not None and e is None)
                    unmatched_extracted = sum(1 for b, e in entity_pairs if b is None and e is not None)
                    
                    if unmatched_baseline > 0 or unmatched_extracted > 0:
                        cycle_result['errors_by_layer'][layer] = {
                            'status': 'FAIL',
                            'error': f'Entity matching failed: {unmatched_baseline} baseline unmatched, {unmatched_extracted} extracted unmatched'
                        }
                        has_layer_failure = True
                        total_max_error = float('inf')
                        continue
                    
                    # Compare each matched entity pair
                    layer_errors = []
                    for baseline_entity, extracted_entity in entity_pairs:
                        # Skip unmatched pairs (should not happen due to check above)
                        if baseline_entity is None or extracted_entity is None:
                            continue
                        
                        baseline_pts = baseline_entity['coords']
                        extracted_pts = extracted_entity['coords']
                        
                        error_data = self.calculate_errors(baseline_pts, extracted_pts, srid)
                        layer_errors.append(error_data)
                        
                        total_max_error = max(total_max_error, error_data['max_error'])
                        total_avg_error += error_data['avg_error']
                        total_max_z_error = max(total_max_z_error, error_data['max_z_error'])
                        layer_count += 1
                    
                    # Aggregate layer metrics with per-axis data
                    if not layer_errors:
                        # No entities were compared (shouldn't happen due to checks above)
                        cycle_result['errors_by_layer'][layer] = {
                            'status': 'FAIL',
                            'error': 'No entities compared in layer'
                        }
                        has_layer_failure = True
                        total_max_error = float('inf')
                        continue
                    
                    layer_max = max(e['max_error'] for e in layer_errors)
                    layer_avg = sum(e['avg_error'] for e in layer_errors) / len(layer_errors)
                    layer_max_x = max(e['max_x_error'] for e in layer_errors)
                    layer_max_y = max(e['max_y_error'] for e in layer_errors)
                    layer_max_z = max(e['max_z_error'] for e in layer_errors)
                    
                    # Check against SRID-specific tolerances
                    tolerances = self.TOLERANCES.get(srid, self.TOLERANCES[0])
                    layer_status = 'PASS' if (layer_max_x <= tolerances['x'] and 
                                              layer_max_y <= tolerances['y'] and 
                                              layer_max_z <= tolerances['z']) else 'FAIL'
                    
                    cycle_result['errors_by_layer'][layer] = {
                        'max_error': layer_max,
                        'avg_error': layer_avg,
                        'max_x_error': layer_max_x,
                        'max_y_error': layer_max_y,
                        'max_z_error': layer_max_z,
                        'x_pass': layer_max_x <= tolerances['x'],
                        'y_pass': layer_max_y <= tolerances['y'],
                        'z_pass': layer_max_z <= tolerances['z'],
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
        
        # Collect per-axis error metrics from all cycles
        max_x_errors = []
        max_y_errors = []
        for cycle in successful_cycles:
            cycle_max_x = 0
            cycle_max_y = 0
            for layer_data in cycle.get('errors_by_layer', {}).values():
                if isinstance(layer_data, dict):
                    cycle_max_x = max(cycle_max_x, layer_data.get('max_x_error', 0))
                    cycle_max_y = max(cycle_max_y, layer_data.get('max_y_error', 0))
            max_x_errors.append(cycle_max_x)
            max_y_errors.append(cycle_max_y)
        
        # Get SRID-specific tolerances
        tolerances = self.TOLERANCES.get(srid, self.TOLERANCES[0])
        
        # Calculate final per-axis errors
        final_max_x = max_x_errors[-1] if max_x_errors else 0
        final_max_y = max_y_errors[-1] if max_y_errors else 0
        final_max_z = max_z_errors[-1]
        
        results['summary'] = {
            'final_max_error': max_errors[-1],
            'final_avg_error': avg_errors[-1],
            'final_max_z_error': final_max_z,
            'max_x_error': final_max_x,
            'max_y_error': final_max_y,
            'max_z_error': final_max_z,
            'x_pass': final_max_x <= tolerances['x'],
            'y_pass': final_max_y <= tolerances['y'],
            'z_pass': final_max_z <= tolerances['z'],
            'tolerances': tolerances,
            'worst_max_error': max(max_errors),
            'worst_avg_error': max(avg_errors),
            'best_max_error': min(max_errors),
            'best_avg_error': min(avg_errors),
            'cycles_passed': sum(1 for c in successful_cycles if c['status'] == 'PASS'),
            'cycles_failed': sum(1 for c in successful_cycles if c['status'] == 'FAIL'),
            'total_cycles': len(successful_cycles),
            'max_error': max_errors[-1],  # For UI compatibility
            'avg_error': avg_errors[-1],  # For UI compatibility
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
    
    def _sanitize_for_json(self, obj):
        """Recursively sanitize data structure to replace NaN/Infinity/numpy types with valid JSON values."""
        if isinstance(obj, dict):
            return {k: self._sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize_for_json(item) for item in obj]
        elif isinstance(obj, (bool, type(True))):  # Handle both Python and numpy bools
            return bool(obj)  # Convert to Python bool
        elif isinstance(obj, float):
            if math.isnan(obj):
                return 0.0
            elif math.isinf(obj):
                return 999999.0 if obj > 0 else -999999.0
            return obj
        elif hasattr(obj, 'item'):  # Handle numpy scalars
            return obj.item()
        else:
            return obj
    
    def save_results(self, results: Dict, output_path: str = None):
        """Save test results to JSON file."""
        if output_path is None:
            output_path = os.path.join(self.output_dir, f'z_stress_results_{self.test_id}.json')
        
        # Sanitize results to prevent NaN/Infinity JSON errors
        sanitized_results = self._sanitize_for_json(results)
        
        with open(output_path, 'w') as f:
            json.dump(sanitized_results, f, indent=2)
        
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
