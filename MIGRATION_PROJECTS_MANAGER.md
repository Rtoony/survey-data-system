# Projects Manager - Migration Documentation

## Overview

The Projects Manager is the foundational organizational unit for the entire ACAD-GIS system. It provides project-level management that serves as the parent container for all related drawings, sheet sets, note sets, and project details. Projects represent client engagements or development efforts that encompass multiple CAD drawings and construction documents.

**Key Value:** Centralized project organization, client tracking, drawing aggregation, project lifecycle management, and serves as the primary navigation/filtering mechanism throughout the application.

## Use Cases

1. **Project Organization**: Create and manage client projects with names, numbers, and descriptions
2. **Client Management**: Track client information for billing and communication
3. **Drawing Aggregation**: View all drawings associated with a project in one place
4. **Project Navigation**: Filter and navigate through projects to access related data
5. **Project Lifecycle**: Track project creation dates and manage project closure/archival
6. **Cross-Feature Integration**: Serve as the foreign key parent for drawings, sheet sets, note sets, and project details

---

## Database Schema

### `projects` - Core Project Table

Central table that serves as the parent for all project-related data.

```sql
CREATE TABLE projects (
    project_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_name VARCHAR(255) NOT NULL,
    project_number VARCHAR(100),                   -- Client project number, PO number, job code
    client_name VARCHAR(255),                      -- Client/owner name
    description TEXT,                              -- Project description/scope
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_projects_name ON projects(project_name);
CREATE INDEX idx_projects_client ON projects(client_name);
CREATE INDEX idx_projects_number ON projects(project_number);
CREATE INDEX idx_projects_created ON projects(created_at DESC);
```

**Key Points:**
- `project_id` is UUID primary key
- `project_name` is required (NOT NULL)
- `project_number` can store client job codes, PO numbers, or internal tracking numbers
- `client_name` stores client/owner for billing and reporting
- `description` provides detailed project scope/notes
- Timestamps track creation and last update

**Related Tables** (Foreign Key Relationships):
- `drawings` → `project_id` (one-to-many)
- `sheet_sets` → `project_id` (one-to-many)
- `sheet_note_sets` → `project_id` (one-to-many)
- `project_details` → `project_id` (one-to-one)

---

## API Endpoints

### `GET /api/projects`
Get all projects with drawing counts.

**Query Parameters:**
None

**Response:**
```json
{
  "projects": [
    {
      "project_id": "123e4567-e89b-12d3-a456-426614174000",
      "project_name": "Main Street Development",
      "project_number": "2025-001",
      "client_name": "City of San Jose",
      "description": "Mixed-use development with retail and residential components",
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-20T14:22:00Z",
      "drawing_count": 12
    },
    {
      "project_id": "abc12345-e89b-12d3-a456-426614174001",
      "project_name": "Civic Center Improvements",
      "project_number": "CC-2025-02",
      "client_name": "City Public Works Department",
      "description": "Site improvements including grading, utilities, and paving",
      "created_at": "2025-01-10T09:00:00Z",
      "updated_at": "2025-01-10T09:00:00Z",
      "drawing_count": 8
    }
  ]
}
```

**Implementation Notes:**
- Returns ALL projects (no pagination in current implementation)
- Includes `drawing_count` via LEFT JOIN aggregation
- Ordered by `created_at DESC` (newest first)
- `updated_at` may equal `created_at` if project never modified

---

### `GET /api/projects/<project_id>`
Get detailed information for a specific project.

**Path Parameters:**
- `project_id` (UUID): Project identifier

**Response:**
```json
{
  "project": {
    "project_id": "123e4567-e89b-12d3-a456-426614174000",
    "project_name": "Main Street Development",
    "project_number": "2025-001",
    "client_name": "City of San Jose",
    "description": "Mixed-use development with retail and residential components",
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-20T14:22:00Z",
    "drawing_count": 12
  }
}
```

**Error Responses:**
- `404 Not Found`: Project does not exist

---

### `POST /api/projects`
Create a new project.

**Request Body:**
```json
{
  "project_name": "New Development Project",
  "project_number": "2025-003",
  "client_name": "ABC Development LLC",
  "description": "Commercial office building with underground parking"
}
```

**Required Fields:**
- `project_name` (string, NOT NULL)

**Optional Fields:**
- `project_number` (string)
- `client_name` (string)
- `description` (text)

**Response:**
```json
{
  "project_id": "new-uuid-here...",
  "project_name": "New Development Project",
  "client_name": "ABC Development LLC",
  "created_at": "2025-01-25T11:45:00Z"
}
```

**Status Code:** `201 Created`

