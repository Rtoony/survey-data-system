# Sheet Set Manager - Migration Documentation

## Overview

The Sheet Set Manager is a comprehensive system for organizing construction document sheets into deliverable packages, tracking sheet assignments to CAD drawings, managing sheet revisions, and generating sheet indexes. It provides full lifecycle management for construction document production from design through construction.

**Key Value:** Organizes sheets into phased deliverables (schematic design, permitting, construction docs), tracks which CAD files produce which sheets, manages revision history, enables sheet renumbering, and generates professional sheet indexes automatically.

## Use Cases

1. **Sheet Set Organization**: Group sheets into deliverable packages ("100% Civil Plans", "Addendum #2")
2. **Sheet Management**: Create and organize individual sheets with codes (C-1.1, S-3.5), titles, categories
3. **Drawing Assignments**: Link sheets to specific DXF drawing files and layout tabs
4. **Revision Tracking**: Maintain complete history of sheet revisions with dates and descriptions
5. **Sheet Relationships**: Track cross-references between sheets (detail references, continuations)
6. **Sheet Indexing**: Auto-generate professional sheet indexes for title blocks

---

## Database Schema

### 1. `project_details` - Extended Project Metadata

Extends basic project information with detailed data needed for construction documents.

```sql
CREATE TABLE project_details (
    project_id UUID PRIMARY KEY REFERENCES projects(project_id) ON DELETE CASCADE,
    project_address VARCHAR(500),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    county VARCHAR(100),
    engineer_of_record VARCHAR(255),
    engineer_license VARCHAR(100),
    jurisdiction VARCHAR(200),                    -- Building department/agency
    permit_number VARCHAR(100),
    parcel_number VARCHAR(100),
    project_area_acres DECIMAL(10,2),
    project_description TEXT,
    owner_name VARCHAR(255),
    owner_contact TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Key Points:**
- One-to-one relationship with `projects` table
- Stores metadata that appears in title blocks and cover sheets
- Essential for permitting and regulatory compliance

---

### 2. `sheet_category_standards` - Standard Sheet Categories

Defines industry-standard sheet categories with hierarchy.

```sql
CREATE TABLE sheet_category_standards (
    category_code VARCHAR(20) PRIMARY KEY,         -- 'COVER', 'DEMO', 'GRAD', 'UTIL', etc.
    category_name VARCHAR(100) NOT NULL,           -- 'Cover Sheets', 'Demolition Plans'
    hierarchy_order INTEGER,                       -- Display order (10, 20, 30...)
    description TEXT,
    discipline VARCHAR(50),                        -- 'Civil', 'Structural', 'Architectural'
    is_active BOOLEAN DEFAULT TRUE
);

