# **Truth-Driven Architecture Migration Plan**

*SQL Migration Scripts & Remediation Procedures*

---

## **Document Purpose**

This document provides the complete SQL migration scripts necessary to remediate all violations of the Truth-Driven Architecture identified in `TRUTH_DRIVEN_ARCHITECTURE.md`. Each migration includes:
- Current schema analysis
- Target schema definition
- Data cleanup queries (fix existing data before FK constraints)
- ALTER TABLE statements (add foreign keys, change column types)
- Validation queries (verify migration success)
- Rollback procedures (if migration fails)

**CRITICAL:** Always test migrations on a development database before running on production.

---

## **Migration Phases**

### **Phase 1: Critical Violations** (Target: Q1 2026)
1. Relationship Set Naming Templates ✅ **COMPLETED**
2. Material Type Enforcement
3. Structure Type Standardization

### **Phase 2: High-Value Improvements** (Target: Q2 2026)
4. Survey Point Descriptions
5. Standard Note Categories

### **Phase 3: Comprehensive Coverage** (Target: Q3-Q4 2026)
6. Equipment/Asset Types (future feature)
7. Custom Attribute Vocabulary
8. DXF Classification Lock-Down

---

## **Phase 1, Migration 1: Relationship Set Naming Templates**

### **Status:** ✅ COMPLETED (November 15, 2025)

### **Summary**
Created `relationship_set_naming_templates` table to enforce truth-driven naming for Project Relationship Sets.

### **Deployed Scripts**
- `database/create_relationship_set_naming_templates.sql` ✅ Executed
- `database/seed_relationship_set_naming_templates.sql` ✅ Executed

### **Validation**
```sql
-- Verify table exists
SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'relationship_set_naming_templates'
ORDER BY ordinal_position;

-- Verify seed data (should return 10 rows)
SELECT COUNT(*) as template_count, COUNT(DISTINCT category) as category_count
FROM relationship_set_naming_templates
WHERE is_active = TRUE;

-- Expected: template_count = 10, category_count = 8
```

### **Next Step**
Update `templates/project_relationship_sets.html` to use templates instead of free-text inputs (Task 5 & 6).

---

## **Phase 1, Migration 2: Material Type Enforcement**

### **Status:** ⚠️ NOT STARTED

### **Problem**
Multiple tables allow free-text material entry, causing inconsistency:
- `utility_lines.material` (VARCHAR, no FK)
- `utility_structures.material_type` (VARCHAR, no FK)
- Other asset tables with material columns

**Impact:**
- Same material entered differently: "PVC" vs "pvc" vs "P.V.C."
- Compliance rules fail
- Cost estimation breaks
- Detail cross-references fail

---

### **Current Schema Analysis**

```sql
-- Check current material columns
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE column_name LIKE '%material%'
    AND table_name IN ('utility_lines', 'utility_structures', 'bmps')
ORDER BY table_name, ordinal_position;
```

**Expected Results:**
```
table_name         | column_name    | data_type         | is_nullable
-------------------|----------------|-------------------|-------------
utility_lines      | material       | character varying | YES
utility_structures | material_type  | character varying | YES
```

---

### **Data Cleanup Queries**

**Step 1: Analyze existing material values**
```sql
-- Find all unique material values in utility_lines
SELECT DISTINCT material, COUNT(*) as usage_count
FROM utility_lines
WHERE material IS NOT NULL
GROUP BY material
ORDER BY usage_count DESC;

-- Find all unique material_type values in utility_structures
SELECT DISTINCT material_type, COUNT(*) as usage_count
FROM utility_structures
WHERE material_type IS NOT NULL
GROUP BY material_type
ORDER BY usage_count DESC;
```

