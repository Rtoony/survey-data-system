# Migration 019: Remove All drawing_id Columns

## Problem
After migrating to the new architecture (Projects → Entities), many tables still have `drawing_id` columns that are no longer used. These columns:
- Are always NULL (not used by the code)
- Create confusion about the data model
- Take up unnecessary space
- May cause future bugs if developers accidentally use them

## Solution
This migration removes the `drawing_id` column from all tables, completing the migration to project_id-only architecture.

## Prerequisites

**CRITICAL:** Run migration 018 first!

Migration 018 adds `project_id` columns to tables that need them. If you run 019 before 018, you'll lose the drawing_id column without having project_id in place.

## What This Migration Does

Removes `drawing_id` column from 24+ tables across three categories:

### Core DXF Tables (7 tables)
- drawing_text
- drawing_dimensions
- drawing_hatches
- drawing_entities
- block_inserts
- layers (if not already removed by migration 011)
- dxf_entity_links

### Intelligent Object Tables (13 tables)
- utility_lines
- utility_structures
- survey_points
- survey_line_segments
- survey_observations
- survey_sequences
- site_trees
- surface_features
- surface_models
- parcels
- easements
- right_of_way
- grading_limits

### Reference Tables (3 tables)
- project_standard_overrides
- sheet_drawing_assignments
- sheet_note_assignments

## How to Execute This Migration

### Option 1: Using psql Command Line (Recommended)
```bash
psql "$DATABASE_URL" -f database/migrations/019_remove_drawing_id_columns.sql
```

### Option 2: Via Supabase SQL Editor
1. Log into your Supabase dashboard
2. Go to SQL Editor
3. Copy and paste the SQL from `019_remove_drawing_id_columns.sql`
4. Click "Run"

### Option 3: Using Python Migration Runner
Update `run_migration.py` to point to migration 019:
```python
migration_file = 'database/migrations/019_remove_drawing_id_columns.sql'
```

Then run:
```bash
python run_migration.py
```

## Verification

### Automated Verification
```bash
python database/migrations/verify_019.py
```

### Manual Verification
After running the migration, verify no drawing_id columns remain:

```sql
SELECT table_name, column_name
FROM information_schema.columns
WHERE column_name = 'drawing_id'
  AND table_schema = 'public'
  AND table_name NOT LIKE 'pg_%'
ORDER BY table_name;
```

**Expected result:** 0 rows (no drawing_id columns found)

## Safety Features

The migration includes:
- `DROP COLUMN IF EXISTS` - won't fail if column doesn't exist
- Validation checks before execution
- Comprehensive verification at the end
- Transaction wrapping (BEGIN/COMMIT) for atomicity

## Expected Result

After this migration:
- ✅ No tables have `drawing_id` column
- ✅ All entity tables use `project_id` exclusively
- ✅ Database schema matches the code expectations
- ✅ No breaking changes (drawing_id was already unused)

## Next Steps

After verifying this migration succeeds, proceed to:
- **Migration 020:** Drop obsolete drawing tables
