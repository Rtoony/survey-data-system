# ACAD-GIS Architecture Documentation Audit Report

**Date:** November 17, 2025  
**Scope:** 7 Architecture Documentation Files + README.md + replit.md  
**Total Issues Found:** 20 (4 Critical, 8 High, 8 Medium)

---

## Executive Summary

The architecture documentation reveals **significant inconsistencies** between:
1. Multiple architecture documents describing the same systems
2. Documentation vs. actual database schema
3. Stated architectural principles vs. implementation
4. Terminology and naming conventions

While the core AI-first database architecture is sound, **Truth-Driven Architecture violations** undermine the system's data quality goals, and **schema inconsistencies** create confusion for developers.

---

## CRITICAL ISSUES (Must Fix Immediately)

### 1. Material Standards FK Constraint Gap (CRITICAL)

**Files:** TRUTH_DRIVEN_ARCHITECTURE.md, CIVIL_ENGINEERING_DOMAIN_MODEL.md, Actual Schema

**Problem:**
- TRUTH_DRIVEN_ARCHITECTURE.md claims `material_standards` table has "✅ Full CRUD (Schema Explorer)" status (line 71)
- But later admits it's "Partially implemented - `material_standards` exists but NOT enforced via FK" (line 244)
- CIVIL_ENGINEERING_DOMAIN_MODEL.md shows:
  ```sql
  material VARCHAR(100),    -- FREE TEXT! No FK constraint
  ```
- Actual schema confirms: `material character varying(100)` with NO FK on utility_lines
- Same issue in utility_structures

