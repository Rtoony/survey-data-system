# ACAD-GIS Architecture Audit - Fix Checklist

**Status:** Ready for implementation  
**Priority Order:** Critical first, then High, then Medium  
**Estimated Total Time:** 12-15 hours  

---

## CRITICAL FIXES (Do First - Blocking Issues)

### [CRITICAL #1] Material Standards FK Constraint ⚠️ **PRIORITY 1**

**Issue:** Material columns lack FK constraints, violating truth-driven architecture

**Files to Update:**
- [ ] Add FK to `utility_lines.material` → `material_standards(material_code)`
- [ ] Add FK to `utility_structures.material` → `material_standards(material_code)`
- [ ] Update `CIVIL_ENGINEERING_DOMAIN_MODEL.md` schema examples

**SQL to Apply:**
```sql
-- Check for existing data that won't conform
SELECT DISTINCT material FROM utility_lines 
WHERE material NOT IN (SELECT material_code FROM material_standards);

-- Then add constraint
ALTER TABLE utility_lines 
ADD CONSTRAINT fk_utility_lines_material 
FOREIGN KEY (material) REFERENCES material_standards(material_code);

ALTER TABLE utility_structures 
ADD CONSTRAINT fk_utility_structures_material 
FOREIGN KEY (material) REFERENCES material_standards(material_code);
```

**Verification:**
- [ ] Query returns no results (all values valid)
- [ ] Constraints added successfully
- [ ] Test INSERT with valid material codes succeeds
- [ ] Test INSERT with invalid material codes fails

**Documentation:**
- [ ] Update database schema
- [ ] Update CIVIL_ENGINEERING_DOMAIN_MODEL.md
- [ ] Mark issue as ✅ FIXED in TRUTH_DRIVEN_ARCHITECTURE.md

**Estimated Time:** 2 hours

---

### [CRITICAL #2] BMP Geometry Type - Invalid PostGIS Type ⚠️ **PRIORITY 1**

**Issue:** `geometry(GeometryZ, 2226)` is not a valid PostGIS type

**Files to Update:**
- [ ] Update `CIVIL_ENGINEERING_DOMAIN_MODEL.md` schema (line 460)
- [ ] Run migration to fix actual schema

**Options:**

**Option A: Support both Point and Polygon (recommended)**
```sql
-- Create separate columns or accept generic Geometry
ALTER TABLE bmps ALTER COLUMN geometry TYPE geometry(Geometry, 2226);
```

**Option B: Enforce Point BMPs only**
```sql
ALTER TABLE bmps ALTER COLUMN geometry TYPE geometry(PointZ, 2226);
```

**Option C: Separate tables**
```sql
-- For point BMPs:
CREATE TABLE point_bmps (..., geometry geometry(PointZ, 2226));
-- For area BMPs:
CREATE TABLE area_bmps (..., geometry geometry(PolygonZ, 2226));
```

**Verification:**
- [ ] Existing BMP data still loads
- [ ] CREATE TABLE statement with new type succeeds
- [ ] INSERT operations work
- [ ] Query examples in docs return results

**Documentation:**
- [ ] Update CIVIL_ENGINEERING_DOMAIN_MODEL.md with correct type
- [ ] Document decision (which option was chosen and why)
- [ ] Update any related queries in documentation

**Estimated Time:** 1 hour

---

### [CRITICAL #3] Horizontal Alignments Missing Z Coordinate ⚠️ **PRIORITY 1**

**Issue:** Alignments should be LineStringZ, not LineString (2D only)

**Files to Update:**
- [ ] Update `CIVIL_ENGINEERING_DOMAIN_MODEL.md` (line 511)
- [ ] Run schema migration
- [ ] Verify cross-section/profile relationships work

**SQL to Apply:**
```sql
-- Add Z-coordinates if data exists
-- First check existing data
SELECT ST_GeometryType(geometry) FROM horizontal_alignments LIMIT 5;

-- Update existing data with Z values from profiles
-- (Or re-import with 3D coordinates)

-- Then change type
ALTER TABLE horizontal_alignments 
ALTER COLUMN geometry TYPE geometry(LineStringZ, 2226);
```

**Verification:**
- [ ] Existing alignment data loads with Z values
- [ ] Cross-sections tie in correctly to alignments
- [ ] Vertical profile queries work
- [ ] Cut/fill calculations based on profiles/alignments work

**Documentation:**
- [ ] Update CIVIL_ENGINEERING_DOMAIN_MODEL.md
- [ ] Update any related workflow documentation
- [ ] Document why Z is needed (elevation data)

**Estimated Time:** 2 hours

---

### [CRITICAL #4] Structure Type Status - Documentation Out of Sync ⚠️ **PRIORITY 1**

**Issue:** Status says "Not Implemented" but CHECK constraint actually exists

**Files to Update:**
- [ ] Update `TRUTH_DRIVEN_ARCHITECTURE.md` line 271
- [ ] Verify actual CHECK constraint in schema
- [ ] Note future improvement: Convert to FK for manageability

**Changes:**

**Current (line 271):**
```
Status: ⚠️ **Not implemented** - Free text currently allowed
```

