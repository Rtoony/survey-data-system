# Project Relationship Sets System

## Executive Summary

**Project Relationship Sets** is a flexible dependency tracking and compliance auditing system that enables you to define, monitor, and maintain relationships between any project elements - CAD geometry, specifications, details, notes, hatches, materials, and more.

**The Problem:** In real-world engineering projects, changing one element (like pavement material in specs) creates a ripple effect requiring updates to related items (hatch patterns, details, notes, geometry) - currently managed manually with high error rates.

**The Solution:** Create "Relationship Sets" that group interconnected elements together, then automatically detect when these relationships fall out of sync through intelligent checking algorithms.

---

## Core Concept

### What is a Relationship Set?

A **Relationship Set** is a named collection of related project elements that should remain synchronized. Think of it as a "compliance tracker" or "change impact monitor" for a specific aspect of your project.

**Example:**
```
Set Name: "Pavement Material Compliance Set"
Members:
  - Spec Section 02741.23 (Asphalt Concrete)
  - Detail D-12 (Pavement Section)  
  - Note N-8 (Material Specification Callout)
  - Hatch Pattern PAVE-AC
  - Utility Pipes WHERE material='AC' AND diameter>=12

Rules:
  - All members must have matching 'material' attribute
  - Detail D-12 must reference Spec 02741.23
  - If any member is modified, flag for review
```

When the spec is updated to change the material from AC to PCC, the system automatically flags violations:
- ❌ Detail D-12 still shows AC (needs update)
- ❌ Note N-8 references old material (needs revision)
- ❌ Hatch pattern doesn't match new material

---

## Key Features

### 1. **Flexible Many-to-Many Relationships**
- Not limited to 1:1 relationships
- A single set can contain 5, 10, or 30 interconnected elements
- Link anything to anything (CAD → Specs → Notes → Details → Codes)

### 2. **Metadata-Based Filtering**
- Link not just specific entities, but filtered queries:
  - "All pipes WHERE material='PVC' AND diameter>12"
  - "Notes tagged with 'structural' in Drawing Sheet 5"
  - "Details created after 2024-01-01 by Engineer Smith"

### 3. **Template System**
- Define relationship sets as reusable templates
- Apply templates to new projects instantly
- Capture organizational standards and best practices

### 4. **Audit-First Approach**
- Start with detection and flagging (not auto-correction)
- User reviews and confirms fixes
- Maintains human oversight and accountability

### 5. **Extensible Architecture**
- Supports entities that don't exist yet in your database
- Add new relationship types without code changes
- Grow with your system as you build more features

---

## System Architecture

### Database Schema

The system uses 4 core tables:

#### 1. `project_relationship_sets`
The container for a relationship set.

**Key Fields:**
- `set_id` - Unique identifier
- `project_id` - Project this set belongs to (NULL for templates)
- `set_name` - Human-readable name
- `category` - Grouping (material_compliance, utility_standards, etc.)
- `sync_status` - Current state: in_sync, out_of_sync, incomplete, unknown
- `requires_all_members` - Flag if missing members = violation
- `is_template` - True if this is a reusable template

#### 2. `project_relationship_members`
Individual elements within a relationship set.

**Key Fields:**
- `member_id` - Unique identifier
- `set_id` - Parent relationship set
- `entity_type` - Type of element (detail, note, pipe, spec, etc.)
- `entity_table` - Database table name
- `entity_id` - Specific entity ID (or NULL for filtered queries)
- `filter_conditions` - JSONB metadata filters
- `member_role` - Purpose (source, dependent, reference, governed_by)
- `is_required` - If true, missing element = violation
- `exists` - Cached existence check result

**Example:**
```json
{
  "entity_type": "utility_line",
  "entity_table": "utility_lines",
  "entity_id": null,
  "filter_conditions": {
    "material": "AC",
    "diameter_gte": 12,
    "project_id": "abc123"
  },
  "is_required": true
}
```

#### 3. `project_relationship_rules`
Sync and compliance rules for checking consistency.

**Key Fields:**
- `rule_id` - Unique identifier
- `set_id` - Parent relationship set
- `rule_type` - Type: existence, link_integrity, metadata_consistency, version_check, dependency
- `check_attribute` - Attribute to verify (e.g., 'material', 'revision_date')
- `expected_value` - Expected value or NULL for "all_match"
- `operator` - equals, contains, greater_than, all_match, etc.
- `severity` - info, warning, error, critical

