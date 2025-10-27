# Drawings Manager - Migration Documentation

## Overview

The Drawings Manager handles individual CAD drawing files and their associated data within the ACAD-GIS system. It provides complete lifecycle management for DXF/DWG files, including metadata storage, DXF content handling, georeferencing capabilities, and integration with the DXF import/export workflow. Drawings belong to projects and serve as the container for all CAD entities, blocks, layers, and text elements.

**Key Value:** CAD file management, DXF round-trip workflow, georeferencing support, drawing visualization data, sheet-to-drawing assignment tracking, and CAD entity storage for GIS integration.

## Use Cases

1. **Drawing Management**: Create, update, and organize CAD drawings within projects
2. **DXF Storage**: Store complete DXF file content for round-trip export
3. **Georeferencing**: Link CAD drawings to real-world coordinates with EPSG codes
4. **Drawing Visualization**: Provide render data (layers, blocks, bounds) for web-based CAD viewers
5. **Sheet Assignments**: Track which construction document sheets use which drawing layouts
6. **CAD Entity Storage**: Store geometric entities, text, blocks for GIS analysis
7. **Search & Filter**: Find drawings by name, number, type, or project

---

## Database Schema

### `drawings` - Core Drawing Table

Stores metadata and content for individual CAD drawing files.

```sql
CREATE TABLE drawings (
    drawing_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    drawing_name VARCHAR(255) NOT NULL,
    drawing_number VARCHAR(100),                   -- Sheet number or file code (C-1.1, SITE-01)
    drawing_type VARCHAR(100),                     -- 'Plan', 'Section', 'Detail', 'Profile', 'Site Plan'
    scale VARCHAR(50),                             -- '1"=20'', '1:100', 'AS NOTED'
    description TEXT,
    tags TEXT[],                                   -- Array for categorization/search
    metadata JSONB,                                -- Flexible metadata storage
    
    -- DXF Content (for round-trip export)
    dxf_content TEXT,                              -- Complete DXF file stored as text
    
    -- Georeferencing
    is_georeferenced BOOLEAN DEFAULT FALSE,
    drawing_epsg_code VARCHAR(20),                 -- 'EPSG:2227' (State Plane CA Zone 3)
    drawing_coordinate_system VARCHAR(100),        -- 'NAD83 State Plane California III'
    georef_point GEOMETRY(PointZ, 4326),          -- Reference point for georeferencing
    
    -- CAD Units
    cad_units VARCHAR(50) DEFAULT 'Feet',          -- 'Feet', 'Meters', 'Inches', 'Millimeters'
    scale_factor NUMERIC(10, 4) DEFAULT 1.0,       -- Unit conversion factor
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_drawings_project ON drawings(project_id);
CREATE INDEX idx_drawings_name ON drawings(drawing_name);
CREATE INDEX idx_drawings_number ON drawings(drawing_number);
CREATE INDEX idx_drawings_type ON drawings(drawing_type);
CREATE INDEX idx_drawings_georeferenced ON drawings(is_georeferenced);
CREATE INDEX idx_drawings_created ON drawings(created_at DESC);

-- GiST index for spatial queries (if using georef_point)
CREATE INDEX idx_drawings_georef_point ON drawings USING GIST(georef_point);
```

**Key Points:**
- `drawing_id` is UUID primary key
- `project_id` foreign key with CASCADE delete
- `drawing_name` is required (file name without extension)
- `drawing_number` typically matches sheet codes (C-1.1, S-2.3)
- `dxf_content` stores entire DXF file as TEXT for round-trip export
- `is_georeferenced` flag enables GIS integration
- PostGIS `GEOMETRY(PointZ, 4326)` for georeferencing (WGS84 with Z)
- `tags` array for flexible categorization
- `metadata` JSONB for extensible custom fields

**Related Tables** (Foreign Key Relationships):
- `projects` → ONE project (many-to-one)
- `sheet_drawing_assignments` → MANY sheets (one-to-many)
- `layers` → MANY layers (one-to-many) [via DXF schema]
- `block_inserts` → MANY blocks (one-to-many) [via DXF schema]
- `drawing_entities` → MANY entities (one-to-many) [via DXF schema]
- `drawing_text` → MANY text elements (one-to-many) [via DXF schema]

