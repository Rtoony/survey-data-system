# Revolutionary CAD Standards for Database-Optimized Civil Engineering

## Design Philosophy

**Core Principle**: The database is the source of truth. Layer names are just semantic labels that describe what the database already knows.

**Layer Name Format**: `DISCIPLINE-CATEGORY-TYPE-ATTRIBUTES-PHASE-GEOMETRY`

Example: `CIV-UTIL-STORM-12IN-NEW-LN` = Civil utility storm pipe, 12 inches, new construction, line geometry

---

## 1. Discipline Codes (What field of work)

| Code | Full Name | Description |
|------|-----------|-------------|
| CIV | Civil | Civil engineering infrastructure |
| SITE | Site | Site development, grading, earthwork |
| SURV | Survey | Survey data, control points, topo |
| LAND | Landscape | Planting, irrigation, landscape features |
| ARCH | Architectural | Buildings, structures, architecture |
| UTIL | Utility | General utilities (when not civil-led) |
| ANNO | Annotation | Notes, labels, dimensions, callouts |
| XREF | External Reference | Referenced drawings |

---

## 2. Category Codes (What type of system)

### Civil (CIV) Categories
| Code | Full Name | Description |
|------|-----------|-------------|
| UTIL | Utility | All underground utilities |
| ROAD | Road | Streets, pavements, curbs |
| GRAD | Grading | Earthwork, slopes, pads |
| STOR | Stormwater | Storm drainage, BMP, water quality |
| POND | Pond | Detention/retention ponds |
| TANK | Tank | Water storage tanks |
| ADA | ADA | Accessibility features, ramps, paths |
| EROS | Erosion Control | SWPPP, erosion control measures |

### Site (SITE) Categories
| Code | Full Name | Description |
|------|-----------|-------------|
| GRAD | Grading | Site grading, mass grading |
| DEMO | Demolition | Demolition work |
| FENCE | Fencing | Fences, gates, barriers |
| PAVE | Pavement | Parking lots, driveways |
| WALL | Retaining Wall | Retaining walls, seat walls |
| SIGN | Signage | Site signage |

### Survey (SURV) Categories
| Code | Full Name | Description |
|------|-----------|-------------|
| CTRL | Control | Control points, benchmarks |
| TOPO | Topographic | Topo shots, ground shots |
| BLDG | Building | Building corners, features |
| UTIL | Utility | Located utilities |
| TREE | Tree | Tree locations, sizes |
| BNDY | Boundary | Property boundaries |

### Landscape (LAND) Categories
| Code | Full Name | Description |
|------|-----------|-------------|
| TREE | Trees | Trees, palms |
| SHRU | Shrubs | Shrubs, plants |
| TURF | Turf | Lawn, groundcover |
| IRIG | Irrigation | Irrigation systems |
| HARD | Hardscape | Paving, walkways, plazas |

---

## 3. Object Type Codes (Specific object)

### Utility Types (UTIL Category)
| Code | Full Name | Attributes |
|------|-----------|------------|
| STORM | Storm Drain | diameter, material |
| SANIT | Sanitary Sewer | diameter, material |
| WATER | Water | diameter, material, pressure |
| RECYC | Recycled Water | diameter, material |
| GAS | Gas | diameter, pressure |
| ELEC | Electric | voltage, type |
| TELE | Telecom | type |
| FIBER | Fiber Optic | type |
| JOINT | Joint Trench | contents |

### Structure Types (Within UTIL)
| Code | Full Name | Attributes |
|------|-----------|------------|
| MH | Manhole | utility_type, diameter |
| INLET | Inlet | type, grate_type |
| CB | Catch Basin | type |
| CLNOUT | Cleanout | utility_type |
| VALVE | Valve | type, size |
| METER | Meter | utility_type |
| HYDRA | Hydrant | type |
| PUMP | Pump Station | capacity |
| JBOX | Junction Box | type |

### Road Types (ROAD Category)
| Code | Full Name | Attributes |
|------|-----------|------------|
| CL | Centerline | classification |
| CURB | Curb | type (vertical, rolled, mountable) |
| GUTR | Gutter | width |
| SDWK | Sidewalk | width, material |
| PVMT | Pavement | type, thickness |
| STRP | Striping | type, color |
| RAMP | Ramp | slope, type |

