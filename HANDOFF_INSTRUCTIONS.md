# 🚀 Spec-Geometry Linking Project - Handoff Instructions

## Copy-Paste This Into New Chat

```
I'm continuing work on the Spec-Geometry Linking System for the ACAD-GIS project.

**Context**: We're building a comprehensive specification-to-geometry linking system that provides BIM-like intelligence for civil engineering CAD data. This system links CSI MasterFormat specifications to geometric entities with compliance checking, auto-linking, and GraphRAG integration.

**Project Documentation**: Read these files first:
- /home/user/survey-data-system/SPEC_GEOMETRY_LINKING_PROJECT.md (architecture overview)
- /home/user/survey-data-system/IMPLEMENTATION_LOG.md (current progress)
- /home/user/survey-data-system/HANDOFF_INSTRUCTIONS.md (this file)

**Current Status**: [CHECK IMPLEMENTATION_LOG.md FOR CURRENT PHASE]

**What I need**: Continue implementation from where the previous session left off. Check IMPLEMENTATION_LOG.md for the last completed task, then proceed with the next task in the sequence.

**Important Context**:
- We're on branch: claude/review-replit-plan-01Tn3QTRUnK2LBmzn8djkiST
- Database: PostgreSQL with PostGIS
- Backend: Flask/Python
- Frontend: Vanilla JS with cyber/tech aesthetic
- API endpoints already exist for spec_standards and spec_library (see app.py lines 2991-3115)

**Architecture Decision**: We chose Option B (Strategic Foundation) - building for scale from the start, not just an MVP.

**Key Integration Points**:
1. Entity registry (existing) - JSONB entities in various tables
2. Layer standards (existing) - classification patterns we can leverage
3. GraphRAG (existing) - semantic query engine
4. Map Viewer (existing) - needs spec linking integration
5. Project context (existing) - project-scoped operations

Please review the progress, then continue with the next task.
```

---

## Quick Reference: Project Structure

### Phase 1: Database Foundation
**Tasks**:
1. Create `csi_masterformat` table
2. Create `spec_geometry_links` table
3. Create `compliance_rules` table
4. Create `auto_link_rules` table
5. Add `csi_code` column to `spec_library`
6. Create migration script
7. Seed CSI MasterFormat data (civil divisions)

**Files**:
- `migrations/010_spec_geometry_linking.sql`
- `migrations/011_csi_masterformat_seed.sql`

### Phase 2: Backend Services
**Tasks**:
1. Create `services/spec_linking_service.py`
2. Create `services/compliance_service.py`
3. Create `services/auto_linking_service.py`
4. Update `app.py` to import services

**Key Classes**:
- `SpecLinkingService` - CRUD for links, bulk operations
- `ComplianceService` - Rule evaluation, status checks
- `AutoLinkingService` - Pattern matching, classification

### Phase 3: API Endpoints
**Tasks**:
1. Add CSI MasterFormat endpoints (GET hierarchy)
2. Add spec-geometry link CRUD endpoints
3. Add compliance checking endpoints
4. Add auto-linking endpoints
5. Add bulk operation endpoints

**New Routes** (add to `app.py`):
```python
# CSI MasterFormat
GET    /api/csi-masterformat
GET    /api/csi-masterformat/<code>

# Spec-Geometry Links
GET    /api/spec-geometry-links
POST   /api/spec-geometry-links
PUT    /api/spec-geometry-links/<link_id>
DELETE /api/spec-geometry-links/<link_id>
GET    /api/entities/<entity_id>/specs
GET    /api/specs/<spec_id>/entities

# Compliance
POST   /api/compliance/check
GET    /api/compliance/rules
POST   /api/compliance/rules
GET    /api/projects/<project_id>/compliance-status

# Auto-Linking
POST   /api/auto-link/entity/<entity_id>
POST   /api/auto-link/project/<project_id>
GET    /api/auto-link/rules
```

### Phase 4: UI Components
**Tasks**:
1. Update Map Viewer entity panel (add "Link Spec" button)
2. Create spec linking modal component
3. Create compliance dashboard page
4. Update Spec Library with CSI code UI
5. Add visual compliance indicators

**Files**:
- `templates/tools/spec_compliance_dashboard.html`
- `static/js/SpecLinkingManager.js`
- Updates to Map Viewer templates

### Phase 5: Intelligence Layer
**Tasks**:
1. Implement auto-linking rules engine
2. Integrate GraphRAG queries
3. Build change propagation system
4. Add spec version control

---

## Database Schema Quick Reference

### Full Schema Definition