---

## API Endpoints

### `GET /api/drawings`
Get all drawings with optional search and project filter.

**Query Parameters:**
- `limit` (integer, default: 500): Maximum results to return
- `search` (string, optional): Search across name, number, type, and project name

**Response:**
```json
[
  {
    "drawing_id": "abc123...",
    "drawing_name": "Site Plan",
    "drawing_number": "C-1.1",
    "drawing_type": "Plan",
    "scale": "1\"=20'",
    "description": "Overall site plan showing grading and utilities",
    "tags": ["civil", "site", "grading"],
    "is_georeferenced": true,
    "drawing_epsg_code": "EPSG:2227",
    "drawing_coordinate_system": "NAD83 State Plane California III",
    "cad_units": "Feet",
    "scale_factor": 1.0,
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-20T14:22:00Z",
    "project_id": "project-uuid...",
    "project_name": "Main Street Development",
    "project_number": "2025-001",
    "has_content": true
  }
]
```

**Implementation Notes:**
- `has_content` is calculated: `CASE WHEN dxf_content IS NOT NULL THEN true ELSE false END`
- Ordered by `created_at DESC` (newest first)
- Limit defaults to 500 to prevent huge responses
- Search is case-insensitive (ILIKE in PostgreSQL)

---

### `GET /api/projects/<project_id>/drawings`
Get all drawings for a specific project.

**Path Parameters:**
- `project_id` (UUID): Project identifier

**Response:**
```json
[
  {
    "drawing_id": "abc123...",
    "drawing_name": "Site Plan",
    "drawing_number": "C-1.1",
    "drawing_type": "Plan",
    "scale": "1\"=20'",
    "description": "Overall site plan",
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-20T14:22:00Z",
    "is_georeferenced": true,
    "has_content": true
  }
]
```

**Implementation Notes:**
- Filtered by `project_id`
- Ordered by `drawing_number`, then `drawing_name`
- Used extensively in Sheet Sets Manager and Sheet Note Manager

---

### `GET /api/drawings/<drawing_id>`
Get detailed information for a specific drawing.

**Path Parameters:**
- `drawing_id` (UUID): Drawing identifier

**Response:**
```json
{
  "drawing_id": "abc123...",
  "drawing_name": "Site Plan",
  "drawing_number": "C-1.1",
  "drawing_type": "Plan",
  "scale": "1\"=20'",
  "description": "Overall site plan showing grading and utilities",
  "tags": ["civil", "site", "grading"],
  "metadata": {
    "author": "John Smith",
    "client_review_date": "2025-01-10",
    "custom_field": "value"
  },
  "is_georeferenced": true,
  "drawing_epsg_code": "EPSG:2227",
  "drawing_coordinate_system": "NAD83 State Plane California III",
  "cad_units": "Feet",
  "scale_factor": 1.0,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-20T14:22:00Z",
  "project_id": "project-uuid...",
  "project_name": "Main Street Development",
  "project_number": "2025-001",
  "has_content": true
}
```

**Error Responses:**
- `404 Not Found`: Drawing does not exist

---

### `POST /api/drawings`
Create a new drawing.

**Request Body:**
```json
{
  "drawing_name": "New Site Plan",
  "drawing_number": "C-1.2",
  "project_id": "project-uuid...",
  "drawing_type": "Plan",
  "scale": "1\"=30'",
  "description": "Updated site plan with revised grading",
  "tags": ["civil", "site", "revision"],
  "cad_units": "Feet",
  "scale_factor": 1.0,
  "is_georeferenced": false
}
```

**Required Fields:**
- `drawing_name` (string, NOT NULL)

**Optional Fields:**
- `drawing_number` (string)
- `project_id` (UUID) - Recommended but nullable
- `drawing_type` (string)
- `scale` (string)
- `description` (text)
- `tags` (array of strings)
- `metadata` (JSON object)
- `cad_units` (string, default: 'Feet')
- `scale_factor` (number, default: 1.0)
- `is_georeferenced` (boolean, default: false)
- `drawing_epsg_code` (string)
- `drawing_coordinate_system` (string)

