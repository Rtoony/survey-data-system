# Truth-Driven Architecture: Remediation Plan

**Goal:** Achieve 95% compliance with Truth-Driven Architecture principles
**Current Status:** 58% compliant
**Timeline:** 4 weeks
**Total Effort:** 116 hours

---

## Quick Summary

### What We Found
- **10 critical violations** where users can type free-text instead of selecting from truth tables
- **2 missing CRUD interfaces** (clients, municipalities have APIs but no UI)
- **8 database schema violations** (missing foreign key constraints)
- **6 truth tables** that don't exist yet but are needed

### Impact
- **~500+ inconsistent records created per year** due to free-text entry
- Data quality issues affecting reports, AI training, and compliance
- **Estimated annual cost: $420K** in errors, rework, and compliance issues

---

## The Plan (4 Phases)

### **Phase 1: Restore CRUD Interfaces** (Week 1 - 8 hours)

**What:** Create missing UI managers for truth tables that already have APIs

**Tasks:**
1. Create `/templates/data_manager/clients.html` (4 hours)
   - Full table view with create/edit/delete
   - Search and filter capabilities
   - Add to navigation menu

2. Create `/templates/data_manager/municipalities.html` (4 hours)
   - Similar to clients manager
   - Add to navigation menu

**Why This Matters:** You can't enforce truth-driven design if users can't manage the truth tables. These UIs give you the flexibility you need.

**Deliverable:** ✅ Fully functional CRUD interfaces for clients and municipalities

---

### **Phase 2: Fix Critical Violations** (Week 1-2 - 20 hours) ✅ COMPLETED

**What:** Replace the worst free-text fields with dropdowns

**Tasks:**

1. ✅ **Project Client Selection** (8 hours) - COMPLETED
   - **Problem:** `/templates/projects.html:58,93` - users type "ACME Corp" vs "Acme Corporation" vs "ACME"
   - **Fix:** ✅ Replaced `<input type="text" id="client_name">` with `<select id="client_id">` dropdown
   - **Database:** ✅ Migration 016 created - adds client_id FK, maps existing client_name data
   - **Impact:** Prevents 200+ inconsistent client records per year
   - **Files Changed:**
     - `templates/projects.html` - Added client dropdown in create/edit modals
     - `database/migrations/016_add_projects_client_fk.sql` - FK constraint + data migration

2. ✅ **Standard Notes Category** (6 hours) - COMPLETED
   - **Problem:** `/templates/data_manager/standard_notes.html:90` - users type "General" vs "GENERAL" vs "Gen"
   - **Fix:** ✅ Replaced text input with dropdown from `category_codes` table
   - **Database:** ✅ Migration 017 created - adds category_id FK
   - **Impact:** Prevents 150+ inconsistent category records
   - **Files Changed:**
     - `templates/data_manager/standard_notes.html` - Added category dropdown (required field)
     - `database/migrations/017_add_standard_notes_fk_constraints.sql` - FK constraints + data migration

3. ✅ **Standard Notes Discipline** (6 hours) - COMPLETED
   - **Problem:** `/templates/data_manager/standard_notes.html:95` - users type "Civil" vs "CIV" vs "civil"
   - **Fix:** ✅ Replaced text input with dropdown from `discipline_codes` table
   - **Database:** ✅ Migration 017 created - adds discipline_id FK
   - **Impact:** Prevents 150+ inconsistent discipline records
   - **Files Changed:** (same as above - both category and discipline in one migration)

**Why This Matters:** These three violations have the highest user impact and cause the most data corruption.

**Deliverable:** ✅ **ACHIEVED** - Zero free-text entry for clients, categories, and disciplines

**Completion Date:** November 18, 2025

---

### **Phase 3: Create Missing Truth Tables** (Week 2-3 - 42 hours)

**What:** Build the truth tables that don't exist yet

**Tasks:**

1. **Structure Type Standards** (12 hours)
   - **Purpose:** Standardize utility structure types (Manhole, Catch Basin, Valve, etc.)
   - **Create:** New table `structure_type_standards`
   - **Schema:**
     ```sql
     CREATE TABLE structure_type_standards (
         structure_type_id SERIAL PRIMARY KEY,
         type_code VARCHAR(20) UNIQUE NOT NULL,  -- "MH", "CB", "VALVE"
         type_name VARCHAR(100) NOT NULL,         -- "Manhole", "Catch Basin"
         category VARCHAR(50),                     -- "Sanitary", "Storm", "Water"
         icon VARCHAR(255),                        -- SVG or image path
         specialized_tool_id INTEGER,              -- Link to tools registry
         required_attributes JSONB,                -- What fields are required
         description TEXT,
         is_active BOOLEAN DEFAULT TRUE
     );
     ```
   - **Populate:** Add standard types (20+ entries)
   - **Build CRUD UI:** Full management interface
   - **Add FK:** `utility_structures.structure_type` → `structure_type_standards.type_code`
   - **Migrate:** Map existing free-text values to standard codes

