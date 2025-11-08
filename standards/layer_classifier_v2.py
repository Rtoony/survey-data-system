"""
Layer Classifier V2 - Standards-Driven Approach
Parses layer names using the new hierarchical standards vocabulary
"""

import re
from typing import Dict, Optional, List
from dataclasses import dataclass
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from standards.layer_name_builder import LayerNameBuilder, LayerComponents

# Try to import mapping manager (may not be available if database not set up)
try:
    from standards.import_mapping_manager import ImportMappingManager
    MAPPING_AVAILABLE = True
except:
    MAPPING_AVAILABLE = False


@dataclass
class LayerClassification:
    """Result of layer name classification"""
    object_type: str
    properties: Dict
    confidence: float
    database_table: Optional[str] = None
    standard_layer_name: Optional[str] = None
    original_layer_name: Optional[str] = None


class LayerClassifierV2:
    """
    Classify layer names using the standards vocabulary database.
    
    This version:
    1. First tries to parse as a standard layer name
    2. Falls back to pattern matching for non-standard layers
    3. Generates confidence scores based on match quality
    """
    
    def __init__(self):
        """Initialize classifier with layer name builder"""
        self.builder = LayerNameBuilder()
        
        # Import mapping manager (if available)
        self.mapping_manager = None
        if MAPPING_AVAILABLE:
            try:
                self.mapping_manager = ImportMappingManager()
            except:
                pass  # Database not ready yet
        
        # Legacy patterns for non-standard layer names
        self.legacy_patterns = self._build_legacy_patterns()
    
    def _build_legacy_patterns(self) -> List[Dict]:
        """
        Build regex patterns for common non-standard layer formats.
        These help import data from existing CAD files.
        """
        return [
            # Storm drain patterns
            {
                'pattern': r'(?:SD|STORM)[-_]?(\d+)(?:IN|INCH)?[-_]?(PIPE|LINE|NEW|EXIST|PROP)?',
                'discipline': 'CIV',
                'category': 'UTIL',
                'object_type': 'STORM',
                'extract_diameter': 1,
                'extract_phase': 2,
                'confidence': 0.85
            },
            # Sanitary sewer patterns
            {
                'pattern': r'(?:SS|SANIT|SEWER)[-_]?(\d+)(?:IN|INCH)?[-_]?(PIPE|LINE|NEW|EXIST|PROP)?',
                'discipline': 'CIV',
                'category': 'UTIL',
                'object_type': 'SANIT',
                'extract_diameter': 1,
                'extract_phase': 2,
                'confidence': 0.85
            },
            # Water patterns
            {
                'pattern': r'(?:W|WATER)[-_]?(\d+)(?:IN|INCH)?[-_]?(PIPE|LINE|NEW|EXIST|PROP)?',
                'discipline': 'CIV',
                'category': 'UTIL',
                'object_type': 'WATER',
                'extract_diameter': 1,
                'extract_phase': 2,
                'confidence': 0.85
            },
            # Manhole patterns
            {
                'pattern': r'(?:MH|MANHOLE)[-_]?(STORM|SD|SANIT|SS|WATER)?[-_]?(NEW|EXIST|PROP)?',
                'discipline': 'CIV',
                'category': 'UTIL',
                'object_type': 'MH',
                'extract_utility': 1,
                'extract_phase': 2,
                'confidence': 0.85
            },
            # Inlet/CB patterns
            {
                'pattern': r'(?:INLET|CB|CATCH[-_]?BASIN)[-_]?(STORM|SD)?[-_]?(NEW|EXIST|PROP)?',
                'discipline': 'CIV',
                'category': 'UTIL',
                'object_type': 'INLET',
                'extract_phase': 2,
                'confidence': 0.85
            },
            # Contour patterns
            {
                'pattern': r'(?:CONTOUR|CNTR)[-_]?(EXIST|PROP|EG|FG|NEW)?',
                'discipline': 'SITE',
                'category': 'GRAD',
                'object_type': 'CNTR',
                'extract_phase': 1,
                'confidence': 0.90
            },
            # Survey points
            {
                'pattern': r'(?:SURVEY|TOPO)[-_]?(POINT|SHOT)?',
                'discipline': 'SURV',
                'category': 'TOPO',
                'object_type': 'SHOT',
                'confidence': 0.85
            },
            # Trees
            {
                'pattern': r'TREE[-_]?(EXIST|NEW|REMOVE)?[-_]?(\d+)?(?:IN)?',
                'discipline': 'SURV',
                'category': 'TREE',
                'object_type': 'OAK',
                'extract_phase': 1,
                'extract_diameter': 2,
                'confidence': 0.80
            },
        ]
    
    def classify(self, layer_name: str) -> Optional[LayerClassification]:
        """
        Classify a layer name and extract properties.
        
        3-tier classification approach:
        1. Try standard format (highest confidence ~95%)
        2. Try database import mappings (medium-high ~80-90%)
        3. Fall back to legacy hardcoded patterns (lower ~75-85%)
        
        Args:
            layer_name: The layer name to classify
        
        Returns:
            LayerClassification object or None if not recognized
        """
        if not layer_name:
            return None
        
        layer_upper = layer_name.upper().strip()
        
        # Tier 1: Try standard format first
        standard_result = self._classify_standard(layer_upper)
        if standard_result:
            return standard_result
        
        # Tier 2: Try database import mappings
        if self.mapping_manager:
            mapping_result = self._classify_with_mapping(layer_upper)
            if mapping_result:
                return mapping_result
        
        # Tier 3: Fall back to legacy patterns
        legacy_result = self._classify_legacy(layer_upper)
        if legacy_result:
            return legacy_result
        
        return None
    
    def _classify_standard(self, layer_name: str) -> Optional[LayerClassification]:
        """
        Classify using standard format: DISC-CAT-TYPE-[ATTR]-PHASE-GEOM
        """
        components = self.builder.parse(layer_name)
        
        if not components:
            return None
        
        # Extract properties using builder
        properties = self.builder.extract_properties(layer_name)
        
        # Get database table
        database_table = self.builder.get_database_table(layer_name)
        
        # Determine object type for database
        # Map layer object_type to database object classification
        obj_type_map = {
            'STORM': 'utility_line',
            'SANIT': 'utility_line',
            'WATER': 'utility_line',
            'RECYC': 'utility_line',
            'GAS': 'utility_line',
            'ELEC': 'utility_line',
            'TELE': 'utility_line',
            'FIBER': 'utility_line',
            'MH': 'utility_structure',
            'INLET': 'utility_structure',
            'CB': 'utility_structure',
            'CLNOUT': 'utility_structure',
            'VALVE': 'utility_structure',
            'METER': 'utility_structure',
            'HYDRA': 'utility_structure',
            'PUMP': 'utility_structure',
            'CL': 'alignment',
            'CNTR': 'contour',
            'SPOT': 'spot_elevation',
            'MONUMENT': 'survey_point',
            'BENCH': 'survey_point',
            'SHOT': 'survey_point',
            'BIORT': 'bmp',
            'SWALE': 'bmp',
            'BASIN': 'bmp',
            'RAMP': 'ada_feature',
            'PATH': 'ada_feature',
            'TREE': 'site_tree',
        }
        
        object_type = obj_type_map.get(components.object_type, 'generic')
        
        # Add utility type for utility objects
        if components.category == 'UTIL':
            properties['utility_type'] = components.object_type.lower()
        
        # Add phase to properties
        properties['phase'] = components.phase
        
        return LayerClassification(
            object_type=object_type,
            properties=properties,
            confidence=0.95,  # High confidence for standard format
            database_table=database_table,
            standard_layer_name=layer_name,
            original_layer_name=layer_name
        )
    
    def _classify_with_mapping(self, layer_name: str) -> Optional[LayerClassification]:
        """
        Classify using database import mapping patterns.
        This handles client-specific CAD standards.
        """
        match = self.mapping_manager.find_match(layer_name)
        
        if not match:
            return None
        
        # Build standard layer name from matched components
        standard_name = self.builder.build(
            discipline=match.discipline_code,
            category=match.category_code,
            object_type=match.type_code,
            phase=match.phase_code,
            geometry=match.geometry_code,
            attributes=match.attributes
        )
        
        if not standard_name:
            return None
        
        # Build properties
        properties = {
            'discipline': match.discipline_code,
            'category': match.category_code,
            'type': match.type_code,
            'phase': match.phase_code,
            'geometry': match.geometry_code,
        }
        
        # Add attributes
        if match.attributes:
            for i, attr in enumerate(match.attributes):
                properties[f'attribute_{i+1}'] = attr
        
        # Map to object type
        obj_type_map = {
            'STORM': 'utility_line',
            'SANIT': 'utility_line',
            'WATER': 'utility_line',
            'RECYC': 'utility_line',
            'GAS': 'utility_line',
            'ELEC': 'utility_line',
            'TELE': 'utility_line',
            'FIBER': 'utility_line',
            'MH': 'utility_structure',
            'INLET': 'utility_structure',
            'CB': 'utility_structure',
            'CLNOUT': 'utility_structure',
            'VALVE': 'utility_structure',
            'METER': 'utility_structure',
            'HYDRA': 'utility_structure',
            'PUMP': 'utility_structure',
            'CNTR': 'contour',
            'SPOT': 'spot_elevation',
            'MONUMENT': 'survey_point',
            'BENCH': 'survey_point',
            'SHOT': 'survey_point',
            'BIORT': 'bmp',
            'SWALE': 'bmp',
            'BASIN': 'bmp',
            'RAMP': 'ada_feature',
            'PATH': 'ada_feature',
            'TREE': 'site_tree',
        }
        
        object_type = obj_type_map.get(match.type_code, 'generic')
        
        # Add utility type for utility objects
        if match.category_code == 'UTIL':
            properties['utility_type'] = match.type_code.lower()
        
        return LayerClassification(
            object_type=object_type,
            properties=properties,
            confidence=match.confidence,
            database_table=None,  # Could enhance to look this up
            standard_layer_name=standard_name,
            original_layer_name=layer_name
        )
    
    def _classify_legacy(self, layer_name: str) -> Optional[LayerClassification]:
        """
        Classify using legacy pattern matching for non-standard layers.
        """
        for pattern_def in self.legacy_patterns:
            match = re.search(pattern_def['pattern'], layer_name, re.IGNORECASE)
            
            if match:
                properties = {}
                
                # Extract diameter if specified
                if 'extract_diameter' in pattern_def:
                    try:
                        diameter = match.group(pattern_def['extract_diameter'])
                        if diameter:
                            properties['diameter_inches'] = int(diameter)
                    except (ValueError, IndexError):
                        pass
                
                # Extract phase if specified
                if 'extract_phase' in pattern_def:
                    try:
                        phase_raw = match.group(pattern_def['extract_phase'])
                        if phase_raw:
                            phase_map = {
                                'NEW': 'NEW',
                                'EXIST': 'EXIST',
                                'PROP': 'PROP',
                                'PROPOSED': 'PROP',
                                'EXISTING': 'EXIST',
                                'EG': 'EXIST',
                                'FG': 'PROP'
                            }
                            properties['phase'] = phase_map.get(phase_raw.upper(), 'EXIST')
                    except IndexError:
                        properties['phase'] = 'EXIST'
                
                # Extract utility type if specified
                if 'extract_utility' in pattern_def:
                    try:
                        utility_raw = match.group(pattern_def['extract_utility'])
                        if utility_raw:
                            utility_map = {
                                'STORM': 'storm',
                                'SD': 'storm',
                                'SANIT': 'sanitary',
                                'SS': 'sanitary',
                                'WATER': 'water',
                                'W': 'water'
                            }
                            properties['utility_type'] = utility_map.get(utility_raw.upper(), 'storm')
                    except IndexError:
                        pass
                
                # Add discipline and category
                properties['discipline'] = pattern_def['discipline']
                properties['category'] = pattern_def['category']
                properties['object_type'] = pattern_def['object_type']
                
                # Map to database table
                if pattern_def['object_type'] in ['STORM', 'SANIT', 'WATER', 'RECYC', 'GAS', 'ELEC']:
                    database_table = 'utility_lines'
                    object_type = 'utility_line'
                elif pattern_def['object_type'] in ['MH', 'INLET', 'CB', 'CLNOUT', 'VALVE', 'HYDRA']:
                    database_table = 'utility_structures'
                    object_type = 'utility_structure'
                elif pattern_def['object_type'] == 'CNTR':
                    database_table = 'drawing_entities'
                    object_type = 'contour'
                elif pattern_def['object_type'] == 'SHOT':
                    database_table = 'survey_points'
                    object_type = 'survey_point'
                else:
                    database_table = 'drawing_entities'
                    object_type = 'generic'
                
                # Generate standard layer name
                standard_name = self._generate_standard_name(
                    pattern_def['discipline'],
                    pattern_def['category'],
                    pattern_def['object_type'],
                    properties
                )
                
                return LayerClassification(
                    object_type=object_type,
                    properties=properties,
                    confidence=pattern_def['confidence'],
                    database_table=database_table,
                    standard_layer_name=standard_name,
                    original_layer_name=layer_name
                )
        
        return None
    
    def _generate_standard_name(self, 
                                 discipline: str,
                                 category: str,
                                 object_type: str,
                                 properties: Dict) -> str:
        """
        Generate a standard layer name from extracted properties.
        """
        attributes = []
        
        # Add diameter
        if 'diameter_inches' in properties:
            attributes.append(f"{properties['diameter_inches']}IN")
        
        # Get phase (default to EXIST)
        phase = properties.get('phase', 'EXIST')
        
        # Assume line geometry for pipes, point for structures
        if object_type in ['STORM', 'SANIT', 'WATER', 'RECYC', 'GAS', 'ELEC']:
            geometry = 'LN'
        elif object_type in ['MH', 'INLET', 'CB', 'CLNOUT', 'VALVE', 'HYDRA']:
            geometry = 'PT'
        elif object_type == 'CNTR':
            geometry = 'LN'
        elif object_type == 'SHOT':
            geometry = 'PT'
        else:
            geometry = 'LN'
        
        # Build standard name
        standard_name = self.builder.build(
            discipline=discipline,
            category=category,
            object_type=object_type,
            phase=phase,
            geometry=geometry,
            attributes=attributes
        )
        
        return standard_name or f"{discipline}-{category}-{object_type}-{phase}-{geometry}"


