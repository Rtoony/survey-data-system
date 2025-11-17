# Attribute System Guide

## Overview

The **Attribute System** adds a third dimension to the specialized tools framework in ACAD-GIS, enabling **surgical precision filtering** for CAD object classifications. This system allows the same object type to be used by different tools for different purposes based on attribute qualifiers.

### Three-Dimensional Filtering

```
Object Type → Attribute → Database Table
```

**Example:**
- A **BASIN** can be classified with different attributes:
  - `BASIN + STORAGE` → Detention basin (used by Volume Calculator)
  - `BASIN + TREATMENT` → Biotreatment basin (used by Pervious Analysis)
  - `BASIN + NULL` → Generic basin (used by any tool)

This enables client-specific CAD standards and flexible tool mappings without hard-coding.

---

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     CAD Layer Name                              │
│          SITE-BMP-BASIN-STORAGE-NEW-PG                         │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ├─→ DISCIPLINE: SITE
                 ├─→ CATEGORY: BMP
                 ├─→ OBJECT TYPE: BASIN
                 ├─→ ATTRIBUTE: STORAGE ◄── NEW DIMENSION
                 ├─→ PHASE: NEW
                 └─→ GEOMETRY: PG
                        │
                        ▼
        ┌───────────────────────────────────┐
        │   Tool-Object Mappings Filter     │
        │   (tool_object_mappings table)    │
        └───────────────┬───────────────────┘
                        │
        ┌───────────────┴───────────────────┐
        │                                   │
        ▼                                   ▼
   VOL Tool                            PERV Tool
   Filters:                            Filters:
   • BASIN + STORAGE                   • BASIN + TREATMENT
   • POND + STORAGE                    • POND + TREATMENT
        │                                   │
        ▼                                   ▼
   Entity Registry                     Entity Registry
   BASIN → storm_bmps                  BASIN → storm_bmps
        │                                   │
        ▼                                   ▼
   Database Query:                     Database Query:
   SELECT * FROM storm_bmps            SELECT * FROM storm_bmps
   WHERE object_type='BASIN'           WHERE object_type='BASIN'
   AND attribute_code='STORAGE'        AND attribute_code='TREATMENT'
```

### Database Schema

#### attribute_codes Table

Stores all available attributes for layer classification.

| Column | Type | Description |
|--------|------|-------------|
| `code` | VARCHAR(10) PK | Short code (e.g., STORAGE, 8IN, PVC) |
| `full_name` | VARCHAR(100) | Human-readable name |
| `attribute_category` | VARCHAR(50) | Category: Size, Material, Function |
| `attribute_type` | VARCHAR(50) | Type classification |
| `description` | TEXT | Detailed description |
| `is_locked` | BOOLEAN | System-critical attribute (cannot delete) |
| `sort_order` | INTEGER | Display ordering |
| `is_active` | BOOLEAN | Active flag |

**Seeded Attributes (30 total, 16 locked):**

**Size Attributes (6):**
- 4IN, 6IN, 8IN, 12IN, 18IN, 24IN

**Material Attributes (3):**
- PVC, RCP, CONC

**Function Attributes (6):**
- STORAGE, TREATMENT, DETENTION, INFILTRATION, TOPO, CONTROL

**Other Attributes (15):**
- Various project-specific codes

#### tool_object_mappings Table (Enhanced)

Links tools to object types with optional attribute filtering.

| Column | Type | Description |
|--------|------|-------------|
| `mapping_id` | SERIAL PK | Unique ID |
| `tool_code` | VARCHAR(10) FK | Tool identifier |
| `object_type_code` | VARCHAR(10) FK | Object type code |
| `attribute_code` | VARCHAR(10) FK | **Attribute filter (NULL = wildcard)** |
| `purpose` | TEXT | Why this mapping exists |
| `sort_order` | INTEGER | Display order |
| `is_active` | BOOLEAN | Active flag |

**Unique Constraint:**
```sql
UNIQUE NULLS NOT DISTINCT (tool_code, object_type_code, attribute_code)
```

This allows:
- ✅ `(VOL, BASIN, NULL)` - Wildcard mapping
- ✅ `(VOL, BASIN, STORAGE)` - Attribute-specific mapping
- ✅ `(VOL, BASIN, TREATMENT)` - Different attribute mapping
- ❌ Duplicate combinations

---

## How It Works: Data Flow

### 1. Layer Name Classification

When a DXF layer is imported:

```
Input: SITE-BMP-BASIN-STORAGE-NEW-PG