### Stormwater Types (STOR Category)
| Code | Full Name | Attributes |
|------|-----------|------------|
| BIORT | Bioretention | area, depth |
| SWALE | Swale | type |
| BASIN | Detention Basin | volume |
| FILTR | Filter | type |
| VNDR | Vendor Device | manufacturer, model |
| PERVP | Pervious Pavement | type, area |

### ADA Types (ADA Category)
| Code | Full Name | Attributes |
|------|-----------|------------|
| RAMP | Accessible Ramp | slope, width, landing |
| PATH | Accessible Path | width, surface |
| PARK | Accessible Parking | type, van_accessible |
| DCRB | Detectable Curb Ramp | type |
| SIGN | ADA Signage | type |

### Grading Types (GRAD Category)
| Code | Full Name | Attributes |
|------|-----------|------------|
| CNTR | Contour | elevation, interval |
| SPOT | Spot Elevation | elevation |
| SLOPE | Slope | ratio |
| PAD | Building Pad | elevation |
| SWALE | Swale | depth, bottom_width |
| BERM | Berm | height |

---

## 4. Attribute Codes (Object properties)

### Size/Dimension Attributes
| Pattern | Example | Meaning |
|---------|---------|---------|
| ##IN | 12IN | Diameter in inches |
| ##FT | 4FT | Width/height in feet |
| ###CF | 500CF | Volume in cubic feet |
| ###AC | 2AC | Area in acres |
| ###SF | 1000SF | Area in square feet |
| PCT## | PCT15 | Percentage (15%) |
| SLP## | SLP2:1 | Slope ratio |

### Material Attributes
| Code | Full Name |
|------|-----------|
| PVC | PVC |
| HDPE | HDPE |
| RCP | Reinforced Concrete Pipe |
| VCP | Vitrified Clay Pipe |
| DI | Ductile Iron |
| CONC | Concrete |
| AC | Asphalt Concrete |
| PVCC | PVC Concrete |

### Type/Style Attributes
| Code | Meaning |
|------|---------|
| A/B/C | Type variants |
| STD | Standard |
| CUST | Custom |
| TYP | Typical |

---

## 5. Phase Codes (Construction timing)

| Code | Full Name | Description |
|------|-----------|-------------|
| EXIST | Existing | Existing features to remain |
| DEMO | Demolish | To be demolished/removed |
| NEW | New | New construction |
| TEMP | Temporary | Temporary work |
| FUTR | Future | Future phase |
| PROP | Proposed | Proposed (generic) |
| PH1/2/3 | Phase 1/2/3 | Specific construction phases |

---

## 6. Geometry Codes (CAD representation)

| Code | Geometry Type | DXF Entity Types |
|------|---------------|------------------|
| LN | Line/Polyline | LINE, LWPOLYLINE, POLYLINE |
| PT | Point | POINT, INSERT (block) |
| PG | Polygon/Area | LWPOLYLINE (closed), HATCH |
| TX | Text/Label | TEXT, MTEXT |
| 3D | 3D Object | 3DFACE, SOLID, MESH |
| BK | Block Reference | INSERT |
| HT | Hatch Pattern | HATCH |
| DIM | Dimension | DIMENSION |

---

## Complete Layer Name Examples

### Utilities
```
CIV-UTIL-STORM-12IN-NEW-LN           Storm drain pipe, 12", new, line
CIV-UTIL-STORM-MH-EXIST-PT           Storm manhole, existing, point
CIV-UTIL-WATER-8IN-PVC-FUTR-LN       Water pipe, 8" PVC, future, line
CIV-UTIL-SANIT-CLNOUT-NEW-PT         Sanitary cleanout, new, point
```

### Roads
```
CIV-ROAD-CL-NEW-LN                   Road centerline, new, line
CIV-ROAD-CURB-6IN-NEW-LN             Curb, 6", new, line
CIV-ROAD-SDWK-5FT-ADA-NEW-PG         Sidewalk, 5' wide, ADA compliant, polygon
CIV-ROAD-RAMP-8PCT-NEW-PG            Ramp, 8% slope, new, polygon
```

