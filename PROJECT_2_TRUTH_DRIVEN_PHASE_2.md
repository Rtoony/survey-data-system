# Project 2: Truth-Driven Architecture Phase 2 - Complete Migration

## Executive Summary
Expand the proven truth-driven architecture from 6 FK constraints to complete system-wide enforcement. Eliminate ALL free-text chaos by implementing remaining 15+ foreign key constraints, building comprehensive CRUD interfaces, and converting all UI forms to dropdown-driven architecture. This project builds directly on the successful Phase 1 foundation.

## Phase 1 Accomplishments (Already Complete)

### ✅ Proven FK Constraints (6 total)
1. `utility_lines.material` → `material_standards.material_code` (920 records)
2. `utility_structures.material` → `material_standards.material_code` (0 records)
3. `utility_structures.structure_type` → `structure_type_standards.type_code` (312 records)
4. `standard_notes.category_id` → `category_codes.category_id` (3 records)
5. `standard_notes.discipline_id` → `discipline_codes.discipline_id` (3 records)
6. `projects.client_id` → `clients.client_id` (0 records)

### ✅ Evidence-Based Success
- 1,235 existing records migrated without data loss
- All constraints tested with both invalid (blocked) and valid (allowed) values
- UI templates using FK-backed dropdowns (projects.html, standard_notes.html)
- Comprehensive documentation with verifiable SQL evidence
- Architect PASS approval confirming production-ready status

## Current State Assessment

### Remaining Free-Text Fields (Truth-Driven Architecture.md)
From the roadmap document, these are **PLANNED** but not yet implemented:

#### Survey Points (4 constraints)
- `survey_points.coord_system_id` → `coordinate_systems.system_id`
- `survey_points.description` → `survey_point_descriptions.description_code`
- Survey point attributes (multiple columns)
- Point classification codes

#### Utility Lines (3 constraints)
- `utility_lines.utility_system` (STORM, SEWER, WATER, etc.)
- `utility_lines.status` (EXISTING, PROPOSED, ABANDONED)
- `utility_lines.owner`

#### Utility Structures (2 constraints)
- `utility_structures.utility_system`
- `utility_structures.status`

#### CAD Blocks (1 constraint)
- `cad_blocks.block_category` (STRUCTURE, DETAIL, SYMBOL)

#### Relationship Sets (2 constraints - CRITICAL)
- `relationship_sets.set_name` → `relationship_set_naming_templates` (PLANNED)
- `relationship_sets.short_code` → template-based generation

#### Projects (3 constraints)
- `projects.municipality_id` → `municipalities.municipality_id`
- `projects.coord_system_id` → `coordinate_systems.system_id`
- `projects.project_status` (ACTIVE, COMPLETE, ON_HOLD, ARCHIVED)

### Missing CRUD Interfaces
- ❌ Structure Type Standards manager (no UI exists)
- ❌ Survey Point Descriptions manager
- ❌ Coordinate Systems manager
- ❌ Municipalities manager
- ❌ Material Standards manager (read-only currently)
- ❌ Relationship Set Naming Templates manager (table exists but no UI)

## Goals & Objectives

### Primary Goals
1. **Implement 13 Core FK Constraints**: Complete all remaining core constraints from roadmap (excluding obsolete drawings table, plus 2 potential additional)
2. **Build 8 CRUD Interfaces**: Full management UIs for all reference data
3. **Convert 12 UI Forms**: Replace free-text inputs with FK-backed dropdowns
4. **Automated Testing Suite**: Integration tests for all FK constraints
5. **Data Quality Dashboard**: Real-time constraint compliance monitoring

### Success Metrics
- 100% of text columns use FK constraints or have documented reason for free-text
- Zero free-text inputs in production UI forms (all dropdowns)
- All FK constraints tested with automated test suite
- Data quality dashboard shows 98%+ compliance
- Complete CRUD interfaces for all 20+ reference tables

## Implementation Phases

### Phase 1: Utility System & Status Standards (Week 1-2)

