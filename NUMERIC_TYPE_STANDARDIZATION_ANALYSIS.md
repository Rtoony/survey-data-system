# Numeric Type Standardization Analysis

**Date:** November 18, 2025
**Related:** AUDIT_FIX_CHECKLIST.md - MEDIUM #9-12

---

## Executive Summary

Audit of `quality_score` columns across the database schema revealed **inconsistent numeric precision** that should be standardized. Additionally, **no CHECK constraints** exist to enforce valid ranges.

### Issues Found:
1. **Inconsistent Precision:** 9 tables use NUMERIC(4,3), most others use NUMERIC(3,2)
2. **Missing CHECK Constraints:** No validation that scores stay within 0.0-1.0 range
3. **Default Values:** Inconsistent defaults across tables

---

## Detailed Findings

### 1. Quality Score Column Precision

#### Tables Using NUMERIC(3,2) - CORRECT ✅
**Precision:** 0.00 to 9.99 (supports 0.00-1.00 with 2 decimal places)
**Count:** ~30 tables

Examples:
- `abbreviation_standards.quality_score` - NUMERIC(3,2) DEFAULT 0.0
- `alignment_pis.quality_score` - NUMERIC(3,2) DEFAULT 0.0
- `annotation_standards.quality_score` - NUMERIC(3,2) DEFAULT 0.0
- `horizontal_alignments.quality_score` - NUMERIC(3,2) DEFAULT 0.0
- `utility_lines.quality_score` - NUMERIC(3,2) DEFAULT 0.0
- `utility_structures.quality_score` - NUMERIC(3,2) DEFAULT 0.0

#### Tables Using NUMERIC(4,3) - INCONSISTENT ⚠️
**Precision:** 0.000 to 9.999 (supports 0.000-1.000 with 3 decimal places)
**Count:** 9 tables

**List of Inconsistent Tables:**
1. `block_definitions.quality_score` - NUMERIC(4,3)
2. `color_standards.quality_score` - NUMERIC(4,3)
3. `hatch_patterns.quality_score` - NUMERIC(4,3)
4. `layer_standards.quality_score` - NUMERIC(4,3)
5. `linetypes.quality_score` - NUMERIC(4,3)
6. `standards_entities.quality_score` - NUMERIC(4,3)
7. `plot_styles.quality_score` - NUMERIC(4,3)
8. `projects.quality_score` - NUMERIC(4,3)
9. `text_styles.quality_score` - NUMERIC(4,3)

**Analysis:**
- Most of these are **standards/style tables** (7 of 9)
- `standards_entities` is the unified entity registry (critical)
- `projects` is the project-level quality score

---

### 2. Confidence Score Column

#### Entity Relationships Table
**Column:** `entity_relationships.confidence_score`
**Type:** NUMERIC(4,3) DEFAULT 1.0
**Purpose:** AI confidence in relationship detection
**Range:** 0.000 to 1.000
**Status:** ✅ Correct precision for confidence scores

---

### 3. CHECK Constraint Status

**Finding:** **NO CHECK constraints exist** on any quality_score or confidence_score columns

**Impact:**
- Data can have values outside valid range (e.g., -1.0, 2.5)
- No database-level validation of score integrity
- Application code must handle validation (brittle)

**Examples of Missing Constraints:**
```sql
-- None of these exist:
ALTER TABLE utility_lines ADD CONSTRAINT chk_quality_score
  CHECK (quality_score >= 0.0 AND quality_score <= 1.0);

ALTER TABLE entity_relationships ADD CONSTRAINT chk_confidence_score
  CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0);
```

---

## Analysis & Recommendations

### Question: Why Two Different Precisions?

**Hypothesis 1: Historical Evolution**
- Early tables (standards) used NUMERIC(4,3) for more precision
- Later tables standardized on NUMERIC(3,2) for simplicity
- Not a deliberate design choice

**Hypothesis 2: Different Requirements**
- Standards/styles might need 3 decimal places (0.000-1.000)
- Entity-level data only needs 2 decimal places (0.00-1.00)
- However, no documentation supports this distinction

**Hypothesis 3: Copy-Paste Inconsistency**
- Most likely cause: schema evolved without strict standards
- Developers used different templates

### Recommended Standard

**For Quality Scores (0.0-1.0 range):**
- **Recommended:** NUMERIC(3,2)
- **Rationale:**
  - Sufficient precision for quality metrics (0.00, 0.25, 0.50, 0.75, 1.00)
  - Consistent with compute_quality_score() function output
  - Smaller storage footprint
  - Majority of tables already use this

**For Confidence Scores (0.0-1.0 range):**
- **Recommended:** NUMERIC(3,2) OR keep NUMERIC(4,3)
- **Rationale:**
  - AI confidence might benefit from extra precision
  - Current NUMERIC(4,3) is acceptable
  - Consider keeping if ML models output high-precision scores

---

## Migration Strategy

### Option 1: Full Standardization (Recommended)
**Goal:** All quality_score columns → NUMERIC(3,2) with CHECK constraints

**Pros:**
- Complete consistency
- Easier maintenance
- Clear standard for future tables

**Cons:**
- Requires data migration for 9 tables
- Slight precision loss (0.001 → 0.01 granularity)
- Must verify no data has >2 decimal places

### Option 2: Two-Tier Standard
**Goal:**
- Standards tables → NUMERIC(4,3) (higher precision)
- Entity tables → NUMERIC(3,2) (standard precision)

**Pros:**
- Preserves potential precision requirements
- Formalizes existing pattern

**Cons:**
- Maintains inconsistency
- Requires documentation of the distinction
- More complex migration

### Option 3: Status Quo + CHECK Constraints Only
**Goal:** Add CHECK constraints but leave precision as-is