**Step 2: Map free-text values to standard material codes**
```sql
-- Create temporary mapping table
CREATE TEMP TABLE material_migration_map (
    old_value VARCHAR(200),
    new_value VARCHAR(50),  -- References material_standards.material_code
    table_name VARCHAR(100)
);

-- Example mappings (customize based on your data)
INSERT INTO material_migration_map (old_value, new_value, table_name) VALUES
('PVC', 'PVC-SDR35', 'utility_lines'),
('pvc', 'PVC-SDR35', 'utility_lines'),
('P.V.C.', 'PVC-SDR35', 'utility_lines'),
('Polyvinyl Chloride', 'PVC-SDR35', 'utility_lines'),
('HDPE', 'HDPE-DR17', 'utility_lines'),
('hdpe', 'HDPE-DR17', 'utility_lines'),
('RCP', 'RCP-CLASS3', 'utility_lines'),
('Reinforced Concrete', 'RCP-CLASS3', 'utility_lines'),
('DI', 'DI-C900', 'utility_lines'),
('Ductile Iron', 'DI-C900', 'utility_lines'),
('Cast Iron', 'CI-CLASS50', 'utility_lines'),
('CI', 'CI-CLASS50', 'utility_lines'),
('UNKNOWN', NULL, 'utility_lines'),  -- Set to NULL for missing data
('', NULL, 'utility_lines');

-- Repeat for utility_structures
INSERT INTO material_migration_map (old_value, new_value, table_name) VALUES
('Precast Concrete', 'CONC-PRECAST', 'utility_structures'),
('Concrete', 'CONC-PRECAST', 'utility_structures'),
('Polymer', 'POLY-COMPOSITE', 'utility_structures'),
('HDPE', 'HDPE-DR17', 'utility_structures'),
('PVC', 'PVC-SDR35', 'utility_structures');
```

**Step 3: Apply material code standardization**
```sql
-- Update utility_lines materials
UPDATE utility_lines ul
SET material = mm.new_value
FROM material_migration_map mm
WHERE mm.table_name = 'utility_lines'
    AND ul.material = mm.old_value;

-- Update utility_structures materials
UPDATE utility_structures us
SET material_type = mm.new_value
FROM material_migration_map mm
WHERE mm.table_name = 'utility_structures'
    AND us.material_type = mm.old_value;
```

**Step 4: Identify orphan values (not in mapping)**
```sql
-- Find utility_lines materials not in mapping
SELECT DISTINCT ul.material, COUNT(*) as count
FROM utility_lines ul
LEFT JOIN material_migration_map mm 
    ON ul.material = mm.old_value AND mm.table_name = 'utility_lines'
WHERE ul.material IS NOT NULL
    AND mm.old_value IS NULL
GROUP BY ul.material
ORDER BY count DESC;

-- Manual intervention required for these values
-- Either add to mapping or set to NULL
```

**Step 5: Verify material_standards table has all referenced codes**
```sql
-- Check for materials referenced but not in material_standards
SELECT DISTINCT ul.material
FROM utility_lines ul
LEFT JOIN material_standards ms ON ul.material = ms.material_code
WHERE ul.material IS NOT NULL
    AND ms.material_code IS NULL;

-- If any results, add missing materials to material_standards first
```

---

### **Schema Migration**

**Step 1: Add new FK-constrained columns**
```sql
-- Add new column to utility_lines (nullable initially)
ALTER TABLE utility_lines 
ADD COLUMN material_code VARCHAR(50) REFERENCES material_standards(material_code);

-- Add new column to utility_structures (nullable initially)
ALTER TABLE utility_structures 
ADD COLUMN material_code VARCHAR(50) REFERENCES material_standards(material_code);

-- Copy cleaned data to new columns
UPDATE utility_lines SET material_code = material;
UPDATE utility_structures SET material_code = material_type;
```

**Step 2: Rename columns (swap old for new)**
```sql
-- utility_lines
ALTER TABLE utility_lines RENAME COLUMN material TO material_legacy;
ALTER TABLE utility_lines RENAME COLUMN material_code TO material;

-- utility_structures  
ALTER TABLE utility_structures RENAME COLUMN material_type TO material_type_legacy;
ALTER TABLE utility_structures RENAME COLUMN material_code TO material_type;
```

**Step 3: Mark legacy columns for future removal (after verification period)**
```sql
COMMENT ON COLUMN utility_lines.material_legacy IS 'DEPRECATED - Migration backup, remove after Q2 2026';
COMMENT ON COLUMN utility_structures.material_type_legacy IS 'DEPRECATED - Migration backup, remove after Q2 2026';
```

---

### **Validation Queries**

