# CAD Standards Redesign Plan
## AI-First, Database-Centric CAD Standards System

**Date:** November 4, 2025  
**Purpose:** Master plan for redesigning CAD standards optimized for LLM understanding and database-first workflows

---

## Core Design Decisions (Finalized)

### Philosophy & Principles

1. **Naming Convention**: STRICT and CONSISTENT
   - Not necessarily traditional format (X-XXXX-XXXX)
   - Optimized for machine/LLM understanding first
   - Human translation layer available when needed
   - No ambiguity - AI should instantly know what's true

2. **Standard Type**: DESCRIPTIVE (capture what is, not prescribe what must be)
   - Standards evolve from real usage patterns
   - AI can suggest improvements based on actual practice
   - Quality scoring rewards better-described standards

3. **Governance Model**: MASTER + JUSTIFIED OVERRIDES
   - Single company-wide master standard
   - Project-specific overrides allowed only with good reason
   - No "rule breaking just to break rules"
   - All overrides tracked and reviewed for potential incorporation

4. **Consistency Priority**: ABSOLUTE
   - Standards must be consistent across all drawings and projects
   - AI shouldn't have to "work" to understand what's true
   - Predictability and reliability over flexibility

---

## Layer Standards Design

### Core Requirements

**Semantic Groupings:**
- Layers capture meaningful semantic categories beyond discipline codes
- Groups include: discipline, object type, lifecycle phase, visibility context
- Each layer has rich metadata for AI discovery

**Lifecycle States:**
- `active` - Current standard, use for all new work
- `deprecated` - Being phased out, do not use for new work
- `archived` - Historical only, retained for old project reference
- `draft` - Under development, not yet approved
- `superseded_by` - Points to replacement layer

**AI-Discoverable Metadata:**
Layers encode information that AI can extract:
- Viewport visibility rules (scale-dependent)
- Typical associated blocks/symbols
- Related details and sheet notes
- Common object types that appear on this layer
- Best Management Practices (BMPs)
- Code/specification references
- Discipline relationships

### Layer Naming Structure (To Be Designed)

**Requirements:**
- Strict format, machine-parseable
- Embeds semantic meaning in the name itself
- Consistent across all disciplines
- Not bound by traditional CAD conventions
- Can be algorithmically translated to NCS/client standards if needed

**Open Questions for LLM Design Session:**
1. What delimiter structure? (underscore, dash, dot, mixed?)
2. How many segments? (discipline-type-subtype? or more granular?)
3. Should lifecycle be in the name or metadata only?
4. How to handle cross-discipline layers?
5. Naming convention for temporary/construction-phase layers?

### Layer Metadata Schema

```json
{
  "layer_id": "uuid",
  "layer_name": "STRING - strict format TBD",
  "canonical_name": "human_readable_name",
  "discipline": "civil|architectural|structural|mechanical|electrical|plumbing|landscape|survey",
  "lifecycle_state": "active|deprecated|archived|draft",
  "superseded_by": "layer_id or null",
  
  "semantic_groups": {
    "object_category": "utility|building|site|annotation|reference",
    "material_type": "concrete|asphalt|pipe|wire|vegetation",
    "phase": "existing|demolition|new_construction|future",
    "purpose": "design|construction|as_built|coordination"
  },
  
  "visibility_rules": {
    "viewport_display": {
      "min_scale": "1:100",
      "max_scale": "1:1",
      "default_visibility": true,
      "freeze_in": ["overall_site_plan", "key_plan"]
    },
    "print_priority": 5,
    "typical_color_index": 7,
    "typical_linetype": "continuous|dashed|hidden",
    "typical_lineweight": 0.25
  },
  
  "relationships": {
    "required_symbols": ["symbol_id_1", "symbol_id_2"],
    "common_symbols": ["symbol_id_3", "symbol_id_4"],
    "related_layers": ["layer_id_1", "layer_id_2"],
    "appears_in_details": ["detail_id_1", "detail_id_2"],
    "references_sheet_notes": ["note_id_1", "note_id_2"],
    "governed_by_bmps": ["bmp_id_1", "bmp_id_2"]
  },
  
  "technical_specs": {
    "typical_objects": ["polyline", "circle", "text", "block"],
    "geometry_type": "2D|3D|mixed",
    "coordination_critical": true,
    "clash_detection_enabled": true
  },
  
  "regulatory_context": {
    "code_references": ["IBC", "CBC", "ACI318"],
    "spec_sections": ["02300", "02500"],
    "authority_standards": ["APWA", "ASTM", "ASCE"]
  },
  
  "ai_metadata": {
    "embedding_vector": "1536-dim vector",
    "quality_score": 0.95,
    "usage_count": 1247,
    "last_reviewed": "2025-11-01",
    "tags": ["storm_drain", "civil", "underground", "public"]
  }
}
```