### Stormwater BMPs
```
CIV-STOR-BIORT-500CF-NEW-PG          Bioretention, 500 CF, new, polygon
CIV-STOR-SWALE-GRASS-NEW-LN          Grass swale, new, line
CIV-STOR-BASIN-2AC-NEW-PG            Detention basin, 2 acres, new, polygon
```

### Grading
```
SITE-GRAD-CNTR-EXIST-LN              Existing contour, line
SITE-GRAD-CNTR-PROP-LN               Proposed contour, line
SITE-GRAD-SPOT-NEW-TX                Spot elevation, new, text
SITE-GRAD-PAD-FF100-NEW-PG           Building pad, FF=100', new, polygon
```

### Survey
```
SURV-CTRL-MONUMENT-EXIST-PT          Control monument, existing, point
SURV-TOPO-SHOT-EXIST-PT              Topo shot, existing, point
SURV-TREE-OAK-24IN-EXIST-PT          Oak tree, 24" diameter, existing, point
```

### ADA
```
CIV-ADA-RAMP-2PCT-NEW-PG             ADA ramp, 2% slope, new, polygon
CIV-ADA-PATH-5FT-NEW-PG              Accessible path, 5' wide, new, polygon
CIV-ADA-PARK-VAN-NEW-PG              Van accessible parking, new, polygon
```

### Landscape
```
LAND-TREE-OAK-24IN-NEW-PT            Oak tree, 24" box, new, point
LAND-IRIG-LATERAL-1IN-NEW-LN         Irrigation lateral, 1", new, line
LAND-HARD-PAVING-CONC-NEW-PG         Concrete paving, new, polygon
```

### Annotation
```
ANNO-NOTE-GENERAL-TX                 General note, text
ANNO-LABEL-UTIL-TX                   Utility label, text
ANNO-DIM-PLAN-DIM                    Plan dimension
```

---

## Design Rules

### 1. Order Matters
Always: `DISCIPLINE-CATEGORY-TYPE-[ATTRIBUTES]-PHASE-GEOMETRY`

Attributes are flexible and can be combined: `12IN-PVC` or `500CF-CONC`

### 2. Uniqueness
Each complete layer name should represent a unique combination of properties.

### 3. Parsing Logic
- Split by `-`
- First segment = Discipline (required)
- Second segment = Category (required)
- Third segment = Type (required)
- Last segment = Geometry (required)
- Second-to-last segment = Phase (required)
- Middle segments = Attributes (variable, optional)

### 4. Database First
The layer name is generated FROM database properties, not parsed TO create them.
Layer names are display labels, not data storage.

---

## Migration Strategy

### For Import (Client CAD → Database)
1. Use regex pattern matching to extract intent from client layers
2. Map to standard object types in database
3. Store original layer name for reference
4. Generate standard layer name for export

### For Export (Database → CAD)
1. Query object properties from database
2. Apply export template rules
3. Generate layer name using standard format (or client-specific variant)
4. Create DXF entities on generated layers

---

## Why This Works

1. **Human-Readable**: Engineers can understand `CIV-UTIL-STORM-12IN-NEW-LN` at a glance
2. **Machine-Parseable**: Regex patterns can extract every component
3. **Flexible**: Attributes can be combined as needed
4. **Extensible**: New codes can be added without breaking existing patterns
5. **Database-Optimized**: Properties live in database, layer name is just a view
6. **Multi-Client**: Can map TO this standard FROM various client formats
7. **AI-Friendly**: Clear hierarchy makes LLM processing straightforward

---

# EXTENDED NAMING CONVENTIONS: ALL CAD ELEMENTS

## Overview

The layer naming convention (DISCIPLINE-CATEGORY-TYPE-ATTRIBUTES-PHASE-GEOMETRY) is extended to cover all CAD element types. Each element type adapts the pattern while maintaining machine parseability and semantic alignment.

---

## 7. Block/Symbol Naming Convention

### Format
`DISCIPLINE-CATEGORY-TYPE-[ATTRIBUTES]-PHASE-FORM`