**Validation Rules:**
- `project_name` cannot be empty or null
- Returns `400 Bad Request` if `project_name` missing

**Business Logic:**
- `project_id` auto-generated as UUID
- `created_at` auto-set to current timestamp
- `updated_at` initially equals `created_at`

---

### `PUT /api/projects/<project_id>`
Update an existing project.

**Path Parameters:**
- `project_id` (UUID): Project identifier

**Request Body:**
```json
{
  "project_name": "Updated Project Name",
  "project_number": "2025-003-REV1",
  "client_name": "ABC Development LLC (Updated)",
  "description": "Updated description with additional scope details"
}
```

**All Fields Optional** (only include fields to update):
- `project_name` (string)
- `project_number` (string)
- `client_name` (string)
- `description` (text)

**Response:**
```json
{
  "success": true,
  "project": {
    "project_id": "123e4567...",
    "project_name": "Updated Project Name",
    "project_number": "2025-003-REV1",
    "client_name": "ABC Development LLC (Updated)",
    "description": "Updated description with additional scope details",
    "updated_at": "2025-01-26T09:15:00Z"
  }
}
```

**Business Logic:**
- `updated_at` automatically set to current timestamp
- Partial updates supported (only provided fields are modified)
- Returns `404 Not Found` if project doesn't exist

---

### `DELETE /api/projects/<project_id>`
Delete a project and all related data.

**Path Parameters:**
- `project_id` (UUID): Project identifier

**Response:**
```json
{
  "success": true
}
```

**Status Code:** `200 OK`

**Business Logic:**
- **CASCADE DELETE**: Deletes all associated data:
  - All drawings for the project
  - All sheet sets for the project
  - All note sets for the project
  - Project details record
  - All DXF entities linked to project drawings
  - All sheet assignments
  - All note assignments

**Warning:** This is a destructive operation that cannot be undone. Consider implementing soft delete (is_archived flag) in production.

**Error Responses:**
- `404 Not Found`: Project does not exist
- `500 Internal Server Error`: Database constraint violation or other error

---

### `GET /api/recent-activity`
Get recent projects and drawings for dashboard display.

**Query Parameters:**
None

**Response:**
```json
{
  "recent_projects": [
    {
      "project_id": "123e4567...",
      "project_name": "Main Street Development",
      "project_number": "2025-001",
      "client_name": "City of San Jose",
      "created_at": "2025-01-15T10:30:00Z",
      "drawing_count": 12
    }
  ],
  "recent_drawings": [
    {
      "drawing_id": "abc123...",
      "drawing_name": "Site Plan",
      "drawing_number": "C-1.1",
      "drawing_type": "Plan",
      "created_at": "2025-01-20T14:30:00Z",
      "project_name": "Main Street Development",
      "project_number": "2025-001"
    }
  ],
  "stats": {
    "total_projects": 45,
    "total_drawings": 234,
    "total_layers": 150,
    "total_blocks": 89
  }
}
```

**Implementation Notes:**
- Returns 5 most recent projects
- Returns 5 most recent drawings
- Includes database statistics
- **Cached for 60 seconds** using Flask-Caching

---

## Business Logic & Validation Rules

### Project Creation
- `project_name` is required and cannot be null or empty
- All other fields are optional
- `project_id` auto-generated as UUID
- Timestamps auto-set on creation

### Project Updates
- Partial updates supported (only modified fields need to be sent)
- `updated_at` automatically updated to current timestamp
- `project_id` and `created_at` are immutable

### Project Deletion
- **Cascading Delete**: All related records deleted automatically:
  - Drawings (and their DXF entities)
  - Sheet sets (and their sheets, assignments, revisions)
  - Note sets (and their project notes, assignments)
  - Project details
- Current implementation: Hard delete (permanent removal)
- **Production Recommendation**: Implement soft delete with `is_archived` flag to preserve historical data

### Drawing Count Aggregation
- Calculated via `COUNT(d.drawing_id)` with LEFT JOIN
- Count includes ALL drawings (active and inactive)
- Returns `0` if no drawings exist for project

### Filtering & Search
- No built-in search in current implementation
- Frontend can filter projects client-side by name, number, or client
- **Enhancement Opportunity**: Add server-side search query parameter

---

## Frontend Component Structure

### Technology
- Currently uses **server-side rendering** with Jinja2 templates
- Project selector dropdowns throughout application (Sheet Sets, Sheet Notes, etc.)
- No dedicated Projects Manager UI page yet

### Common UI Patterns

