# Projects Only System: Migration Guide

## Executive Summary

The ACAD-GIS system has migrated from a "Projects + Drawings" architecture to a streamlined "Projects Only" system. This guide explains the changes, benefits, and how to use the new hybrid intelligent object creation workflow.

## Table of Contents

1. [Overview](#overview)
2. [What Changed](#what-changed)
3. [Hybrid Classification System](#hybrid-classification-system)
4. [Database Architecture](#database-architecture)
5. [New Tools & APIs](#new-tools--apis)
6. [Migration Path](#migration-path)
7. [User Guide](#user-guide)
8. [Technical Reference](#technical-reference)

---

## Overview

### Before: Projects + Drawings Architecture

```
Project
├── Drawing 1 (DXF File)
│   ├── Entity 1 → Links to Drawing
│   ├── Entity 2 → Links to Drawing
│   └── ...
├── Drawing 2 (DXF File)
│   ├── Entity 3 → Links to Drawing
│   └── ...
```

**Problems:**
- Overhead of managing drawing files
- Complex queries (project → drawings → entities)
- Drawing files often unnecessary in civil engineering workflows
- No clear path for unclassified entities

### After: Projects Only System

```
Project
├── Intelligent Objects
│   ├── Utility Line (High confidence, auto-classified)
│   ├── BMP (High confidence, auto-classified)
│   ├── Generic Object (Low confidence, needs review)
│   └── ...
└── Entity Links (Direct project-level linking)
```

**Benefits:**
- Simplified architecture: Entities link directly to projects
- Faster queries: No intermediate drawing table joins
- No data loss: Low-confidence entities saved for review
- Clear workflow: Automatic classification + manual review

---

## What Changed

### 1. DXF Import Flow

**Before:**
```
DXF Upload → Create Drawing Record → Parse Entities → Classify → Create Objects OR Drop
```

**After:**
```
DXF Upload → Parse Entities → Classify
                              ├─ High Confidence (≥0.7) → Create Specific Object (utility_line, bmp, etc.)
                              └─ Low Confidence (<0.7) → Create Generic Object → Flag for Review
```

### 2. Entity Linking

**Before:**
- `dxf_entity_links.drawing_id` was REQUIRED
- Unique constraint: `(drawing_id, dxf_handle)`

**After:**
- `dxf_entity_links.drawing_id` is NULLABLE
- Two unique constraints:
  - Drawing-level: `UNIQUE (drawing_id, dxf_handle)` (legacy support)
  - Project-level: `UNIQUE (project_id, dxf_handle) WHERE drawing_id IS NULL` (new)

### 3. Classification Workflow

**New Hybrid Approach:**

```
Layer Name → Classification Engine
                ├─ Confidence ≥ 0.7 → Automatic Classification
                │   ├─ utility_line
                │   ├─ utility_structure
                │   ├─ bmp
                │   ├─ alignment
                │   ├─ surface_model
                │   ├─ survey_point
                │   └─ site_tree
                │
                └─ Confidence < 0.7 → Generic Object
                    └─ Review Workflow
                        ├─ Pending (needs review)
                        ├─ Approved (keep as generic)
                        ├─ Reclassified (converted to specific type)
                        └─ Ignored (hide from review)
```

---

## Hybrid Classification System

### Automatic Classification (High Confidence)

When the layer name classifier has ≥0.7 confidence, entities are automatically created as specific object types:

**Example: Utility Lines**
```
Layer: "CIV-PIPE-GRAV-EXST-AXIS"
↓ Classification (confidence: 0.95)
↓
utility_lines table
├── line_id: uuid
├── project_id: uuid
├── utility_type: "Gravity Sewer"
├── material: "PVC"
├── geometry: PostGIS LineString
└── quality_score: 0.95
```

**Supported Object Types:**
1. **utility_lines** - Water, sewer, storm, gas, electric lines
2. **utility_structures** - Manholes, valves, inlets, hydrants
3. **bmps** - Bioretention, swales, detention ponds, infiltration basins
4. **alignments** - Road centerlines, profile alignments
5. **surface_models** - Terrain models, grading surfaces
6. **survey_points** - Control points, monuments
7. **site_trees** - Existing/proposed trees

### Manual Review Workflow (Low Confidence)

When confidence < 0.7, entities are saved as `generic_objects` for manual review:

**Example: Unclassified Layer**
```
Layer: "PROPOSED-BASIN"
↓ Classification (confidence: 0.45)
↓
generic_objects table
├── object_id: uuid
├── project_id: uuid
├── object_name: "PROPOSED-BASIN (LWPOLYLINE)"
├── original_layer_name: "PROPOSED-BASIN"
├── original_entity_type: "LWPOLYLINE"
├── classification_confidence: 0.45
├── suggested_object_type: "bmp"
├── needs_review: true
├── review_status: "pending"
├── geometry: PostGIS Polygon
└── attributes: jsonb
```

**User Actions:**
1. **Reclassify** - Convert to specific type (utility_line, bmp, etc.)
2. **Approve** - Keep as generic object (no classification needed)
3. **Ignore** - Hide from review (but keep in database)

---

## Database Architecture

### New Table: generic_objects

```sql
CREATE TABLE generic_objects (
    object_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(project_id),
    
    -- Original DXF metadata
    object_name TEXT,
    original_layer_name TEXT,
    original_entity_type TEXT,
    source_dxf_handle TEXT,
    
    -- Classification tracking
    classification_confidence NUMERIC(3,2),
    suggested_object_type TEXT,
    
    -- Review workflow
    needs_review BOOLEAN DEFAULT TRUE,
    review_status TEXT DEFAULT 'pending',
    review_notes TEXT,
    reviewed_at TIMESTAMP,
    reviewed_by UUID,
    
    -- Spatial data
    geometry geometry(Geometry, 2226),
    
    -- Metadata
    tags TEXT[],
    attributes JSONB,
    
    -- AI features
    search_vector tsvector,
    quality_score NUMERIC(3,2),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Key Features:**
- Full PostGIS geometry support (SRID 2226)
- Review workflow states (pending/approved/reclassified/ignored)
- Confidence tracking for classification decisions
- Full-text search with automatic tsvector updates
- Quality scoring for data integrity

### Updated Table: dxf_entity_links

```sql
CREATE TABLE dxf_entity_links (
    link_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Project link (ALWAYS set)
    project_id UUID NOT NULL REFERENCES projects(project_id),
    
    -- Drawing link (NULLABLE for project-level imports)
    drawing_id UUID REFERENCES drawings(drawing_id),
    
    -- DXF entity metadata
    dxf_handle TEXT NOT NULL,
    entity_type TEXT,
    layer_name TEXT,
    entity_geom_hash TEXT,
    
    -- Intelligent object link
    object_table_name TEXT,
    object_id UUID,
    
    -- Sync tracking
    sync_state TEXT DEFAULT 'active',
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dual unique constraints for backward compatibility
CREATE UNIQUE INDEX idx_dxf_entity_links_drawing_handle 
ON dxf_entity_links (drawing_id, dxf_handle) 
WHERE drawing_id IS NOT NULL;

CREATE UNIQUE INDEX idx_dxf_entity_links_project_handle 
ON dxf_entity_links (project_id, dxf_handle) 
WHERE drawing_id IS NULL;
```

**Key Changes:**
- `drawing_id` is now NULLABLE
- Project-level links use `(project_id, dxf_handle)` as unique key
- Legacy drawing-level links still supported for backward compatibility

---

## New Tools & APIs

### 1. Object Reclassifier UI

**Route:** `/tools/object-reclassifier`

**Features:**
- Project-based filtering
- Review status filtering (pending/approved/reclassified/ignored)
- Confidence threshold slider
- Real-time statistics dashboard
- One-click reclassification to specific types
- Bulk approve/ignore actions

**Workflow:**
```
1. Select Project → Load Generic Objects
2. Filter by Status & Confidence
3. Review Each Object:
   - See original layer name, entity type, confidence
   - View suggested object type
   - Choose Action:
     a) Reclassify → Select target type → Add notes → Submit
     b) Approve → Mark as approved (no classification needed)
     c) Ignore → Hide from review list
4. Statistics Update in Real-Time
```

### 2. Reclassification API Endpoints

#### List Generic Objects
```http
GET /api/projects/{project_id}/generic-objects

Query Parameters:
- review_status: pending|approved|reclassified|ignored
- min_confidence: 0.0 to 1.0
- needs_review: true|false

Response:
{
  "objects": [...],
  "summary": {
    "total": 42,
    "by_status": {
      "pending": 15,
      "approved": 10,
      "reclassified": 12,
      "ignored": 5
    },
    "by_confidence": {
      "high": 5,
      "medium": 20,
      "low": 17
    }
  }
}
```

#### Reclassify Object
```http
POST /api/projects/{project_id}/generic-objects/{object_id}/reclassify

Body:
{
  "target_type": "utility_line|utility_structure|bmp|...",
  "notes": "Optional reclassification notes"
}

Response:
{
  "success": true,
  "new_object_id": "uuid",
  "object_type": "utility_line",
  "table_name": "utility_lines"
}
```

#### Approve Object
```http
POST /api/projects/{project_id}/generic-objects/{object_id}/approve

Body:
{
  "notes": "Optional approval notes"
}
```

#### Ignore Object
```http
POST /api/projects/{project_id}/generic-objects/{object_id}/ignore

Body:
{
  "notes": "Optional ignore notes"
}
```

### 3. Intelligent Objects Map API

**Route:** `GET /api/projects/{project_id}/intelligent-objects-map`

**Purpose:** Fetch all intelligent objects for map display (separate from raw DXF geometry)

**Response:**
```json
{
  "project_id": "uuid",
  "project_name": "Project Name",
  "intelligent_objects": {
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "properties": {
          "object_id": "uuid",
          "object_type": "utility_line",
          "table_name": "utility_lines",
          "utility_type": "Water",
          "material": "PVC",
          "diameter": 8
        },
        "geometry": { "type": "LineString", "coordinates": [...] }
      }
    ]
  },
  "summary": {
    "utility_lines": 25,
    "utility_structures": 10,
    "bmps": 5,
    "alignments": 3,
    "site_trees": 12,
    "generic_objects": 8,
    "total": 63
  }
}
```

### 4. Enhanced Project Statistics

**Route:** `GET /api/projects/{project_id}/statistics`

**New Fields:**
```json
{
  "intelligent_objects_counts": {
    "utility_lines": 25,
    "utility_structures": 10,
    "bmps": 5,
    "alignments": 3,
    "surface_models": 2,
    "site_trees": 12,
    "generic_objects": 8,
    "generic_objects_pending": 5
  },
  "total_intelligent_objects": 65
}
```

---

## Migration Path

### Backward Compatibility

**Existing Projects:** All existing drawing-based projects continue to work unchanged.
- Drawing records remain in database
- Entity links with `drawing_id` still function
- No data migration required

**New Imports:** Automatically use project-level linking.
- `drawing_id` is NULL in entity links
- Entities link directly to project
- No drawing record created

### Transition Strategy

**Option 1: Gradual Migration**
```
1. Keep existing projects as-is
2. New projects use project-level imports
3. Migrate old projects as needed (future feature)
```

**Option 2: Immediate Adoption**
```
1. Import DXF directly to project (no drawing)
2. Review generic objects via Object Reclassifier
3. Reclassify as needed
4. Export clean DXF from project
```

---

## User Guide

### Importing a DXF File

**Step 1: Upload DXF**
```
1. Navigate to DXF Import Tool
2. Select Project
3. Upload DXF file
```

**Step 2: Review Import Results**
```
Import Summary:
✓ 150 entities processed
✓ 120 automatically classified (high confidence)
  - 50 utility lines
  - 30 utility structures
  - 25 BMPs
  - 15 alignments
⚠ 30 flagged for review (low confidence)
  → Open Object Reclassifier to review
```

**Step 3: Review Unclassified Objects**
```
1. Go to /tools/object-reclassifier
2. Select your project
3. Click "Load Objects"
4. Review each generic object:
   - Check layer name and entity type
   - See confidence score and suggested type
   - Decide action (reclassify/approve/ignore)
```

### Reclassifying Objects

**Example Workflow:**

**Object Details:**
```
Layer: "PROPOSED-BIORETENTION"
Entity Type: LWPOLYLINE
Confidence: 0.55
Suggested Type: bmp
```

**Action: Reclassify**
```
1. Click "Reclassify" button
2. Select "BMP (Stormwater Feature)"
3. Add notes: "Bioretention area per plan C-3"
4. Submit
```

**Result:**
```
✓ Object reclassified to BMP
✓ New bmp_id created in bmps table
✓ Generic object status updated to "reclassified"
✓ Entity link UPDATED to point to new bmp (preserves unique constraint)
✓ No duplicate links created (safe for re-import)
```

**Important:** The reclassification process UPDATES the existing `dxf_entity_links` record to point to the new object. This ensures:
- Unique constraint compliance (`project_id, dxf_handle`)
- Safe re-import of the same DXF file
- No orphaned entity links
- Proper link chain: DXF entity → new specific object

### Viewing Intelligent Objects

**Map Viewer:**
```
1. Navigate to Map Viewer
2. Select Project
3. Toggle "Show Intelligent Objects" filter
4. See classified objects with different styling:
   - Blue = Utility Lines
   - Red = Utility Structures
   - Green = BMPs
   - Yellow = Alignments
   - Gray = Generic Objects (unclassified)
```

**Project Statistics:**
```
Project Dashboard shows:
- Total Intelligent Objects: 150
  - Utility Lines: 50
  - Utility Structures: 30
  - BMPs: 25
  - Alignments: 15
  - Trees: 12
  - Generic (Pending Review): 8
  - Generic (Approved): 10
```

---

## Technical Reference

### IntelligentObjectCreator Class

**Key Methods:**

```python
def create_from_entity(self, entity_data: Dict, project_id: str, 
                      drawing_id: Optional[str] = None) -> Optional[Tuple[str, str, str]]:
    """
    Create intelligent object from DXF entity.
    
    Flow:
    1. Classify layer name
    2. If confidence >= 0.7: Create specific object type
    3. If confidence < 0.7: Create generic object
    4. Create entity link (project-level or drawing-level)
    
    Returns:
        (object_type, object_id, table_name) or None
    """
```

**Confidence Thresholds:**
```python
HIGH_CONFIDENCE = 0.7  # Automatic classification
LOW_CONFIDENCE = 0.0   # Flag for review
```

### Database Triggers

**automatic_search_vector_update:**
```sql
CREATE TRIGGER update_generic_objects_search_vector
BEFORE INSERT OR UPDATE ON generic_objects
FOR EACH ROW EXECUTE FUNCTION tsvector_update_trigger(
    search_vector, 'pg_catalog.english',
    object_name, original_layer_name, original_entity_type, review_notes
);
```

### Layer Classification Engine

**Location:** `standards/layer_classifier_v2.py`

**Confidence Scoring:**
```python
def calculate_confidence(self, matches: List) -> float:
    """
    Calculate confidence based on:
    - Exact matches: 1.0
    - Partial matches: 0.6-0.9
    - Fuzzy matches: 0.3-0.6
    - No matches: 0.0
    
    Returns score 0.0 to 1.0
    """
```

---

## Best Practices

### 1. Import Workflow

```
✓ DO: Import DXF directly to project
✓ DO: Review generic objects immediately after import
✓ DO: Reclassify high-value objects (utilities, BMPs)
✓ DO: Approve clearly generic objects (logos, decorative elements)

✗ DON'T: Ignore all generic objects without review
✗ DON'T: Reclassify objects you're unsure about
✗ DON'T: Delete generic objects (mark as ignored instead)
```

### 2. Reclassification Guidelines

**When to Reclassify:**
- Object clearly belongs to a specific type
- Layer name is non-standard but intent is clear
- Object has engineering significance (utilities, BMPs)

**When to Approve:**
- Object is truly generic (text, logos, borders)
- No clear fit to any intelligent object type
- Decorative or annotation elements

**When to Ignore:**
- Object is clearly irrelevant
- Duplicate or error entities
- Test data or temporary objects

### 3. Confidence Interpretation

```
0.9-1.0: Extremely confident (rarely needs review)
0.7-0.9: Confident (automatic classification)
0.5-0.7: Uncertain (manual review recommended)
0.3-0.5: Low confidence (likely misclassified)
0.0-0.3: Very low confidence (unknown layer format)
```

---

## FAQ

### Q: What happens to my existing drawing-based projects?

**A:** They continue to work unchanged. The system supports both legacy drawing-level and new project-level entity linking.

### Q: Can I still use drawing files?

**A:** Yes, the system is backward compatible. You can create drawing records and link entities to them if needed.

### Q: What if I classify an object wrong?

**A:** You can reclassify it again. The system tracks the history in `review_notes` and allows re-reclassification.

### Q: How do I know which objects need review?

**A:** Use the Object Reclassifier tool with status filter = "pending" to see all objects awaiting review.

### Q: Can I bulk reclassify objects?

**A:** Not yet, but this feature is planned. Currently, you must reclassify objects individually to ensure accuracy.

### Q: What's the difference between "Approve" and "Ignore"?

**A:**
- **Approve:** Object is valid but doesn't need classification (e.g., logos, text labels)
- **Ignore:** Object should be hidden from review (e.g., errors, duplicates)

### Q: Where do reclassified objects go?

**A:** They're inserted into the appropriate specific table (utility_lines, bmps, etc.) and the generic_object record is marked as "reclassified" with a link to the new object.

---

## Support & Resources

**Documentation:**
- [Database Architecture Guide](DATABASE_ARCHITECTURE_GUIDE.md)
- [CAD Standards Guide](CAD_STANDARDS_GUIDE.md)
- [Replit Project Overview](replit.md)

**Key Files:**
- `intelligent_object_creator.py` - Classification engine
- `standards/layer_classifier_v2.py` - Layer name classifier
- `templates/tools/object_reclassifier.html` - Review UI
- `app.py` - API endpoints (lines 762-1124)

**Database Tables:**
- `generic_objects` - Unclassified entities
- `dxf_entity_links` - Entity-to-object mapping
- `utility_lines`, `utility_structures`, `bmps`, etc. - Specific object types

---

## Changelog

### Version 1.0 (November 2025)
- Initial release of Projects Only system
- Hybrid classification with confidence thresholds
- Generic objects table and review workflow
- Object Reclassifier UI
- Intelligent Objects Map API
- Enhanced project statistics

### Future Enhancements
- Bulk reclassification
- ML-based confidence improvement
- Automated object suggestions
- Integration with Map Viewer filtering
- Export reclassified objects to DXF


## Critical Production Fixes (November 2025)

### SRID Transformation and Geometry Validation

The Intelligent Objects Map API has been updated with critical fixes for production use:

**Fixed Issues:**
1. **SRID Transformation:** All queries now properly handle SRID 0 (CAD coordinates) and SRID 2226 (State Plane) with conversion to EPSG:4326 for Leaflet map display
2. **Geometry Validation:** Added `ST_IsValid(geometry)` filters to prevent rendering errors from malformed geometries
3. **Null Geometry Handling:** Queries explicitly filter out NULL geometries before transformation
4. **Increased Limits:** Changed from 100 to 500 objects per type (2500+ total capacity)
5. **Complete Coverage:** Generic objects now include ALL review statuses (pending/approved/reclassified/ignored) for complete map view

**Technical Details:**
```sql
-- Proper SRID handling with CASE statement
CASE
    WHEN ST_SRID(geometry) = 0 THEN ST_Transform(ST_SetSRID(geometry, 2226), 4326)
    WHEN ST_SRID(geometry) = 2226 THEN ST_Transform(geometry, 4326)
    ELSE ST_Transform(geometry, 4326)
END
```

### Entity Link Update During Reclassification

The reclassification endpoint now UPDATES existing entity links instead of creating duplicates:

**Fixed Issues:**
1. **Unique Constraint Compliance:** Reclassification now updates the existing `dxf_entity_links` record to point to the new object
2. **Safe Re-import:** Prevents unique constraint violations when re-importing the same DXF file
3. **No Orphaned Links:** Ensures clean link chain from DXF entity → intelligent object
4. **Fail-safe Creation:** If no existing link found (shouldn't happen), creates new one as fallback

**Implementation:**
```python
# UPDATE existing link (critical for unique constraint)
UPDATE dxf_entity_links
SET object_table_name = 'bmps',
    object_id = '<new_bmp_id>',
    updated_at = CURRENT_TIMESTAMP
WHERE project_id = '<project_id>' 
  AND dxf_handle = '<dxf_handle>'
  AND object_table_name = 'generic_objects'
  AND object_id = '<old_generic_object_id>'
```

**Why This Matters:**
- Without this fix, reclassification creates duplicate entity links with the same (project_id, dxf_handle)
- Unique constraint `(project_id, dxf_handle) WHERE drawing_id IS NULL` blocks future imports
- Update approach maintains referential integrity and import repeatability

### Production Readiness Checklist

✅ **SRID Transformation:** Handles all coordinate systems correctly  
✅ **Geometry Validation:** Filters invalid geometries before rendering  
✅ **Entity Link Management:** Updates existing links during reclassification  
✅ **Unique Constraint Compliance:** Safe for repeated DXF imports  
✅ **Complete Object Coverage:** Shows all object types and review statuses  
✅ **Error Handling:** Graceful handling of null/invalid geometries  
✅ **Scalability:** 500+ objects per type (2500+ total)  

---

