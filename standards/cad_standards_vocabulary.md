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

## Next Steps

1. Create database tables to store all these codes
2. Build layer name generator/validator
3. Create import mapping system for client variations
4. Update export system to use these standards
5. Build UI for managing standards vocabulary