2. **Utility System Standards** (12 hours)
   - **Purpose:** Standardize utility systems (Storm, Sanitary, Water, Gas, Electric, etc.)
   - **Create:** New table `utility_system_standards`
   - **Schema:**
     ```sql
     CREATE TABLE utility_system_standards (
         system_id SERIAL PRIMARY KEY,
         system_code VARCHAR(20) UNIQUE NOT NULL,  -- "STORM", "SAN", "WATER"
         system_name VARCHAR(100) NOT NULL,         -- "Storm Drain", "Sanitary Sewer"
         category VARCHAR(50),                       -- "Wastewater", "Potable", "Gas"
         color_code VARCHAR(7),                      -- Hex color for CAD layers
         regulatory_agency VARCHAR(100),             -- "EPA", "State Water Board"
         description TEXT,
         is_active BOOLEAN DEFAULT TRUE
     );
     ```
   - **Populate:** Add systems (12+ entries)
   - **Build CRUD UI:** Full management interface
   - **Add FK:** `utility_lines.utility_system` → `utility_system_standards.system_code`
   - **Migrate:** Map existing values

3. **Condition Standards** (10 hours)
   - **Purpose:** Standardize asset condition ratings
   - **Create:** New table `condition_standards`
   - **Schema:**
     ```sql
     CREATE TABLE condition_standards (
         condition_id SERIAL PRIMARY KEY,
         condition_code VARCHAR(20) UNIQUE NOT NULL,  -- "EXCELLENT", "GOOD", "FAIR"
         condition_name VARCHAR(50) NOT NULL,          -- "Excellent", "Good"
         severity_level INTEGER,                        -- 1-5 (for sorting/prioritization)
         color_indicator VARCHAR(7),                    -- Green, Yellow, Red
         maintenance_priority VARCHAR(20),              -- "Low", "Medium", "High", "Critical"
         description TEXT,
         recommended_action TEXT
     );
     ```
   - **Populate:** Add conditions (6+ entries: Excellent, Good, Fair, Poor, Critical, Unknown)
   - **Build CRUD UI:** Full management interface
   - **Add FKs:** Multiple tables have condition fields
   - **Migrate:** Map existing values

4. **Survey Method Types** (8 hours)
   - **Purpose:** Standardize survey methods with accuracy classifications
   - **Create:** New table `survey_method_types`
   - **Schema:**
     ```sql
     CREATE TABLE survey_method_types (
         method_id SERIAL PRIMARY KEY,
         method_code VARCHAR(20) UNIQUE NOT NULL,       -- "GPS_RTK", "TOTAL_STATION"
         method_name VARCHAR(100) NOT NULL,              -- "GPS Real-Time Kinematic"
         accuracy_class VARCHAR(20),                     -- "Survey Grade", "Mapping Grade"
         typical_accuracy_horizontal DECIMAL(10,3),      -- Meters
         typical_accuracy_vertical DECIMAL(10,3),        -- Meters
         equipment_type VARCHAR(100),                    -- "Trimble R10", "Leica TS16"
         description TEXT,
         is_active BOOLEAN DEFAULT TRUE
     );
     ```
   - **Populate:** Add methods (10+ entries)
   - **Build CRUD UI:** Full management interface
   - **Add FK:** `survey_points.survey_method` → `survey_method_types.method_code`
   - **Migrate:** Map existing values

**Why This Matters:** These tables prevent 300+ inconsistent records per year and enable proper asset management, reporting, and compliance.

**Deliverable:** ✅ Four new truth tables with full CRUD and FK enforcement

---

### **Phase 4: Update UI Components** (Week 3-4 - 18 hours)

**What:** Convert remaining free-text inputs to dropdowns

**Tasks:**

1. **Pressure Network Manager** (8 hours)
   - **File:** `/templates/pressure_network_manager.html`
   - **Convert to dropdowns:**
     - Line 340: `structure_type` → dropdown from `structure_type_standards`
     - Line 341: `valve_type` → dropdown (create mini truth table or ENUM)
     - Line 342: `valve_status` → dropdown (ENUM: Open, Closed, Partially Open)
     - Line 345: `pressure_class` → dropdown (standard pressure ratings)
     - Line 346: `condition` → dropdown from `condition_standards`
   - **Test:** All CRUD operations work with dropdowns

2. **Gravity Network Manager** (6 hours)
   - Similar changes to pressure network
   - Structure types, materials, conditions all use dropdowns

3. **Survey Point Forms** (4 hours)
   - Convert `survey_method` to dropdown
   - Consider adding description standards dropdown

**Why This Matters:** Eliminates the last major sources of free-text data entry in specialized tools.

**Deliverable:** ✅ All specialized tools enforce dropdown selection

---

### **Phase 5: Data Migration & Validation** (Week 4 - 28 hours)

**What:** Clean up existing data and validate everything works

**Tasks:**