#### Database Changes
```sql
-- Create utility_system_standards table
CREATE TABLE utility_system_standards (
    system_code VARCHAR(20) PRIMARY KEY,
    system_name VARCHAR(100) NOT NULL,
    description TEXT,
    color_hex VARCHAR(7),
    display_order INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert initial data
INSERT INTO utility_system_standards (system_code, system_name, color_hex, display_order) VALUES
('STORM', 'Storm Drainage', '#0066CC', 1),
('SEWER', 'Sanitary Sewer', '#8B4513', 2),
('WATER', 'Water Distribution', '#0099FF', 3),
('RECLAIM', 'Reclaimed Water', '#9933FF', 4),
('GAS', 'Natural Gas', '#FFCC00', 5),
('ELECTRIC', 'Electric', '#FF0000', 6),
('TELECOM', 'Telecommunications', '#00CC00', 7);

-- Create status_standards table
CREATE TABLE status_standards (
    status_code VARCHAR(20) PRIMARY KEY,
    status_name VARCHAR(100) NOT NULL,
    description TEXT,
    applies_to VARCHAR(50), -- 'UTILITY', 'DRAWING', 'PROJECT'
    display_order INTEGER,
    is_active BOOLEAN DEFAULT true
);

-- Insert initial data
INSERT INTO status_standards (status_code, status_name, applies_to, display_order) VALUES
('EXISTING', 'Existing', 'UTILITY', 1),
('PROPOSED', 'Proposed', 'UTILITY', 2),
('ABANDONED', 'Abandoned', 'UTILITY', 3),
('ACTIVE', 'Active', 'PROJECT', 1),
('COMPLETE', 'Complete', 'PROJECT', 2),
('ON_HOLD', 'On Hold', 'PROJECT', 3),
('ARCHIVED', 'Archived', 'PROJECT', 4),
('DRAFT', 'Draft', 'DRAWING', 1),
('REVIEW', 'Under Review', 'DRAWING', 2),
('APPROVED', 'Approved', 'DRAWING', 3);

-- Add FK constraints
ALTER TABLE utility_lines 
    ADD CONSTRAINT fk_utility_lines_system 
    FOREIGN KEY (utility_system) 
    REFERENCES utility_system_standards(system_code) 
    ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE utility_structures 
    ADD CONSTRAINT fk_utility_structures_system 
    FOREIGN KEY (utility_system) 
    REFERENCES utility_system_standards(system_code) 
    ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE utility_lines 
    ADD CONSTRAINT fk_utility_lines_status 
    FOREIGN KEY (status) 
    REFERENCES status_standards(status_code) 
    ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE utility_structures 
    ADD CONSTRAINT fk_utility_structures_status 
    FOREIGN KEY (status) 
    REFERENCES status_standards(status_code) 
    ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE projects 
    ADD CONSTRAINT fk_projects_status 
    FOREIGN KEY (project_status) 
    REFERENCES status_standards(status_code) 
    ON UPDATE CASCADE ON DELETE SET NULL;
```

#### UI Components
1. Build `utility_system_standards.html` CRUD interface
2. Build `status_standards.html` CRUD interface
3. Update `gravity_pipe_manager.html` with system/status dropdowns
4. Update `pressure_pipe_manager.html` with system/status dropdowns
5. Update `utility_structure_manager.html` with system/status dropdowns

**Deliverables**: 5 FK constraints, 2 CRUD interfaces, 3 updated manager UIs

### Phase 2: Survey Point Standards (Week 3-4)

#### Database Changes
```sql
-- Already exists: coordinate_systems, survey_point_descriptions
-- Add FK constraints

ALTER TABLE survey_points 
    ADD CONSTRAINT fk_survey_points_coord_system 
    FOREIGN KEY (coord_system_id) 
    REFERENCES coordinate_systems(system_id) 
    ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE survey_points 
    ADD CONSTRAINT fk_survey_points_description 
    FOREIGN KEY (description) 
    REFERENCES survey_point_descriptions(description_code) 
    ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE projects 
    ADD CONSTRAINT fk_projects_coord_system 
    FOREIGN KEY (coord_system_id) 
    REFERENCES coordinate_systems(system_id) 
    ON UPDATE CASCADE ON DELETE SET NULL;
```