```sql
-- Verify FK constraints exist
SELECT 
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_name IN ('utility_lines', 'utility_structures')
    AND kcu.column_name LIKE '%material%';

-- Verify no NULL materials where data existed before
SELECT 
    'utility_lines' as table_name,
    COUNT(*) FILTER (WHERE material IS NULL AND material_legacy IS NOT NULL) as null_after_migration
FROM utility_lines
UNION ALL
SELECT 
    'utility_structures',
    COUNT(*) FILTER (WHERE material_type IS NULL AND material_type_legacy IS NOT NULL)
FROM utility_structures;

-- Expected: null_after_migration = 0 for both tables

-- Verify all materials reference valid material_standards
SELECT table_name, material_value, COUNT(*) as invalid_count
FROM (
    SELECT 'utility_lines' as table_name, material as material_value
    FROM utility_lines
    WHERE material IS NOT NULL
        AND NOT EXISTS (
            SELECT 1 FROM material_standards ms 
            WHERE ms.material_code = utility_lines.material
        )
    UNION ALL
    SELECT 'utility_structures', material_type
    FROM utility_structures
    WHERE material_type IS NOT NULL
        AND NOT EXISTS (
            SELECT 1 FROM material_standards ms 
            WHERE ms.material_code = utility_structures.material_type
        )
) invalid_materials
GROUP BY table_name, material_value;

-- Expected: 0 rows (all materials valid)
```

---

### **Rollback Procedure**

If migration fails or data corruption occurs:

```sql
-- ROLLBACK STEP 1: Restore original columns
ALTER TABLE utility_lines RENAME COLUMN material TO material_failed;
ALTER TABLE utility_lines RENAME COLUMN material_legacy TO material;
ALTER TABLE utility_lines DROP COLUMN material_failed;

ALTER TABLE utility_structures RENAME COLUMN material_type TO material_type_failed;
ALTER TABLE utility_structures RENAME COLUMN material_type_legacy TO material_type;
ALTER TABLE utility_structures DROP COLUMN material_type_failed;

-- ROLLBACK STEP 2: Verify restoration
SELECT COUNT(*) as restored_count
FROM utility_lines
WHERE material IS NOT NULL;

-- Expected: Same count as before migration
```

---

## **Phase 1, Migration 3: Structure Type Standardization**

### **Status:** ⚠️ NOT STARTED

### **Problem**
`utility_structures.structure_type` allows free text, causing inconsistent naming:
- "Manhole" vs "MH" vs "manhole" vs "Man Hole"
- Prevents type-specific tool auto-launch
- Breaks inventory reports

**Impact:**
- Type-specific tools can't auto-launch ("If type = MH, open Manhole Inspector")
- Inventory/compliance reports unreliable
- Standards enforcement fails

---

### **Current Schema Analysis**

```sql
-- Check structure_type column
SELECT 
    data_type,
    is_nullable,
    character_maximum_length
FROM information_schema.columns
WHERE table_name = 'utility_structures'
    AND column_name = 'structure_type';

-- Analyze existing values
SELECT structure_type, COUNT(*) as usage_count
FROM utility_structures
WHERE structure_type IS NOT NULL
GROUP BY structure_type
ORDER BY usage_count DESC;
```

---

### **Target Schema: Create structure_type_standards Table**

```sql
-- Create controlled vocabulary table
CREATE TABLE IF NOT EXISTS structure_type_standards (
    type_code VARCHAR(20) PRIMARY KEY,
    type_name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL,
    icon VARCHAR(50),
    specialized_tool_id VARCHAR(100),  -- Links to specialized_tools_registry
    required_attributes JSONB,
    description TEXT,
    usage_instructions TEXT,
    
    -- Status
    is_active BOOLEAN NOT NULL DEFAULT true,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_structure_types_category 
    ON structure_type_standards(category) 
    WHERE is_active = true;

-- Comments
COMMENT ON TABLE structure_type_standards IS 'Controlled vocabulary for utility structure types - enforces truth-driven naming';
COMMENT ON COLUMN structure_type_standards.type_code IS 'Short code (e.g., MH, CB, INLET)';
COMMENT ON COLUMN structure_type_standards.type_name IS 'Full name (e.g., Manhole, Catch Basin)';
COMMENT ON COLUMN structure_type_standards.specialized_tool_id IS 'Optional link to specialized management tool';
```

---

### **Seed Data: Standard Structure Types**

