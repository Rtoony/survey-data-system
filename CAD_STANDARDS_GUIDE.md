# ACAD-GIS CAD Standards System - User Guide

## Quick Overview

The ACAD-GIS system uses a **database-first approach** where PostgreSQL is the source of truth, not your DXF files. Layer names are semantic labels that help classify and organize your data, but the real information lives in the database.

### The Big Picture

```
Legacy DXF Files → Import Patterns → Database Objects → Standard Layer Names → Clean DXF Export
     (messy)         (translate)      (organized)         (consistent)         (clean)
```

## The Layer Naming System

### Standard Format

```
DISCIPLINE-CATEGORY-TYPE-[ATTRIBUTES]-PHASE-GEOMETRY
```

### Real Examples

| Layer Name | Meaning |
|------------|---------|
| `CIV-UTIL-STORM-12IN-NEW-LN` | Civil utility, storm pipe, 12 inch, new construction, line |
| `SITE-ROAD-ASPHALT-EXIST-PL` | Site roads, asphalt pavement, existing, polyline |
| `SURV-TOPO-CONTOUR-2FT-EXIST-LN` | Survey topo, contour line, 2 foot interval, existing, line |
| `CIV-UTIL-SANITARY-8IN-DEMO-LN` | Civil utility, sanitary sewer, 8 inch, to be demolished, line |

### Breaking Down the Parts

**1. DISCIPLINE** (What field?)
- `CIV` - Civil engineering
- `SITE` - Site development
- `SURV` - Survey/topography
- `LAND` - Landscape architecture
- `ARCH` - Architecture
- `UTIL` - General utilities
- `ANNO` - Annotations/labels
- `XREF` - External references

**2. CATEGORY** (What type of work?)
- `UTIL` - Utilities (pipes, cables)
- `ROAD` - Roads and paving
- `TOPO` - Topography
- `GRAD` - Grading
- `STRU` - Structures
- `EROS` - Erosion control
- `ADA` - ADA compliance

**3. TYPE** (Specific object?)
- `STORM` - Storm drainage
- `SANITARY` - Sanitary sewer
- `WATER` - Water supply
- `ASPHALT` - Asphalt pavement
- `CONTOUR` - Contour lines
- `SPOT` - Spot elevations

**4. ATTRIBUTES** (Optional details)
- `12IN` - 12 inch diameter
- `2FT` - 2 foot interval
- `CONC` - Concrete material
- `Class-A` - Class designation

**5. PHASE** (Construction phase)
- `EXIST` - Existing conditions
- `DEMO` - To be demolished
- `NEW` - New construction
- `FUTURE` - Future phase

**6. GEOMETRY** (CAD entity type)
- `LN` - Lines/polylines
- `PL` - Filled polylines/polygons
- `PT` - Points
- `TX` - Text
- `BL` - Blocks

## How to Use the System

### Step 1: Set Up Your Vocabulary (One Time)

Go to **Standards > Bulk Standards Editor** (`/standards/bulk-editor`)

1. **Add Disciplines** - If you need new ones beyond the defaults
2. **Add Categories** - Must be linked to a discipline
3. **Add Object Types** - Must be linked to a category
4. **Add Phases** - Set colors for visual coding
5. **Add Geometries** - Usually the defaults (LN, PL, PT, TX, BL) are enough
6. **Add Attributes** - Common sizes, materials, classes

### Step 2: Create Import Patterns (For Each Client)

Go to **Standards > Import Template Manager** (`/standards/import-manager`)

#### Example: Client with layers like `S-UTIL-STORM-12`

**Pattern Setup:**
- **Client Name:** "Acme Engineering"
- **Source Pattern:** `^([A-Z]+)-([A-Z]+)-([A-Z0-9]+)-([A-Z0-9]+)$`
- **Description:** "Legacy format: DISC-CAT-TYPE-ATTR"
- **Extraction Rules:**
```json
{
  "discipline_group": 1,
  "category_group": 2,
  "type_group": 3,
  "attribute_group": 4
}
```

**Test It:** Use the live testing panel on the right to verify your pattern matches real layer names.

#### Example: Another client with `CIVIL.UTILITIES.STORM.NEW`

**Pattern Setup:**
- **Client Name:** "XYZ Consultants"
- **Source Pattern:** `^([A-Z]+)\.([A-Z]+)\.([A-Z0-9]+)\.([A-Z]+)$`
- **Extraction Rules:**
```json
{
  "discipline_group": 1,
  "category_group": 2,
  "type_group": 3,
  "phase_group": 4
}
```

### Step 3: Filter Your Map Data

Go to **Map Viewer** (`/map-viewer`)

1. **Open Standards Filter Panel** (click the arrow to expand)
2. **Select Disciplines** - Check boxes for CIV, SITE, etc.
3. **Select Categories** - Only categories under selected disciplines show
4. **Select Phases** - Filter by construction phase
5. **Click Apply** - See only matching layers
6. **Click Clear** - Reset to see everything