**Should be:**
```
Status: ✅ Partially Implemented - CHECK constraint exists on utility_structures.structure_type
Future: Replace CHECK constraint with FK to structure_type_standards table for better manageability
```

**Verification:**
- [ ] Verify CHECK constraint exists in schema
- [ ] Confirm list of allowed values matches documentation
- [ ] Test INSERT with invalid structure_type fails

**Documentation:**
- [ ] Update TRUTH_DRIVEN_ARCHITECTURE.md
- [ ] Add note about future improvement (FK migration)
- [ ] Document the allowed values

**Estimated Time:** 30 minutes

---

## HIGH PRIORITY FIXES

### [HIGH #5] Quality Score Calculation Inconsistency ⚠️ **PRIORITY 2**

**Issue:** Two different formulas in DATABASE_ARCHITECTURE_GUIDE.md vs DATA_FLOW_AND_LIFECYCLE.md

**Investigation Required:**
- [ ] Locate actual `calculate_quality_score()` function in codebase
- [ ] Determine which formula is actually being used
- [ ] Check if tests specify the formula
- [ ] Look for any config files with weights

**Determine Authoritative Formula:**

**Formula A** (DATABASE_ARCHITECTURE_GUIDE.md):
- Embedding: 40%
- Relationships: 30%
- Completeness: 30%

**Formula B** (DATA_FLOW_AND_LIFECYCLE.md):
- Embedding: 30%
- Geometry: 20%
- Relationships: 30%
- Usage: 20%

**Resolution:**
- [ ] Pick the correct formula (likely Formula B based on actual code)
- [ ] Update DATABASE_ARCHITECTURE_GUIDE.md to match
- [ ] Document why formula was chosen
- [ ] Update any code comments to match docs

**Verification:**
- [ ] Both docs show same formula
- [ ] Code implements documented formula
- [ ] Tests validate formula weights
- [ ] Quality scores make sense in system

**Documentation:**
- [ ] Update both architecture docs
- [ ] Add comment in code showing formula
- [ ] Document weight rationale

**Estimated Time:** 3 hours (1 hour audit + 2 hours documentation)

---

### [HIGH #6] Drawing vs Project-Level Import Status ⚠️ **PRIORITY 2**

**Issue:** Architectural transition from drawing-level to project-level import not clearly documented

**Investigation Required:**
- [ ] Check migration files to understand transition
- [ ] Look for drawing_id references in codebase
- [ ] Determine if drawing_entities table is still used
- [ ] Check if old drawing-based workflow is deprecated

**Files to Review:**
- `011_remove_drawing_id_from_layers.sql` - Explains transition
- `DATA_FLOW_AND_LIFECYCLE.md` - References both systems
- `ENTITY_RELATIONSHIP_MODEL.md` - Says project-level now

**Resolution:**
- [ ] Audit codebase for drawing_id usage
- [ ] Confirm if drawing_entities table still used
- [ ] Document deprecation timeline (if applicable)
- [ ] Update all docs to use consistent terminology

**Clarifications Needed:**
- [ ] Is drawing_entities table still in schema?
- [ ] Can drawings still be imported separately?
- [ ] How do multi-file projects work?
- [ ] What's the migration path for existing drawing-based projects?

**Verification:**
- [ ] All docs use consistent terminology
- [ ] No references to deprecated drawing workflow
- [ ] If drawing_entities exists, document its role clearly
- [ ] Migration path documented for existing projects

**Documentation:**
- [ ] Update ENTITY_RELATIONSHIP_MODEL.md
- [ ] Update DATA_FLOW_AND_LIFECYCLE.md
- [ ] Add migration guide if needed
- [ ] Document project-level import workflow clearly

**Estimated Time:** 2-3 hours (audit + documentation)

---

### [HIGH #7] Entity Type Name Collision ⚠️ **PRIORITY 2**

**Issue:** Three different "entity_type" meanings cause confusion

**Current Situation:**
1. `standards_entities.entity_type` → 'layer', 'block', 'survey_point', etc.
2. `cad_entities.entity_type` → 'LINE', 'POLYLINE', 'ARC', 'CIRCLE'
3. `project_context_mappings.source_type` → 'keynote', 'block', 'detail'

**Proposed Fix:**
- Rename to clarify intent:
  1. `standard_entity_type` (in standards_entities)
  2. `dxf_entity_type` (in cad_entities)
  3. `source_standard_type` (in project_context_mappings)

**Implementation Steps:**
- [ ] Add new column names to schema
- [ ] Migrate data
- [ ] Update all code/queries
- [ ] Drop old columns
- [ ] Update documentation

**Note:** This is a significant refactoring. Consider whether to implement immediately or defer.

**Short-term Workaround:**
- [ ] Add database comments explaining each entity_type meaning
- [ ] Add prefixes in code: `se_entity_type`, `cad_entity_type`, etc.

**Verification:**
- [ ] No join errors due to ambiguous column names
- [ ] Code clearly documents which entity_type is being used
- [ ] Comments explain the three different systems

**Documentation:**
- [ ] Add schema documentation explaining each type
- [ ] Update all architecture docs with clarified names
- [ ] Add code comments in key query files

