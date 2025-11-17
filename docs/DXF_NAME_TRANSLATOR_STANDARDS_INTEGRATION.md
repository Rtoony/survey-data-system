# DXF Name Translator - Standards Integration Analysis

**Date:** 2025-11-17 | **Phase:** 2A - Step 3

## Executive Summary

**Finding:** The DXF Name Translator operates in **complete isolation** from the Entity Registry and CAD Layer Vocabulary systems. There is zero validation, zero compliance checking, and zero integration with the core taxonomy that defines what constitutes a valid layer name.

---

## 1. Entity Registry Integration Status: ❌ NONE

### What Is the Entity Registry?

**File:** `services/entity_registry.py`

The Entity Registry maintains the canonical list of all valid entity types in the system, organized by discipline → category → type hierarchy.

### Required Integration (Missing)

**Validation After Translation:**
```python
# CURRENT (no validation)
match = import_mapping_manager.find_match("SS-8-PROP")
# Returns: MappingMatch(type_code="STORM", ...)
# No check if "STORM" is a valid type!

# PROPOSED (with validation)
match = import_mapping_manager.find_match("SS-8-PROP")
if match:
    valid = entity_registry.validate_entity(
        discipline=match.discipline_code,
        category=match.category_code,
        type=match.type_code
    )
    if not valid:
        # Log warning, reduce confidence, or reject translation
```

### Benefits of Integration

1. **Prevent Invalid Translations:** Reject patterns that produce non-existent entity types
2. **Suggest Corrections:** If "STRM" extracted, suggest "STORM" from registry
3. **Auto-Complete:** When building patterns, offer valid types from registry
4. **Consistency:** Ensure all translations resolve to database-registered entities

---

## 2. CAD Layer Vocabulary Integration Status: ❌ NONE

### What Is the CAD Layer Vocabulary?

The Layer Vocabulary defines the **naming rules and standards** for constructing layer names:
- Discipline codes (CIV, ARCH, ELEC, etc.)
- Category codes per discipline (UTIL, SITE, STR, etc.)
- Type codes per category (STORM, WATER, SANITARY, etc.)
- Valid attributes, phase codes, geometry codes

**Expected Location:** `standards/layer_vocabulary.py` or similar (not found in codebase)

### Required Integration (Missing)

**Standards Validation:**
```python
# PROPOSED
def validate_against_vocabulary(mapping_match):
    """Validate extracted components against layer vocabulary rules"""

    # 1. Check discipline is valid
    if mapping_match.discipline_code not in vocabulary.get_disciplines():
        return False, "Invalid discipline code"

    # 2. Check category belongs to discipline
    valid_categories = vocabulary.get_categories(mapping_match.discipline_code)
    if mapping_match.category_code not in valid_categories:
        return False, f"Category {mapping_match.category_code} not valid for {mapping_match.discipline_code}"

    # 3. Check type belongs to category
    valid_types = vocabulary.get_types(mapping_match.category_code)
    if mapping_match.type_code not in valid_types:
        return False, f"Type {mapping_match.type_code} not valid for {mapping_match.category_code}"

    # 4. Validate attributes format
    for attr in mapping_match.attributes:
        if not vocabulary.validate_attribute(attr):
            return False, f"Invalid attribute: {attr}"

    # 5. Check phase code is valid
    if mapping_match.phase_code not in vocabulary.get_phase_codes():
        return False, f"Invalid phase code: {mapping_match.phase_code}"

    # 6. Check geometry code is valid
    if mapping_match.geometry_code not in vocabulary.get_geometry_codes():
        return False, f"Invalid geometry code: {mapping_match.geometry_code}"

    return True, "Valid"
```

### Auto-Generation from Vocabulary

**Opportunity:** Use vocabulary to auto-generate import patterns

```python
# PROPOSED: Generate patterns from vocabulary rules
def generate_patterns_from_vocabulary():
    """
    Analyze vocabulary and create generic import patterns.
    Example: If vocabulary defines "STORM" as valid type,
    generate pattern for "SS", "STM", "STORM" variations.
    """

    for type_code in vocabulary.get_all_types():
        # Get common abbreviations
        abbrevs = vocabulary.get_abbreviations(type_code)

        for abbrev in abbrevs:
            # Create pattern
            pattern = ImportPattern(
                client_name="Auto-Generated",
                source_pattern=f"{abbrev}-{{SIZE}}-{{PHASE}}",
                regex_pattern=f"^{abbrev}-(?P<size>\\d+)-(?P<phase>\\w+)$",
                extraction_rules={
                    "type": type_code,
                    "attributes": ["group:size"],
                    "phase": "group:phase"
                },
                confidence_score=70
            )
            # Save pattern
```

---

## 3. Standards Compliance Enforcement

### Pattern Quality Rules (Missing)

**Proposed Validation Rules:**

1. **Completeness Check:**
   - Pattern must extract all required components (discipline, category, type, phase, geometry)
   - Warn if pattern uses defaults instead of extracting from input

2. **Uniqueness Check:**
   - Detect overlapping patterns (same regex matches)
   - Warn if new pattern conflicts with existing high-confidence pattern