**Example Use Case:** "Show me only existing civil utilities"
- Disciplines: ☑ CIV
- Categories: ☑ UTIL
- Phases: ☑ EXIST
- Click Apply → See only `CIV-UTIL-*-*-EXIST-*` layers

### Step 4: Import DXF Files

Go to **DXF Tools** (`/dxf-tools`)

1. **Select or Create a Drawing** in the database
2. **Choose Your DXF File** from your computer
3. **Select Import Pattern** (optional but recommended)
   - Pick your client's pattern from the dropdown
   - If no pattern selected, imports as-is without classification
4. **Check Import Options**
   - ☑ Import Model Space (usually yes)
   - ☑ Import Paper Space (optional)
5. **Click Import**

**What Happens:**
- If pattern selected → System analyzes layers, creates intelligent objects
- See import statistics: entities imported, layers processed
- See classification preview: matched/unmatched layers, confidence score

**Example Results:**
```
Pattern Applied: Acme Engineering - ^([A-Z]+)-([A-Z]+)-([A-Z0-9]+)-([A-Z0-9]+)$
Matched Layers: 45
Unmatched Layers: 3
Confidence: 87%
```

## Creating Test Files

### Scenario 1: Basic Civil Utilities Test

**Create a DXF with these layers:**
```
CIV-UTIL-STORM-12IN-NEW-LN       (storm drainage pipes)
CIV-UTIL-STORM-MH-NEW-BL         (storm manholes)
CIV-UTIL-SANITARY-8IN-NEW-LN     (sanitary sewer)
CIV-UTIL-SANITARY-MH-NEW-BL      (sanitary manholes)
CIV-UTIL-WATER-6IN-NEW-LN        (water supply)
```

**Draw in AutoCAD:**
- Set layer to `CIV-UTIL-STORM-12IN-NEW-LN`
- Draw some polylines representing storm pipes
- Set layer to `CIV-UTIL-STORM-MH-NEW-BL`
- Insert blocks or draw circles for manholes
- Repeat for sanitary and water

**Import Test:**
- Import without pattern → All entities stored as-is
- Filter in Map Viewer by CIV + UTIL → See all utilities

### Scenario 2: Legacy Client Format Test

**Create a DXF with non-standard layers:**
```
S-UTIL-STORM-12      (their old format)
S-UTIL-SAN-8
S-UTIL-WTR-6
C-ROAD-ASPH
C-CURB-CONC
```

**Before Import:**
1. Go to Import Template Manager
2. Create pattern: `^([A-Z])-([A-Z]+)-([A-Z]+)-([0-9]+)$`
3. Set extraction rules to map groups 1-4 to discipline/category/type/attribute
4. Test pattern with your layer names

**Import Test:**
- Select your pattern from dropdown
- Import the file
- Check classification results
- System should create objects mapped to standard vocabulary

### Scenario 3: Multi-Phase Project Test

**Create a DXF showing demolition and new work:**
```
CIV-UTIL-STORM-12IN-EXIST-LN     (existing storm to remain)
CIV-UTIL-STORM-12IN-DEMO-LN      (existing storm to remove)
CIV-UTIL-STORM-12IN-NEW-LN       (new storm pipes)
SITE-ROAD-ASPHALT-EXIST-PL       (existing pavement)
SITE-ROAD-ASPHALT-NEW-PL         (new pavement)
```

**Filter Test:**
- Filter by Phase = EXIST → See existing conditions only
- Filter by Phase = NEW → See new construction only
- Filter by Phase = DEMO → See demolition work
- Use this for creating phased construction drawings

## Common Workflows

### Workflow 1: Quality Control Review

1. **Import** client DXF with pattern selected
2. **Check** classification statistics
   - High confidence (>90%) = Good match
   - Low confidence (<70%) = Review unmatched layers
3. **Filter** in Map Viewer by discipline
4. **Review** each category for completeness
5. **Export** clean DXF with standard layer names

### Workflow 2: Multi-Discipline Coordination

1. **Filter** Map Viewer by discipline (CIV)
2. **Export** civil-only DXF for civil engineer
3. **Filter** by discipline (ARCH)
4. **Export** architecture-only DXF for architect
5. Each consultant works with clean, relevant data

### Workflow 3: Construction Phasing

1. **Create** patterns for your client's format
2. **Import** design files
3. **Filter** by Phase = NEW for bid documents
4. **Filter** by Phase = DEMO for demolition plan
5. **Export** phase-specific drawings for contractors

## Troubleshooting

### Import Pattern Not Matching

**Problem:** "Matched Layers: 0" after import

**Solutions:**
1. Go to Import Template Manager
2. Use the live testing panel
3. Test your regex against actual layer names
4. Adjust pattern until groups capture correctly
5. Update extraction rules to map correct groups

### Layers Not Showing in Map Viewer Filter

**Problem:** Filtered but no results

**Causes:**
- Table doesn't have `layer_name` column
- Layer names don't match pattern (typos in DISCIPLINE codes)
- No data in selected categories

**Solutions:**
- Check if your layers use exact vocabulary codes
- Use Clear button, verify layers exist without filters
- Check vocabulary in Bulk Editor to confirm codes exist

### Can't Find a Discipline/Category

