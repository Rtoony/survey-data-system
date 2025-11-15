# **Truth-Driven Architecture: The Foundation of Data Quality**

*Architectural Philosophy Document for ACAD-GIS System*

---

## **Executive Summary**

ACAD-GIS is built on a fundamental principle: **CAD Vocabulary and Reference Data Hub tables are the single source of truth for all standardized data.** Users should **never manually type** information that should be selected from these authoritative sources.

**Why this matters:**
- **Data Quality:** Prevents typos, inconsistencies, and invalid entries
- **AI Understanding:** Machine learning requires clean, standardized data
- **Standards Enforcement:** Ensures compliance with engineering standards
- **Change Management:** Updates to vocabulary automatically propagate throughout the system
- **Cost Prevention:** A single typo can cascade into expensive construction errors

This document inventories all truth tables, identifies areas where manual input still exists (violations), and outlines the remediation roadmap.

---

## **The Philosophy: Why Truth-Driven Design**

### **The Problem with Manual Entry**

Traditional CAD systems allow engineers to type anything:
- Layer name: "storm drain" vs "Storm Drain" vs "STORM-DRAIN" vs "SD"
- Material: "PVC" vs "pvc" vs "Polyvinyl Chloride" vs "P.V.C."
- Status: "Existing" vs "EXIST" vs "EX" vs "E"

**Result:** Chaos. Reports break. AI can't understand. Queries miss data. Compliance checking fails.

### **The Solution: Controlled Vocabulary**

Instead of free text, users select from **database-backed dropdown menus** populated from truth tables:

```
❌ BAD: User types "storm drain" (free text input)
✅ GOOD: User selects "Storm Drain" from dropdown (populated from object_type_codes table)

❌ BAD: User types "PVC" (might type "pvc", "P.V.C.", etc.)
✅ GOOD: User selects "PVC" from dropdown (populated from material_standards table)

❌ BAD: User types "Pavement Material Compliance Set" (no standard format)
✅ GOOD: User selects "PAVE-MAT-01" from template (populated from relationship_set_naming_templates table)
```

### **The Ripple Effect of Clean Data**

When vocabulary is controlled:
1. **AI embeddings are consistent** - "PVC" always means PVC, enabling semantic search
2. **Reports are accurate** - Queries for "material = 'PVC'" catch 100% of PVC, not 87%
3. **Rules enforcement works** - "If material is PVC, require Detail D-PVC-01" can be automated
4. **Standards evolve cleanly** - Change "PVC" to "PVC Schedule 40" in one table, updates everywhere
5. **Compliance is provable** - Auditors see standardized, traceable data

---

## **The Truth Tables: Complete Inventory**

### **1. CAD Vocabulary (14 Tables)**

These tables define the standardized CAD elements that appear in drawings:

| Table | Purpose | Examples | Current CRUD Status |
|-------|---------|----------|-------------------|
| `layer_standards` | Standardized layer names, colors, lineweights | "CIV-UTIL-STORM-12IN-NEW-LN" | ✅ Full CRUD (Schema Explorer) |
| `block_definitions` | Reusable symbols with SVG previews | Manhole symbols, valve symbols | ✅ Full CRUD |
| `detail_standards` | Pre-approved construction details | Storm drain connections, curb sections | ✅ Full CRUD |
| `hatch_patterns` | Material representation patterns | Concrete hatch, asphalt hatch | ✅ Full CRUD |
| `material_standards` | Construction material specifications | PVC SDR-35, Concrete 4000 PSI | ✅ Full CRUD |
| `note_standards` | Standard callout text | "See Detail D-01", "3% slope min" | ✅ Full CRUD |
| `linetype_standards` | Line style definitions | Dashed, centerline, hidden | ✅ Full CRUD |
| `color_standards` | Standardized color palette | AutoCAD Color Index mappings | ✅ Full CRUD |
| `text_styles` | Text formatting standards | Arial 0.1", Romans 0.08" | ✅ Full CRUD |
| `plot_styles` | Plot/print configurations | Lineweights, color mappings | ✅ Full CRUD |
| `dimension_styles` | Dimension formatting | Architectural, civil, metric | ✅ Full CRUD |
| `viewport_standards` | Standard viewport scales | 1"=20', 1"=50' | ✅ Full CRUD |
| `annotation_standards` | Annotation style definitions | Leader styles, multileader formats | ✅ Full CRUD |
| `symbol_categories` | Organization of block library | Utilities, Landscape, Site Amenities | ✅ Full CRUD |

**Status:** CAD Vocabulary is **fully implemented** with complete CRUD interfaces.

---

