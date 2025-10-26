# Sheet Note Manager - Migration Documentation

## Overview

The Sheet Note Manager is a comprehensive system for managing construction drawing notes across projects and sheets. It enables teams to maintain a library of standard company-approved notes, create project-specific note sets (with versioning), override standard notes with custom text, and assign notes to specific drawing sheets/layouts for automated legend generation.

**Key Value:** Eliminates repetitive note typing, ensures consistent language across projects, maintains legal compliance, tracks note usage, and automatically generates formatted note legends for CAD drawings.

## Use Cases

1. **Standard Note Library**: Maintain company-wide approved notes (e.g., "All dimensions to be verified in field")
2. **Project Note Sets**: Create versioned collections of notes per project (Draft v1, 100% Submittal, Final Construction)
3. **Custom Notes**: Add project-specific notes while optionally linking to standard notes
4. **Note Assignment**: Assign notes to specific sheets/layouts with sequence control
5. **Legend Generation**: Automatically format notes into ready-to-insert CAD legends

---

## Database Schema

### 1. `standard_notes` - Company Note Library

Master library of company-approved standard notes.

```sql
CREATE TABLE standard_notes (
    note_id SERIAL PRIMARY KEY,
    note_category VARCHAR(100),                    -- 'General', 'Grading', 'Utilities', 'Demolition', etc.
    note_title VARCHAR(255) NOT NULL,
    note_text TEXT NOT NULL,
    discipline VARCHAR(50),                        -- 'Civil', 'Structural', 'MEP', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_standard_notes_category ON standard_notes(note_category);
CREATE INDEX idx_standard_notes_discipline ON standard_notes(discipline);
```

**Key Points:**
- `note_id` is INTEGER (SERIAL) not UUID
- Categories organize notes for easy browsing
- `is_active` allows soft deletion of outdated notes
- Discipline enables filtering by trade/specialty

---

### 2. `sheet_note_sets` - Project Note Collections

Organizes notes into versioned sets per project.

```sql
CREATE TABLE sheet_note_sets (
    set_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    set_name VARCHAR(255) NOT NULL,                -- '100% Civil Plans Notes', 'Final Construction Notes'
    description TEXT,
    discipline VARCHAR(50),
    is_active BOOLEAN DEFAULT FALSE,               -- Only one active set per project
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sheet_note_sets_project ON sheet_note_sets(project_id);
CREATE INDEX idx_sheet_note_sets_active ON sheet_note_sets(project_id, is_active);
```

**Key Points:**
- Each project can have multiple note sets (for versioning)
- Only ONE set can be `is_active=TRUE` per project at a time
- Cascading delete removes all note sets when project is deleted
- Set name should be descriptive (include phase/version info)

---

### 3. `project_sheet_notes` - Project Note Instance

Stores actual notes for each project (either standard or custom).

```sql
CREATE TABLE project_sheet_notes (
    project_note_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    set_id UUID NOT NULL REFERENCES sheet_note_sets(set_id) ON DELETE CASCADE,
    standard_note_id INTEGER REFERENCES standard_notes(note_id) ON DELETE SET NULL,  -- NULL = custom note
    display_code VARCHAR(20),                      -- 'GN-1', '1', 'A', etc. for legend display
    custom_title VARCHAR(255),                     -- Overrides standard_title if present
    custom_text TEXT,                              -- Overrides standard_text if present
    is_modified BOOLEAN DEFAULT FALSE,             -- TRUE if standard note was customized
    sort_order INTEGER DEFAULT 0,                  -- For manual reordering within set
    usage_count INTEGER DEFAULT 0,                 -- How many sheets use this note
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_project_sheet_notes_set ON project_sheet_notes(set_id);
CREATE INDEX idx_project_sheet_notes_standard ON project_sheet_notes(standard_note_id);
CREATE INDEX idx_project_sheet_notes_order ON project_sheet_notes(set_id, sort_order);
```