**FORM** replaces GEOMETRY with one of:
- `DEF` = Block Definition (stored in `block_definitions` table)
- `INST` = Block Instance (placed in drawing, may have context qualifiers)

### Block Definition Examples
```
CIV-UTIL-MH-STORM-48IN-NEW-DEF       Storm manhole, 48", new construction, definition
CIV-UTIL-HYDRA-FIRE-6IN-EXIST-DEF    Fire hydrant, 6" outlet, existing, definition
CIV-UTIL-VALVE-WATER-8IN-GATE-NEW-DEF    Water valve, 8", gate type, new, definition
CIV-ROAD-SIGN-STOP-36IN-MUTCD-NEW-DEF    Stop sign, 36", MUTCD standard, new, definition
LAND-TREE-OAK-COAST-24IN-NEW-DEF     Coast live oak, 24" box, new, definition
SURV-CTRL-MONUMENT-BRASS-EXIST-DEF   Control monument, brass cap, existing, definition
```

### Block Instance Examples
```
CIV-UTIL-MH-STORM-48IN-NEW-INST      Storm manhole instance (basic)
CIV-UTIL-MH-STORM-48IN-SHT5-NEW-INST Storm manhole instance, sheet 5 context, new
CIV-ROAD-SIGN-STOP-36IN-MUTCD-INT1-NEW-INST Stop sign, intersection 1 context, new
```

### Block Naming Rules
1. **Definition (DEF)**: Canonical name stored in `block_definitions.name`
2. **Instance (INST)**: May append context like sheet number, detail callout, or location in ATTRIBUTES segment
3. **TYPE**: The object type category (MH=manhole, HYDRA=hydrant, VALVE, INLET, etc.)
4. **Attributes**: First attribute often identifies the system (STORM, WATER, SANIT) which links to keynote THEME and detail FAMILY; additional attributes specify size, material, type variant (GATE, MUTCD, etc.)
5. **Phase**: Uses standard phase codes (EXIST, NEW, TEMP, DEMO, FUTR, PROP, PH1/2/3)
6. **Cross-Reference**: Block's first ATTRIBUTE (STORM, WATER, CURB, etc.) aligns with keynote THEME and detail FAMILY for semantic linkage

### Block Type Codes
| Code | Type | Examples |
|------|----------|----------|
| SYMB | Generic Symbol | North arrow, title block, detail bubble |
| MH | Manhole | Storm, sanitary, telecom manholes |
| HYDRA | Hydrant | Fire hydrant types |
| VALVE | Valve | All valve types |
| INLET | Inlet/CB | Drainage inlets, catch basins |
| SIGN | Signage | Traffic, street name, regulatory |
| TREE | Tree Symbol | Landscape tree symbols |
| LIGHT | Light Fixture | Site lighting |
| BENCH | Furniture | Site furniture, benches, tables |

---

## 8. Detail Naming Convention

### Format
`DISCIPLINE-DETAIL-FAMILY-SEQUENCE-[ATTRIBUTES]-PHASE-VIEW`

**VIEW** replaces GEOMETRY with:
- `PLAN` = Plan view detail
- `SECT` = Section/profile detail
- `ELEV` = Elevation view detail
- `ISO` = Isometric/3D view
- `SCHEM` = Schematic diagram

**SEQUENCE** = Three-digit number (001-999) stored in `detail_standards.detail_number`

### Detail Name Examples
```
CIV-DETAIL-CURB-001-6IN-NEW-SECT         Curb detail 001, 6", new construction, section
CIV-DETAIL-CURB-002-NEW-PLAN             Curb detail 002, new, plan
CIV-DETAIL-DRAIN-010-ADA-NEW-SECT        Drainage detail 010, ADA compliant, new, section
CIV-DETAIL-RAMP-015-8PCT-NEW-SECT        Ramp detail 015, 8% slope, new, section
SITE-DETAIL-WALL-020-6FT-NEW-ELEV        Retaining wall detail 020, 6 ft high, new, elevation
LAND-DETAIL-PLANTER-005-BIOSWALE-NEW-SECT Planter detail 005, bioswale type, new, section
CIV-DETAIL-MH-030-TYPE1-EXIST-PLAN       Manhole detail 030, type 1, existing, plan
CIV-DETAIL-INLET-012-TYPEC-NEW-SECT      Inlet detail 012, type C, new, section
```

