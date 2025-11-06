"""
Layer Pattern Classification Engine
Parses layer names to extract intelligent object properties.
"""

import re
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass


@dataclass
class LayerClassification:
    """Result of layer name classification."""
    object_type: str
    properties: Dict
    confidence: float
    network_mode: Optional[str] = None


class LayerClassifier:
    """
    Classifies layer names and extracts properties using pattern matching.
    
    Examples:
        '12IN-STORM' -> {diameter: 12, utility_type: 'storm', unit: 'inches'}
        'BMP-BIORETENTION-500CF' -> {bmp_type: 'bioretention', volume: 500, unit: 'cubic_feet'}
        'SURFACE-EG' -> {surface_type: 'existing_grade'}
        'MH-STORM' -> {structure_type: 'manhole', utility_type: 'storm'}
    """
    
    def __init__(self):
        self.utility_patterns = [
            (r'(\d+)(?:IN|INCH)?[-_]?(STORM|SEWER|SANITARY|WATER|GAS|ELECTRIC)', 'utility_line'),
            (r'(STORM|SEWER|SANITARY|WATER|GAS|ELECTRIC)[-_]?(\d+)(?:IN|INCH)?', 'utility_line'),
            (r'(PIPE|LINE)[-_]?(STORM|SEWER|SANITARY|WATER)', 'utility_line'),
        ]
        
        self.structure_patterns = [
            (r'(MH|MANHOLE|MHOLE)[-_]?(STORM|SEWER|SANITARY)?', 'utility_structure'),
            (r'(CB|CATCH[-_]?BASIN)[-_]?(STORM)?', 'utility_structure'),
            (r'(INLET|FES|VALVE|HYDRANT|CLEANOUT|CO)[-_]?(STORM|WATER)?', 'utility_structure'),
        ]
        
        self.bmp_patterns = [
            (r'BMP[-_]?(BIORETENTION|SWALE|BASIN|RAIN[-_]?GARDEN|FILTER|PLANTER)[-_]?(\d+)?(?:CF|CY)?', 'bmp'),
            (r'(BIORETENTION|RAIN[-_]?GARDEN|SWALE|DETENTION)[-_]?(\d+)?(?:CF|CY)?', 'bmp'),
        ]
        
        self.surface_patterns = [
            (r'SURFACE[-_]?(EG|EXIST|EXISTING|PROP|PROPOSED|FG|FINISH|TIN)', 'surface_model'),
            (r'(EG|EXIST|PROP|FG)[-_]?SURFACE', 'surface_model'),
            (r'(TIN|DTM|DEM)[-_]?(EG|PROP)?', 'surface_model'),
        ]
        
        self.alignment_patterns = [
            (r'(CENTERLINE|CL|ALIGN|ALIGNMENT)[-_]?(ROAD|STREET|UTILITY)?', 'alignment'),
            (r'(ROAD|STREET)[-_]?(CL|CENTERLINE)', 'alignment'),
        ]
        
        self.survey_patterns = [
            (r'(SURVEY|TOPO)[-_]?(POINT|SHOT|CONTROL)', 'survey_point'),
            (r'(CONTROL|MONUMENT|BENCHMARK|BM)[-_]?(POINT)?', 'survey_point'),
        ]
        
        self.note_patterns = [
            (r'(NOTE|NOTES|TEXT|LABEL|CALLOUT|GENERAL[-_]?NOTE)', 'project_note'),
        ]
        
        self.tree_patterns = [
            (r'TREE[-_]?(EXIST|PROP|TO[-_]?REMAIN|TO[-_]?REMOVE)?', 'site_tree'),
            (r'(LANDSCAPE|PLANTING)[-_]?TREE', 'site_tree'),
        ]
        
        self.parcel_patterns = [
            (r'(PARCEL|LOT|PROPERTY)[-_]?(LINE|BOUNDARY)?', 'parcel'),
            (r'(ROW|RIGHT[-_]?OF[-_]?WAY|EASEMENT)', 'parcel'),
        ]
    
    def classify(self, layer_name: str) -> Optional[LayerClassification]:
        """
        Classify a layer name and extract properties.
        
        Args:
            layer_name: The layer name to classify
            
        Returns:
            LayerClassification object or None if not recognized
        """
        if not layer_name:
            return None
        
        layer_upper = layer_name.upper().strip()
        
        result = (
            self._classify_utility_line(layer_upper) or
            self._classify_structure(layer_upper) or
            self._classify_bmp(layer_upper) or
            self._classify_surface(layer_upper) or
            self._classify_alignment(layer_upper) or
            self._classify_survey_point(layer_upper) or
            self._classify_note(layer_upper) or
            self._classify_tree(layer_upper) or
            self._classify_parcel(layer_upper)
        )
        
        return result
    
    def _classify_utility_line(self, layer_name: str) -> Optional[LayerClassification]:
        """Classify utility line layers and extract diameter and type."""
        for pattern, obj_type in self.utility_patterns:
            match = re.search(pattern, layer_name, re.IGNORECASE)
            if match:
                groups = match.groups()
                properties = {}
                
                if groups[0].isdigit():
                    properties['diameter_inches'] = int(groups[0])
                    properties['utility_type'] = groups[1].lower()
                else:
                    properties['utility_type'] = groups[0].lower()
                    if len(groups) > 1 and groups[1].isdigit():
                        properties['diameter_inches'] = int(groups[1])
                
                utility_type_map = {
                    'storm': 'Storm',
                    'sewer': 'Sanitary',
                    'sanitary': 'Sanitary',
                    'water': 'Water',
                    'gas': 'Gas',
                    'electric': 'Electric'
                }
                properties['utility_type'] = utility_type_map.get(
                    properties['utility_type'], properties['utility_type']
                )
                
                network_mode = self._determine_network_mode(properties['utility_type'])
                
                return LayerClassification(
                    object_type='utility_line',
                    properties=properties,
                    confidence=0.9,
                    network_mode=network_mode
                )
        return None
    
    def _classify_structure(self, layer_name: str) -> Optional[LayerClassification]:
        """Classify utility structure layers."""
        for pattern, obj_type in self.structure_patterns:
            match = re.search(pattern, layer_name, re.IGNORECASE)
            if match:
                groups = match.groups()
                properties = {}
                
                structure_type_map = {
                    'MH': 'Manhole',
                    'MANHOLE': 'Manhole',
                    'MHOLE': 'Manhole',
                    'CB': 'Catch Basin',
                    'CATCH BASIN': 'Catch Basin',
                    'CATCH_BASIN': 'Catch Basin',
                    'INLET': 'Inlet',
                    'FES': 'Flared End Section',
                    'VALVE': 'Valve',
                    'HYDRANT': 'Fire Hydrant',
                    'CLEANOUT': 'Cleanout',
                    'CO': 'Cleanout'
                }
                
                properties['structure_type'] = structure_type_map.get(
                    groups[0].upper().replace('-', ' ').replace('_', ' '),
                    groups[0]
                )
                
                network_mode = None
                if len(groups) > 1 and groups[1]:
                    utility_map = {
                        'STORM': 'Storm',
                        'SEWER': 'Sanitary',
                        'SANITARY': 'Sanitary',
                        'WATER': 'Water'
                    }
                    properties['utility_type'] = utility_map.get(groups[1].upper(), groups[1])
                    network_mode = self._determine_network_mode(properties['utility_type'])
                
                return LayerClassification(
                    object_type='utility_structure',
                    properties=properties,
                    confidence=0.85,
                    network_mode=network_mode
                )
        return None
    
    def _classify_bmp(self, layer_name: str) -> Optional[LayerClassification]:
        """Classify BMP layers and extract type and volume."""
        for pattern, obj_type in self.bmp_patterns:
            match = re.search(pattern, layer_name, re.IGNORECASE)
            if match:
                groups = match.groups()
                properties = {}
                
                bmp_type_map = {
                    'BIORETENTION': 'Bioretention',
                    'SWALE': 'Vegetated Swale',
                    'BASIN': 'Detention Basin',
                    'RAIN GARDEN': 'Rain Garden',
                    'RAIN_GARDEN': 'Rain Garden',
                    'FILTER': 'Sand Filter',
                    'PLANTER': 'Tree Planter',
                    'DETENTION': 'Detention Basin'
                }
                
                bmp_type = groups[0].upper().replace('-', ' ').replace('_', ' ')
                properties['bmp_type'] = bmp_type_map.get(bmp_type, bmp_type)
                
                if len(groups) > 1 and groups[1] and groups[1].isdigit():
                    volume = int(groups[1])
                    if 'CF' in layer_name.upper():
                        properties['design_volume_cf'] = volume
                    elif 'CY' in layer_name.upper():
                        properties['design_volume_cf'] = volume * 27
                    else:
                        properties['design_volume_cf'] = volume
                
                return LayerClassification(
                    object_type='bmp',
                    properties=properties,
                    confidence=0.9,
                    network_mode='bmp'
                )
        return None
    
    def _classify_surface(self, layer_name: str) -> Optional[LayerClassification]:
        """Classify surface model layers."""
        for pattern, obj_type in self.surface_patterns:
            match = re.search(pattern, layer_name, re.IGNORECASE)
            if match:
                groups = match.groups()
                properties = {}
                
                surface_type_map = {
                    'EG': 'Existing Grade',
                    'EXIST': 'Existing Grade',
                    'EXISTING': 'Existing Grade',
                    'PROP': 'Proposed Grade',
                    'PROPOSED': 'Proposed Grade',
                    'FG': 'Finish Grade',
                    'FINISH': 'Finish Grade',
                    'TIN': 'TIN Surface',
                    'DTM': 'DTM Surface',
                    'DEM': 'DEM Surface'
                }
                
                surface_type = groups[0].upper().replace('-', ' ').replace('_', ' ')
                properties['surface_type'] = surface_type_map.get(surface_type, surface_type)
                
                return LayerClassification(
                    object_type='surface_model',
                    properties=properties,
                    confidence=0.85
                )
        return None
    
    def _classify_alignment(self, layer_name: str) -> Optional[LayerClassification]:
        """Classify alignment layers."""
        for pattern, obj_type in self.alignment_patterns:
            match = re.search(pattern, layer_name, re.IGNORECASE)
            if match:
                groups = match.groups()
                properties = {}
                
                properties['alignment_type'] = 'Centerline'
                if len(groups) > 1 and groups[1]:
                    properties['description'] = groups[1].capitalize()
                
                return LayerClassification(
                    object_type='alignment',
                    properties=properties,
                    confidence=0.8
                )
        return None
    
    def _classify_survey_point(self, layer_name: str) -> Optional[LayerClassification]:
        """Classify survey point layers."""
        for pattern, obj_type in self.survey_patterns:
            match = re.search(pattern, layer_name, re.IGNORECASE)
            if match:
                groups = match.groups()
                properties = {}
                
                point_type_map = {
                    'CONTROL': 'Control',
                    'MONUMENT': 'Control',
                    'BENCHMARK': 'Benchmark',
                    'BM': 'Benchmark',
                    'TOPO': 'Topo',
                    'SURVEY': 'Topo'
                }
                
                point_type = groups[0].upper().replace('-', ' ').replace('_', ' ')
                properties['point_type'] = point_type_map.get(point_type, 'Topo')
                
                return LayerClassification(
                    object_type='survey_point',
                    properties=properties,
                    confidence=0.75
                )
        return None
    
    def _classify_note(self, layer_name: str) -> Optional[LayerClassification]:
        """Classify note/text layers."""
        for pattern, obj_type in self.note_patterns:
            match = re.search(pattern, layer_name, re.IGNORECASE)
            if match:
                return LayerClassification(
                    object_type='project_note',
                    properties={'note_type': 'General'},
                    confidence=0.7
                )
        return None
    
    def _classify_tree(self, layer_name: str) -> Optional[LayerClassification]:
        """Classify tree layers."""
        for pattern, obj_type in self.tree_patterns:
            match = re.search(pattern, layer_name, re.IGNORECASE)
            if match:
                groups = match.groups()
                properties = {}
                
                if groups and groups[0]:
                    status_map = {
                        'EXIST': 'Existing',
                        'PROP': 'Proposed',
                        'TO REMAIN': 'To Remain',
                        'TO_REMAIN': 'To Remain',
                        'TO REMOVE': 'To Remove',
                        'TO_REMOVE': 'To Remove'
                    }
                    status = groups[0].upper().replace('-', ' ').replace('_', ' ')
                    properties['tree_status'] = status_map.get(status, 'Existing')
                else:
                    properties['tree_status'] = 'Existing'
                
                return LayerClassification(
                    object_type='site_tree',
                    properties=properties,
                    confidence=0.8
                )
        return None
    
    def _classify_parcel(self, layer_name: str) -> Optional[LayerClassification]:
        """Classify parcel/property layers."""
        for pattern, obj_type in self.parcel_patterns:
            match = re.search(pattern, layer_name, re.IGNORECASE)
            if match:
                groups = match.groups()
                properties = {}
                
                if 'ROW' in layer_name.upper() or 'RIGHT' in layer_name.upper():
                    properties['parcel_type'] = 'Right of Way'
                elif 'EASEMENT' in layer_name.upper():
                    properties['parcel_type'] = 'Easement'
                else:
                    properties['parcel_type'] = 'Parcel'
                
                return LayerClassification(
                    object_type='parcel',
                    properties=properties,
                    confidence=0.75
                )
        return None
    
    def _determine_network_mode(self, utility_type: str) -> Optional[str]:
        """
        Determine network mode based on utility type.
        
        Returns:
            'gravity' for Storm and Sanitary systems
            'pressure' for Water, Gas, Electric systems
            None for unknown
        """
        gravity_types = ['Storm', 'Sanitary']
        pressure_types = ['Water', 'Gas', 'Electric', 'Fire']
        
        if utility_type in gravity_types:
            return 'gravity'
        elif utility_type in pressure_types:
            return 'pressure'
        return None
    
    def classify_block_name(self, block_name: str) -> Optional[LayerClassification]:
        """
        Classify block names to identify structure types and network modes.
        
        Examples:
            'SD-MH-48' -> Storm Drain Manhole (gravity)
            'SS-MH-60' -> Sanitary Sewer Manhole (gravity)
            'W-VALVE-6' -> Water Valve (pressure)
            'SD-CB-TYPE-C' -> Storm Catch Basin (gravity)
        """
        if not block_name:
            return None
        
        block_upper = block_name.upper().strip()
        
        structure_prefixes = {
            'SD': ('Storm', 'gravity'),
            'SS': ('Sanitary', 'gravity'),
            'W': ('Water', 'pressure'),
            'G': ('Gas', 'pressure'),
            'E': ('Electric', 'pressure'),
            'F': ('Fire', 'pressure'),
        }
        
        for prefix, (utility_type, network_mode) in structure_prefixes.items():
            if block_upper.startswith(f'{prefix}-'):
                properties = {'utility_type': utility_type}
                
                if 'MH' in block_upper or 'MANHOLE' in block_upper:
                    properties['structure_type'] = 'Manhole'
                elif 'CB' in block_upper or 'CATCH' in block_upper:
                    properties['structure_type'] = 'Catch Basin'
                elif 'INLET' in block_upper:
                    properties['structure_type'] = 'Inlet'
                elif 'VALVE' in block_upper:
                    properties['structure_type'] = 'Valve'
                elif 'HYDRANT' in block_upper:
                    properties['structure_type'] = 'Fire Hydrant'
                elif 'CLEANOUT' in block_upper or 'CO' in block_upper:
                    properties['structure_type'] = 'Cleanout'
                else:
                    properties['structure_type'] = 'Unknown'
                
                size_match = re.search(r'-(\d+)', block_upper)
                if size_match:
                    properties['size_mm'] = int(float(size_match.group(1)) * 25.4)
                
                return LayerClassification(
                    object_type='utility_structure',
                    properties=properties,
                    confidence=0.95,
                    network_mode=network_mode
                )
        
        return None
