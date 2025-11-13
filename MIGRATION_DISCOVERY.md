# Drawing Container Elimination - Migration Discovery

**Date:** November 13, 2025  
**Purpose:** Comprehensive audit of all "drawing" references in the ACAD-GIS system

## Executive Summary

This migration eliminates the Drawing table (Level 2) from the Project → Drawing → Layer → Entity hierarchy, simplifying to Project → Entity (Object Class). This discovery phase identified all affected files across database schema, backend API, frontend, and documentation.

**CRITICAL FINDING:** No database is currently provisioned. This means we can perform a **clean schema refactor** without worrying about data migration, rollback plans, or dual-write periods. We simply refactor all schema files first, then provision a fresh database with the new Project-centric structure.

---

## Database Schema Files (8 files)

### Core Schema Files
1. `create_dxf_entity_links_schema.sql` - Links DXF entities to drawings **[DELETE]**
2. `create_sheet_sets_schema.sql` - Sheet sets reference drawings **[DELETE]**
3. `create_dxf_export_schema.sql` - Export functionality uses drawings **[REFACTOR]**
4. `create_sheet_notes_schema.sql` - Notes linked to drawings **[REFACTOR]**
5. `create_survey_civil_schema.sql` - Domain tables have drawing_id FK **[MODIFY]**
6. `database/schema/complete_schema.sql` - Master schema with drawings table **[MODIFY]**
   - Contains database functions for drawing entities: `drawingent_search_trigger()`, `drawingtext_search_trigger()`
   - Contains triggers on: `drawing_dimensions`, `drawing_entities`, `drawing_text`, `drawing_hatches`, `sheet_drawing_assignments`

### Migration Files
7. `database/migrations/create_project_context_mappings.sql` - May reference drawings **[REVIEW]**
8. `database/migrations/create_name_mapping_tables.sql` - May reference drawings **[REVIEW]**

### Additional Discovery - Database Functions/Triggers
Found in `complete_schema.sql`:
- `drawingent_search_trigger()` - Search trigger for drawing_entities table **[DELETE]**
- `drawingtext_search_trigger()` - Search trigger for drawing_text table **[DELETE]**
- `sheetdrawing_search_trigger()` - Search trigger for sheet_drawing_assignments **[DELETE]**
- Triggers on `drawing_dimensions`, `drawing_entities`, `drawing_text`, `drawing_hatches` **[DELETE]**

---

## Backend Python Files (18 files)

### Core API & Services
1. `app.py` - Main Flask application with drawing CRUD endpoints **[MAJOR REFACTOR]**
2. `dxf_importer.py` - Imports DXF into drawing records **[MAJOR REFACTOR]**
3. `dxf_exporter.py` - Exports from drawing records **[MAJOR REFACTOR]**
4. `dxf_lookup_service.py` - Lookup by drawing **[REFACTOR]**
5. `dxf_change_detector.py` - Detects changes in drawings **[REFACTOR]**
6. `map_export_service.py` - Map export uses drawings **[REFACTOR]**
7. `intelligent_object_creator.py` - Creates objects from drawing entities **[REFACTOR]**

### Import/Processing Services
8. `survey_import_service.py` - Survey imports reference drawings **[REFACTOR]**
9. `batch_pnezd_parser.py` - Batch processing **[REVIEW]**
10. `batch_block_extractor.py` - Block extraction **[REVIEW]**
11. `batch_cad_extractor.py` - CAD extraction **[REVIEW]**
12. `retroactive_structure_creation.py` - Structure creation **[REVIEW]**
13. `standards/load_standards_data.py` - Standards loading **[REVIEW]**

### Test & Utility Files
14. `test_dxf_import.py` - Tests drawing imports **[UPDATE]**
15. `test_coordinate_preservation.py` - Tests coordinates **[REVIEW]**
16. `test_map_viewer.py` - Tests map viewer **[UPDATE]**
17. `test_z_preservation.py` - Tests Z coordinates **[REVIEW]**
18. `create_test_project.py` - Creates test projects **[UPDATE]**
19. `scripts/z_stress_harness.py` - Stress testing **[REVIEW]**

---

## Frontend Files

### JavaScript (1 file)
1. `static/js/project_context_manager.js` - Manages project/drawing context **[REFACTOR]**

### HTML Templates (37 files)

#### Drawing Management Pages **[DELETE ENTIRE PAGES]**
- `templates/drawings.html` - Main drawings page
- `templates/data_manager/drawings.html` - Data manager drawings page
- `templates/data_manager/sheet_sets.html` - Sheet sets manager
- `templates/sheet_sets.html` - Sheet sets page