**Problem:** Need MECH discipline, but it doesn't exist

**Solution:**
1. Go to Bulk Standards Editor
2. Select Disciplines tab
3. Click "Add New"
4. Enter code: `MECH`, name: "Mechanical", description
5. Save
6. Now MECH is available throughout the system

## Quick Reference: Regex Patterns

### Common Client Formats

| Client Format | Regex Pattern | Example Match |
|---------------|---------------|---------------|
| `DISC-CAT-TYPE-ATTR` | `^([A-Z]+)-([A-Z]+)-([A-Z0-9]+)-([A-Z0-9]+)$` | `CIV-UTIL-STORM-12` |
| `DISC.CAT.TYPE.PHASE` | `^([A-Z]+)\.([A-Z]+)\.([A-Z0-9]+)\.([A-Z]+)$` | `CIVIL.UTIL.STORM.NEW` |
| `D_CAT_TYPE_ATTR` | `^([A-Z]+)_([A-Z]+)_([A-Z0-9]+)_([A-Z0-9]+)$` | `C_UTIL_STORM_12` |
| `DTYPE-ATTR` | `^([A-Z])([A-Z]+)-([A-Z0-9]+)$` | `CSTORM-12` |

### Extraction Rule Examples

**4-Part Pattern:**
```json
{
  "discipline_group": 1,
  "category_group": 2,
  "type_group": 3,
  "attribute_group": 4
}
```

**3-Part Pattern with Default Phase:**
```json
{
  "discipline_group": 1,
  "category_group": 2,
  "type_group": 3,
  "default_phase": "EXIST"
}
```

## Tips and Best Practices

### For Creating Test Files

1. **Start Simple** - Test with 3-5 layers before creating complex drawings
2. **Use Real Coordinates** - SRID 2226 (California State Plane) for GIS, SRID 0 for CAD
3. **Name Blocks Consistently** - Use standard names like `STORM-MH`, `WATER-VALVE`
4. **Include Attributes** - Add sizes, materials in layer names or block attributes
5. **Test Both Spaces** - Model space for design, paper space for sheets

### For Import Patterns

1. **Test Before Using** - Always use the live testing panel
2. **Document Your Patterns** - Use clear descriptions and client names
3. **Version Control** - Keep old patterns when updating (set inactive instead of delete)
4. **Start Permissive** - Broad patterns first, then refine based on results
5. **Confidence Scores** - Aim for >85% confidence on production imports

### For Map Filtering

1. **Hierarchical Filtering** - Select discipline first, then categories appear
2. **Multiple Selections** - Check multiple boxes for OR logic
3. **Clear Between Tests** - Always clear before trying new filter combinations
4. **Check Feature Counts** - Low counts might indicate filter too restrictive
5. **Save Exports** - Filtered views can be exported to DXF/SHP

## System Architecture Notes

### Why Database-First?

Traditional CAD: `Layer name = Data storage` (locked, hard to change)

ACAD-GIS: `Layer name = Semantic label` (flexible, AI-readable)

**Benefits:**
- Change layer naming conventions without touching data
- Run ML/AI queries on structured database
- Support multiple clients with different standards
- Track relationships (this pipe connects to that manhole)
- Version control and audit trails

### The Vocabulary Tables

All controlled vocabularies live in 6 tables:
1. `discipline_codes` - Top-level disciplines
2. `category_codes` - Linked to disciplines
3. `object_type_codes` - Linked to categories
4. `phase_codes` - Construction phases with colors
5. `geometry_codes` - CAD entity types
6. `attribute_codes` - Sizes, materials, classes

### The Pattern Tables

Client-specific layer mappings:
1. `import_mapping_patterns` - Regex patterns to parse client layers
2. `standard_layer_patterns` - Templates for exporting standard layers

## Need Help?

### Common Questions

**Q: Do I have to use standard layer names in my DXF files?**
A: No! That's the point. Create import patterns for your client's format, import their files, work in the database, then export with whatever layer names you want.

**Q: Can I have multiple patterns for one client?**
A: Yes! Create different patterns for different project types or legacy vs. current standards.

**Q: What if a layer doesn't match any pattern?**
A: It still imports, just without intelligent classification. You'll see it in the "unmatched" count.

**Q: Can I change vocabulary codes after importing?**
A: Yes, but you'll need to update existing database objects. The Bulk Editor shows what's in use.

**Q: How do I export with client-specific layer names?**
A: Future feature! The Export Template Manager will let you create reverse mappings (database → client layers).

### Where to Go

- **Manage Vocabulary:** `/standards/bulk-editor`
- **Create Patterns:** `/standards/import-manager`
- **Filter Layers:** `/map-viewer`
- **Import/Export:** `/dxf-tools`
- **View All Standards:** `/cad-standards`

## Summary

1. **Set up vocabulary** in Bulk Editor (one time)
2. **Create import patterns** for each client format
3. **Import DXF files** with pattern selection
4. **Work in database** with clean, structured data
5. **Filter and export** as needed for deliverables

The system learns your clients' quirks and translates everything to a consistent, AI-friendly format in the database!