```sql
INSERT INTO structure_type_standards 
(type_code, type_name, category, icon, description, required_attributes)
VALUES
('MH', 'Manhole', 'Sanitary Sewer', 'fa-circle', 'Standard manhole structure', 
 '["diameter", "rim_elevation", "invert_elevation"]'::jsonb),
 
('CB', 'Catch Basin', 'Storm Drainage', 'fa-square', 'Catch basin for surface drainage',
 '["grate_type", "sump_depth", "rim_elevation"]'::jsonb),
 
('INLET', 'Inlet', 'Storm Drainage', 'fa-inbox', 'Storm drain inlet structure',
 '["inlet_type", "rim_elevation", "grate_size"]'::jsonb),
 
('CLNOUT', 'Cleanout', 'Sanitary Sewer', 'fa-dot-circle', 'Sewer cleanout access point',
 '["diameter", "rim_elevation"]'::jsonb),
 
('VALVE', 'Valve', 'Water System', 'fa-circle-notch', 'Water system valve',
 '["valve_type", "valve_size", "operating_nut"]'::jsonb),
 
('METER', 'Meter', 'Water System', 'fa-tachometer-alt', 'Water meter',
 '["meter_size", "meter_type"]'::jsonb),
 
('HYDRA', 'Fire Hydrant', 'Water System', 'fa-fire-extinguisher', 'Fire hydrant',
 '["hydrant_type", "nozzle_configuration"]'::jsonb),
 
('PUMP', 'Pump Station', 'Utilities', 'fa-cog', 'Pump station structure',
 '["pump_capacity", "wet_well_depth", "controls"]'::jsonb),
 
('JBOX', 'Junction Box', 'Electrical', 'fa-box', 'Utility junction box',
 '["box_size", "utility_type"]'::jsonb),
 
('VAULT', 'Vault', 'Utilities', 'fa-cube', 'Underground utility vault',
 '["vault_type", "dimensions"]'::jsonb);
```

---

### **Data Cleanup Queries**

**Step 1: Create mapping for existing values**
```sql
CREATE TEMP TABLE structure_type_migration_map (
    old_value VARCHAR(100),
    new_type_code VARCHAR(20)
);

-- Map common variations to standard codes
INSERT INTO structure_type_migration_map (old_value, new_type_code) VALUES
('Manhole', 'MH'),
('MH', 'MH'),
('manhole', 'MH'),
('Man Hole', 'MH'),
('Catch Basin', 'CB'),
('CB', 'CB'),
('catch basin', 'CB'),
('CatchBasin', 'CB'),
('Inlet', 'INLET'),
('inlet', 'INLET'),
('Storm Inlet', 'INLET'),
('Cleanout', 'CLNOUT'),
('Clean Out', 'CLNOUT'),
('CLNOUT', 'CLNOUT'),
('Valve', 'VALVE'),
('valve', 'VALVE'),
('Gate Valve', 'VALVE'),
('Meter', 'METER'),
('Water Meter', 'METER'),
('Hydrant', 'HYDRA'),
('Fire Hydrant', 'HYDRA'),
('HYDRA', 'HYDRA'),
('Pump', 'PUMP'),
('Pump Station', 'PUMP'),
('Junction Box', 'JBOX'),
('JBOX', 'JBOX'),
('Vault', 'VAULT'),
('UNKNOWN', NULL),
('', NULL);

-- Identify unmapped values
SELECT DISTINCT us.structure_type, COUNT(*) as count
FROM utility_structures us
LEFT JOIN structure_type_migration_map mm ON us.structure_type = mm.old_value
WHERE us.structure_type IS NOT NULL
    AND mm.old_value IS NULL
GROUP BY us.structure_type
ORDER BY count DESC;

-- Manual intervention: Add mappings for unmapped values or set to NULL
```

---

### **Schema Migration**

```sql
-- Step 1: Add new FK-constrained column
ALTER TABLE utility_structures 
ADD COLUMN structure_type_code VARCHAR(20) 
REFERENCES structure_type_standards(type_code);

-- Step 2: Populate new column using mapping
UPDATE utility_structures us
SET structure_type_code = mm.new_type_code
FROM structure_type_migration_map mm
WHERE us.structure_type = mm.old_value;

-- Step 3: Verify no data loss
SELECT 
    COUNT(*) FILTER (WHERE structure_type IS NOT NULL) as original_count,
    COUNT(*) FILTER (WHERE structure_type_code IS NOT NULL) as migrated_count,
    COUNT(*) FILTER (WHERE structure_type IS NOT NULL AND structure_type_code IS NULL) as failed_count
FROM utility_structures;

-- Expected: failed_count = 0 (or only for explicitly NULL mappings like "UNKNOWN")

-- Step 4: Rename columns
ALTER TABLE utility_structures RENAME COLUMN structure_type TO structure_type_legacy;
ALTER TABLE utility_structures RENAME COLUMN structure_type_code TO structure_type;

-- Step 5: Mark legacy column
COMMENT ON COLUMN utility_structures.structure_type_legacy 
IS 'DEPRECATED - Migration backup, remove after Q2 2026';
```