### **2. Reference Data Hub (11+ Tables)**

These tables define project-agnostic reference data and organizational standards:

| Table | Purpose | Examples | Current CRUD Status |
|-------|---------|----------|-------------------|
| `clients` | Client organizations | City of San Jose, ABC Engineering | ✅ Full CRUD |
| `municipalities` | Jurisdictions and agencies | Santa Clara County, Caltrans | ✅ Full CRUD |
| `cad_standards` | CAD standard sets | City of SJ 2024, County Standard | ✅ Full CRUD |
| `projects` | Engineering projects | Main St Reconstruction, Park Improvements | ✅ Full CRUD (Civil Project Manager) |
| `discipline_codes` | Engineering disciplines | Civil (CIV), Site (SITE), Survey (SURV) | ✅ Full CRUD |
| `category_codes` | System categories | Utilities (UTIL), Roads (ROAD), Grading (GRAD) | ✅ Full CRUD |
| `object_type_codes` | Specific object types | Storm Drain (STORM), Manhole (MH), Curb (CURB) | ✅ Full CRUD |
| `phase_codes` | Construction phases | Existing (EXIST), New (NEW), Proposed (PROP) | ✅ Full CRUD |
| `geometry_codes` | Geometry types | Line (LN), Point (PT), Polygon (PG) | ✅ Full CRUD |
| `attribute_codes` | Object attributes | 12IN, PVC, 4FT | ✅ Full CRUD |
| `filterable_entity_columns` | Metadata field registry | Which fields are filterable per entity type | ✅ Full CRUD |
| `code_references` | General codes library | Building codes, spec references | ✅ Full CRUD |
| `sheet_templates` | Standard sheet layouts | 24x36 Plan, 11x17 Detail | ✅ Full CRUD |

**Status:** Reference Data Hub is **fully implemented** with complete CRUD interfaces.

---

### **3. Specialized Vocabularies (4 Tables)**

These tables support specific features with their own controlled vocabularies:

| Table | Purpose | Examples | Current CRUD Status |
|-------|---------|----------|-------------------|
| `survey_code_library` | Field survey point codes | "EP" = Edge of Pavement, "TW" = Top of Wall | ✅ Full CRUD (Survey Code Manager) |
| `specialized_tools_registry` | Object type → tool mappings | "gravity_pipe" → Gravity Pipe Manager | ✅ Database-driven (no UI CRUD yet) |
| `project_usage_tracking` | Usage analytics | Project/layer/block frequency | ✅ Read-only dashboard |
| `entity_registry` | Entity type → table mappings | "utility_line" → utility_lines table | ✅ Code-based (services/entity_registry.py) |

**Status:** Specialized vocabularies are **implemented but need CRUD interfaces**.

---

## **Violations Audit: Where Manual Input Still Exists**

Despite the truth-driven philosophy, several areas still allow users to type freely instead of selecting from controlled vocabularies. These are **architectural violations** that need remediation.

### **Category A: High-Priority Violations (User-Facing)**

These violations directly impact user experience and data quality:

#### **1. Project Relationship Sets**

**Location:** `templates/project_relationship_sets.html` - Create Relationship Set modal

**Violation:**
```html
<!-- CURRENT: Free text input -->
<input type="text" id="setName" placeholder="e.g. Pavement Material Compliance Set">
<input type="text" id="shortCode" placeholder="e.g. PAVE-MAT-01">
```

**Impact:**
- Users invent naming conventions ("Storm System", "storm_sys", "SS-MAIN-01")
- No standardization across projects
- Difficult to search/filter relationship sets
- Templates can't be reliably reused

**Solution Needed:**
- Create `relationship_set_naming_templates` table
- Fields: `template_id`, `template_name`, `name_format`, `short_code_format`, `category`, `description`
- Examples:
  - Template: "Storm System Compliance" → Format: "{DISC}-{CAT}-{PROJECT_CODE}-{SEQ}"
  - Template: "Material Compliance Check" → Format: "MAT-{MATERIAL}-{PROJECT_CODE}"
- Replace text inputs with:
  1. Template dropdown (select naming standard)
  2. Token replacement fields (fill in project-specific values)
  3. Auto-generated name preview

**Status:** ⚠️ **Not implemented** - CRUD interface needed

---

#### **2. Survey Points**

**Location:** Survey point import/management

**Violation:**
```sql
-- From survey_points table schema
point_description TEXT,           -- Free text (should be from controlled vocabulary)
survey_method VARCHAR(50),        -- Free text (should be dropdown: GPS, Total Station, Level)
```