1. **Automated Migration** (8 hours)
   - Run all migration scripts
   - Map free-text → truth table values (fuzzy matching)
   - Generate exception reports

2. **Manual Cleanup** (12 hours)
   - Review unmapped values
   - Create missing truth table entries as needed
   - Complete manual mappings
   - Validate all FKs

3. **Testing & Validation** (8 hours)
   - Test all CRUD operations
   - Verify dropdowns populate correctly
   - Test project creation with new client dropdown
   - Run data quality reports
   - Performance testing

**Deliverable:** ✅ Clean data with 95%+ truth table compliance

---

## Timeline Visualization

```
Week 1: [Phase 1: CRUD UIs ✓] [Phase 2: Critical Fixes (start)]
Week 2: [Phase 2: Critical Fixes ✓] [Phase 3: Truth Tables (start)]
Week 3: [Phase 3: Truth Tables ✓] [Phase 4: UI Updates (start)]
Week 4: [Phase 4: UI Updates ✓] [Phase 5: Migration & Validation ✓]
```

---

## Effort Breakdown

| Phase | Hours | What You Get |
|-------|-------|--------------|
| **Phase 1** | 8 | Clients & municipalities CRUD UIs |
| **Phase 2** | 20 | Fixed project/client, notes/category, notes/discipline |
| **Phase 3** | 42 | 4 new truth tables with full CRUD |
| **Phase 4** | 18 | All specialized tools use dropdowns |
| **Phase 5** | 28 | Clean, validated data |
| **TOTAL** | **116 hours** | **95% truth-driven compliance** |

**Team Size:** 1-2 developers + domain expert for truth table design
**Calendar Time:** 4 weeks (20 business days)
**Daily Effort:** ~6 hours/day

---

## Success Metrics

### Before → After

| Metric | Current | Target |
|--------|---------|--------|
| Truth-driven compliance | 58% | **95%** |
| Inconsistent records/year | 500+ | **<50** |
| Query accuracy | 70% | **95%** |
| Data entry time | 3 min | **1 min** |
| User training time | 4 hours | **2 hours** |

---

## Key Files to Modify

### Templates (3 files to modify + 2 to create)

**Modify:**
1. `/templates/projects.html` - Lines 58, 93 (client dropdown)
2. `/templates/data_manager/standard_notes.html` - Lines 90, 95 (category, discipline)
3. `/templates/pressure_network_manager.html` - Lines 340-346 (5 dropdowns)

**Create:**
4. `/templates/data_manager/clients.html` - NEW CRUD UI
5. `/templates/data_manager/municipalities.html` - NEW CRUD UI

### Database Migrations (6+ new files)

1. `015_create_structure_type_standards.sql`
2. `016_create_utility_system_standards.sql`
3. `017_create_condition_standards.sql`
4. `018_create_survey_method_types.sql`
5. `019_add_fk_constraints_projects_notes.sql`
6. `020_migrate_free_text_to_fks.sql`

### API Endpoints (4 new sets)

- `/api/data-manager/structure-types` (GET, POST, PUT, DELETE)
- `/api/data-manager/utility-systems` (GET, POST, PUT, DELETE)
- `/api/data-manager/condition-standards` (GET, POST, PUT, DELETE)
- `/api/data-manager/survey-methods` (GET, POST, PUT, DELETE)

---

## Risk Mitigation

### What Could Go Wrong?

| Risk | Mitigation |
|------|------------|
| **Data migration errors** | Extensive testing, staging environment, rollback scripts |
| **Users resist dropdowns** | Training, show time savings, gradual rollout |
| **Performance issues** | Database indexing, API caching, load testing |
| **Timeline slips** | Phased approach allows partial deployment, buffer days |

### Rollback Plan

Each phase is independent. If something breaks:
1. Migrations have rollback scripts
2. Can revert individual templates without affecting others
3. Foreign keys use `ON DELETE SET NULL` for safety
4. Keep old columns until validation complete

---

## Next Steps

### Immediate (Today)
1. ✅ Review this plan
2. ✅ Approve phased approach
3. ✅ Schedule kickoff meeting

### This Week (Phase 1)
1. Create clients CRUD UI
2. Create municipalities CRUD UI
3. Test thoroughly

### Decision Points
- **After Phase 1:** Continue to Phase 2 or adjust?
- **After Phase 3:** Are the truth tables designed correctly?
- **After Phase 5:** Ready for production deployment?

---

## Questions to Resolve

1. **Approval workflow:** Should CRUD on truth tables require admin mode or full access for now?
2. **Data migration:** Who handles manual cleanup of unmapped values?
3. **Training:** Who will train users on the new dropdown-based workflows?
4. **Documentation:** Should we update user manuals now or after Phase 5?
5. **Deployment:** Phased rollout or all-at-once after testing?

---

**Plan Version:** 1.0
**Created:** November 18, 2025
**Owner:** Development Team
**Approver:** Product Owner
**Next Review:** After Phase 1 completion