**Response:**
```json
{
  "drawing_id": "new-uuid...",
  "drawing_name": "New Site Plan",
  "drawing_number": "C-1.2",
  "project_id": "project-uuid...",
  "created_at": "2025-01-25T11:45:00Z"
}
```

**Status Code:** `201 Created`

**Validation Rules:**
- `drawing_name` cannot be empty or null
- Returns `400 Bad Request` if `drawing_name` missing
- `project_id` should exist in projects table (referential integrity)

---

### `PUT /api/drawings/<drawing_id>`
Update an existing drawing.

**Path Parameters:**
- `drawing_id` (UUID): Drawing identifier

**Request Body:**
```json
{
  "drawing_name": "Updated Site Plan",
  "drawing_number": "C-1.2-REV1",
  "drawing_type": "Plan",
  "scale": "1\"=40'",
  "description": "Updated description",
  "tags": ["civil", "site", "final"],
  "is_georeferenced": true,
  "drawing_epsg_code": "EPSG:2227",
  "drawing_coordinate_system": "NAD83 State Plane California III"
}
```

**All Fields Optional** (only include fields to update)

**Response:**
```json
{
  "success": true,
  "drawing": {
    "drawing_id": "abc123...",
    "drawing_name": "Updated Site Plan",
    "drawing_number": "C-1.2-REV1",
    "updated_at": "2025-01-26T09:15:00Z"
  }
}
```

**Business Logic:**
- `updated_at` automatically set to current timestamp
- Partial updates supported
- Returns `404 Not Found` if drawing doesn't exist

---

### `DELETE /api/drawings/<drawing_id>`
Delete a drawing and all associated data.

**Path Parameters:**
- `drawing_id` (UUID): Drawing identifier

**Response:**
```json
{
  "success": true
}
```

**Status Code:** `200 OK`

**Business Logic:**
- **CASCADE DELETE**: Deletes all associated data:
  - All layers for the drawing
  - All block inserts for the drawing
  - All drawing entities for the drawing
  - All drawing text for the drawing
  - All sheet assignments for the drawing
- DXF content permanently deleted

**Warning:** Destructive operation that cannot be undone.

---

### `GET /api/drawings/<drawing_id>/render`
Get all data needed to render a drawing in a web viewer.

**Path Parameters:**
- `drawing_id` (UUID): Drawing identifier

**Query Parameters:**
- `limit` (integer, default: 2500): Maximum block inserts to return

**Response:**
```json
{
  "drawing": {
    "drawing_id": "abc123...",
    "drawing_name": "Site Plan",
    "drawing_number": "C-1.1",
    "is_georeferenced": true,
    "drawing_coordinate_system": "NAD83 State Plane California III",
    "drawing_epsg_code": "EPSG:2227"
  },
  "layers": [
    {
      "layer_id": "layer-uuid...",
      "layer_name": "C-BLDG",
      "color": 1,
      "linetype": "Continuous",
      "is_frozen": false,
      "is_locked": false
    }
  ],
  "inserts": [
    {
      "insert_id": "insert-uuid...",
      "insert_x": 1234.56,
      "insert_y": 7890.12,
      "insert_z": 0.0,
      "scale_x": 1.0,
      "scale_y": 1.0,
      "rotation": 45.0,
      "layout_name": "Model",
      "block_id": "block-uuid...",
      "block_name": "TREE-DECIDUOUS",
      "svg_content": "<svg>...</svg>",
      "category": "Landscape",
      "domain": "Site",
      "semantic_type": "vegetation",
      "semantic_label": "Deciduous Tree"
    }
  ],
  "bounds": {
    "min_x": 0.0,
    "max_x": 5000.0,
    "min_y": 0.0,
    "max_y": 3000.0
  },
  "stats": {
    "insert_count": 245,
    "total_inserts": 2450,
    "is_truncated": true
  }
}
```

**Implementation Notes:**
- Returns layers, block inserts with SVG symbols, and drawing bounds
- `limit` prevents huge responses (default 2500 inserts)
- `is_truncated` indicates if data was limited
- Used by web-based CAD viewer for visualization
- Joins `block_inserts` with `block_definitions` for SVG content

---

### `GET /api/drawings/<drawing_id>/extent`
Calculate full drawing extent/bounds without row limits.

