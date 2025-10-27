# DXF Tools - Migration Documentation

## Overview

The DXF Tools provide a complete round-trip workflow for importing CAD drawing files into PostGIS and exporting them back to DXF format. This system enables full geometric analysis, GIS integration, and CAD data management while preserving the ability to regenerate industry-standard DXF files. The implementation uses the `ezdxf` library for parsing/generating DXF files and PostGIS for storing 3D geometry with proper coordinate reference systems.

**Key Value:** Complete CAD-to-database workflow, GIS spatial analysis integration, normalized entity storage with foreign keys, intelligent name-to-UUID lookup caching, export job tracking, and round-trip DXF fidelity preservation.

## Use Cases

1. **DXF Import**: Upload DXF files and decompose into database entities (layers, blocks, lines, text, dimensions, hatches)
2. **Entity Storage**: Store CAD primitives with PostGIS GeometryZ for 3D spatial analysis
3. **DXF Export**: Regenerate DXF files from database entities with version control (AutoCAD 2013, 2018, etc.)
4. **GIS Integration**: Perform spatial queries, buffering, intersections on CAD geometry
5. **CAD Standards Compliance**: Link drawing entities to company layer and block standards
6. **Export Tracking**: Monitor export jobs with status, metrics, and error logging
7. **Layer/Linetype Management**: Track layer and linetype usage across drawings

---

## System Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        DXF Tools Workflow                     │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   DXF File   │ ──────> │ DXFImporter  │ ──────> │  PostgreSQL  │
│  (Upload)    │         │  + ezdxf    │         │  + PostGIS   │
└──────────────┘         └──────────────┘         └──────────────┘
                                │                         │
                                │                         │
                                v                         v
                        ┌──────────────┐         ┌──────────────┐
                        │ Lookup       │ <────── │ CAD Entities │
                        │ Service      │         │   Storage    │
                        └──────────────┘         └──────────────┘
                                                         │
                                                         │
                                                         v
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│  DXF File    │ <────── │ DXFExporter  │ <────── │  Database    │
│  (Download)  │         │  + ezdxf    │         │   Entities   │
└──────────────┘         └──────────────┘         └──────────────┘
                                │
                                v
                        ┌──────────────┐
                        │ Export Jobs  │
                        │   Tracking   │
                        └──────────────┘
```

### Key Components

1. **DXFImporter** (`dxf_importer.py`): Parses DXF files using ezdxf and stores entities in database
2. **DXFExporter** (`dxf_exporter.py`): Reads entities from database and generates DXF files
3. **DXFLookupService** (`dxf_lookup_service.py`): Resolves names to UUIDs with caching for performance
4. **PostGIS Storage**: Stores geometry as GeometryZ for 3D coordinates
5. **Export Job Tracking**: Monitors export operations with metrics and error logging

---

## Database Schema

### Core Entity Tables

#### `layers` - Drawing-Specific Layers

Stores layer definitions for each drawing.

```sql
CREATE TABLE layers (
    layer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    drawing_id UUID REFERENCES drawings(drawing_id) ON DELETE CASCADE,
    layer_name VARCHAR(255) NOT NULL,
    layer_standard_id UUID,                    -- FK to layer_standards (nullable)
    color INTEGER,                              -- AutoCAD Color Index (ACI)
    linetype VARCHAR(100),                      -- 'Continuous', 'DASHED', 'CENTER'
    lineweight INTEGER,                         -- Line weight in mm
    is_frozen BOOLEAN DEFAULT FALSE,
    is_locked BOOLEAN DEFAULT FALSE,
    UNIQUE(drawing_id, layer_name)
);

