# CAD Layer Naming Standards
## Database-Driven DXF-to-Database Translation System

**Version:** 3.0  
**Last Updated:** November 2025  
**Purpose:** Define the bidirectional translation between DXF layer names and intelligent database objects

---

## Overview

This document establishes the **universal layer naming standard** for all CAD imports and exports. Layer names serve as the primary classifier for translating CAD geometry into intelligent database objects with rich metadata.

### Core Principle

**Layer Name = Object Classifier**

When importing DXF files:
- Layer name → parsed → determines object type, properties, database table
- Geometry stored with metadata (elevations, slopes, connectivity, etc.)

When re-importing modified DXF files:
- Same DXF handle + different layer → property update detected
- Database metadata preserved while layer-derived properties update

---

## Layer Naming Pattern

### Standard Format

```
[DISCIPLINE]-[CATEGORY]-[OBJECT_TYPE]-[PHASE]-[GEOMETRY]
```

### Component Definitions

| Component | Description | Source Table | Required |
|-----------|-------------|--------------|----------|
| **DISCIPLINE** | Design discipline | `discipline_codes` | Yes |
| **CATEGORY** | Object category within discipline | `category_codes` | Yes |
| **OBJECT_TYPE** | Specific object type | `object_type_codes` | Yes |
| **PHASE** | Construction phase | `phase_codes` | Optional |
| **GEOMETRY** | Geometry type indicator | `geometry_codes` | Optional |

### Delimiter Rules

- Primary delimiter: `-` (hyphen)
- Components are case-insensitive during import
- Export always uses UPPERCASE
- Spaces are not allowed

---

## Database Code Reference

### Discipline Codes

| Code | Full Name | Description | Typical Use |
|------|-----------|-------------|-------------|
| **CIV** | Civil | Civil engineering infrastructure | Utilities, roads, drainage |
| **SITE** | Site | Site development, grading | Grading plans, earthwork |
| **SURV** | Survey | Survey data, control points | Existing conditions, topo |
| **LAND** | Landscape | Planting, irrigation | Trees, planters, irrigation |
| **ARCH** | Architectural | Buildings, structures | Building elements |
| **UTIL** | Utility | General utilities | When not civil-led |
| **ANNO** | Annotation | Notes, labels, dimensions | Text, callouts |
| **XREF** | External Reference | Referenced DXF files | XREF boundaries |

### Category Codes (by Discipline)

#### Civil (CIV)
- **ROAD** - Streets, pavements, curbs
- **GRAD** - Earthwork, slopes, pads
- **STOR** - Stormwater, BMP, water quality
- **POND** - Detention/retention ponds
- **TANK** - Water storage tanks
- **ADA** - Accessibility features, ramps
- **EROS** - SWPPP, erosion control

#### Site (SITE)
- **GRAD** - Site grading, mass grading
- **DEMO** - Demolition work
- **FENCE** - Fences, gates, barriers
- **PAVE** - Parking lots, driveways
- **SIGN** - Site signage

#### Survey (SURV)
- **CTRL** - Control points, benchmarks
- **TOPO** - Topo shots, ground shots
- **BLDG** - Building corners, features
- **TREE** - Tree locations, sizes
- **BNDY** - Property boundaries

#### Landscape (LAND)
- **TREE** - Trees
- **SHRU** - Shrubs, plants
- **TURF** - Turf areas
- **IRIG** - Irrigation systems
- **HARD** - Paving, walkways, plazas

### Object Type Codes

#### Utilities (Category: STOR, ROAD, etc.)
| Code | Full Name | Database Table | Geometry |
|------|-----------|----------------|----------|
| **STORM** | Storm Drain | `utility_lines` | Line |
| **SANIT** | Sanitary Sewer | `utility_lines` | Line |
| **WATER** | Water | `utility_lines` | Line |
| **RECYC** | Recycled Water | `utility_lines` | Line |
| **GAS** | Gas | `utility_lines` | Line |
| **ELEC** | Electric | `utility_lines` | Line |
| **TELE** | Telecom | `utility_lines` | Line |
| **FIBER** | Fiber Optic | `utility_lines` | Line |
| **MH** | Manhole | `utility_structures` | Point |
| **INLET** | Inlet | `utility_structures` | Point |
| **CB** | Catch Basin | `utility_structures` | Point |
| **CLNOUT** | Cleanout | `utility_structures` | Point |
| **VALVE** | Valve | `utility_structures` | Point |
| **METER** | Meter | `utility_structures` | Point |
| **HYDRA** | Hydrant | `utility_structures` | Point |
| **PUMP** | Pump Station | `utility_structures` | Point |