def demo():
    """Demonstrate the classifier"""
    classifier = LayerClassifierV2()
    
    print("\n" + "="*60)
    print("Layer Classifier V2 Demo")
    print("="*60 + "\n")
    
    test_layers = [
        # Standard format
        'CIV-UTIL-STORM-12IN-NEW-LN',
        'CIV-ROAD-CL-PROP-LN',
        'SURV-CTRL-MONUMENT-EXIST-PT',
        'CIV-STOR-BIORT-500CF-NEW-PG',
        
        # Legacy formats (common in the wild)
        '12IN-STORM',
        'SD-8-NEW',
        'MH-STORM-EXIST',
        'CONTOUR-EXIST',
        'SURVEY-POINT',
        'TREE-EXIST-24IN',
    ]
    
    for layer in test_layers:
        print(f"Layer: {layer}")
        classification = classifier.classify(layer)
        
        if classification:
            print(f"  ✓ Recognized as: {classification.object_type}")
            print(f"  Confidence: {classification.confidence * 100:.0f}%")
            print(f"  Database table: {classification.database_table}")
            if classification.standard_layer_name != classification.original_layer_name:
                print(f"  Standard name: {classification.standard_layer_name}")
            
            # Show key properties
            props = classification.properties
            if 'diameter_inches' in props:
                print(f"  Diameter: {props['diameter_inches']}\"")
            if 'phase' in props:
                print(f"  Phase: {props['phase']}")
            if 'utility_type' in props:
                print(f"  Utility: {props['utility_type']}")
        else:
            print("  ✗ Not recognized")
        
        print()
    
    print("="*60 + "\n")


if __name__ == '__main__':
    demo()
