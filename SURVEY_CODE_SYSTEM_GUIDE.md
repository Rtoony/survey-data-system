# ACAD-GIS Survey Point Code System - User Guide

## Quick Start

**Access the Survey Code Library Manager at:** `/tools/survey-codes`

**What You Can Do:**
- View and manage 62 pre-configured survey point codes
- Create custom codes for your project-specific needs
- Test code parsing and CAD generation in the Testing tab
- Export codes to CSV for distribution to field data collectors
- See real-world field crew workflow examples

---

## Overview

The **Survey Point Code System** transforms traditional field data collection by replacing arbitrary text descriptions with **structured, machine-parsable codes** that automatically generate CAD entities, create polylines, and apply proper layer naming standards.

### The Problem We're Solving

**Traditional surveying workflows:**
- Field crews use inconsistent abbreviations ("MH", "STMH", "STM-MH")
- Data requires manual interpretation and CAD conversion
- Layer naming is inconsistent
- No automatic line connectivity
- Descriptions don't drive CAD output

**Our solution:**
- **Structured codes** that are machine-readable and human-friendly
- **Automatic CAD generation** from survey shots
- **Consistent layer naming** based on templates
- **Auto-connectivity** for sequential points
- **Block insertion** for symbols at node locations

---

## Code Structure

Every survey code follows a hierarchical structure:

```
[DISCIPLINE]-[CATEGORY]-[FEATURE_TYPE]-[ATTRIBUTES]-[CONNECTIVITY]-[FLAGS]
```

### Example Codes

| Code | What It Means | Field Use |
|------|---------------|-----------|
| `CIV-UTIL-STORM-MH` | Storm Manhole | Shoot rim elevation of storm manhole |
| `SITE-ROAD-ASPH-EDGE` | Asphalt Edge | Shoot sequential edge points (auto-connects) |
| `SURV-TOPO-GROUND-SHOT` | Topographic Shot | Random ground elevation for contouring |
| `CIV-UTIL-WATER-HYDRANT` | Fire Hydrant | Single point - creates hydrant symbol |
| `SITE-BLDG-FOOTPRINT` | Building Footprint | Building corners (closes polygon) |

---

## Connectivity Types

The system supports six connectivity behaviors:

### 1. **NODE** - Network Nodes
- **Use:** Manholes, valves, catch basins, utilities
- **Behavior:** Single point, often creates a CAD block symbol
- **Example:** Storm manhole, water valve, fire hydrant

### 2. **LINE** - Auto-Connect Sequential Points
- **Use:** Road edges, curbs, pipes, fences, walls
- **Behavior:** Automatically connects points shot in sequence
- **Example:** Asphalt edge, concrete curb, storm pipe centerline
- **Field Tip:** Shoot points in order, system draws polyline automatically

### 3. **EDGE** - Closed Polygon
- **Use:** Building footprints, parking islands, enclosed areas
- **Behavior:** Connects sequential points AND closes back to first point
- **Example:** Building outline, property boundary

### 4. **POINT** - Standalone Point
- **Use:** Topographic shots, trees, signs, isolated features
- **Behavior:** No automatic connection, just marks location
- **Example:** Ground shot, tree, light pole

### 5. **BREAK** - Stop Line
- **Use:** End a continuous line sequence
- **Behavior:** Stops auto-connection without closing
- **Example:** End of fence, end of curb run

### 6. **CLOSE** - Close Current Polygon
- **Use:** Complete a polygon/building footprint
- **Behavior:** Closes current sequence back to start point
- **Example:** Final corner of building

---

## Categories & Disciplines

### Disciplines
- **CIV** - Civil Engineering (utilities, infrastructure)
- **SITE** - Site features (roads, buildings, landscape)
- **SURV** - Survey/topographic data
- **ARCH** - Architectural elements

### Category Groups
- **utilities** - Storm, sanitary, water, gas, electric, telecom
- **site** - Roads, parking, sidewalks, buildings, fences
- **topo** - Ground shots, breaklines, contours
- **control** - Survey monuments, benchmarks, property corners