**Path Parameters:**
- `drawing_id` (UUID): Drawing identifier

**Response:**
```json
{
  "drawing_id": "abc123...",
  "drawing_name": "Site Plan",
  "epsg_code": "EPSG:2227",
  "bounds": {
    "min_x": 0.0,
    "max_x": 5000.0,
    "min_y": 0.0,
    "max_y": 3000.0
  },
  "stats": {
    "total_features": 2450,
    "total_inserts": 2450,
    "total_entities": 0,
    "total_text": 0
  }
}
```

**Implementation Notes:**
- Calculates bounds from ALL block inserts (no limit)
- Used for map extent calculation and zooming
- Returns EPSG code for coordinate system context
- Feature counts useful for progress tracking

---

## DXF Integration

### DXF Content Storage

The `dxf_content` column stores the complete DXF file as TEXT for round-trip export.

**Storage Process:**
1. User uploads DXF file via DXF import endpoint
2. DXF parser reads file using `ezdxf` library
3. Entities, blocks, text extracted to separate tables
4. Original DXF file content stored in `dxf_content`
5. Drawing metadata (name, scale, units) extracted

**Round-Trip Export:**
1. User requests DXF export for drawing
2. System retrieves `dxf_content` from database
3. Optionally: Regenerate DXF from stored entities
4. Return DXF file to user

### Georeferencing Workflow

**Georeferencing CAD drawings enables GIS integration:**

1. **Set Reference Point:**
   ```sql
   UPDATE drawings 
   SET is_georeferenced = true,
       drawing_epsg_code = 'EPSG:2227',
       drawing_coordinate_system = 'NAD83 State Plane California III',
       georef_point = ST_GeomFromText('POINTZ(6000000 2000000 100)', 4326)
   WHERE drawing_id = 'abc123...';
   ```

2. **Transform Coordinates:**
   - CAD coordinates (local) → Real-world coordinates (EPSG)
   - Use PostGIS `ST_Transform()` for coordinate conversion
   - Apply to block inserts, entities, text

3. **GIS Integration:**
   - Export to GeoJSON with real-world coordinates
   - Overlay on web maps (Leaflet, Mapbox)
   - Perform spatial analysis (intersections, buffers, etc.)

---

## Business Logic & Validation Rules

### Drawing Creation
- `drawing_name` is required
- `project_id` should reference valid project
- `drawing_id` auto-generated as UUID
- Timestamps auto-set on creation

### Drawing Updates
- Partial updates supported
- `updated_at` automatically updated
- `drawing_id` and `created_at` are immutable

### Drawing Deletion
- **CASCADE DELETE**: All related data removed
- Includes layers, blocks, entities, text, assignments
- DXF content permanently deleted

### DXF Content Handling
- Stored as TEXT (can be large - 1MB to 100MB+)
- Consider compression or external storage for very large files
- `has_content` flag for quick checks without loading TEXT

### Georeferencing
- `is_georeferenced` flag enables GIS features
- Requires `drawing_epsg_code` and `georef_point`
- EPSG code format: "EPSG:2227" (State Plane)
- Georef point stored as WGS84 (EPSG:4326) with Z

### CAD Units
- Default: 'Feet'
- Options: 'Feet', 'Meters', 'Inches', 'Millimeters'
- `scale_factor` for unit conversion (e.g., 1 foot = 0.3048 meters)

---

## Frontend Component Structure

### Technology
- Currently uses **server-side rendering** with Jinja2 templates
- Drawing selectors used in Sheet Sets Manager, Sheet Note Manager
- No dedicated Drawings Manager UI page yet

### Common UI Patterns

**Drawing Selector Dropdown:**
```javascript
async function loadDrawings(projectId) {
  const response = await fetch(`/api/projects/${projectId}/drawings`);
  const drawings = await response.json();
  
  const selector = document.getElementById('drawing-selector');
  selector.innerHTML = '<option value="">Select Drawing...</option>';
  
  drawings.forEach(drawing => {
    const option = document.createElement('option');
    option.value = drawing.drawing_id;
    option.textContent = `${drawing.drawing_number || 'N/A'} - ${drawing.drawing_name}`;
    selector.appendChild(option);
  });
}
```