### Detail Naming Rules
1. **FAMILY**: Groups related details (CURB, DRAIN, RAMP, WALL, etc.) - aligns with keynote THEME and block ATTRIBUTE for cross-referencing (e.g., DRAIN family covers STORM/SANIT systems)
2. **SEQUENCE**: Unique 3-digit ID within company standards
3. **ATTRIBUTES**: Optional type variants, sizes, special requirements (ADA, 8PCT, 6FT, TYPEC, etc.)
4. **PHASE**: Uses standard phase codes (EXIST, NEW, TEMP, DEMO, FUTR, PROP, PH1/2/3)
5. **VIEW**: Specifies drawing view type

### Detail Family Codes
| Code | Family | Description |
|------|--------|-------------|
| CURB | Curb Details | All curb and gutter details |
| DRAIN | Drainage Details | Inlets, catch basins, manholes |
| RAMP | Ramp Details | ADA ramps, vehicle ramps |
| WALL | Wall Details | Retaining walls, seat walls |
| PAVE | Pavement Details | Pavement sections, joints |
| UTIL | Utility Details | Pipe connections, trenching |
| FENCE | Fence Details | Fencing and gates |
| SIGN | Sign Details | Signage mounting, foundations |
| LIGHT | Lighting Details | Light pole foundations, wiring |
| PLANTER | Planter Details | Planter boxes, bioretention |

---

## 9. Hatch Pattern Naming Convention

### Format
`MAT-CATEGORY-TEXTURE-[SCALE]-PHASE-HT`

**MAT** = Material discipline prefix
**HT** = Hatch terminator (distinguishes from other elements)
**SCALE** = Optional pattern scale factor (1X, 2X, ANSI31, etc.)

### Hatch Pattern Examples
```
MAT-CONC-SOLID-NEW-HT                Concrete solid fill, new construction
MAT-ASPH-AC-FINE-NEW-HT              Asphalt concrete, fine pattern, new
MAT-SOIL-SAND-COARSE-EXIST-HT        Sand fill, coarse pattern, existing
MAT-GRAVEL-CRUSHED-MED-NEW-HT        Crushed gravel, medium pattern, new
MAT-PAVE-BRICK-RUNNING-NEW-HT        Brick pavement, running bond, new
MAT-PAVE-UNIT-HERRING-NEW-HT         Unit pavers, herringbone pattern, new
MAT-WATER-SOLID-EXIST-HT             Water body, solid fill, existing
MAT-TURF-GRASS-FINE-NEW-HT           Turf grass, fine texture, new
MAT-ROCK-RIP-LARGE-NEW-HT            Riprap, large stone pattern, new
MAT-CONC-ANSI31-2X-NEW-HT            Concrete ANSI31 pattern, 2x scale, new
```

### Hatch Naming Rules
1. **CATEGORY**: Material type (CONC, ASPH, SOIL, GRAVEL, PAVE, WATER, TURF, ROCK)
2. **TEXTURE**: Pattern style (SOLID, FINE, COARSE, MED, ANSI31, specific patterns)
3. **SCALE**: Optional scale factor (1X, 2X, HALF, etc.) placed in ATTRIBUTES segment
4. **PHASE**: Uses standard phase codes (EXIST, NEW, TEMP, DEMO, FUTR, PROP, PH1/2/3)
5. **Links to Materials**: CATEGORY+TEXTURE maps to `material_standards` entries
6. **Storage**: Pattern definition stored in `hatch_patterns` table

### Hatch Category Codes
| Code | Category | Description |
|------|----------|-------------|
| CONC | Concrete | All concrete materials |
| ASPH | Asphalt | Asphalt concrete, paving |
| SOIL | Soil | Natural soil, fill material |
| GRAVEL | Gravel | Gravel, aggregate base |
| PAVE | Pavement | Unit pavers, brick, stone |
| WATER | Water | Water bodies, features |
| TURF | Turf | Grass, groundcover |
| ROCK | Rock | Riprap, boulders, rock |
| SAND | Sand | Sand fill, beach sand |
| WETLAND | Wetland | Wetland vegetation patterns |