---

### **Validation Queries**

```sql
-- Verify FK constraint
SELECT constraint_name, table_name, column_name
FROM information_schema.key_column_usage
WHERE table_name = 'utility_structures'
    AND column_name = 'structure_type';

-- Verify all structure_types reference valid codes
SELECT COUNT(*) as invalid_count
FROM utility_structures
WHERE structure_type IS NOT NULL
    AND NOT EXISTS (
        SELECT 1 FROM structure_type_standards sts
        WHERE sts.type_code = utility_structures.structure_type
    );

-- Expected: invalid_count = 0

-- Verify distribution
SELECT us.structure_type, sts.type_name, COUNT(*) as count
FROM utility_structures us
JOIN structure_type_standards sts ON us.structure_type = sts.type_code
GROUP BY us.structure_type, sts.type_name
ORDER BY count DESC;
```

---

### **Rollback Procedure**

```sql
-- Restore original column
ALTER TABLE utility_structures RENAME COLUMN structure_type TO structure_type_failed;
ALTER TABLE utility_structures RENAME COLUMN structure_type_legacy TO structure_type;
ALTER TABLE utility_structures DROP COLUMN structure_type_failed;

-- Drop standards table
DROP TABLE IF EXISTS structure_type_standards CASCADE;
```

---

## **Phase 2, Migration 4: Survey Point Descriptions**

### **Status:** ⚠️ NOT STARTED

### **Problem**
`survey_points.point_description` (TEXT) and `survey_points.survey_method` (VARCHAR) allow free text.

**Impact:**
- Descriptions vary: "edge of pavement" vs "EP" vs "edge pavement"
- Methods inconsistent: "GPS" vs "gps" vs "RTK GPS" vs "GNSS"
- Reports unreliable
- AI can't parse semantics

---

### **Target Schema**

**Option A: Use existing survey_code_library**
```sql
-- Link point_description to survey_code_library
ALTER TABLE survey_points
ADD COLUMN survey_code_id UUID REFERENCES survey_code_library(code_id);

-- Populate from existing descriptions
UPDATE survey_points sp
SET survey_code_id = scl.code_id
FROM survey_code_library scl
WHERE sp.point_description ILIKE scl.code || '%'
    OR sp.point_description ILIKE '%' || scl.description || '%';
```

**Option B: Create survey_method_types table**
```sql
CREATE TABLE IF NOT EXISTS survey_method_types (
    method_code VARCHAR(20) PRIMARY KEY,
    method_name VARCHAR(100) NOT NULL UNIQUE,
    accuracy_class VARCHAR(20),  -- e.g., 'SURVEY_GRADE', 'MAPPING_GRADE'
    equipment_type VARCHAR(100),
    typical_precision_horizontal NUMERIC(10,3),  -- in feet
    typical_precision_vertical NUMERIC(10,3),    -- in feet
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Seed data
INSERT INTO survey_method_types 
(method_code, method_name, accuracy_class, equipment_type, typical_precision_horizontal, typical_precision_vertical)
VALUES
('GPS-RTK', 'GPS Real-Time Kinematic', 'SURVEY_GRADE', 'GPS Receiver', 0.02, 0.03),
('GPS-PPK', 'GPS Post-Processed Kinematic', 'SURVEY_GRADE', 'GPS Receiver', 0.03, 0.05),
('GPS-AUTO', 'GPS Autonomous', 'MAPPING_GRADE', 'Handheld GPS', 3.0, 5.0),
('TOTAL-STATION', 'Total Station', 'SURVEY_GRADE', 'Total Station', 0.01, 0.01),
('LEVEL-DIGITAL', 'Digital Level', 'SURVEY_GRADE', 'Digital Level', NULL, 0.01),
('LEVEL-AUTO', 'Automatic Level', 'SURVEY_GRADE', 'Automatic Level', NULL, 0.02),
('LASER-SCAN', 'Laser Scanner', 'SURVEY_GRADE', 'Laser Scanner', 0.05, 0.05),
('PHOTOGRAMMETRY', 'Aerial Photogrammetry', 'MAPPING_GRADE', 'Drone/Aircraft', 0.5, 1.0),
('TABLET-GPS', 'Tablet GPS', 'MAPPING_GRADE', 'Tablet', 5.0, 10.0);
```

