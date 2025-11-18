# Truth-Driven Architecture Phase 2 - FK Constraints Migration

**Project Start Date:** 2025-11-18
**Status:** Phase 1 Complete, Ready for Testing
**Branch:** `claude/complete-fk-constraints-migration-01ShM6C7pUJLErTM4CqsLK5V`

## Executive Summary

This document tracks the implementation of Phase 2 of the Truth-Driven Architecture, which expands FK constraint enforcement from 6 constraints to 19+ constraints system-wide. The goal is to eliminate ALL free-text chaos by implementing remaining foreign key constraints, building comprehensive CRUD interfaces, and converting all UI forms to dropdown-driven architecture.

## Phase 1 Status: COMPLETE ✓

### Database Migrations Created

| Migration | File | Purpose | Status |
|-----------|------|---------|--------|
| 032 | `032_create_utility_system_standards.sql` | Create utility_system_standards table with 15 standard systems | ✓ Created |
| 033 | `033_create_status_standards.sql` | Create status_standards table with 23 standard status codes | ✓ Created |
| 034 | `034_add_utility_system_status_fk_constraints.sql` | Add 5 FK constraints + data migration + testing | ✓ Created |

### FK Constraints Added (5 Total)

1. **utility_lines.utility_system → utility_system_standards.system_code**
   - Constraint: `fk_utility_lines_system`
   - On Delete: SET NULL
   - On Update: CASCADE
   - Status: Created in Migration 034

2. **utility_structures.utility_system → utility_system_standards.system_code**
   - Constraint: `fk_utility_structures_system`
   - On Delete: SET NULL
   - On Update: CASCADE
   - Status: Created in Migration 034

3. **utility_lines.status → status_standards.status_code**
   - Constraint: `fk_utility_lines_status`
   - On Delete: SET NULL
   - On Update: CASCADE
   - Status: Created in Migration 034

4. **utility_structures.status → status_standards.status_code**
   - Constraint: `fk_utility_structures_status`
   - On Delete: SET NULL
   - On Update: CASCADE
   - Status: Created in Migration 034

5. **projects.project_status → status_standards.status_code**
   - Constraint: `fk_projects_status`
   - On Delete: SET NULL
   - On Update: CASCADE
   - Status: Created in Migration 034

### Reference Data Created

#### Utility System Standards (15 Records)
- STORM (Storm Drainage)
- SEWER (Sanitary Sewer)
- WATER (Water Distribution)
- RECLAIM (Reclaimed Water)
- FIRE (Fire Protection)
- GAS (Natural Gas)
- ELECTRIC (Electric)
- STEAM (Steam)
- TELECOM (Telecommunications)
- CABLE (Cable TV)
- FIBER (Fiber Optic)
- IRRIGATION (Irrigation)
- FUEL (Fuel)
- COMPRESSED_AIR (Compressed Air)
- UNKNOWN (Unknown Utility)

#### Status Standards (23 Records)

**Utility Status Codes (7):**
- EXISTING, PROPOSED, ABANDONED, REMOVED, TEMPORARY, RELOCATED, FUTURE

**Project Status Codes (6):**
- ACTIVE, PLANNING, COMPLETE, ON_HOLD, CANCELLED, ARCHIVED

**Drawing Status Codes (6):**
- DRAFT, REVIEW, APPROVED, ISSUED, SUPERSEDED, VOID

**Universal Status Codes (3):**
- UNKNOWN, VERIFY, CONFLICT

### UI Components Created

| Component | File | Status |
|-----------|------|--------|
| Utility Systems Manager | `templates/data_manager/utility_systems.html` | ✓ Created |
| Status Standards Manager | *Pending* | To be created |

### Data Migration Strategy

Migration 034 includes comprehensive data migration:

1. **Pre-Migration Validation**
   - Checks for non-conforming values in utility_lines and utility_structures
   - Reports all values that don't match standards

2. **Automated Data Mapping**
   - Maps common abbreviations to standard codes:
     - SD, Storm → STORM
     - SS, Sewer → SEWER
     - W, Water → WATER
     - etc.

3. **Fallback Handling**
   - Sets remaining non-conforming values to 'UNKNOWN'
   - Prevents migration failures due to data inconsistencies

4. **Default Status Assignment**
   - Existing utilities default to 'EXISTING' status
   - Active projects default to 'ACTIVE' status

### Automated Testing

Migration 034 includes 4 built-in tests:

1. **Test 1:** Verify invalid utility_system is rejected (FK violation)
2. **Test 2:** Verify valid utility_system is accepted
3. **Test 3:** Verify invalid status is rejected (FK violation)
4. **Test 4:** Verify valid status is accepted

All tests run automatically during migration execution.

## Running the Migrations

### Prerequisites
- PostgreSQL database running
- Database connection configured
- Backup of production data (recommended)

### Execution Steps

```bash
# 1. Run migrations in order
psql -U postgres -d survey_data -f database/migrations/032_create_utility_system_standards.sql
psql -U postgres -d survey_data -f database/migrations/033_create_status_standards.sql
psql -U postgres -d survey_data -f database/migrations/034_add_utility_system_status_fk_constraints.sql

# 2. Verify migrations succeeded
psql -U postgres -d survey_data -c "
SELECT constraint_name, table_name
FROM information_schema.table_constraints
WHERE constraint_name LIKE 'fk_utility%' OR constraint_name = 'fk_projects_status';
"

# Expected output: 5 constraints
# - fk_utility_lines_system
# - fk_utility_structures_system
# - fk_utility_lines_status
# - fk_utility_structures_status
# - fk_projects_status
```

