# Relationship Set Naming Templates - User Guide

## Overview

The **Naming Templates** system eliminates free-text naming inconsistencies by providing standardized, reusable naming patterns for Project Relationship Sets. This ensures consistency across projects and enables powerful search and filtering capabilities.

---

## Accessing the System

### Managing Templates

1. Navigate to **Standards > Reference Data Hub**
2. Click the **"Naming Templates"** tab
3. You'll see all available templates organized by category

### Using Templates in Relationship Sets

1. Navigate to **Project > Relationship Sets**
2. Click **"New Set"**
3. Select a template from the **"Naming Template"** dropdown
4. Fill in the required token values
5. Watch the live preview update automatically

---

## Template Structure

Each naming template consists of:

| Field | Description | Example |
|-------|-------------|---------|
| **Template Name** | Descriptive name for the pattern | "Storm System Compliance" |
| **Category** | Organizational grouping | "Drainage Infrastructure" |
| **Name Format** | Full name pattern with `{TOKENS}` | `{PROJECT_CODE} - Storm System - {LOCATION}` |
| **Short Code Format** | Abbreviated pattern | `STORM-{PROJECT_CODE}-{SEQ}` |
| **Required Tokens** | Must be filled (validation enforced) | `["PROJECT_CODE", "LOCATION", "SEQ"]` |
| **Optional Tokens** | Can be left empty | `["PHASE"]` |
| **Example** | Filled-in demonstration | `PRJ-2024-001 - Storm System - Main St & 5th Ave` |

---

## Using Templates (Step-by-Step)

### Step 1: Create a Relationship Set

1. Go to **Project > Relationship Sets**
2. Click **"New Set"**
3. Select a template from the dropdown

Example: Select **"Storm System Compliance"**

### Step 2: Fill in Token Values

The system will display input fields for each token:

```
Template: {PROJECT_CODE} - Storm System - {LOCATION}
```

**Token Fields:**
- **PROJECT_CODE** *(required)*: `PRJ-2024-001`
- **LOCATION** *(required)*: `Main St & 5th Ave`
- **SEQ** *(required)*: `01`

### Step 3: Review Live Preview

As you type, the preview updates automatically:

```
✓ Generated Name: PRJ-2024-001 - Storm System - Main St & 5th Ave
✓ Short Code: STORM-PRJ-2024-001-01
```

### Step 4: Complete the Form

- Add a **Description** (optional)
- Select a **Category** (optional)
- Click **"Save Set"**

The system stores both the generated name/code **and** the template reference for future auditing.

---

## Managing Templates (Admin)

### Creating a New Template

1. Navigate to **Reference Data Hub > Naming Templates**
2. Click **"Add New Template"**
3. Fill in the form:

**Basic Information:**
- **Template Name**: e.g., "Pavement Rehabilitation Package"
- **Category**: e.g., "Pavement"
- **Name Format**: e.g., `{STREET_NAME} - Pavement {WORK_TYPE} - Phase {PHASE}`
- **Short Code Format**: e.g., `PAVE-{STREET}-{PHASE}`

**Tokens:**
- **Required Tokens (JSON)**: `["STREET_NAME", "WORK_TYPE", "PHASE"]`
- **Optional Tokens (JSON)**: `["CONTRACTOR"]`

**Examples:**
- **Example Name**: `Main Street - Pavement Overlay - Phase 1`
- **Example Code**: `PAVE-MAIN-1`
- **Example Tokens (JSON)**:
  ```json
  {
    "STREET_NAME": "Main Street",
    "WORK_TYPE": "Overlay",
    "PHASE": "1"
  }
  ```

**Usage Instructions:**
```
Use this template for pavement rehabilitation projects.
STREET_NAME should match the primary street being rehabilitated.
WORK_TYPE: Overlay, Reconstruction, Mill & Fill, etc.
PHASE: Construction phase number (1, 2, 3, etc.)
```

4. Click **"Save Template"**

### Editing Templates

1. Click the **Edit (pencil)** icon on any template card
2. Modify fields as needed
3. Click **"Save Template"**

**⚠️ Warning:** Changing a template does NOT update existing relationship sets that used it. Only new sets will use the updated format.

### Deleting Templates

1. Click the **Delete (trash)** icon on a template
2. Confirm the deletion

**Note:** This is a soft delete. The template is marked as `is_active = FALSE` but remains in the database for historical reference.

---

## Common Token Patterns

