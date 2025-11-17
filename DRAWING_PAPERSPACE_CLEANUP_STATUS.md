# Drawing/Paper Space Cleanup - Status Report

**Date:** 2025-11-17
**Branch:** `claude/audit-drawing-paperspace-cleanup-011H72VKRABJ3BKGhNd67fab`

## Executive Summary

This document tracks the progress of migrating from "Projects → Drawings → Entities" architecture to "Projects → Entities" architecture, removing all paper space and legacy drawing references.

## ✅ COMPLETED - Phase 1: Paper Space Removal

### Code Changes Completed
- ✅ **dxf_importer.py**: Removed `import_paperspace` parameter and paper space import logic
  - Deleted `_import_viewports()` function (lines 672-709)
  - Removed paper space import block (lines 101-106)
  - Updated function signature and documentation

- ✅ **dxf_exporter.py**: Removed `include_paperspace` parameter and paper space export logic
  - Deleted `_export_layouts()` function (stub at line 644-647)
  - Removed paper space export block (lines 114-116)
  - Updated function signature and documentation

- ✅ **app.py**: Removed paper space API parameters
  - Line ~10911: Removed `import_paperspace` from DXF import endpoint
  - Line ~10984: Removed `include_paperspace` from DXF export endpoint
  - Line ~11073: Removed `import_paperspace` from reimport endpoint
  - Line ~11172: Removed `import_paperspace=True` from change detection

- ✅ **test_coordinate_preservation.py**: Removed `include_paperspace=False` parameter

- ✅ **scripts/z_stress_harness.py**: Removed paper space parameters from both import and export calls

### SQL Migrations Created
- ✅ **Migration 009**: `database/migrations/009_remove_paperspace_tables.sql`
  - Drops `layout_viewports` table (100% paper space)
  - Drops `drawing_layer_usage` table (unused)
  - Drops `drawing_linetype_usage` table (unused)
  - Includes data validation and verification steps

## ✅ PREPARED - Phase 2: space_type Column Removal

### SQL Migrations Created
- ✅ **Migration 010**: `database/migrations/010_remove_space_type_columns.sql`
  - Validates no PAPER space data exists
  - Removes `space_type` column from `drawing_entities`
  - Removes `space_type` column from `drawing_text`
  - Removes `space_type` column from `drawing_dimensions`
  - Removes `space_type` column from `drawing_hatches`
  - Drops indexes `idx_drawingent_space` and `idx_drawingtext_space`

### Code Changes Needed (NOT YET COMPLETED)
The following files still reference `space_type` and need updates:

#### dxf_importer.py
- [ ] Line 96-98: Remove `space` parameter from `_import_entities()` call
- [ ] Line 163: Remove `de.space_type` from SELECT query
- [ ] Line 190: Remove `'space_type': entity['space_type']` from entity data
- [ ] Line 237-238: Remove `space: str` parameter from `_import_entities()` function
- [ ] Lines 321, 494, 541, 601, 733, 790, 833, 883, 935: Remove `space_type` from INSERT statements
- [ ] All helper functions (`_import_entity`, `_import_text`, `_import_dimension`, etc.): Remove `space` parameter

#### dxf_exporter.py
- [ ] Lines 239, 515, 558, 601, 641: Remove `AND de.space_type = %s` / `AND dt.space_type = %s` filters
- [ ] Remove corresponding `%s` parameter values (currently 'MODEL')

**Note:** After removing space_type from code, run Migration 010 to drop the columns.

## 🚧 TODO - Phase 3: drawing_id Cleanup

### Files Requiring drawing_id Removal

#### High Priority
1. **dxf_lookup_service.py**
   - Remove `drawing_id` parameter from `get_or_create_layer()` (line 41)
   - Simplify cache key logic (lines 56-89)
   - Remove `drawing_id` from `track_layer_usage()` (line 311)
   - Remove `drawing_id` from `track_linetype_usage()` (line 349)

2. **intelligent_object_creator.py**
   - Remove `drawing_id` parameter from `create_from_entity()` (line 41)
   - Remove `drawing_id` parameter from `_create_entity_link()` (line 890)
   - Simplify logic in lines 916-936 to project-level only

3. **dxf_change_detector.py**
   - Remove `drawing_id` parameter from `detect_changes()` (line 22)
   - Remove `drawing_id` parameter from `_get_existing_links()` (line 106)
   - Keep only project-level query logic (lines 134-147)

4. **survey_import_service.py**
   - Remove `drawing_id` parameter from all functions (lines 22, 282, 298)
   - Remove all drawing_id references throughout file

5. **app.py**
   - Refactor drawing-related endpoints (lines 11068-11070, 11162-11164)
   - Change to use `project_id` instead of `drawing_id`
   - Refactor drawing statistics endpoint (lines 12764-12895)

#### Medium Priority
6. **batch_pnezd_parser.py**
   - Change `check_existing_points()` to use `project_id` instead of `drawing_id`