**Impact:** Material values are inconsistent across database (PVC, pvc, P.V.C., Polyvinyl Chloride), breaking:
- Compliance rules (can't enforce "material must be PVC")
- AI semantic search (embeddings see different strings as different)
- Reporting accuracy (cost estimation by material fails)
- Standards enforcement (Detail cross-references fail)

**Status:** ❌ **Not compliant with truth-driven architecture**

**Fix Required:**
```sql
-- Add foreign key constraint to utility_lines.material
ALTER TABLE utility_lines 
ADD CONSTRAINT fk_utility_lines_material 
FOREIGN KEY (material) REFERENCES material_standards(material_code);
```

---

### 2. Structure Type Standardization Status Conflict (CRITICAL)

**Files:** TRUTH_DRIVEN_ARCHITECTURE.md vs CIVIL_ENGINEERING_DOMAIN_MODEL.md

**Problem:**
- TRUTH_DRIVEN_ARCHITECTURE.md (line 271) lists Structure Types as "⚠️ Not implemented" with "Status: Free text currently allowed"
- BUT CIVIL_ENGINEERING_DOMAIN_MODEL.md (lines 361-365) shows:
  ```sql
  structure_type VARCHAR(100) CHECK (structure_type IN (
      'manhole', 'inlet', 'outlet', 'junction',
      'catch_basin', 'cleanout', 'valve', 'meter',
      'pump_station', 'tank', 'vault'
  ))
  ```
- Actual schema confirms CHECK constraint exists

**Impact:** Documentation is out-of-date. Developers don't know the current implementation status.

**Status:** ⚠️ **Documentation is incorrect - constraint IS implemented**

**Fix Required:** Update TRUTH_DRIVEN_ARCHITECTURE.md (line 271) to:
```
Status: ✅ Partially implemented - CHECK constraint exists but should be replaced with FK for manageability
```

---

### 3. Horizontal Alignments Missing Z Coordinate (CRITICAL)

**Files:** CIVIL_ENGINEERING_DOMAIN_MODEL.md vs other geometry definitions

**Problem:**
- Line 511 shows:
  ```sql
  geometry geometry(LineString, 2226) NOT NULL,  -- 2D ONLY!
  ```
- All other alignment-related tables use Z-aware geometries:
  - `vertical_profiles.profile_points` (JSONB with elevation)
  - `cross_sections.section_geometry` (LineStringZ)
  - `surface_models.tin_geometry` (TINZ)
  
- Comment says "2D Geometry (horizontal only)" but profiles ARE 3D data

**Impact:** Alignment geometry loses elevation data, breaking:
- Cross-section vertical tie-ins
- Profile visualization
- Cut/fill calculations

**Status:** ❌ **Schema definition is incomplete**

**Fix Required:** Change to:
```sql
geometry geometry(LineStringZ, 2226) NOT NULL,  -- Include elevation
```

---

### 4. BMP Geometry Type Invalid (CRITICAL)

**Files:** CIVIL_ENGINEERING_DOMAIN_MODEL.md, line 460

**Problem:**
```sql
geometry geometry(GeometryZ, 2226) NOT NULL,
```

**Why Invalid:**
- `GeometryZ` is not a valid PostGIS type
- PostGIS doesn't have a generic Z-aware type
- Document says "polygon for area BMPs, point for device BMPs" but uses `GeometryZ`
- Valid options: `PointZ`, `PolygonZ`, or use base types

**Status:** ❌ **SQL is invalid - will not execute**

**Fix Required:**
```sql
-- Option 1: Support both with geometry column type
geometry geometry(Geometry, 2226) NOT NULL,  -- Allow any type

-- Option 2: Separate point/polygon BMPs into different tables
-- For point BMPs:
geometry geometry(PointZ, 2226) NOT NULL,
-- For area BMPs:
geometry geometry(PolygonZ, 2226) NOT NULL,
```

---

## HIGH PRIORITY ISSUES

### 5. Quality Score Calculation Inconsistency (HIGH)

**Files:** DATABASE_ARCHITECTURE_GUIDE.md vs DATA_FLOW_AND_LIFECYCLE.md

**Problem:**
- DATABASE_ARCHITECTURE_GUIDE.md (lines 443-489):
  - Embedding: 40% weight
  - Relationships: 30% weight
  - Completeness: 30% weight
  - **Total: 100%**
  - **Does NOT mention geometry**

- DATA_FLOW_AND_LIFECYCLE.md (lines 434-484):
  - Embedding: 0.3 (30%)
  - Geometry: 0.2 (20%)
  - Relationships: 0.3 (30%)
  - Usage: 0.2 (20%)
  - **Total: 100%**
  - **Does NOT mention completeness**

**Impact:** Developers don't know which formula is authoritative. AI models trained on quality scores get inconsistent data.

**Status:** ⚠️ **Conflicting specifications**

**Resolution Required:**
- Audit actual `calculate_quality_score()` function in codebase
- Document the single authoritative formula
- Update both files to match

---

### 6. Drawing vs Project-Level Import Ambiguity (HIGH)

**Files:** ENTITY_RELATIONSHIP_MODEL.md vs DATA_FLOW_AND_LIFECYCLE.md vs DATABASE_ARCHITECTURE_GUIDE.md

**Problem:**
- ENTITY_RELATIONSHIP_MODEL.md (line 91): "DXF import/export now happens at project level; entities can be imported with drawing_id = NULL"
- But DATABASE_ARCHITECTURE_GUIDE.md (lines 294-298) lists table group "Construction Documents (14 tables)" including sheets, which implies drawing-level organization
- DATA_FLOW_AND_LIFECYCLE.md references both `drawing_entities` table AND `dxf_entity_links` with `project_id`
- Migration file exists: `011_remove_drawing_id_from_layers.sql` (suggests recent change)

**Unclear:**
- Is `drawing_entities` table still in use?
- Are drawings completely replaced by projects?
- What about multi-file projects?

**Status:** ⚠️ **Architectural transition incomplete/undocumented**

**Resolution Required:**
- Clarify: Is drawing-level import deprecated?
- Document the migration path
- Update all docs to use consistent terminology

---

### 7. Entity Type Name Collision (HIGH)

**Files:** ENTITY_RELATIONSHIP_MODEL.md, CIVIL_ENGINEERING_DOMAIN_MODEL.md

**Problem:**
- `standards_entities.entity_type` (e.g., 'layer', 'block', 'survey_point', 'utility_line')
- `cad_entities.entity_type` (e.g., 'LINE', 'POLYLINE', 'ARC', 'CIRCLE')
- `project_context_mappings.source_type` (e.g., 'keynote', 'block', 'detail')

**These are three different entity type systems!**

- Developers may confuse "entity_type" meanings
- Queries joining across tables could get wrong results

**Status:** ⚠️ **Poor naming causing confusion**

**Fix Required:** Rename columns to clarify:
```sql
-- In standards_entities:
standard_entity_type  -- or canonical_entity_type

-- In cad_entities:
dxf_entity_type  -- clarifies it's from DXF

-- In project_context_mappings:
source_standard_type
target_standard_type
```

---

### 8. Survey Point Description Column Naming (HIGH)

**Files:** TRUTH_DRIVEN_ARCHITECTURE.md vs CIVIL_ENGINEERING_DOMAIN_MODEL.md

**Problem:**
- TRUTH_DRIVEN_ARCHITECTURE.md (line 172) refers to: `point_description TEXT`
- CIVIL_ENGINEERING_DOMAIN_MODEL.md (line 73) shows: `description TEXT`

**Unclear:** Is the column named `description` or `point_description`?

**Status:** ⚠️ **Column naming ambiguous in documentation**

**Impact:** New developers might create wrong column names, breaking queries

---

## MEDIUM PRIORITY ISSUES

### 9. Missing Database Table for Entity Registry (MEDIUM)

**Files:** README.md, replit.md, TRUTH_DRIVEN_ARCHITECTURE.md

**Problem:**
- README.md: "Entity Registry System: Core architectural component that maps CAD object type codes (STORM, MH, SURVEY, etc.) to database tables"
- TRUTH_DRIVEN_ARCHITECTURE.md (line 119): "`entity_registry` | Code-based (services/entity_registry.py)"
- replit.md (lines 35, 39): References "Entity Registry"

**Contradiction:**
- Described as "central switchboard" and "database-driven system"
- But actually "Code-based (services/entity_registry.py)" - NOT in database
- Not in 81-table inventory
- Actually a Python service, not a database table

**Status:** ⚠️ **Mischaracterized in documentation**

**Fix Required:** Update to clarify:
- "Entity Registry: Python service (services/entity_registry.py) mapping object codes to database tables"
- OR create actual database table if needed for truth-driven architecture

---

### 10. Relationship Strength Range Inconsistency (MEDIUM)

**Files:** DATABASE_ARCHITECTURE_GUIDE.md vs ENTITY_RELATIONSHIP_MODEL.md

**Problem:**
- DATABASE_ARCHITECTURE_GUIDE.md (line 154): `relationship_strength NUMERIC,` (no range)
- ENTITY_RELATIONSHIP_MODEL.md (line 156): `relationship_strength (0.0 - 1.0)` (implied range)

**Status:** ⚠️ **Range not consistently documented**

**Fix Required:** Specify in both:
```sql
relationship_strength NUMERIC(3,2) CHECK (relationship_strength >= 0.0 AND relationship_strength <= 1.0),
```

---

### 11. Quality Score NUMERIC Type Inconsistency (MEDIUM)

**Files:** Multiple

**Problem:**
- DATABASE_ARCHITECTURE_GUIDE.md (line 343): "0.0 to 1.0" (implies 3,2 precision)
- STANDARDS_CONFORMANCE_PATTERN.md (line 94): `NUMERIC(5,2)` (too large)
- Actual schema shows: `NUMERIC(3,2)` (correct)

**Status:** ⚠️ **Documentation has wrong precision**

**Fix Required:** Update to consistently show:
```sql
quality_score NUMERIC(3,2) CHECK (quality_score >= 0.0 AND quality_score <= 1.0)
```

---

### 12. SRID 0 vs SRID 2226 Usage Undefined (MEDIUM)

**Files:** README.md, all schema docs

**Problem:**
- README.md (line 72): "Spatial: PostGIS with SRID 2226 for GIS and SRID 0 for CAD data"
- **No schema shows SRID 0 usage anywhere**
- All geometries use SRID 2226

**Unclear:**
- When is SRID 0 used?
- Which tables use SRID 0?
- How is coordinate transformation between 0 and 2226 handled?

**Status:** ⚠️ **Stated principle not evident in schema**

**Fix Required:**
- Clarify if SRID 0 is actually used
- If used, document which tables and why
- If not used, remove from README

---

### 13. Conformance vs Standardization Status Ambiguity (MEDIUM)

**Files:** STANDARDS_CONFORMANCE_PATTERN.md

**Problem:**
- Two parallel status systems in `project_{entity_type}` table:
  1. **Conformance Status**: "how much it deviates" (COMPLIANT, MINOR_DEVIATION, MAJOR_DEVIATION, NON_COMPLIANT)
  2. **Standardization Status**: "candidate for standardization" (NOT_NOMINATED, NOMINATED, UNDER_REVIEW, APPROVED, STANDARDIZED, REJECTED, DEFERRED)

**Unclear:**
- How do these interact?
- Can something be "MAJOR_DEVIATION" but "STANDARDIZED"? (Seems contradictory)
- If item is "APPROVED" for standardization, does conformance_status become irrelevant?

**Status:** ⚠️ **Relationship between two status systems unclear**

**Fix Required:** Document state machine showing valid transitions and combinations

---

### 14. Filterable Entity Columns Purpose Ambiguity (MEDIUM)

**Files:** TRUTH_DRIVEN_ARCHITECTURE.md vs replit.md vs codebase usage

**Problem:**
- TRUTH_DRIVEN_ARCHITECTURE.md (line 102): "Metadata field registry | Which fields are filterable per entity type"
- replit.md (line 40, 64): "Truth-Driven Filterable Columns Registry: Reference Data Hub table serving as authoritative source for filterable metadata columns in **Project Relationship Sets**"

**Unclear:**
- Is this table **generic** (any filterable field in system)?
- Or **specific** (only for Project Relationship Sets)?
- Can other features use it?

**Impact:** Affects API design and reusability

**Status:** ⚠️ **Scope and purpose unclear**

---

### 15. 81 Tables vs Actual 69 Tables Count (MEDIUM)

**Files:** README.md vs database/schema/complete_schema.sql

**Problem:**
- README.md (line 131): "Complete schema reference (81 tables)"
- Actual schema file: 69 CREATE TABLE statements
- Missing 12 tables from documented inventory

**Possible explanations:**
- Documentation is aspirational (not yet implemented)
- Tables were consolidated
- Documentation wasn't updated

**Status:** ⚠️ **Count mismatch**

**Resolution Required:**
- Audit actual table count
- Update README with accurate count
- Document which tables are planned vs implemented

---

### 16. Layer Standard FK Requirement Unclear (MEDIUM)

**Files:** ENTITY_RELATIONSHIP_MODEL.md

**Problem:**
```sql
layers
├── layer_id
├── project_id
├── layer_name
├── entity_id
└── layer_standard_id → layer_standards.layer_standard_id
```

**Unclear:**
- Is `layer_standard_id` a required FK or optional?
- Can a layer have a custom name without referencing a standard?
- What if layer_name doesn't match any standard?

**Impact:** Violates truth-driven architecture principle if FK is optional

**Status:** ⚠️ **Relationship constraint not specified**

---

### 17. Check Constraints Listed in Docs But Implementation Status Unclear (MEDIUM)

**Files:** CIVIL_ENGINEERING_DOMAIN_MODEL.md

**Problem:**
- Document shows CHECK constraints on 10+ columns:
  - point_type IN (...)
  - structure_type IN (...)
  - condition_rating BETWEEN 1 AND 5
  - line_type IN (...)
  - bmp_type IN (...)
  - etc.

- But actual implementation may be different (using VARCHAR without FK)
- Need to verify which are actually in schema vs aspirational

**Status:** ⚠️ **CHECK constraint coverage unclear**

---

### 18. Survey Method and Description Standards Implementation Status (MEDIUM)

**Files:** TRUTH_DRIVEN_ARCHITECTURE.md

**Problem:**
- Lines 165-192 detail "Survey Points Violations"
- Claims need for `survey_point_description_standards` and `survey_method_types` tables
- Status listed as "⚠️ Partially implemented"

**Not Clear:**
- What IS implemented?
- What's still needed?
- Are these tables in the actual schema?

**Status:** ⚠️ **Implementation status vague**

---

### 19. Standard Notes Table Missing from Mapping Framework Schema (MEDIUM)

**Files:** STANDARDS_MAPPING_FRAMEWORK.md

**Problem:**
- Document says "Name Mapping Tables (5 Tables)" including "note_name_mappings"
- References "standard_notes" table multiple times
- But never shows the schema for standard_notes
- TRUTH_DRIVEN_ARCHITECTURE.md lists it as CAD vocabulary table

**Impact:** Developer needs to find schema elsewhere

**Status:** ⚠️ **Incomplete documentation**

---

### 20. Embedding Model Version Tracking Columns Unclear (MEDIUM)

**Files:** DATABASE_ARCHITECTURE_GUIDE.md

**Problem:**
- Line 458 shows check: `WHERE entity_id = p_entity_id AND is_current = true`
- But schema definition (lines 100-104) doesn't show `is_current` column:
  ```sql
  CREATE TABLE entity_embeddings (
      entity_id UUID,
      embedding vector(1536),
      model_id UUID
  );
  ```

**Unclear:**
- Is `is_current` actually in the schema?
- How is embedding versioning implemented?
- How are old embeddings soft-deleted?

**Status:** ⚠️ **Schema definition incomplete**

---

## Summary Table: Issues by Severity

| Severity | Count | Categories |
|----------|-------|-----------|
| **Critical** | 4 | FK constraints, geometry types, SQL validity |
| **High** | 8 | Schema conflicts, ambiguities, design issues |
| **Medium** | 8 | Naming, documentation gaps, unclear status |
| **Total** | 20 | |

---

## Terminology Consistency Analysis

### INCONSISTENT TERMS ACROSS DOCUMENTS:

| Term | Usage 1 | Usage 2 | Correct Term? |
|------|---------|---------|--------------|
| drawing_id | DATA_FLOW | Deprecated? | Need clarification |
| entity_type | standards_entities | cad_entities | Add prefix: standard_entity_type, dxf_entity_type |
| material | "field name" | "reference column" | Add FK: REFERENCES material_standards |
| structure_type | "field name" | "truth table" | Implement as FK or check status |
| point_description | Docs | point.description | Clarify actual column name |
| quality_score precision | (3,2) | (5,2) | Use consistent NUMERIC(3,2) |
| relationship_strength | no range | (0-1) | Add explicit CHECK constraint |

---

## SQL Validity Issues

### Valid SQL Found:
✅ Recursive CTEs (DATABASE_ARCHITECTURE_GUIDE.md)  
✅ Vector similarity searches (DATABASE_ARCHITECTURE_GUIDE.md)  
✅ PostGIS spatial operations (all docs)  
✅ JSONB queries (DATA_FLOW_AND_LIFECYCLE.md)  
✅ Materialized views (DATABASE_ARCHITECTURE_GUIDE.md)  

### Invalid SQL Found:
❌ `geometry(GeometryZ, 2226)` - GeometryZ type doesn't exist (CIVIL_ENGINEERING_DOMAIN_MODEL.md, line 460)

---

## Recommendations

### Immediate Actions (This Week)

1. **Fix material_standards FK** (Issue #1)
   - Add FK constraint to utility_lines.material
   - Add FK constraint to utility_structures.material
   - Test for existing non-conforming data

2. **Fix BMP geometry type** (Issue #4)
   - Change `GeometryZ` to `Geometry` or use separate Point/Polygon columns
   - Verify no data breaks on schema change

3. **Update structure_type documentation** (Issue #2)
   - Mark as "Implemented with CHECK constraint" in TRUTH_DRIVEN_ARCHITECTURE.md
   - Note: Future improvement would be to use FK to structure_type_standards

4. **Fix horizontal_alignments geometry** (Issue #3)
   - Change to LineStringZ for elevation support
   - Verify cross-section/profile ties work correctly

### Short-Term (This Month)

5. **Audit quality_score calculation** (Issue #5)
   - Review actual `calculate_quality_score()` implementation
   - Document single authoritative formula
   - Align both docs to implementation

6. **Clarify Drawing vs Project import** (Issue #6)
   - Audit actual codebase to understand current state
   - Document migration path
   - Update all docs with consistent terminology

7. **Rename entity_type columns** (Issue #7)
   - Add database comments explaining usage
   - Update code/queries to use prefixed names where possible

8. **Document Survey Points schema** (Issue #8)
   - Confirm actual column names
   - Update TRUTH_DRIVEN_ARCHITECTURE.md

### Medium-Term (Next Quarter)

9. **Convert Code-Based Entity Registry to Database** (Issue #9)
   - Create actual entity_registry table or clearly document why it's code-based
   - Update documentation to match

10. **Standardize all numeric constraint specifications** (Issues #10, #11)
    - Add CHECK constraints to all specification docs
    - Use consistent precision: NUMERIC(3,2) for scores/strength

11. **Clarify SRID usage** (Issue #12)
    - Document when SRID 0 is used (if at all)
    - Add examples showing coordinate transformation

12. **Document status system state machine** (Issue #13)
    - Create flow diagram for conformance vs standardization status
    - Document valid state transitions

13. **Clarify filterable_entity_columns scope** (Issue #14)
    - Document if this is generic or Project Relationship Sets specific
    - Design for reusability

14. **Account for table count** (Issue #15)
    - Audit actual schema
    - Update README with accurate count
    - Document planned vs implemented tables

15. **Add FK constraint clarity** (Issue #16)
    - Specify if layer_standard_id is required or optional
    - Enforce at database level if required

16. **Verify CHECK constraints** (Issue #17)
    - Audit schema for all stated constraints
    - Update implementation if needed

17. **Clarify survey standards status** (Issue #18)
    - Document what's implemented vs planned
    - Add estimated timeline for missing features

18. **Complete Standards Mapping Framework documentation** (Issue #19)
    - Add standard_notes schema definition
    - Show complete mapping examples

19. **Clarify embedding versioning** (Issue #20)
    - Show complete entity_embeddings schema with is_current column
    - Document version tracking workflow

---

## Next Steps

1. **Create an architecture review checklist** to prevent future inconsistencies
2. **Establish a schema-documentation sync process** (update docs when schema changes)
3. **Add automated validation** of code examples in documentation
4. **Schedule quarterly architecture documentation audit**

---

**Report Status:** Complete  
**Prepared By:** Documentation Audit System  
**Files Analyzed:** 9 (7 architecture docs + 2 overview docs)  
**Issues Categorized:** 20 (4 Critical, 8 High, 8 Medium)