**Example:**
```json
{
  "rule_type": "metadata_consistency",
  "check_attribute": "material",
  "expected_value": "PVC",
  "operator": "equals",
  "severity": "error"
}
```

#### 4. `project_relationship_violations`
Detected out-of-sync conditions and compliance issues.

**Key Fields:**
- `violation_id` - Unique identifier
- `set_id` - Parent relationship set
- `violation_type` - missing_element, broken_link, metadata_mismatch
- `violation_message` - Human-readable description
- `severity` - info, warning, error, critical
- `status` - open, acknowledged, resolved, ignored
- `details` - JSONB with diagnostic information

---

## Implementation Status

### ✅ Phase 1: Core Foundation (COMPLETED)

**Database Schema**
- [x] 4 core tables created
- [x] Summary view (`vw_relationship_set_summary`)
- [x] Helper function for auto-updating sync status
- [x] Automatic triggers for violation tracking

**Backend Services**
- [x] `RelationshipSetService` - Full CRUD for sets, members, rules
- [x] `RelationshipSyncChecker` - Checking engine with 3 algorithms
- [x] Template application system

**API Endpoints**
- [x] 15 RESTful endpoints covering all operations
- [x] GET/POST/PUT/DELETE for sets, members, rules, violations
- [x] Sync checking endpoint
- [x] Template application endpoint

**User Interface**
- [x] Relationship Set Manager page
- [x] List view with status cards
- [x] Create/Edit modal
- [x] Sync status indicators
- [x] Violation counts and badges
- [x] Template selection modal

### ✅ Phase 2: Sync Checking Algorithms (COMPLETED)

#### Check #1: Existence Check
**Purpose:** Verify that all required members exist in the database.

**Detects:**
- Missing entities (specific ID not found in table)
- Empty filtered queries (metadata conditions return no results)

**Example Violation:**
```
"Required detail with ID abc-123 not found in database"
"Required utility_line matching conditions (material=AC, diameter>=12) not found"
```

**Implementation:**
- Queries each member's entity_table
- Checks specific entity_id OR evaluates filter_conditions
- Updates member.exists status
- Creates violation if required member missing

#### Check #2: Link Integrity Check
**Purpose:** Detect broken relationships from branching or deletion.

**Detects:**
- Entities deleted without replacement
- Entities branched (original deleted, new copy created)
- Suggests potential replacement entities

**Example Violation:**
```
"Detail D-12 (ID: def-456) was deleted or branched. 
Found 2 potential replacements created since this relationship was established."
```

**Implementation:**
- Checks if entity_id still exists in entity_table
- If missing, searches for recently created entities of same type
- Provides replacement suggestions in violation details
- Severity: ERROR if no replacements, WARNING if potential replacements exist

#### Check #3: Metadata Consistency Check
**Purpose:** Verify that attributes match across related members.

**Detects:**
- Attribute mismatches (e.g., one member has material='AC', another has material='PVC')
- Inconsistent values across the set

**Example Violation:**
```
"Metadata mismatch: material should be 'PVC' but 3 member(s) have different values"
"Metadata inconsistency: revision_date has 4 different values across members"
```

**Implementation:**
- Reads active metadata_consistency rules for the set
- Queries each member for specified check_attribute
- Compares using operator (equals, all_match)
- Creates violation if inconsistencies found

**Supported Operators:**
- `equals` - All members must match expected_value
- `all_match` - All members must have same value (unspecified)

---

## Future Enhancements

### 🔮 Phase 3: Advanced Checking (PLANNED)

#### Check #4: Version/Revision Check
**Purpose:** Track when elements were last modified and flag stale relationships.

**Detects:**
- Spec updated but related detail not reviewed
- One member modified, others unchanged for 30+ days
- Revision date mismatches

**Example Rule:**
```json
{
  "rule_type": "version_check",
  "check_attribute": "updated_at",
  "operator": "max_age_days",
  "expected_value": "30",
  "severity": "warning"
}
```

**Violation:**
```
"Spec Section 02741 updated 3 days ago, but Detail D-12 last modified 45 days ago. Review required."
```

#### Check #5: Dependency Rule Check
**Purpose:** Enforce conditional logic and business rules.

**Detects:**
- Rule violations (e.g., "If pipe diameter > 12in, Detail D-15 required instead of D-12")
- Missing prerequisite elements
- Incorrect element pairings

