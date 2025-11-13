import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional
import re


class SurveyCodeParser:
    """
    Parse and validate survey codes against the code library.
    Resolves layer templates, extracts properties, and provides CAD generation guidance.
    """
    
    def __init__(self, db_config: Dict):
        self.db_config = db_config
    
    def parse_code(self, code: str) -> Dict:
        """
        Parse a survey code and return all properties from the library.
        
        Args:
            code: The survey code to parse (e.g., 'CIV-UTIL-STORM-MH')
        
        Returns:
            Dict containing:
                - valid: bool
                - code: str
                - display_name: str
                - description: str
                - discipline: str
                - category: str
                - feature_type: str
                - connectivity_type: str
                - geometry_output: str
                - category_group: str
                - auto_connect: bool
                - create_block: bool
                - block_name: str
                - layer_template: str
                - default_phase: str
                - is_favorite: bool
                - usage_count: int
                - error: str (if invalid)
        """
        if not code or not isinstance(code, str):
            return {
                'valid': False,
                'error': 'Code is required and must be a string'
            }
        
        code_upper = code.strip().upper()
        
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cur.execute("""
                SELECT 
                    code_id,
                    code,
                    display_name,
                    description,
                    discipline_code,
                    category_code,
                    feature_type,
                    connectivity_type,
                    geometry_output,
                    category_group,
                    auto_connect,
                    create_block,
                    block_name,
                    layer_template,
                    default_phase,
                    is_favorite,
                    usage_count,
                    is_active
                FROM survey_code_library
                WHERE UPPER(code) = %s AND is_active = true
            """, (code_upper,))
            
            row = cur.fetchone()
            
            if not row:
                return {
                    'valid': False,
                    'error': f'Code "{code}" not found in library or is inactive'
                }
            
            return {
                'valid': True,
                'code_id': str(row['code_id']),
                'code': row['code'],
                'display_name': row['display_name'],
                'description': row['description'],
                'discipline': row['discipline_code'],
                'category': row['category_code'],
                'feature_type': row['feature_type'],
                'connectivity_type': row['connectivity_type'],
                'geometry_output': row['geometry_output'],
                'category_group': row['category_group'],
                'auto_connect': row['auto_connect'],
                'create_block': row['create_block'],
                'block_name': row['block_name'] or '',
                'layer_template': row['layer_template'],
                'default_phase': row['default_phase'],
                'is_favorite': row['is_favorite'],
                'usage_count': row['usage_count']
            }
            
        finally:
            cur.close()
            conn.close()
    
    def resolve_layer_name(self, code_data: Dict, phase: Optional[str] = None) -> str:
        """
        Resolve layer template to actual layer name.
        
        Template variables:
            {discipline} - e.g., 'CIV', 'SITE', 'SURV'
            {category} - e.g., 'UTIL', 'ROAD', 'TOPO'
            {feature} - e.g., 'STORM-MH', 'ASPH-EDGE'
            {phase} - e.g., 'EXIST', 'PROP', 'DEMO'
            {geometry} - e.g., 'SYMB', 'EDGE', 'LINE'
        
        Args:
            code_data: Dict from parse_code() with valid=True
            phase: Optional phase override ('EXIST', 'PROP', 'DEMO', etc.)
        
        Returns:
            Resolved layer name string
        """
        if not code_data.get('valid'):
            return ''
        
        template = code_data.get('layer_template', '')
        if not template:
            return ''
        
        actual_phase = phase or code_data.get('default_phase', 'EXIST')
        
        resolved = template
        resolved = resolved.replace('{discipline}', code_data.get('discipline', ''))
        resolved = resolved.replace('{category}', code_data.get('category', ''))
        resolved = resolved.replace('{feature}', code_data.get('feature_type', ''))
        resolved = resolved.replace('{phase}', actual_phase)
        
        geometry_suffix = self._get_geometry_suffix(code_data.get('geometry_output', ''))
        resolved = resolved.replace('{geometry}', geometry_suffix)
        
        return resolved.upper()
    
    def _get_geometry_suffix(self, geometry_output: str) -> str:
        """Map geometry output codes to layer suffixes"""
        mapping = {
            'BL': 'SYMB',
            'PL': 'EDGE',
            'LN': 'LINE',
            'PT': 'TOPO'
        }
        return mapping.get(geometry_output, geometry_output)
    
    def simulate_field_sequence(self, shots: List[Dict]) -> Dict:
        """
        Simulate a sequence of field shots and determine connectivity.
        
        Args:
            shots: List of dicts with keys:
                - point_number: str
                - code: str
                - northing: float
                - easting: float
                - elevation: float
        
        Returns:
            Dict containing:
                - valid: bool
                - shots: List of processed shots with connectivity info
                - polylines: List of polyline segments
                - blocks: List of block insertions
                - warnings: List of warning messages
                - error: str (if invalid)
        """
        if not shots:
            return {
                'valid': False,
                'error': 'No shots provided'
            }
        
        processed_shots = []
        polylines = []
        blocks = []
        warnings = []
        current_line = []
        current_code = None
        
        for idx, shot in enumerate(shots):
            point_num = shot.get('point_number', f'PT{idx+1}')
            code = shot.get('code', '').strip().upper()
            
            if not code:
                warnings.append(f'Point {point_num}: No code provided')
                continue
            
            code_data = self.parse_code(code)
            
            if not code_data.get('valid'):
                warnings.append(f'Point {point_num}: {code_data.get("error")}')
                continue
            
            connectivity = code_data.get('connectivity_type')
            layer_name = self.resolve_layer_name(code_data)
            
            shot_info = {
                'point_number': point_num,
                'code': code,
                'display_name': code_data.get('display_name'),
                'connectivity': connectivity,
                'layer': layer_name,
                'geometry_output': code_data.get('geometry_output'),
                'northing': shot.get('northing', 0),
                'easting': shot.get('easting', 0),
                'elevation': shot.get('elevation', 0)
            }
            
            if connectivity == 'NODE':
                if current_line:
                    polylines.append({
                        'code': current_code,
                        'points': current_line.copy(),
                        'closed': False
                    })
                    current_line = []
                    current_code = None
                
                if code_data.get('create_block'):
                    blocks.append({
                        'point': point_num,
                        'code': code,
                        'block_name': code_data.get('block_name') or code,
                        'layer': layer_name,
                        'northing': shot.get('northing'),
                        'easting': shot.get('easting'),
                        'elevation': shot.get('elevation')
                    })
                    shot_info['creates_block'] = True
                
                shot_info['connects_to'] = None
                
            elif connectivity == 'LINE':
                if current_code and current_code != code:
                    polylines.append({
                        'code': current_code,
                        'points': current_line.copy(),
                        'closed': False
                    })
                    current_line = []
                
                current_line.append(point_num)
                current_code = code
                
                if len(current_line) > 1:
                    shot_info['connects_to'] = current_line[-2]
                else:
                    shot_info['connects_to'] = None
            
            elif connectivity == 'EDGE':
                if current_code and current_code != code:
                    polylines.append({
                        'code': current_code,
                        'points': current_line.copy(),
                        'closed': True
                    })
                    current_line = []
                
                current_line.append(point_num)
                current_code = code
                
                if len(current_line) > 1:
                    shot_info['connects_to'] = current_line[-2]
                else:
                    shot_info['connects_to'] = None
            
            elif connectivity == 'POINT':
                if current_line:
                    polylines.append({
                        'code': current_code,
                        'points': current_line.copy(),
                        'closed': False
                    })
                    current_line = []
                    current_code = None
                
                shot_info['connects_to'] = None
            
            elif connectivity == 'BREAK':
                if current_line:
                    polylines.append({
                        'code': current_code,
                        'points': current_line.copy(),
                        'closed': False
                    })
                    current_line = []
                    current_code = None
                
                shot_info['is_break'] = True
                shot_info['connects_to'] = None
                continue
            
            elif connectivity == 'CLOSE':
                if current_line:
                    polylines.append({
                        'code': current_code,
                        'points': current_line.copy(),
                        'closed': True
                    })
                    current_line = []
                    current_code = None
                
                shot_info['is_close'] = True
                shot_info['connects_to'] = None
                continue
            
            processed_shots.append(shot_info)
        
        if current_line:
            closed = current_code and self.parse_code(current_code).get('connectivity_type') == 'EDGE'
            polylines.append({
                'code': current_code,
                'points': current_line.copy(),
                'closed': closed
            })
        
        return {
            'valid': True,
            'shots': processed_shots,
            'polylines': polylines,
            'blocks': blocks,
            'warnings': warnings
        }
    
    def batch_validate(self, codes: List[str]) -> Dict:
        """
        Validate multiple codes at once.
        
        Args:
            codes: List of code strings to validate
        
        Returns:
            Dict containing:
                - total: int
                - valid: int
                - invalid: int
                - results: List of validation results
        """
        results = []
        valid_count = 0
        invalid_count = 0
        
        for code in codes:
            parsed = self.parse_code(code)
            if parsed.get('valid'):
                valid_count += 1
            else:
                invalid_count += 1
            results.append(parsed)
        
        return {
            'total': len(codes),
            'valid': valid_count,
            'invalid': invalid_count,
            'results': results
        }
    
    def get_connectivity_rules(self) -> Dict:
        """
        Get documentation for connectivity types.
        
        Returns:
            Dict mapping connectivity types to their behavior
        """
        return {
            'NODE': {
                'name': 'Network Node',
                'behavior': 'Single point, often creates block symbol',
                'auto_connect': False,
                'closes_polygon': False,
                'examples': ['Manholes', 'Valves', 'Hydrants', 'Catch Basins']
            },
            'LINE': {
                'name': 'Auto-Connect Sequential Points',
                'behavior': 'Automatically connects points shot in sequence',
                'auto_connect': True,
                'closes_polygon': False,
                'examples': ['Road edges', 'Curbs', 'Pipes', 'Fences']
            },
            'EDGE': {
                'name': 'Closed Polygon',
                'behavior': 'Connects sequential points AND closes back to first',
                'auto_connect': True,
                'closes_polygon': True,
                'examples': ['Building footprints', 'Property boundaries', 'Parking islands']
            },
            'POINT': {
                'name': 'Standalone Point',
                'behavior': 'No automatic connection, just marks location',
                'auto_connect': False,
                'closes_polygon': False,
                'examples': ['Topo shots', 'Trees', 'Signs', 'Light poles']
            },
            'BREAK': {
                'name': 'Stop Line',
                'behavior': 'Ends current line sequence without closing',
                'auto_connect': False,
                'closes_polygon': False,
                'examples': ['End of fence', 'End of curb run']
            },
            'CLOSE': {
                'name': 'Close Polygon',
                'behavior': 'Closes current sequence back to start point',
                'auto_connect': False,
                'closes_polygon': True,
                'examples': ['Final corner of building', 'Close property boundary']
            }
        }
