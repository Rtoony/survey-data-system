# Spec-Geometry Linking System - Project Documentation

## Project Overview

**Goal**: Build a comprehensive specification-to-geometry linking system for civil engineering projects that provides BIM-like intelligence for CAD data.

**Competitive Advantage**: Database-first architecture with AI/GraphRAG integration for civil/survey workflows - filling the gap between Procore (no geometry intelligence), BIM tools (building-only), and Civil 3D (file-based, no semantic intelligence).

## Architecture Components

### 1. Database Schema (Foundation Layer)

#### CSI MasterFormat Hierarchy
- Full 50-division industry-standard taxonomy
- Hierarchical structure (Division → Section → Subsection)
- Focus on civil engineering divisions: 02 (Sitework), 33 (Utilities), 34 (Transportation)

#### Spec-Geometry Links
- Bi-directional linking between specs and CAD entities
- Relationship types: `governs`, `references`, `impacts`
- Compliance status tracking
- Audit trail for all linkages

#### Compliance Rules Engine
- Flexible rule definitions using JSONB
- Rule types: dimension_check, property_match, material_validation
- Severity levels: error, warning, info
- Automated compliance checking

### 2. Backend Services Layer

#### SpecLinkingService
- CRUD operations for spec-geometry links
- Bulk linking operations
- Link validation and verification

#### ComplianceService
- Rule evaluation engine
- Compliance status calculation
- Violation detection and reporting

#### AutoLinkingService
- Pattern-based auto-linking
- Layer name classification
- Property-based matching
- ML/AI classification integration

### 3. API Layer

#### Endpoints Required
- `/api/csi-masterformat` - CSI code hierarchy
- `/api/spec-geometry-links` - Link management
- `/api/compliance/check` - Run compliance checks
- `/api/compliance/rules` - Manage rules
- `/api/auto-link` - Trigger auto-linking
- `/api/spec-geometry/bulk` - Bulk operations

### 4. UI Components

#### Map Viewer Integration
- "Link Spec" button in entity property panel
- Visual compliance status indicators
- Color-coded entities by compliance
- Spec assignment interface

#### Compliance Dashboard
- Project-wide compliance overview
- Violation lists and filtering
- Spec coverage statistics
- Missing link detection

#### Spec Library Enhancements
- CSI code assignment UI
- Linked entities viewer
- Impact analysis tool

## Implementation Phases

### Phase 1: Database Foundation ✅ (Week 1-2)
- [ ] Create CSI MasterFormat table + seed data
- [ ] Create spec_geometry_links table
- [ ] Create compliance_rules table
- [ ] Create auto_link_rules table
- [ ] Add csi_code column to spec_library
- [ ] Create database migration script

### Phase 2: Backend Services (Week 2-3)
- [ ] SpecLinkingService class
- [ ] ComplianceService class
- [ ] AutoLinkingService class
- [ ] Helper utilities for rule evaluation

### Phase 3: API Endpoints (Week 3-4)
- [ ] CSI MasterFormat endpoints
- [ ] Spec-geometry link CRUD
- [ ] Compliance checking endpoints
- [ ] Auto-linking endpoints
- [ ] Bulk operations endpoints

### Phase 4: UI Development (Week 4-6)
- [ ] Map Viewer entity panel enhancements
- [ ] Spec linking modal
- [ ] Compliance dashboard page
- [ ] Spec Library CSI integration
- [ ] Visual compliance indicators

### Phase 5: Intelligence Layer (Week 6-8)
- [ ] Auto-linking rules implementation
- [ ] GraphRAG query integration
- [ ] Change propagation system
- [ ] Spec version control

## Database Schema Details

### CSI MasterFormat Structure
```sql
csi_masterformat
├── csi_code (PK): "02 66 13"
├── csi_title: "Storm Drainage"
├── division: 2
├── section: 66
├── subsection: 13
├── parent_code: "02 66 00"
├── level: 1=Division, 2=Section, 3=Subsection
└── description: Full text description
```

### Spec-Geometry Links
```sql
spec_geometry_links
├── link_id (PK)
├── spec_library_id (FK)
├── entity_id (references entities in various tables)
├── project_id (FK)
├── link_type: 'governs'|'references'|'impacts'
├── compliance_status: 'compliant'|'warning'|'violation'|'pending'
├── linked_by, linked_at (audit)
├── auto_linked (boolean)
└── compliance_notes (text)
```

### Compliance Rules
```sql
compliance_rules
├── rule_id (PK)
├── csi_code (FK)
├── rule_type: dimension_check, property_match, material_validation
├── rule_expression (JSONB)
├── severity: error, warning, info
└── error_message (template)
```

## Integration Points

### Existing Systems to Leverage
1. **Entity Registry**: Already have flexible JSONB entities
2. **Layer Standards**: Pattern matching for auto-linking
3. **GraphRAG**: Semantic queries across spec-geometry graph
4. **Map Viewer**: Spatial visualization of compliance
5. **Project Context**: Project-scoped spec assignments

## Success Metrics

### Technical Metrics
- Query performance: <100ms for compliance checks
- Auto-link accuracy: >85% correct classification
- Scale: Handle 100k+ entity-spec links per project

### User Value Metrics
- Time savings: 70% reduction in manual spec tracking
- Compliance: 90%+ spec coverage on entities
- Audit readiness: Complete spec-geometry traceability

## Files Created in This Implementation

### Documentation
- `SPEC_GEOMETRY_LINKING_PROJECT.md` - This file
- `HANDOFF_INSTRUCTIONS.md` - Copy-paste instructions for new chat
- `IMPLEMENTATION_LOG.md` - Progress tracking

### Database
- `migrations/010_spec_geometry_linking.sql` - Main migration
- `migrations/011_csi_masterformat_seed.sql` - CSI code data

### Backend
- `services/spec_linking_service.py` - Link management
- `services/compliance_service.py` - Compliance engine
- `services/auto_linking_service.py` - Auto-linking intelligence

### Frontend
- `templates/tools/spec_compliance_dashboard.html` - Dashboard UI
- `static/js/SpecLinkingManager.js` - Frontend logic
- Updates to existing Map Viewer components

## Current Status

**Started**: 2025-11-18
**Current Phase**: Phase 1 - Database Foundation
**Completion**: 0%

See `IMPLEMENTATION_LOG.md` for detailed progress updates.

## References

### Industry Standards
- CSI MasterFormat 2020 Edition
- Uniformat II Classification
- Caltrans Standard Specifications
- APWA Uniform Public Works Specifications

### Technical Documentation
- PostgreSQL JSONB documentation
- PostGIS spatial queries
- GraphRAG architecture patterns

---

**Next Steps**: See `HANDOFF_INSTRUCTIONS.md` for how to continue this project in a new chat session.