---

### **Migration Script (Survey Methods)**

```sql
-- Add new column
ALTER TABLE survey_points
ADD COLUMN method_code VARCHAR(20) REFERENCES survey_method_types(method_code);

-- Create mapping
CREATE TEMP TABLE survey_method_map (old_value VARCHAR(100), new_code VARCHAR(20));
INSERT INTO survey_method_map VALUES
('GPS', 'GPS-RTK'),
('gps', 'GPS-RTK'),
('RTK', 'GPS-RTK'),
('RTK GPS', 'GPS-RTK'),
('GNSS', 'GPS-RTK'),
('Total Station', 'TOTAL-STATION'),
('TS', 'TOTAL-STATION'),
('Level', 'LEVEL-DIGITAL'),
('Auto Level', 'LEVEL-AUTO'),
('Scanner', 'LASER-SCAN'),
('Drone', 'PHOTOGRAMMETRY');

-- Populate
UPDATE survey_points sp
SET method_code = smm.new_code
FROM survey_method_map smm
WHERE sp.survey_method = smm.old_value;

-- Rename columns
ALTER TABLE survey_points RENAME COLUMN survey_method TO survey_method_legacy;
ALTER TABLE survey_points RENAME COLUMN method_code TO survey_method;
```

---

## **Phase 2, Migration 5: Standard Note Categories**

### **Status:** ⚠️ NOT STARTED

### **Problem**
`standard_notes.note_category` (VARCHAR) and `standard_notes.discipline` (VARCHAR) use free text instead of foreign keys.

**Impact:**
- Categories vary: "General" vs "GENERAL" vs "Gen"
- Disciplines inconsistent: "Civil" vs "CIV" vs "civil"
- Filtering breaks
- Cross-referencing with layers/blocks fails

---

### **Target Schema**

```sql
-- These tables already exist, just need to link to them
-- discipline_codes (discipline_code, discipline_name)
-- category_codes (category_code, category_name)

-- Add FK columns
ALTER TABLE standard_notes
ADD COLUMN discipline_code_fk VARCHAR(20) REFERENCES discipline_codes(discipline_code);

ALTER TABLE standard_notes
ADD COLUMN category_code_fk VARCHAR(100) REFERENCES category_codes(category_code);
```

---

### **Migration Script**

```sql
-- Map disciplines
UPDATE standard_notes sn
SET discipline_code_fk = dc.discipline_code
FROM discipline_codes dc
WHERE UPPER(sn.discipline) = UPPER(dc.discipline_code)
    OR UPPER(sn.discipline) = UPPER(dc.discipline_name);

-- Map categories
UPDATE standard_notes sn
SET category_code_fk = cc.category_code
FROM category_codes cc
WHERE UPPER(sn.note_category) = UPPER(cc.category_code)
    OR UPPER(sn.note_category) = UPPER(cc.category_name);

-- Identify unmapped
SELECT discipline, COUNT(*) as count
FROM standard_notes
WHERE discipline IS NOT NULL 
    AND discipline_code_fk IS NULL
GROUP BY discipline;

-- Manual mapping required for these

-- Rename columns
ALTER TABLE standard_notes RENAME COLUMN discipline TO discipline_legacy;
ALTER TABLE standard_notes RENAME COLUMN note_category TO note_category_legacy;
ALTER TABLE standard_notes RENAME COLUMN discipline_code_fk TO discipline;
ALTER TABLE standard_notes RENAME COLUMN category_code_fk TO note_category;
```

---

## **Migration Execution Checklist**

For each migration:

- [ ] **1. Backup database**
  ```bash
  pg_dump -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE -F c -f backup_$(date +%Y%m%d_%H%M%S).dump
  ```

- [ ] **2. Run in transaction (development)**
  ```sql
  BEGIN;
  -- Run all migration queries
  -- Run all validation queries
  -- If all pass: COMMIT;
  -- If any fail: ROLLBACK;
  ```