**Estimated Time:** 3-5 hours (if full refactoring) or 1 hour (if short-term fix)

---

### [HIGH #8] Survey Point Description Column Naming ⚠️ **PRIORITY 2**

**Issue:** Documentation inconsistent - is column named `description` or `point_description`?

**Investigation Required:**
- [ ] Check actual schema for column name
- [ ] Check codebase for column references
- [ ] Verify with domain model definition

**Expected Result:** Likely `description` is correct

**Verification:**
- [ ] Confirm actual column name in schema
- [ ] Verify it's used consistently in queries
- [ ] Check data types match documentation

**Documentation Update:**
- [ ] Update TRUTH_DRIVEN_ARCHITECTURE.md (line 172)
- [ ] Update CIVIL_ENGINEERING_DOMAIN_MODEL.md if needed
- [ ] Ensure survey import documentation uses correct name

**Estimated Time:** 30 minutes

---

## MEDIUM PRIORITY FIXES

### [MEDIUM #9-12] Numeric Constraints and Type Consistency ⚠️ **PRIORITY 3**

**Issue:** Inconsistent specification of numeric types and precision

**Changes Needed:**

| Field | Current | Should Be | Location |
|-------|---------|-----------|----------|
| quality_score | varies | NUMERIC(3,2) | All docs |
| relationship_strength | unspecified | NUMERIC(3,2) | All docs |
| conformance_status_color | not shown | VARCHAR(7) | STANDARDS_CONFORMANCE_PATTERN.md |

**Fixes:**
- [ ] Update DATABASE_ARCHITECTURE_GUIDE.md schema examples
- [ ] Update ENTITY_RELATIONSHIP_MODEL.md schema examples
- [ ] Update STANDARDS_CONFORMANCE_PATTERN.md (line 94: change to 3,2)
- [ ] Add CHECK constraints to all numeric types

**SQL to Add:**
```sql
ALTER TABLE standards_entities 
ADD CONSTRAINT chk_quality_score 
CHECK (quality_score >= 0.0 AND quality_score <= 1.0);

ALTER TABLE entity_relationships 
ADD CONSTRAINT chk_relationship_strength 
CHECK (relationship_strength >= 0.0 AND relationship_strength <= 1.0);
```

**Estimated Time:** 1 hour

---

### [MEDIUM #13-20] Documentation Gaps and Ambiguities ⚠️ **PRIORITY 3**

#### #13: Entity Registry (Code-based vs Database)
- [ ] Clarify in README.md that entity_registry is Python service, not database table
- [ ] Add link to `services/entity_registry.py` in docs
- [ ] Document if future database table is planned

**Estimated Time:** 30 minutes

#### #14: SRID Usage (0 vs 2226)
- [ ] Audit codebase for SRID 0 usage
- [ ] Clarify if SRID 0 is actually used
- [ ] If used, document which tables and why
- [ ] If not used, remove from README.md line 72

**Estimated Time:** 1 hour

#### #15: Schema Table Count (81 vs 69)
- [ ] Run `grep CREATE TABLE database/schema/complete_schema.sql | wc -l`
- [ ] Count actual vs documented tables
- [ ] Update README.md with correct count
- [ ] Document which tables are planned vs implemented

**Estimated Time:** 1 hour

#### #16-20: Various documentation gaps
- [ ] Clarify layer_standard_id constraint (required vs optional)
- [ ] Document conformance vs standardization status interaction
- [ ] Clarify filterable_entity_columns scope
- [ ] Document survey standards implementation status
- [ ] Add standard_notes schema to STANDARDS_MAPPING_FRAMEWORK.md
- [ ] Clarify embedding version tracking in entity_embeddings

**Estimated Time:** 2-3 hours total

---

## IMPLEMENTATION TIMELINE

### Week 1 (Critical Fixes)
- [ ] Monday: Issue #1 (Material FK) + Issue #4 (BMP Geometry)
- [ ] Tuesday: Issue #3 (Alignments Z) + Issue #2 (Structure Type Docs)
- [ ] Wednesday-Friday: Testing and verification

### Week 2-3 (High Priority Fixes)
- [ ] Issue #5 (Quality Score Audit + Docs)
- [ ] Issue #6 (Drawing vs Project)
- [ ] Issue #7 (Entity Type Collision) - or defer
- [ ] Issue #8 (Survey Point Naming)

### Week 4+ (Medium Priority)
- [ ] Issue #9-12 (Numeric Types)
- [ ] Issue #13-20 (Documentation Gaps)
- [ ] Create architecture review checklist
- [ ] Establish schema-docs sync process

---

## Sign-Off Checklist

When all fixes are complete:

- [ ] All 4 critical issues resolved
- [ ] All 8 high priority issues resolved
- [ ] All 8 medium priority issues resolved
- [ ] Architecture Audit Report marked complete
- [ ] All documentation files reviewed and updated
- [ ] Database schema tested
- [ ] Team trained on new/clarified patterns
- [ ] Quarterly audit process established

---

**Prepared By:** Documentation Audit System  
**Date:** November 17, 2025  
**Checklist Version:** 1.0