**Project Selector Dropdown:**
```javascript
// Used in Sheet Sets Manager, Sheet Notes Manager, etc.
async function loadProjects() {
  const response = await fetch('/api/projects');
  const data = await response.json();
  const projects = data.projects;
  
  const selector = document.getElementById('project-selector');
  selector.innerHTML = '<option value="">Select Project...</option>';
  
  projects.forEach(project => {
    const option = document.createElement('option');
    option.value = project.project_id;
    option.textContent = `${project.project_name} ${project.project_number ? '(' + project.project_number + ')' : ''}`;
    selector.appendChild(option);
  });
}
```

**Project Display Pattern:**
```javascript
function renderProjectCard(project) {
  return `
    <div class="project-card">
      <h3>${project.project_name}</h3>
      <div class="project-meta">
        <span class="project-number">${project.project_number || 'No Number'}</span>
        <span class="client-name">${project.client_name || 'No Client'}</span>
      </div>
      <p class="project-description">${project.description || 'No description'}</p>
      <div class="project-stats">
        <span class="badge">${project.drawing_count} Drawings</span>
      </div>
    </div>
  `;
}
```

### Enhancement: Full Projects Manager UI

**Recommended Component Structure:**
```
ProjectsApp (root component)
├── TopBar
│   ├── Search Input (filter by name, number, client)
│   ├── Create Project Button
│   └── Stats (total projects, total drawings)
├── ProjectsList
│   ├── ProjectCard (for each project)
│   │   ├── Project Name & Number
│   │   ├── Client Name
│   │   ├── Description Preview
│   │   ├── Drawing Count Badge
│   │   ├── Created Date
│   │   └── Actions (Edit, Delete)
└── ProjectDetailsModal
    ├── Edit Form (name, number, client, description)
    └── Save/Cancel Buttons
```

---

## Integration Tips for FastAPI

### Pydantic Models

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class ProjectBase(BaseModel):
    project_name: str = Field(..., min_length=1, max_length=255)
    project_number: Optional[str] = Field(None, max_length=100)
    client_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    project_name: Optional[str] = Field(None, min_length=1, max_length=255)
    project_number: Optional[str] = Field(None, max_length=100)
    client_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None

class Project(ProjectBase):
    project_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ProjectWithCount(Project):
    drawing_count: int = 0
```

### SQLAlchemy Models

```python
from sqlalchemy import Column, String, Text, DateTime, UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

class Project(Base):
    __tablename__ = "projects"
    
    project_id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    project_name = Column(String(255), nullable=False)
    project_number = Column(String(100))
    client_name = Column(String(255))
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    drawings = relationship("Drawing", back_populates="project", cascade="all, delete-orphan")
    sheet_sets = relationship("SheetSet", back_populates="project", cascade="all, delete-orphan")
    note_sets = relationship("SheetNoteSet", back_populates="project", cascade="all, delete-orphan")
    project_details = relationship("ProjectDetails", back_populates="project", uselist=False, cascade="all, delete-orphan")
```

### FastAPI Router Example

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

router = APIRouter(prefix="/api/projects", tags=["projects"])

@router.get("/", response_model=List[ProjectWithCount])
def get_projects(db: Session = Depends(get_db)):
    """Get all projects with drawing counts"""
    projects = db.query(
        Project,
        func.count(Drawing.drawing_id).label("drawing_count")
    ).outerjoin(
        Drawing, Project.project_id == Drawing.project_id
    ).group_by(
        Project.project_id
    ).order_by(
        Project.created_at.desc()
    ).all()
    
    return [
        ProjectWithCount(
            **project.__dict__,
            drawing_count=drawing_count
        )
        for project, drawing_count in projects
    ]

@router.get("/{project_id}", response_model=ProjectWithCount)
def get_project(project_id: UUID, db: Session = Depends(get_db)):
    """Get a specific project"""
    result = db.query(
        Project,
        func.count(Drawing.drawing_id).label("drawing_count")
    ).outerjoin(
        Drawing, Project.project_id == Drawing.project_id
    ).filter(
        Project.project_id == project_id
    ).group_by(
        Project.project_id
    ).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project, drawing_count = result
    return ProjectWithCount(**project.__dict__, drawing_count=drawing_count)

@router.post("/", response_model=Project, status_code=201)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project"""
    db_project = Project(**project.dict())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.put("/{project_id}", response_model=Project)
def update_project(project_id: UUID, project: ProjectUpdate, db: Session = Depends(get_db)):
    """Update an existing project"""
    db_project = db.query(Project).filter(Project.project_id == project_id).first()
    
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    update_data = project.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)
    
    db.commit()
    db.refresh(db_project)
    return db_project

@router.delete("/{project_id}")
def delete_project(project_id: UUID, db: Session = Depends(get_db)):
    """Delete a project (cascades to all related data)"""
    db_project = db.query(Project).filter(Project.project_id == project_id).first()
    
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db.delete(db_project)
    db.commit()
    return {"success": True}

@router.get("/recent-activity/")
def get_recent_activity(db: Session = Depends(get_db)):
    """Get recent projects and drawings for dashboard"""
    recent_projects = db.query(
        Project,
        func.count(Drawing.drawing_id).label("drawing_count")
    ).outerjoin(
        Drawing
    ).group_by(
        Project.project_id
    ).order_by(
        Project.created_at.desc()
    ).limit(5).all()
    
    recent_drawings = db.query(Drawing).order_by(Drawing.created_at.desc()).limit(5).all()
    
    stats = {
        "total_projects": db.query(Project).count(),
        "total_drawings": db.query(Drawing).count(),
        "total_layers": db.query(LayerStandard).count(),
        "total_blocks": db.query(BlockDefinition).count()
    }
    
    return {
        "recent_projects": [
            ProjectWithCount(**p.__dict__, drawing_count=count)
            for p, count in recent_projects
        ],
        "recent_drawings": recent_drawings,
        "stats": stats
    }
```