**Pros:**
- No data migration needed
- Minimal risk
- Still improves data integrity

**Cons:**
- Doesn't address inconsistency
- Future confusion remains

---

## Proposed Migration (Option 1)

### Phase 1: Add CHECK Constraints
**Priority:** HIGH
**Risk:** LOW

```sql
-- Add CHECK constraints to all quality_score columns
DO $$
DECLARE
    table_rec RECORD;
BEGIN
    FOR table_rec IN
        SELECT table_name
        FROM information_schema.columns
        WHERE column_name = 'quality_score'
        AND table_schema = 'public'
    LOOP
        EXECUTE format(
            'ALTER TABLE %I ADD CONSTRAINT chk_%I_quality_score
             CHECK (quality_score IS NULL OR (quality_score >= 0.0 AND quality_score <= 1.0))',
            table_rec.table_name,
            table_rec.table_name
        );
    END LOOP;
END $$;

-- Add CHECK constraint to confidence_score
ALTER TABLE entity_relationships
ADD CONSTRAINT chk_confidence_score
CHECK (confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0));
```

### Phase 2: Standardize Precision (Optional)
**Priority:** MEDIUM
**Risk:** MEDIUM

```sql
-- Verify no data will be truncated
SELECT
    'block_definitions' as table_name,
    COUNT(*) as rows_affected
FROM block_definitions
WHERE quality_score IS NOT NULL
AND quality_score != ROUND(quality_score, 2)

UNION ALL

SELECT 'color_standards', COUNT(*)
FROM color_standards
WHERE quality_score IS NOT NULL
AND quality_score != ROUND(quality_score, 2)

-- ... repeat for all 9 tables

-- If no rows affected, proceed with type change
ALTER TABLE block_definitions ALTER COLUMN quality_score TYPE NUMERIC(3,2);
ALTER TABLE color_standards ALTER COLUMN quality_score TYPE NUMERIC(3,2);
ALTER TABLE hatch_patterns ALTER COLUMN quality_score TYPE NUMERIC(3,2);
ALTER TABLE layer_standards ALTER COLUMN quality_score TYPE NUMERIC(3,2);
ALTER TABLE linetypes ALTER COLUMN quality_score TYPE NUMERIC(3,2);
ALTER TABLE standards_entities ALTER COLUMN quality_score TYPE NUMERIC(3,2);
ALTER TABLE plot_styles ALTER COLUMN quality_score TYPE NUMERIC(3,2);
ALTER TABLE projects ALTER COLUMN quality_score TYPE NUMERIC(3,2);
ALTER TABLE text_styles ALTER COLUMN quality_score TYPE NUMERIC(3,2);
```

---

## Impact Assessment

### Storage Impact
**Current:**
- NUMERIC(4,3): ~6-8 bytes per value
- NUMERIC(3,2): ~4-6 bytes per value
- Savings: ~2 bytes per value across 9 tables

**Estimated Total Savings:**
- Assuming 1,000 rows across affected tables
- 1,000 × 2 bytes = 2 KB (negligible)

### Performance Impact
**Query Performance:** No significant impact
**Index Impact:** Slightly smaller indexes (negligible)
**Application Impact:** None (values still in 0.0-1.0 range)

### Risk Assessment
**Data Loss Risk:** LOW (if verification query shows no truncation)
**Application Break Risk:** VERY LOW (precision reduction, not range change)
**Migration Rollback:** EASY (reverse ALTER TYPE statements)

---

## Recommendations

### Immediate Actions (High Priority):
1. ✅ **Add CHECK constraints** (Migration Phase 1)
   - No data migration needed
   - Prevents future data integrity issues
   - Low risk, high value

2. ✅ **Document the standard** in schema comments
   - Add COMMENT ON COLUMN for all quality_score columns
   - Clarify that range is 0.0-1.0

### Follow-up Actions (Medium Priority):
3. ⚠️ **Standardize precision** (Migration Phase 2)
   - Only if verification shows no data truncation
   - Consider team input on whether extra precision is needed
   - Can be deferred if deemed not critical

4. ✅ **Update documentation**
   - Add quality_score standard to DATABASE_ARCHITECTURE_GUIDE.md
   - Document precision choice and rationale

### Future Prevention:
5. ✅ **Schema standards document**
   - Create SCHEMA_STANDARDS.md with common column types
   - Include quality_score, confidence_score, timestamps, IDs, etc.
   - Reference during code reviews

---

## Tables Requiring Standardization

### High Priority (Standards Registry):
- `standards_entities.quality_score` - Most important (unified registry)
- `layer_standards.quality_score` - Frequently used

### Medium Priority (Standards Tables):
- `block_definitions.quality_score`
- `color_standards.quality_score`
- `hatch_patterns.quality_score`
- `linetypes.quality_score`
- `plot_styles.quality_score`
- `text_styles.quality_score`

### Special Consideration:
- `projects.quality_score` - Project-level aggregate score
  - Consider keeping NUMERIC(4,3) if calculated from high-precision sources
  - Or standardize to NUMERIC(3,2) for consistency

---

## Conclusion

**Current State:**
- Inconsistent precision across 9 tables
- No CHECK constraints on any quality scores
- Data integrity relies on application validation

**Recommended State:**
- CHECK constraints on all quality_score and confidence_score columns (Phase 1)
- Consider standardizing to NUMERIC(3,2) after verification (Phase 2)
- Document the standard for future schema changes

**Priority:**
- Phase 1 (CHECK constraints): **HIGH - Implement immediately**
- Phase 2 (Precision standardization): **MEDIUM - Implement after review**

---

**Prepared By:** Claude Code Agent
**Analysis Date:** November 18, 2025
**Related Migration:** 025_standardize_numeric_types.sql (to be created)