#### UI Components
1. Build `coordinate_systems.html` CRUD interface
2. Enhance `survey_point_descriptions.html` (already has basic UI)
3. Update `survey_point_manager.html` with coordinate system dropdown
4. Update `batch_point_import.html` with enhanced coord system selection
5. Update `projects.html` with coord_system_id dropdown

**Deliverables**: 3 FK constraints, 2 CRUD interfaces, 4 updated UIs

### Phase 3: Block Standards (Week 5)

**NOTE**: The `drawings` table was removed in Migration 012 in favor of "Projects → Entities" architecture. Drawing-related constraints are no longer applicable.

#### Database Changes
```sql
-- Create block_category_standards table
CREATE TABLE block_category_standards (
    category_code VARCHAR(20) PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL,
    description TEXT,
    display_order INTEGER
);

INSERT INTO block_category_standards (category_code, category_name, display_order) VALUES
('STRUCTURE', 'Utility Structures', 1),
('DETAIL', 'Detail Callouts', 2),
('SYMBOL', 'Symbols & Markers', 3),
('BORDER', 'Title Blocks & Borders', 4),
('ANNOTATION', 'Annotation Elements', 5);

-- Add FK constraint
ALTER TABLE cad_blocks 
    ADD CONSTRAINT fk_cad_blocks_category 
    FOREIGN KEY (block_category) 
    REFERENCES block_category_standards(category_code) 
    ON UPDATE CASCADE ON DELETE SET NULL;
```

#### UI Components
1. Build `block_category_standards.html` CRUD interface
2. Update CAD block import tools with category dropdown

**Deliverables**: 1 FK constraint, 1 CRUD interface

### Phase 4: Relationship Set Naming Templates (Week 6-7)

**CRITICAL**: This is marked PLANNED in current system but not implemented.

#### Database Changes
```sql
-- Table already exists: relationship_set_naming_templates
-- Add FK constraint
ALTER TABLE relationship_sets 
    ADD CONSTRAINT fk_relationship_sets_template 
    FOREIGN KEY (template_id) 
    REFERENCES relationship_set_naming_templates(template_id) 
    ON UPDATE CASCADE ON DELETE SET NULL;

-- Add generated columns for set_name and short_code
ALTER TABLE relationship_sets 
    ADD COLUMN generated_name TEXT,
    ADD COLUMN generated_short_code VARCHAR(20);

-- Create trigger to auto-generate names from template
CREATE OR REPLACE FUNCTION generate_relationship_set_name()
RETURNS TRIGGER AS $$
BEGIN
    -- Logic to replace tokens in template with actual values
    -- Example: "{SYSTEM}-{TYPE}-{SEQ}" → "STORM-BASIN-001"
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

#### UI Components
1. Build `relationship_set_naming_templates.html` full CRUD (currently missing)
2. Update `relationship_sets.html` to use template selection instead of free-text
3. Add template token replacement preview
4. Implement auto-incrementing sequence numbers per template

**Deliverables**: 1 FK constraint, template-based name generation, 2 UIs

### Phase 5: Municipality & Owner Standards (Week 8)

#### Database Changes
```sql
-- Municipalities table already exists
-- Add owner_standards table
CREATE TABLE owner_standards (
    owner_code VARCHAR(20) PRIMARY KEY,
    owner_name VARCHAR(100) NOT NULL,
    owner_type VARCHAR(50), -- 'MUNICIPAL', 'PRIVATE', 'HOA', 'UTILITY'
    contact_info TEXT,
    is_active BOOLEAN DEFAULT true
);