3. **Standards Conformance:**
   - Extracted components must exist in vocabulary
   - Canonical name format must match DISCIPLINE-CATEGORY-TYPE-ATTR-PHASE-GEO

4. **Confidence Calibration:**
   - Patterns with static values (not extracted) → lower confidence
   - Patterns tested and approved by user → higher confidence
   - Patterns with high override rate → reduce confidence

### Approval Workflow (Missing)

**Proposed Pattern Lifecycle:**

```
Draft → Pending Review → Approved → Active → Deprecated
  ↓          ↓              ↓         ↓          ↓
[Created] [Tested]     [Validated] [In Use]  [Replaced]
```

- **Draft:** Pattern created but not tested
- **Pending Review:** Pattern tested, awaiting standards approval
- **Approved:** Pattern validated against vocabulary/registry
- **Active:** Pattern in production use
- **Deprecated:** Pattern replaced by better pattern, kept for history

---

## 4. Integration Architecture Proposal

### Layered Validation System

```
┌─────────────────────────────────────────────────┐
│ DXF Layer Name: "SS-8-PROP"                     │
└──────────────┬──────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│ LAYER 1: Import Mapping Manager                 │
│ - Regex pattern matching                        │
│ - Component extraction                          │
│ Output: MappingMatch(..., type="STORM")         │
└──────────────┬──────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│ LAYER 2: Entity Registry Validation             │
│ - Check if STORM exists in registry             │
│ - Verify discipline/category/type hierarchy     │
│ Output: ✅ Valid entity or ❌ Unknown entity    │
└──────────────┬──────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│ LAYER 3: Layer Vocabulary Compliance            │
│ - Validate naming convention                    │
│ - Check attribute format                        │
│ - Verify phase/geometry codes                   │
│ Output: ✅ Standards-compliant or ❌ Non-standard│
└──────────────┬──────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│ FINAL OUTPUT: CIV-UTIL-STORM-8IN-PROP-LN        │
│ Status: ✅ Valid, Standards-Compliant            │
│ Confidence: 0.85                                 │
└─────────────────────────────────────────────────┘
```

### Implementation in ImportMappingManager

```python
class ImportMappingManager:
    def __init__(self):
        self.patterns = []
        self.entity_registry = EntityRegistry()  # NEW
        self.layer_vocabulary = LayerVocabulary()  # NEW
        self._load_patterns()

    def find_match(self, layer_name: str) -> Optional[ValidatedMatch]:
        # Existing pattern matching
        match = self._pattern_match(layer_name)
        if not match:
            return None

        # NEW: Validate against Entity Registry
        entity_valid, entity_msg = self.entity_registry.validate(
            match.discipline_code,
            match.category_code,
            match.type_code
        )

        # NEW: Validate against Layer Vocabulary
        vocab_valid, vocab_msg = self.layer_vocabulary.validate(match)

        # NEW: Adjust confidence based on validation
        final_confidence = match.confidence
        if not entity_valid:
            final_confidence *= 0.5  # Reduce confidence
        if not vocab_valid:
            final_confidence *= 0.7

        return ValidatedMatch(
            **match.to_dict(),
            entity_validation=entity_valid,
            vocabulary_validation=vocab_valid,
            final_confidence=final_confidence,
            validation_messages=[entity_msg, vocab_msg]
        )
```

---

## 5. Recommendations

### Critical (Implement First)

1. **Create Entity Registry Integration**
   - Add `entity_registry` reference to ImportMappingManager
   - Validate extracted type codes against registry
   - Reject or flag invalid translations

2. **Create Layer Vocabulary System**
   - Build layer_vocabulary.py module
   - Define valid codes for all components
   - Provide validation functions

3. **Add Validation to Pattern Creation**
   - When user creates pattern, test against vocabulary
   - Prevent saving patterns that produce invalid names
   - Show real-time validation feedback in UI

### High Priority

4. **Pattern Approval Workflow**
   - Add status column to import_mapping_patterns (draft/approved/active/deprecated)
   - Require standards review before activating pattern
   - Track who approved pattern and when

5. **Auto-Generate Patterns from Vocabulary**
   - Scan vocabulary for common abbreviations
   - Create generic patterns for each type code
   - Pre-populate pattern library

6. **Compliance Dashboard**
   - Show percentage of patterns that are standards-compliant
   - Highlight patterns producing non-standard names
   - Suggest corrections for non-compliant patterns

---

## 6. Integration Points Summary

| Integration | Status | Priority | Estimated Effort |
|-------------|--------|----------|------------------|
| Entity Registry | ❌ Missing | Critical | 2 days |
| Layer Vocabulary | ❌ Missing | Critical | 3 days |
| Standards Validation | ❌ Missing | Critical | 2 days |
| Pattern Approval Workflow | ❌ Missing | High | 3 days |
| Auto-Pattern Generation | ❌ Missing | Medium | 4 days |
| Compliance Dashboard | ❌ Missing | Medium | 3 days |

**Total Estimated Effort:** 17 days for full standards integration

---

**Next:** Database Schema Audit