**Impact:**
- Descriptions vary: "edge of pavement" vs "EP" vs "edge pavement" vs "pave edge"
- Survey methods inconsistent: "GPS" vs "gps" vs "RTK GPS" vs "GNSS"
- Reports and queries unreliable
- AI can't parse semantics

**Solution Needed:**
- Create `survey_point_description_standards` table
  - Fields: `description_code`, `description_text`, `category`, `icon`, `cad_representation`
  - Examples: "EP" = "Edge of Pavement", "TW" = "Top of Wall"
- Create `survey_method_types` table
  - Fields: `method_code`, `method_name`, `accuracy_class`, `equipment_type`
  - Examples: "GPS-RTK", "TOTAL-STATION", "LEVEL-DIGITAL", "LEVEL-AUTO"
- Replace text inputs with dropdown selects

**Status:** ⚠️ **Partially implemented** - Survey codes exist, but not enforced for descriptions

---

#### **3. Standard Notes**

**Location:** `templates/sheet_note_manager.html`, `standard_notes` table

**Violation:**
```sql
-- From standard_notes table schema
note_category VARCHAR(100),       -- Free text (should be from category_codes)
discipline VARCHAR(50),           -- Free text (should be from discipline_codes)
```

**Impact:**
- Categories vary: "General" vs "GENERAL" vs "Gen" vs "General Notes"
- Disciplines inconsistent: "Civil" vs "CIV" vs "civil" vs "C"
- Filtering and organization breaks down
- Cross-referencing with layers/blocks fails

**Solution Needed:**
- Replace `note_category` with foreign key to `category_codes.category_code`
- Replace `discipline` with foreign key to `discipline_codes.discipline_code`
- Update UI to use dropdown selects populated from truth tables
- Migration script to map existing free text to canonical codes

**Status:** ⚠️ **Not implemented** - Schema uses VARCHAR instead of FK

---

#### **4. Material Types (Throughout System)**

**Location:** Multiple locations - utility lines, structures, specifications

**Violation:**
- Utility lines: `material` column allows free text
- Utility structures: `material_type` allows free text
- No enforcement of approved materials list

**Impact:**
- Same material entered differently: "PVC", "pvc", "P.V.C.", "Polyvinyl Chloride"
- Compliance rules fail: "Material must be PVC, HDPE, or RCP" can't match "pvc"
- Cost estimation breaks: Can't aggregate quantities by material
- Detail cross-references fail: Can't auto-link "If PVC, use Detail D-PVC-01"

**Solution Needed:**
- Create `approved_material_types` table (may already exist as `material_standards`)
- Fields: `material_code`, `material_name`, `category`, `specification`, `approved_by`, `effective_date`
- Examples: "PVC-SDR35", "HDPE-DR17", "RCP-CLASS3", "DI-C900"
- Enforce foreign key constraints on all material columns
- Add dropdowns in all UIs that reference materials

**Status:** ⚠️ **Partially implemented** - `material_standards` exists but not enforced via FK

---

#### **5. Structure Types**

**Location:** Utility structures, equipment assets

**Violation:**
```sql
-- utility_structures table
structure_type VARCHAR(50),       -- Free text (should be controlled vocabulary)
```

**Impact:**
- Inconsistent naming: "Manhole" vs "MH" vs "manhole" vs "Man Hole"
- Type-specific tools can't auto-launch: "If type = MH, open Manhole Inspector"
- Inventory reports unreliable
- Standards enforcement fails

**Solution Needed:**
- Create `structure_type_standards` table
- Fields: `type_code`, `type_name`, `category`, `icon`, `specialized_tool_id`, `required_attributes`
- Examples: "MH" = "Manhole", "CB" = "Catch Basin", "CLNOUT" = "Cleanout"
- Link to `specialized_tools_registry` for auto-tool launching
- Enforce via dropdown selects

**Status:** ⚠️ **Not implemented** - Free text currently allowed

---

#### **6. Equipment/Asset Types**

**Location:** Future asset management features

**Violation:**
- No controlled vocabulary for equipment types yet
- When implemented, likely to use free text without standards

**Impact (Projected):**
- Inconsistent naming across projects
- Can't aggregate maintenance schedules
- Inventory tracking unreliable

**Solution Needed:**
- Create `equipment_type_standards` table (proactive)
- Fields: `equipment_code`, `equipment_name`, `category`, `maintenance_schedule`, `manufacturer_std`
- Examples: "PUMP-SUB-1HP", "VALVE-GATE-6IN", "METER-WATER-2IN"

**Status:** ⚠️ **Not implemented** - Future feature

---

### **Category B: Medium-Priority Violations (Backend/Internal)**