---

## CAD Output & Layer Generation

### Geometry Output Types
- **BL** - Block Insert (symbol placed at point)
- **PL** - Polyline (connected line segments)
- **LN** - Line (single segment)
- **PT** - Point (marker only)

### Layer Naming Template

Most codes use this template:
```
{discipline}-{category}-{feature}-{phase}-{geometry}
```

**Examples:**
- `CIV-UTIL-STORM-EXST-SYMB` (existing storm manhole symbol)
- `SITE-ROAD-ASPH-PROP-EDGE` (proposed asphalt edge)
- `SURV-TOPO-GROUND-EXST-TOPO` (existing topographic data)

---

## Field Crew Workflow

### 1. **Setup**
- Load code library into data collector (CSV export available)
- Field crews can search/filter by category, favorites, or full list

### 2. **Field Data Collection**

**For NODE features (manholes, valves):**
1. Locate structure
2. Select code: `CIV-UTIL-STORM-MH`
3. Shoot rim elevation
4. System creates block symbol at location

**For LINE features (curbs, edges):**
1. Start at beginning of feature
2. Select code: `SITE-ROAD-CONC-CURB`
3. Shoot sequential points along curb
4. System auto-connects points into polyline
5. Use `BREAK` code to stop when curb ends

**For EDGE features (buildings):**
1. Start at first building corner
2. Select code: `SITE-BLDG-FOOTPRINT`
3. Shoot all corners in sequence
4. Use `CLOSE` code at last corner
5. System creates closed polygon

**For POINT features (trees, topo):**
1. Locate feature
2. Select code: `SITE-TREE-DECIDUOUS`
3. Shoot single point
4. System places tree symbol

### 3. **Post-Processing**
- Import survey data into ACAD-GIS database
- System automatically:
  - Parses codes
  - Generates CAD entities
  - Assigns to correct layers
  - Creates polylines where specified
  - Inserts blocks at NODE locations

---

## Code Library Organization

### 62 Comprehensive Codes Included

**Utilities (28 codes):**
- Storm drainage: manholes, inlets, cleanouts, catch basins, pipe centerlines
- Sanitary sewer: manholes, cleanouts, laterals, pipe centerlines
- Water: valves, hydrants, meters, pipe centerlines
- Gas: valves, meters, pipe centerlines
- Electric: poles, transformers, pedestals, conduits
- Telecom: manholes, pedestals, conduits

**Site Features (22 codes):**
- Roads: edges, curbs, gutters, centerlines, stripes, ramps
- Parking: lot edges, islands, stall stripes
- Walks: sidewalk edges, joints, path edges
- Fences/Walls: chain link, wood, retaining walls, freestanding walls
- Features: signs, lights, bollards, benches

**Topographic (4 codes):**
- Ground shots, breaklines, ridge/valley lines, spot elevations

**Vegetation (4 codes):**
- Deciduous trees, conifers, palms, shrubs, hedge lines

**Buildings (3 codes):**
- Footprint corners, overhangs, doors

**Control Points (4 codes):**
- Monuments, benchmarks, GPS base stations, property corners, ROW markers

---

## Favorites System

**Star your most-used codes** for quick access:
- Favorites appear first in sorted lists
- Favorites exported at top of CSV
- Currently 13 favorited codes (manholes, hydrants, curbs, breaklines, monuments)

**Recommendation:** Star codes your crews use daily

---

## Best Practices

### Do:
- ✅ **Use consistent codes** across all projects
- ✅ **Train crews** on connectivity types (NODE, LINE, EDGE, POINT)
- ✅ **Shoot in sequence** for LINE/EDGE features
- ✅ **Use BREAK** to end lines cleanly
- ✅ **Add new codes** as needed through the manager UI

### Don't:
- ❌ Skip points when shooting LINE features (creates gaps)
- ❌ Mix connectivity types in same sequence
- ❌ Forget to use CLOSE for buildings/polygons
- ❌ Create custom abbreviations instead of using codes

---

## System Benefits