-- Sample categories
INSERT INTO sheet_category_standards VALUES
('COVER', 'Cover Sheets', 10, 'Project title sheets and general information', 'General', true),
('DEMO', 'Demolition Plans', 20, 'Existing conditions and demolition', 'Civil', true),
('GRAD', 'Grading Plans', 30, 'Site grading and earthwork', 'Civil', true),
('UTIL', 'Utility Plans', 40, 'Water, sewer, storm drainage utilities', 'Civil', true),
('PAVE', 'Paving Plans', 50, 'Street paving and striping', 'Civil', true),
('LAND', 'Landscape Plans', 60, 'Landscape and irrigation', 'Landscape', true),
('DETAIL', 'Details', 100, 'Construction details', 'Civil', true),
('PROF', 'Profiles', 110, 'Utility and street profiles', 'Civil', true);
```

**Key Points:**
- Standardizes sheet categories across all projects
- `hierarchy_order` controls display sequence in sheet sets
- Categories organize sheets by type/discipline

---

### 3. `sheet_sets` - Deliverable Packages

Collections of sheets that get delivered together as packages.

```sql
CREATE TABLE sheet_sets (
    set_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    set_name VARCHAR(255) NOT NULL,                -- '100% Civil Plans', 'Addendum #2'
    description TEXT,
    phase VARCHAR(100),                            -- 'Schematic Design', 'Design Development', 'Construction Documents'
    discipline VARCHAR(50),                        -- 'Civil', 'Structural', 'Architectural'
    status VARCHAR(50) DEFAULT 'Draft',            -- 'Draft', 'In Review', 'Issued for Permit', 'Issued for Construction'
    issued_date DATE,
    issued_to VARCHAR(255),                        -- Building department, contractor, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sheet_sets_project ON sheet_sets(project_id);
CREATE INDEX idx_sheet_sets_status ON sheet_sets(status);
```

**Key Points:**
- Each project can have multiple sheet sets (for different phases/submittals)
- `phase` tracks design phase (SD, DD, CD)
- `status` tracks submittal status (Draft, In Review, Issued)
- `issued_date` records when set was delivered

---

### 4. `sheets` - Individual Construction Document Sheets

Individual sheets within sheet sets.

```sql
CREATE TABLE sheets (
    sheet_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    set_id UUID NOT NULL REFERENCES sheet_sets(set_id) ON DELETE CASCADE,
    sheet_number INTEGER,                          -- Auto-assigned sequential number within set
    sheet_code VARCHAR(50),                        -- 'C-1.1', 'S-3.5', 'A-101'
    sheet_title VARCHAR(255) NOT NULL,             -- 'Site Plan', 'Foundation Details'
    discipline_code VARCHAR(20),                   -- 'C' (Civil), 'S' (Structural), etc.
    sheet_type VARCHAR(50),                        -- 'Plan', 'Detail', 'Section', 'Profile'
    sheet_category TEXT,                           -- References category_code (stored as TEXT in Supabase)
    sheet_hierarchy_number INTEGER DEFAULT 50,     -- Manual ordering within set
    scale VARCHAR(50),                             -- '1"=20'', '1/4"=1'-0"', 'AS NOTED'
    sheet_size VARCHAR(20) DEFAULT '24x36',        -- '24x36', '11x17', 'A1', 'A3'
    template_id INTEGER,                           -- Links to sheet templates (if available)
    revision_number INTEGER DEFAULT 0,             -- Current revision (0, 1, 2, or A, B, C)
    revision_date DATE,
    notes TEXT,
    tags TEXT[],                                   -- Array for categorization/searching
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sheets_set ON sheets(set_id);
CREATE INDEX idx_sheets_category ON sheets(sheet_category);
CREATE INDEX idx_sheets_code ON sheets(sheet_code);
CREATE UNIQUE INDEX idx_sheets_unique_code ON sheets(set_id, sheet_code);
```

**Key Points:**
- **IMPORTANT**: `sheet_category` is TEXT field, not foreign key (Supabase schema)
- **IMPORTANT**: `template_id` is INTEGER, not UUID (Supabase schema)
- `sheet_number` is auto-assigned sequentially when sheets are created/renumbered
- `sheet_code` follows discipline conventions (C-1.1, S-3.5, A-101)
- `sheet_hierarchy_number` allows manual ordering (independent of sheet_number)
- Unique constraint prevents duplicate sheet codes within a set

---

### 5. `sheet_drawing_assignments` - Sheet-to-Drawing Linkage

Links sheets to their corresponding CAD drawing files and layout tabs.

```sql
CREATE TABLE sheet_drawing_assignments (
    assignment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sheet_id UUID NOT NULL REFERENCES sheets(sheet_id) ON DELETE CASCADE,
    drawing_id UUID REFERENCES drawings(drawing_id) ON DELETE CASCADE,
    layout_name VARCHAR(100),                      -- 'Model', 'Layout1', 'Sheet C-1.1'
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(100),
    notes TEXT
);

CREATE INDEX idx_sheet_drawing_assignments_sheet ON sheet_drawing_assignments(sheet_id);
CREATE INDEX idx_sheet_drawing_assignments_drawing ON sheet_drawing_assignments(drawing_id);
CREATE UNIQUE INDEX idx_unique_sheet_assignment ON sheet_drawing_assignments(sheet_id, drawing_id, layout_name);
```

**Key Points:**
- Links construction document sheets to DXF drawing files
- `layout_name` specifies which layout tab in the DXF contains the sheet
- Enables automated PDF/DWG export (pull specific layout from specific drawing)
- Unique constraint prevents duplicate assignments
- Used to show "assigned" vs "unassigned" badges in UI

---

### 6. `sheet_revisions` - Revision History Tracking

Complete audit trail of sheet revisions.

```sql
CREATE TABLE sheet_revisions (
    revision_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sheet_id UUID NOT NULL REFERENCES sheets(sheet_id) ON DELETE CASCADE,
    revision_number VARCHAR(20) NOT NULL,          -- '0', '1', 'A', 'B', 'ASI-1'
    revision_date DATE NOT NULL,
    description TEXT,                              -- What changed in this revision
    revised_by VARCHAR(100),                       -- Who made the revision
    reference_number VARCHAR(100),                 -- RFI #, change order #, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sheet_revisions_sheet ON sheet_revisions(sheet_id);
CREATE INDEX idx_sheet_revisions_date ON sheet_revisions(revision_date DESC);
```

**Key Points:**
- Tracks complete revision history for each sheet
- `revision_number` can be numeric (0, 1, 2) or alphabetic (A, B, C)
- `description` explains what changed
- `reference_number` links to RFIs, change orders, addenda
- Critical for construction administration and dispute resolution

---

### 7. `sheet_relationships` - Cross-References Between Sheets

Defines relationships and cross-references between sheets.

```sql
CREATE TABLE sheet_relationships (
    relationship_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_sheet_id UUID NOT NULL REFERENCES sheets(sheet_id) ON DELETE CASCADE,
    target_sheet_id UUID NOT NULL REFERENCES sheets(sheet_id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL,        -- 'references', 'detail_of', 'continued_from', 'see_also'
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sheet_relationships_source ON sheet_relationships(source_sheet_id);
CREATE INDEX idx_sheet_relationships_target ON sheet_relationships(target_sheet_id);
```

**Key Points:**
- Tracks cross-references between sheets
- Common relationship types:
  - `references`: General reference ("See Sheet C-2.3")
  - `detail_of`: Detail sheet references plan sheet
  - `continued_from`: Multi-sheet continuations
  - `see_also`: Related information
- Helps ensure updated sheets reference current information

---

## API Endpoints

### Project Details

#### `GET /api/project-details?project_id=<uuid>`
Get extended project details.

**Response:**
```json
{
  "project_details": {
    "project_id": "123e4567...",
    "project_address": "123 Main Street",
    "city": "San Jose",
    "state": "CA",
    "zip_code": "95113",
    "engineer_of_record": "John Smith, PE",
    "engineer_license": "C12345",
    "jurisdiction": "City of San Jose Building Department",
    "permit_number": "PERMIT-2025-001",
    ...
  }
}
```

#### `POST /api/project-details`
Create project details.

#### `PUT /api/project-details/<project_id>`
Update project details.

---

### Sheet Sets

#### `GET /api/sheet-sets?project_id=<uuid>`
Get all sheet sets for a project.

**Response:**
```json
{
  "sheet_sets": [
    {
      "set_id": "set-uuid...",
      "project_id": "project-uuid...",
      "set_name": "100% Civil Plans",
      "description": "Complete set for permit submittal",
      "phase": "Construction Documents",
      "discipline": "Civil",
      "status": "Issued for Permit",
      "issued_date": "2025-01-15",
      "issued_to": "City Building Department",
      "sheet_count": 12,
      "project_name": "Main Street Development",
      "project_number": "2025-001"
    }
  ]
}
```

#### `POST /api/sheet-sets`
Create a new sheet set.

**Request:**
```json
{
  "project_id": "project-uuid...",
  "set_name": "50% Design Development",
  "description": "Preliminary design submittal",
  "phase": "Design Development",
  "discipline": "Civil",
  "status": "Draft"
}
```

#### `PUT /api/sheet-sets/<set_id>`
Update sheet set.

#### `DELETE /api/sheet-sets/<set_id>`
Delete sheet set (cascades to all sheets, assignments, revisions).

---

### Sheets

#### `GET /api/sheets?set_id=<uuid>`
Get all sheets in a set.

**Response:**
```json
{
  "sheets": [
    {
      "sheet_id": "sheet-uuid...",
      "set_id": "set-uuid...",
      "sheet_number": 1,
      "sheet_code": "C-1.1",
      "sheet_title": "Site Plan",
      "discipline_code": "C",
      "sheet_type": "Plan",
      "sheet_category": "GRAD",
      "sheet_hierarchy_number": 30,
      "scale": "1\"=20'",
      "sheet_size": "24x36",
      "revision_number": 2,
      "revision_date": "2025-01-20",
      "assignment_status": "assigned",
      "drawing_id": "drawing-uuid...",
      "layout_name": "Sheet C-1.1"
    }
  ]
}
```

#### `POST /api/sheets`
Create a new sheet.

**Request:**
```json
{
  "set_id": "set-uuid...",
  "sheet_code": "C-1.1",
  "sheet_title": "Site Plan",
  "discipline_code": "C",
  "sheet_type": "Plan",
  "sheet_category": "GRAD",
  "sheet_hierarchy_number": 30,
  "scale": "1\"=20'",
  "sheet_size": "24x36",
  "revision_number": 0
}
```

**Response:**
```json
{
  "sheet": {
    "sheet_id": "new-sheet-uuid...",
    "sheet_number": 3,
    ...
  }
}
```

**Business Logic:** Automatically calls `renumber_sheets(set_id)` to assign sequential `sheet_number`.

#### `PUT /api/sheets/<sheet_id>`
Update sheet.

**Request:**
```json
{
  "sheet_code": "C-1.2",
  "sheet_title": "Updated Site Plan Title",
  "scale": "1\"=30'"
}
```

#### `DELETE /api/sheets/<sheet_id>`
Delete sheet (cascades to assignments and revisions).

#### `POST /api/sheets/renumber/<set_id>`
Renumber all sheets in a set based on hierarchy.

**Response:**
```json
{
  "message": "Sheets renumbered successfully",
  "updated_count": 12
}
```

**Business Logic:**
- Orders sheets by `sheet_hierarchy_number`, then `sheet_code`
- Assigns sequential `sheet_number` (1, 2, 3...)
- Updates all sheets in a single transaction

---

### Sheet Drawing Assignments

#### `GET /api/sheet-drawing-assignments?sheet_id=<uuid>`
Get drawing assignments for a sheet.

**Response:**
```json
{
  "assignments": [
    {
      "assignment_id": "assign-uuid...",
      "sheet_id": "sheet-uuid...",
      "drawing_id": "drawing-uuid...",
      "layout_name": "Sheet C-1.1",
      "drawing_name": "SitePlan_Civil.dwg",
      "assigned_at": "2025-01-15T10:30:00Z",
      "assigned_by": "John Smith"
    }
  ]
}
```

#### `POST /api/sheet-drawing-assignments`
Assign drawing to sheet.

**Request:**
```json
{
  "sheet_id": "sheet-uuid...",
  "drawing_id": "drawing-uuid...",
  "layout_name": "Sheet C-1.1",
  "assigned_by": "John Smith",
  "notes": "Main site plan layout"
}
```

#### `DELETE /api/sheet-drawing-assignments/<assignment_id>`
Remove drawing assignment.

---

### Sheet Revisions

#### `GET /api/sheet-revisions?sheet_id=<uuid>`
Get revision history for a sheet.

**Response:**
```json
{
  "revisions": [
    {
      "revision_id": "rev-uuid...",
      "sheet_id": "sheet-uuid...",
      "revision_number": "A",
      "revision_date": "2025-01-20",
      "description": "Added fire hydrant details per building department comments",
      "revised_by": "John Smith",
      "reference_number": "RFI-005"
    }
  ]
}
```

#### `POST /api/sheet-revisions`
Add a revision to a sheet.

**Request:**
```json
{
  "sheet_id": "sheet-uuid...",
  "revision_number": "B",
  "revision_date": "2025-02-01",
  "description": "Updated grading contours per geotechnical report",
  "revised_by": "Jane Doe",
  "reference_number": "GEO-2025-001"
}
```

---

### Sheet Relationships

#### `GET /api/sheet-relationships?sheet_id=<uuid>`
Get relationships for a sheet.

**Response:**
```json
{
  "relationships": [
    {
      "relationship_id": "rel-uuid...",
      "source_sheet_id": "sheet-uuid...",
      "target_sheet_id": "target-uuid...",
      "relationship_type": "detail_of",
      "source_sheet_code": "D-3.1",
      "source_sheet_title": "Foundation Details",
      "target_sheet_code": "S-2.1",
      "target_sheet_title": "Foundation Plan"
    }
  ]
}
```

#### `POST /api/sheet-relationships`
Create relationship between sheets.

**Request:**
```json
{
  "source_sheet_id": "detail-sheet-uuid...",
  "target_sheet_id": "plan-sheet-uuid...",
  "relationship_type": "detail_of",
  "notes": "Detail 3/D-3.1 shows section through typical foundation"
}
```

#### `DELETE /api/sheet-relationships/<relationship_id>`
Delete relationship.

---

### Sheet Index Generation

#### `GET /api/sheet-index/<set_id>`
Generate formatted sheet index for a set.

**Response:**
```json
{
  "set_id": "set-uuid...",
  "sheets": [
    {
      "sheet_number": 1,
      "sheet_code": "C-0.0",
      "sheet_title": "Cover Sheet",
      "scale": "N/A",
      "revision_number": 0,
      "revision_date": null
    },
    {
      "sheet_number": 2,
      "sheet_code": "C-1.1",
      "sheet_title": "Site Plan",
      "scale": "1\"=20'",
      "revision_number": 2,
      "revision_date": "2025-01-20"
    }
  ],
  "total_sheets": 12
}
```

**Usage:** This endpoint returns formatted data ready to be inserted into cover sheets and title blocks.

---

## Business Logic & Validation Rules

### Sheet Numbering
- `sheet_number` is auto-assigned sequentially (1, 2, 3...)
- Renumbering triggered automatically after sheet creation
- Renumbering can be manually triggered via `POST /api/sheets/renumber/:set_id`
- Ordering based on `sheet_hierarchy_number` then `sheet_code`

### Sheet Codes
- Must be unique within a sheet set
- Follow discipline conventions: C-1.1 (Civil), S-3.5 (Structural), A-101 (Architectural)
- Unique constraint enforced at database level

### Assignment Status
- Sheets show "assigned" if they have a drawing assignment
- Sheets show "unassigned" if no drawing is linked
- Calculated via LEFT JOIN in GET sheets query

### Category Standards
- `sheet_category_standards` defines available categories
- However, `sheets.sheet_category` is TEXT field (not FK) in current Supabase schema
- Future enhancement: Convert to foreign key relationship

### Cascading Deletes
- Delete sheet set → deletes all sheets → deletes all assignments and revisions
- Delete sheet → deletes all assignments and revisions
- Delete drawing → deletes all sheet assignments

### Revision Tracking
- Each revision is a separate record in `sheet_revisions`
- `sheets.revision_number` tracks current revision
- Revision history provides complete audit trail

---

## Frontend Component Structure

### Technology
- **React 18** with hooks (`useState`, `useEffect`)
- **Pure JavaScript** using `React.createElement()` (no JSX/Babel)
- **Two-panel layout**: Sheet Sets List | Sheets Table
- **Mission Control theme**: Dark blues, cyan borders, gold accents

### Component Hierarchy

```
SheetSetApp (root component)
├── TopBar
│   ├── Project Selector (dropdown)
│   └── Stats Badges (total sets, total sheets)
├── TwoPanelLayout
│   ├── LeftPanel: Sheet Sets
│   │   ├── Create Set Button
│   │   ├── Set List (with sheet count badges)
│   │   └── Set Actions (Delete button)
│   └── RightPanel: Sheets Table
│       ├── Add Sheet Button
│       ├── Sheet Table (code, title, category, status badges, actions)
│       └── Sheet Actions (Edit, Delete buttons)
```

### Key State Variables

```javascript
const [projects, setProjects] = useState([]);
const [selectedProject, setSelectedProject] = useState('');
const [sheetSets, setSheetSets] = useState([]);
const [selectedSetId, setSelectedSetId] = useState('');
const [sheets, setSheets] = useState([]);
const [stats, setStats] = useState({ totalSets: 0, totalSheets: 0 });
const [loading, setLoading] = useState(true);
```

### Key Functions

```javascript
// Data loading
async function loadProjects() { /* Fetch from /api/projects */ }
async function loadSheetSets(projectId) { /* Fetch from /api/sheet-sets */ }
async function loadSheets(setId) { /* Fetch from /api/sheets */ }

// CRUD operations
async function createSheetSet(name) { /* POST to /api/sheet-sets */ }
async function deleteSet(setId) { /* DELETE to /api/sheet-sets/:id */ }
async function createSheet(code, title) { /* POST to /api/sheets */ }
async function editSheet(sheetId, data) { /* PUT to /api/sheets/:id */ }
async function deleteSheet(sheetId) { /* DELETE to /api/sheets/:id */ }

// UI helpers
function calculateStats() { /* Count total sets and sheets */ }
function renderSetItem(set) { /* Render sheet set card with badges */ }
function renderSheetRow(sheet) { /* Render sheet table row with actions */ }
```

### User Workflows

1. **Create Sheet Set:**
   - Select project → Click "Create Set" → Enter name → Save

2. **Create Sheet:**
   - Select project and sheet set → Click "Add Sheet" → Enter code and title → Save

3. **Edit Sheet:**
   - Click edit button → Update code/title → Save

4. **Delete Sheet:**
   - Click delete button → Confirm → Sheet removed

5. **Delete Sheet Set:**
   - Click delete button on set card → Confirm → Set and all sheets removed

---

## Integration Tips for FastAPI

### Pydantic Models

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID

class ProjectDetailsBase(BaseModel):
    project_id: UUID
    project_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    engineer_of_record: Optional[str] = None
    jurisdiction: Optional[str] = None

class ProjectDetails(ProjectDetailsBase):
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SheetSetBase(BaseModel):
    project_id: UUID
    set_name: str
    description: Optional[str] = None
    phase: Optional[str] = None
    discipline: Optional[str] = None
    status: str = "Draft"
    issued_date: Optional[date] = None

class SheetSet(SheetSetBase):
    set_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SheetBase(BaseModel):
    set_id: UUID
    sheet_code: str
    sheet_title: str
    discipline_code: Optional[str] = None
    sheet_type: Optional[str] = None
    sheet_category: Optional[str] = None  # TEXT field, not FK
    sheet_hierarchy_number: int = 50
    scale: Optional[str] = None
    sheet_size: str = "24x36"
    template_id: Optional[int] = None     # INTEGER, not UUID
    revision_number: int = 0

class Sheet(SheetBase):
    sheet_id: UUID
    sheet_number: Optional[int] = None
    revision_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SheetAssignmentBase(BaseModel):
    sheet_id: UUID
    drawing_id: Optional[UUID] = None
    layout_name: Optional[str] = None
    assigned_by: Optional[str] = None

class SheetAssignment(SheetAssignmentBase):
    assignment_id: UUID
    assigned_at: datetime
    
    class Config:
        from_attributes = True

class SheetRevisionBase(BaseModel):
    sheet_id: UUID
    revision_number: str
    revision_date: date
    description: Optional[str] = None
    revised_by: Optional[str] = None
    reference_number: Optional[str] = None

class SheetRevision(SheetRevisionBase):
    revision_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True
```

### SQLAlchemy Models

```python
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, Date, ForeignKey, UUID, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

class ProjectDetails(Base):
    __tablename__ = "project_details"
    
    project_id = Column(UUID, ForeignKey("projects.project_id", ondelete="CASCADE"), primary_key=True)
    project_address = Column(String(500))
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(20))
    engineer_of_record = Column(String(255))
    jurisdiction = Column(String(200))
    permit_number = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    project = relationship("Project", back_populates="details")

class SheetCategoryStandard(Base):
    __tablename__ = "sheet_category_standards"
    
    category_code = Column(String(20), primary_key=True)
    category_name = Column(String(100), nullable=False)
    hierarchy_order = Column(Integer)
    description = Column(Text)
    discipline = Column(String(50))
    is_active = Column(Boolean, default=True)

class SheetSet(Base):
    __tablename__ = "sheet_sets"
    
    set_id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    project_id = Column(UUID, ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    set_name = Column(String(255), nullable=False)
    description = Column(Text)
    phase = Column(String(100))
    discipline = Column(String(50))
    status = Column(String(50), default="Draft")
    issued_date = Column(Date)
    issued_to = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    project = relationship("Project", back_populates="sheet_sets")
    sheets = relationship("Sheet", back_populates="sheet_set", cascade="all, delete-orphan")

class Sheet(Base):
    __tablename__ = "sheets"
    
    sheet_id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    set_id = Column(UUID, ForeignKey("sheet_sets.set_id", ondelete="CASCADE"), nullable=False)
    sheet_number = Column(Integer)
    sheet_code = Column(String(50))
    sheet_title = Column(String(255), nullable=False)
    discipline_code = Column(String(20))
    sheet_type = Column(String(50))
    sheet_category = Column(Text)  # TEXT field, not FK (Supabase schema)
    sheet_hierarchy_number = Column(Integer, default=50)
    scale = Column(String(50))
    sheet_size = Column(String(20), default="24x36")
    template_id = Column(Integer)  # INTEGER, not UUID (Supabase schema)
    revision_number = Column(Integer, default=0)
    revision_date = Column(Date)
    notes = Column(Text)
    tags = Column(ARRAY(Text))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    sheet_set = relationship("SheetSet", back_populates="sheets")
    assignments = relationship("SheetDrawingAssignment", back_populates="sheet", cascade="all, delete-orphan")
    revisions = relationship("SheetRevision", back_populates="sheet", cascade="all, delete-orphan")

class SheetDrawingAssignment(Base):
    __tablename__ = "sheet_drawing_assignments"
    
    assignment_id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    sheet_id = Column(UUID, ForeignKey("sheets.sheet_id", ondelete="CASCADE"), nullable=False)
    drawing_id = Column(UUID, ForeignKey("drawings.drawing_id", ondelete="CASCADE"))
    layout_name = Column(String(100))
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    assigned_by = Column(String(100))
    notes = Column(Text)
    
    sheet = relationship("Sheet", back_populates="assignments")
    drawing = relationship("Drawing")

class SheetRevision(Base):
    __tablename__ = "sheet_revisions"
    
    revision_id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    sheet_id = Column(UUID, ForeignKey("sheets.sheet_id", ondelete="CASCADE"), nullable=False)
    revision_number = Column(String(20), nullable=False)
    revision_date = Column(Date, nullable=False)
    description = Column(Text)
    revised_by = Column(String(100))
    reference_number = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    sheet = relationship("Sheet", back_populates="revisions")

class SheetRelationship(Base):
    __tablename__ = "sheet_relationships"
    
    relationship_id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    source_sheet_id = Column(UUID, ForeignKey("sheets.sheet_id", ondelete="CASCADE"), nullable=False)
    target_sheet_id = Column(UUID, ForeignKey("sheets.sheet_id", ondelete="CASCADE"), nullable=False)
    relationship_type = Column(String(50), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### FastAPI Router Example

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(prefix="/api/sheet-sets", tags=["sheet_sets"])

@router.get("/", response_model=List[SheetSet])
def get_sheet_sets(project_id: UUID, db: Session = Depends(get_db)):
    """Get all sheet sets for a project"""
    sets = db.query(SheetSet).filter(SheetSet.project_id == project_id).all()
    return sets

@router.post("/", response_model=SheetSet, status_code=201)
def create_sheet_set(sheet_set: SheetSetBase, db: Session = Depends(get_db)):
    """Create new sheet set"""
    db_set = SheetSet(**sheet_set.dict())
    db.add(db_set)
    db.commit()
    db.refresh(db_set)
    return db_set

@router.delete("/{set_id}")
def delete_sheet_set(set_id: UUID, db: Session = Depends(get_db)):
    """Delete sheet set (cascades to sheets, assignments, revisions)"""
    db_set = db.query(SheetSet).filter(SheetSet.set_id == set_id).first()
    if not db_set:
        raise HTTPException(status_code=404, detail="Sheet set not found")
    
    db.delete(db_set)
    db.commit()
    return {"message": "Sheet set deleted successfully"}

# Sheets router
sheets_router = APIRouter(prefix="/api/sheets", tags=["sheets"])

@sheets_router.post("/", response_model=Sheet, status_code=201)
def create_sheet(sheet: SheetBase, db: Session = Depends(get_db)):
    """Create new sheet and trigger auto-renumbering"""
    db_sheet = Sheet(**sheet.dict())
    db.add(db_sheet)
    db.commit()
    
    # Trigger auto-renumbering
    renumber_sheets(db, sheet.set_id)
    
    db.refresh(db_sheet)
    return db_sheet

def renumber_sheets(db: Session, set_id: UUID):
    """Renumber all sheets in a set based on hierarchy"""
    sheets = db.query(Sheet).filter(
        Sheet.set_id == set_id
    ).order_by(
        Sheet.sheet_hierarchy_number,
        Sheet.sheet_code
    ).all()
    
    for idx, sheet in enumerate(sheets, start=1):
        sheet.sheet_number = idx
    
    db.commit()
```

---

## Testing Checklist

- [ ] Create project with project details
- [ ] Create sheet set for project
- [ ] Add multiple sheets to set with different categories
- [ ] Verify auto-renumbering after sheet creation
- [ ] Edit sheet (code, title, scale)
- [ ] Delete sheet (verify cascades)
- [ ] Assign drawing to sheet (verify "assigned" badge)
- [ ] Remove drawing assignment (verify "unassigned" badge)
- [ ] Add sheet revision with description
- [ ] View revision history for sheet
- [ ] Create sheet relationship (detail_of, references)
- [ ] Generate sheet index for set
- [ ] Delete sheet set (verify cascades to all sheets, assignments, revisions)
- [ ] Test unique constraint (duplicate sheet codes)

---

## Migration Checklist

- [ ] Create all database tables with proper foreign keys and indexes
- [ ] Seed `sheet_category_standards` table with standard categories
- [ ] Implement Pydantic models for request/response validation
- [ ] Create SQLAlchemy ORM models with proper relationships
- [ ] Implement API routes for all CRUD operations
- [ ] Add sheet renumbering logic (auto-trigger on create)
- [ ] Implement cascading delete logic
- [ ] Build React frontend component (or adapt existing one)
- [ ] Test all user workflows end-to-end
- [ ] Add error handling and validation
- [ ] Document API in Swagger/OpenAPI

---

## Important Notes for FastAPI Migration

### Schema Differences
**CRITICAL:** The current Supabase schema uses:
- `sheets.sheet_category` as TEXT field (not foreign key)
- `sheets.template_id` as INTEGER (not UUID)

If migrating to FastAPI with new database:
1. **Keep as-is**: Maintain TEXT and INTEGER for compatibility
2. **Or refactor**: Convert to proper foreign keys (requires data migration)

### Recommended Approach
1. Start with exact Supabase schema (TEXT, INTEGER)
2. Verify all functionality works
3. Later refactor to foreign keys if desired

### Auto-Renumbering
- Must trigger `renumber_sheets()` after every sheet creation
- Renumbering orders by `sheet_hierarchy_number` then `sheet_code`
- Updates `sheet_number` sequentially (1, 2, 3...)
- Critical for maintaining proper sheet index ordering