#### **7. Custom Project Attributes**

**Location:** Various project-specific metadata fields

**Violation:**
- Projects allow custom JSON attributes without vocabulary control
- Users can invent attribute names on the fly

**Solution Needed:**
- Create `project_attribute_vocabulary` table
- Define allowed custom attribute keys
- Validate JSON against vocabulary

**Status:** ⚠️ **Design phase**

---

#### **8. DXF Import Classification Overrides**

**Location:** Object reclassifier tool

**Violation:**
- Users can manually type entity types during reclassification
- Should only select from registered entity types

**Solution Needed:**
- Enforce entity type dropdown from `entity_registry`
- Prevent free text entry

**Status:** ⚠️ **Review needed**

---

## **The Remediation Roadmap**

### **Phase 1: Critical Violations (Immediate)**

**Target Date:** Q1 2026

1. **Project Relationship Set Naming**
   - Create `relationship_set_naming_templates` table
   - Build template CRUD interface
   - Update relationship set create modal to use templates
   - Migrate existing sets to closest template

2. **Material Type Enforcement**
   - Add foreign key constraints to all material columns
   - Update all material input fields to use dropdowns from `material_standards`
   - Data migration script for existing free text

3. **Structure Type Standardization**
   - Create `structure_type_standards` table
   - Build CRUD interface
   - Update structure management UIs
   - Link to specialized tools registry

---

### **Phase 2: High-Value Improvements (Near-Term)**

**Target Date:** Q2 2026

4. **Survey Point Descriptions**
   - Create `survey_point_description_standards` table
   - Create `survey_method_types` table
   - Update survey point import/manager UIs
   - Migrate existing survey data

5. **Standard Note Categories**
   - Refactor `standard_notes` schema to use foreign keys
   - Update Sheet Note Manager UI
   - Data migration and cleanup

---

### **Phase 3: Comprehensive Coverage (Long-Term)**

**Target Date:** Q3-Q4 2026

6. **Equipment/Asset Types** (when asset management built)
7. **Custom Attribute Vocabulary** (validation framework)
8. **DXF Classification Lock-Down** (prevent manual type entry)

---

## **Future Vision: User-Configurable Standards**

### **The Ultimate Goal**

Enable users to **create new controlled vocabularies on-the-fly** without code changes:

**Scenario:**
1. Engineer realizes: "We need to track 'Retaining Wall Types' (Gravity, MSE, Cantilever)"
2. Goes to Reference Data Hub → "Create New Vocabulary"
3. Fills in form:
   - **Vocabulary Name:** "Retaining Wall Types"
   - **Code Column:** `wall_type_code` (VARCHAR(20))
   - **Name Column:** `wall_type_name` (VARCHAR(100))
   - **Category:** "Structures"
4. System auto-generates:
   - Database table: `retaining_wall_type_standards`
   - CRUD interface: Accessible via Reference Data Hub
   - Dropdown component: Available for use in any form
   - API endpoints: `/api/standards/retaining-wall-types`

**Impact:**
- No developer needed to add new vocabularies
- Standards scale with business needs
- Organizations customize to their workflows
- Truth-driven design becomes self-sustaining

### **Technical Challenges**

1. **Schema Generation:** Dynamic table creation (security/safety concerns)
2. **UI Generation:** Auto-generating CRUD interfaces for unknown schemas
3. **Dropdown Registration:** Making new vocabularies available system-wide
4. **Migration Management:** Handling vocabulary evolution over time
5. **Validation:** Ensuring user-created vocabularies follow data integrity rules

### **Phased Approach**

**Phase A: Template-Based Vocabulary Creation**
- Pre-defined table templates (simple lookup, hierarchical, attributed)
- User fills in template parameters
- System generates from template

**Phase B: Form-Based Schema Design**
- UI for defining columns, types, constraints
- Validation before generation
- Automated testing of generated tables

**Phase C: Full Self-Service**
- Advanced users can design complex vocabularies
- Approval workflow for production deployment
- Version control for vocabulary schemas

---

## **Enforcement Mechanisms**

### **Current Enforcement**

**Database Level:**
- Foreign key constraints (where implemented)
- CHECK constraints on enum-like columns
- NOT NULL constraints on required fields

**Application Level:**
- Dropdown selects in UI (prevents free text)
- Server-side validation against truth tables
- `filterable_entity_columns` registry prevents invalid field references

**Code Level:**
- `entity_registry.py` validates entity types
- `relationship_set_service.py` validates filter columns against table schema
- Layer classifier enforces naming conventions

### **Gaps in Enforcement**

