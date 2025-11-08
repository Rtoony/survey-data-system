"""
Layer Name Builder
Generates and validates standard layer names based on the vocabulary database
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.db_utils import execute_query

@dataclass
class LayerComponents:
    """Parsed components of a layer name"""
    discipline: str
    category: str
    object_type: str
    attributes: List[str]
    phase: str
    geometry: str
    full_name: str
    
    def __str__(self):
        return self.full_name


class LayerNameBuilder:
    """
    Build and validate standard layer names using the vocabulary database.
    
    Format: DISCIPLINE-CATEGORY-TYPE-[ATTRIBUTES]-PHASE-GEOMETRY
    Example: CIV-UTIL-STORM-12IN-NEW-LN
    """
    
    def __init__(self):
        """Initialize builder and cache vocabulary"""
        self.disciplines = {}
        self.categories = {}
        self.object_types = {}
        self.phases = {}
        self.geometries = {}
        self.attributes = {}
        self._load_vocabulary()
    
    def _load_vocabulary(self):
        """Load vocabulary from database"""
        # Load disciplines
        disc_query = "SELECT code, full_name FROM discipline_codes WHERE is_active = TRUE"
        disciplines = execute_query(disc_query)
        if disciplines:
            self.disciplines = {d['code']: d['full_name'] for d in disciplines}
        
        # Load categories
        cat_query = """
            SELECT c.code, c.full_name, d.code as discipline_code
            FROM category_codes c
            JOIN discipline_codes d ON c.discipline_id = d.discipline_id
            WHERE c.is_active = TRUE
        """
        categories = execute_query(cat_query)
        if categories:
            for cat in categories:
                key = f"{cat['discipline_code']}-{cat['code']}"
                self.categories[key] = cat
        
        # Load object types
        type_query = """
            SELECT t.code, t.full_name, t.database_table,
                   d.code as discipline_code, c.code as category_code
            FROM object_type_codes t
            JOIN category_codes c ON t.category_id = c.category_id
            JOIN discipline_codes d ON c.discipline_id = d.discipline_id
            WHERE t.is_active = TRUE
        """
        types = execute_query(type_query)
        if types:
            for t in types:
                key = f"{t['discipline_code']}-{t['category_code']}-{t['code']}"
                self.object_types[key] = t
        
        # Load phases
        phase_query = "SELECT code, full_name FROM phase_codes WHERE is_active = TRUE"
        phases = execute_query(phase_query)
        if phases:
            self.phases = {p['code']: p['full_name'] for p in phases}
        
        # Load geometries
        geom_query = "SELECT code, full_name FROM geometry_codes WHERE is_active = TRUE"
        geometries = execute_query(geom_query)
        if geometries:
            self.geometries = {g['code']: g['full_name'] for g in geometries}
        
        # Load attributes
        attr_query = "SELECT code, full_name, pattern FROM attribute_codes WHERE is_active = TRUE"
        attributes = execute_query(attr_query)
        if attributes:
            self.attributes = {a['code']: a for a in attributes}
    
    def build(self, 
              discipline: str,
              category: str,
              object_type: str,
              phase: str,
              geometry: str,
              attributes: Optional[List[str]] = None) -> Optional[str]:
        """
        Build a standard layer name from components.
        
        Args:
            discipline: Discipline code (e.g., 'CIV')
            category: Category code (e.g., 'UTIL')
            object_type: Object type code (e.g., 'STORM')
            phase: Phase code (e.g., 'NEW')
            geometry: Geometry code (e.g., 'LN')
            attributes: Optional list of attribute codes (e.g., ['12IN', 'PVC'])
        
        Returns:
            Full layer name or None if invalid
        """
        # Validate components
        if discipline not in self.disciplines:
            return None
        
        cat_key = f"{discipline}-{category}"
        if cat_key not in self.categories:
            return None
        
        type_key = f"{discipline}-{category}-{object_type}"
        if type_key not in self.object_types:
            return None
        
        if phase not in self.phases:
            return None
        
        if geometry not in self.geometries:
            return None
        
        # Build layer name
        parts = [discipline, category, object_type]
        
        # Add attributes in the middle
        if attributes:
            parts.extend(attributes)
        
        # Add phase and geometry at the end
        parts.extend([phase, geometry])
        
        return '-'.join(parts)
    
    def parse(self, layer_name: str) -> Optional[LayerComponents]:
        """
        Parse a standard layer name into components.
        
        Args:
            layer_name: Full layer name (e.g., 'CIV-UTIL-STORM-12IN-NEW-LN')
        
        Returns:
            LayerComponents object or None if invalid format
        """
        if not layer_name:
            return None
        
        parts = layer_name.upper().split('-')
        
        if len(parts) < 5:  # Minimum: DISC-CAT-TYPE-PHASE-GEOM
            return None
        
        # Extract fixed positions
        discipline = parts[0]
        category = parts[1]
        geometry = parts[-1]
        phase = parts[-2]
        object_type = parts[2]
        
        # Validate core components
        if discipline not in self.disciplines:
            return None
        
        cat_key = f"{discipline}-{category}"
        if cat_key not in self.categories:
            return None
        
        type_key = f"{discipline}-{category}-{object_type}"
        if type_key not in self.object_types:
            return None
        
        if phase not in self.phases:
            return None
        
        if geometry not in self.geometries:
            return None
        
        # Extract attributes (everything between type and phase)
        attributes = parts[3:-2] if len(parts) > 5 else []
        
        return LayerComponents(
            discipline=discipline,
            category=category,
            object_type=object_type,
            attributes=attributes,
            phase=phase,
            geometry=geometry,
            full_name=layer_name
        )
    
    def validate(self, layer_name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a layer name against standards.
        
        Args:
            layer_name: Layer name to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        components = self.parse(layer_name)
        
        if not components:
            return False, "Invalid layer name format or unrecognized components"
        
        return True, None
    
    def get_database_table(self, layer_name: str) -> Optional[str]:
        """
        Get the database table for objects on this layer.
        
        Args:
            layer_name: Layer name
        
        Returns:
            Database table name or None
        """
        components = self.parse(layer_name)
        if not components:
            return None
        
        type_key = f"{components.discipline}-{components.category}-{components.object_type}"
        obj_type = self.object_types.get(type_key)
        
        return obj_type['database_table'] if obj_type else None
    
    def extract_properties(self, layer_name: str) -> Dict:
        """
        Extract properties from layer name for database storage.
        
        Args:
            layer_name: Layer name to parse
        
        Returns:
            Dictionary of properties
        """
        components = self.parse(layer_name)
        if not components:
            return {}
        
        properties = {
            'discipline': components.discipline,
            'category': components.category,
            'object_type': components.object_type,
            'phase': components.phase,
            'geometry': components.geometry,
            'attributes': components.attributes,
            'database_table': self.get_database_table(layer_name)
        }
        
        # Parse size attributes
        for attr in components.attributes:
            if attr.endswith('IN'):
                # Diameter in inches
                try:
                    properties['diameter_inches'] = int(attr[:-2])
                except ValueError:
                    pass
            elif attr.endswith('FT'):
                # Width/height in feet
                try:
                    properties['width_feet'] = int(attr[:-2])
                except ValueError:
                    pass
            elif attr.endswith('CF'):
                # Volume in cubic feet
                try:
                    properties['volume_cf'] = int(attr[:-2])
                except ValueError:
                    pass
            elif attr.endswith('PCT'):
                # Percentage (slope, grade)
                try:
                    properties['slope_percent'] = int(attr[3:])
                except ValueError:
                    pass
            elif attr in self.attributes:
                # Known attribute code
                attr_info = self.attributes[attr]
                if attr_info['pattern']:
                    properties[f'attr_{attr_info["attribute_category"]}'] = attr
        
        return properties
    
    def list_valid_layers(self,
                          discipline: Optional[str] = None,
                          category: Optional[str] = None,
                          object_type: Optional[str] = None) -> List[Dict]:
        """
        List all valid layer combinations.
        
        Args:
            discipline: Filter by discipline
            category: Filter by category
            object_type: Filter by object type
        
        Returns:
            List of valid layer definitions
        """
        query = """
            SELECT 
                d.code as discipline,
                c.code as category,
                t.code as object_type,
                t.full_name as type_name,
                t.database_table,
                d.full_name as discipline_name,
                c.full_name as category_name
            FROM object_type_codes t
            JOIN category_codes c ON t.category_id = c.category_id
            JOIN discipline_codes d ON c.discipline_id = d.discipline_id
            WHERE t.is_active = TRUE
        """
        
        params = []
        if discipline:
            query += " AND d.code = %s"
            params.append(discipline)
        if category:
            query += " AND c.code = %s"
            params.append(category)
        if object_type:
            query += " AND t.code = %s"
            params.append(object_type)
        
        query += " ORDER BY d.sort_order, c.sort_order, t.sort_order"
        
        return execute_query(query, tuple(params) if params else None)


def demo():
    """Demonstrate layer name builder"""
    builder = LayerNameBuilder()
    
    print("\n" + "="*60)
    print("Layer Name Builder Demo")
    print("="*60 + "\n")
    
    # Build some examples
    examples = [
        {
            'discipline': 'CIV',
            'category': 'UTIL',
            'object_type': 'STORM',
            'attributes': ['12IN'],
            'phase': 'NEW',
            'geometry': 'LN'
        },
        {
            'discipline': 'CIV',
            'category': 'ROAD',
            'object_type': 'CL',
            'attributes': [],
            'phase': 'PROP',
            'geometry': 'LN'
        },
        {
            'discipline': 'CIV',
            'category': 'ADA',
            'object_type': 'RAMP',
            'attributes': ['2PCT', '5FT'],
            'phase': 'NEW',
            'geometry': 'PG'
        },
    ]
    
    print("Building layer names:\n")
    for ex in examples:
        layer = builder.build(**ex)
        if layer:
            print(f"  ✓ {layer}")
            props = builder.extract_properties(layer)
            print(f"    Table: {props.get('database_table', 'N/A')}")
            if 'diameter_inches' in props:
                print(f"    Diameter: {props['diameter_inches']}\"")
            if 'slope_percent' in props:
                print(f"    Slope: {props['slope_percent']}%")
            print()
    
    # Parse examples
    print("\nParsing layer names:\n")
    test_layers = [
        'CIV-UTIL-STORM-12IN-NEW-LN',
        'SURV-CTRL-MONUMENT-EXIST-PT',
        'SITE-GRAD-CNTR-PROP-LN',
        'CIV-STOR-BIORT-500CF-NEW-PG'
    ]
    
    for layer in test_layers:
        components = builder.parse(layer)
        if components:
            print(f"  {layer}")
            print(f"    Discipline: {components.discipline}")
            print(f"    Category: {components.category}")
            print(f"    Type: {components.object_type}")
            print(f"    Attributes: {', '.join(components.attributes) if components.attributes else 'None'}")
            print(f"    Phase: {components.phase}")
            print(f"    Geometry: {components.geometry}")
            print()
    
    print("="*60 + "\n")


if __name__ == '__main__':
    demo()