Parsed:
- discipline_code: SITE
- category_code: BMP
- object_type_code: BASIN
- attribute_code: STORAGE  ◄── Extracted
- phase_code: NEW
- geometry_code: PG
```

### 2. Tool Mapping Lookup

The system queries `tool_object_mappings`:

```sql
SELECT tool_code, object_type_code, attribute_code, database_table
FROM tool_object_mappings
WHERE object_type_code = 'BASIN'
AND (attribute_code = 'STORAGE' OR attribute_code IS NULL)
AND is_active = TRUE;
```

**Result:**
- `VOL` tool matches: `(VOL, BASIN, STORAGE)` ✅
- `PERV` tool does NOT match: `(PERV, BASIN, TREATMENT)` ❌

### 3. Entity Registry Resolution

The matched mapping provides the database table via Entity Registry:

```
BASIN → storm_bmps table
```

### 4. Database Storage

Entity is stored with full metadata:

```sql
INSERT INTO storm_bmps (
    object_type_code, 
    attribute_code,
    -- other fields...
)
VALUES ('BASIN', 'STORAGE', ...);
```

### 5. Tool Access

When the **Volume Calculator** (VOL) tool loads:

```sql
SELECT * FROM storm_bmps
WHERE object_type_code IN (
    SELECT object_type_code 
    FROM tool_object_mappings 
    WHERE tool_code = 'VOL'
    AND (attribute_code = 'STORAGE' OR attribute_code IS NULL)
);
```

**Result:** Only BASIN+STORAGE entities appear in the tool.

---

## User Guide: Managing Attributes

### Adding a New Attribute

1. Navigate to **Standards → Reference Data Hub**
2. Click the **Attribute Codes** tab
3. Click **+ Add New Attribute**
4. Fill in the form:
   - **Code**: Short uppercase code (e.g., `16IN`)
   - **Full Name**: Descriptive name (e.g., `16 Inch Diameter`)
   - **Category**: Size, Material, or Function
   - **Type**: Optional type classification
   - **Description**: When/why to use this attribute
   - **Sort Order**: Display ordering (lower = first)
   - **Locked**: Check ONLY for system-critical attributes

5. Click **Save Attribute**

### Editing an Attribute

1. Click the **Edit** (pencil) icon next to any attribute
2. Modify fields (cannot change code for locked attributes)
3. Click **Save Attribute**

### Deleting an Attribute

1. Click the **Delete** (trash) icon
2. Confirm deletion

**Note:** Locked attributes cannot be deleted (protected server-side).

---

## User Guide: Creating Attribute-Aware Tool Mappings

### Creating a Mapping with Attribute Filter

**Scenario:** You want the Volume Calculator to ONLY manage detention basins with STORAGE function (not treatment basins).

1. Navigate to **Standards → Reference Data Hub**
2. Click the **Tool Object Mappings** tab
3. Click **+ Add New Mapping**
4. Fill in the form:
   - **Tool**: Material Volume Calculator (VOL)
   - **Object Type**: BASIN
   - **Attribute Filter**: STORAGE ◄── **Select specific attribute**
   - **Purpose**: "Calculate detention basin storage volume (STORAGE function only)"
   - **Sort Order**: 100

5. Click **Save Mapping**

### Creating a Wildcard Mapping (All Attributes)

**Scenario:** You want the Area Calculator to work with ALL basin types regardless of attribute.

1. Follow steps 1-3 above
2. Fill in the form:
   - **Tool**: Area Calculator (AREA)
   - **Object Type**: BASIN
   - **Attribute Filter**: No Filter (All Attributes) ◄── **Leave as default**
   - **Purpose**: "Calculate basin area for all types"
   - **Sort Order**: 10

3. Click **Save Mapping**

### Understanding the Mapping Display

In the Tool Mappings tab, you'll see:

```
📊 Material Volume Calculator (VOL)