- [ ] **3. Test application functionality**
  - Create/edit records with new constraints
  - Verify dropdowns populate correctly
  - Test reports/queries

- [ ] **4. Monitor for issues (1 week)**
  - Watch for FK violations in logs
  - User feedback on missing options

- [ ] **5. Remove legacy columns (after Q2 2026)**
  ```sql
  ALTER TABLE table_name DROP COLUMN column_name_legacy;
  ```

---

## **Common Migration Patterns**

### **Pattern 1: Free Text → Controlled Vocabulary**

```sql
-- 1. Create standards table
CREATE TABLE {vocabulary}_standards (...);

-- 2. Seed with initial values
INSERT INTO {vocabulary}_standards VALUES (...);

-- 3. Add new FK column to data table
ALTER TABLE {data_table} ADD COLUMN {field}_code VARCHAR(...) 
REFERENCES {vocabulary}_standards({pk_column});

-- 4. Create mapping table
CREATE TEMP TABLE {field}_map (old_value VARCHAR, new_code VARCHAR);

-- 5. Populate mapping
INSERT INTO {field}_map VALUES (...);

-- 6. Migrate data
UPDATE {data_table} dt
SET {field}_code = m.new_code
FROM {field}_map m
WHERE dt.{field} = m.old_value;

-- 7. Verify
SELECT COUNT(*) FROM {data_table} 
WHERE {field} IS NOT NULL AND {field}_code IS NULL;

-- 8. Rename columns
ALTER TABLE {data_table} RENAME COLUMN {field} TO {field}_legacy;
ALTER TABLE {data_table} RENAME COLUMN {field}_code TO {field};
```

### **Pattern 2: VARCHAR → FK to Existing Table**

```sql
-- 1. Add new FK column
ALTER TABLE {data_table} ADD COLUMN {field}_fk VARCHAR(...)
REFERENCES {existing_table}({pk_column});

-- 2. Fuzzy match existing values
UPDATE {data_table} dt
SET {field}_fk = et.{pk_column}
FROM {existing_table} et
WHERE UPPER(dt.{field}) = UPPER(et.{pk_column})
    OR UPPER(dt.{field}) = UPPER(et.{name_column});

-- 3. Manual mapping for remainder
-- (output unmapped values, create manual mapping table, update)

-- 4. Rename columns
ALTER TABLE {data_table} RENAME COLUMN {field} TO {field}_legacy;
ALTER TABLE {data_table} RENAME COLUMN {field}_fk TO {field};
```

---

## **Success Criteria**

Each migration is considered successful when:

✅ **Data Integrity**
- Zero rows lost (original count = migrated count)
- All FK constraints valid
- No NULL values where data existed before

✅ **Application Functionality**
- UI dropdowns populate correctly
- CRUD operations work
- Reports/queries return expected results

✅ **User Experience**
- No complaints about missing options
- Improved consistency in data entry

✅ **Performance**
- No significant query slowdown
- Indexes support FK joins

---

## **Rollback Strategy**

Every migration includes:
1. **Legacy column preservation** - Original data kept for 3 months
2. **Explicit rollback script** - Documented procedure to reverse changes
3. **Validation queries** - Prove migration success before committing
4. **Transaction wrapping** - All changes in single transaction for atomicity

**Emergency Rollback Template:**
```sql
BEGIN;
ALTER TABLE {table} RENAME COLUMN {field} TO {field}_failed;
ALTER TABLE {table} RENAME COLUMN {field}_legacy TO {field};
ALTER TABLE {table} DROP COLUMN {field}_failed;
COMMIT;
```

---

## **Future Enhancements**

### **Automated Migration Testing**
Create migration test framework:
```sql
-- Create test database
CREATE DATABASE migration_test_db;

-- Populate with sample data
-- Run migration scripts
-- Execute validation queries
-- Compare results to expected values

-- Drop test database
DROP DATABASE migration_test_db;
```

### **Migration Monitoring Dashboard**
Track migration progress:
- Percentage of records migrated
- Unmapped values needing manual intervention
- FK violation rates
- User-reported issues

---

**Document Version:** 1.0  
**Last Updated:** November 15, 2025  
**Next Review:** After each phase completion  
**Owner:** System Architecture Team