**Example Rule:**
```json
{
  "rule_type": "dependency",
  "rule_config": {
    "condition": "pipe.diameter > 12",
    "requires": {
      "entity_type": "detail",
      "entity_id": "detail-d15"
    }
  },
  "severity": "error"
}
```

**Violation:**
```
"Rule violation: 18-inch pipe requires Detail D-15, but relationship references Detail D-12"
```

### 🚀 Phase 4: UI Enhancements (PLANNED)

#### Set Builder Interface (Task #7)
- Visual drag-and-drop member selection
- Entity browser for adding members
- Metadata filter builder (no-code interface)
- Live preview of filtered queries
- Bulk member operations

#### Violation Dashboard (Task #8)
- Centralized violation management
- Severity-based filtering
- Batch resolution workflows
- Violation history and trends
- Automated notifications

#### Detail View Page
- Complete set overview with graph visualization
- Member relationship diagram
- Rule editor with syntax highlighting
- Inline violation resolution
- Change impact analysis

### 🎯 Phase 5: Automation & Intelligence (FUTURE)

**Auto-Fix Capabilities:**
- Propose automatic fixes for simple violations
- User confirms before applying
- Audit trail of all changes

**AI-Powered Suggestions:**
- Detect potential relationships from project patterns
- Suggest relationship sets based on similar projects
- Auto-generate metadata consistency rules

**Change Propagation:**
- When element X changes, suggest updates to related elements
- Generate change order impact reports
- Track downstream effects of design changes

**Integration Points:**
- Link to BIM/CAD change detection
- Connect to specification management systems
- Integration with municipal code databases
- Document management system hooks

---

## Usage Guide

### Creating a Relationship Set

**1. Navigate to Relationship Sets**
```
Projects → [Your Project] → Relationship Sets
```

**2. Create New Set**
```
Click "New Set"
Enter:
  - Name: "Storm Drain Material Compliance"
  - Category: "Material Compliance"
  - Description: "Ensures consistency across storm drain materials"
  ☑ All members required
```

**3. Add Members**
```
Add Specific Entity:
  - Entity Type: detail
  - Entity: Detail D-08 (Storm Drain Section)
  - Role: reference
  - Required: Yes

Add Filtered Query:
  - Entity Type: utility_line
  - Table: utility_lines
  - Filter: {"utility_type": "storm", "material": "HDPE"}
  - Role: governed_by
  - Required: Yes
```

**4. Add Rules**
```
Metadata Consistency Rule:
  - Check Attribute: material
  - Expected Value: HDPE
  - Operator: equals
  - Severity: error

Link Integrity Rule:
  - Auto-generated
  - Detects when detail is branched/deleted
```

**5. Check Sync**
```
Click "Check Sync" to run all 3 checks
Review violations
Resolve issues
```

### Applying a Template

**1. Select "Apply Template"**
```
Browse available templates
Select template matching your needs
```

**2. Customize**
```
Template creates base set structure
Add project-specific members
Adjust rules as needed
```

**3. Activate**
```
Set status to "active"
Run initial sync check
Monitor violations
```

---

## Real-World Examples

### Example 1: Pavement Material Compliance

**Scenario:** City requires AC pavement, but spec might reference PCC.

**Relationship Set:**
```
Name: "Pavement Material Compliance"
Members:
  - Spec Section 02741
  - Detail D-12 (Pavement Section)
  - Note N-8 (Material Callout)
  - Hatch PAVE-AC
  - All utility trenches in roadway

Rules:
  - material = "AC" across all members
  - Detail D-12 references Spec 02741
```

**Violation Detection:**
If engineer changes spec to PCC but forgets detail:
```
❌ Metadata mismatch: material should be 'AC' but Detail D-12 shows 'PCC'
❌ Hatch pattern PAVE-PCC doesn't match spec material AC
```

### Example 2: Utility Coordination

**Scenario:** Gas and electrical utilities can't be in same trench.

**Relationship Set:**
```
Name: "Joint Trench Separation Rules"
Members:
  - Gas lines in Trench A
  - Electric lines
  - Municipal Code Section 12.8.5

Rules:
  - Gas and electric in different trenches
  - All trenches comply with code section
  - Minimum 3ft separation
```

**Violation Detection:**
If designer places both in same trench:
```
❌ Dependency violation: Gas and electric utilities cannot share trench
❌ Code Section 12.8.5 requires 3ft minimum separation
```

### Example 3: ADA Compliance Set

**Scenario:** Ramps, slopes, and notes must match ADA requirements.