---

## 10. Keynote Naming Convention

### Format
`DISCIPLINE-SYSTEM-THEME-SEQUENCE-PHASE-TX`

**SYSTEM** = Major system category (aligns with layer CATEGORY)
**THEME** = Specification group (aligns with detail FAMILY and block TYPE)
**SEQUENCE** = Four-digit unique ID from `standard_notes` table (0001-9999)
**TX** = Text terminator

### Keynote Examples
```
CIV-UTIL-STORM-0010-NEW-TX           Civil utility storm note 0010, new construction
CIV-UTIL-WATER-0025-EXIST-TX         Civil utility water note 0025, existing
CIV-ROAD-CURB-0015-NEW-TX            Civil road curb note 0015, new
SITE-PAVE-ASPH-0032-NEW-TX           Site pavement asphalt note 0032, new
LAND-TREE-PROT-0008-TEMP-TX          Landscape tree protection note 0008, temporary
CIV-EROS-SWPPP-0041-TEMP-TX          Civil erosion SWPPP note 0041, temporary
ANNO-GENERAL-CONST-0001-PROP-TX      Annotation general construction note 0001, proposed
CIV-ADA-RAMP-0012-NEW-TX             Civil ADA ramp note 0012, new
```

### Keynote Naming Rules
1. **SEQUENCE**: Four-digit unique ID (0001-9999) from `standard_notes.note_id`
2. **THEME**: Specification group that links to block ATTRIBUTE and detail FAMILY for cross-referencing (e.g., STORM theme links to blocks with STORM attribute and DRAIN detail family)
3. **PHASE**: Uses standard phase codes (EXIST, NEW, TEMP, DEMO, FUTR, PROP, PH1/2/3)
4. **Content**: Note text stored in `standard_notes.note_text`
5. **Chaining**: Keynote THEME → Block ATTRIBUTE → Detail FAMILY creates semantic web

### Keynote System Codes
(Reuses layer CATEGORY codes: UTIL, ROAD, GRAD, STOR, PAVE, WALL, FENCE, TREE, etc.)

### Keynote Theme Codes
| Code | Theme | Links To |
|------|-------|----------|
| STORM | Storm Drainage | Block: INLET, Detail: DRAIN |
| WATER | Water System | Block: HYDRA/VALVE, Detail: UTIL |
| CURB | Curb & Gutter | Block: N/A, Detail: CURB |
| PAVE | Pavement | Block: N/A, Detail: PAVE |
| RAMP | Ramps | Block: N/A, Detail: RAMP |
| WALL | Walls | Block: N/A, Detail: WALL |
| PROT | Protection | Block: FENCE, Detail: FENCE |
| SWPPP | Erosion Control | Block: N/A, Detail: EROS |
| CONST | General Construction | Block: Various, Detail: Various |

---

## 11. Material Naming Convention

### Format
`MAT-DISCIPLINE-CATEGORY-COMPOSITION-[FINISH]-PHASE`

**DISCIPLINE** = Engineering discipline using material
**CATEGORY** = Material family
**COMPOSITION** = Specific formulation or type
**FINISH** = Optional surface treatment or appearance

### Material Name Examples
```
MAT-CIV-CONC-4000PSI-SMOOTH-NEW      Concrete, 4000 psi, smooth finish, new
MAT-CIV-CONC-5000PSI-BROOM-NEW       Concrete, 5000 psi, broom finish, new
MAT-CIV-ASPH-AC2-TYPE2-NEW           Asphalt, AC-2, Type II, new
MAT-CIV-BASE-AB-6IN-NEW              Aggregate base, 6 inch, new
MAT-SITE-SOIL-IMPORT-COMP-NEW        Import soil, compacted, new
MAT-SITE-GRAVEL-CRUSHED-3_4IN-NEW    Crushed gravel, 3/4 inch, new
MAT-LAND-MULCH-BARK-3IN-NEW          Bark mulch, 3 inch depth, new
MAT-LAND-SOIL-PLANTER-BLEND-NEW      Planter soil mix, blend formula, new
MAT-CIV-PIPE-PVC-SDR35-NEW           PVC pipe, SDR 35, new
MAT-CIV-PIPE-HDPE-DR17-NEW           HDPE pipe, DR 17, new
```

