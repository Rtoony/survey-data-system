# Standards Conformance Tracking Pattern

**Version:** 1.0  
**Date:** November 10, 2025  
**Status:** Prototype Implementation Complete

---

## Overview

The Standards Conformance Tracking system is a **foundational architectural pattern** for managing the relationship between approved standards and project-specific elements across the entire ACAD-GIS platform. This pattern applies to:

- **Sheet Notes** (✅ Implemented)
- **Blocks/Symbols** (Ready to implement)
- **Details** (Ready to implement)
- **Hatches** (Ready to implement)
- **Annotations** (Ready to implement)
- **Materials** (Ready to implement)

## The Problem This Solves

In real-world civil engineering and surveying firms:

1. **Standards provide consistency** - Firms maintain libraries of approved CAD elements
2. **Projects vary** - Every project has unique requirements (clients, jurisdictions, site conditions)
3. **Custom elements emerge** - Designers create non-standard elements when needed
4. **Patterns get lost** - Repeated custom elements don't get standardized
5. **Standards stagnate** - No evidence-based process for evolving standards

## The Solution

A **three-layer tracking system**:

### Layer 1: Source Tracking
Track whether each project element is:
- `standard` - Pulled from approved standards library
- `custom` - Created specifically for this project
- `modified_standard` - Based on a standard but modified
- `deprecated_standard` - Using an old standard that's been superseded

### Layer 2: Deviation Tracking
For non-standard elements, capture:
- **Category** - Why it deviates (client requirement, jurisdiction, cost optimization, etc.)
- **Reason** - Detailed explanation
- **Original standard reference** - What standard it's based on (if modified)

### Layer 3: Pattern Analysis & Standardization
Track custom element usage across projects to:
- Identify frequently-reused custom elements
- Flag standardization candidates
- Support evidence-based standards evolution

---

## Database Schema Pattern

### Core Components (Reusable Across All Element Types)