**Relationship Set:**
```
Name: "ADA Ramp Compliance"
Members:
  - All ADA ramps (slope <= 8.33%)
  - Detail D-25 (ADA Ramp Detail)
  - Note N-15 (ADA Compliance Statement)
  - Municipal ADA requirements

Rules:
  - All ramps reference Detail D-25
  - Slopes don't exceed 8.33%
  - Note N-15 present on all sheets with ramps
```

**Violation Detection:**
If ramp exceeds slope:
```
❌ Ramp R-03 has slope 10.5% (exceeds 8.33% maximum)
❌ Missing Note N-15 on Sheet C-4 (contains ADA ramps)
```

---

## Technical Details

### API Usage

**List Sets for Project:**
```javascript
GET /api/projects/{project_id}/relationship-sets
Response: {
  "sets": [
    {
      "set_id": "...",
      "set_name": "Pavement Material Compliance",
      "sync_status": "out_of_sync",
      "member_count": 5,
      "open_violations": 2,
      ...
    }
  ]
}
```

**Create Set:**
```javascript
POST /api/relationship-sets
Body: {
  "project_id": "abc-123",
  "set_name": "Storm Drain Compliance",
  "category": "material_compliance",
  "requires_all_members": true
}
```

**Add Member:**
```javascript
POST /api/relationship-sets/{set_id}/members
Body: {
  "entity_type": "utility_line",
  "entity_table": "utility_lines",
  "filter_conditions": {
    "utility_type": "storm",
    "material": "HDPE"
  },
  "is_required": true
}
```

**Run Sync Check:**
```javascript
POST /api/relationship-sets/{set_id}/check-sync
Response: {
  "total_violations": 3,
  "existence_violations": 1,
  "link_integrity_violations": 0,
  "metadata_violations": 2,
  "violations_by_severity": {
    "error": 2,
    "warning": 1
  }
}
```

### Extending the System

**Adding New Entity Types:**
No code changes required! Just:
1. Ensure entity table exists in database
2. Add member with correct entity_type and entity_table
3. System automatically queries the table

**Custom Rules:**
```sql
INSERT INTO project_relationship_rules (
  set_id,
  rule_type,
  rule_name,
  check_attribute,
  operator,
  expected_value,
  severity
) VALUES (
  'set-uuid',
  'metadata_consistency',
  'Material Must Be PVC',
  'material',
  'equals',
  'PVC',
  'error'
);
```

**Filter Condition Syntax:**
```json
{
  "material": "AC",              // Exact match
  "diameter_gte": 12,            // Greater than or equal
  "diameter_lte": 24,            // Less than or equal
  "created_at_gt": "2024-01-01", // Greater than (dates)
  "updated_at_lt": "2024-12-31"  // Less than (dates)
}
```

---

## Benefits

### For Project Managers
- **Catch errors early** - Before they reach construction
- **Reduce rework** - Consistency checks prevent mistakes
- **Audit trail** - Track what changed and when
- **Client confidence** - Demonstrate quality control

### For Engineers
- **Less manual checking** - System flags issues automatically
- **Change impact visibility** - See what else needs updating
- **Standards enforcement** - Templates ensure compliance
- **Time savings** - Focus on design, not verification

### For QA/QC Teams
- **Systematic review** - Every relationship checked
- **Prioritized violations** - Severity-based triage
- **Violation tracking** - Monitor resolution progress
- **Reporting** - Export compliance reports

---

## Conclusion

The **Project Relationship Sets** system transforms dependency tracking from a manual, error-prone process into an automated, intelligent compliance engine. By defining relationships once and checking them continuously, you ensure project-wide consistency and catch issues before they become costly problems.

**Current Status:** ✅ MVP Complete (Phases 1-2)
**Next Steps:** UI enhancements (Phase 4) and advanced checking (Phase 3)

**Start using it today:**
1. Navigate to Projects → [Your Project] → Relationship Sets
2. Create your first set tracking a critical dependency
3. Run sync check and see violations detected
4. Build more sets as you identify relationships in your projects

---

## Support & Feedback

For questions, issues, or feature requests:
- Review this documentation
- Check API endpoints in `app.py`
- Examine database schema in `database/create_project_relationship_sets.sql`
- Explore service logic in `services/relationship_set_service.py` and `services/relationship_sync_checker.py`

**Remember:** This is a living system. As you build more features (specs system, deliverables tracking, etc.), you can add new entity types to relationship sets without changing any code. The architecture is designed to grow with your project.
