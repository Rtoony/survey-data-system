# ACAD-GIS Project Assignment Model

## Overview

This document explains how the ACAD-GIS system manages the relationship between **standards library** (shared, read-only templates) and **project instances** (project-specific, customizable copies). It covers assignment, modification tracking, deviation analysis, and the standardization feedback loop.

---

## Core Concept: Dual Identity System

### The Fundamental Pattern

Every standardized element exists in **two forms**:

```
┌──────────────────────────────────────────────────────────────┐
│                    STANDARDS LIBRARY                         │
│  - Shared across ALL projects                                │
│  - Read-only (cannot be modified directly)                   │
│  - Serves as template/source of truth                        │
│  - Version-controlled                                        │
└──────────────────────────────────────────────────────────────┘
                          ↓ (Assignment)
┌──────────────────────────────────────────────────────────────┐
│                    PROJECT INSTANCE                          │
│  - Belongs to ONE project                                    │
│  - Can be customized (creates modified copy)                 │
│  - Tracks deviation from standard                            │
│  - Links back to source standard                             │
└──────────────────────────────────────────────────────────────┘
```

### Why This Matters

**Problem:** Projects need to customize standards, but direct modification breaks reusability.

**Solution:** 
1. Assign standard to project (creates read-only reference)
2. If customization needed, create modified copy (new record)
3. Track what changed and why (deviation metadata)
4. Maintain link to original standard (traceability)

---

## Database Schema Pattern

### Standard Library Table

