# Intelligent DXF Workflow

## Overview

This system implements a bidirectional workflow between CAD (DXF files) and a PostgreSQL/PostGIS database, where the **database is the source of truth** for civil engineering project data.

## Core Concept

The database stores "intelligent objects" (utility lines, BMPs, alignments, structures, etc.) with all their properties and relationships. DXF files are used for:
1. **Import**: Bringing CAD data into the database and creating intelligent objects
2. **Export**: Generating DXF files from database objects for submission/review
3. **Re-import**: Detecting changes made in CAD and updating the database

## Key Components

### 1. Layer Pattern Classification (`layer_classifier.py`)

Parses layer names to extract object properties:

**Examples:**
- `12IN-STORM` → Creates utility_line with diameter=12", type=Storm
- `BMP-BIORETENTION-500CF` → Creates BMP with type=Bioretention, volume=500 CF
- `SURFACE-EG` → Creates surface_model with type=Existing Grade
- `MH-STORM` → Creates utility_structure with type=Manhole, utility=Storm
- `TREE-EXIST` → Creates site_tree with status=Existing

### 2. DXF Entity Links Table (`create_dxf_entity_links_schema.sql`)

Bidirectional mapping between DXF entities and database objects:
- Tracks DXF handle (unique CAD identifier)
- Links to intelligent object (UUID + table name)
- Stores geometry hash for change detection
- Enables round-trip workflow

### 3. Intelligent Object Creator (`intelligent_object_creator.py`)

Creates database objects from classified DXF entities:
- Uses layer pattern classification
- Validates geometry types (POINT for structures, LINESTRING for pipes, etc.)
- Populates appropriate database tables
- Creates entity links for tracking

### 4. Enhanced DXF Importer (`dxf_importer.py`)

Supports comprehensive DXF entity types:
- Basic: LINE, POLYLINE, ARC, CIRCLE, ELLIPSE, SPLINE
- Points: POINT (survey points, structures, trees)
- 3D: 3DFACE (TIN surfaces), 3DSOLID, MESH
- Annotation: TEXT, MTEXT, DIMENSION, LEADER
- Other: HATCH, BLOCK (INSERT)

## Workflow

### Import Workflow (CAD → Database)

```
1. User draws in CAD using layer naming conventions
   Example: Draw pipe on layer "12IN-STORM"
   
2. Export to DXF and import into system
   
3. System processes:
   a. Reads DXF geometry and metadata
   b. Classifies layer name → "utility_line" with diameter=12", type=Storm
   c. Creates record in utility_lines table
   d. Links DXF entity to database object in dxf_entity_links
   e. Stores geometry hash for change detection
```

### Export Workflow (Database → CAD)

```
1. Query intelligent objects from database
   Example: SELECT * FROM utility_lines WHERE utility_type = 'Storm'
   
2. Generate DXF geometry with intelligent layer names
   Example: 12" storm pipe → Layer "12IN-STORM"
   
3. Export DXF file for submission/review
```

### Re-import Workflow (Change Detection)

```
1. User modifies DXF in CAD:
   - Changes layer "12IN-STORM" to "15IN-STORM" (property update)
   - Moves pipe location (geometry change)
   - Deletes entity (deletion)
   
2. Re-import DXF
   
3. System detects changes:
   a. Layer name change → Update diameter in database (12" → 15")
   b. Geometry change → Compare geometry hash, update coordinates
   c. Missing entity → Mark as deleted or remove from database
```

## Database Tables

### Intelligent Object Tables
- `utility_lines` - Pipes and conduits
- `utility_structures` - Manholes, catch basins, valves, etc.
- `bmps` - Best Management Practices (bioretention, swales, etc.)
- `surface_models` - TIN/DTM surfaces
- `horizontal_alignments` - Centerlines
- `survey_points` - Survey control and topo points
- `site_trees` - Tree inventory
- `parcels` - Property boundaries
- `project_notes` - Sheet notes and callouts

### Linking Table
- `dxf_entity_links` - Bidirectional CAD ↔ Database mapping

## Layer Naming Conventions

### Utility Lines
- Pattern: `{SIZE}{UNIT}-{TYPE}`
- Examples: `12IN-STORM`, `8IN-SANITARY`, `6IN-WATER`

### Utility Structures
- Pattern: `{STRUCTURE}-{TYPE}`
- Examples: `MH-STORM`, `CB-STORM`, `VALVE-WATER`

### BMPs
- Pattern: `BMP-{TYPE}-{VOLUME}{UNIT}`
- Examples: `BMP-BIORETENTION-500CF`, `BMP-SWALE`

### Surfaces
- Pattern: `SURFACE-{TYPE}` or `{TYPE}-SURFACE`
- Examples: `SURFACE-EG`, `SURFACE-PROP`, `TIN-EG`

### Alignments
- Pattern: `{TYPE}-{DESCRIPTION}`
- Examples: `CENTERLINE-ROAD`, `CL-UTILITY`, `ALIGNMENT`

### Survey Points
- Pattern: `{TYPE}-POINT` or `{TYPE}`
- Examples: `TOPO-POINT`, `CONTROL`, `BENCHMARK`

### Trees
- Pattern: `TREE-{STATUS}`
- Examples: `TREE-EXIST`, `TREE-PROP`, `TREE-TO-REMOVE`

## Future Enhancements

1. **Geometry Fingerprinting** - SHA256 hashing of geometry for precise change detection
2. **DXF Export Engine** - Generate DXF from database objects
3. **Change Detection Logic** - Automated merge on re-import
4. **API Endpoints** - REST API for import/export/sync operations
5. **Block Support** - Handle complex blocks with attributes
6. **Conflict Resolution** - UI for handling import conflicts

## Benefits

1. **Database as Source of Truth** - All intelligence lives in the database
2. **Simple CAD Workflow** - Users just draw with proper layer names
3. **Automated Intelligence** - System extracts properties from layers
4. **Bidirectional Sync** - Changes flow both ways (CAD ↔ Database)
5. **Change Tracking** - Know what changed and when
6. **Relationship Management** - Database handles all object relationships
7. **Quality Control** - Validate properties and relationships before export
