"""
Survey Import Service
Processes PNEZD data with survey codes and generates connectivity (polylines, blocks)
"""

import uuid
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
import psycopg2
import psycopg2.extras
from psycopg2.extras import RealDictCursor
from survey_code_parser import SurveyCodeParser


class ConnectivityProcessor:
    """Processes point sequences and generates line segments based on connectivity rules"""
    
    def __init__(self, db_config):
        self.db_config = db_config
        self.parser = SurveyCodeParser(db_config)
    
    def process_points(self, points: List[Dict[str, Any]], drawing_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process points and generate connectivity
        
        Args:
            points: List of point dictionaries with parsed code data
            drawing_id: Optional drawing ID for context
            
        Returns:
            Dictionary with processed points, sequences, line segments, warnings
        """
        sequences = []
        line_segments = []
        warnings = []
        current_sequence = None
        sequence_counter = 0
        
        for i, point in enumerate(points):
            connectivity = point.get('connectivity_type', 'POINT')
            code = point.get('code', '')
            
            if connectivity == 'NODE':
                if current_sequence:
                    sequences.append(current_sequence)
                    current_sequence = None
                
                point['auto_connected'] = False
                
            elif connectivity == 'LINE':
                if current_sequence is None or current_sequence['code'] != code:
                    if current_sequence:
                        sequences.append(current_sequence)
                    
                    sequence_counter += 1
                    current_sequence = {
                        'sequence_id': str(uuid.uuid4()),
                        'sequence_number': sequence_counter,
                        'code': code,
                        'discipline_code': point.get('discipline_code'),
                        'category_code': point.get('category_code'),
                        'feature_type': point.get('feature_type'),
                        'connectivity_type': 'LINE',
                        'phase': point.get('phase'),
                        'layer_name': point.get('layer_name'),
                        'points': [],
                        'is_closed': False,
                        'drawing_id': drawing_id
                    }
                
                current_sequence['points'].append(point)
                point['auto_connected'] = True
                point['sequence_id'] = current_sequence['sequence_id']
                
            elif connectivity == 'EDGE':
                if current_sequence is None or current_sequence['code'] != code:
                    if current_sequence:
                        sequences.append(current_sequence)
                    
                    sequence_counter += 1
                    current_sequence = {
                        'sequence_id': str(uuid.uuid4()),
                        'sequence_number': sequence_counter,
                        'code': code,
                        'discipline_code': point.get('discipline_code'),
                        'category_code': point.get('category_code'),
                        'feature_type': point.get('feature_type'),
                        'connectivity_type': 'EDGE',
                        'phase': point.get('phase'),
                        'layer_name': point.get('layer_name'),
                        'points': [],
                        'is_closed': False,
                        'drawing_id': drawing_id
                    }
                
                current_sequence['points'].append(point)
                point['auto_connected'] = True
                point['sequence_id'] = current_sequence['sequence_id']
                
            elif connectivity == 'BREAK':
                if current_sequence:
                    sequences.append(current_sequence)
                    current_sequence = None
                
                point['auto_connected'] = False
                
            elif connectivity == 'CLOSE':
                if current_sequence and len(current_sequence['points']) >= 2:
                    current_sequence['points'].append(point)
                    point['auto_connected'] = True
                    point['sequence_id'] = current_sequence['sequence_id']
                    current_sequence['is_closed'] = True
                    sequences.append(current_sequence)
                    current_sequence = None
                else:
                    warnings.append(f"Point {point.get('point_number')}: CLOSE without active sequence (minimum 2 points required)")
                    point['auto_connected'] = False
                    
            elif connectivity == 'POINT':
                point['auto_connected'] = False
                
            else:
                warnings.append(f"Point {point.get('point_number')}: Unknown connectivity type '{connectivity}'")
                point['auto_connected'] = False
        
        if current_sequence:
            if len(current_sequence['points']) >= 2:
                sequences.append(current_sequence)
            else:
                warnings.append(f"Incomplete sequence for code {current_sequence['code']}: only {len(current_sequence['points'])} point(s)")
        
        for sequence in sequences:
            segment = self._create_line_segment(sequence)
            if segment:
                line_segments.append(segment)
        
        return {
            'points': points,
            'sequences': sequences,
            'line_segments': line_segments,
            'warnings': warnings,
            'stats': {
                'total_points': len(points),
                'connected_points': sum(1 for p in points if p.get('auto_connected')),
                'total_sequences': len(sequences),
                'total_line_segments': len(line_segments)
            }
        }
    
    def _create_line_segment(self, sequence: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create line segment geometry from point sequence"""
        points = sequence.get('points', [])
        
        if len(points) < 2:
            return None
        
        coordinates = []
        for point in points:
            easting = point.get('easting')
            northing = point.get('northing')
            elevation = point.get('elevation', 0)
            
            if easting is not None and northing is not None:
                coordinates.append((float(easting), float(northing), float(elevation)))
        
        if len(coordinates) < 2:
            return None
        
        wkt_coords = ', '.join([f'{e} {n} {z}' for e, n, z in coordinates])
        wkt = f'LINESTRING Z ({wkt_coords})'
        
        drawing_id = sequence.get('drawing_id')
        
        return {
            'segment_id': str(uuid.uuid4()),
            'sequence_id': sequence.get('sequence_id'),
            'code': sequence.get('code'),
            'discipline_code': sequence.get('discipline_code'),
            'category_code': sequence.get('category_code'),
            'feature_type': sequence.get('feature_type'),
            'connectivity_type': sequence.get('connectivity_type'),
            'phase': sequence.get('phase'),
            'layer_name': sequence.get('layer_name'),
            'is_closed': sequence.get('is_closed', False),
            'geometry_wkt': wkt,
            'point_ids': [p.get('point_id', str(uuid.uuid4())) for p in points],
            'point_count': len(points),
            'drawing_id': drawing_id if drawing_id else None
        }


class SurveyImportService:
    """Main service for importing survey data with code processing"""
    
    def __init__(self, db_config):
        self.db_config = db_config
        self.parser = SurveyCodeParser(db_config)
        self.connectivity_processor = ConnectivityProcessor(db_config)
    
    def parse_pnezd_with_codes(self, file_content: str, coordinate_system: str = 'SRID_2226', 
                                delimiter: str = None) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Parse PNEZD data with survey codes
        
        Args:
            file_content: Raw file content (CSV or space-delimited)
            coordinate_system: Coordinate system (SRID_2226, SRID_0, SRID_4326)
            delimiter: Field delimiter (None for auto-detect)
            
        Returns:
            Tuple of (parsed_points, errors)
        """
        from batch_pnezd_parser import PNEZDParser
        
        pnezd_parser = PNEZDParser(self.db_config)
        
        parsed_data = pnezd_parser.parse_file(file_content, 'uploaded_file.txt')
        
        points = []
        errors = []
        
        if parsed_data.get('error_count', 0) > 0:
            for err in parsed_data.get('errors', []):
                errors.append(f"Line {err.get('line')}: {err.get('error')}")
        
        for record in parsed_data.get('points', []):
            point_number = record.get('point_number')
            northing = record.get('northing')
            easting = record.get('easting')
            elevation = record.get('elevation')
            description = record.get('description', '')
            
            code = description.strip()
            
            if not code:
                errors.append(f"Point {point_number}: Missing survey code")
                continue
            
            try:
                parsed_code = self.parser.parse_code(code)
                
                if not parsed_code.get('valid'):
                    errors.append(f"Point {point_number}: {parsed_code.get('error', 'Invalid code')}")
                    continue
                
                point = {
                    'point_id': str(uuid.uuid4()),
                    'point_number': str(point_number),
                    'northing': northing,
                    'easting': easting,
                    'elevation': elevation,
                    'code': code,
                    'code_id': parsed_code.get('code_id'),
                    'discipline_code': parsed_code.get('discipline'),
                    'category_code': parsed_code.get('category'),
                    'feature_type': parsed_code.get('feature_type'),
                    'connectivity_type': parsed_code.get('connectivity_type'),
                    'layer_name': parsed_code.get('layer_name'),
                    'phase': parsed_code.get('default_phase'),
                    'geometry_output': parsed_code.get('geometry_output'),
                    'block_name': parsed_code.get('block_name'),
                    'create_block': parsed_code.get('create_block'),
                    'display_name': parsed_code.get('display_name'),
                    'description': parsed_code.get('description'),
                    'auto_connected': False,
                    'sequence_id': None,
                    'coordinate_system': coordinate_system,
                    'parsed_attributes': {
                        'category_group': parsed_code.get('category_group'),
                        'layer_template': parsed_code.get('layer_template'),
                        'auto_connect': parsed_code.get('auto_connect')
                    }
                }
                
                points.append(point)
                
            except Exception as e:
                errors.append(f"Point {point_number}: Error parsing code - {str(e)}")
        
        return points, errors
    
    def generate_preview(self, points: List[Dict[str, Any]], drawing_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate preview of connectivity without saving to database
        
        Args:
            points: List of parsed points with code data
            drawing_id: Optional drawing ID
            
        Returns:
            Preview data with points, sequences, line segments, warnings
        """
        result = self.connectivity_processor.process_points(points, drawing_id)
        
        return result
    
    def commit_import(self, preview_data: Dict[str, Any], project_id: str, 
                     drawing_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Commit import to database (transactional)
        
        Args:
            preview_data: Preview data from generate_preview
            project_id: Project ID
            drawing_id: Optional drawing ID
            
        Returns:
            Import summary with counts and IDs
        """
        conn = None
        cursor = None
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            import_batch_id = str(uuid.uuid4())
            
            # Step 1: Insert sequences FIRST (before points can reference them)
            sequences_inserted = []
            for sequence in preview_data.get('sequences', []):
                cursor.execute("""
                    INSERT INTO survey_sequences (
                        sequence_id, project_id, drawing_id, code, discipline_code,
                        category_code, feature_type, connectivity_type, phase, layer_name,
                        point_count, is_closed, sequence_number, import_batch_id, is_active,
                        created_at
                    ) VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, TRUE,
                        CURRENT_TIMESTAMP
                    )
                    RETURNING sequence_id
                """, (
                    sequence['sequence_id'], project_id, drawing_id, sequence['code'], sequence.get('discipline_code'),
                    sequence.get('category_code'), sequence.get('feature_type'), sequence.get('connectivity_type'), 
                    sequence.get('phase'), sequence.get('layer_name'),
                    len(sequence.get('points', [])), sequence.get('is_closed', False), 
                    sequence.get('sequence_number'), import_batch_id
                ))
                
                result = cursor.fetchone()
                if result:
                    sequences_inserted.append(result['sequence_id'])
            
            # Step 2: Insert points (with sequence_id foreign keys)
            points_inserted = []
            for point in preview_data.get('points', []):
                cursor.execute("""
                    INSERT INTO survey_points (
                        point_id, project_id, drawing_id, point_number, point_description,
                        geometry, northing, easting, elevation, coordinate_system,
                        code, code_id, discipline_code, category_code, feature_type,
                        connectivity_type, layer_name, phase, auto_connected, sequence_id,
                        parsed_attributes, is_active, created_at
                    ) VALUES (
                        %s, %s, %s, %s, %s,
                        ST_SetSRID(ST_MakePoint(%s, %s, %s), 2226), %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, TRUE, CURRENT_TIMESTAMP
                    )
                    RETURNING point_id
                """, (
                    point['point_id'], project_id, drawing_id, point['point_number'], point.get('display_name'),
                    point['easting'], point['northing'], point['elevation'], point['northing'], point['easting'], point['elevation'], point.get('coordinate_system'),
                    point['code'], point.get('code_id'), point.get('discipline_code'), point.get('category_code'), point.get('feature_type'),
                    point.get('connectivity_type'), point.get('layer_name'), point.get('phase'), point.get('auto_connected'), point.get('sequence_id'),
                    psycopg2.extras.Json(point.get('parsed_attributes', {}))
                ))
                
                result = cursor.fetchone()
                if result:
                    points_inserted.append(result['point_id'])
            
            # Step 3: Insert line segments last
            segments_inserted = []
            for segment in preview_data.get('line_segments', []):
                cursor.execute("""
                    INSERT INTO survey_line_segments (
                        segment_id, project_id, drawing_id, feature_type, layer_name,
                        connectivity_type, is_closed, geometry, point_ids, point_count,
                        attributes, created_at
                    ) VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, ST_GeomFromText(%s, 2226), %s::uuid[], %s,
                        %s, CURRENT_TIMESTAMP
                    )
                    RETURNING segment_id
                """, (
                    segment['segment_id'], project_id, drawing_id, segment.get('feature_type'), segment.get('layer_name'),
                    segment.get('connectivity_type'), segment.get('is_closed', False), 
                    segment['geometry_wkt'], segment.get('point_ids', []), segment.get('point_count'),
                    psycopg2.extras.Json({
                        'code': segment.get('code'),
                        'discipline_code': segment.get('discipline_code'),
                        'category_code': segment.get('category_code'),
                        'phase': segment.get('phase')
                    })
                ))
                
                result = cursor.fetchone()
                if result:
                    segments_inserted.append(result['segment_id'])
            
            conn.commit()
            
            return {
                'success': True,
                'import_batch_id': import_batch_id,
                'points_inserted': len(points_inserted),
                'sequences_created': len(sequences_inserted),
                'line_segments_created': len(segments_inserted),
                'point_ids': points_inserted,
                'sequence_ids': sequences_inserted,
                'segment_ids': segments_inserted
            }
            
        except Exception as e:
            if conn:
                conn.rollback()
            raise Exception(f"Import failed: {str(e)}")
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