### Rollback Plan

```sql
-- If needed, remove FK constraints
ALTER TABLE utility_lines DROP CONSTRAINT IF EXISTS fk_utility_lines_system;
ALTER TABLE utility_structures DROP CONSTRAINT IF EXISTS fk_utility_structures_system;
ALTER TABLE utility_lines DROP CONSTRAINT IF EXISTS fk_utility_lines_status;
ALTER TABLE utility_structures DROP CONSTRAINT IF EXISTS fk_utility_structures_status;
ALTER TABLE projects DROP CONSTRAINT IF EXISTS fk_projects_status;

-- Optionally drop the standards tables
DROP TABLE IF EXISTS utility_system_standards CASCADE;
DROP TABLE IF EXISTS status_standards CASCADE;
```

## Phase 2-5 Roadmap

### Phase 2: Survey Point Standards (Planned)
**Target:** 3 new FK constraints

- survey_points.coord_system_id → coordinate_systems.system_id
- survey_points.description → survey_point_descriptions.description_code
- projects.coord_system_id → coordinate_systems.system_id

**Deliverables:**
- Migration files for FK constraints
- coordinate_systems.html CRUD interface
- Updated survey point manager UI

### Phase 3: Block Standards (Planned)
**Target:** 1 new FK constraint

- cad_blocks.block_category → block_category_standards.category_code

**Note:** Need to verify if cad_blocks table exists. May need schema updates.

### Phase 4: Relationship Set Naming Templates (Planned)
**Target:** 1 new FK constraint

- relationship_sets.template_id → relationship_set_naming_templates.template_id

**Deliverables:**
- Template-based name generation system
- Auto-incrementing sequence numbers
- relationship_set_naming_templates.html CRUD interface

### Phase 5: Municipality & Owner Standards (Planned)
**Target:** 3 new FK constraints

- projects.municipality_id → municipalities.municipality_id
- utility_lines.owner → owner_standards.owner_code
- utility_structures.owner → owner_standards.owner_code

**Deliverables:**
- owner_standards table creation
- owner_standards.html CRUD interface
- Updated utility manager UIs

## Progress Tracking

### Overall Progress
- **Phase 1:** ✓ Complete (5 FK constraints)
- **Phase 2:** Pending (3 FK constraints)
- **Phase 3:** Pending (1 FK constraint)
- **Phase 4:** Pending (1 FK constraint)
- **Phase 5:** Pending (3 FK constraints)

**Total FK Constraints:** 13 new (5 complete + 8 pending)
**Combined with Phase 1 Original:** 19 total FK constraints planned

### Existing FK Constraints (From Phase 1)
1. utility_lines.material → material_standards.material_code
2. utility_structures.material → material_standards.material_code
3. utility_structures.structure_type → structure_type_standards.type_code
4. standard_notes.category_id → category_codes.category_id
5. standard_notes.discipline_id → discipline_codes.discipline_id
6. projects.client_id → clients.client_id

## Success Metrics

### Phase 1 Metrics
- ✓ 5 FK constraints implemented
- ✓ 38 reference records created (15 systems + 23 statuses)
- ✓ 1 CRUD interface built (utility_systems.html)
- ✓ Automated tests included in migrations
- ✓ Data migration strategy with fallback handling
- ⏳ 1 CRUD interface pending (status_standards.html)
- ⏳ UI forms not yet updated with dropdowns

### Target Metrics (All Phases)
- 100% of text columns use FK constraints or have documented reason for free-text
- Zero free-text inputs in production UI forms (all dropdowns)
- All FK constraints tested with automated test suite
- Complete CRUD interfaces for all 20+ reference tables

## Known Issues & Considerations

1. **Database not running in current environment**
   - Migrations created but not yet executed
   - Will need database access to test

2. **CAD Blocks table may not exist**
   - Need to verify schema before Phase 3
   - May require additional schema modifications

3. **UI Form Updates**
   - Forms not yet updated to use new dropdown fields
   - Will require frontend work in subsequent commits

4. **API Endpoints**
   - Backend API routes need to be created for:
     - `/api/data-manager/utility-systems`
     - `/api/data-manager/status-standards`

## Next Steps

1. **Complete Status Standards CRUD Interface**
   - Create `templates/data_manager/status_standards.html`
   - Follow pattern from utility_systems.html

2. **Create Backend API Routes**
   - Add routes for utility systems CRUD
   - Add routes for status standards CRUD

3. **Update Utility Manager Forms**
   - gravity_pipe_manager.html - add system/status dropdowns
   - pressure_pipe_manager.html - add system/status dropdowns
   - utility_structure_manager.html - add system/status dropdowns

4. **Testing & Validation**
   - Execute migrations on development database
   - Verify all FK constraints work correctly
   - Test CRUD interfaces

5. **Proceed to Phase 2**
   - Begin survey point standards implementation
   - Create coordinate systems CRUD interface

## Resources & References

- **Project Specification:** Project 3: Truth-Driven Architecture Phase 2 - Complete Migration
- **Migration Directory:** `/database/migrations/`
- **UI Templates:** `/templates/data_manager/`
- **Branch:** `claude/complete-fk-constraints-migration-01ShM6C7pUJLErTM4CqsLK5V`

---

*Last Updated: 2025-11-18*
*Author: Claude Code (Automated Migration System)*