BASIN 🔒STORAGE  Detention Basin  SITE-BMP  • Calculate detention basin storage volume
POND  🔒STORAGE  Detention Pond   SITE-BMP  • Calculate detention pond storage volume
SLOPE            Slope            SITE-GRAD • Calculate volume for slope grading
```

**Legend:**
- `🔒STORAGE` = Orange badge indicates attribute-specific filter
- No badge = Wildcard mapping (works with all attributes)

---

## Locked vs. Editable Attributes

### System-Critical (Locked) Attributes

**28 locked attributes** are essential to core system functionality and cannot be deleted:

**Pipe Sizes (13):** 4IN, 6IN, 8IN, 10IN, 12IN, 15IN, 18IN, 21IN, 24IN, 30IN, 36IN, 42IN, 48IN
**Materials (8):** PVC, HDPE, RCP, VCP, DI, STEEL, CONC, AC
**Functions (7):** STORAGE, TREATMENT, DETENTION, RETENTION, INFILTRATION, TOPO, CONTROL

**Characteristics:**
- ✅ Can be edited (name, description, sort order)
- ❌ Cannot be deleted
- ❌ Code cannot be changed
- 🔒 Shows lock icon in UI
- Protected by server-side validation (403 error if delete attempted)

### Custom (Editable) Attributes

**14 custom attributes** can be fully managed (2FT-10FT sizes, PVMT, BIOTREAT, BNDY, type modifiers, surface types):

**Characteristics:**
- ✅ Can be edited
- ✅ Can be deleted (if not in use)
- ✅ Code can be changed
- No lock icon in UI

**Best Practice:** Lock any attribute that becomes critical to your workflows.

---

## Real-World Examples

### Example 1: Detention vs. Biotreatment Basins

**Problem:** You have two types of basins that need different tool workflows.

**Solution:** Use attribute filtering.

**Setup:**
```
Attribute Codes:
- STORAGE (locked, function)
- TREATMENT (locked, function)

Tool Mappings:
- VOL + BASIN + STORAGE  → Volume calculations for detention
- VOL + POND + STORAGE   → Volume calculations for retention
- PERV + BASIN + TREATMENT → Pervious analysis for biotreatment
- PERV + POND + TREATMENT  → Pervious analysis for biotreatment ponds
```

**Layer Names:**
```
SITE-BMP-BASIN-STORAGE-NEW-PG    → Goes to VOL tool
SITE-BMP-BASIN-TREATMENT-NEW-PG  → Goes to PERV tool
```

**Result:** Same object type (BASIN), different workflows based on function.

### Example 2: Pipe Size Differentiation

**Problem:** You need to calculate volumes for different pipe sizes separately.

**Setup:**
```
Attribute Codes:
- 8IN, 12IN, 18IN (locked, size)

Tool Mappings:
- VOL + PIPE + 8IN  → Calculate 8" pipe volumes
- VOL + PIPE + 12IN → Calculate 12" pipe volumes
- VOL + PIPE + 18IN → Calculate 18" pipe volumes
```

**Layer Names:**
```
UTIL-STORM-PIPE-8IN-NEW-LN   → 8" storm pipe
UTIL-STORM-PIPE-12IN-NEW-LN  → 12" storm pipe
UTIL-STORM-PIPE-18IN-NEW-LN  → 18" storm pipe
```

**Result:** Volume calculator can filter by pipe size for accurate quantity takeoffs.

### Example 3: Material-Based Workflows

**Problem:** Different construction materials require different specifications.

**Setup:**
```
Attribute Codes:
- PVC, RCP, CONC (locked, material)

