"""
Export Layer Generator
Generates standard layer names for DXF export based on database properties.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Optional, List
from standards.layer_name_builder import LayerNameBuilder


class ExportLayerGenerator:
    """
    Generate standard layer names for DXF export.
    
    Takes database object properties and generates appropriate standard layer names.
    """
    
    def __init__(self):
        """Initialize with layer name builder"""
        self.builder = LayerNameBuilder()
        
        # Map database object types to standard components
        self.object_type_mapping = {
            # Utilities
            'utility_line': self._generate_utility_line_layer,
            'utility_structure': self._generate_utility_structure_layer,
            'pipe_network_pipe': self._generate_utility_line_layer,
            'pipe_network_structure': self._generate_utility_structure_layer,
            
            # Roads/Transportation
            'alignment': self._generate_alignment_layer,
            'road_centerline': self._generate_alignment_layer,
            
            # Grading/Topography
            'contour': self._generate_contour_layer,
            'spot_elevation': self._generate_spot_layer,
            'surface_model': self._generate_surface_layer,
            
            # Survey
            'survey_point': self._generate_survey_point_layer,
            
            # Stormwater
            'bmp': self._generate_bmp_layer,
            
            # ADA
            'ada_feature': self._generate_ada_layer,
            
            # Trees/Site
            'site_tree': self._generate_tree_layer,
        }
    
    def generate_layer_name(self, 
                           object_type: str,
                           properties: Dict,
                           geometry_type: Optional[str] = None) -> Optional[str]:
        """
        Generate standard layer name from object properties.
        
        Args:
            object_type: Database object type (e.g., 'utility_line')
            properties: Dictionary of object properties
            geometry_type: DXF geometry type (LINE, POINT, POLYGON, TEXT, etc.)
            
        Returns:
            Standard layer name or None if cannot generate
        """
        # Get generator function for this object type
        generator_func = self.object_type_mapping.get(object_type)
        
        if not generator_func:
            # Fall back to generic layer
            return self._generate_generic_layer(object_type, properties, geometry_type)
        
        return generator_func(properties, geometry_type)
    
    def _generate_utility_line_layer(self, 
                                     properties: Dict,
                                     geometry_type: Optional[str]) -> Optional[str]:
        """Generate layer name for utility lines"""
        utility_type = properties.get('utility_type', 'UTIL')
        
        # Map utility type to standard code
        utility_map = {
            'storm': 'STORM',
            'sanitary': 'SANIT',
            'sewer': 'SANIT',
            'water': 'WATER',
            'recycled': 'RECYC',
            'reclaimed': 'RECYC',
            'gas': 'GAS',
            'electric': 'ELEC',
            'electrical': 'ELEC',
            'telephone': 'TELE',
            'fiber': 'FIBER',
            'communications': 'TELE',
        }
        
        type_code = utility_map.get(utility_type.lower(), 'UTIL')
        
        # Extract attributes (size, material, etc.)
        attributes = []
        
        # Add diameter/size if available
        for size_key in ['diameter', 'size', 'diameter_inches', 'width']:
            if size_key in properties and properties[size_key]:
                size = str(properties[size_key])
                if size.replace('.', '').isdigit():
                    attributes.append(f"{size}IN")
                break
        
        # Add material if available
        material = properties.get('material', '')
        if material:
            material_map = {
                'pvc': 'PVC',
                'hdpe': 'HDPE',
                'ductile iron': 'DI',
                'cast iron': 'CI',
                'concrete': 'CONC',
                'steel': 'STEEL',
                'copper': 'CU',
            }
            material_code = material_map.get(material.lower(), material.upper()[:5])
            if material_code:
                attributes.append(material_code)
        
        # Determine phase
        phase = self._get_phase_code(properties)
        
        # Determine geometry
        geometry = 'LN'  # Lines are always LN
        
        return self.builder.build(
            discipline='CIV',
            category='UTIL',
            object_type=type_code,
            phase=phase,
            geometry=geometry,
            attributes=attributes
        )
    
    def _generate_utility_structure_layer(self,
                                          properties: Dict,
                                          geometry_type: Optional[str]) -> Optional[str]:
        """Generate layer name for utility structures"""
        structure_type = properties.get('structure_type', 'MH')
        
        # Map structure types
        structure_map = {
            'manhole': 'MH',
            'inlet': 'INLET',
            'catch_basin': 'CB',
            'catch basin': 'CB',
            'cleanout': 'CLNOUT',
            'valve': 'VALVE',
            'meter': 'METER',
            'hydrant': 'HYDRA',
            'pump': 'PUMP',
        }
        
        type_code = structure_map.get(structure_type.lower(), 'MH')
        
        # Attributes (size, depth, etc.)
        attributes = []
        if 'diameter' in properties and properties['diameter']:
            attributes.append(f"{properties['diameter']}IN")
        
        phase = self._get_phase_code(properties)
        geometry = 'PT'  # Structures are points
        
        return self.builder.build(
            discipline='CIV',
            category='UTIL',
            object_type=type_code,
            phase=phase,
            geometry=geometry,
            attributes=attributes
        )
    
    def _generate_alignment_layer(self,
                                   properties: Dict,
                                   geometry_type: Optional[str]) -> Optional[str]:
        """Generate layer name for alignments/centerlines"""
        attributes = []
        
        # Add road name if available
        if 'name' in properties and properties['name']:
            road_name = properties['name'][:10].upper().replace(' ', '')
            attributes.append(road_name)
        
        phase = self._get_phase_code(properties)
        geometry = 'LN'
        
        return self.builder.build(
            discipline='CIV',
            category='ROAD',
            object_type='CNTR',
            phase=phase,
            geometry=geometry,
            attributes=attributes
        )
    
    def _generate_surface_layer(self,
                                 properties: Dict,
                                 geometry_type: Optional[str]) -> Optional[str]:
        """Generate layer name for surface models"""
        surface_type = properties.get('surface_type', 'surface')
        
        # Map surface type to standard code
        surface_map = {
            'existing_grade': 'EG',
            'existing': 'EG',
            'proposed_grade': 'FG',
            'finished_grade': 'FG',
            'proposed': 'FG',
            'top_of_curb': 'TOC',
            'flow_line': 'FL',
        }
        
        type_code = surface_map.get(surface_type.lower(), surface_type.upper()[:8])
        phase = self._get_phase_code(properties)
        
        return self.builder.build(
            discipline='CIV',
            category='GRAD',
            object_type=type_code,
            phase=phase,
            geometry='PG',
            attributes=[]
        )
    
    def _generate_contour_layer(self,
                                 properties: Dict,
                                 geometry_type: Optional[str]) -> Optional[str]:
        """Generate layer name for contours"""
        attributes = []
        
        # Add interval if available
        interval = properties.get('interval', properties.get('contour_interval'))
        if interval:
            attributes.append(f"{interval}FT")
        
        # Check if major/minor
        is_major = properties.get('is_major', False)
        if is_major:
            attributes.append('MAJ')
        
        phase = self._get_phase_code(properties)
        geometry = 'LN'
        
        # Determine if existing or proposed
        discipline = 'SITE' if phase == 'EXIST' else 'SITE'
        
        return self.builder.build(
            discipline=discipline,
            category='GRAD',
            object_type='CNTR',
            phase=phase,
            geometry=geometry,
            attributes=attributes
        )
    
    def _generate_spot_layer(self,
                              properties: Dict,
                              geometry_type: Optional[str]) -> Optional[str]:
        """Generate layer name for spot elevations"""
        phase = self._get_phase_code(properties)
        
        return self.builder.build(
            discipline='SURV',
            category='TOPO',
            object_type='SPOT',
            phase=phase,
            geometry='PT',
            attributes=[]
        )
    
    def _generate_survey_point_layer(self,
                                      properties: Dict,
                                      geometry_type: Optional[str]) -> Optional[str]:
        """Generate layer name for survey control points"""
        point_type = properties.get('point_type', 'MONUMENT')
        
        type_map = {
            'monument': 'MONUMENT',
            'benchmark': 'BENCH',
            'control': 'MONUMENT',
            'shot': 'SHOT',
        }
        
        type_code = type_map.get(point_type.lower(), 'MONUMENT')
        phase = self._get_phase_code(properties)
        
        return self.builder.build(
            discipline='SURV',
            category='CTRL',
            object_type=type_code,
            phase=phase,
            geometry='PT',
            attributes=[]
        )
    
    def _generate_bmp_layer(self,
                             properties: Dict,
                             geometry_type: Optional[str]) -> Optional[str]:
        """Generate layer name for BMPs/stormwater features"""
        bmp_type = properties.get('bmp_type', 'BIORT')
        
        type_map = {
            'bioretention': 'BIORT',
            'bioswale': 'SWALE',
            'detention': 'BASIN',
            'retention': 'BASIN',
            'basin': 'BASIN',
        }
        
        type_code = type_map.get(bmp_type.lower(), 'BIORT')
        phase = self._get_phase_code(properties)
        
        return self.builder.build(
            discipline='CIV',
            category='STOR',
            object_type=type_code,
            phase=phase,
            geometry='PG',
            attributes=[]
        )
    
    def _generate_ada_layer(self,
                             properties: Dict,
                             geometry_type: Optional[str]) -> Optional[str]:
        """Generate layer name for ADA features"""
        feature_type = properties.get('feature_type', 'RAMP')
        
        type_map = {
            'ramp': 'RAMP',
            'path': 'PATH',
            'parking': 'PARK',
        }
        
        type_code = type_map.get(feature_type.lower(), 'RAMP')
        phase = self._get_phase_code(properties)
        
        # Add slope/width attributes if available
        attributes = []
        if 'slope_pct' in properties:
            attributes.append(f"{properties['slope_pct']}PCT")
        if 'width_ft' in properties:
            attributes.append(f"{properties['width_ft']}FT")
        
        return self.builder.build(
            discipline='CIV',
            category='ADA',
            object_type=type_code,
            phase=phase,
            geometry='PG',
            attributes=attributes
        )
    
    def _generate_tree_layer(self,
                              properties: Dict,
                              geometry_type: Optional[str]) -> Optional[str]:
        """Generate layer name for trees"""
        species = properties.get('species', 'OAK')
        
        # Simplify species to code
        species_map = {
            'oak': 'OAK',
            'pine': 'PINE',
            'maple': 'MAPLE',
            'elm': 'ELM',
        }
        
        species_code = species_map.get(species.lower(), species.upper()[:5])
        phase = self._get_phase_code(properties)
        
        # Add diameter if available
        attributes = []
        if 'diameter' in properties:
            attributes.append(f"{properties['diameter']}IN")
        
        return self.builder.build(
            discipline='SURV',
            category='TREE',
            object_type=species_code,
            phase=phase,
            geometry='PT',
            attributes=attributes
        )
    
    def _generate_generic_layer(self,
                                 object_type: str,
                                 properties: Dict,
                                 geometry_type: Optional[str]) -> str:
        """Generate generic layer for unknown types"""
        phase = self._get_phase_code(properties)
        geom = self._map_geometry_type(geometry_type)
        
        # Try to extract basic info
        type_code = object_type.upper()[:10]
        
        return self.builder.build(
            discipline='MISC',
            category='OBJ',
            object_type=type_code,
            phase=phase,
            geometry=geom,
            attributes=[]
        ) or f"MISC-OBJ-{type_code}-{phase}-{geom}"
    
    def _get_phase_code(self, properties: Dict) -> str:
        """Extract phase code from properties"""
        phase = properties.get('phase', properties.get('status', 'EXIST'))
        
        phase_map = {
            'new': 'NEW',
            'existing': 'EXIST',
            'proposed': 'PROP',
            'demolition': 'DEMO',
            'future': 'FUTR',
            'temporary': 'TEMP',
        }
        
        return phase_map.get(phase.lower(), 'EXIST')
    
    def _map_geometry_type(self, geometry_type: Optional[str]) -> str:
        """Map DXF geometry type to standard geometry code"""
        if not geometry_type:
            return 'LN'
        
        geom_map = {
            'LINE': 'LN',
            'POLYLINE': 'LN',
            'LWPOLYLINE': 'LN',
            'ARC': 'LN',
            'CIRCLE': 'LN',
            'POINT': 'PT',
            'HATCH': 'PG',
            'SOLID': 'PG',
            '3DFACE': 'PG',
            'TEXT': 'TX',
            'MTEXT': 'TX',
            'DIMENSION': 'DIM',
        }
        
        return geom_map.get(geometry_type.upper(), 'LN')


# Example usage
if __name__ == '__main__':
    generator = ExportLayerGenerator()
    
    # Test utility line
    test_cases = [
        {
            'object_type': 'utility_line',
            'properties': {
                'utility_type': 'storm',
                'diameter': 12,
                'material': 'pvc',
                'phase': 'new'
            },
            'geometry_type': 'LINE'
        },
        {
            'object_type': 'utility_structure',
            'properties': {
                'structure_type': 'manhole',
                'diameter': 48,
                'phase': 'existing'
            },
            'geometry_type': 'POINT'
        },
        {
            'object_type': 'contour',
            'properties': {
                'interval': 1,
                'is_major': False,
                'phase': 'existing'
            },
            'geometry_type': 'LINE'
        },
    ]
    
    print("Testing Export Layer Generator:\n")
    for test in test_cases:
        layer_name = generator.generate_layer_name(
            test['object_type'],
            test['properties'],
            test['geometry_type']
        )
        print(f"{test['object_type']} → {layer_name}")
        print(f"  Properties: {test['properties']}")
        print()