#### 1. Lookup Table: deviation_categories
```sql
CREATE TABLE deviation_categories (
    category_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_code VARCHAR(50) UNIQUE NOT NULL,
    category_name VARCHAR(100) NOT NULL,
    description TEXT,
    element_types TEXT[] DEFAULT ARRAY['note', 'block', 'detail', 'hatch', 'annotation'],
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Standard Categories:**
- `CLIENT_REQUIREMENT` - Client standards or preferences
- `JURISDICTION` - Local code/regulatory requirements
- `SITE_CONDITION` - Unique site conditions
- `COST_OPTIMIZATION` - Value engineering
- `DESIGN_PREFERENCE` - Designer preference
- `MATERIAL_AVAILABILITY` - Material substitution
- `IMPROVED_PRACTICE` - Better approach discovered
- `ERROR_CORRECTION` - Fixing a standard deficiency
- `LEGACY_PROJECT` - Inherited from previous work
- `OTHER` - Other reason

#### 2. Lookup Table: conformance_statuses
```sql
CREATE TABLE conformance_statuses (
    status_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status_code VARCHAR(50) UNIQUE NOT NULL,
    status_name VARCHAR(100) NOT NULL,
    description TEXT,
    color_hex VARCHAR(7) DEFAULT '#00ffff',
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Standard Statuses:**
- `FULL_COMPLIANCE` (green: #00ff88) - Fully complies with standards
- `MINOR_DEVIATION` (yellow: #ffaa00) - Minor modifications
- `MAJOR_DEVIATION` (orange: #ff6600) - Significant deviation
- `NON_STANDARD` (magenta: #ff00ff) - Completely custom
- `UNDER_REVIEW` (cyan: #00ffff) - Being evaluated

#### 3. Lookup Table: standardization_statuses
```sql
CREATE TABLE standardization_statuses (
    status_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status_code VARCHAR(50) UNIQUE NOT NULL,
    status_name VARCHAR(100) NOT NULL,
    description TEXT,
    workflow_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Workflow Statuses:**
1. `NOT_NOMINATED` - Not nominated for standardization
2. `NOMINATED` - Nominated as candidate
3. `UNDER_REVIEW` - Being reviewed by standards committee
4. `APPROVED` - Approved to become a standard
5. `STANDARDIZED` - Added to standards library
6. `REJECTED` - Not suitable for standardization
7. `DEFERRED` - Deferred for future consideration

#### 4. Cross-Project Usage Tracking: project_element_usages
```sql
CREATE TABLE project_element_usages (
    usage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    element_type VARCHAR(50) NOT NULL CHECK (element_type IN ('note', 'block', 'detail', 'hatch', 'annotation')),
    element_hash VARCHAR(64) NOT NULL,
    element_content_summary TEXT,
    project_id UUID REFERENCES projects(project_id),
    first_project_id UUID REFERENCES projects(project_id),
    times_reused INTEGER DEFAULT 1,
    project_count INTEGER DEFAULT 1,
    first_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_standardization_candidate BOOLEAN DEFAULT FALSE,
    attributes JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(element_type, element_hash, project_id)
);
```

### Per-Element-Type Extensions

Add these columns to each project element table (`project_sheet_notes`, `project_blocks`, `project_details`, etc.):

```sql
-- Source and Reference Tracking
source_type VARCHAR(50) DEFAULT 'custom' CHECK (source_type IN ('standard', 'custom', 'modified_standard', 'deprecated_standard')),
standard_reference_id UUID REFERENCES <standards_table>(id),

-- Deviation Tracking
deviation_category_id UUID REFERENCES deviation_categories(category_id),
deviation_reason TEXT,

-- Conformance Status
conformance_status_id UUID REFERENCES conformance_statuses(status_id),

-- Standardization Workflow
standardization_status_id UUID REFERENCES standardization_statuses(status_id),
standardization_note TEXT,

-- Usage Tracking
first_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
usage_count INTEGER DEFAULT 0,

-- Foreign Key Constraints
CONSTRAINT fk_<element>_deviation_category FOREIGN KEY (deviation_category_id) REFERENCES deviation_categories(category_id),
CONSTRAINT fk_<element>_conformance_status FOREIGN KEY (conformance_status_id) REFERENCES conformance_statuses(status_id),
CONSTRAINT fk_<element>_standardization_status FOREIGN KEY (standardization_status_id) REFERENCES standardization_statuses(status_id),
CONSTRAINT fk_<element>_standard_reference FOREIGN KEY (standard_reference_id) REFERENCES <standards_table>(id) ON DELETE SET NULL
```

---

## API Pattern

### 1. Get Lookup Data
```http
GET /api/conformance/deviation-categories
GET /api/conformance/statuses
```

Returns all deviation categories and conformance/standardization statuses.

### 2. Assign Standard to Project
```http
POST /api/project-<elements>/assign-standard
Content-Type: application/json

{
  "set_id": "<set_id>",
  "standard_<element>_id": "<standard_id>",
  "display_code": "XX-1"
}
```

**Creates project element from standard with:**
- `source_type` = 'standard'
- `conformance_status` = 'FULL_COMPLIANCE'
- `standardization_status` = 'NOT_NOMINATED'

### 3. Update Conformance Tracking
```http
PATCH /api/project-<elements>/<element_id>/conformance
Content-Type: application/json

{
  "deviation_category_id": "<category_id>",
  "deviation_reason": "Client requested custom legend format per their brand guidelines",
  "conformance_status_id": "<status_id>",
  "standardization_status_id": "<status_id>",
  "standardization_note": "Used on 3 recent projects, consider standardizing"
}
```

### 4. Get Elements with Conformance Data
```http
GET /api/project-<elements>?set_id=<set_id>
```

Returns elements with JOINs to all conformance lookup tables.

---

## UI Pattern

### Visual Indicators

**Color-Coded Badges:**
```jsx
{conformance_status_code === 'FULL_COMPLIANCE' && (
  <span className="badge" style={{backgroundColor: conformance_color}}>
    ✓ Standard
  </span>
)}

{conformance_status_code === 'NON_STANDARD' && (
  <span className="badge" style={{backgroundColor: conformance_color}}>
    ⚠ Custom
  </span>
)}

{conformance_status_code === 'MINOR_DEVIATION' && (
  <span className="badge" style={{backgroundColor: conformance_color}}>
    ≈ Modified
  </span>
)}
```

### Conformance Dashboard (Summary Metrics)

```jsx
<div className="conformance-metrics">
  <div className="metric">
    <div className="metric-label">Standards Compliance</div>
    <div className="metric-value">{compliancePercentage}%</div>
    <div className="metric-breakdown">
      <span className="badge-full-compliance">{fullComplianceCount} Full</span>
      <span className="badge-minor-deviation">{minorDeviationCount} Minor</span>
      <span className="badge-non-standard">{customCount} Custom</span>
    </div>
  </div>
  
  <div className="metric">
    <div className="metric-label">Standardization Candidates</div>
    <div className="metric-value">{candidateCount}</div>
  </div>
</div>
```

### Deviation Tracking Modal

```jsx
<Modal title="Track Deviation">
  <FormGroup label="Deviation Category">
    <Select options={deviationCategories} />
  </FormGroup>
  
  <FormGroup label="Reason">
    <TextArea placeholder="Explain why this element deviates from standards..." />
  </FormGroup>
  
  <FormGroup label="Conformance Status">
    <Select options={conformanceStatuses} />
  </FormGroup>
  
  <FormGroup label="Consider for Standardization?">
    <Checkbox label="Mark as standardization candidate" />
    <TextArea placeholder="Why should this become a standard?" />
  </FormGroup>
</Modal>
```

---

## Implementation Checklist (Per Element Type)

### Database Migration
- [ ] Add conformance tracking columns to `project_<elements>` table
- [ ] Add foreign key constraints
- [ ] Set default conformance statuses for existing records
- [ ] Create indexes on conformance status columns

### API Endpoints
- [ ] Add `/api/project-<elements>/assign-standard` endpoint
- [ ] Update `/api/project-<elements>` GET to include conformance JOINs
- [ ] Add `/api/project-<elements>/<id>/conformance` PATCH endpoint
- [ ] Add validation for all foreign key references

### UI Updates
- [ ] Add color-coded conformance badges to element lists
- [ ] Build "Assign Standard" button/modal
- [ ] Build "Track Deviation" modal
- [ ] Add conformance metrics dashboard
- [ ] Update element detail view to show conformance info

### Reporting & Analytics
- [ ] Conformance compliance report by project
- [ ] Standardization candidates report
- [ ] Deviation analysis by category
- [ ] Cross-project usage patterns

---

## Example: Applying to Blocks

### Database
```sql
ALTER TABLE project_blocks
ADD COLUMN source_type VARCHAR(50) DEFAULT 'custom',
ADD COLUMN standard_reference_id UUID REFERENCES block_definitions(block_id),
ADD COLUMN deviation_category_id UUID REFERENCES deviation_categories(category_id),
ADD COLUMN deviation_reason TEXT,
ADD COLUMN conformance_status_id UUID REFERENCES conformance_statuses(status_id),
ADD COLUMN standardization_status_id UUID REFERENCES standardization_statuses(status_id),
ADD COLUMN standardization_note TEXT,
ADD COLUMN first_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN usage_count INTEGER DEFAULT 0;
```

### API
```python
@app.route('/api/project-blocks/assign-standard', methods=['POST'])
def assign_standard_block():
    """Assign a standard block to a project"""
    # Same pattern as sheet notes
    pass

@app.route('/api/project-blocks/<block_id>/conformance', methods=['PATCH'])
def update_block_conformance(block_id):
    """Update conformance tracking for a project block"""
    # Same pattern as sheet notes
    pass
```

### UI
- Copy Sheet Note Manager conformance UI components
- Replace "note" with "block" throughout
- Reuse conformance modals and badges

---

## Production Hardening Considerations

### Additional Validation Needed (Requires Authentication)
1. **User authentication** - Implement user login/session management
2. **Project ownership** - Associate users with projects they can access
3. **Permission checks** - Verify user has permission to modify conformance tracking for their assigned projects
4. **Project-scoped API calls** - Add project_id to all API requests, validate against user's assigned projects
5. **Audit logging** - Track who made conformance status changes and when

**Current State:** Validation helpers (`validate_project_note_membership`, `validate_set_membership`) verify that notes/sets exist and return their project context, but without authentication there's no way to determine "which project the user should be accessing" to compare against.

### Performance Optimizations
1. **Indexed queries** - Add indexes on conformance_status_id, standardization_status_id
2. **Materialized views** - Pre-compute conformance metrics per project
3. **Caching** - Cache lookup tables (deviation categories, statuses)
4. **Batch operations** - Support bulk conformance updates

### Analytics Enhancements
1. **Time-series tracking** - Track conformance status changes over time
2. **Standardization pipeline** - Automated workflow for promoting custom→standard
3. **Pattern matching** - Use element_hash to detect similar custom elements across projects
4. **ML recommendations** - Suggest standardization candidates based on usage patterns

---

## Key Benefits

### For Designers
- **Use standards when applicable** - Easy assignment from library
- **Flexibility when needed** - Create custom elements without friction
- **Track deviations** - Document why custom elements were needed

### For Standards Managers
- **Evidence-based evolution** - See which custom elements get reused
- **Compliance visibility** - Know which projects deviate and why
- **Standardization pipeline** - Clear path from custom→candidate→standard

### For Principals/QA
- **Compliance metrics** - Instant visibility into standards adherence
- **Risk identification** - Flag projects with high deviation rates
- **Knowledge capture** - Never lose good custom solutions

---

## Implementation Status

### ✅ Completed (Sheet Notes Prototype)
- Database schema with 3 lookup tables
- Foreign key constraints for lookup tables
- API endpoints with lookup table validation
- Conformance tracking fields in `project_sheet_notes`

### ⚠️ Known Gaps (Production Hardening Required)
- **Authentication/Authorization**: No user authentication system exists, so API cannot determine "which project the user should access"
- **Project-scoped validation**: Validation helpers verify notes/sets exist and return project context, but endpoints don't compare against expected project_id (no way to determine expected project without auth)
- **Cross-project access**: Without authentication, any client can access any project's notes/sets if they know the UUIDs
- **Display code uniqueness**: Enforced per-set but not validated during assignment edge cases
- See "Production Hardening Considerations" section for authentication integration requirements

### 🔨 Ready to Implement
- UI components (conformance badges, modals, dashboard)
- Apply pattern to blocks, details, hatches, annotations
- Cross-project usage tracking
- Reporting and analytics

### 📋 Future Enhancements
- Production-level validation (project-scoped checks)
- Audit logging
- Automated standardization workflow
- ML-based pattern detection
- Time-series conformance trending

---

## Contact & Support

For questions about implementing this pattern for other element types, refer to:
- Database schema in `STANDARDS_CONFORMANCE_PATTERN.md` (this file)
- API reference in `app.py` (search for "CONFORMANCE TRACKING API")
- Sheet Note Manager implementation as reference example

**Pattern Version:** 1.0  
**Last Updated:** November 10, 2025