**Drawing Card Display:**
```javascript
function renderDrawingCard(drawing) {
  return `
    <div class="drawing-card">
      <div class="drawing-header">
        <span class="drawing-number">${drawing.drawing_number || 'No Number'}</span>
        ${drawing.has_content ? '<span class="badge-dxf">DXF</span>' : ''}
        ${drawing.is_georeferenced ? '<span class="badge-geo">GEO</span>' : ''}
      </div>
      <h4>${drawing.drawing_name}</h4>
      <p class="drawing-meta">
        ${drawing.drawing_type || 'Unknown Type'} | ${drawing.scale || 'No Scale'}
      </p>
      <p class="drawing-description">${drawing.description || ''}</p>
      <div class="drawing-tags">
        ${(drawing.tags || []).map(tag => `<span class="tag">${tag}</span>`).join('')}
      </div>
    </div>
  `;
}
```

### Enhancement: Full Drawings Manager UI

**Recommended Component Structure:**
```
DrawingsApp (root component)
├── TopBar
│   ├── Project Filter
│   ├── Search Input (name, number, type)
│   ├── Upload DXF Button
│   └── Stats (total drawings, georeferenced count)
├── DrawingsList
│   ├── DrawingCard (for each drawing)
│   │   ├── Drawing Number & Name
│   │   ├── Type & Scale
│   │   ├── DXF Badge (if has_content)
│   │   ├── GEO Badge (if georeferenced)
│   │   ├── Tags
│   │   └── Actions (View, Edit, Export, Delete)
└── DrawingDetailsModal
    ├── Edit Form
    ├── Georeferencing Controls
    └── DXF Upload/Export
```

---

## Integration Tips for FastAPI

### Pydantic Models

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class DrawingBase(BaseModel):
    drawing_name: str = Field(..., min_length=1, max_length=255)
    drawing_number: Optional[str] = Field(None, max_length=100)
    project_id: Optional[UUID] = None
    drawing_type: Optional[str] = Field(None, max_length=100)
    scale: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    tags: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = {}
    cad_units: str = "Feet"
    scale_factor: float = 1.0
    is_georeferenced: bool = False
    drawing_epsg_code: Optional[str] = None
    drawing_coordinate_system: Optional[str] = None

class DrawingCreate(DrawingBase):
    pass

class DrawingUpdate(BaseModel):
    drawing_name: Optional[str] = Field(None, min_length=1, max_length=255)
    drawing_number: Optional[str] = None
    drawing_type: Optional[str] = None
    scale: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    is_georeferenced: Optional[bool] = None
    drawing_epsg_code: Optional[str] = None
    drawing_coordinate_system: Optional[str] = None

class Drawing(DrawingBase):
    drawing_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class DrawingWithContent(Drawing):
    has_content: bool = False

class DrawingWithProject(DrawingWithContent):
    project_name: Optional[str] = None
    project_number: Optional[str] = None

class DrawingRenderData(BaseModel):
    drawing: Dict[str, Any]
    layers: List[Dict[str, Any]]
    inserts: List[Dict[str, Any]]
    bounds: Dict[str, float]
    stats: Dict[str, Any]

class DrawingExtent(BaseModel):
    drawing_id: UUID
    drawing_name: str
    epsg_code: Optional[str]
    bounds: Dict[str, float]
    stats: Dict[str, int]
```

### SQLAlchemy Models

```python
from sqlalchemy import Column, String, Text, DateTime, Boolean, Numeric, UUID, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

