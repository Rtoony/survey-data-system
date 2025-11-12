# ACAD-GIS Entity Relationship Model

## Overview

This document explains how all database entities relate to each other in the ACAD-GIS system, from the highest-level project containers down to individual CAD primitives.

---

## Hierarchical Organization

### Level 1: Projects (Top-Level Container)

```
projects
├── project_id (UUID, primary key)
├── project_name
├── project_number
├── client_id → clients
├── project_type
├── status
└── metadata (JSONB)
```

**Purpose:** The organizational unit for all work. Everything belongs to a project.

**Relationships:**
- Has many: drawings, sheets, survey points, utilities, parcels
- Belongs to: client (optional)
- Can have many: clients, vendors, municipalities (via junction tables)

---

### Level 2: Drawings & Sheet Sets

```
drawings
├── drawing_id (UUID)
├── project_id → projects.project_id
├── drawing_number
├── drawing_title
├── file_path
└── dxf_metadata (JSONB)

sheet_sets
├── set_id (UUID)
├── project_id → projects.project_id
├── set_name
└── set_description

sheets
├── sheet_id (UUID)
├── set_id → sheet_sets.set_id
├── sheet_number
├── sheet_title
└── layout_name
```

**Purpose:** Organize construction documents and CAD files.

**Relationships:**
- `drawings` → Many layers, blocks, entities per drawing
- `sheets` → Many viewports, notes, references per sheet
- `sheet_revisions` → Track changes to individual sheets

---

### Level 3: CAD Content (Per Drawing)

```
layers
├── layer_id (UUID)
├── drawing_id → drawings.drawing_id
├── layer_name
├── entity_id → standards_entities.entity_id
└── layer_standard_id → layer_standards.layer_standard_id

block_inserts
├── block_insert_id (UUID)
├── drawing_id → drawings.drawing_id
├── block_definition_id → block_definitions.block_definition_id
├── entity_id → standards_entities.entity_id
├── geometry (PostGIS PointZ)
└── attributes (JSONB)

drawing_entities
├── entity_id (UUID)
├── drawing_id → drawings.drawing_id
├── layer_id → layers.layer_id
├── entity_type (LINE, POLYLINE, ARC, CIRCLE, etc.)
├── geometry (PostGIS Geometry)
└── dxf_data (JSONB)
```

**Purpose:** Store actual CAD primitives and their organization.

**Relationships:**
- All entities reference their parent `drawing_id`
- All entities reference their `layer_id`
- Many entities have `entity_id` linking to unified registry

---

## The Unified Entity Model

### Core Concept: Canonical Identity

Every significant object in the database gets a **canonical entity_id** that links it across multiple tables.

```
standards_entities (The Central Registry)
├── entity_id (UUID, primary key)
├── entity_type (layer, block, survey_point, utility_line, etc.)
├── entity_name
├── description
├── created_at
└── quality_score
```

### What Gets an Entity ID?

**Standards Library:**
- Layer standards
- Block definitions
- Detail standards
- Material standards
- Hatch patterns
- Note standards

**Project-Specific Data:**
- Survey points
- Utility lines
- Utility structures
- Parcels
- Alignments
- BMPs

**CAD Content:**
- Layers (instances)
- Block inserts (instances)
- Significant drawing entities

### Why This Matters

This unified model enables:
1. **Cross-table queries**: Find everything related to an entity, regardless of table
2. **Embeddings**: Generate one embedding per entity, stored centrally
3. **Relationships**: Build graph edges between any two entities
4. **Quality tracking**: Score data quality consistently across entity types

---

## Relationship Types

The `entity_relationships` table stores explicit connections between entities:

```sql
entity_relationships
├── relationship_id (UUID)
├── source_entity_id → standards_entities.entity_id
├── target_entity_id → standards_entities.entity_id
├── relationship_type (spatial, engineering, semantic, hierarchical, reference)
├── relationship_strength (0.0 - 1.0)
├── metadata (JSONB)
└── confidence_score
```

### 1. Spatial Relationships

**Definition:** Entities physically near or intersecting each other.

**Examples:**
- Fire hydrant → Water main (within 10 feet)
- Manhole → Storm pipe (connected)
- Survey point → Parcel (within boundary)

**Source:** Computed from PostGIS spatial queries:
```sql
ST_DWithin(source.geometry, target.geometry, 50)  -- Within 50 feet
ST_Intersects(pipe.geometry, parcel.geometry)
```

### 2. Engineering Relationships

**Definition:** Functional connections defined by civil engineering logic.

**Examples:**
- Inlet → Pipe → Outlet (flow direction)
- BMP → Drainage area (serves)
- Alignment station → Cross-section (profile relationship)

**Source:** Domain-specific logic and network topology.

### 3. Semantic Relationships

**Definition:** Conceptual similarity based on meaning.

**Examples:**
- "Catch basin" ↔ "Storm drain inlet" (synonyms)
- "Water quality BMP" ↔ "Bioretention basin" (related concepts)

**Source:** Vector embedding similarity (cosine distance < 0.2).