---

## Testing Checklist

- [ ] Create project with only required field (project_name)
- [ ] Create project with all fields populated
- [ ] Retrieve list of all projects (verify drawing count)
- [ ] Retrieve single project by ID
- [ ] Update project (partial update - only some fields)
- [ ] Update project (full update - all fields)
- [ ] Verify `updated_at` changes after update
- [ ] Create project with duplicate name (should succeed - no unique constraint)
- [ ] Delete project with no drawings (verify success)
- [ ] Delete project with drawings (verify CASCADE delete)
- [ ] Verify deleted project also deletes sheet sets
- [ ] Verify deleted project also deletes note sets
- [ ] Verify deleted project also deletes project details
- [ ] Test GET with non-existent project_id (verify 404)
- [ ] Test DELETE with non-existent project_id (verify 404)
- [ ] Test recent activity endpoint (verify caching)
- [ ] Verify timestamp auto-generation on create

---

## Migration Checklist

- [ ] Create `projects` table with proper indexes
- [ ] Implement Pydantic models for request/response validation
- [ ] Create SQLAlchemy ORM model with relationships
- [ ] Implement API routes for all CRUD operations
- [ ] Add CASCADE delete relationships for all child tables
- [ ] Configure proper indexes for query performance
- [ ] Implement caching for recent activity endpoint
- [ ] Add error handling and validation
- [ ] Document API in Swagger/OpenAPI
- [ ] Consider soft delete implementation (is_archived flag)

---

## Production Recommendations

### Soft Delete Pattern
Instead of permanent deletion, consider implementing soft delete:

```sql
ALTER TABLE projects ADD COLUMN is_archived BOOLEAN DEFAULT FALSE;
ALTER TABLE projects ADD COLUMN archived_at TIMESTAMP;
CREATE INDEX idx_projects_archived ON projects(is_archived);
```

Then modify queries to filter out archived projects:
```sql
WHERE is_archived = FALSE
```

### Search Implementation
Add full-text search capabilities:

```sql
-- Add search vector column
ALTER TABLE projects ADD COLUMN search_vector tsvector;

-- Create GIN index for fast search
CREATE INDEX idx_projects_search ON projects USING GIN(search_vector);

-- Update search vector on insert/update
CREATE TRIGGER projects_search_update BEFORE INSERT OR UPDATE
ON projects FOR EACH ROW EXECUTE FUNCTION
tsvector_update_trigger(search_vector, 'pg_catalog.english', 
    project_name, project_number, client_name, description);
```

### Pagination
Add pagination to GET /api/projects for large datasets:

```python
@router.get("/", response_model=PaginatedProjects)
def get_projects(
    page: int = 1,
    per_page: int = 50,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Project)
    
    if search:
        query = query.filter(
            or_(
                Project.project_name.ilike(f"%{search}%"),
                Project.project_number.ilike(f"%{search}%"),
                Project.client_name.ilike(f"%{search}%")
            )
        )
    
    total = query.count()
    projects = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return {
        "projects": projects,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }
```

---

## Related Documentation

- **MIGRATION_SHEET_SET_MANAGER.md**: Sheet sets that reference projects
- **MIGRATION_SHEET_NOTE_MANAGER.md**: Note sets that reference projects
- **MIGRATION_DRAWINGS_MANAGER.md**: Drawings that belong to projects
- **project_details table**: One-to-one extension in MIGRATION_SHEET_SET_MANAGER.md