#### Site Features
| Code | Full Name | Database Table | Geometry |
|------|-----------|----------------|----------|
| **CL** | Centerline | `horizontal_alignments` | Line |
| **CURB** | Curb | `drawing_entities` | Line |
| **GUTR** | Gutter | `drawing_entities` | Line |
| **SDWK** | Sidewalk | `drawing_entities` | Polygon |

### Phase Codes

| Code | Full Name | Color | Description |
|------|-----------|-------|-------------|
| **EXIST** | Existing | Gray (#808080) | Existing features to remain |
| **DEMO** | Demolish | Red (#FF0000) | To be demolished/removed |
| **NEW** | New | Blue (#0000FF) | New construction |
| **TEMP** | Temporary | Orange (#FFA500) | Temporary work |
| **FUTR** | Future | Purple (#800080) | Future phase |
| **PROP** | Proposed | Green (#00FF00) | Proposed (generic) |
| **PH1** | Phase 1 | Cyan (#00FFFF) | Construction phase 1 |
| **PH2** | Phase 2 | Magenta (#FF00FF) | Construction phase 2 |
| **PH3** | Phase 3 | Yellow (#FFFF00) | Construction phase 3 |

### Geometry Codes

| Code | Full Name | DXF Entity Types | Use Case |
|------|-----------|------------------|----------|
| **LN** | Line/Polyline | LINE, LWPOLYLINE, POLYLINE | Linear features |
| **PT** | Point | POINT | Point features |
| **PG** | Polygon/Area | LWPOLYLINE (closed), HATCH | Area features |
| **TX** | Text/Label | TEXT, MTEXT | Annotations |
| **3D** | 3D Object | 3DFACE, SOLID, MESH | 3D entities |
| **BK** | Block Reference | INSERT | Block instances |
| **HT** | Hatch Pattern | HATCH | Hatch patterns |
| **DIM** | Dimension | DIMENSION | Dimensions |

---

## Layer Naming Examples

### Gravity Pipe Networks

#### Storm Drain System
```
CIV-STOR-STORM-NEW-LN          → New 12" storm drain pipe
CIV-STOR-STORM-EXIST-LN        → Existing storm drain pipe
CIV-STOR-MH-NEW-PT             → New storm manhole
CIV-STOR-CB-NEW-PT             → New catch basin
CIV-STOR-INLET-EXIST-PT        → Existing inlet
```

**Database Translation:**
- `CIV-STOR-STORM-NEW-LN` creates `utility_lines` record:
  - `utility_system` = "Storm"
  - `utility_mode` = "gravity"
  - `phase` = "New"
  - Geometry: LINESTRING Z

#### Sanitary Sewer System
```
CIV-STOR-SANIT-NEW-LN          → New sanitary sewer pipe
CIV-STOR-SANIT-EXIST-LN        → Existing sanitary sewer
CIV-STOR-MH-NEW-PT             → New sanitary manhole
CIV-STOR-CLNOUT-NEW-PT         → New cleanout
```

### Pressure Pipe Networks

#### Water System
```
CIV-ROAD-WATER-NEW-LN          → New water main
CIV-ROAD-WATER-EXIST-LN        → Existing water main
CIV-ROAD-HYDRA-NEW-PT          → New fire hydrant
CIV-ROAD-VALVE-NEW-PT          → New water valve
CIV-ROAD-METER-NEW-PT          → New water meter
```

**Database Translation:**
- `CIV-ROAD-WATER-NEW-LN` creates `utility_lines` record:
  - `utility_system` = "Water"
  - `utility_mode` = "pressure"
  - `phase` = "New"

#### Recycled Water
```
CIV-ROAD-RECYC-NEW-LN          → New recycled water pipe
CIV-ROAD-RECYC-EXIST-LN        → Existing recycled water
```

### Alignments and Linear Features

```
CIV-ROAD-CL-EXIST-LN           → Existing road centerline
CIV-ROAD-CL-PROP-LN            → Proposed road centerline
CIV-ROAD-CURB-NEW-LN           → New curb
CIV-ROAD-GUTR-NEW-LN           → New gutter
CIV-ROAD-SDWK-NEW-PG           → New sidewalk (polygon)
```

**Database Translation:**
- `CIV-ROAD-CL-PROP-LN` creates `horizontal_alignments` record
- `CIV-ROAD-CURB-NEW-LN` creates `drawing_entities` record with type metadata

### Grading and Earthwork

```
CIV-GRAD-PAD-PROP-PG           → Proposed building pad
SITE-GRAD-SLOPE-PROP-PG        → Proposed slope area
CIV-GRAD-RETWALL-NEW-LN        → New retaining wall
```

### Landscape Features

```
LAND-TREE-TREE-EXIST-PT        → Existing tree to remain
LAND-TREE-TREE-DEMO-PT         → Tree to be removed
LAND-TREE-TREE-PROP-PT         → Proposed new tree
LAND-SHRU-SHRU-PROP-PG         → Proposed shrub planting area
LAND-IRIG-IRIG-NEW-LN          → New irrigation line
LAND-HARD-HARD-NEW-PG          → New hardscape paving
```

**Database Translation:**
- `LAND-TREE-TREE-EXIST-PT` creates `site_trees` record
- `LAND-IRIG-IRIG-NEW-LN` creates `utility_lines` record (irrigation system)

### Survey Features

```
SURV-CTRL-CTRL-EXIST-PT        → Existing control point
SURV-TOPO-TOPO-EXIST-PT        → Existing topo shot
SURV-BNDY-BNDY-EXIST-LN        → Existing property boundary
SURV-BLDG-BLDG-EXIST-PT        → Existing building corner
```

**Database Translation:**
- `SURV-CTRL-CTRL-EXIST-PT` creates `survey_points` record with control flag
- `SURV-TOPO-TOPO-EXIST-PT` creates `survey_points` record (ground shot)

### BMPs and Water Quality

```
CIV-STOR-BIO-NEW-PG            → New bioretention basin
CIV-STOR-FILT-NEW-PG           → New filter strip
CIV-POND-POND-NEW-PG           → New detention pond
```

**Database Translation:**
- `CIV-STOR-BIO-NEW-PG` creates `bmps` record with type="Bioretention"

### Annotations and Labels

```
ANNO-ANNO-NOTE-PROP-TX         → Proposed note text
ANNO-ANNO-DIM-PROP-DIM         → Proposed dimension
CIV-STOR-LABEL-NEW-TX          → New storm drain label
```

### Block References

```
CIV-STOR-MH-NEW-BK             → Manhole block
CIV-ROAD-SIGN-NEW-BK           → Sign block
LAND-TREE-TREE-PROP-BK         → Tree block symbol
```

**Database Translation:**
- Block INSERT on these layers creates both block reference AND intelligent object
- Block name provides additional detail (e.g., "MH-48-STORM")

---

## Size and Material Encoding

### Pipe Diameter Patterns

For utility pipes, diameter can be encoded in the object type or layer name:

#### Option 1: Size in Object Type Code
```
CIV-STOR-12STORM-NEW-LN        → 12" storm drain
CIV-ROAD-8WATER-NEW-LN         → 8" water main
CIV-STOR-18SANIT-NEW-LN        → 18" sanitary sewer
```

#### Option 2: Size as Separate Component
```
CIV-STOR-STORM-12IN-NEW-LN     → 12" storm drain
CIV-ROAD-WATER-8IN-NEW-LN      → 8" water main
```

**Parsing Rules:**
- Extract digits followed by optional unit (IN, MM, FT)
- Convert to mm for database storage
- If no unit specified, assume inches for imperial projects

### Material Encoding

Material can optionally be included:

```
CIV-STOR-STORM-PVC-NEW-LN      → PVC storm pipe
CIV-ROAD-WATER-DI-NEW-LN       → Ductile iron water main
CIV-STOR-SANIT-VCP-EXIST-LN    → Vitrified clay pipe sanitary
```

**Common Material Codes:**
- **PVC** - PVC pipe
- **DI** - Ductile iron
- **VCP** - Vitrified clay pipe
- **HDPE** - High-density polyethylene
- **RCP** - Reinforced concrete pipe
- **CMP** - Corrugated metal pipe
- **CONC** - Concrete

---

## Import Workflow

### First Import: DXF → Database

1. **Entity Reading**
   - DXF entities read with ezdxf library
   - Layer name, geometry, handle extracted

2. **Layer Classification**
   - Parse layer name into components (discipline, category, object type, phase, geometry)
   - Query database codes tables for validation
   - Extract properties (size, material, etc.)
   - Determine target database table

3. **Confidence Scoring**
   - Exact code matches: 100% confidence
   - Partial matches: 70-90% confidence
   - Unknown patterns: <70% (not imported as intelligent object)

4. **Object Creation**
   - Create record in appropriate table (`utility_lines`, `utility_structures`, etc.)
   - Store geometry as PostGIS GeometryZ (SRID 2226)
   - Store layer-derived properties (diameter, phase, utility system)
   - Store metadata (material, elevations, etc. from other sources)

5. **Entity Linking**
   - Create `dxf_entity_links` record
   - Links DXF handle → database object
   - Enables change detection on re-import

### Re-Import: Modified DXF → Database Updates

1. **Entity Matching**
   - Match DXF handle to existing `dxf_entity_links` record
   - Identify corresponding database object

2. **Change Detection**
   - **Geometry changed:** Update geometry field
   - **Layer changed:** Re-classify and update properties
   - **Both changed:** Update geometry + properties
   - **Deleted from DXF:** Mark as deleted or remove link

3. **Property Updates**
   - Parse new layer name
   - Update diameter, phase, material, etc.
   - **Preserve** metadata not derivable from layer (elevations, slopes, connectivity)

4. **Example:**
   ```
   Original:  CIV-STOR-STORM-12IN-NEW-LN (12" storm pipe)
   Modified:  CIV-STOR-STORM-18IN-NEW-LN (changed to 18")
   
   Database Update:
   - diameter_mm: 304.8 → 457.2
   - geometry: unchanged
   - invert_elevation: PRESERVED
   - from_structure_id: PRESERVED
   ```

---

## Export Workflow

### Database → DXF Layer Generation

1. **Object Query**
   - Query objects from database (e.g., all `utility_lines` for project)
   - Include properties: discipline, category, type, phase, diameter, material

2. **Layer Name Generation**
   - Look up codes from database tables
   - Construct layer name: `[DISC]-[CAT]-[TYPE]-[PHASE]-[GEOM]`
   - Add size/material if present

3. **Example:**
   ```
   Database Record:
   - Table: utility_lines
   - utility_system: "Storm"
   - utility_mode: "gravity"
   - diameter_mm: 304.8
   - phase: "New"
   
   Generated Layer: CIV-STOR-12STORM-NEW-LN
   ```

4. **DXF Entity Creation**
   - Convert PostGIS geometry to DXF entities
   - Assign to generated layer
   - Preserve or create DXF handle
   - Update `dxf_entity_links` table

---

## Classifier Algorithm

### Layer Name Parsing

```python
def parse_layer_name(layer_name: str) -> dict:
    """
    Parse layer name into components.
    
    Examples:
        "CIV-STOR-12STORM-NEW-LN" → {
            discipline: "CIV",
            category: "STOR",
            object_type: "12STORM",
            phase: "NEW",
            geometry: "LN",
            diameter: 12,
            unit: "IN"
        }
    """
    parts = layer_name.upper().split('-')
    
    # Query database for valid codes
    discipline = lookup_discipline_code(parts[0])
    category = lookup_category_code(parts[1], discipline)
    
    # Extract size from object type if present
    object_type, diameter = extract_size(parts[2])
    object_type_record = lookup_object_type_code(object_type, category)
    
    phase = lookup_phase_code(parts[3]) if len(parts) > 3 else None
    geometry = lookup_geometry_code(parts[4]) if len(parts) > 4 else None
    
    return {
        'discipline': discipline,
        'category': category,
        'object_type': object_type_record,
        'phase': phase,
        'geometry': geometry,
        'diameter': diameter,
        'confidence': calculate_confidence(...)
    }
```

### Database Table Mapping

```python
def determine_database_table(classification: dict) -> str:
    """
    Determine which database table to use based on classification.
    """
    object_type_code = classification['object_type']
    
    # Query object_type_codes table for database_table
    return object_type_code.database_table
    
    # Examples:
    # STORM → utility_lines
    # MH → utility_structures
    # CL → horizontal_alignments
    # TREE → site_trees
```

---

## Validation Rules

### Required Components

- **Minimum:** `[DISCIPLINE]-[CATEGORY]-[OBJECT_TYPE]`
- **Recommended:** `[DISCIPLINE]-[CATEGORY]-[OBJECT_TYPE]-[PHASE]-[GEOMETRY]`

### Code Validation

All codes must exist in respective database tables:
- `discipline_codes`
- `category_codes` (with matching discipline)
- `object_type_codes` (with matching category)
- `phase_codes`
- `geometry_codes`

### Geometry Type Matching

Classifier validates that DXF entity type matches expected geometry:

```
Layer: CIV-STOR-STORM-NEW-LN
DXF Entity: LWPOLYLINE → ✓ Valid (LN accepts LINE, LWPOLYLINE)

Layer: CIV-STOR-MH-NEW-PT
DXF Entity: POINT → ✓ Valid (PT accepts POINT)

Layer: CIV-STOR-STORM-NEW-PT
DXF Entity: LWPOLYLINE → ✗ Invalid (PT expects POINT, not line)
```

---

## Edge Cases and Special Rules

### Mixed Geometry Layers

If a layer contains mixed geometry (e.g., lines and points), omit geometry code:

```
CIV-STOR-STORM-NEW              → Accepts any geometry type
```

### Legacy Layer Names

For compatibility with old naming conventions:

```
12IN-STORM          → Classified as CIV-STOR-STORM (inferred)
MH-STORM-48         → Classified as CIV-STOR-MH
STORM-PROPOSED      → Classified as CIV-STOR-STORM-PROP
```

**Confidence:** Legacy patterns receive lower confidence (70-85%)

### Ambiguous Cases

When multiple interpretations possible:
1. Check project context (assigned standards)
2. Use most common interpretation
3. Present options to user for manual selection

### Unknown Layers

Layers that don't match any pattern:
- Imported as `drawing_entities` only
- No intelligent object created
- Flagged for manual review

---

## Implementation Notes

### Database Lookups

Classifier queries these tables during import:
- `discipline_codes`
- `category_codes`
- `object_type_codes`
- `phase_codes`
- `geometry_codes`

**Performance Optimization:**
- Cache codes in memory during import batch
- Pre-load all codes at classifier initialization
- Use dictionary lookups (O(1)) instead of database queries per entity

### Extensibility

To add new object types:
1. Insert into `object_type_codes` table
2. Specify target `database_table`
3. No code changes needed - classifier auto-detects

To add new disciplines/categories:
1. Insert into respective codes tables
2. Classifier automatically supports new combinations

---

## Future Enhancements

### Planned Features

1. **Fuzzy Matching**
   - Handle typos: "STROM" → "STORM"
   - Abbreviation variants: "SAN" → "SANIT"

2. **Machine Learning Classification**
   - Learn from user corrections
   - Improve confidence scoring over time

3. **Multi-Standard Support**
   - Support multiple layer naming standards per project
   - Auto-detect standard from layer patterns

4. **Block Attribute Integration**
   - Extract properties from block attributes
   - Override layer-derived properties with attribute data

---

## Quick Reference

### Common Gravity Pipe Layers

| Layer Name | Object | Database Table |
|------------|--------|----------------|
| `CIV-STOR-STORM-NEW-LN` | Storm drain pipe | `utility_lines` |
| `CIV-STOR-SANIT-NEW-LN` | Sanitary sewer pipe | `utility_lines` |
| `CIV-STOR-MH-NEW-PT` | Manhole | `utility_structures` |
| `CIV-STOR-CB-NEW-PT` | Catch basin | `utility_structures` |
| `CIV-STOR-INLET-NEW-PT` | Inlet | `utility_structures` |
| `CIV-STOR-CLNOUT-NEW-PT` | Cleanout | `utility_structures` |

### Common Pressure Pipe Layers

| Layer Name | Object | Database Table |
|------------|--------|----------------|
| `CIV-ROAD-WATER-NEW-LN` | Water main | `utility_lines` |
| `CIV-ROAD-RECYC-NEW-LN` | Recycled water | `utility_lines` |
| `CIV-ROAD-HYDRA-NEW-PT` | Fire hydrant | `utility_structures` |
| `CIV-ROAD-VALVE-NEW-PT` | Water valve | `utility_structures` |
| `CIV-ROAD-METER-NEW-PT` | Water meter | `utility_structures` |

---

**Document Control:**
- Location: `/docs/CAD_LAYER_NAMING_STANDARDS.md`
- Referenced by: `layer_classifier_v3.py`, DXF import/export modules
- Updates: Modify when adding new codes to database tables