**Key Points:**
- **Custom Notes**: `standard_note_id = NULL` with `custom_title` and `custom_text` populated
- **Standard Notes**: `standard_note_id` references standard note, optional custom title/text for overrides
- **Modified Flag**: Set `is_modified=TRUE` when standard note has custom overrides
- **Sort Order**: Manual reordering within note set (use PATCH endpoint to reorder)
- **Usage Count**: Incremented when note is assigned to a sheet, decremented on unassignment

---

### 4. `sheet_note_assignments` - Note-to-Sheet Mapping

Assigns specific notes to specific drawing sheets/layouts with legend sequence.

```sql
CREATE TABLE sheet_note_assignments (
    assignment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_note_id UUID NOT NULL REFERENCES project_sheet_notes(project_note_id) ON DELETE CASCADE,
    drawing_id UUID NOT NULL REFERENCES drawings(drawing_id) ON DELETE CASCADE,
    layout_name VARCHAR(100) DEFAULT 'Model',      -- 'Model', 'Layout1', etc.
    legend_sequence INTEGER NOT NULL,              -- Order in note legend (1, 2, 3...)
    show_in_legend BOOLEAN DEFAULT TRUE,           -- FALSE = hidden note (for reference only)
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(100)
);

CREATE INDEX idx_sheet_note_assignments_note ON sheet_note_assignments(project_note_id);
CREATE INDEX idx_sheet_note_assignments_drawing ON sheet_note_assignments(drawing_id, layout_name);
CREATE INDEX idx_sheet_note_assignments_sequence ON sheet_note_assignments(drawing_id, layout_name, legend_sequence);

-- Prevent duplicate assignments
CREATE UNIQUE INDEX idx_unique_note_assignment ON sheet_note_assignments(project_note_id, drawing_id, layout_name);
```

**Key Points:**
- Links project notes to specific drawing files and layout tabs
- `legend_sequence` controls order in the generated legend (1, 2, 3...)
- `show_in_legend=FALSE` hides notes from legend while maintaining reference
- Unique constraint prevents assigning same note twice to same drawing/layout
- Cascading delete removes assignments when note or drawing is deleted

---

## API Endpoints

### Sheet Note Sets

#### `GET /api/sheet-note-sets?project_id=<uuid>`
Get all note sets for a project.

**Request:**
```http
GET /api/sheet-note-sets?project_id=123e4567-e89b-12d3-a456-426614174000
```

**Response:**
```json
{
  "sets": [
    {
      "set_id": "abc123...",
      "project_id": "123e4567...",
      "set_name": "100% Civil Plans Notes",
      "description": "Note set for 100% submittal",
      "discipline": "Civil",
      "is_active": true,
      "created_at": "2025-01-15T10:00:00Z",
      "note_count": 15
    }
  ]
}
```

#### `POST /api/sheet-note-sets`
Create a new note set.

**Request:**
```json
{
  "project_id": "123e4567-e89b-12d3-a456-426614174000",
  "set_name": "Draft Note Set v1",
  "description": "Initial note collection for schematic design",
  "discipline": "Civil",
  "is_active": false
}
```

**Response:**
```json
{
  "set": {
    "set_id": "new-uuid...",
    "project_id": "123e4567...",
    "set_name": "Draft Note Set v1",
    "description": "Initial note collection for schematic design",
    "discipline": "Civil",
    "is_active": false,
    "created_at": "2025-01-20T14:30:00Z"
  }
}
```

#### `PUT /api/sheet-note-sets/<set_id>`
Update an existing note set.

**Request:**
```json
{
  "set_name": "Final Construction Notes",
  "description": "Updated for final construction documents",
  "is_active": true
}
```

**Response:**
```json
{
  "set": {
    "set_id": "abc123...",
    "set_name": "Final Construction Notes",
    ...
  }
}
```

#### `DELETE /api/sheet-note-sets/<set_id>`
Delete a note set (cascades to all project notes and assignments).

**Request:**
```http
DELETE /api/sheet-note-sets/abc123...
```

**Response:**
```json
{
  "message": "Sheet note set deleted successfully"
}
```