### 4. Hierarchical Relationships

**Definition:** Parent-child organizational structure.

**Examples:**
- Project → Drawing → Layer → Entity
- Standard library → Project instance → Modified copy
- Sheet set → Sheet → Revision

**Source:** Foreign key relationships made explicit.

### 5. Reference Relationships

**Definition:** Documentation and citation links.

**Examples:**
- Block → Detail standard (references)
- Note → Specification section (cites)
- Material → Manufacturer product (specifies)

**Source:** Metadata and cross-references.

---

## Standards Library vs. Project Instances

### The Dual Identity System

Every standardized element exists in **two forms**:

#### 1. Standard Library (Canonical Definition)

```
block_definitions
├── block_definition_id (UUID)
├── block_code (e.g., "STM-INLET-01")
├── block_name
├── geometry (SVG or DXF)
├── entity_id → standards_entities
└── is_active = TRUE
```

**Characteristics:**
- Read-only in project context
- Serves as template
- Shared across all projects
- Version-controlled

#### 2. Project Instance (Usage Context)

```
project_blocks
├── project_block_id (UUID)
├── project_id → projects.project_id
├── block_definition_id → block_definitions.block_definition_id
├── standard_reference_id (original standard source)
├── source_type (standard | modified_standard | custom)
├── is_modified (boolean)
└── deviation_tracking (metadata)
```

**Characteristics:**
- Project-specific copy
- Can be modified (creates new record)
- Tracks deviation from standard
- Usage-specific attributes

### Assignment Tables (Junction Pattern)

Many-to-many relationships between projects and standards:

```
project_clients
├── project_id → projects.project_id
└── client_id → clients.client_id

project_vendors
├── project_id → projects.project_id
└── vendor_id → vendors.vendor_id

project_standard_assignments
├── project_id → projects.project_id
├── standard_type (layer | block | detail | material | note)
└── standard_id (polymorphic reference)
```

---

## Foreign Key Relationship Map

### Projects Domain

```
projects
  ↓ (1:N)
  ├── drawings
  │     ↓ (1:N)
  │     ├── layers
  │     ├── block_inserts
  │     ├── drawing_entities
  │     └── drawing_text
  │
  ├── sheet_sets
  │     ↓ (1:N)
  │     └── sheets
  │           ↓ (1:N)
  │           └── sheet_revisions
  │
  ├── survey_points
  ├── utility_lines
  ├── utility_structures
  ├── parcels
  ├── alignments
  └── bmps
```

### Standards Domain

```
discipline_standards
  ↓ (1:N)
  ├── category_standards
        ↓ (1:N)
        └── object_type_standards

layer_standards
  ↓ (1:N)
  └── layers (instances per drawing)

block_definitions
  ↓ (1:N)
  └── block_inserts (instances per drawing)

detail_standards
  ↓ (1:N)
  └── project_details (project-specific instances)
```

### AI Infrastructure

```
embedding_models
  ↓ (1:N)
  └── entity_embeddings
        ↓ (N:1)
        standards_entities ←── (1:N) ──┐
              ↓ (1:N)                    │
              entity_relationships ──────┘
                (source_entity_id, target_entity_id)
```

---

## Cross-Table Entity Resolution

### How Entity IDs Link Everything

**Example: A Storm Drain Inlet**

```
1. Standards Library Entry:
   block_definitions.block_definition_id = "abc-123"
   block_definitions.entity_id = "entity-001"

2. Unified Entity Record:
   standards_entities.entity_id = "entity-001"
   standards_entities.entity_type = "block"
   standards_entities.entity_name = "Storm Drain Inlet Type A"

3. Vector Embedding:
   entity_embeddings.entity_id = "entity-001"
   entity_embeddings.embedding = [0.023, -0.145, ...]

4. Project Instance:
   block_inserts.block_insert_id = "insert-456"
   block_inserts.block_definition_id = "abc-123"
   block_inserts.entity_id = "entity-001" (same!)

5. Spatial Relationships:
   entity_relationships.source_entity_id = "entity-001" (inlet)
   entity_relationships.target_entity_id = "entity-002" (pipe)
   entity_relationships.relationship_type = "engineering"

6. Quality Scoring:
   standards_entities.quality_score = 0.92
   (Based on: has embedding, has geometry, has relationships, usage count)
```

### Query Pattern: Find Everything About an Entity

```sql
-- 1. Get the entity
SELECT * FROM standards_entities WHERE entity_id = 'entity-001';

-- 2. Get its embedding
SELECT * FROM entity_embeddings WHERE entity_id = 'entity-001';

-- 3. Get all relationships (outbound and inbound)
SELECT * FROM entity_relationships 
WHERE source_entity_id = 'entity-001' OR target_entity_id = 'entity-001';

-- 4. Find the source table (polymorphic lookup)
SELECT * FROM block_definitions WHERE entity_id = 'entity-001';

-- 5. Find all project uses
SELECT * FROM block_inserts WHERE entity_id = 'entity-001';

-- 6. Find similar entities (semantic search)
SELECT entity_id, 1 - (embedding <=> target_embedding) AS similarity
FROM entity_embeddings
WHERE 1 - (embedding <=> target_embedding) > 0.80
ORDER BY embedding <=> target_embedding;
```