CREATE INDEX idx_layers_drawing ON layers(drawing_id);
```

**Key Points:**
- Each drawing has its own layer instances
- `layer_standard_id` links to company standards (optional)
- UNIQUE constraint prevents duplicate layer names per drawing
- CASCADE delete when drawing is deleted

---

#### `layer_standards` - CAD Standards Reference

Company-wide layer naming standards.

```sql
CREATE TABLE layer_standards (
    layer_standard_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    layer_name VARCHAR(255) UNIQUE NOT NULL,    -- 'C-BLDG', 'A-WALL', 'E-POWER'
    discipline VARCHAR(100),                     -- 'Civil', 'Architectural', 'Electrical'
    color_rgb VARCHAR(50),                       -- 'rgb(255, 0, 0)'
    color_hex VARCHAR(7),                        -- '#FF0000'
    linetype VARCHAR(100),                       -- Standard linetype
    lineweight INTEGER,                          -- Standard lineweight
    description TEXT
);
```

**Key Points:**
- UNIQUE layer_name for standards enforcement
- Used as reference during DXF import (lookup service)
- Links to `layers` table via `layer_standard_id`

---

#### `block_standards` - Symbol Definitions

Company-wide block (symbol) library.

```sql
CREATE TABLE block_standards (
    block_standard_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    block_name VARCHAR(255) UNIQUE NOT NULL,    -- 'TREE-DECIDUOUS', 'VALVE-GATE'
    category VARCHAR(100),                       -- 'Landscape', 'Mechanical', 'Electrical'
    description TEXT,
    svg_preview TEXT,                            -- SVG for web visualization
    discipline VARCHAR(100)                      -- 'Civil', 'MEP', 'Landscape'
);
```

**Key Points:**
- UNIQUE block_name for standards
- SVG preview for web-based CAD viewers
- Used as reference during DXF import

---

#### `block_inserts` - Block Instances

Individual block placements in drawings.

```sql
CREATE TABLE block_inserts (
    insert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    drawing_id UUID REFERENCES drawings(drawing_id) ON DELETE CASCADE,
    block_name VARCHAR(255) NOT NULL,            -- References block_standards.block_name
    insertion_point GEOMETRY(PointZ) NOT NULL,   -- 3D insertion point (PostGIS)
    scale_x NUMERIC(10, 4) DEFAULT 1.0,
    scale_y NUMERIC(10, 4) DEFAULT 1.0,
    scale_z NUMERIC(10, 4) DEFAULT 1.0,
    rotation NUMERIC(10, 4) DEFAULT 0.0,         -- Rotation angle in degrees
    attributes JSONB,                             -- Block attributes (key-value pairs)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_block_inserts_drawing ON block_inserts(drawing_id);
```

**Key Points:**
- PostGIS `GEOMETRY(PointZ)` for 3D coordinates
- `block_name` is string reference (not FK) for flexibility
- JSONB attributes store dynamic block data
- CASCADE delete with drawing

---

### CAD Primitive Tables

#### `drawing_entities` - CAD Primitives

Stores lines, polylines, arcs, circles, ellipses, splines.

```sql
CREATE TABLE drawing_entities (
    entity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    drawing_id UUID REFERENCES drawings(drawing_id) ON DELETE CASCADE,
    layer_id UUID REFERENCES layers(layer_id),   -- FK to layers
    entity_type VARCHAR(50) NOT NULL,             -- 'LINE', 'POLYLINE', 'ARC', 'CIRCLE', 'ELLIPSE', 'SPLINE'
    space_type VARCHAR(20) DEFAULT 'MODEL',       -- 'MODEL' or 'PAPER'
    geometry GEOMETRY(GeometryZ) NOT NULL,        -- PostGIS geometry (supports 3D)
    dxf_handle VARCHAR(100),                      -- DXF handle for round-trip
    color_aci INTEGER,                            -- AutoCAD Color Index
    linetype VARCHAR(100),                        -- Linetype override
    lineweight INTEGER,                           -- Lineweight override
    transparency INTEGER,                         -- Transparency (0-255)
    metadata JSONB,                               -- Additional entity data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_entities_drawing ON drawing_entities(drawing_id);
CREATE INDEX idx_entities_layer ON drawing_entities(layer_id);
CREATE INDEX idx_entities_geometry ON drawing_entities USING GIST(geometry);
```

**Key Points:**
- `GEOMETRY(GeometryZ)` supports LineString, Polygon, Point, etc.
- GIST spatial index for fast spatial queries
- `dxf_handle` preserves original DXF references
- `space_type` distinguishes modelspace vs paperspace

---

#### `drawing_text` - Text Annotations

Stores text and mtext entities.

```sql
CREATE TABLE drawing_text (
    text_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    drawing_id UUID REFERENCES drawings(drawing_id) ON DELETE CASCADE,
    layer_id UUID REFERENCES layers(layer_id),
    space_type VARCHAR(20) DEFAULT 'MODEL',
    text_content TEXT NOT NULL,                   -- Actual text content
    insertion_point GEOMETRY(PointZ) NOT NULL,    -- Text insertion point
    text_height NUMERIC(10, 4),                   -- Text height in drawing units
    rotation_angle NUMERIC(10, 4) DEFAULT 0.0,    -- Rotation in degrees
    text_style VARCHAR(100),                      -- Text style name
    horizontal_justification VARCHAR(50),         -- 'LEFT', 'CENTER', 'RIGHT'
    vertical_justification VARCHAR(50),           -- 'BASELINE', 'MIDDLE', 'TOP', 'BOTTOM'
    dxf_handle VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_text_drawing ON drawing_text(drawing_id);
CREATE INDEX idx_text_geometry ON drawing_text USING GIST(insertion_point);
```

**Key Points:**
- Full text formatting support
- PostGIS point for spatial queries on text locations
- GIST index for spatial text search

---

#### `drawing_dimensions` - Dimension Annotations

Stores dimension entities (linear, aligned, angular, radial, diametric, ordinate).

```sql
CREATE TABLE dimension_styles (
    dimension_style_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    style_name VARCHAR(255) UNIQUE NOT NULL,
    text_height NUMERIC(10, 4),
    arrow_size NUMERIC(10, 4),
    extension_line_offset NUMERIC(10, 4),
    dimension_line_color INTEGER,
    text_color INTEGER,
    description TEXT
);

CREATE TABLE drawing_dimensions (
    dimension_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    drawing_id UUID REFERENCES drawings(drawing_id) ON DELETE CASCADE,
    layer_id UUID REFERENCES layers(layer_id),
    dimension_style_id UUID REFERENCES dimension_styles(dimension_style_id),
    space_type VARCHAR(20) DEFAULT 'MODEL',
    dimension_type VARCHAR(50) NOT NULL,          -- 'LINEAR', 'ALIGNED', 'ANGULAR', 'RADIAL', 'DIAMETER', 'ORDINATE'
    geometry GEOMETRY(GeometryZ) NOT NULL,        -- Dimension line geometry
    override_value VARCHAR(100),                  -- Custom dimension text override
    dimension_style VARCHAR(100),                 -- Dimension style name
    dxf_handle VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dimensions_drawing ON drawing_dimensions(drawing_id);
```

**Key Points:**
- Supports all AutoCAD dimension types
- Links to dimension style standards
- `override_value` for custom dimension text

---

#### `drawing_hatches` - Hatch/Fill Patterns

Stores hatch pattern instances.

```sql
CREATE TABLE hatch_patterns (
    pattern_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_name VARCHAR(255) UNIQUE NOT NULL,    -- 'ANSI31', 'AR-CONC', 'SOLID'
    pattern_type VARCHAR(50),                      -- 'PREDEFINED', 'USER_DEFINED', 'CUSTOM'
    description TEXT,
    material_type VARCHAR(100)                     -- 'Concrete', 'Earth', 'Gravel'
);

CREATE TABLE drawing_hatches (
    hatch_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    drawing_id UUID REFERENCES drawings(drawing_id) ON DELETE CASCADE,
    layer_id UUID REFERENCES layers(layer_id),
    pattern_id UUID REFERENCES hatch_patterns(pattern_id),
    space_type VARCHAR(20) DEFAULT 'MODEL',
    boundary_geometry GEOMETRY(PolygonZ) NOT NULL, -- Hatch boundary as polygon
    pattern_name VARCHAR(255),                     -- Pattern name
    pattern_scale NUMERIC(10, 4) DEFAULT 1.0,
    pattern_angle NUMERIC(10, 4) DEFAULT 0.0,      -- Rotation angle in degrees
    dxf_handle VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_hatches_drawing ON drawing_hatches(drawing_id);
CREATE INDEX idx_hatches_geometry ON drawing_hatches USING GIST(boundary_geometry);
```

**Key Points:**
- `GEOMETRY(PolygonZ)` for hatch boundaries
- GIST index for spatial queries
- Links to hatch pattern library

---

#### `layout_viewports` - Paperspace Viewports

Stores paperspace viewport configurations.

```sql
CREATE TABLE layout_viewports (
    viewport_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    drawing_id UUID REFERENCES drawings(drawing_id) ON DELETE CASCADE,
    layout_name VARCHAR(255) NOT NULL,             -- 'Layout1', 'Sheet-C1.1'
    viewport_geometry GEOMETRY(PolygonZ) NOT NULL, -- Viewport boundary
    view_center GEOMETRY(PointZ),                  -- View center point in modelspace
    scale_factor NUMERIC(10, 4) DEFAULT 1.0,       -- Viewport scale (e.g., 0.0416667 = 1"=20')
    view_twist_angle NUMERIC(10, 4) DEFAULT 0.0,   -- Rotation angle
    frozen_layers TEXT[],                          -- Array of frozen layer names
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_viewports_drawing ON layout_viewports(drawing_id);
```

**Key Points:**
- Essential for multi-sheet drawings
- `frozen_layers` array for viewport layer control
- `scale_factor` represents viewport scale

---

### Tracking & Management Tables

#### `export_jobs` - DXF Export Job Tracking

Monitors DXF export operations with status and metrics.

```sql
CREATE TABLE export_jobs (
    export_job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    drawing_id UUID REFERENCES drawings(drawing_id) ON DELETE CASCADE,
    export_format VARCHAR(20) NOT NULL,            -- 'DXF', 'DWG'
    dxf_version VARCHAR(20),                       -- 'AC1027' (AutoCAD 2013), 'AC1032' (AutoCAD 2018)
    output_file_path TEXT,                         -- Path to generated file
    status VARCHAR(50) DEFAULT 'pending',          -- 'pending', 'processing', 'completed', 'failed'
    entities_exported INTEGER DEFAULT 0,
    text_exported INTEGER DEFAULT 0,
    dimensions_exported INTEGER DEFAULT 0,
    hatches_exported INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_export_jobs_drawing ON export_jobs(drawing_id);
```

**Key Points:**
- Tracks export progress and success/failure
- Stores metrics for exported entities
- `dxf_version` controls AutoCAD compatibility

---

#### `drawing_layer_usage` & `drawing_linetype_usage`

Track active layers and linetypes per drawing.

```sql
CREATE TABLE drawing_layer_usage (
    usage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    drawing_id UUID REFERENCES drawings(drawing_id) ON DELETE CASCADE,
    layer_name VARCHAR(255) NOT NULL,
    entity_count INTEGER DEFAULT 0,
    UNIQUE(drawing_id, layer_name)
);

CREATE TABLE drawing_linetype_usage (
    usage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    drawing_id UUID REFERENCES drawings(drawing_id) ON DELETE CASCADE,
    linetype_name VARCHAR(255) NOT NULL,
    entity_count INTEGER DEFAULT 0,
    UNIQUE(drawing_id, linetype_name)
);
```

**Key Points:**
- Aggregate statistics for optimization
- Used for purging unused layers/linetypes
- UNIQUE constraint prevents duplicates

---

## API Endpoints

### `POST /api/dxf/import`
Import a DXF file into the database.

**Request Type:** `multipart/form-data`

**Form Parameters:**
- `file` (file, required): DXF file to upload
- `drawing_id` (string, required): UUID of existing drawing record
- `import_modelspace` (boolean, default: true): Import modelspace entities
- `import_paperspace` (boolean, default: true): Import paperspace layouts

**Response:**
```json
{
  "success": true,
  "stats": {
    "entities": 1245,
    "text": 89,
    "dimensions": 34,
    "hatches": 12,
    "blocks": 567,
    "viewports": 3,
    "layers": ["C-BLDG", "C-ROAD", "C-UTIL", "A-WALL"],
    "linetypes": ["Continuous", "DASHED", "CENTER"],
    "errors": []
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "stats": {
    "entities": 0,
    "errors": [
      "Failed to parse LWPOLYLINE on layer C-ROAD",
      "Unknown block reference: VALVE-GATE"
    ]
  }
}
```

**Status Codes:**
- `200 OK`: Import successful
- `400 Bad Request`: Missing file or drawing_id
- `500 Internal Server Error`: Import failure

**Implementation Notes:**
- Uses `DXFImporter` class from `dxf_importer.py`
- Parses DXF with `ezdxf.readfile()`
- Stores entities in database with normalized FK structure
- Uses `DXFLookupService` for name-to-UUID resolution
- Wrapped in database transaction for atomicity

---

### `POST /api/dxf/export`
Export a drawing from database to DXF file.

**Request Body:**
```json
{
  "drawing_id": "abc123-uuid...",
  "dxf_version": "AC1027",
  "include_modelspace": true,
  "include_paperspace": true,
  "layer_filter": ["C-BLDG", "C-ROAD"]
}
```

**Required Fields:**
- `drawing_id` (UUID): Drawing to export

**Optional Fields:**
- `dxf_version` (string, default: "AC1027"): DXF version
  - `AC1027` = AutoCAD 2013
  - `AC1032` = AutoCAD 2018/2019/2020
  - `AC1024` = AutoCAD 2010
- `include_modelspace` (boolean, default: true)
- `include_paperspace` (boolean, default: true)
- `layer_filter` (array of strings): Only export specific layers

**Response:**
```json
{
  "success": true,
  "file_path": "/tmp/drawing_abc123_8f4a2b3c.dxf",
  "filename": "drawing_abc123_8f4a2b3c.dxf",
  "file_size": 2457893,
  "stats": {
    "entities": 1245,
    "text": 89,
    "dimensions": 34,
    "hatches": 12,
    "layers": ["C-BLDG", "C-ROAD", "C-UTIL"],
    "errors": []
  }
}
```

**Status Codes:**
- `200 OK`: Export successful, file available for download
- `400 Bad Request`: Missing drawing_id
- `404 Not Found`: Drawing not found
- `500 Internal Server Error`: Export failure

**Implementation Notes:**
- Uses `DXFExporter` class from `dxf_exporter.py`
- Creates new DXF document with `ezdxf.new(dxf_version)`
- Queries database for entities, text, dimensions, hatches
- Reconstructs DXF structure with layers, linetypes, blocks
- Saves file to `/tmp` directory
- Records export job in `export_jobs` table

---

### `GET /api/dxf/drawings`
Get list of drawings for DXF tools interface.

**Query Parameters:** None

**Response:**
```json
{
  "drawings": [
    {
      "drawing_id": "abc123-uuid...",
      "drawing_name": "Site Plan",
      "project_name": "Main Street Development",
      "client_name": "City of San Jose",
      "created_at": "2025-01-15T10:30:00Z",
      "entity_count": 1245,
      "text_count": 89
    }
  ]
}
```

**Implementation Notes:**
- Returns up to 100 most recent drawings
- Includes entity and text counts for each drawing
- Used by DXF tools UI to populate drawing selector

---

### `GET /api/dxf/export-jobs`
Get export job history.

**Query Parameters:** None

**Response:**
```json
{
  "jobs": [
    {
      "export_job_id": "job-uuid...",
      "drawing_id": "abc123-uuid...",
      "drawing_name": "Site Plan",
      "export_format": "DXF",
      "dxf_version": "AC1027",
      "status": "completed",
      "metrics": {
        "entities": 1245,
        "text": 89,
        "dimensions": 34,
        "hatches": 12
      },
      "started_at": "2025-01-20T14:30:00Z",
      "completed_at": "2025-01-20T14:30:15Z"
    },
    {
      "export_job_id": "job-uuid-2...",
      "drawing_id": "xyz789-uuid...",
      "drawing_name": "Grading Plan",
      "export_format": "DXF",
      "dxf_version": "AC1032",
      "status": "failed",
      "error_message": "Layer C-TOPO not found",
      "started_at": "2025-01-20T14:28:00Z",
      "completed_at": "2025-01-20T14:28:03Z"
    }
  ]
}
```

**Implementation Notes:**
- Returns up to 50 most recent export jobs
- Ordered by `started_at DESC`
- Includes success/failure status and metrics
- Used for monitoring and debugging exports

---

## DXF Lookup Service

### Purpose

The `DXFLookupService` resolves string names (layer names, linetype names, block names, etc.) to database UUIDs during import/export operations. It implements intelligent caching to avoid repeated database queries for the same names.

### Key Features

1. **Name-to-UUID Resolution**: Converts "C-BLDG" → UUID
2. **Auto-Creation**: Creates missing layers/linetypes on-the-fly during import
3. **Standards Linking**: Links to company standards when available
4. **Performance Caching**: Caches lookups in memory for speed
5. **Transaction Support**: Works within database transactions

### API Methods

```python
class DXFLookupService:
    def __init__(self, db_config: Dict, conn=None):
        """
        Args:
            db_config: Database connection config
            conn: Optional existing connection (for transactions)
        """
        
    def get_or_create_layer(self, layer_name: str, drawing_id: str = None,
                           color_aci: int = 7, linetype: str = 'Continuous') -> tuple:
        """
        Returns: (layer_id UUID, layer_standard_id UUID or None)
        """
        
    def get_or_create_linetype(self, linetype_name: str) -> str:
        """
        Returns: linetype_standard_id UUID
        """
        
    def get_or_create_textstyle(self, style_name: str) -> str:
        """
        Returns: text_style_id UUID
        """
        
    def get_or_create_hatch_pattern(self, pattern_name: str) -> str:
        """
        Returns: pattern_id UUID
        """
        
    def get_or_create_dimension_style(self, dimstyle_name: str) -> str:
        """
        Returns: dimension_style_id UUID
        """
        
    def record_layer_usage(self, drawing_id: str, layer_id: str, 
                          layer_standard_id: Optional[str] = None):
        """Record drawing layer usage for statistics"""
        
    def clear_cache(self):
        """Clear all cached lookups"""
```

### Usage Example

```python
from dxf_lookup_service import DXFLookupService

# Initialize with database config
lookup = DXFLookupService(db_config)

# Resolve layer name to UUID (creates if doesn't exist)
layer_id, layer_standard_id = lookup.get_or_create_layer(
    layer_name='C-BLDG',
    drawing_id='abc123-uuid',
    color_aci=1,
    linetype='Continuous'
)

# Use layer_id as foreign key for entities
entity_id = insert_entity(
    drawing_id='abc123-uuid',
    layer_id=layer_id,  # Normalized FK
    geometry=linestring_geom
)
```

---

## DXF Import Workflow

### Step-by-Step Process

```python
from dxf_importer import DXFImporter

# 1. Initialize importer
importer = DXFImporter(DB_CONFIG)

# 2. Import DXF file
stats = importer.import_dxf(
    file_path='/tmp/uploaded_file.dxf',
    drawing_id='abc123-uuid',
    import_modelspace=True,
    import_paperspace=True
)

# 3. Check results
if stats['errors']:
    print(f"Import completed with {len(stats['errors'])} errors")
else:
    print(f"Successfully imported {stats['entities']} entities")
```

### Import Statistics

```python
{
    'entities': 1245,      # Lines, arcs, circles, polylines, etc.
    'text': 89,            # Text and mtext entities
    'dimensions': 34,      # Dimension annotations
    'hatches': 12,         # Hatch patterns
    'blocks': 567,         # Block inserts
    'viewports': 3,        # Paperspace viewports
    'layers': {'C-BLDG', 'C-ROAD', 'C-UTIL'},  # Set of layer names
    'linetypes': {'Continuous', 'DASHED'},     # Set of linetypes
    'errors': []           # List of error messages
}
```

### Entity Type Mapping

| DXF Entity Type | Database Table | PostGIS Geometry Type |
|----------------|----------------|----------------------|
| LINE | `drawing_entities` | `LINESTRINGZ` |
| LWPOLYLINE | `drawing_entities` | `LINESTRINGZ` or `POLYGONZ` |
| ARC | `drawing_entities` | `LINESTRINGZ` (discretized) |
| CIRCLE | `drawing_entities` | `POLYGONZ` (discretized) |
| ELLIPSE | `drawing_entities` | `LINESTRINGZ` (discretized) |
| SPLINE | `drawing_entities` | `LINESTRINGZ` (discretized) |
| POINT | `drawing_entities` | `POINTZ` |
| TEXT / MTEXT | `drawing_text` | `POINTZ` (insertion point) |
| DIMENSION | `drawing_dimensions` | `LINESTRINGZ` (dimension line) |
| HATCH | `drawing_hatches` | `POLYGONZ` (boundary) |
| INSERT (block) | `block_inserts` | `POINTZ` (insertion point) |
| VIEWPORT | `layout_viewports` | `POLYGONZ` (viewport boundary) |

---

## DXF Export Workflow

### Step-by-Step Process

```python
from dxf_exporter import DXFExporter

# 1. Initialize exporter
exporter = DXFExporter(DB_CONFIG)

# 2. Export drawing to DXF
stats = exporter.export_dxf(
    drawing_id='abc123-uuid',
    output_path='/tmp/exported_drawing.dxf',
    dxf_version='AC1027',
    include_modelspace=True,
    include_paperspace=True,
    layer_filter=['C-BLDG', 'C-ROAD']  # Optional
)

# 3. Check results
if stats['errors']:
    print(f"Export completed with {len(stats['errors'])} errors")
else:
    print(f"Successfully exported {stats['entities']} entities")
```

### DXF Version Codes

| DXF Version Code | AutoCAD Version | Year |
|------------------|----------------|------|
| AC1009 | AutoCAD Release 12 | 1992 |
| AC1015 | AutoCAD 2000 | 1999 |
| AC1018 | AutoCAD 2004 | 2003 |
| AC1021 | AutoCAD 2007 | 2006 |
| AC1024 | AutoCAD 2010 | 2009 |
| AC1027 | AutoCAD 2013 | 2012 |
| AC1032 | AutoCAD 2018/2019/2020 | 2017+ |

**Recommendation:** Use `AC1027` (AutoCAD 2013) for maximum compatibility.

---

## Business Logic & Validation Rules

### Import Rules

1. **Layer Resolution:**
   - Check `layer_standards` for matching layer name
   - If found: Link via `layer_standard_id`
   - If not found: Create new `layers` record without standard link
   - Record in `drawing_layer_usage` for statistics

2. **Block Resolution:**
   - Check `block_standards` for matching block name
   - Store block_name as string (not FK) in `block_inserts`
   - Allows flexibility for non-standard blocks

3. **Geometry Conversion:**
   - All coordinates stored as PostGIS GeometryZ (3D)
   - Z-coordinate defaults to 0.0 if not provided
   - Curves (arcs, circles, ellipses) discretized to polylines
   - Splines approximated with polylines

4. **Transaction Safety:**
   - Entire import wrapped in database transaction
   - Rollback on any error to prevent partial imports
   - Clear lookup cache after successful import

### Export Rules

1. **Layer Export:**
   - Query all layers for drawing
   - Create layers in DXF with color, linetype, lineweight
   - Use layer properties from database or standards

2. **Entity Reconstruction:**
   - Convert PostGIS geometry back to DXF coordinates
   - Preserve color, linetype, lineweight overrides
   - Use `dxf_handle` if available for fidelity

3. **Block Export:**
   - Query block inserts
   - Create block references with scale, rotation
   - Populate block attributes from JSONB

4. **Job Tracking:**
   - Record export job in `export_jobs` table
   - Update status: pending → processing → completed/failed
   - Store metrics: entity counts, file size, errors

---

## Integration Tips for FastAPI

### Pydantic Models

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class DXFImportRequest(BaseModel):
    drawing_id: UUID
    import_modelspace: bool = True
    import_paperspace: bool = True

class DXFImportStats(BaseModel):
    entities: int = 0
    text: int = 0
    dimensions: int = 0
    hatches: int = 0
    blocks: int = 0
    viewports: int = 0
    layers: List[str] = []
    linetypes: List[str] = []
    errors: List[str] = []

class DXFImportResponse(BaseModel):
    success: bool
    stats: DXFImportStats

class DXFExportRequest(BaseModel):
    drawing_id: UUID
    dxf_version: str = "AC1027"
    include_modelspace: bool = True
    include_paperspace: bool = True
    layer_filter: Optional[List[str]] = None

class DXFExportResponse(BaseModel):
    success: bool
    file_path: str
    filename: str
    file_size: int
    stats: DXFImportStats  # Reuse same stats model

class ExportJob(BaseModel):
    export_job_id: UUID
    drawing_id: UUID
    drawing_name: str
    export_format: str
    dxf_version: Optional[str]
    status: str
    metrics: Optional[Dict[str, int]] = None
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class DrawingForDXF(BaseModel):
    drawing_id: UUID
    drawing_name: str
    project_name: Optional[str]
    client_name: Optional[str]
    created_at: datetime
    entity_count: int = 0
    text_count: int = 0
```

### SQLAlchemy Models

```python
from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, Numeric, UUID, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

class Layer(Base):
    __tablename__ = "layers"
    
    layer_id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    drawing_id = Column(UUID, ForeignKey("drawings.drawing_id", ondelete="CASCADE"), nullable=False)
    layer_name = Column(String(255), nullable=False)
    layer_standard_id = Column(UUID, ForeignKey("layer_standards.layer_standard_id"))
    color = Column(Integer)
    linetype = Column(String(100))
    lineweight = Column(Integer)
    is_frozen = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    
    # Relationships
    drawing = relationship("Drawing", back_populates="layers")
    layer_standard = relationship("LayerStandard")
    entities = relationship("DrawingEntity", back_populates="layer")

class BlockInsert(Base):
    __tablename__ = "block_inserts"
    
    insert_id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    drawing_id = Column(UUID, ForeignKey("drawings.drawing_id", ondelete="CASCADE"), nullable=False)
    block_name = Column(String(255), nullable=False)
    insertion_point = Column(Geometry('POINTZ'), nullable=False)
    scale_x = Column(Numeric(10, 4), default=1.0)
    scale_y = Column(Numeric(10, 4), default=1.0)
    scale_z = Column(Numeric(10, 4), default=1.0)
    rotation = Column(Numeric(10, 4), default=0.0)
    attributes = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    drawing = relationship("Drawing", back_populates="block_inserts")

class DrawingEntity(Base):
    __tablename__ = "drawing_entities"
    
    entity_id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    drawing_id = Column(UUID, ForeignKey("drawings.drawing_id", ondelete="CASCADE"), nullable=False)
    layer_id = Column(UUID, ForeignKey("layers.layer_id"))
    entity_type = Column(String(50), nullable=False)
    space_type = Column(String(20), default='MODEL')
    geometry = Column(Geometry('GEOMETRYZ'), nullable=False)
    dxf_handle = Column(String(100))
    color_aci = Column(Integer)
    linetype = Column(String(100))
    lineweight = Column(Integer)
    transparency = Column(Integer)
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    drawing = relationship("Drawing", back_populates="entities")
    layer = relationship("Layer", back_populates="entities")

class ExportJob(Base):
    __tablename__ = "export_jobs"
    
    export_job_id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    drawing_id = Column(UUID, ForeignKey("drawings.drawing_id", ondelete="CASCADE"), nullable=False)
    export_format = Column(String(20), nullable=False)
    dxf_version = Column(String(20))
    output_file_path = Column(Text)
    status = Column(String(50), default='pending')
    entities_exported = Column(Integer, default=0)
    text_exported = Column(Integer, default=0)
    dimensions_exported = Column(Integer, default=0)
    hatches_exported = Column(Integer, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    drawing = relationship("Drawing", back_populates="export_jobs")
```

### FastAPI Router Example

```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import tempfile
import os
from dxf_importer import DXFImporter
from dxf_exporter import DXFExporter

router = APIRouter(prefix="/api/dxf", tags=["dxf"])

@router.post("/import", response_model=DXFImportResponse)
async def import_dxf(
    file: UploadFile = File(...),
    drawing_id: str = Form(...),
    import_modelspace: bool = Form(True),
    import_paperspace: bool = Form(True),
    db: Session = Depends(get_db)
):
    """Import DXF file into database"""
    
    # Validate file type
    if not file.filename.lower().endswith('.dxf'):
        raise HTTPException(status_code=400, detail="File must be a DXF file")
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf') as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # Import DXF
        importer = DXFImporter(DB_CONFIG)
        stats = importer.import_dxf(
            tmp_path,
            drawing_id,
            import_modelspace=import_modelspace,
            import_paperspace=import_paperspace
        )
        
        return DXFImportResponse(
            success=len(stats['errors']) == 0,
            stats=DXFImportStats(**stats)
        )
    
    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@router.post("/export", response_model=DXFExportResponse)
def export_dxf(
    request: DXFExportRequest,
    db: Session = Depends(get_db)
):
    """Export drawing to DXF file"""
    
    # Generate output path
    output_filename = f'drawing_{request.drawing_id}_{uuid.uuid4().hex[:8]}.dxf'
    output_path = os.path.join('/tmp', output_filename)
    
    # Export DXF
    exporter = DXFExporter(DB_CONFIG)
    stats = exporter.export_dxf(
        str(request.drawing_id),
        output_path,
        dxf_version=request.dxf_version,
        include_modelspace=request.include_modelspace,
        include_paperspace=request.include_paperspace,
        layer_filter=request.layer_filter
    )
    
    # Get file size
    file_size = os.path.getsize(output_path)
    
    return DXFExportResponse(
        success=len(stats['errors']) == 0,
        file_path=output_path,
        filename=output_filename,
        file_size=file_size,
        stats=DXFImportStats(**stats)
    )

@router.get("/export/{job_id}/download")
def download_export(job_id: UUID, db: Session = Depends(get_db)):
    """Download exported DXF file"""
    
    job = db.query(ExportJob).filter(ExportJob.export_job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")
    
    if job.status != 'completed':
        raise HTTPException(status_code=400, detail="Export not completed")
    
    if not os.path.exists(job.output_file_path):
        raise HTTPException(status_code=404, detail="Export file not found")
    
    return FileResponse(
        job.output_file_path,
        media_type='application/dxf',
        filename=os.path.basename(job.output_file_path)
    )

@router.get("/drawings", response_model=List[DrawingForDXF])
def get_drawings_for_dxf(limit: int = 100, db: Session = Depends(get_db)):
    """Get list of drawings for DXF tools"""
    
    # Query with subquery counts
    drawings = db.query(
        Drawing.drawing_id,
        Drawing.drawing_name,
        Project.project_name,
        Project.client_name,
        Drawing.created_at,
        func.count(DrawingEntity.entity_id).label("entity_count"),
        func.count(DrawingText.text_id).label("text_count")
    ).outerjoin(Project).outerjoin(DrawingEntity).outerjoin(DrawingText)\
     .group_by(Drawing.drawing_id, Project.project_name, Project.client_name)\
     .order_by(Drawing.created_at.desc())\
     .limit(limit).all()
    
    return drawings

@router.get("/export-jobs", response_model=List[ExportJob])
def get_export_jobs(limit: int = 50, db: Session = Depends(get_db)):
    """Get export job history"""
    
    jobs = db.query(ExportJob).order_by(ExportJob.created_at.desc()).limit(limit).all()
    return jobs
```

---

## Testing Checklist

- [ ] Import simple DXF file (lines, arcs, text)
- [ ] Import complex DXF file (blocks, hatches, dimensions)
- [ ] Import DXF with modelspace and paperspace
- [ ] Import DXF with non-standard layers (verify auto-creation)
- [ ] Verify entity geometry stored as PostGIS GeometryZ
- [ ] Verify layer linkage to layer_standards when available
- [ ] Export drawing back to DXF
- [ ] Verify exported DXF opens in AutoCAD
- [ ] Test round-trip fidelity (import → export → compare)
- [ ] Test export with layer filter
- [ ] Test export with different DXF versions (AC1027, AC1032)
- [ ] Verify export job tracking (status, metrics, errors)
- [ ] Test lookup service caching performance
- [ ] Test import error handling (corrupt DXF file)
- [ ] Test export error handling (missing layers)
- [ ] Verify CASCADE delete (drawing deletion removes entities)
- [ ] Test spatial queries on entity geometry (intersection, buffer)
- [ ] Verify drawing_layer_usage statistics
- [ ] Test paperspace viewport export

---

## Migration Checklist

- [ ] Install PostGIS extension
- [ ] Install `ezdxf` Python library
- [ ] Create all DXF-related tables (16 tables)
- [ ] Configure GiST spatial indexes
- [ ] Implement DXFImporter class
- [ ] Implement DXFExporter class
- [ ] Implement DXFLookupService class
- [ ] Create API routes for import/export
- [ ] Add file upload handling (multipart/form-data)
- [ ] Add file download handling (FileResponse)
- [ ] Implement export job tracking
- [ ] Add transaction support for imports
- [ ] Configure temp file cleanup
- [ ] Add error handling for DXF parsing
- [ ] Document DXF version compatibility
- [ ] Create migration documentation for team

---

## Production Recommendations

### File Storage Strategy

For production systems with large DXF files:

1. **External Storage**: Store exported DXF files in S3/Azure Blob instead of `/tmp`
2. **Signed URLs**: Generate time-limited download URLs for security
3. **Cleanup Jobs**: Scheduled task to delete old export files (>7 days)

```python
# Example S3 integration
import boto3

s3_client = boto3.client('s3')

def upload_to_s3(local_path, bucket, key):
    s3_client.upload_file(local_path, bucket, key)
    return s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket, 'Key': key},
        ExpiresIn=3600  # 1 hour
    )
```

### Performance Optimization

1. **Batch Inserts**: Use batch INSERT for large imports
2. **Connection Pooling**: Reuse database connections
3. **Async Processing**: Use Celery/RQ for background DXF processing
4. **Progress Tracking**: WebSocket updates for long-running imports

### Spatial Query Optimization

```sql
-- Enable PostGIS spatial indexes
CREATE INDEX idx_entities_geometry ON drawing_entities USING GIST(geometry);
CREATE INDEX idx_text_geometry ON drawing_text USING GIST(insertion_point);
CREATE INDEX idx_hatches_geometry ON drawing_hatches USING GIST(boundary_geometry);

-- Example spatial query: Find all entities within bounding box
SELECT entity_id, entity_type, ST_AsText(geometry)
FROM drawing_entities
WHERE drawing_id = 'abc123-uuid'
  AND geometry && ST_MakeEnvelope(1000, 2000, 5000, 8000, 4326);
```

### Error Handling

```python
# Comprehensive error handling
try:
    stats = importer.import_dxf(file_path, drawing_id)
except ezdxf.DXFStructureError as e:
    # DXF file is corrupt or invalid
    return {"error": f"Invalid DXF file: {str(e)}"}
except psycopg2.IntegrityError as e:
    # Database constraint violation
    return {"error": f"Database error: {str(e)}"}
except Exception as e:
    # Unexpected error
    logger.exception("DXF import failed")
    return {"error": "Import failed unexpectedly"}
```

---

## Related Documentation

- **MIGRATION_DRAWINGS_MANAGER.md**: Drawings table and DXF content storage
- **MIGRATION_PROJECTS_MANAGER.md**: Project organization for drawings
- **create_dxf_export_schema.sql**: Complete SQL schema definition
- **dxf_importer.py**: DXF import implementation
- **dxf_exporter.py**: DXF export implementation
- **dxf_lookup_service.py**: Name-to-UUID resolution service

---

## Additional Resources

### ezdxf Documentation
- Official Docs: https://ezdxf.readthedocs.io/
- DXF Version Reference: https://ezdxf.readthedocs.io/en/stable/dxfinternals/fileencoding.html
- Entity Types: https://ezdxf.readthedocs.io/en/stable/dxfentities/index.html

### PostGIS Documentation
- Geometry Types: https://postgis.net/docs/using_postgis_dbmanagement.html#PostGIS_GeometryTypes
- Spatial Indexing: https://postgis.net/docs/using_postgis_dbmanagement.html#idm2855
- 3D Functions: https://postgis.net/docs/reference.html#PostGIS_3D_Functions

### AutoCAD DXF Reference
- DXF Format Specification: https://help.autodesk.com/view/OARX/2024/ENU/?guid=GUID-235B22E0-A567-4CF6-92D3-38A2306D73F3