#### `PATCH /api/sheet-note-sets/activate`
Activate a note set (deactivates all others for the project).

**Request:**
```json
{
  "set_id": "abc123...",
  "project_id": "123e4567..."
}
```

**Response:**
```json
{
  "message": "Sheet note set activated successfully"
}
```

---

### Project Sheet Notes

#### `GET /api/project-sheet-notes?set_id=<uuid>`
Get all notes in a note set.

**Response:**
```json
{
  "notes": [
    {
      "project_note_id": "note-uuid...",
      "set_id": "set-uuid...",
      "standard_note_id": 5,
      "display_code": "GN-1",
      "custom_title": null,
      "custom_text": null,
      "is_modified": false,
      "sort_order": 1,
      "usage_count": 3,
      "standard_title": "General Construction Note",
      "standard_text": "All dimensions to be verified in field...",
      "note_category": "General",
      "discipline": "Civil"
    }
  ]
}
```

#### `POST /api/project-sheet-notes`
Create a new project note (custom or from standard).

**Request (Custom Note):**
```json
{
  "set_id": "set-uuid...",
  "standard_note_id": null,
  "display_code": "CN-1",
  "custom_title": "Project-Specific Note",
  "custom_text": "This project requires special coordination with utility company..."
}
```

**Request (Standard Note):**
```json
{
  "set_id": "set-uuid...",
  "standard_note_id": 5,
  "display_code": "GN-1"
}
```

**Response:**
```json
{
  "note": {
    "project_note_id": "new-note-uuid...",
    "set_id": "set-uuid...",
    "standard_note_id": 5,
    "display_code": "GN-1",
    "sort_order": 10,
    "usage_count": 0,
    ...
  }
}
```

#### `PUT /api/project-sheet-notes/<project_note_id>`
Update a project note.

**Request:**
```json
{
  "display_code": "GN-2",
  "custom_title": "Modified Title",
  "custom_text": "Modified text content..."
}
```

#### `DELETE /api/project-sheet-notes/<project_note_id>`
Delete a project note (removes all assignments).

#### `PATCH /api/project-sheet-notes/<project_note_id>/reorder`
Change sort order of a note.

**Request:**
```json
{
  "new_order": 5
}
```

**Response:**
```json
{
  "message": "Note reordered successfully"
}
```

---

### Sheet Note Assignments

#### `GET /api/sheet-note-assignments?drawing_id=<uuid>&layout_name=<string>`
Get all note assignments for a drawing/layout.

**Response:**
```json
{
  "assignments": [
    {
      "assignment_id": "assign-uuid...",
      "project_note_id": "note-uuid...",
      "drawing_id": "drawing-uuid...",
      "layout_name": "Layout1",
      "legend_sequence": 1,
      "display_code": "GN-1",
      "note_title": "General Note Title",
      "note_text": "Note text content..."
    }
  ]
}
```