❌ **No database-level enforcement for:**
- Material types (VARCHAR, no FK)
- Structure types (VARCHAR, no FK)
- Survey methods (VARCHAR, no FK)
- Note categories (VARCHAR, no FK)

❌ **No application-level enforcement for:**
- Relationship set naming (free text)
- Custom project attributes (unconstrained JSON)

### **Future Enforcement**

✅ **Add to all vocabulary-controlled fields:**
1. Database: Foreign key constraints
2. UI: Dropdown selects only (no text input)
3. API: Validation middleware
4. Import: Auto-mapping + manual review for unknowns

---

## **Benefits of Full Truth-Driven Implementation**

### **For Engineers**
✅ **No guessing** - Clear, predefined options for every field  
✅ **Consistency** - Projects follow organizational standards automatically  
✅ **Efficiency** - Dropdowns faster than typing, no typos to fix  
✅ **Confidence** - Data quality guaranteed by system constraints  

### **For Project Managers**
✅ **Compliance** - Standards enforcement built into workflow  
✅ **Reporting** - Reliable data for cost estimates, schedules, resource planning  
✅ **Auditability** - Provable adherence to codes and standards  
✅ **Change Management** - Vocabulary updates cascade automatically  

### **For AI/ML Systems**
✅ **Clean Training Data** - No noise from typos/variations  
✅ **Semantic Understanding** - Controlled vocabulary enables relationship learning  
✅ **Reliable Embeddings** - Same term always generates same vector  
✅ **GraphRAG** - Explicit relationships enable multi-hop reasoning  

### **For Organizations**
✅ **Scalability** - Standards grow with organization needs  
✅ **Customization** - Adapt vocabularies to client requirements  
✅ **Knowledge Preservation** - Institutional knowledge codified in truth tables  
✅ **Competitive Advantage** - Higher data quality = better AI = better results  

---

## **Metrics for Success**

### **Data Quality Metrics**

| Metric | Current (Estimate) | Target |
|--------|-------------------|--------|
| % of fields using controlled vocabulary | 65% | 95% |
| % of data with typos/inconsistencies | 15% | <2% |
| % of queries needing ILIKE for variations | 30% | <5% |
| Foreign key coverage on lookup fields | 40% | 90% |
| User-reported "wrong dropdown option" | N/A | Track monthly |

### **User Experience Metrics**

| Metric | Current | Target |
|--------|---------|--------|
| Time to create relationship set | 3 min | 1 min |
| Errors during data entry | High | <5% of entries |
| User requests for "add to dropdown" | N/A | Track monthly |
| Training time for new users | High | 50% reduction |

### **System Performance Metrics**

| Metric | Current | Target |
|--------|---------|--------|
| Query accuracy (exact matches) | 70% | 95% |
| AI embedding consistency | Medium | High |
| Standards update propagation time | Manual | <1 hour automated |
| Compliance rule success rate | 60% | 90% |

---

## **Conclusion**

Truth-driven architecture is not just a technical pattern—it's a **commitment to data quality** that prevents costly mistakes, enables intelligent automation, and scales with organizational needs.

**The North Star:** Every piece of data in ACAD-GIS should trace back to an authoritative source of truth. If a user is typing it, we're doing it wrong.

**Current State:** 65% compliant - strong foundation in CAD Vocabulary and Reference Data Hub

**Target State:** 95% compliant - comprehensive vocabulary coverage with user-configurable standards

**Path Forward:** Systematic remediation of violations, starting with high-impact user-facing fields

---

**Document Version:** 1.0  
**Last Updated:** November 15, 2025  
**Maintained By:** System Architecture Team  
**Next Review:** Q1 2026 (with Phase 1 completion)

---

## **Appendix A: Quick Reference - Truth Table Index**

**CAD Vocabulary (14 tables):**
layer_standards • block_definitions • detail_standards • hatch_patterns • material_standards • note_standards • linetype_standards • color_standards • text_styles • plot_styles • dimension_styles • viewport_standards • annotation_standards • symbol_categories

**Reference Data Hub (13 tables):**
clients • municipalities • cad_standards • projects • discipline_codes • category_codes • object_type_codes • phase_codes • geometry_codes • attribute_codes • filterable_entity_columns • code_references • sheet_templates

**Specialized Vocabularies (4 tables):**
survey_code_library • specialized_tools_registry • project_usage_tracking • entity_registry

**Future Tables (6+ planned):**
relationship_set_naming_templates • survey_point_description_standards • survey_method_types • structure_type_standards • equipment_type_standards • project_attribute_vocabulary

**Total:** 31 current + 6 planned = **37 truth tables**
