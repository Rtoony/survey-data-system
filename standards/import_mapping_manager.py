"""
Import Mapping Manager
Manages regex patterns for translating client CAD layer names to standard format.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.db_utils import execute_query

@dataclass
class MappingMatch:
    """Result of a successful mapping pattern match"""
    discipline_code: str
    category_code: str
    type_code: str
    attributes: List[str]
    phase_code: str
    geometry_code: str
    confidence: float
    client_name: Optional[str] = None
    source_pattern: Optional[str] = None
    
    def to_dict(self):
        return {
            'discipline_code': self.discipline_code,
            'category_code': self.category_code,
            'type_code': self.type_code,
            'attributes': self.attributes,
            'phase_code': self.phase_code,
            'geometry_code': self.geometry_code,
            'confidence': self.confidence,
            'client_name': self.client_name,
            'source_pattern': self.source_pattern
        }


class ImportMappingManager:
    """
    Manages import mapping patterns for converting client CAD layers to standard format.
    
    Uses regex patterns with named capture groups to extract components from various
    client naming conventions.
    """
    
    def __init__(self):
        """Initialize mapping manager and load patterns from database"""
        self.patterns = []
        self._load_patterns()
    
    def _load_patterns(self):
        """Load all active mapping patterns from database"""
        query = """
            SELECT 
                m.mapping_id,
                m.client_name,
                m.source_pattern,
                m.regex_pattern,
                m.extraction_rules,
                m.confidence_score,
                d.code as discipline_code,
                c.code as category_code,
                t.code as type_code
            FROM import_mapping_patterns m
            LEFT JOIN discipline_codes d ON m.target_discipline_id = d.discipline_id
            LEFT JOIN category_codes c ON m.target_category_id = c.category_id
            LEFT JOIN object_type_codes t ON m.target_type_id = t.type_id
            WHERE m.is_active = TRUE
            ORDER BY m.confidence_score DESC
        """
        
        results = execute_query(query)
        if results:
            self.patterns = results
    
    def find_match(self, layer_name: str) -> Optional[MappingMatch]:
        """
        Find the best matching pattern for a layer name.
        
        Args:
            layer_name: Client CAD layer name
            
        Returns:
            MappingMatch object or None if no match found
        """
        if not layer_name:
            return None
        
        # Try each pattern in order (sorted by confidence)
        for pattern_data in self.patterns:
            regex = pattern_data['regex_pattern']
            extraction_rules = pattern_data.get('extraction_rules', {})
            
            try:
                match = re.match(regex, layer_name, re.IGNORECASE)
                if match:
                    # Extract components using extraction rules
                    result = self._extract_components(
                        match, 
                        pattern_data,
                        extraction_rules
                    )
                    if result:
                        return result
            except re.error:
                # Skip invalid regex patterns
                continue
        
        return None
    
    def _extract_components(self, 
                           match: re.Match,
                           pattern_data: Dict,
                           extraction_rules: Dict) -> Optional[MappingMatch]:
        """
        Extract standard components from regex match using extraction rules.
        
        Extraction rules format:
        {
            "discipline": "CIV",  // Static value
            "category": "UTIL",   // Static value
            "type": "group:utility_type",  // From named group
            "attributes": ["group:size"],  // From named groups
            "phase": "group:phase",
            "geometry": "LN"  // Static default
        }
        """
        try:
            # Get matched groups
            groups = match.groupdict()
            
            # Extract discipline
            discipline = self._extract_value(
                extraction_rules.get('discipline'),
                groups,
                pattern_data.get('discipline_code')
            )
            
            # Extract category
            category = self._extract_value(
                extraction_rules.get('category'),
                groups,
                pattern_data.get('category_code')
            )
            
            # Extract type
            obj_type = self._extract_value(
                extraction_rules.get('type'),
                groups,
                pattern_data.get('type_code')
            )
            
            # Extract phase
            phase = self._extract_value(
                extraction_rules.get('phase'),
                groups,
                'NEW'  # Default
            )
            
            # Extract geometry
            geometry = self._extract_value(
                extraction_rules.get('geometry'),
                groups,
                'LN'  # Default
            )
            
            # Extract attributes (list)
            attributes = []
            attr_rules = extraction_rules.get('attributes', [])
            if isinstance(attr_rules, list):
                for attr_rule in attr_rules:
                    attr_val = self._extract_value(attr_rule, groups, None)
                    if attr_val:
                        attributes.append(attr_val)
            
            # Validate required components
            if not all([discipline, category, obj_type, phase, geometry]):
                return None
            
            confidence = pattern_data.get('confidence_score', 80) / 100.0
            
            return MappingMatch(
                discipline_code=discipline,
                category_code=category,
                type_code=obj_type,
                attributes=attributes,
                phase_code=phase,
                geometry_code=geometry,
                confidence=confidence,
                client_name=pattern_data.get('client_name'),
                source_pattern=pattern_data.get('source_pattern')
            )
            
        except Exception as e:
            print(f"Error extracting components: {e}")
            return None
    
    def _extract_value(self, rule: str, groups: Dict, default: str) -> Optional[str]:
        """
        Extract a value from regex groups or use static/default value.
        
        Rule formats:
        - "group:name" → Extract from named group
        - "CIV" → Use static value
        - None → Use default
        """
        if not rule:
            return default
        
        if isinstance(rule, str) and rule.startswith('group:'):
            group_name = rule[6:]  # Remove 'group:' prefix
            value = groups.get(group_name)
            if value:
                return value.upper()
            return default
        
        # Static value
        return str(rule).upper()
    
    def add_pattern(self,
                   client_name: str,
                   source_pattern: str,
                   regex_pattern: str,
                   extraction_rules: Dict,
                   discipline_code: Optional[str] = None,
                   category_code: Optional[str] = None,
                   type_code: Optional[str] = None,
                   confidence_score: int = 80) -> bool:
        """
        Add a new import mapping pattern to the database.
        
        Args:
            client_name: Name of client/source
            source_pattern: Human-readable pattern description
            regex_pattern: Regex with named groups
            extraction_rules: JSON rules for extracting components
            discipline_code: Optional target discipline
            category_code: Optional target category
            type_code: Optional target type
            confidence_score: 0-100 confidence score
            
        Returns:
            True if successful
        """
        # Get IDs for codes
        discipline_id = self._get_discipline_id(discipline_code) if discipline_code else None
        category_id = self._get_category_id(category_code, discipline_id) if category_code else None
        type_id = self._get_type_id(type_code, category_id) if type_code else None
        
        query = """
            INSERT INTO import_mapping_patterns
            (client_name, source_pattern, regex_pattern, extraction_rules,
             target_discipline_id, target_category_id, target_type_id, confidence_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        import json
        params = (
            client_name,
            source_pattern,
            regex_pattern,
            json.dumps(extraction_rules),
            discipline_id,
            category_id,
            type_id,
            confidence_score
        )
        
        try:
            # Execute INSERT without fetching results
            execute_query(query, params, fetch=False)
            self._load_patterns()  # Reload patterns
            return True
        except Exception as e:
            print(f"Error adding pattern: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _get_discipline_id(self, code: str) -> Optional[int]:
        """Get discipline ID from code"""
        result = execute_query(
            "SELECT discipline_id FROM discipline_codes WHERE code = %s",
            (code,)
        )
        return result[0]['discipline_id'] if result else None
    
    def _get_category_id(self, code: str, discipline_id: int) -> Optional[int]:
        """Get category ID from code and discipline"""
        result = execute_query(
            "SELECT category_id FROM category_codes WHERE code = %s AND discipline_id = %s",
            (code, discipline_id)
        )
        return result[0]['category_id'] if result else None
    
    def _get_type_id(self, code: str, category_id: int) -> Optional[int]:
        """Get type ID from code and category"""
        result = execute_query(
            "SELECT type_id FROM object_type_codes WHERE code = %s AND category_id = %s",
            (code, category_id)
        )
        return result[0]['type_id'] if result else None


# Example usage
if __name__ == '__main__':
    manager = ImportMappingManager()
    
    # Test some layer names
    test_layers = [
        "12IN-STORM",
        "SD-8-NEW",
        "W-6-EXIST",
        "SS-8-PROP",
    ]
    
    for layer in test_layers:
        match = manager.find_match(layer)
        if match:
            print(f"\n{layer} →")
            print(f"  Discipline: {match.discipline_code}")
            print(f"  Category: {match.category_code}")
            print(f"  Type: {match.type_code}")
            print(f"  Attributes: {match.attributes}")
            print(f"  Phase: {match.phase_code}")
            print(f"  Geometry: {match.geometry_code}")
            print(f"  Confidence: {match.confidence:.0%}")
        else:
            print(f"\n{layer} → No match found")