```sql
CREATE TABLE standard_notes (
    note_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Standard identification
    note_code VARCHAR(50) UNIQUE NOT NULL,
    note_title VARCHAR(500),
    note_text TEXT,
    
    -- Classification
    category VARCHAR(100),
    discipline VARCHAR(50),
    
    -- Entity registry link
    entity_id UUID REFERENCES standards_entities(entity_id),
    
    -- AI optimization
    quality_score NUMERIC(5,2) DEFAULT 0.00,
    search_vector TSVECTOR,
    tags TEXT[],
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Characteristics:**
- ✅ Shared across all projects
- ✅ Read-only in project context
- ✅ Single source of truth
- ✅ No project-specific data

### Project Assignment Table

```sql
CREATE TABLE project_notes (
    project_note_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Project context
    project_id UUID REFERENCES projects(project_id) NOT NULL,
    set_id UUID,  -- Group related notes (e.g., sheet set)
    
    -- Standard reference (CRITICAL!)
    standard_note_id UUID REFERENCES standard_notes(note_id),
    standard_reference_id UUID,  -- Original standard if this is modified
    
    -- Display information
    display_code VARCHAR(50) NOT NULL,
    custom_title VARCHAR(500),
    custom_text TEXT,
    
    -- Source tracking (CRITICAL!)
    source_type VARCHAR(50) CHECK (source_type IN (
        'standard',           -- Unmodified standard reference
        'modified_standard',  -- Modified copy of standard
        'custom',            -- Fully custom (no standard source)
        'deprecated_standard' -- Old standard kept for history
    )) NOT NULL,
    
    is_modified BOOLEAN DEFAULT FALSE,
    
    -- Deviation tracking (required for modified_standard)
    deviation_category_id UUID REFERENCES deviation_categories(category_id),
    deviation_reason TEXT,
    conformance_status_id UUID REFERENCES conformance_statuses(status_id),
    
    -- Standardization tracking
    standardization_status_id UUID REFERENCES standardization_statuses(status_id),
    standardization_note TEXT,
    
    -- Usage tracking
    sort_order INTEGER,
    first_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    
    -- AI optimization
    search_vector TSVECTOR,
    quality_score NUMERIC(5,2) DEFAULT 0.00,
    
    -- Unique within a set
    UNIQUE(set_id, display_code)
);
```

**Characteristics:**
- ✅ Project-specific instance
- ✅ Can be modified (creates new record with `source_type = 'modified_standard'`)
- ✅ Tracks deviation from standard
- ✅ Links to original standard

---

## Source Types Explained

### 1. `source_type = 'standard'`

**Meaning:** Unmodified reference to standards library.

**Properties:**
- `standard_note_id` points to standards library
- `standard_reference_id` is NULL (this IS the standard)
- `custom_title` and `custom_text` are NULL (use standard's values)
- `is_modified = FALSE`
- **Cannot be edited** (API returns 403 Forbidden)

**Display:**
```
┌─────────────────────────────────────────┐
│ 📌 1.01 - Storm Drain Inlet Type A      │
│ ⭐ STANDARD                              │
│                                         │
│ [Text from standard_notes.note_text]    │
│                                         │
│ [🔧 Modify]  [🗑️ Remove from Project]   │
└─────────────────────────────────────────┘
```

### 2. `source_type = 'modified_standard'`

**Meaning:** Customized copy of a standard.

**Properties:**
- `standard_note_id` points to current standard definition
- `standard_reference_id` points to ORIGINAL standard (lineage)
- `custom_title` and/or `custom_text` contain modified values
- `is_modified = TRUE`
- `deviation_category_id`, `deviation_reason`, `conformance_status_id` are **required**
- **Can be edited** (modifies custom fields)

**Display:**
```
┌─────────────────────────────────────────┐
│ 📌 1.01-M - Storm Drain Inlet Type A    │
│ 🔧 MODIFIED                              │
│                                         │
│ [Modified custom text]                  │
│                                         │
│ Deviation: CLIENT_PREFERENCE            │
│ Reason: Client requested 6" deeper      │
│ Conformance: MINOR_DEVIATION            │
│                                         │
│ [✏️ Edit]  [📋 View Original Standard]  │
└─────────────────────────────────────────┘
```

### 3. `source_type = 'custom'`

**Meaning:** Fully custom note, no standard source.

**Properties:**
- `standard_note_id` is NULL (no standard source)
- `standard_reference_id` is NULL
- `custom_title` and `custom_text` contain all data
- `is_modified = FALSE` (nothing to deviate from)
- **Can be edited** (full control)

**Display:**
```
┌─────────────────────────────────────────┐
│ 📌 99.01 - Project-Specific Note        │
│ ✏️ CUSTOM                                │
│                                         │
│ [Custom text written by user]           │
│                                         │
│ [✏️ Edit]  [🗑️ Delete]                  │
└─────────────────────────────────────────┘
```

### 4. `source_type = 'deprecated_standard'`

**Meaning:** Old standard still in use but superseded.

**Properties:**
- `standard_note_id` may be NULL if standard was deleted
- `standard_reference_id` tracks original source
- Kept for historical record (drawing packages)
- **Cannot be assigned to new projects**

---

## Assignment Workflow

### Step 1: Assign Standard to Project

**User Action:** "Add Standard Note 1.01 to Project ABC"

**Backend Process:**
```python
def assign_standard_to_project(project_id, standard_note_id):
    # 1. Verify standard exists
    standard = get_standard_note(standard_note_id)
    if not standard:
        raise ValueError("Standard not found")
    
    # 2. Check if already assigned
    existing = execute_query("""
        SELECT 1 FROM project_notes
        WHERE project_id = %s AND standard_note_id = %s AND is_active = TRUE
    """, (project_id, standard_note_id))
    
    if existing:
        raise ValueError("Standard already assigned to project")
    
    # 3. Get next display code
    next_code = get_next_note_code(project_id)  # e.g., "1.01"
    
    # 4. Create project instance (as unmodified standard)
    project_note_id = str(uuid.uuid4())
    
    execute_query("""
        INSERT INTO project_notes
        (project_note_id, project_id, standard_note_id, standard_reference_id,
         display_code, source_type, is_modified, first_used_at, last_used_at)
        VALUES (%s, %s, %s, NULL, %s, 'standard', FALSE, 
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """, (project_note_id, project_id, standard_note_id, next_code))
    
    return project_note_id
