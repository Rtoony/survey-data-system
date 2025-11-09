"""
Layer Classifier V3 - Database-Driven
Parses CAD layer names and classifies objects using database code tables.

Replaces hardcoded regex patterns with dynamic database lookups for:
- discipline_codes
- category_codes
- object_type_codes
- phase_codes
- geometry_codes

Supports bidirectional DXF-Database translation for all object types.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
import re
from functools import lru_cache


@dataclass
class LayerClassification:
    """Classification result for a layer name."""
    object_type: str
    properties: Dict
    confidence: float
    network_mode: Optional[str] = None
    database_table: Optional[str] = None
    discipline_code: Optional[str] = None
    category_code: Optional[str] = None
    phase_code: Optional[str] = None
    geometry_code: Optional[str] = None


class LayerClassifierV3:
    """
    Database-driven layer name classifier.
    
    Parses layer names like:
    - CIV-STOR-STORM-NEW-LN → Storm drain pipe
    - CIV-ROAD-WATER-NEW-LN → Water main
    - CIV-STOR-MH-NEW-PT → Manhole
    - LAND-TREE-TREE-EXIST-PT → Existing tree
    
    Uses database code tables for validation and property extraction.
    """
    
    def __init__(self, db_config: Optional[Dict] = None, conn=None):
        """
        Initialize classifier with database connection.
        
        Args:
            db_config: Database configuration dict (host, port, database, user, password)
            conn: Existing database connection (optional, overrides db_config)
        """
        self.db_config = db_config
        self.external_conn = conn
        
        # Code caches (loaded from database)
        self.disciplines = {}
        self.categories = {}
        self.object_types = {}
        self.phases = {}
        self.geometries = {}
        
        # Load codes into memory
        self._load_codes()
    
    def _get_connection(self):
        """Get database connection (use external or create new)."""
        if self.external_conn:
            return self.external_conn, False
        elif self.db_config:
            return psycopg2.connect(**self.db_config), True
        else:
            raise ValueError("No database connection or config provided")
    
    def _load_codes(self):
        """Load all code tables into memory for fast lookups."""
        conn, should_close = self._get_connection()
        
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Load discipline codes
            cur.execute("SELECT code, full_name, description FROM discipline_codes WHERE is_active = true")
            for row in cur.fetchall():
                self.disciplines[row['code'].upper()] = dict(row)
            
            # Load category codes (with discipline relationship)
            cur.execute("""
                SELECT c.code, c.full_name, c.description, d.code as discipline_code
                FROM category_codes c
                LEFT JOIN discipline_codes d ON c.discipline_id = d.discipline_id
                WHERE c.is_active = true
            """)
            for row in cur.fetchall():
                code = row['code'].upper()
                if code not in self.categories:
                    self.categories[code] = []
                self.categories[code].append(dict(row))
            
            # Load object type codes (with category relationship and database table)
            cur.execute("""
                SELECT ot.code, ot.full_name, ot.description, ot.database_table,
                       c.code as category_code
                FROM object_type_codes ot
                LEFT JOIN category_codes c ON ot.category_id = c.category_id
                WHERE ot.is_active = true
            """)
            for row in cur.fetchall():
                code = row['code'].upper()
                if code not in self.object_types:
                    self.object_types[code] = []
                self.object_types[code].append(dict(row))
            
            # Load phase codes
            cur.execute("SELECT code, full_name, description, color_rgb FROM phase_codes WHERE is_active = true")
            for row in cur.fetchall():
                self.phases[row['code'].upper()] = dict(row)
            
            # Load geometry codes (with DXF entity type mappings)
            cur.execute("SELECT code, full_name, description, dxf_entity_types FROM geometry_codes WHERE is_active = true")
            for row in cur.fetchall():
                self.geometries[row['code'].upper()] = dict(row)
            
            cur.close()
            
        finally:
            if should_close:
                conn.close()
    
    def classify(self, layer_name: str) -> Optional[LayerClassification]:
        """
        Classify a layer name and extract properties.
        
        Args:
            layer_name: The CAD layer name to classify
        
        Returns:
            LayerClassification object or None if not recognized
        
        Examples:
            >>> classifier.classify("CIV-STOR-STORM-NEW-LN")
            LayerClassification(
                object_type='utility_line',
                properties={'utility_type': 'Storm', 'diameter_inches': None},
                confidence=1.0,
                network_mode='gravity',
                database_table='utility_lines'
            )
        """
        if not layer_name:
            return None
        
        layer_upper = layer_name.upper().strip()
        
        # Try standard format: [DISCIPLINE]-[CATEGORY]-[OBJECT_TYPE]-[PHASE]-[GEOMETRY]
        result = self._classify_standard_format(layer_upper)
        if result:
            return result
        
        # Try legacy formats for backward compatibility
        result = self._classify_legacy_format(layer_upper)
        if result:
            return result
        
        return None
    
    def _classify_standard_format(self, layer_name: str) -> Optional[LayerClassification]:
        """
        Classify using standard format: [DISC]-[CAT]-[OBJ]-[PHASE]-[GEOM]
        
        Examples:
            CIV-STOR-STORM-NEW-LN
            CIV-ROAD-WATER-NEW-LN
            LAND-TREE-TREE-EXIST-PT
        """
        parts = layer_name.split('-')
        
        if len(parts) < 3:
            return None
        
        discipline_code = parts[0]
        category_code = parts[1]
        object_code = parts[2]
        phase_code = parts[3] if len(parts) > 3 else None
        geometry_code = parts[4] if len(parts) > 4 else None
        
        # Validate discipline
        if discipline_code not in self.disciplines:
            return None
        
        discipline = self.disciplines[discipline_code]
        
        # Validate category (must match discipline)
        category = None
        if category_code in self.categories:
            for cat in self.categories[category_code]:
                if cat.get('discipline_code') == discipline_code:
                    category = cat
                    break
        
        if not category:
            return None
        
        # Extract size/material from object code if present
        object_code_clean, diameter, material = self._extract_properties(object_code)
        
        # Validate object type (must match category)
        object_type = None
        if object_code_clean in self.object_types:
            for obj in self.object_types[object_code_clean]:
                if obj.get('category_code') == category_code:
                    object_type = obj
                    break
        
        if not object_type:
            return None
        
        # Validate phase (optional)
        phase = None
        if phase_code and phase_code in self.phases:
            phase = self.phases[phase_code]
        
        # Validate geometry (optional)
        geometry = None
        if geometry_code and geometry_code in self.geometries:
            geometry = self.geometries[geometry_code]
        
        # Determine object classification
        database_table = object_type.get('database_table', 'drawing_entities')
        obj_type_name = object_type['full_name']
        
        # Map to internal object type
        internal_object_type = self._map_to_internal_type(database_table, obj_type_name)
        
        # Determine network mode for utilities
        network_mode = self._determine_network_mode(obj_type_name, category_code)
        
        # Build properties dictionary
        properties = {
            'utility_type': obj_type_name if database_table in ['utility_lines', 'utility_structures'] else None,
            'object_type': obj_type_name,
            'diameter_inches': diameter,
            'material': material,
            'phase': phase['full_name'] if phase else None,
            'structure_type': obj_type_name if database_table == 'utility_structures' else None,
            'bmp_type': obj_type_name if database_table == 'bmps' else None,
        }
        
        # Calculate confidence (100% for perfect match)
        confidence = 1.0
        if not phase:
            confidence *= 0.95
        if not geometry:
            confidence *= 0.95
        
        return LayerClassification(
            object_type=internal_object_type,
            properties=properties,
            confidence=confidence,
            network_mode=network_mode,
            database_table=database_table,
            discipline_code=discipline_code,
            category_code=category_code,
            phase_code=phase_code,
            geometry_code=geometry_code
        )
    
    def _classify_legacy_format(self, layer_name: str) -> Optional[LayerClassification]:
        """
        Classify using legacy formats for backward compatibility.
        
        Examples:
            12IN-STORM → Infer CIV-STOR-STORM
            MH-STORM-48 → Infer CIV-STOR-MH
            STORM-PROPOSED → Infer CIV-STOR-STORM-PROP
        """
        # Pattern: [SIZE][UNIT]-[TYPE]
        match = re.match(r'^(\d+)(IN|MM|FT)?-(\w+)$', layer_name)
        if match:
            size, unit, type_name = match.groups()
            diameter = int(size)
            
            # Try to find matching object type
            type_upper = type_name.upper()
            if type_upper in self.object_types:
                obj_type = self.object_types[type_upper][0]
                
                return LayerClassification(
                    object_type='utility_line',
                    properties={
                        'utility_type': obj_type['full_name'],
                        'diameter_inches': diameter,
                        'object_type': obj_type['full_name']
                    },
                    confidence=0.8,
                    network_mode=self._determine_network_mode(obj_type['full_name'], 'STOR'),
                    database_table='utility_lines',
                    discipline_code='CIV',
                    category_code='STOR'
                )
        
        # Pattern: [TYPE]-[PHASE]
        match = re.match(r'^(\w+)-(EXIST|PROPOSED|NEW|DEMO)$', layer_name)
        if match:
            type_name, phase_name = match.groups()
            
            type_upper = type_name.upper()
            if type_upper in self.object_types:
                obj_type = self.object_types[type_upper][0]
                
                # Map phase name
                phase_map = {'PROPOSED': 'PROP', 'EXIST': 'EXIST', 'NEW': 'NEW', 'DEMO': 'DEMO'}
                phase_code = phase_map.get(phase_name, 'NEW')
                
                return LayerClassification(
                    object_type='utility_line',
                    properties={
                        'utility_type': obj_type['full_name'],
                        'object_type': obj_type['full_name'],
                        'phase': self.phases.get(phase_code, {}).get('full_name')
                    },
                    confidence=0.75,
                    network_mode=self._determine_network_mode(obj_type['full_name'], 'STOR'),
                    database_table=obj_type.get('database_table', 'utility_lines'),
                    phase_code=phase_code
                )
        
        return None
    
    def _extract_properties(self, object_code: str) -> Tuple[str, Optional[int], Optional[str]]:
        """
        Extract size and material from object code.
        
        Examples:
            "12STORM" → ("STORM", 12, None)
            "8WATER" → ("WATER", 8, None)
            "STORM" → ("STORM", None, None)
            "PVC" → ("PVC", None, "PVC")
        
        Returns:
            (clean_code, diameter_inches, material)
        """
        # Pattern: [SIZE][OBJECTTYPE]
        match = re.match(r'^(\d+)([A-Z]+)$', object_code)
        if match:
            size, obj_type = match.groups()
            return (obj_type, int(size), None)
        
        # Pattern: [OBJECTTYPE][SIZE]
        match = re.match(r'^([A-Z]+)(\d+)$', object_code)
        if match:
            obj_type, size = match.groups()
            # Only if object type is known
            if obj_type in self.object_types:
                return (obj_type, int(size), None)
        
        # Check if it's a material code
        material_codes = ['PVC', 'DI', 'VCP', 'HDPE', 'RCP', 'CMP', 'CONC']
        if object_code in material_codes:
            return (object_code, None, object_code)
        
        return (object_code, None, None)
    
    def _map_to_internal_type(self, database_table: str, obj_type_name: str) -> str:
        """
        Map database table to internal object type name.
        
        Used by IntelligentObjectCreator to route to correct creation method.
        """
        table_map = {
            'utility_lines': 'utility_line',
            'utility_structures': 'utility_structure',
            'bmps': 'bmp',
            'surface_models': 'surface_model',
            'horizontal_alignments': 'alignment',
            'survey_points': 'survey_point',
            'site_trees': 'site_tree',
            'parcels': 'parcel',
            'drawing_entities': 'drawing_entity'
        }
        
        return table_map.get(database_table, 'drawing_entity')
    
    def _determine_network_mode(self, utility_type: str, category_code: str) -> Optional[str]:
        """
        Determine if utility is gravity or pressure mode.
        
        Gravity systems: Storm, Sanitary
        Pressure systems: Water, Recycled Water, Gas, Electric, etc.
        """
        utility_upper = utility_type.upper()
        
        # Gravity systems
        if any(x in utility_upper for x in ['STORM', 'SANITARY', 'SANIT', 'SEWER']):
            return 'gravity'
        
        # Pressure systems
        if any(x in utility_upper for x in ['WATER', 'GAS', 'ELECTRIC', 'ELEC', 'TELE', 'FIBER']):
            return 'pressure'
        
        # Default to gravity for drainage category
        if category_code == 'STOR':
            return 'gravity'
        
        return None
    
    def get_supported_disciplines(self) -> List[str]:
        """Return list of supported discipline codes."""
        return sorted(self.disciplines.keys())
    
    def get_supported_categories(self, discipline_code: Optional[str] = None) -> List[str]:
        """Return list of supported category codes, optionally filtered by discipline."""
        if discipline_code:
            categories = []
            for code, cat_list in self.categories.items():
                for cat in cat_list:
                    if cat.get('discipline_code') == discipline_code.upper():
                        categories.append(code)
            return sorted(categories)
        else:
            return sorted(self.categories.keys())
    
    def get_supported_object_types(self, category_code: Optional[str] = None) -> List[str]:
        """Return list of supported object type codes, optionally filtered by category."""
        if category_code:
            types = []
            for code, type_list in self.object_types.items():
                for obj_type in type_list:
                    if obj_type.get('category_code') == category_code.upper():
                        types.append(code)
            return sorted(types)
        else:
            return sorted(self.object_types.keys())
    
    def get_database_table_for_object(self, object_type_code: str, category_code: Optional[str] = None) -> Optional[str]:
        """Get the database table name for a given object type code."""
        if object_type_code.upper() in self.object_types:
            for obj_type in self.object_types[object_type_code.upper()]:
                if not category_code or obj_type.get('category_code') == category_code.upper():
                    return obj_type.get('database_table')
        return None
    
    def reload_codes(self):
        """Reload code tables from database (call after database updates)."""
        self.disciplines.clear()
        self.categories.clear()
        self.object_types.clear()
        self.phases.clear()
        self.geometries.clear()
        self._load_codes()


# Backward compatibility alias
LayerClassification = LayerClassification