class Drawing(Base):
    __tablename__ = "drawings"
    
    drawing_id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    project_id = Column(UUID, ForeignKey("projects.project_id", ondelete="CASCADE"))
    drawing_name = Column(String(255), nullable=False)
    drawing_number = Column(String(100))
    drawing_type = Column(String(100))
    scale = Column(String(50))
    description = Column(Text)
    tags = Column(ARRAY(Text))
    metadata = Column(JSONB)
    
    # DXF Content
    dxf_content = Column(Text)
    
    # Georeferencing
    is_georeferenced = Column(Boolean, default=False)
    drawing_epsg_code = Column(String(20))
    drawing_coordinate_system = Column(String(100))
    georef_point = Column(Geometry('POINTZ', srid=4326))
    
    # CAD Units
    cad_units = Column(String(50), default='Feet')
    scale_factor = Column(Numeric(10, 4), default=1.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="drawings")
    sheet_assignments = relationship("SheetDrawingAssignment", back_populates="drawing", cascade="all, delete-orphan")
    layers = relationship("Layer", back_populates="drawing", cascade="all, delete-orphan")
    block_inserts = relationship("BlockInsert", back_populates="drawing", cascade="all, delete-orphan")
    entities = relationship("DrawingEntity", back_populates="drawing", cascade="all, delete-orphan")
    text_elements = relationship("DrawingText", back_populates="drawing", cascade="all, delete-orphan")
```

### FastAPI Router Example

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import List, Optional

router = APIRouter(prefix="/api/drawings", tags=["drawings"])

@router.get("/", response_model=List[DrawingWithProject])
def get_drawings(
    limit: int = Query(500, le=1000),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all drawings with optional search"""
    query = db.query(
        Drawing,
        Project.project_name,
        Project.project_number,
        case(
            (Drawing.dxf_content.isnot(None), True),
            else_=False
        ).label("has_content")
    ).outerjoin(Project)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Drawing.drawing_name.ilike(search_term),
                Drawing.drawing_number.ilike(search_term),
                Drawing.drawing_type.ilike(search_term),
                Project.project_name.ilike(search_term)
            )
        )
    
    results = query.order_by(Drawing.created_at.desc()).limit(limit).all()
    
    return [
        DrawingWithProject(
            **drawing.__dict__,
            project_name=project_name,
            project_number=project_number,
            has_content=has_content
        )
        for drawing, project_name, project_number, has_content in results
    ]

@router.get("/{drawing_id}", response_model=DrawingWithProject)
def get_drawing(drawing_id: UUID, db: Session = Depends(get_db)):
    """Get a specific drawing"""
    result = db.query(
        Drawing,
        Project.project_name,
        Project.project_number,
        case((Drawing.dxf_content.isnot(None), True), else_=False).label("has_content")
    ).outerjoin(Project).filter(Drawing.drawing_id == drawing_id).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Drawing not found")
    
    drawing, project_name, project_number, has_content = result
    return DrawingWithProject(**drawing.__dict__, project_name=project_name, 
                             project_number=project_number, has_content=has_content)

@router.post("/", response_model=Drawing, status_code=201)
def create_drawing(drawing: DrawingCreate, db: Session = Depends(get_db)):
    """Create a new drawing"""
    db_drawing = Drawing(**drawing.dict())
    db.add(db_drawing)
    db.commit()
    db.refresh(db_drawing)
    return db_drawing

@router.put("/{drawing_id}", response_model=Drawing)
def update_drawing(drawing_id: UUID, drawing: DrawingUpdate, db: Session = Depends(get_db)):
    """Update an existing drawing"""
    db_drawing = db.query(Drawing).filter(Drawing.drawing_id == drawing_id).first()
    
    if not db_drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")
    
    update_data = drawing.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_drawing, field, value)
    
    db.commit()
    db.refresh(db_drawing)
    return db_drawing

@router.delete("/{drawing_id}")
def delete_drawing(drawing_id: UUID, db: Session = Depends(get_db)):
    """Delete a drawing (cascades to all related data)"""
    db_drawing = db.query(Drawing).filter(Drawing.drawing_id == drawing_id).first()
    
    if not db_drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")
    
    db.delete(db_drawing)
    db.commit()
    return {"success": True}

@router.get("/{drawing_id}/render", response_model=DrawingRenderData)
def get_drawing_render_data(
    drawing_id: UUID,
    limit: int = Query(2500, le=10000),
    db: Session = Depends(get_db)
):
    """Get all data needed to render a drawing"""
    # Implementation similar to existing endpoint
    # Returns layers, inserts, bounds, stats
    pass

@router.get("/{drawing_id}/extent", response_model=DrawingExtent)
def get_drawing_extent(drawing_id: UUID, db: Session = Depends(get_db)):
    """Calculate full drawing extent without row limits"""
    # Implementation similar to existing endpoint
    # Returns bounds and feature counts
    pass
```

