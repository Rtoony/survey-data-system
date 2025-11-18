"""
Import Mapping Manager
Manages regex patterns for translating client CAD layer names to standard format.

Key Features:
- Pre-compiled regex patterns for performance
- Conflict detection when multiple patterns match
- Entity Registry validation
- Standards compliance checking
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.db_utils import execute_query
from services.entity_registry import EntityRegistry
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    mapping_id: Optional[int] = None
    entity_valid: bool = True
    has_conflicts: bool = False
    conflict_patterns: List[str] = None

    def __post_init__(self):
        if self.conflict_patterns is None:
            self.conflict_patterns = []

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
            'source_pattern': self.source_pattern,
            'mapping_id': self.mapping_id,
            'entity_valid': self.entity_valid,
            'has_conflicts': self.has_conflicts,
            'conflict_patterns': self.conflict_patterns
        }


class ImportMappingManager:
    """
    Manages import mapping patterns for converting client CAD layers to standard format.

    Uses regex patterns with named capture groups to extract components from various
    client naming conventions.

    Features:
    - Pre-compiled regex patterns for performance (no recompilation on each match)
    - Conflict detection when multiple patterns match
    - Entity Registry validation for extracted types
    - Comprehensive logging and error handling
    """

    def __init__(self, validate_entities: bool = True):
        """
        Initialize mapping manager and load patterns from database.

        Args:
            validate_entities: Whether to validate extracted types against Entity Registry
        """
        self.patterns = []
        self.compiled_patterns = {}  # Cache for compiled regex patterns
        self.validate_entities = validate_entities
        self.entity_registry = EntityRegistry()
        self._load_patterns()
        logger.info(f"Loaded {len(self.patterns)} import mapping patterns")
    
    def _load_patterns(self):
        """Load all active mapping patterns from database and pre-compile regex"""
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
            # Pre-compile all regex patterns for performance
            for pattern_data in self.patterns:
                mapping_id = pattern_data['mapping_id']
                regex_pattern = pattern_data['regex_pattern']
                try:
                    self.compiled_patterns[mapping_id] = re.compile(regex_pattern, re.IGNORECASE)
                    logger.debug(f"Pre-compiled pattern {mapping_id}: {regex_pattern}")
                except re.error as e:
                    logger.error(f"Failed to compile pattern {mapping_id}: {e}")
                    # Mark pattern as invalid in compiled cache
                    self.compiled_patterns[mapping_id] = None
    
    def find_match(self, layer_name: str, detect_conflicts: bool = True) -> Optional[MappingMatch]:
        """
        Find the best matching pattern for a layer name.

        Args:
            layer_name: Client CAD layer name
            detect_conflicts: Whether to detect and report conflicting patterns

        Returns:
            MappingMatch object or None if no match found

        Features:
        - Uses pre-compiled regex patterns for performance
        - Detects conflicting patterns
        - Validates against Entity Registry
        """
        if not layer_name:
            return None

        matches = []
        conflict_patterns = []

        # Try each pattern in order (sorted by confidence)
        for pattern_data in self.patterns:
            mapping_id = pattern_data['mapping_id']
            compiled_regex = self.compiled_patterns.get(mapping_id)

            # Skip patterns that failed to compile
            if compiled_regex is None:
                continue

            extraction_rules = pattern_data.get('extraction_rules', {})

            try:
                match = compiled_regex.match(layer_name)
                if match:
                    # Extract components using extraction rules
                    result = self._extract_components(
                        match,
                        pattern_data,
                        extraction_rules
                    )
                    if result:
                        matches.append((result, pattern_data))

                        # If not detecting conflicts, return first match
                        if not detect_conflicts:
                            return result

            except Exception as e:
                logger.error(f"Error matching pattern {mapping_id} against '{layer_name}': {e}")
                continue

        # No matches found
        if not matches:
            logger.debug(f"No mapping pattern matched '{layer_name}'")
            return None

        # Return best match (first in list, sorted by confidence)
        best_match, best_pattern = matches[0]

        # Detect conflicts
        if detect_conflicts and len(matches) > 1:
            best_match.has_conflicts = True
            for result, pattern_data in matches[1:]:
                conflict_info = f"{pattern_data['source_pattern']} (ID: {pattern_data['mapping_id']})"
                best_match.conflict_patterns.append(conflict_info)
            logger.warning(
                f"Layer '{layer_name}' matched {len(matches)} patterns. "
                f"Using highest confidence: {best_pattern['source_pattern']} "
                f"(confidence: {best_pattern['confidence_score']})"
            )

        return best_match
    
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

        Also validates extracted types against Entity Registry if enabled.
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
                logger.warning(f"Pattern {pattern_data['mapping_id']} missing required components")
                return None

            confidence = pattern_data.get('confidence_score', 80) / 100.0

            # Validate against Entity Registry if enabled
            entity_valid = True
            if self.validate_entities and obj_type:
                # Construct potential entity type from extracted components
                # Common pattern: discipline_type (e.g., "utility_line", "survey_point")
                potential_entity_types = [
                    obj_type.lower(),
                    f"{discipline.lower()}_{obj_type.lower()}",
                    f"{category.lower()}_{obj_type.lower()}"
                ]

                # Check if any potential entity type is valid
                entity_valid = any(
                    self.entity_registry.is_valid_entity_type(et)
                    for et in potential_entity_types
                )

                if not entity_valid:
                    logger.debug(
                        f"Extracted type '{obj_type}' not found in Entity Registry. "
                        f"Checked: {potential_entity_types}"
                    )

            return MappingMatch(
                discipline_code=discipline,
                category_code=category,
                type_code=obj_type,
                attributes=attributes,
                phase_code=phase,
                geometry_code=geometry,
                confidence=confidence,
                client_name=pattern_data.get('client_name'),
                source_pattern=pattern_data.get('source_pattern'),
                mapping_id=pattern_data.get('mapping_id'),
                entity_valid=entity_valid
            )

        except Exception as e:
            logger.error(f"Error extracting components from pattern {pattern_data.get('mapping_id')}: {e}")
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