| Token Name | Description | Example Values |
|------------|-------------|----------------|
| `PROJECT_CODE` | Unique project identifier | `PRJ-2024-001`, `SUNSET-BLVD` |
| `SEQ` | Sequence number (2 digits) | `01`, `02`, `99` |
| `LOCATION` | Geographic description | `Main St & 5th Ave`, `Downtown` |
| `UTILITY_TYPE` | Utility system type | `STORM`, `SEWER`, `WATER`, `RECLAIM` |
| `MATERIAL` | Material type | `PVC`, `HDPE`, `RCP`, `CONCRETE` |
| `PHASE` | Construction phase | `1`, `2A`, `FINAL` |
| `STREET_NAME` | Street name | `Main Street`, `Highway 101` |
| `WORK_TYPE` | Type of work | `OVERLAY`, `RECONSTRUCTION` |
| `BMP_TYPE` | Best Management Practice | `BIOSWALE`, `BASIN`, `FILTER` |
| `FEATURE_TYPE` | Feature classification | `RAMPS`, `CROSSWALKS`, `PARKING` |

---

## Best Practices

### 1. Use Descriptive Token Names
✅ **Good**: `{UTILITY_TYPE}`, `{STREET_NAME}`, `{BMP_TYPE}`
❌ **Bad**: `{TYPE}`, `{NAME}`, `{X}`

### 2. Keep Short Codes Concise
✅ **Good**: `STORM-PRJ001-01` (18 chars)
❌ **Bad**: `STORM-DRAINAGE-SYSTEM-PROJECT-2024-001-SEQUENCE-01` (50 chars)

### 3. Mark Critical Tokens as Required
- If a token is essential for uniqueness, make it **required**
- Example: `PROJECT_CODE`, `SEQ` should almost always be required

### 4. Provide Clear Usage Instructions
Help users understand:
- When to use this template
- What values are expected for each token
- Any naming conventions or restrictions

### 5. Use Examples
Show a fully filled-in example so users can see the pattern in action.

---

## Token Definitions (Advanced)

For more sophisticated templates, you can define structured token metadata in the `token_definitions` JSONB field:

```json
{
  "UTILITY_TYPE": {
    "label": "Utility Type",
    "type": "dropdown",
    "options": ["STORM", "SEWER", "WATER", "RECLAIM"],
    "required": true,
    "help_text": "Primary utility system type"
  },
  "LOCATION": {
    "label": "Location/Area",
    "type": "text",
    "max_length": 50,
    "required": true,
    "help_text": "Geographic area or street name"
  }
}
```

**Future Enhancement:** This structure supports a future **Token Builder UI** that generates dropdowns, text inputs, and validation rules automatically.

---

## API Reference

### Preview Template with Token Values

**Endpoint:** `POST /api/naming-templates/<template_id>/preview`

**Request Body:**
```json
{
  "PROJECT_CODE": "PRJ-2024-001",
  "LOCATION": "Main St & 5th Ave",
  "SEQ": "01"
}
```

**Response:**
```json
{
  "generated_name": "PRJ-2024-001 - Storm System - Main St & 5th Ave",
  "generated_code": "STORM-PRJ-2024-001-01",
  "remaining_tokens": {
    "name": [],
    "code": []
  },
  "is_complete": true
}
```

---

## Troubleshooting

### "Missing required tokens" Error
**Problem:** You tried to save a relationship set without filling in all required token fields.

**Solution:** Check the preview pane. Any `{TOKEN}` placeholders that remain indicate missing values.

### Template Not Appearing in Dropdown
**Problem:** The template was soft-deleted or marked as `is_active = FALSE`.

**Solution:** Only active templates appear in the dropdown. Check the template in Reference Data Hub and ensure it's not deleted.

### Generated Name Too Long
**Problem:** Your token values created a name exceeding database limits (255 chars for `set_name`).

**Solution:** Use shorter token values or modify the template's `name_format` to be more concise.

---

## Roadmap Enhancements

### Phase 2 (Planned)
- **Token Builder UI**: Visual editor for token definitions (no manual JSON)
- **Template Analytics**: Track which templates are most used
- **Smart Suggestions**: AI recommends templates based on relationship set members
- **Versioning**: Track template changes over time, migrate sets to new versions
- **Import/Export**: Share templates across ACAD-GIS instances
- **Client-Specific Templates**: Multi-tenant templates with client-specific standards

---

## Summary

The Naming Templates system:
- ✅ Eliminates free-text naming chaos
- ✅ Ensures consistency across projects
- ✅ Enables powerful search and filtering
- ✅ Captures organizational naming standards as reusable templates
- ✅ Provides live preview feedback
- ✅ Tracks template usage for analytics

**Next Steps:**
1. Review the 10+ seed templates in Reference Data Hub
2. Create your first relationship set using a template
3. Build custom templates for your organization's naming conventions