### For Field Crews
- Standardized, searchable code list
- No ambiguity about feature types
- Faster data collection with favorites
- Clear instructions via display names

### For CAD Technicians
- Automatic layer assignments
- Auto-generated polylines
- Consistent symbology
- Reduced manual drafting

### For Project Managers
- Consistent data across projects
- Traceable standards
- Quality metrics (usage tracking)
- Easy updates to code library

### For Database
- Structured, queryable data
- AI-ready for embeddings/search
- GraphRAG relationships
- Audit trail of field data

---

## Example Field Scenarios

### Scenario 1: Surveying Existing Storm System
```
1. SHOOT: CIV-UTIL-STORM-MH (manhole rim)
   → Creates block symbol at location
   
2. SHOOT: CIV-UTIL-STORM-PIPE-CL (pipe inverts)
   → Auto-connects points into pipe centerline
   
3. SHOOT: CIV-UTIL-CATCH-BASIN (grate elevation)
   → Creates catch basin symbol
   
4. SHOOT: CIV-UTIL-STORM-PIPE-CL (continue pipe)
   → Extends polyline to next structure
   
5. SHOOT: CIV-UTIL-STORM-MH (next manhole)
   → Creates second manhole symbol
```

**Result:** Complete storm system with manholes, catch basins, and connecting pipes—all on correct layers.

### Scenario 2: Building Footprint
```
1. SHOOT: SITE-BLDG-FOOTPRINT (corner 1)
2. SHOOT: SITE-BLDG-FOOTPRINT (corner 2)
3. SHOOT: SITE-BLDG-FOOTPRINT (corner 3)
4. SHOOT: SITE-BLDG-FOOTPRINT (corner 4)
5. SHOOT: CLOSE
   → Creates closed polygon on SITE-BLDG-FOOTPRINT-EXST-EDGE layer
```

### Scenario 3: Topographic Survey
```
1. SHOOT: SURV-TOPO-BREAKLINE (grade break start)
2. SHOOT: SURV-TOPO-BREAKLINE (follow grade break)
3. SHOOT: SURV-TOPO-BREAKLINE (continue...)
4. SHOOT: BREAK (end of grade break)
   → Creates breakline polyline

5. SHOOT: SURV-TOPO-GROUND-SHOT (random topo point)
   → Single point for contouring
6. SHOOT: SURV-TOPO-GROUND-SHOT (another point)
   → Another isolated topo point
```

---

## CSV Export for Data Collectors

### What You Get
The CSV export includes:
- Code (searchable in data collector)
- Display Name (human-readable)
- Description (field instructions)
- Discipline, Category, Feature Type
- Connectivity type, Geometry output
- Auto-connect/block creation flags
- Layer template, default phase
- Favorite status, usage count

### Loading into Data Collectors
1. Click "Export CSV" in Survey Code Library Manager
2. Download `survey_codes_library.csv`
3. Import into your data collector's code library
4. Codes appear as selectable options during survey

**Supported formats:** Most modern data collectors accept CSV code lists (Trimble, Leica, Topcon, etc.)

---

## Future Phases

### Phase 2: Code Parser & Testing
- Web interface to test code parsing
- Preview layer names, CAD output
- Simulate field shots
- Validate attribute prompts

### Phase 3: Import Tool with Auto-Connectivity
- Import PNEZD files with codes
- Automatically generate polylines
- Create line segments from connected points
- Insert blocks at NODE locations

### Phase 4: DXF Export Integration
- Export complete CAD drawings
- Auto-layered based on templates
- Survey-grade 3D elevation preservation
- Integration with existing DXF tools

---

## Questions?

**For technical support or to request new codes:**
- Add codes directly through `/tools/survey-codes` UI
- Contact your CAD manager for project-specific standards
- Review this guide for connectivity type explanations

**Current Library Status:**
- **62 active codes** covering civil, site, survey, and control applications
- **13 favorited codes** for quick access
- **4 category groups** (utilities, site, topo, control)
- **6 connectivity types** supporting all field scenarios

---

*Last Updated: November 2025*  
*ACAD-GIS Survey Point Code System v1.0*