-- Add FK constraints
ALTER TABLE projects 
    ADD CONSTRAINT fk_projects_municipality 
    FOREIGN KEY (municipality_id) 
    REFERENCES municipalities(municipality_id) 
    ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE utility_lines 
    ADD CONSTRAINT fk_utility_lines_owner 
    FOREIGN KEY (owner) 
    REFERENCES owner_standards(owner_code) 
    ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE utility_structures 
    ADD CONSTRAINT fk_utility_structures_owner 
    FOREIGN KEY (owner) 
    REFERENCES owner_standards(owner_code) 
    ON UPDATE CASCADE ON DELETE SET NULL;
```

#### UI Components
1. Build `municipalities.html` CRUD interface
2. Build `owner_standards.html` CRUD interface
3. Update `projects.html` with municipality dropdown
4. Update utility managers with owner dropdown

**Deliverables**: 3 FK constraints, 2 CRUD interfaces

### Phase 6: Automated Testing Suite (Week 9)

#### Test Infrastructure
```python
# tests/test_fk_constraints.py
import pytest
from database.db_connection import get_db_connection

class TestFKConstraints:
    def test_utility_lines_material_invalid(self):
        """FK should block invalid material"""
        conn = get_db_connection()
        with pytest.raises(Exception, match="fk_utility_lines_material"):
            conn.execute("""
                INSERT INTO utility_lines (project_id, material)
                VALUES (%s, 'INVALID_MATERIAL')
            """, (test_project_id,))
    
    def test_utility_lines_material_valid(self):
        """FK should allow valid material"""
        conn = get_db_connection()
        result = conn.execute("""
            INSERT INTO utility_lines (project_id, material)
            VALUES (%s, 'PVC')
            RETURNING line_id
        """, (test_project_id,))
        assert result.rowcount == 1
```

#### Test Coverage
- All 19 core FK constraints (6 existing + 13 new)
- Both invalid (should block) and valid (should allow) cases
- CASCADE update behavior
- SET NULL delete behavior
- Migration rollback safety

**Deliverables**: 38 automated tests (2 per constraint)

### Phase 7: Data Quality Dashboard (Week 10)

#### Web Interface
1. **FK Compliance Dashboard**
   - Show % of records with valid FK references
   - Highlight orphaned records (NULL FK values)
   - Track FK constraint violations over time

2. **Reference Data Health**
   - Count of active vs inactive reference codes
   - Unused reference codes (never referenced)
   - Missing reference codes (requested but not in table)

3. **UI Form Audit**
   - List all UI forms and their input types
   - Flag any remaining free-text inputs
   - Track dropdown usage statistics

**Deliverables**: Interactive dashboard with real-time metrics

## Complete FK Constraint List (19 Core Total)

### Existing (6)
1. utility_lines.material → material_standards
2. utility_structures.material → material_standards
3. utility_structures.structure_type → structure_type_standards
4. standard_notes.category_id → category_codes
5. standard_notes.discipline_id → discipline_codes
6. projects.client_id → clients

### New Utility System (4)
7. utility_lines.utility_system → utility_system_standards
8. utility_structures.utility_system → utility_system_standards
9. utility_lines.status → status_standards
10. utility_structures.status → status_standards

### New Projects (3)
11. projects.municipality_id → municipalities
12. projects.coord_system_id → coordinate_systems
13. projects.project_status → status_standards

### New Survey (2)
14. survey_points.coord_system_id → coordinate_systems
15. survey_points.description → survey_point_descriptions

### New Blocks (1)
16. cad_blocks.block_category → block_category_standards

### New Relationship Sets (1)
17. relationship_sets.template_id → relationship_set_naming_templates

### New Owners (2)
18. utility_lines.owner → owner_standards
19. utility_structures.owner → owner_standards

### Potential Additional (2+)
20. bmp_structures.bmp_type → bmp_type_standards (if not already constrained)
21. survey_codes.code_category → survey_code_categories

**Total Planned: 19 FK constraints (6 existing + 13 new core + 2 potential)**
**Core Deliverables: 19 FK constraints (6 existing + 13 new)**

## CRUD Interface Requirements

All CRUD interfaces should follow this pattern:

### Standard CRUD Features
1. **List View**: Sortable table with search/filter
2. **Create Form**: Modal or dedicated page with validation
3. **Edit Form**: Pre-populated with existing values
4. **Delete**: Soft delete (is_active=false) with FK dependency check
5. **Bulk Actions**: Enable/disable multiple, export to CSV

### UI Consistency
- Mission Control design system (cyan/neon theme)
- Form validation with clear error messages
- Success/error toasts for user feedback
- Responsive layout for all screen sizes
- Keyboard shortcuts for power users

## Migration Strategy

### Data Migration Process
1. **Audit Existing Data**: Find unique values in free-text columns
2. **Create Standards Records**: Insert into new reference tables
3. **Data Mapping**: Map existing values to standard codes
4. **Backfill FKs**: Update existing records with FK values
5. **Add Constraint**: Apply FK constraint after data is clean
6. **Verify**: Run test suite to confirm constraint works

### Example Migration Script
```sql
-- Step 1: Find existing utility systems
SELECT DISTINCT utility_system, COUNT(*)
FROM utility_lines
WHERE utility_system IS NOT NULL
GROUP BY utility_system
ORDER BY COUNT(*) DESC;

