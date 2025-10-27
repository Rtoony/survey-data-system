None
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