Tool Mappings:
- SPEC + PIPE + PVC  → PVC pipe specifications
- SPEC + PIPE + RCP  → RCP pipe specifications
- SPEC + PIPE + CONC → Concrete pipe specifications
```

**Result:** Specification tool shows only relevant specs for each material type.

---

## API Reference

### GET /api/standards/attributes

Retrieve all attributes.

**Success Response (200):**
```json
{
  "success": true,
  "attributes": [
    {
      "code": "STORAGE",
      "full_name": "Storage",
      "attribute_category": "Function",
      "attribute_type": "function",
      "description": "Storage and detention function",
      "is_locked": true,
      "sort_order": 10,
      "is_active": true,
      "created_at": "2025-01-15T12:00:00",
      "updated_at": "2025-01-15T12:00:00"
    }
  ]
}
```

**Error Response (500):**
```json
{
  "error": "Database connection failed",
  "status": 500
}
```

### POST /api/standards/attributes

Create a new attribute.

**Request:**
```json
{
  "code": "24IN",
  "full_name": "24 Inch Diameter",
  "attribute_category": "Size",
  "attribute_type": "size",
  "description": "24 inch pipe diameter",
  "sort_order": 60,
  "is_locked": false
}
```

**Success Response (201):**
```json
{
  "success": true,
  "message": "Attribute created successfully",
  "attribute_code": "24IN"
}
```

**Error Responses:**

**400 - Validation Error:**
```json
{
  "error": "Missing required field: code",
  "status": 400
}
```

**409 - Duplicate Code:**
```json
{
  "error": "Attribute code '24IN' already exists",
  "status": 409
}
```

### PUT /api/standards/attributes/{code}

Update an existing attribute.

**Request:**
```json
{
  "full_name": "24 Inch Pipe Diameter",
  "description": "Updated description",
  "sort_order": 65
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Attribute updated successfully",
  "attribute_code": "24IN"
}
```

**Error Responses:**

**403 - Locked Attribute Code Change:**
```json
{
  "error": "Cannot change code of locked attribute: STORAGE",
  "status": 403
}
```

**404 - Not Found:**
```json
{
  "error": "Attribute not found: INVALID_CODE",
  "status": 404
}
```

### DELETE /api/standards/attributes/{code}

Delete an attribute (soft delete).

**Success Response (200):**
```json
{
  "success": true,
  "message": "Attribute deleted successfully",
  "attribute_code": "24IN"
}
```

**Error Responses:**

**403 - Locked Attribute:**
```json
{
  "error": "Cannot delete locked attribute: STORAGE",
  "status": 403
}
```

**404 - Not Found:**
```json
{
  "error": "Attribute not found: INVALID_CODE",
  "status": 404
}
```

**409 - In Use:**
```json
{
  "error": "Cannot delete attribute: currently in use by 15 entities",
  "status": 409
}
```

### GET /api/standards/tool-layer-examples?tool_code={code}

Get tool information with attribute-aware mappings.

**Response:**
```json
{
  "success": true,
  "tools": [
    {
      "tool_code": "VOL",
      "tool_name": "Material Volume Calculator",
      "mapped_object_types": [
        {
          "code": "BASIN",
          "name": "Detention Basin",
          "attribute_code": "STORAGE",
          "attribute_name": "Storage",
          "attribute_category": "Function"
        }
      ],
      "layer_examples": [
        {
          "layer_name": "SITE-BMP-BASIN-STORAGE-NEW-PG",
          "object_type": "BASIN",
          "attribute_code": "STORAGE",
          "description": "New Detention Basin (Storage) - Site/BMP"
        }
      ]
    }
  ]
}
```

---

## Troubleshooting

### Problem: Attribute Filter Not Working

**Symptom:** Tool shows entities regardless of attribute.

**Causes:**
1. **Wildcard mapping exists**: Check if `(tool, object, NULL)` mapping exists
2. **Case sensitivity**: Attribute codes are case-sensitive
3. **Cache issue**: Restart the server to clear API cache

**Solution:**
```sql
-- Check existing mappings
SELECT tool_code, object_type_code, attribute_code, purpose
FROM tool_object_mappings
WHERE tool_code = 'VOL' AND object_type_code = 'BASIN';

-- You should see ONLY attribute-specific or ONLY wildcard, not both
```

### Problem: Cannot Delete Attribute

**Symptom:** Delete button disabled or 403 error.

**Cause:** Attribute is locked (system-critical).

**Solution:** This is by design. Locked attributes protect system integrity. If you need to remove it, first:
1. Check if it's truly not needed
2. Update `is_locked = FALSE` in database (only if you're certain)
3. Better: Keep it and set `is_active = FALSE` instead

### Problem: Duplicate Mapping Error

**Symptom:** "Unique constraint violation" when creating mapping.

**Cause:** Mapping with same `(tool_code, object_type_code, attribute_code)` already exists.

**Solution:**
1. Check existing mappings in Tool Object Mappings tab
2. Either edit the existing mapping or delete it first
3. Remember: `NULL` attribute is treated as a distinct value

### Problem: Layer Not Classified Correctly

**Symptom:** DXF import doesn't extract attribute from layer name.

**Cause:** Attribute not in standard position in layer name.

**Solution:** Ensure layer follows format:
```
{DISC}-{CAT}-{OBJ}-{ATTR}-{PHASE}-{GEOM}
                    ^^^^^^
                    Position 4
