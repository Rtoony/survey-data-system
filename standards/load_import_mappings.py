"""
Load Common Import Mapping Patterns
Populates import_mapping_patterns table with common client CAD standards.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from standards.import_mapping_manager import ImportMappingManager

def load_common_patterns():
    """Load common client CAD layer patterns"""
    manager = ImportMappingManager()
    
    patterns = [
        # ========== UTILITY PATTERNS ==========
        
        # Pattern 1: Size-UtilityType format (e.g., "12IN-STORM", "8IN-SEWER")
        {
            'client_name': 'Generic',
            'source_pattern': 'SIZE-UTILITY (e.g., 12IN-STORM)',
            'regex_pattern': r'^(?P<size>\d+IN)-(?P<utility_type>STORM|SEWER|WATER|GAS|ELECTRIC|SANITARY)$',
            'extraction_rules': {
                'discipline': 'CIV',
                'category': 'UTIL',
                'type': 'group:utility_type',
                'attributes': ['group:size'],
                'phase': 'NEW',
                'geometry': 'LN'
            },
            'discipline_code': 'CIV',
            'category_code': 'UTIL',
            'confidence_score': 85
        },
        
        # Pattern 2: Abbrev-Size-Phase (e.g., "SD-8-NEW", "W-12-EXIST")
        {
            'client_name': 'Generic',
            'source_pattern': 'ABBREV-SIZE-PHASE (e.g., SD-8-NEW)',
            'regex_pattern': r'^(?P<abbrev>SD|SS|W|S|G|E)-(?P<size>\d+)-(?P<phase>NEW|EXIST|PROP|DEMO)$',
            'extraction_rules': {
                'discipline': 'CIV',
                'category': 'UTIL',
                'type': 'group:abbrev',
                'attributes': ['group:size'],
                'phase': 'group:phase',
                'geometry': 'LN'
            },
            'discipline_code': 'CIV',
            'category_code': 'UTIL',
            'confidence_score': 90
        },
        
        # Pattern 3: Manhole/Structure (e.g., "MH-NEW", "CB-EXIST")
        {
            'client_name': 'Generic',
            'source_pattern': 'STRUCTURE-PHASE (e.g., MH-NEW, CB-EXIST)',
            'regex_pattern': r'^(?P<structure>MH|CB|INLET|CATCH BASIN|CLEANOUT)-(?P<phase>NEW|EXIST|PROP|DEMO)$',
            'extraction_rules': {
                'discipline': 'CIV',
                'category': 'UTIL',
                'type': 'group:structure',
                'attributes': [],
                'phase': 'group:phase',
                'geometry': 'PT'
            },
            'discipline_code': 'CIV',
            'category_code': 'UTIL',
            'confidence_score': 88
        },
        
        # Pattern 4: Simple utility type (e.g., "STORM", "SANITARY")
        {
            'client_name': 'Generic',
            'source_pattern': 'UTILITY (e.g., STORM, SANITARY)',
            'regex_pattern': r'^(?P<utility_type>STORM|SANITARY|WATER|GAS|SEWER)$',
            'extraction_rules': {
                'discipline': 'CIV',
                'category': 'UTIL',
                'type': 'group:utility_type',
                'attributes': [],
                'phase': 'EXIST',
                'geometry': 'LN'
            },
            'discipline_code': 'CIV',
            'category_code': 'UTIL',
            'confidence_score': 75
        },
        
        # ========== ROAD/TRANSPORTATION PATTERNS ==========
        
        # Pattern 5: Road centerline (e.g., "CL-NEW", "CENTERLINE")
        {
            'client_name': 'Generic',
            'source_pattern': 'CENTERLINE (e.g., CL, CL-NEW)',
            'regex_pattern': r'^(?P<road_element>CL|CENTERLINE|CENTER LINE)(-(?P<phase>NEW|EXIST|PROP|DEMO))?$',
            'extraction_rules': {
                'discipline': 'CIV',
                'category': 'ROAD',
                'type': 'CNTR',
                'attributes': [],
                'phase': 'group:phase',
                'geometry': 'LN'
            },
            'discipline_code': 'CIV',
            'category_code': 'ROAD',
            'type_code': 'CNTR',
            'confidence_score': 90
        },
        
        # Pattern 6: Curb/Gutter (e.g., "CURB-NEW", "GUTTER")
        {
            'client_name': 'Generic',
            'source_pattern': 'CURB/GUTTER (e.g., CURB-NEW)',
            'regex_pattern': r'^(?P<element>CURB|GUTTER|CURB AND GUTTER)(-(?P<phase>NEW|EXIST|PROP|DEMO))?$',
            'extraction_rules': {
                'discipline': 'CIV',
                'category': 'ROAD',
                'type': 'CURB',
                'attributes': [],
                'phase': 'group:phase',
                'geometry': 'LN'
            },
            'discipline_code': 'CIV',
            'category_code': 'ROAD',
            'type_code': 'CURB',
            'confidence_score': 88
        },
        
        # Pattern 7: Pavement edge (e.g., "PAVE-EDGE", "EDGE-EXIST")
        {
            'client_name': 'Generic',
            'source_pattern': 'PAVEMENT EDGE (e.g., PAVE-EDGE)',
            'regex_pattern': r'^(?P<element>PAVE|PAVEMENT|EDGE)(-(?P<modifier>EDGE|OF PAVEMENT))?(-(?P<phase>NEW|EXIST|PROP|DEMO))?$',
            'extraction_rules': {
                'discipline': 'CIV',
                'category': 'ROAD',
                'type': 'EDGE',
                'attributes': [],
                'phase': 'group:phase',
                'geometry': 'LN'
            },
            'discipline_code': 'CIV',
            'category_code': 'ROAD',
            'type_code': 'EDGE',
            'confidence_score': 85
        },
        
        # ========== GRADING/TOPOGRAPHY PATTERNS ==========
        
        # Pattern 8: Contours (e.g., "CONTOUR-EXIST", "TOPO-1FT")
        {
            'client_name': 'Generic',
            'source_pattern': 'CONTOURS (e.g., CONTOUR-EXIST)',
            'regex_pattern': r'^(?P<element>CONTOUR|TOPO|TOPOGRAPHY)(-(?P<interval>\d+FT|MAJOR|MINOR))?(-(?P<phase>NEW|EXIST|PROP))?$',
            'extraction_rules': {
                'discipline': 'SURV',
                'category': 'TOPO',
                'type': 'CNTR',
                'attributes': ['group:interval'],
                'phase': 'group:phase',
                'geometry': 'LN'
            },
            'discipline_code': 'SURV',
            'category_code': 'TOPO',
            'confidence_score': 87
        },
        
        # Pattern 9: Elevation points (e.g., "SPOT-ELEV", "ELEV")
        {
            'client_name': 'Generic',
            'source_pattern': 'SPOT ELEVATION (e.g., SPOT-ELEV)',
            'regex_pattern': r'^(?P<element>SPOT|ELEV|ELEVATION|SPOT ELEV|SPOT ELEVATION)(-(?P<phase>NEW|EXIST|PROP))?$',
            'extraction_rules': {
                'discipline': 'SURV',
                'category': 'TOPO',
                'type': 'SPOT',
                'attributes': [],
                'phase': 'group:phase',
                'geometry': 'PT'
            },
            'discipline_code': 'SURV',
            'category_code': 'TOPO',
            'confidence_score': 85
        },
        
        # ========== SURVEY CONTROL PATTERNS ==========
        
        # Pattern 10: Control monuments (e.g., "MONUMENT", "CONTROL-PT")
        {
            'client_name': 'Generic',
            'source_pattern': 'CONTROL MONUMENT (e.g., MONUMENT)',
            'regex_pattern': r'^(?P<element>MONUMENT|CONTROL|CONTROL PT|BENCHMARK|BM)(-(?P<phase>EXIST|FOUND|SET))?$',
            'extraction_rules': {
                'discipline': 'SURV',
                'category': 'CTRL',
                'type': 'MONUMENT',
                'attributes': [],
                'phase': 'group:phase',
                'geometry': 'PT'
            },
            'discipline_code': 'SURV',
            'category_code': 'CTRL',
            'type_code': 'MONUMENT',
            'confidence_score': 92
        },
        
        # ========== ADA COMPLIANCE PATTERNS ==========
        
        # Pattern 11: ADA ramps (e.g., "RAMP-ADA", "ADA-RAMP")
        {
            'client_name': 'Generic',
            'source_pattern': 'ADA RAMP (e.g., ADA-RAMP)',
            'regex_pattern': r'^(?P<element>ADA|RAMP|ADA RAMP|HANDICAP RAMP)(-(?P<phase>NEW|EXIST|PROP))?$',
            'extraction_rules': {
                'discipline': 'CIV',
                'category': 'ADA',
                'type': 'RAMP',
                'attributes': [],
                'phase': 'group:phase',
                'geometry': 'PG'
            },
            'discipline_code': 'CIV',
            'category_code': 'ADA',
            'type_code': 'RAMP',
            'confidence_score': 90
        },
        
        # ========== STORMWATER PATTERNS ==========
        
        # Pattern 12: Bioretention/bioswale (e.g., "BIOSWALE-NEW", "BIO")
        {
            'client_name': 'Generic',
            'source_pattern': 'BIORETENTION (e.g., BIOSWALE-NEW)',
            'regex_pattern': r'^(?P<element>BIO|BIOSWALE|BIORETENTION|BIORT)(-(?P<phase>NEW|EXIST|PROP))?$',
            'extraction_rules': {
                'discipline': 'CIV',
                'category': 'STOR',
                'type': 'BIORT',
                'attributes': [],
                'phase': 'group:phase',
                'geometry': 'PG'
            },
            'discipline_code': 'CIV',
            'category_code': 'STOR',
            'type_code': 'BIORT',
            'confidence_score': 88
        },
    ]
    
    print("Loading import mapping patterns...")
    success_count = 0
    
    for pattern in patterns:
        success = manager.add_pattern(
            client_name=pattern['client_name'],
            source_pattern=pattern['source_pattern'],
            regex_pattern=pattern['regex_pattern'],
            extraction_rules=pattern['extraction_rules'],
            discipline_code=pattern.get('discipline_code'),
            category_code=pattern.get('category_code'),
            type_code=pattern.get('type_code'),
            confidence_score=pattern.get('confidence_score', 80)
        )
        
        if success:
            success_count += 1
            print(f"✓ {pattern['source_pattern']}")
        else:
            print(f"✗ Failed: {pattern['source_pattern']}")
    
    print(f"\nLoaded {success_count}/{len(patterns)} patterns successfully")
    return success_count == len(patterns)


if __name__ == '__main__':
    success = load_common_patterns()
    sys.exit(0 if success else 1)