### Material Naming Rules
1. **PHASE**: Uses standard phase codes (EXIST, NEW, TEMP, DEMO, FUTR, PROP, PH1/2/3)
2. **Links to Hatches**: MAT-CATEGORY-COMPOSITION maps to hatch pattern families
3. **Specification**: Full spec text stored in `material_standards.specification`
4. **Attributes**: Strength, size, grade stored in `material_standards.attributes` JSON
5. **Cross-Reference**: Materials link to details, keynotes, and hatches

### Material Category Codes
| Code | Category | Examples |
|------|----------|----------|
| CONC | Concrete | Portland cement concrete, various strengths |
| ASPH | Asphalt | AC paving, emulsions |
| BASE | Base Material | Aggregate base, subbase |
| SOIL | Soil | Native, import, engineered fill |
| GRAVEL | Gravel | Crushed rock, pea gravel |
| PIPE | Pipe Material | PVC, HDPE, RCP, DI |
| REBAR | Reinforcement | Rebar, mesh, fiber |
| MULCH | Mulch | Bark, decomposed granite |
| SAND | Sand | Plaster sand, bedding sand |
| FABRIC | Geofabric | Filter fabric, reinforcement |

---

## 12. Cross-Element Relationship Mapping

### Semantic Alignment Through Shared Codes

**THEME/FAMILY Alignment Example 1 (Storm Drainage):**
```
Keynote: CIV-UTIL-STORM-0010-NEW-TX
         ↓ (THEME: STORM)
Block:   CIV-UTIL-MH-STORM-48IN-NEW-DEF
         ↓ (ATTRIBUTE: STORM identifies utility type)
Detail:  CIV-DETAIL-DRAIN-010-TYPEC-NEW-SECT
         ↓ (FAMILY: DRAIN covers storm drainage systems)
```
**Alignment:** Keynote THEME (STORM) → Block ATTRIBUTE (STORM) → Detail FAMILY (DRAIN handles storm systems)

**THEME/FAMILY Alignment Example 2 (Curb & Gutter):**
```
Keynote: CIV-ROAD-CURB-0015-NEW-TX
         ↓ (THEME: CURB)
Block:   N/A (no standard block for curb)
Detail:  CIV-DETAIL-CURB-001-6IN-NEW-SECT
         ↓ (FAMILY: CURB)
```
**Alignment:** Keynote THEME (CURB) → Detail FAMILY (CURB) - direct match

**Material-Hatch Alignment:**
```
Material: MAT-CIV-ASPH-AC2-TYPE2-NEW
          ↓ (CATEGORY: ASPH, COMPOSITION: AC2)
Hatch:    MAT-ASPH-AC-FINE-NEW-HT
          ↓ (CATEGORY: ASPH, TEXTURE: AC)
Detail:   CIV-DETAIL-PAVE-025-AC2-NEW-SECT
          ↓ (FAMILY: PAVE, ATTRIBUTE: AC2)
```
**Alignment:** Material CATEGORY+COMPOSITION → Hatch CATEGORY+TEXTURE → Detail shows application

### Project-Specific Override Pattern

**Base Standard:**
`CIV-UTIL-STORM-12IN-NEW-LN`

**Project Override (Project Code = PRJ2025):**
`CIV-UTIL-STORM-12IN-PRJ2025-NEW-LN`

Project token inserted before PHASE segment maintains parseability while enabling per-project customization.

---

## 13. Parsing Logic for All Element Types

### Layer Names
```
Pattern: ^([A-Z]+)-([A-Z]+)-([A-Z]+)(?:-([A-Z0-9_]+))*-([A-Z0-9]+)-([A-Z]+)$
Groups:  (DISC)  -(CAT)  -(TYPE) -(ATTRS)        -(PHASE)   -(GEOM)
```

