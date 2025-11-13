# ACAD-GIS Standards Mapping Framework

## Overview

The Standards Mapping Framework is an 11-table database schema that enables **bidirectional translation** between messy client DXF files and clean, standardized database records. It supports both import (DXF → Database) and export (Database → DXF) workflows with complete flexibility for client-specific naming conventions.

---

## The Core Challenge

### The Problem

Different clients use different naming conventions:

| Client | Block Name | Detail Name | Material Name |
|--------|------------|-------------|---------------|
| Client A | `STM-INLET-A` | `STD-01` | `AC Pavement` |
| Client B | `STORM_INLET_TYPE_1` | `DETAIL_STANDARD_001` | `Asphalt Concrete` |
| Client C | `INLET-STORM-01` | `D-001-STORM` | `ASPH-PVMT` |
| **Our Database** | `STORM-INLET-TYPE-A` | `SD-STORM-INLET-01` | `ASPHALT_PAVEMENT` |

### The Solution

**Name Mapping Tables** that translate between:
- Client-specific names (what's in their DXF files)
- Canonical database names (our standardized vocabulary)

---

## Architecture Overview

### 11-Table Schema

```
┌────────────────────────────────────────────────────────────────┐
│                    STANDARDS LIBRARY (5 tables)                │
│  Canonical definitions - shared across all projects            │
├────────────────────────────────────────────────────────────────┤
│  - block_definitions                                           │
│  - detail_standards                                            │
│  - hatch_patterns                                              │
│  - material_standards                                          │
│  - standard_notes                                              │
└────────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────────┐
│                    NAME MAPPING (5 tables)                     │
│  Bidirectional translation: DXF ↔ Database                     │
├────────────────────────────────────────────────────────────────┤
│  - block_name_mappings                                         │
│  - detail_name_mappings                                        │
│  - hatch_name_mappings                                         │
│  - material_name_mappings                                      │
│  - note_name_mappings                                          │
└────────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────────┐
│              PROJECT CONTEXT MAPPINGS (1 table)                │
│  Relationships between different standard types                │
├────────────────────────────────────────────────────────────────┤
│  - project_context_mappings                                    │
│    * Keynote ↔ Block                                           │
│    * Keynote ↔ Detail                                          │
│    * Hatch ↔ Material                                          │
│    * Detail ↔ Material                                         │
│    * Block ↔ Specification                                     │
│    * Cross-References                                          │
└────────────────────────────────────────────────────────────────┘
```

---

## Part 1: Name Mapping Tables (5 Tables)

### Generic Schema Pattern

All 5 name mapping tables follow this pattern:

```sql
CREATE TABLE {entity_type}_name_mappings (
    mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Link to canonical standard
    {entity}_id UUID REFERENCES {entity}_standards({entity}_id),
    
    -- Client/project context
    client_id UUID REFERENCES clients(client_id),
    project_id UUID REFERENCES projects(project_id),  -- Optional: project-specific
    
    -- The translation
    dxf_name VARCHAR(255) NOT NULL,           -- Name in client's DXF file
    canonical_name VARCHAR(255) NOT NULL,     -- Our standardized name
    
    -- Usage tracking
    usage_frequency INTEGER DEFAULT 0,
    first_used_date DATE,
    last_used_date DATE,
    
    -- Metadata
    mapping_notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Prevent duplicates
    UNIQUE(client_id, dxf_name, {entity}_id)
);
```

### 1. Block Name Mappings

**Purpose:** Translate block (symbol) names between DXF and database.

```sql
CREATE TABLE block_name_mappings (
    mapping_id UUID PRIMARY KEY,
    block_definition_id UUID REFERENCES block_definitions(block_definition_id),
    client_id UUID REFERENCES clients(client_id),
    project_id UUID REFERENCES projects(project_id),
    
    -- Translation
    dxf_block_name VARCHAR(255) NOT NULL,      -- "STM-INLET-A"
    canonical_block_name VARCHAR(255) NOT NULL, -- "STORM-INLET-TYPE-A"
    
    usage_frequency INTEGER DEFAULT 0,
    mapping_notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(client_id, dxf_block_name, block_definition_id)
);
```

**Example Records:**

| dxf_block_name | canonical_block_name | client_id | block_definition_id |
|----------------|----------------------|-----------|---------------------|
| `STM-INLET-A` | `STORM-INLET-TYPE-A` | client-123 | block-abc |
| `STORM_INLET_TYPE_1` | `STORM-INLET-TYPE-A` | client-456 | block-abc |
| `INLET-STORM-01` | `STORM-INLET-TYPE-A` | client-789 | block-abc |

**Same database object, three different client names!**

### 2. Detail Name Mappings

**Purpose:** Map construction detail references.

```sql
CREATE TABLE detail_name_mappings (
    mapping_id UUID PRIMARY KEY,
    detail_id UUID REFERENCES detail_standards(detail_id),
    client_id UUID REFERENCES clients(client_id),
    
    dxf_detail_number VARCHAR(100) NOT NULL,    -- "STD-01"
    canonical_detail_number VARCHAR(100) NOT NULL, -- "SD-STORM-INLET-01"
    
    usage_frequency INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(client_id, dxf_detail_number, detail_id)
);
```

### 3. Hatch Pattern Mappings

**Purpose:** Translate hatch pattern names (fill patterns for areas).

```sql
CREATE TABLE hatch_name_mappings (
    mapping_id UUID PRIMARY KEY,
    hatch_pattern_id UUID REFERENCES hatch_patterns(hatch_pattern_id),
    client_id UUID REFERENCES clients(client_id),
    
    dxf_hatch_name VARCHAR(255) NOT NULL,       -- "ANSI31"
    canonical_hatch_name VARCHAR(255) NOT NULL, -- "EARTH-COMPACTED"
    
    usage_frequency INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(client_id, dxf_hatch_name, hatch_pattern_id)
);
```

### 4. Material Name Mappings

**Purpose:** Standardize material naming across clients.

```sql
CREATE TABLE material_name_mappings (
    mapping_id UUID PRIMARY KEY,
    material_id UUID REFERENCES material_standards(material_id),
    client_id UUID REFERENCES clients(client_id),
    
    dxf_material_name VARCHAR(255) NOT NULL,    -- "AC Pavement"
    canonical_material_name VARCHAR(255) NOT NULL, -- "ASPHALT_CONCRETE_PAVEMENT"
    
    usage_frequency INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(client_id, dxf_material_name, material_id)
);
```

### 5. Note Name Mappings

**Purpose:** Map keynote/callout references.

```sql
CREATE TABLE note_name_mappings (
    mapping_id UUID PRIMARY KEY,
    note_id UUID REFERENCES standard_notes(note_id),
    client_id UUID REFERENCES clients(client_id),
    
    dxf_note_code VARCHAR(100) NOT NULL,        -- "N-1.01"
    canonical_note_code VARCHAR(100) NOT NULL,  -- "STM-INLET-TYPE-A"
    
    usage_frequency INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(client_id, dxf_note_code, note_id)
);
```

---

## Part 2: Bidirectional Translation Workflow

### Import: DXF → Database

```python
def translate_dxf_to_database(dxf_name, entity_type, client_id):
    """
    Lookup canonical database name from DXF name.
    
    Example:
        translate_dxf_to_database("STM-INLET-A", "block", "client-123")
        → Returns: ("STORM-INLET-TYPE-A", block_definition_id)
    """
    
    table = f"{entity_type}_name_mappings"
    
    query = f"""
        SELECT 
            m.canonical_{entity_type}_name,
            m.{entity_type}_id,
            s.*
        FROM {table} m
        JOIN {entity_type}_standards s ON m.{entity_type}_id = s.{entity_type}_id
        WHERE m.client_id = %s
          AND m.dxf_{entity_type}_name = %s
          AND m.is_active = TRUE
        LIMIT 1
    """
    
    result = execute_query(query, (client_id, dxf_name))
    
    if result:
        # Mapping exists - use it
        return result[0]
    else:
        # No mapping - try fuzzy match or create new mapping
        return handle_unmapped_name(dxf_name, entity_type, client_id)
```

### Export: Database → DXF

```python
def translate_database_to_dxf(canonical_name, entity_type, client_id):
    """
    Lookup client-specific DXF name from canonical database name.
    
    Example:
        translate_database_to_dxf("STORM-INLET-TYPE-A", "block", "client-123")
        → Returns: "STM-INLET-A"
    """
    
    table = f"{entity_type}_name_mappings"
    
    query = f"""
        SELECT dxf_{entity_type}_name
        FROM {table}
        WHERE client_id = %s
          AND canonical_{entity_type}_name = %s
          AND is_active = TRUE
        LIMIT 1
    """
    
    result = execute_query(query, (client_id, canonical_name))
    
    if result:
        # Mapping exists - use client's preferred name
        return result[0]['dxf_name']
    else:
        # No mapping - use canonical name (or create mapping)
        return canonical_name
```

---

## Part 3: Project Context Mappings

### The Relationship Problem

Standards don't exist in isolation. They have **cross-references**:

- A keynote references a specific block
- A detail shows a specific material
- A hatch pattern represents a material
- A block references a specification section

### Schema: One Table, Many Relationship Types

```sql
CREATE TABLE project_context_mappings (
    mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id),
    
    -- Source entity (polymorphic reference)
    source_type VARCHAR(50) CHECK (source_type IN (
        'keynote', 'block', 'detail', 'hatch', 'material', 'specification'
    )),
    source_id UUID NOT NULL,
    
    -- Target entity (polymorphic reference)
    target_type VARCHAR(50) CHECK (target_type IN (
        'keynote', 'block', 'detail', 'hatch', 'material', 'specification'
    )),
    target_id UUID NOT NULL,
    
    -- Relationship metadata
    relationship_type VARCHAR(100) CHECK (relationship_type IN (
        'keynote_to_block',
        'keynote_to_detail',
        'hatch_to_material',
        'detail_to_material',
        'block_to_specification',
        'cross_reference',
        'alternative',
        'supersedes'
    )),
    
    relationship_notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(project_id, source_type, source_id, target_type, target_id)
);
```

### Relationship Type 1: Keynote ↔ Block

**Use Case:** Sheet note "1.01" refers to block "STORM-INLET-TYPE-A"

```sql
INSERT INTO project_context_mappings 
(project_id, source_type, source_id, target_type, target_id, relationship_type)
VALUES 
('proj-123', 'keynote', 'note-abc', 'block', 'block-xyz', 'keynote_to_block');
```

**Query:**
```sql
-- Find all blocks referenced by a keynote
SELECT 
    bd.block_name,
    bd.block_code
FROM project_context_mappings pcm
JOIN block_definitions bd ON pcm.target_id = bd.block_definition_id
WHERE pcm.project_id = 'proj-123'
  AND pcm.source_type = 'keynote'
  AND pcm.source_id = 'note-abc'
  AND pcm.target_type = 'block';
```

### Relationship Type 2: Keynote ↔ Detail

**Use Case:** Keynote "2.05" references detail "SD-STORM-INLET-01"

```sql
INSERT INTO project_context_mappings 
(project_id, source_type, source_id, target_type, target_id, relationship_type)
VALUES 
('proj-123', 'keynote', 'note-def', 'detail', 'detail-789', 'keynote_to_detail');
```

### Relationship Type 3: Hatch ↔ Material

**Use Case:** Hatch pattern "EARTH-COMPACTED" represents material "STRUCTURAL_FILL"

```sql
INSERT INTO project_context_mappings 
(project_id, source_type, source_id, target_type, target_id, relationship_type)
VALUES 
('proj-123', 'hatch', 'hatch-456', 'material', 'material-111', 'hatch_to_material');
```

**Use During Export:**
```python
# When exporting area with material "STRUCTURAL_FILL"
# Lookup which hatch pattern to use
hatch_pattern = get_hatch_for_material(project_id, material_id)
```

### Relationship Type 4: Detail ↔ Material

**Use Case:** Detail "SD-RETAINING-WALL-01" specifies material "CONCRETE_3000PSI"

```sql
INSERT INTO project_context_mappings 
(project_id, source_type, source_id, target_type, target_id, relationship_type)
VALUES 
('proj-123', 'detail', 'detail-789', 'material', 'material-222', 'detail_to_material');
```

### Relationship Type 5: Block ↔ Specification

**Use Case:** Block "STORM-INLET-TYPE-A" references spec section "02742 - Storm Drainage"

```sql
INSERT INTO project_context_mappings 
(project_id, source_type, source_id, target_type, target_id, relationship_type)
VALUES 
('proj-123', 'block', 'block-xyz', 'specification', 'spec-333', 'block_to_specification');
```

### Relationship Type 6: Cross-References

**Use Case:** Detail "A" is an alternative to detail "B"

```sql
INSERT INTO project_context_mappings 
(project_id, source_type, source_id, target_type, target_id, relationship_type)
VALUES 
('proj-123', 'detail', 'detail-A', 'detail', 'detail-B', 'alternative');
```

---

## Complete Import Workflow Example

### Scenario: Import Block from Client DXF

**Client DXF Contains:**
- Block name: `STM-INLET-A`
- Client: Acme Engineering

**Step 1: Lookup Name Mapping**

```sql
SELECT 
    bnm.canonical_block_name,
    bd.block_definition_id,
    bd.block_code,
    bd.entity_id
FROM block_name_mappings bnm
JOIN block_definitions bd ON bnm.block_definition_id = bd.block_definition_id
WHERE bnm.client_id = 'acme-engineering-uuid'
  AND bnm.dxf_block_name = 'STM-INLET-A'
  AND bnm.is_active = TRUE;
```

**Result:**
```
canonical_block_name: "STORM-INLET-TYPE-A"
block_definition_id: "block-abc-123"
block_code: "STM-INLET-A"
entity_id: "entity-xyz-789"
```

**Step 2: Create Block Insert**

```sql
INSERT INTO block_inserts 
(block_insert_id, project_id, block_definition_id, entity_id, 
 geometry, rotation, scale_x, scale_y)
VALUES 
(gen_random_uuid(), 'project-456', 'block-abc-123', 'entity-xyz-789',
 ST_GeomFromText('POINT Z (6123456.7 2089123.4 125.5)', 2226),
 0.0, 1.0, 1.0);
```

**Step 3: Update Usage Tracking**

```sql
UPDATE block_name_mappings
SET usage_frequency = usage_frequency + 1,
    last_used_date = CURRENT_DATE
WHERE mapping_id = 'mapping-uuid';
```

**Step 4: Find Related Standards**

```sql
-- Find details that reference this block
SELECT 
    ds.detail_number,
    ds.detail_title
FROM project_context_mappings pcm
JOIN detail_standards ds ON pcm.source_id = ds.detail_id
WHERE pcm.project_id = 'proj-123'
  AND pcm.target_type = 'block'
  AND pcm.target_id = 'block-abc-123'
  AND pcm.relationship_type = 'keynote_to_block';
```

---

## Complete Export Workflow Example

### Scenario: Export Blocks to Client DXF

**Database Contains:**
- 5 blocks with canonical names
- Client: Acme Engineering
- Export format: Client-specific names

**Step 1: Query Blocks for Export**

```sql
SELECT 
    bi.block_insert_id,
    bd.block_code AS canonical_name,
    ST_X(bi.geometry) AS x,
    ST_Y(bi.geometry) AS y,
    ST_Z(bi.geometry) AS z,
    bi.rotation,
    bi.scale_x,
    bi.scale_y
FROM block_inserts bi
JOIN block_definitions bd ON bi.block_definition_id = bd.block_definition_id
WHERE bi.project_id = 'project-456';
```

**Step 2: Translate Names**

```python
for block in blocks:
    # Lookup client-specific name
    client_name = translate_database_to_dxf(
        canonical_name=block['canonical_name'],
        entity_type='block',
        client_id='acme-engineering-uuid'
    )
    
    # If no mapping exists, use canonical name
    if not client_name:
        client_name = block['canonical_name']
    
    # Add to DXF
    msp.add_blockref(
        name=client_name,
        insert=(block['x'], block['y'], block['z']),
        dxfattribs={
            'rotation': block['rotation'],
            'xscale': block['scale_x'],
            'yscale': block['scale_y']
        }
    )
```

---

## Management Interface

### Standards Mapping Manager (`/standards/mapping-manager`)

**Features:**
1. **Bulk Import:** Upload CSV with client name mappings
2. **Individual Mapping:** Create one-off mappings
3. **Mapping Validation:** Check for conflicts and duplicates
4. **Usage Analytics:** See which mappings are most used
5. **Auto-Mapping:** Suggest mappings based on fuzzy matching

### API Endpoints

```python
# Create new mapping
POST /api/name-mappings/{entity_type}
{
    "client_id": "uuid",
    "dxf_name": "STM-INLET-A",
    "canonical_name": "STORM-INLET-TYPE-A",
    "entity_id": "uuid"
}

# Get all mappings for a client
GET /api/name-mappings/{entity_type}?client_id=uuid

# Update mapping
PUT /api/name-mappings/{entity_type}/{mapping_id}

# Delete mapping (soft delete)
DELETE /api/name-mappings/{entity_type}/{mapping_id}

# Test translation
POST /api/name-mappings/{entity_type}/translate
{
    "client_id": "uuid",
    "dxf_name": "STM-INLET-A",
    "direction": "import"  # or "export"
}
```

---

## Summary

### What the Framework Provides

1. **Flexibility:** Support any client naming convention
2. **Bidirectional:** Import and export with translation
3. **Relationships:** Cross-reference standards across types
4. **Tracking:** Monitor usage patterns
5. **Scalability:** Add new clients without code changes

### Key Tables

**Name Mappings (5):**
- `block_name_mappings`
- `detail_name_mappings`
- `hatch_name_mappings`
- `material_name_mappings`
- `note_name_mappings`

**Context Relationships (1):**
- `project_context_mappings`

**Result:** A flexible, database-driven translation layer that makes working with diverse client standards seamless.