---

## Symbol/Block Standards Design

### Core Requirements

**Parametric Symbols:**
- One base symbol definition with parameters
- Parameters control: size, orientation, type variant, annotation
- Example: VALVE_GATE with parameters [diameter: 12|18|24, material: PVC|DI|STEEL]

**Real-World Object Relationships:**
- **Existing features**: Symbols represent surveyed/as-built objects
- **Proposed features**: Symbols represent design intent
- **Keynotes**: Symbols that link to text schedules/specifications
- Each symbol type has different metadata requirements

**Version Control:**
- Immutable versions with unique IDs
- Clear lineage (v2 supersedes v1)
- Migration tools to update old references
- Deprecation workflow

### Symbol Metadata Schema

```json
{
  "symbol_id": "uuid",
  "symbol_name": "STRING - strict format TBD",
  "version": "1.2.3",
  "lifecycle_state": "active|deprecated|archived|draft",
  "superseded_by": "symbol_id or null",
  
  "classification": {
    "symbol_type": "existing_feature|proposed_feature|keynote|annotation|reference",
    "discipline": "civil|landscape|architectural|structural|MEP",
    "category": "vegetation|utility|equipment|fixture|device",
    "subcategory": "tree|valve|hvac_unit|plumbing_fixture|electrical_device"
  },
  
  "parametric_definition": {
    "base_geometry": "DXF block or SVG path",
    "parameters": [
      {
        "name": "diameter",
        "type": "number",
        "unit": "inches",
        "allowed_values": [6, 8, 12, 18, 24, 36],
        "default": 12
      },
      {
        "name": "material",
        "type": "enum",
        "allowed_values": ["PVC", "DI", "STEEL", "HDPE"],
        "default": "PVC"
      }
    ],
    "dynamic_attributes": ["size_label", "material_callout"]
  },
  
  "real_world_mapping": {
    "represents_object_type": "storm_drain_inlet",
    "database_entity_type": "utility_node",
    "attribute_mapping": {
      "symbol_param_diameter": "db_field_pipe_diameter",
      "symbol_param_material": "db_field_material_type"
    }
  },
  
  "layer_association": {
    "primary_layer": "layer_id",
    "allowed_layers": ["layer_id_1", "layer_id_2"],
    "forbidden_layers": ["layer_id_3"]
  },
  
  "relationships": {
    "appears_in_details": ["detail_id_1"],
    "requires_keynote": true,
    "typical_sheet_notes": ["note_id_1", "note_id_2"],
    "manufacturer_catalogs": ["toro", "rainbird", "hunter"],
    "related_symbols": ["symbol_id_variant_1", "symbol_id_variant_2"]
  },
  
  "technical_specs": {
    "insertion_point": "center|corner|connection",
    "scale_dependent": false,
    "annotation_required": true,
    "typical_quantity_per_drawing": "few|many|varies"
  },
  
  "ai_metadata": {
    "embedding_vector": "1536-dim vector",
    "quality_score": 0.92,
    "usage_count": 456,
    "svg_preview": "base64_encoded_svg"
  }
}
```

---

## Detail Standards Design

### Core Requirements

**Static & Pre-Approved:**
- Details are reviewed and approved before becoming standards
- No on-the-fly creation in projects (only variations)
- Clear approval authority and date

**Applicability Tracking:**
- Which building types, project types, climates, code jurisdictions
- AI can suggest appropriate details for project context