```

**Result:**
- Project now has reference to standard
- No customization yet
- Read-only in project context

### Step 2: User Wants to Customize

**User Action:** Clicks "🔧 Modify" button on standard note

**UI Workflow:**
1. **Show Modal:** "Create Modified Copy"
2. **Require Deviation Tracking:**
   - Why are you modifying? (dropdown: client preference, site condition, etc.)
   - Explain the change (text area)
   - How much deviation? (dropdown: minor, major, non-compliant)
3. **Optional Customization:**
   - Custom title (defaults to standard title)
   - Custom text (defaults to standard text)
4. **Create Modified Copy**

**Backend Process (CRITICAL PATTERN):**
```python
def create_modified_copy(project_note_id, deviation_data):
    # 1. Verify project note exists and is a standard
    item = get_project_note(project_note_id)
    if not item:
        raise ValueError("Note not found")
    
    if item['source_type'] != 'standard':
        raise ValueError("Can only create modified copies from standards")
    
    # 2. Validate deviation tracking (REQUIRED!)
    if not all([
        deviation_data.get('deviation_category'),
        deviation_data.get('deviation_reason'),
        deviation_data.get('conformance_status')
    ]):
        raise ValueError("Deviation tracking is required")
    
    # 3. Lookup deviation category and conformance status
    category = get_deviation_category(deviation_data['deviation_category'])
    status = get_conformance_status(deviation_data['conformance_status'])
    
    # 4. Get standard data
    standard = get_standard_note(item['standard_note_id'])
    
    # 5. Generate unique display code (add -M suffix)
    base_code = item['display_code']  # "1.01"
    new_code = f"{base_code}-M"       # "1.01-M"
    
    # Handle collisions
    counter = 1
    while code_exists(item['set_id'], new_code):
        counter += 1
        new_code = f"{base_code}-M{counter}"  # "1.01-M2"
    
    # 6. Create modified copy
    new_id = str(uuid.uuid4())
    
    execute_query("""
        INSERT INTO project_notes
        (project_note_id, project_id, set_id, 
         standard_note_id, standard_reference_id, display_code,
         custom_title, custom_text, 
         source_type, is_modified,
         deviation_category_id, deviation_reason, conformance_status_id,
         first_used_at, last_used_at)
        VALUES (%s, %s, %s,
                %s, %s, %s,
                %s, %s,
                'modified_standard', TRUE,
                %s, %s, %s,
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """, (
        new_id, item['project_id'], item['set_id'],
        item['standard_note_id'], item['standard_note_id'], new_code,
        deviation_data.get('custom_title') or standard['note_title'],
        deviation_data.get('custom_text') or standard['note_text'],
        category['category_id'], deviation_data['deviation_reason'], 
        status['status_id']
    ))
    
    # 7. Return new modified copy (with all joined data for client)
    return get_project_note_with_metadata(new_id)
```

**Result:**
- New record created with `source_type = 'modified_standard'`
- Original standard reference remains unchanged
- Both appear in project (user can remove original if desired)
- Deviation is tracked for analysis

---

## Deviation Tracking System

### Deviation Categories

**Purpose:** Classify WHY a standard was modified.

```sql
CREATE TABLE deviation_categories (
    category_id UUID PRIMARY KEY,
    category_code VARCHAR(50) UNIQUE NOT NULL,
    category_name VARCHAR(100) NOT NULL,
    description TEXT,
    element_types TEXT[] DEFAULT ARRAY['note', 'block', 'detail', 'hatch'],
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0
);