---

## Network Topology (Civil Engineering)

### Utility Networks

```
utility_lines (edges)
├── line_id (UUID)
├── project_id
├── entity_id
├── line_type (gravity_main, pressure_main, storm, sanitary, water)
├── geometry (LineStringZ)
├── upstream_structure_id → utility_structures.structure_id
└── downstream_structure_id → utility_structures.structure_id

utility_structures (nodes)
├── structure_id (UUID)
├── project_id
├── entity_id
├── structure_type (manhole, inlet, outlet, junction, valve)
├── geometry (PointZ)
└── invert_elevation
```

**Graph Structure:**
- Lines connect structures (directed graph)
- Flow direction: upstream → downstream
- Enables network analysis: flow accumulation, criticality, connectivity

### Survey Control Networks

```
survey_points
├── point_id (UUID)
├── point_number
├── entity_id
├── geometry (PointZ)
├── point_type (control, benchmark, monument, topo)
└── elevation

control_point_membership
├── point_id → survey_points.point_id
├── network_id
└── control_type (horizontal, vertical, both)
```

**Network Structure:**
- Control points form surveying reference framework
- Enables least-squares adjustment
- Hierarchical accuracy propagation

---

## DXF Import Linking

### Change Detection & Sync

```
dxf_entity_links
├── link_id (UUID)
├── drawing_id
├── dxf_handle (unique identifier in DXF file)
├── database_table (which table stores this entity)
├── database_id (UUID in that table)
├── geometry_hash (SHA256 of coordinates)
├── attributes_hash (SHA256 of properties)
└── last_sync_at
```

**Purpose:** Track which DXF entities map to which database records.

**Workflow:**
1. **Import:** Create link record for each imported DXF entity
2. **Re-import:** Check if DXF handle exists
3. **Compare:** Hash current geometry vs. stored hash
4. **Update:** If changed, update database record
5. **Delete Detection:** DXF entities missing from file

---

## Materialized Views (Pre-Computed Relationships)

### 1. Survey Points Enriched

```sql
CREATE MATERIALIZED VIEW mv_survey_points_enriched AS
SELECT 
    sp.*,
    COUNT(DISTINCT p.parcel_id) AS parcels_within_100ft,
    COUNT(DISTINCT ul.line_id) AS utilities_within_50ft,
    AVG(nearby.elevation) AS avg_nearby_elevation
FROM survey_points sp
LEFT JOIN parcels p ON ST_DWithin(sp.geometry, p.geometry, 100)
LEFT JOIN utility_lines ul ON ST_DWithin(sp.geometry, ul.geometry, 50)
LEFT JOIN survey_points nearby ON ST_DWithin(sp.geometry, nearby.geometry, 25)
GROUP BY sp.point_id;
```

**Purpose:** Fast access to spatial context around each survey point.

### 2. Entity Graph Summary

```sql
CREATE MATERIALIZED VIEW mv_entity_graph_summary AS
SELECT 
    entity_id,
    COUNT(*) FILTER (WHERE relationship_type = 'spatial') AS spatial_edges,
    COUNT(*) FILTER (WHERE relationship_type = 'engineering') AS engineering_edges,
    COUNT(*) FILTER (WHERE relationship_type = 'semantic') AS semantic_edges,
    AVG(relationship_strength) AS avg_strength
FROM entity_relationships
GROUP BY entity_id;
```

**Purpose:** Quick lookup of relationship statistics per entity.

---

## Summary: The Complete Relationship Web

```
┌─────────────────────────────────────────────────────────────┐
│                    standards_entities                       │
│              (Canonical Entity Registry)                    │
│  Every significant object gets one entity_id                │
└─────────────────────────────────────────────────────────────┘
                          ↓
        ┌─────────────────┼─────────────────┐
        ↓                 ↓                 ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│entity_       │  │entity_       │  │standards     │
│embeddings    │  │relationships │  │library tables│
│(AI semantic) │  │(graph edges) │  │(definitions) │
└──────────────┘  └──────────────┘  └──────────────┘
                                            ↓
                                    ┌──────────────┐
                                    │project       │
                                    │instance      │
                                    │tables        │
                                    └──────────────┘
                                            ↓
                          ┌─────────────────┼─────────────────┐
                          ↓                 ↓                 ↓
                  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
                  │drawings      │  │sheets        │  │civil         │
                  │(CAD files)   │  │(documents)   │  │engineering   │
                  └──────────────┘  └──────────────┘  │(survey/GIS)  │
                          ↓                           └──────────────┘
                  ┌──────────────┐
                  │layers        │
                  │blocks        │
                  │entities      │
                  └──────────────┘
```

**Key Takeaway:** The `entity_id` from `standards_entities` is the thread that ties everything together, enabling AI understanding across the entire database.