**Variation Management:**
- Base detail can have project-specific modifications
- All variations logged and tracked
- Variations reviewed for potential standard incorporation
- Variation approval workflow required

### Detail Metadata Schema

```json
{
  "detail_id": "uuid",
  "detail_number": "STRING - strict format TBD",
  "detail_title": "human_readable_title",
  "lifecycle_state": "active|deprecated|archived|draft",
  "superseded_by": "detail_id or null",
  
  "approval": {
    "approved_by": "user_id",
    "approval_date": "2025-11-01",
    "review_cycle": "annual|biennial|as_needed",
    "next_review_date": "2026-11-01"
  },
  
  "classification": {
    "discipline": "civil|architectural|structural|MEP",
    "category": "foundation|wall|roof|utility|connection",
    "detail_type": "section|plan|elevation|isometric|enlarged_plan"
  },
  
  "applicability": {
    "building_types": ["commercial", "institutional", "residential_multifamily"],
    "project_types": ["new_construction", "renovation", "tenant_improvement"],
    "climate_zones": ["4C", "5A", "5B"],
    "code_jurisdictions": ["IBC_2021", "CBC_2022"],
    "construction_types": ["Type_V_wood", "Type_III_masonry"]
  },
  
  "technical_content": {
    "materials_list": ["self_adhered_membrane", "OSB_sheathing", "pressure_treated_lumber"],
    "spec_sections": ["06_10_00", "07_21_00", "07_92_00"],
    "code_references": ["IBC_1807", "CBC_1211"],
    "performance_requirements": {
      "air_barrier": true,
      "water_resistive": true,
      "thermal_insulation_R": 19
    }
  },
  
  "relationships": {
    "shown_layers": ["layer_id_1", "layer_id_2", "layer_id_3"],
    "required_symbols": ["symbol_id_1", "symbol_id_2"],
    "sheet_notes": ["note_id_1", "note_id_2"],
    "related_details": ["detail_id_companion_1"],
    "typical_sheets": ["A5.1", "A5.2"]
  },
  
  "variation_tracking": {
    "allows_variations": true,
    "variation_approval_required": true,
    "active_variations": [
      {
        "variation_id": "uuid",
        "project_id": "uuid",
        "modification_description": "Added extra layer of insulation",
        "approved_by": "user_id",
        "review_status": "approved|pending|rejected",
        "incorporate_to_standard": false
      }
    ]
  },
  
  "geometry": {
    "dxf_reference": "path/to/detail.dxf",
    "svg_preview": "base64_encoded_svg",
    "pdf_print": "path/to/detail.pdf",
    "scale": "1.5\" = 1'-0\""
  },
  
  "ai_metadata": {
    "embedding_vector": "1536-dim vector",
    "quality_score": 0.88,
    "usage_count": 234,
    "tags": ["waterproofing", "below_grade", "foundation"]
  }
}
```

---

## Abbreviation Standards Design

### Design Decisions Made for You

**Context-Aware Abbreviations:**
- YES - abbreviations should understand context
- Same abbreviation can mean different things in different contexts
- AI uses surrounding layer/object/discipline to disambiguate

**Synonym Handling:**
- System captures multiple ways to say the same thing
- All variants map to one canonical term
- Embedding-based similarity helps find related terms

**Standard Authority Tracking:**
- Track which standards body defines each abbreviation
- Allow company-specific additions
- Flag conflicts between standards

### Abbreviation Metadata Schema