INSERT INTO deviation_categories (category_code, category_name, description) VALUES
('MATERIAL_AVAILABILITY', 'Material Not Available', 'Standard material substituted'),
('CLIENT_PREFERENCE', 'Client Requested Change', 'Client-specific requirements'),
('SITE_CONDITION', 'Site-Specific Requirement', 'Unique site conditions'),
('CODE_REQUIREMENT', 'Building Code Requirement', 'Jurisdictional requirements'),
('COST_OPTIMIZATION', 'Cost Reduction', 'Value engineering'),
('DESIGN_PREFERENCE', 'Designer Preference', 'Designer choice'),
('IMPROVED_PRACTICE', 'Better Approach Discovered', 'Improved standard'),
('ERROR_CORRECTION', 'Fixing Standard Deficiency', 'Standard has issues'),
('LEGACY_PROJECT', 'Inherited from Previous Work', 'Legacy compatibility'),
('OTHER', 'Other Reason', 'Other deviation reason');
```

### Conformance Statuses

**Purpose:** Classify HOW MUCH a standard was modified.

```sql
CREATE TABLE conformance_statuses (
    status_id UUID PRIMARY KEY,
    status_code VARCHAR(50) UNIQUE NOT NULL,
    status_name VARCHAR(100) NOT NULL,
    description TEXT,
    color_hex VARCHAR(7) DEFAULT '#00ffff',
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0
);

INSERT INTO conformance_statuses (status_code, status_name, description, color_hex) VALUES
('COMPLIANT', 'Fully Compliant', 'Minor wording changes only', '#00ff88'),
('MINOR_DEVIATION', 'Minor Deviation', 'Same intent, different approach', '#ffaa00'),
('MAJOR_DEVIATION', 'Major Deviation', 'Significantly different', '#ff6600'),
('NON_COMPLIANT', 'Non-Compliant', 'Completely custom solution', '#ff00ff');
```

### Analytics Queries

**Most Common Deviation Reasons:**
```sql
SELECT 
    dc.category_name,
    COUNT(*) AS modification_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS percentage
FROM project_notes pn
JOIN deviation_categories dc ON pn.deviation_category_id = dc.category_id
WHERE pn.source_type = 'modified_standard'
GROUP BY dc.category_name
ORDER BY modification_count DESC;
```

**Most Modified Standards:**
```sql
SELECT 
    sn.note_code,
    sn.note_title,
    COUNT(DISTINCT pn.project_id) AS project_count,
    COUNT(*) AS modification_count
FROM standard_notes sn
JOIN project_notes pn ON pn.standard_reference_id = sn.note_id
WHERE pn.source_type = 'modified_standard'
GROUP BY sn.note_id, sn.note_code, sn.note_title
ORDER BY modification_count DESC
LIMIT 20;
```

---

## Standardization Feedback Loop

### The Problem

Projects create modified copies. Some modifications are good ideas that should become standards!

### Standardization Workflow

```sql
CREATE TABLE standardization_statuses (
    status_id UUID PRIMARY KEY,
    status_code VARCHAR(50) UNIQUE NOT NULL,
    status_name VARCHAR(100) NOT NULL,
    description TEXT,
    workflow_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);

INSERT INTO standardization_statuses (status_code, status_name, workflow_order) VALUES
('NOT_NOMINATED', 'Not Nominated', 0),
('NOMINATED', 'Nominated for Standardization', 1),
('UNDER_REVIEW', 'Under Review', 2),
('APPROVED', 'Approved', 3),
('STANDARDIZED', 'Added to Standards Library', 4),
('REJECTED', 'Rejected', 5),
('DEFERRED', 'Deferred', 6);
```

### Workflow Steps

**1. Nominate Modified Copy**

User clicks "💡 Nominate for Standardization" on a modified note.

```sql
UPDATE project_notes
SET standardization_status_id = (
    SELECT status_id FROM standardization_statuses 
    WHERE status_code = 'NOMINATED'
),
    standardization_note = 'This approach worked well on 3 projects'
WHERE project_note_id = %s;
```

**2. Review Dashboard**

Standards committee sees all nominated items:

```sql
SELECT 
    pn.project_note_id,
    pn.display_code,
    pn.custom_title,
    p.project_name,
    ss.status_name,
    pn.standardization_note,
    pn.deviation_reason