#### `GET /api/sheet-note-assignments?project_note_id=<uuid>`
Get all assignments for a specific note (shows where it's used).

**Response:**
```json
{
  "assignments": [
    {
      "assignment_id": "assign-uuid...",
      "drawing_id": "drawing-uuid...",
      "layout_name": "Sheet C-1.1",
      "legend_sequence": 3,
      "drawing_name": "Site Plan",
      "drawing_number": "C-1.1",
      "project_name": "Main Street Development"
    }
  ]
}
```

#### `POST /api/sheet-note-assignments`
Assign a note to a drawing/layout.

**Request:**
```json
{
  "project_note_id": "note-uuid...",
  "drawing_id": "drawing-uuid...",
  "layout_name": "Model",
  "legend_sequence": 5,
  "show_in_legend": true,
  "assigned_by": "John Smith"
}
```

**Response:**
```json
{
  "assignment": {
    "assignment_id": "new-assign-uuid...",
    "project_note_id": "note-uuid...",
    "drawing_id": "drawing-uuid...",
    "layout_name": "Model",
    "legend_sequence": 5,
    ...
  }
}
```

**Business Logic:** Increments `usage_count` in `project_sheet_notes` table.

#### `DELETE /api/sheet-note-assignments/<assignment_id>`
Remove note assignment from drawing/layout.

**Response:**
```json
{
  "message": "Assignment deleted successfully"
}
```

**Business Logic:** Decrements `usage_count` in `project_sheet_notes` table.

---

### Note Legend Generation

#### `GET /api/sheet-note-legend?drawing_id=<uuid>&layout_name=<string>`
Generate formatted note legend for a drawing/layout.

**Request:**
```http
GET /api/sheet-note-legend?drawing_id=abc123...&layout_name=Sheet%20C-1.1
```

**Response:**
```json
{
  "drawing_id": "abc123...",
  "layout_name": "Sheet C-1.1",
  "legend": [
    {
      "legend_sequence": 1,
      "display_code": "GN-1",
      "note_title": "General Construction Note",
      "note_text": "All dimensions to be verified in field prior to construction.",
      "standard_note_id": 5,
      "is_modified": false
    },
    {
      "legend_sequence": 2,
      "display_code": "GRAD-1",
      "note_title": "Grading Note",
      "note_text": "All grading to conform to approved drainage plan.",
      "standard_note_id": null,
      "is_modified": false
    }
  ],
  "total_notes": 2
}
```

**Usage:** This endpoint returns formatted notes ready to be inserted into CAD title blocks or note areas.

---

## Business Logic & Validation Rules

### Note Set Activation
- Only ONE note set can be `is_active=TRUE` per project
- When activating a set, all other sets for that project must be set to `is_active=FALSE`
- Implemented via `PATCH /api/sheet-note-sets/activate` endpoint

### Custom vs Standard Notes
- **Custom Note**: `standard_note_id = NULL`, must provide `custom_title` and `custom_text`
- **Standard Note**: `standard_note_id` required, custom title/text optional
- **Modified Note**: If standard note has custom title/text, set `is_modified=TRUE`

### Note Reordering
- `sort_order` controls manual ordering within a note set
- Use PATCH endpoint to update sort order
- When creating new notes, auto-increment to next available sort_order

### Usage Count Tracking
- Increment `usage_count` when creating assignment
- Decrement `usage_count` when deleting assignment
- Use for analytics (which notes are most popular, which are unused)

### Legend Sequence
- Controls display order in generated legends (1, 2, 3...)
- Must be unique per drawing/layout
- When adding assignment, find next available sequence or allow manual specification

### Cascading Deletes
- Delete project → deletes note sets → deletes project notes → deletes assignments
- Delete note set → deletes project notes → deletes assignments
- Delete project note → deletes assignments
- Delete drawing → deletes assignments
- Delete standard note → sets `standard_note_id=NULL` in project notes (soft delete)

---

## Frontend Component Structure

### Technology
- **React 18** with hooks (`useState`, `useEffect`)
- **Pure JavaScript** using `React.createElement()` (no JSX/Babel)
- **Three-panel layout**: Standard Notes Library | Project Notes Editor | Sheet Assignments
- **Mission Control theme**: Dark blues, cyan borders, gold accents

### Component Hierarchy

```
SheetNoteApp (root component)
├── TopBar
│   ├── Project Selector (dropdown)
│   ├── Note Set Selector (dropdown)
│   ├── Create Note Set Button
│   └── Stats Dashboard (badges: total sets, notes, assignments)
├── ThreePanelLayout
│   ├── LeftPanel: Standard Notes Library
│   │   ├── Search/Filter (by category, discipline, text)
│   │   └── Note List (10 sample standard notes)
│   ├── CenterPanel: Project Notes Editor
│   │   ├── Add Note Button
│   │   ├── Note List (with edit/delete buttons)
│   │   └── Note Details (display code, title, text, badges)
│   └── RightPanel: Sheet Assignments
│       ├── Assignment List (grouped by drawing/layout)
│       └── Usage Stats (shows which notes are used where)
```

### Key State Variables

```javascript
const [projects, setProjects] = useState([]);
const [selectedProject, setSelectedProject] = useState('');
const [noteSets, setNoteSets] = useState([]);
const [selectedNoteSet, setSelectedNoteSet] = useState('');
const [projectNotes, setProjectNotes] = useState([]);
const [assignments, setAssignments] = useState([]);
const [standardNotes] = useState([/* 10 sample standard notes */]);
const [stats, setStats] = useState({ totalSets: 0, totalNotes: 0, totalAssignments: 0 });
const [loading, setLoading] = useState(true);
```

### Key Functions

```javascript
// Data loading
async function loadProjects() { /* Fetch from /api/projects */ }
async function loadNoteSets(projectId) { /* Fetch from /api/sheet-note-sets */ }
async function loadProjectNotes(setId) { /* Fetch from /api/project-sheet-notes */ }
async function loadAssignments(projectNoteId) { /* Fetch from /api/sheet-note-assignments */ }

// CRUD operations
async function createNoteSet(name, description) { /* POST to /api/sheet-note-sets */ }
async function createProjectNote(data) { /* POST to /api/project-sheet-notes */ }
async function updateProjectNote(noteId, data) { /* PUT to /api/project-sheet-notes/:id */ }
async function deleteProjectNote(noteId) { /* DELETE to /api/project-sheet-notes/:id */ }

// UI helpers
function calculateStats() { /* Count total sets, notes, assignments */ }
function renderNoteItem(note) { /* Render individual note card */ }
function renderBadge(type) { /* Render standard/custom/modified badge */ }
```

### User Workflows

1. **Create Note Set:**
   - Select project → Click "Create Note Set" → Enter name/description → Save

2. **Add Custom Note:**
   - Select project and note set → Click "Add Note" → Enter display code, title, text → Save

3. **Add Standard Note:**
   - Browse standard notes library → Click standard note → Automatically added to project note set

4. **Assign Note to Sheet:**
   - Select note → Select drawing/layout → Assign (with auto-sequencing)

5. **View Note Usage:**
   - Click note → See all drawings/layouts using that note in right panel

---

## Integration Tips for FastAPI

### Pydantic Models

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class StandardNoteBase(BaseModel):
    note_category: Optional[str] = None
    note_title: str
    note_text: str
    discipline: Optional[str] = None
    is_active: bool = True

class StandardNote(StandardNoteBase):
    note_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class NoteSetBase(BaseModel):
    project_id: UUID
    set_name: str
    description: Optional[str] = None
    discipline: Optional[str] = None
    is_active: bool = False

class NoteSet(NoteSetBase):
    set_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ProjectNoteBase(BaseModel):
    set_id: UUID
    standard_note_id: Optional[int] = None
    display_code: str
    custom_title: Optional[str] = None
    custom_text: Optional[str] = None

class ProjectNote(ProjectNoteBase):
    project_note_id: UUID
    is_modified: bool = False
    sort_order: int
    usage_count: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True

class NoteAssignmentBase(BaseModel):
    project_note_id: UUID
    drawing_id: UUID
    layout_name: str = "Model"
    legend_sequence: int
    show_in_legend: bool = True
    assigned_by: Optional[str] = None

class NoteAssignment(NoteAssignmentBase):
    assignment_id: UUID
    assigned_at: datetime
    
    class Config:
        from_attributes = True
```

### SQLAlchemy Models

```python
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, ForeignKey, UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

class StandardNote(Base):
    __tablename__ = "standard_notes"
    
    note_id = Column(Integer, primary_key=True, autoincrement=True)
    note_category = Column(String(100))
    note_title = Column(String(255), nullable=False)
    note_text = Column(Text, nullable=False)
    discipline = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class SheetNoteSet(Base):
    __tablename__ = "sheet_note_sets"
    
    set_id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    project_id = Column(UUID, ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    set_name = Column(String(255), nullable=False)
    description = Column(Text)
    discipline = Column(String(50))
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    project = relationship("Project", back_populates="note_sets")
    project_notes = relationship("ProjectSheetNote", back_populates="note_set", cascade="all, delete-orphan")

class ProjectSheetNote(Base):
    __tablename__ = "project_sheet_notes"
    
    project_note_id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    set_id = Column(UUID, ForeignKey("sheet_note_sets.set_id", ondelete="CASCADE"), nullable=False)
    standard_note_id = Column(Integer, ForeignKey("standard_notes.note_id", ondelete="SET NULL"))
    display_code = Column(String(20))
    custom_title = Column(String(255))
    custom_text = Column(Text)
    is_modified = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    note_set = relationship("SheetNoteSet", back_populates="project_notes")
    standard_note = relationship("StandardNote")
    assignments = relationship("SheetNoteAssignment", back_populates="project_note", cascade="all, delete-orphan")

class SheetNoteAssignment(Base):
    __tablename__ = "sheet_note_assignments"
    
    assignment_id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    project_note_id = Column(UUID, ForeignKey("project_sheet_notes.project_note_id", ondelete="CASCADE"), nullable=False)
    drawing_id = Column(UUID, ForeignKey("drawings.drawing_id", ondelete="CASCADE"), nullable=False)
    layout_name = Column(String(100), default="Model")
    legend_sequence = Column(Integer, nullable=False)
    show_in_legend = Column(Boolean, default=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    assigned_by = Column(String(100))
    
    project_note = relationship("ProjectSheetNote", back_populates="assignments")
    drawing = relationship("Drawing")
```

### FastAPI Router Example

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(prefix="/api/sheet-note-sets", tags=["sheet_notes"])

@router.get("/", response_model=List[NoteSet])
def get_note_sets(project_id: UUID, db: Session = Depends(get_db)):
    """Get all note sets for a project"""
    sets = db.query(SheetNoteSet).filter(SheetNoteSet.project_id == project_id).all()
    return sets

@router.post("/", response_model=NoteSet, status_code=201)
def create_note_set(note_set: NoteSetBase, db: Session = Depends(get_db)):
    """Create new note set"""
    db_set = SheetNoteSet(**note_set.dict())
    db.add(db_set)
    db.commit()
    db.refresh(db_set)
    return db_set

@router.patch("/activate")
def activate_note_set(set_id: UUID, project_id: UUID, db: Session = Depends(get_db)):
    """Activate a note set (deactivates all others for project)"""
    # Deactivate all sets for this project
    db.query(SheetNoteSet).filter(
        SheetNoteSet.project_id == project_id
    ).update({"is_active": False})
    
    # Activate the specified set
    db.query(SheetNoteSet).filter(
        SheetNoteSet.set_id == set_id
    ).update({"is_active": True})
    
    db.commit()
    return {"message": "Sheet note set activated successfully"}
```

---

## Testing Checklist

- [ ] Create standard notes library (10+ sample notes)
- [ ] Create project and note set
- [ ] Add custom note to set
- [ ] Add standard note to set
- [ ] Override standard note title/text (verify `is_modified=TRUE`)
- [ ] Reorder notes in set (verify `sort_order` updates)
- [ ] Activate note set (verify only one active per project)
- [ ] Assign note to drawing/layout (verify `usage_count` increments)
- [ ] Remove assignment (verify `usage_count` decrements)
- [ ] Generate legend (verify proper formatting and sequence)
- [ ] Delete note (verify assignments cascade delete)
- [ ] Delete note set (verify notes and assignments cascade delete)
- [ ] Delete project (verify all related data cascades)

---

## Migration Checklist

- [ ] Create database tables with proper foreign keys and indexes
- [ ] Seed `standard_notes` table with company-approved notes
- [ ] Implement Pydantic models for request/response validation
- [ ] Create SQLAlchemy ORM models with proper relationships
- [ ] Implement API routes for all CRUD operations
- [ ] Add business logic for activation, usage counting, and cascading
- [ ] Build React frontend component (or adapt existing one)
- [ ] Test all user workflows end-to-end
- [ ] Add error handling and validation
- [ ] Document API in Swagger/OpenAPI