```json
{
  "abbreviation_id": "uuid",
  "abbreviation": "GWB",
  "canonical_term": "gypsum_wallboard",
  
  "context_variants": [
    {
      "context": "architectural_finishes",
      "meaning": "gypsum_wallboard",
      "confidence": 0.95,
      "typical_layers": ["A-WALL", "A-FNSH"],
      "typical_disciplines": ["architectural"]
    },
    {
      "context": "demolition",
      "meaning": "gypsum_wallboard_removal",
      "confidence": 0.85,
      "typical_layers": ["A-DEMO"],
      "typical_disciplines": ["architectural"]
    }
  ],
  
  "synonyms": ["drywall", "sheetrock", "plasterboard", "gyp_board"],
  
  "classification": {
    "term_type": "material|system|action|dimension|location",
    "discipline": "architectural|civil|structural|MEP|general",
    "spec_section": "09_29_00"
  },
  
  "authority": {
    "standard_source": "CSI_MasterFormat|AIA_CAD_Layer_Guidelines|company_custom",
    "authority_abbreviation": "GWB",
    "authority_full_term": "Gypsum Wall Board",
    "conflicts": []
  },
  
  "disambiguation": {
    "needs_disambiguation": false,
    "disambiguation_hints": "Use in wall assembly contexts, interior finishes",
    "ai_resolution_strategy": "check_layer_discipline"
  },
  
  "relationships": {
    "appears_in_layers": ["layer_id_1", "layer_id_2"],
    "related_materials": ["material_id_1"],
    "spec_references": ["spec_section_id_1"]
  },
  
  "ai_metadata": {
    "embedding_vector": "1536-dim vector",
    "quality_score": 0.90,
    "usage_count": 892
  }
}
```

---

## Additional Standard Categories

### Color Standards
```json
{
  "color_id": "uuid",
  "color_name": "red_1",
  "rgb": "rgb(255, 0, 0)",
  "hex": "#FF0000",
  "autocad_index": 1,
  "purpose": "attention|warning|existing|new|demolition",
  "discipline_usage": ["architectural", "structural"],
  "accessibility_wcag": "AAA",
  "print_mapping": "CMYK or Pantone"
}
```

### Linetype Standards
```json
{
  "linetype_id": "uuid",
  "linetype_name": "dashed_2",
  "pattern": "dash-gap-dash",
  "purpose": "hidden|centerline|property_line|utility",
  "scale_factor": 1.0,
  "typical_layers": ["layer_id_1", "layer_id_2"]
}
```

### Sheet Note Standards
```json
{
  "note_id": "uuid",
  "note_number": "GN-001",
  "note_category": "general|specific|code_compliance|construction_sequence",
  "note_text": "Full text of standard note",
  "applicable_details": ["detail_id_1"],
  "applicable_symbols": ["symbol_id_1"],
  "spec_references": ["spec_id_1"],
  "always_include_in": ["sheet_type_civil_grading"],
  "ai_metadata": {...}
}
```

### BMP (Best Management Practice) Standards
```json
{
  "bmp_id": "uuid",
  "bmp_code": "EC-1",
  "bmp_title": "Erosion Control Blanket",
  "category": "erosion_control|sediment_control|waste_management",
  "regulatory_requirement": "NPDES|local_ordinance",
  "typical_symbols": ["symbol_id_1"],
  "typical_layers": ["layer_id_1"],
  "spec_references": ["spec_id_1"],
  "sheet_notes": ["note_id_1"],
  "implementation_details": ["detail_id_1"],
  "ai_metadata": {...}
}
```

---

## Knowledge Graph Relationships

### Explicit Relationship Types

**Spatial Relationships:**
- `layer_contains_symbol` - Symbol typically appears on this layer
- `detail_shows_layer` - Detail drawing displays this layer
- `symbol_requires_layer` - Symbol must be placed on this layer

**Semantic Relationships:**
- `abbreviation_used_in_layer` - Abbreviation appears in layer name
- `symbol_represents_object` - Symbol represents real-world database entity
- `detail_references_spec` - Detail calls out specification section

**Engineering Relationships:**
- `symbol_connects_to_symbol` - Network connectivity (valves connect to pipes)
- `layer_coordinates_with_layer` - Cross-discipline coordination required
- `bmp_requires_symbol` - BMP implementation needs this symbol

**Hierarchical Relationships:**
- `symbol_variant_of_base` - Parametric variations
- `detail_supersedes_detail` - Version control
- `layer_deprecated_for_layer` - Migration path

### Relationship Metadata
```json
{
  "relationship_id": "uuid",
  "source_entity_id": "uuid",
  "target_entity_id": "uuid",
  "relationship_type": "layer_contains_symbol",
  "relationship_category": "spatial|semantic|engineering|hierarchical",
  "strength": 0.85,
  "bidirectional": false,
  "metadata": {
    "frequency": "always|usually|sometimes|rarely",
    "required": true,
    "confidence": 0.92
  }
}
```