---

## Testing Checklist

- [ ] Create drawing with only required field (drawing_name)
- [ ] Create drawing with all fields populated
- [ ] Create drawing with tags array
- [ ] Create drawing with metadata JSON
- [ ] Retrieve list of all drawings (verify has_content flag)
- [ ] Retrieve drawings by project ID
- [ ] Retrieve single drawing by ID
- [ ] Search drawings by name, number, type
- [ ] Update drawing (partial update)
- [ ] Update drawing (full update)
- [ ] Verify `updated_at` changes after update
- [ ] Delete drawing (verify CASCADE to layers, blocks, entities)
- [ ] Test georeferencing (set EPSG code, georef point)
- [ ] Get drawing render data (verify layers, inserts, bounds)
- [ ] Get drawing extent (verify full bounds calculation)
- [ ] Upload DXF file (test DXF import)
- [ ] Export DXF file (test DXF export)
- [ ] Test with very large DXF content (>10MB)
- [ ] Verify spatial index on georef_point

---

## Migration Checklist

- [ ] Create `drawings` table with proper indexes
- [ ] Install PostGIS extension for georeferencing
- [ ] Implement Pydantic models for request/response validation
- [ ] Create SQLAlchemy ORM model with relationships
- [ ] Implement API routes for all CRUD operations
- [ ] Add CASCADE delete relationships
- [ ] Configure spatial indexes (GIST) for georef_point
- [ ] Implement DXF import/export endpoints
- [ ] Add render data and extent endpoints
- [ ] Add error handling and validation
- [ ] Document API in Swagger/OpenAPI
- [ ] Consider DXF content compression strategy

---

## Production Recommendations

### DXF Content Storage Strategy

For very large DXF files (>100MB):
1. **External Storage**: Store DXF in S3/Blob storage, keep URL in database
2. **Compression**: Use PostgreSQL TOAST compression or gzip before storage
3. **Lazy Loading**: Don't include `dxf_content` in list queries

```sql
-- Exclude dxf_content from list queries
SELECT drawing_id, drawing_name, ... (exclude dxf_content)
FROM drawings;

-- Only fetch dxf_content when explicitly needed
SELECT dxf_content FROM drawings WHERE drawing_id = 'abc123';
```

### Pagination & Search

```python
@router.get("/", response_model=PaginatedDrawings)
def get_drawings(
    page: int = 1,
    per_page: int = 50,
    search: Optional[str] = None,
    project_id: Optional[UUID] = None,
    is_georeferenced: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Drawing)
    
    if search:
        query = query.filter(
            or_(
                Drawing.drawing_name.ilike(f"%{search}%"),
                Drawing.drawing_number.ilike(f"%{search}%")
            )
        )
    
    if project_id:
        query = query.filter(Drawing.project_id == project_id)
    
    if is_georeferenced is not None:
        query = query.filter(Drawing.is_georeferenced == is_georeferenced)
    
    total = query.count()
    drawings = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return {
        "drawings": drawings,
        "total": total,
        "page": page,
        "per_page": per_page
    }
```

### Full-Text Search

```sql
-- Add search vector column
ALTER TABLE drawings ADD COLUMN search_vector tsvector;

-- Create GIN index
CREATE INDEX idx_drawings_search ON drawings USING GIN(search_vector);

-- Update trigger
CREATE TRIGGER drawings_search_update BEFORE INSERT OR UPDATE
ON drawings FOR EACH ROW EXECUTE FUNCTION
tsvector_update_trigger(search_vector, 'pg_catalog.english', 
    drawing_name, drawing_number, description);
```

### Georeferencing Best Practices

- Use appropriate EPSG code for your region (State Plane, UTM, etc.)
- Store georef point in WGS84 (EPSG:4326) for web map compatibility
- Transform coordinates using PostGIS `ST_Transform()` when needed
- Index georef_point with GIST for spatial queries

---

## Related Documentation

- **MIGRATION_PROJECTS_MANAGER.md**: Parent projects that contain drawings
- **MIGRATION_SHEET_SET_MANAGER.md**: Sheet assignments that link to drawings
- **create_dxf_export_schema.sql**: Full DXF schema with entities, blocks, layers