7. **retroactive_structure_creation.py**
   - Simplify query on line 168 to filter by `project_id` directly

#### Test Files
8. **test_dxf_import.py** - Update assertions about drawing_id IS NULL
9. **test_coordinate_preservation.py** - Remove drawing_id references
10. **test_map_viewer.py** - Remove drawing_id IS NULL checks
11. **test_z_preservation.py** - Update to not reference drawing_id

### SQL Migration Needed
- [ ] Create Migration 011: Remove `drawing_id` column from `layers` table
  - Drop existing unique index `idx_layers_project_layer_unique`
  - Recreate index without WHERE clause
  - Drop `drawing_id` column

## 🤔 DECISION NEEDED - Phase 4: drawings Table

### Key Decision Point
**Do we need multi-file drawing support?**

Current evidence suggests **NO**:
- All imports set `drawing_id=NULL`
- Application is now "Projects Only" architecture
- Existing code treats project as the primary container

### If Removing drawings Table:

#### Tasks
1. **SQL Migration**
   - [ ] Verify no critical data in `drawings` table
   - [ ] Drop `drawings` table
   - [ ] Drop `export_jobs.drawing_id` column if it exists

2. **Code Updates**
   - [ ] Remove `'drawing': ('drawings', 'drawing_id')` from `services/entity_registry.py:39`
   - [ ] Refactor or deprecate drawing statistics endpoint in `app.py` (lines 12764-12895)

3. **Test Updates**
   - [ ] Update all test files to not reference `drawing_id`

### If Keeping drawings Table:
- Need to restore proper `drawing_id` foreign key relationships
- Need to decide on multi-file import strategy
- NOT RECOMMENDED based on current architecture

## Database Migration Execution Plan

### Recommended Order:
```bash
# 1. Run Migration 009 (Paper Space Tables)
psql -h localhost -U postgres -d survey_data -f database/migrations/009_remove_paperspace_tables.sql

# 2. Complete space_type code removal (Python files)
#    (Manual code updates required)

# 3. Run Migration 010 (space_type Columns)
psql -h localhost -U postgres -d survey_data -f database/migrations/010_remove_space_type_columns.sql

# 4. Complete drawing_id code removal (Python files)
#    (Manual code updates required)

# 5. Run Migration 011 (drawing_id from layers - TO BE CREATED)
psql -h localhost -U postgres -d survey_data -f database/migrations/011_remove_drawing_id_from_layers.sql

# 6. Make decision on drawings table

# 7. Run Migration 012 (drawings table removal - IF DECIDED)
psql -h localhost -U postgres -d survey_data -f database/migrations/012_remove_drawings_table.sql
```

## Summary Statistics

### Completed
- ✅ **Code files modified:** 6 files (dxf_importer.py, dxf_exporter.py, app.py, 2 test files, 1 script)
- ✅ **Functions deleted:** 2 (`_import_viewports`, `_export_layouts`)
- ✅ **SQL migrations created:** 2 (009, 010)
- ✅ **Tables to be dropped:** 3 (layout_viewports, drawing_layer_usage, drawing_linetype_usage)

### Remaining
- 🚧 **Code files pending:** ~10+ files need space_type and drawing_id removal
- 🚧 **SQL migrations needed:** 2 more (011, possibly 012)
- 🚧 **Columns to be removed:** 6 (space_type x4, drawing_id x2+)

## Next Steps

1. **Immediate:** Deploy Phase 1 changes (paper space removal)
   - Migrations 009 is ready to run
   - Code changes are complete and committed

2. **Next Sprint:** Complete Phase 2 (space_type removal)
   - Update Python code to remove all space_type references
   - Run Migration 010

3. **Following Sprint:** Complete Phase 3 (drawing_id cleanup)
   - Update all function signatures
   - Run Migration 011

4. **Final Sprint:** Decide on and execute Phase 4 (drawings table)
   - Make architectural decision
   - Execute final migration

## Risk Assessment

- **Phase 1 (Paper Space):** ✅ ZERO RISK - Paper space is completely unused
- **Phase 2 (space_type):** ⚠️ LOW RISK - All data is MODEL space
- **Phase 3 (drawing_id):** ⚠️ MEDIUM RISK - Requires careful query updates
- **Phase 4 (drawings table):** 🔴 HIGH RISK - Needs business decision

## Testing Checklist

Before deploying each phase:
- [ ] Run full test suite: `pytest`
- [ ] Test DXF import: Upload sample DXF file
- [ ] Test DXF export: Export project to DXF
- [ ] Test layer creation: Verify layers are created correctly
- [ ] Test intelligent object creation: Verify objects are linked
- [ ] Test change detection: Reimport DXF and verify change tracking

---

**Last Updated:** 2025-11-17
**Author:** Claude (Anthropic AI)
**Status:** Phase 1 Complete, Phase 2 Prepared