---

## Embedding Strategy

### What Each Embedding Should Capture

**Layer Embedding Content:**
```
Layer [LAYER_NAME] is a [DISCIPLINE] layer used for [PURPOSE] in [PHASE] drawings. 
It typically contains [OBJECT_TYPES] and appears at scales [SCALE_RANGE]. 
Common symbols on this layer include [SYMBOLS]. 
Related details include [DETAILS]. 
Governed by codes [CODES] and specs [SPECS]. 
Coordinates with layers [RELATED_LAYERS]. 
This layer is [LIFECYCLE_STATE] and is used for [USE_CASES].
```

**Symbol Embedding Content:**
```
Symbol [SYMBOL_NAME] represents a [OBJECT_TYPE] in [DISCIPLINE] drawings. 
It is a [FEATURE_TYPE] feature with parameters [PARAMETERS]. 
Typically placed on layer [PRIMARY_LAYER] in [DRAWING_TYPES]. 
Appears in details [DETAILS] and requires notes [NOTES]. 
Associated with [REAL_WORLD_OBJECT] in the database. 
Governed by [CODES] and manufactured by [MANUFACTURERS]. 
Current version [VERSION], status [LIFECYCLE_STATE].
```

**Detail Embedding Content:**
```
Detail [DETAIL_NUMBER] titled [TITLE] is a [CATEGORY] [DETAIL_TYPE] showing [CONTENT]. 
Applicable to [BUILDING_TYPES] in [CLIMATE_ZONES] under [CODES]. 
Shows layers [LAYERS] with symbols [SYMBOLS]. 
Materials include [MATERIALS] per specs [SPECS]. 
Achieves performance requirements [REQUIREMENTS]. 
Related to details [RELATED_DETAILS]. 
Status [LIFECYCLE_STATE], approved [APPROVAL_DATE].
```

**Abbreviation Embedding Content:**
```
Abbreviation [ABBR] means [CANONICAL_TERM] and has synonyms [SYNONYMS]. 
Used in [DISCIPLINES] contexts, particularly [CONTEXTS]. 
Appears in layers [LAYERS] and spec section [SPEC]. 
Defined by [AUTHORITY] standard. 
May need disambiguation when [DISAMBIGUATION_HINT].
```

---

## Implementation Phases

### Phase 1: Layer Standards Redesign (PRIORITY)
1. Define strict layer naming convention
2. Design complete metadata schema
3. Create master layer library (50-100 core layers)
4. Build AI classifier for existing DXF layers
5. Implement translation layer to/from NCS
6. Test with real project data

### Phase 2: Symbol Standards Implementation
1. Audit existing symbol library
2. Design parametric symbol system
3. Create version control workflow
4. Build symbol-to-database-object mapping
5. Generate embeddings for semantic search
6. Implement variation tracking

### Phase 3: Detail Standards Integration
1. Catalog approved detail library
2. Tag applicability for each detail
3. Build variation workflow
4. Link details to layers/symbols/notes
5. Create detail suggestion AI
6. Implement approval process

### Phase 4: Abbreviation & Support Systems
1. Build context-aware abbreviation resolver
2. Create BMP standards library
3. Implement sheet note management
4. Build color/linetype standards
5. Complete knowledge graph
6. Test end-to-end AI features

---

## Migration Strategy

### From Current Placeholder System

**Step 1: Layer Migration**
- Export current layer_standards table
- Classify each layer using new schema
- Generate embeddings for all layers
- Build relationships to existing symbols/details
- Quality score all entries
- Parallel run: old + new systems

**Step 2: Symbol Migration**
- Audit block_standards/block_definitions
- Extract parametric variations
- Version control assignment
- Real-world object mapping
- Relationship building
- SVG preview generation

**Step 3: Validation**
- Test DXF import with new classifier
- Test DXF export with new generator
- Verify round-trip accuracy
- AI-assisted quality checks
- User acceptance testing

**Step 4: Cutover**
- Deprecate old tables (not delete)
- Switch all APIs to new system
- Update documentation
- Training for users
- Monitor for issues