-- Step 2: Map to standards (manual review required)
UPDATE utility_lines SET utility_system = 'STORM' WHERE utility_system = 'SD';
UPDATE utility_lines SET utility_system = 'SEWER' WHERE utility_system = 'SS';

-- Step 3: Add FK constraint
ALTER TABLE utility_lines ADD CONSTRAINT fk_utility_lines_system...
```

## Risk Assessment

### Technical Risks
- **Data migration complexity**: Some free-text values may not map cleanly
  - **Mitigation**: Create "OTHER" or "UNKNOWN" codes for edge cases
- **Existing UI dependencies**: Forms may have hardcoded values
  - **Mitigation**: Search codebase for all input fields, update systematically
- **Performance impact**: More FK checks on INSERT/UPDATE
  - **Mitigation**: FK lookups are fast with proper indexes

### Data Quality Risks
- **Legacy data inconsistency**: Historical records may have invalid codes
  - **Mitigation**: Clean data before adding constraints, document exceptions
- **User resistance**: Team may prefer free-text flexibility
  - **Mitigation**: Show value of controlled vocabulary (better reports, search, AI)

## Success Criteria

### Must Have
- ✅ All 19 core FK constraints implemented and tested
- ✅ 8+ CRUD interfaces built and functional
- ✅ Zero free-text inputs in production UI forms
- ✅ All existing data successfully migrated
- ✅ Automated test suite passing

### Should Have
- ✅ Data quality dashboard operational
- ✅ All migrations documented with SQL evidence
- ✅ UI forms follow consistent design patterns
- ✅ Performance benchmarks met (<100ms for FK checks)

### Nice to Have
- ✅ Bulk import tools for reference data (CSV upload)
- ✅ Reference data versioning/history
- ✅ API endpoints for all reference tables
- ✅ Documentation for adding new FK constraints

## Timeline Summary
- **Phase 1**: Weeks 1-2 (Utility System/Status)
- **Phase 2**: Weeks 3-4 (Survey Points)
- **Phase 3**: Week 5 (Blocks)
- **Phase 4**: Weeks 6-7 (Relationship Sets)
- **Phase 5**: Week 8 (Municipalities/Owners)
- **Phase 6**: Week 9 (Automated Tests)
- **Phase 7**: Week 10 (Quality Dashboard)

**Total Duration**: 10 weeks

## ROI & Business Value
- **Data Consistency**: Eliminate typos and invalid codes forever
- **AI Enablement**: Clean, structured data enables better AI/ML
- **Reporting**: Accurate aggregations and analytics
- **User Experience**: Dropdowns faster than typing, prevent errors
- **Maintenance**: Centralized standards easier to update
- **Compliance**: Audit trail for all standard changes
- **Scalability**: Add new codes without code changes