### Block Names
```
Format:  DISCIPLINE-CATEGORY-TYPE-[ATTRIBUTES]-PHASE-FORM
Pattern: ^([A-Z]+)-([A-Z]+)-([A-Z]+)(?:-([A-Z0-9_]+))*-([A-Z0-9]+)-(DEF|INST)$
Groups:  (DISC)  -(CAT)  -(TYPE) -(ATTRS)        -(PHASE)   -(FORM)
Example: CIV-UTIL-MH-STORM-48IN-NEW-DEF
```

### Detail Names
```
Format:  DISCIPLINE-DETAIL-FAMILY-SEQUENCE-[ATTRIBUTES]-PHASE-VIEW
Pattern: ^([A-Z]+)-DETAIL-([A-Z]+)-(\d{3})(?:-([A-Z0-9_]+))*-([A-Z0-9]+)-([A-Z]+)$
Groups:  (DISC)  -DETAIL-(FAMILY)-(SEQ)  -(ATTRS)        -(PHASE)   -(VIEW)
Example: CIV-DETAIL-CURB-001-6IN-NEW-SECT
```

### Hatch Names
```
Format:  MAT-CATEGORY-TEXTURE-[SCALE]-PHASE-HT
Pattern: ^MAT-([A-Z]+)-([A-Z]+)(?:-([A-Z0-9_]+))*-([A-Z0-9]+)-HT$
Groups:  MAT -(CAT)  -(TEXT) -(SCALE)        -(PHASE)   -HT
Example: MAT-ASPH-AC-FINE-NEW-HT or MAT-CONC-ANSI31-2X-NEW-HT
```

### Keynote Names
```
Format:  DISCIPLINE-SYSTEM-THEME-SEQUENCE-PHASE-TX
Pattern: ^([A-Z]+)-([A-Z]+)-([A-Z]+)-(\d{4})-([A-Z0-9]+)-TX$
Groups:  (DISC)  -(SYS)  -(THEME)-(SEQ) -(PHASE)   -TX
Example: CIV-UTIL-STORM-0010-NEW-TX
```

### Material Names
```
Format:  MAT-DISCIPLINE-CATEGORY-COMPOSITION-[FINISH]-PHASE
Pattern: ^MAT-([A-Z]+)-([A-Z]+)-([A-Z0-9]+)(?:-([A-Z0-9_]+))*-([A-Z0-9]+)$
Groups:  MAT -(DISC)  -(CAT)  -(COMP)     -(FINISH)       -(PHASE)
Example: MAT-CIV-CONC-4000PSI-SMOOTH-NEW
```

---

## 14. Database Mapping Strategy

### Canonical Name vs DXF Alias

**Canonical Name**: Stored in standards tables (`block_definitions.name`, `detail_standards.detail_name`, etc.)
- Always follows the naming convention exactly
- Used for database queries, AI understanding, internal operations

**DXF Alias**: Client-specific or legacy name variations
- Stored in mapping tables (`block_name_mappings`, `detail_name_mappings`, etc.)
- Multiple aliases can point to one canonical name
- Direction flags: `import_alias` (client CAD → DB) or `export_alias` (DB → client CAD)

### Example Mapping
```
Canonical:     CIV-UTIL-MH-STORM-48IN-STD-DEF
DXF Alias 1:   STM-MH-48 (Client A import)
DXF Alias 2:   STORM_MANHOLE_48" (Client B import)
DXF Alias 3:   MH-S-48 (legacy format)
```

---

## 15. Implementation Roadmap

### Phase 1: Documentation & Database Schema
1. ✓ Define naming conventions (this document)
2. Create mapping tables for each element type
3. Update existing standards tables with canonical names

### Phase 2: CRUD Interfaces
1. Build data managers for each mapping type
2. Enable bulk import/export of naming mappings
3. Create validation tools for name compliance

### Phase 3: Visualization & Documentation
1. Build interactive standards mapping dashboard
2. Create hierarchical relationship viewer
3. Generate exportable documentation (PDF, Excel, web)

### Phase 4: Integration
1. Update DXF import/export to use naming conventions
2. Enable project-level override system
3. Build context mapping UI (keynotes→blocks→details)

---

## Next Steps

1. Create database tables to store all naming mappings
2. Build CRUD managers for mapping management
3. Develop standards visualization dashboard
4. Implement project-specific override system
5. Generate comprehensive documentation exports