#### Pages with Drawing References **[MODIFY]**
- `templates/base.html` - Navigation links to drawings
- `templates/index.html` - Home page references
- `templates/dxf_tools.html` - DXF tool pages
- `templates/map_viewer.html` - Map viewer queries drawings
- `templates/map_viewer_simple.html` - Simple map viewer
- `templates/entity_viewer.html` - Entity viewer
- `templates/projects.html` - Project list shows drawing counts
- `templates/project_overview.html` - Project overview
- `templates/project_operations.html` - Project operations
- `templates/project_survey_points.html` - Survey points
- `templates/project_standards_assignment.html` - Standards assignment
- `templates/project_compliance.html` - Compliance checking
- `templates/sheet_notes.html` - Sheet notes (depends on drawings)
- `templates/data_manager/index.html` - Data manager home
- `templates/data_manager/drawing_materials.html` - Drawing materials

#### Standards & Reference Pages **[REVIEW]**
- `templates/standards/index.html`
- `templates/standards/linetypes.html`
- `templates/standards/viewports.html`
- `templates/standards/plotstyles.html`
- `templates/standards/scales.html`
- `templates/standards/notes.html`
- `templates/standards/abbreviations.html`

#### Architecture & Documentation Pages **[REVIEW]**
- `templates/architecture.html`
- `templates/why_this_matters.html`
- `templates/evolution.html`
- `templates/digital_twin.html`
- `templates/schema_graph.html`
- `templates/schema_relationships.html`
- `templates/usage_dashboard.html`

#### Tool Pages **[REVIEW]**
- `templates/tools/survey_point_manager.html`
- `templates/tools/batch_point_import.html`

---

## Documentation Files (12 files)

### Core Documentation **[MAJOR UPDATES]**
1. `replit.md` - Project overview and architecture **[CRITICAL UPDATE]**
2. `README.md` - Main readme **[UPDATE]**
3. `ENTITY_RELATIONSHIP_MODEL.md` - ER model with Drawing level **[CRITICAL UPDATE]**
4. `DATABASE_ARCHITECTURE_GUIDE.md` - Database architecture **[CRITICAL UPDATE]**

### Standards & Domain Guides **[UPDATE]**
5. `CAD_STANDARDS_GUIDE.md` - CAD standards
6. `docs/CAD_LAYER_NAMING_STANDARDS.md` - Layer naming standards
7. `standards/cad_standards_vocabulary.md` - Vocabulary
8. `STANDARDS_MAPPING_FRAMEWORK.md` - Mapping framework
9. `SURVEY_CODE_SYSTEM_GUIDE.md` - Survey codes

### Project & Assignment Guides **[UPDATE]**
10. `PROJECT_ASSIGNMENT_MODEL.md` - Assignment model
11. `database/SCHEMA_VERIFICATION.md` - Schema verification
12. `database/AI_OPTIMIZATION_SUMMARY.md` - AI optimization

---

## Migration Impact Summary

### High Impact (Requires Major Refactoring)
- **Database Schema:** 6 files need modification
- **Backend Core:** `app.py`, `dxf_importer.py`, `dxf_exporter.py`
- **Documentation:** 4 critical architectural documents

### Medium Impact (Requires Updates)
- **Backend Services:** 10+ service and utility files
- **Frontend Pages:** 20+ HTML templates need review/updates
- **Tests:** 3+ test files need updates

### Low Impact (Requires Review Only)
- **Standards Pages:** May contain drawing references in examples
- **Utility Scripts:** May use drawings for testing

### Files to Delete Entirely
- `templates/drawings.html`
- `templates/data_manager/drawings.html`
- `templates/data_manager/sheet_sets.html`
- `templates/sheet_sets.html`
- `create_dxf_entity_links_schema.sql`
- `create_sheet_sets_schema.sql`

---

## Next Steps

1. ✅ **Discovery Complete** - All references documented
2. **Database Migration** - Create migration scripts
3. **Backend Refactoring** - Update API and services
4. **Frontend Cleanup** - Remove/update UI components
5. **Documentation Updates** - Update all .MD files
6. **Validation** - Test all workflows

---

## Notes

- The drawings table is deeply integrated into the current system
- Migration will touch ~75+ files across all layers
- Most critical: DXF import/export workflows must be completely refactored
- Sheet sets functionality will be removed entirely (client-managed post-production)
- Pattern matching classification engine remains unchanged
- Domain tables and object classes remain unchanged (just lose drawing_id FK)