FROM project_notes pn
JOIN projects p ON pn.project_id = p.project_id
JOIN standardization_statuses ss ON pn.standardization_status_id = ss.status_id
WHERE ss.status_code IN ('NOMINATED', 'UNDER_REVIEW', 'APPROVED')
ORDER BY ss.workflow_order, pn.last_used_at DESC;
```

**3. Approve & Standardize**

Committee approves → Create new standard in library:

```python
def standardize_modified_copy(project_note_id):
    # 1. Get modified copy
    modified = get_project_note(project_note_id)
    
    # 2. Create new standard in library
    new_standard_id = str(uuid.uuid4())
    
    execute_query("""
        INSERT INTO standard_notes
        (note_id, note_code, note_title, note_text, category, entity_id)
        VALUES (%s, %s, %s, %s, %s, gen_random_uuid())
    """, (
        new_standard_id,
        generate_new_standard_code(),
        modified['custom_title'],
        modified['custom_text'],
        modified['category']
    ))
    
    # 3. Update status
    execute_query("""
        UPDATE project_notes
        SET standardization_status_id = (
            SELECT status_id FROM standardization_statuses 
            WHERE status_code = 'STANDARDIZED'
        )
        WHERE project_note_id = %s
    """, (project_note_id,))
    
    return new_standard_id
```

---

## Project-Specific Reference Data

### Assignment Tables (Many-to-Many)

Projects can have many clients, vendors, municipalities, coordinate systems, etc.

```sql
CREATE TABLE project_clients (
    mapping_id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(project_id),
    client_id UUID REFERENCES clients(client_id),
    is_primary BOOLEAN DEFAULT FALSE,
    relationship_notes TEXT,
    display_order INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE project_vendors (
    mapping_id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(project_id),
    vendor_id UUID REFERENCES vendors(vendor_id),
    vendor_role VARCHAR(100),  -- "Surveyor", "Geotechnical", etc.
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE project_municipalities (
    mapping_id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(project_id),
    municipality_id UUID REFERENCES municipalities(municipality_id),
    jurisdiction_type VARCHAR(100),  -- "City", "County", "Water District"
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE project_coordinate_systems (
    mapping_id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(project_id),
    coordinate_system_id UUID REFERENCES coordinate_systems(crs_id),
    usage_type VARCHAR(100),  -- "Survey", "Design", "Construction"
    is_primary BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE
);
```

---

## Summary: The Complete Pattern

```
┌──────────────────────────────────────────────────────────────────┐
│  1. Standard Library (Read-Only, Shared)                        │
│     - block_definitions                                          │
│     - detail_standards                                           │
│     - standard_notes                                             │
│     - material_standards                                         │
└──────────────────────────────────────────────────────────────────┘
                          ↓ (Assign to Project)
┌──────────────────────────────────────────────────────────────────┐
│  2. Project Assignment (source_type = 'standard')                │
│     - Unmodified reference                                       │
│     - Read-only in project context                               │
│     - Links to standard library                                  │
└──────────────────────────────────────────────────────────────────┘
                          ↓ (User Modifies)
┌──────────────────────────────────────────────────────────────────┐
│  3. Modified Copy (source_type = 'modified_standard')            │
│     - New record created                                         │
│     - Custom title/text                                          │
│     - Deviation tracking: why, how much                          │
│     - Maintains link to original standard                        │
└──────────────────────────────────────────────────────────────────┘
                          ↓ (If Good)
┌──────────────────────────────────────────────────────────────────┐
│  4. Standardization Feedback Loop                               │
│     - Nominate modified copy                                     │
│     - Review by standards committee                              │
│     - Approve → Add to standards library                         │
│     - Continuous improvement                                     │
└──────────────────────────────────────────────────────────────────┘
```

**Key Benefits:**
1. **Protect Standards:** Standards remain unchanged, reusable across projects
2. **Enable Customization:** Projects can modify as needed
3. **Track Deviations:** Understand why and how much standards are modified
4. **Continuous Improvement:** Good modifications become new standards
5. **Full Traceability:** Always know the lineage of project-specific data