```sql
-- CSI MasterFormat Hierarchy
CREATE TABLE csi_masterformat (
    csi_code VARCHAR(10) PRIMARY KEY,
    csi_title TEXT NOT NULL,
    division INTEGER,
    section INTEGER,
    subsection INTEGER,
    parent_code VARCHAR(10) REFERENCES csi_masterformat(csi_code),
    level INTEGER NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Spec-Geometry Links
CREATE TABLE spec_geometry_links (
    link_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    spec_library_id UUID NOT NULL REFERENCES spec_library(spec_library_id) ON DELETE CASCADE,
    entity_id UUID NOT NULL,
    entity_type VARCHAR(50),
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,

    link_type VARCHAR(20) NOT NULL DEFAULT 'governs',
    compliance_status VARCHAR(20) DEFAULT 'pending',

    linked_by VARCHAR(100),
    linked_at TIMESTAMP DEFAULT NOW(),
    auto_linked BOOLEAN DEFAULT FALSE,

    compliance_notes TEXT,
    last_checked TIMESTAMP,

    CONSTRAINT valid_link_type CHECK (link_type IN ('governs', 'references', 'impacts')),
    CONSTRAINT valid_compliance_status CHECK (compliance_status IN ('compliant', 'warning', 'violation', 'pending', 'not_applicable'))
);

-- Compliance Rules
CREATE TABLE compliance_rules (
    rule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_name VARCHAR(100) NOT NULL,
    csi_code VARCHAR(10) REFERENCES csi_masterformat(csi_code),
    spec_standard_id UUID REFERENCES spec_standards(spec_standard_id),

    rule_type VARCHAR(50) NOT NULL,
    rule_expression JSONB NOT NULL,

    severity VARCHAR(20) DEFAULT 'warning',
    error_message TEXT,

    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_severity CHECK (severity IN ('error', 'warning', 'info'))
);

-- Auto-Linking Rules
CREATE TABLE auto_link_rules (
    rule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_name VARCHAR(100) NOT NULL,
    priority INTEGER DEFAULT 100,

    match_type VARCHAR(50) NOT NULL,
    match_expression JSONB NOT NULL,

    target_spec_id UUID REFERENCES spec_library(spec_library_id),
    target_csi_code VARCHAR(10) REFERENCES csi_masterformat(csi_code),

    link_type VARCHAR(20) DEFAULT 'governs',
    confidence_threshold FLOAT DEFAULT 0.8,

    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Add CSI code to spec_library
ALTER TABLE spec_library
ADD COLUMN csi_code VARCHAR(10) REFERENCES csi_masterformat(csi_code);

-- Indexes for performance
CREATE INDEX idx_spec_geometry_links_spec ON spec_geometry_links(spec_library_id);
CREATE INDEX idx_spec_geometry_links_entity ON spec_geometry_links(entity_id);
CREATE INDEX idx_spec_geometry_links_project ON spec_geometry_links(project_id);
CREATE INDEX idx_spec_geometry_links_status ON spec_geometry_links(compliance_status);
CREATE INDEX idx_compliance_rules_csi ON compliance_rules(csi_code);
CREATE INDEX idx_auto_link_rules_priority ON auto_link_rules(priority DESC);
```

---

## Key Implementation Notes

### 1. Entity Flexibility
Entities are stored across multiple tables. The `entity_id` in `spec_geometry_links` is a UUID that could reference:
- CAD entities in various geometry tables
- Survey points
- Utility structures
- Any geometry with a UUID primary key

Use `entity_type` column to track which table the entity comes from.

### 2. Compliance Rule Expression Format

```json
{
  "rule_type": "dimension_check",
  "conditions": [
    {
      "property": "pipe_diameter",
      "operator": ">=",
      "value": 8
    },
    {
      "property": "pipe_diameter",
      "operator": "<=",
      "value": 36
    }
  ],
  "entity_type": "pipe"
}
```

### 3. Auto-Link Rule Expression Format

```json
{
  "match_type": "layer_pattern",
  "pattern": "^STORM-MH-.*",
  "entity_type": "manhole",
  "properties": {
    "layer_discipline": "storm"
  }
}
```

---

## Testing Checklist

After each phase:
- [ ] Database migrations run cleanly
- [ ] API endpoints return expected responses
- [ ] Frontend components render without errors
- [ ] Integration with existing systems works
- [ ] Performance meets targets (<100ms queries)

---

## Git Workflow

```bash
# Working on branch
git checkout claude/review-replit-plan-01Tn3QTRUnK2LBmzn8djkiST

# Commit frequently with clear messages
git add .
git commit -m "feat(spec-linking): [specific feature]"

# Push when phase complete
git push -u origin claude/review-replit-plan-01Tn3QTRUnK2LBmzn8djkiST
```

---

## Context Preservation

**Critical Files to Reference**:
1. `SPEC_GEOMETRY_LINKING_PROJECT.md` - Architecture
2. `IMPLEMENTATION_LOG.md` - Progress tracking
3. `migrations/010_spec_geometry_linking.sql` - Schema
4. `services/spec_linking_service.py` - Core logic (once created)

**Always Update**: `IMPLEMENTATION_LOG.md` with each completed task.

---

Last Updated: 2025-11-18