---

## Success Metrics

### Quantitative Metrics
- **Classification Accuracy**: >95% for DXF import layer classification
- **Embedding Coverage**: 100% of active standards have embeddings
- **Relationship Density**: Average 8+ relationships per standard
- **Quality Score**: Average quality score >0.85
- **Usage Tracking**: All standards have usage counts
- **Migration Success**: 100% of existing data migrated without loss

### Qualitative Metrics
- **AI Understanding**: LLM can answer complex queries about standards
- **Consistency**: Zero ambiguity in standard definitions
- **Discoverability**: Engineers find relevant standards in <2 queries
- **Maintainability**: New standards added with complete metadata
- **Governance**: Override requests tracked and reviewed

---

## Questions for Detailed Design Session

### Critical Decisions Needed

**Layer Naming Convention:**
1. Exact syntax format?
2. Number of required segments?
3. Allowed characters and delimiters?
4. Maximum length?
5. How to encode discipline, category, phase, object type?

**Symbol Parametric System:**
6. What parameter types supported? (number, enum, boolean, text, dimension)
7. How to handle parameter combinations? (not all combos valid)
8. Geometry generation: static blocks vs dynamic generation?
9. How to version parameters? (adding new parameter to existing symbol)

**Detail Management:**
10. Detail numbering scheme?
11. How granular should applicability be?
12. Variation approval workflow steps?
13. When to promote variation to standard?

**Abbreviation Context:**
14. How many context dimensions? (discipline, layer, object type, phase)
15. Confidence threshold for disambiguation?
16. Handle abbreviation conflicts between standards?

**Database Schema:**
17. Consolidate standards tables or keep separate?
18. Should lifecycle_state be enum or separate tracking table?
19. How to handle standard versions (new row vs update)?
20. Soft delete or hard delete deprecated standards?

**AI/ML Strategy:**
21. Embedding model choice? (OpenAI, local, custom fine-tuned)
22. Re-embedding frequency?
23. Relationship auto-discovery vs manual curation?
24. Quality score calculation algorithm?

---

## Deliverables for Next Phase

From your design session with another LLM, produce:

1. **Layer Naming Specification** (2-3 pages)
   - Exact syntax with regex pattern
   - Examples for each discipline
   - Edge case handling
   - Translation rules to NCS

2. **Complete Metadata Schemas** (10-15 pages)
   - JSON schemas for each standard type
   - Required vs optional fields
   - Validation rules
   - Default values

3. **Master Layer Library** (spreadsheet or JSON)
   - 50-100 core layers
   - All metadata populated
   - Relationships defined
   - Embeddings generated

4. **Symbol Parametric Specification** (3-5 pages)
   - Parameter type definitions
   - Combination rules
   - Version control process
   - 10-20 example symbols

5. **Detail Library Specification** (3-5 pages)
   - Numbering scheme
   - Applicability taxonomy
   - 20-30 example details with full metadata

6. **Implementation Roadmap** (2-3 pages)
   - Detailed task breakdown
   - Dependencies and sequencing
   - Resource requirements
   - Timeline estimate

---

## Return to Implementation

When you come back with finalized designs, we will:

1. **Update Database Schema**
   - Modify existing tables or create new ones
   - Add indexes for performance
   - Create materialized views
   - Migration scripts

2. **Build Import/Export Tools**
   - DXF classifier using new layer standards
   - DXF generator for export
   - Translation layer for client standards
   - Validation tools

3. **Implement AI Features**
   - Generate embeddings for all standards
   - Build semantic search
   - Auto-suggest standards
   - Quality scoring system
   - Relationship discovery

4. **Create Management UI**
   - CRUD interfaces for standards
   - Approval workflows
   - Variation tracking
   - Analytics dashboard
   - Quality reports

5. **Migration & Testing**
   - Migrate existing data
   - Round-trip testing
   - AI accuracy validation
   - User acceptance testing

---

**END OF PLAN**

This document captures your strategic decisions and provides a comprehensive framework for detailed design. Take this to another LLM to flesh out the specific naming conventions, metadata schemas, and master library content. Return when ready to implement.