```

---

## Best Practices

### 1. Use Attributes Sparingly

**Good:**
```
BASIN + STORAGE    (clear functional difference)
BASIN + TREATMENT  (different workflow)
```

**Bad:**
```
BASIN + TYPE1
BASIN + TYPE2
BASIN + VARIANT_A
```

Keep attributes meaningful. Overuse creates complexity.

### 2. Lock Critical Attributes Early

Once an attribute is used in production projects:
1. Set `is_locked = TRUE`
2. This prevents accidental deletion
3. Maintains data integrity across projects

### 3. Wildcard vs. Specific: Choose Wisely

**Use wildcard (NULL)** when:
- Tool works with ALL variants of an object
- No functional difference exists

**Use attribute filter** when:
- Different workflows required
- Different specifications apply
- Volume/quantity calculations differ

### 4. Document Your Attribute Strategy

In the `description` field, explain:
- When to use this attribute
- What it means functionally
- Which tools consume it

**Example:**
```
Code: STORAGE
Description: "Use for detention/retention basins designed for storage volume. 
              Consumed by Volume Calculator (VOL) for quantity takeoffs. 
              Do NOT use for biotreatment basins (use TREATMENT instead)."
```

### 5. Naming Conventions

**Sizes:** Use standard units
```
4IN, 6IN, 8IN (not FOUR_INCH)
24MM, 36MM (metric)
```

**Materials:** Use industry abbreviations
```
PVC, RCP, CONC (not POLYVINYL_CHLORIDE)
```

**Functions:** Use clear, single-word descriptors
```
STORAGE, TREATMENT (not DETENTION_STORAGE_BASIN)
```

---

## Migration Guide: Adding Attributes to Existing System

If you have an existing ACAD-GIS installation without attributes:

### Step 1: Run Migrations

```bash
# Apply attribute_codes table enhancements
psql -U username -d acad_gis -f database/migrations/create_attribute_codes_table.sql

# Seed initial attributes
psql -U username -d acad_gis -f database/seed_attribute_codes.sql

# Update tool_object_mappings unique constraint
ALTER TABLE tool_object_mappings 
DROP CONSTRAINT IF EXISTS tool_object_mappings_tool_code_object_type_code_key;

ALTER TABLE tool_object_mappings 
ADD CONSTRAINT tool_object_mappings_unique_combination 
UNIQUE NULLS NOT DISTINCT (tool_code, object_type_code, attribute_code);
```

### Step 2: Update Existing Mappings

All existing mappings will have `attribute_code = NULL` (wildcard). This is correct and backward-compatible.

### Step 3: Add Attribute-Specific Mappings

For tools that need filtering, add new mappings:

```sql
INSERT INTO tool_object_mappings (tool_code, object_type_code, attribute_code, purpose, sort_order, is_active)
VALUES ('VOL', 'BASIN', 'STORAGE', 'Calculate detention basin storage volume', 100, TRUE);
```

### Step 4: Test Integration

1. Navigate to Reference Data Hub → Attribute Codes
2. Verify 30 attributes loaded
3. Navigate to Tool Object Mappings
4. Create a test attribute-specific mapping
5. Check a specialized tool (e.g., Volume Calculator)
6. Verify layer examples show attribute badges

---

## Future Enhancements

Potential improvements to the attribute system:

1. **Hierarchical Attributes**: Parent-child relationships (e.g., PIPE → 8IN)
2. **Attribute Groups**: Bundle related attributes (e.g., SIZE_GROUP)
3. **Conditional Attributes**: Rules for when certain attributes apply
4. **Attribute Validation**: Prevent invalid combinations (e.g., BASIN + 8IN)
5. **Bulk Attribute Operations**: Apply attribute to multiple entities at once
6. **Attribute Analytics**: Track usage patterns and popular combinations
7. **Import/Export**: Share attribute configurations between installations

---

## Support

For issues, questions, or suggestions:
- Check this guide first
- Review the API documentation above
- Inspect database schema with Schema Explorer
- Check Reference Data Hub for current configuration

**Remember:** The attribute system is database-driven. All configuration is in the database, not code. This means you can customize it per client without changing the application.
