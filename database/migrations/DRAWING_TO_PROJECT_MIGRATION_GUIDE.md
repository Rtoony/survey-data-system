# Drawing → Project Migration Guide

## Overview

This guide walks you through completing the migration from a "drawings" concept to a "projects" concept in your survey data system. The migration is split into three phases that must be executed in order.

## Background

Your application was originally architected as: **Projects → Drawings → Entities**

The new architecture is: **Projects → Entities**

The code has already been updated to use `project_id` everywhere, but the database schema still contains:
- Missing `project_id` columns in some tables (causing DXF import failures)
- Obsolete `drawing_id` columns that are no longer used
- Obsolete drawing-related tracking tables

## Migration Phases

### Phase 1: Add Missing project_id Columns (Migration 018)
**Status:** CRITICAL - DXF imports are broken without this!

**What it does:**
- Adds `project_id` column to 4 tables that are missing it:
  - `drawing_text`
  - `drawing_dimensions`
  - `drawing_hatches`
  - `block_inserts`

**Files:**
- Migration: `database/migrations/018_add_project_id_to_drawing_tables.sql`
- Instructions: `database/migrations/018_EXECUTE_INSTRUCTIONS.md`
- Verification: `database/migrations/verify_018.py`

### Phase 2: Remove All drawing_id Columns (Migration 019)
**Status:** Should run after Phase 1 is tested and working

**What it does:**
- Removes `drawing_id` column from 24+ tables including:
  - Core DXF tables (drawing_text, drawing_entities, etc.)
  - Intelligent object tables (utility_lines, survey_points, etc.)
  - Reference tables (project_standard_overrides, etc.)

**Files:**
- Migration: `database/migrations/019_remove_drawing_id_columns.sql`
- Verification: `database/migrations/verify_019.py`

### Phase 3: Drop Obsolete Drawing Tables (Migration 020)
**Status:** Final cleanup - run after Phase 2 is complete

**What it does:**
- Drops obsolete tracking tables:
  - `drawing_materials`
  - `drawing_references`
  - `drawings` (if not already dropped by migration 012)

**Files:**
- Migration: `database/migrations/020_drop_obsolete_drawing_tables.sql`
- Verification: `database/migrations/verify_020.py`

## Execution Instructions

### Prerequisites

1. **Backup your database:**
   ```bash
   pg_dump "$DATABASE_URL" > backup_before_drawing_migration_$(date +%Y%m%d).sql
   ```

2. **Ensure database credentials are configured:**
   ```bash
   # Check that .env file exists with database credentials
   cat .env | grep DB_HOST
   ```

3. **Install dependencies (if not already installed):**
   ```bash
   pip install psycopg2-binary python-dotenv
   ```

### Method 1: Using psql (Recommended for Production)

```bash
# Phase 1: Add project_id columns
psql "$DATABASE_URL" -f database/migrations/018_add_project_id_to_drawing_tables.sql

# Verify Phase 1
python database/migrations/verify_018.py

# TEST DXF IMPORT HERE - Make sure it works before continuing!

# Phase 2: Remove drawing_id columns
psql "$DATABASE_URL" -f database/migrations/019_remove_drawing_id_columns.sql

# Verify Phase 2
python database/migrations/verify_019.py

# Phase 3: Drop obsolete tables
psql "$DATABASE_URL" -f database/migrations/020_drop_obsolete_drawing_tables.sql

# Verify Phase 3
python database/migrations/verify_020.py
```

### Method 2: Via Supabase SQL Editor

1. Log into your Supabase dashboard
2. Go to SQL Editor
3. Copy and paste the SQL from each migration file
4. Run each migration one at a time
5. Verify each step using the verification scripts or manual queries

### Method 3: Using Python Migration Runner

```bash
# Phase 1
python run_migration.py  # Runs 018 by default

# Verify
python database/migrations/verify_018.py

# TEST DXF IMPORT

# Phase 2
# Update run_migration.py to point to 019, then:
python run_migration.py

# Verify
python database/migrations/verify_019.py

# Phase 3
# Update run_migration.py to point to 020, then:
python run_migration.py

# Verify
python database/migrations/verify_020.py
```

## Testing Between Phases

### After Phase 1: Test DXF Import

**This is the most critical test!** DXF imports should work after Phase 1.

1. Navigate to your application's DXF import page
2. Upload a test DXF file
3. Check server logs for success messages
4. Verify entities appear in the database:
   ```sql
   SELECT COUNT(*) FROM drawing_text WHERE project_id IS NOT NULL;
   SELECT COUNT(*) FROM drawing_dimensions WHERE project_id IS NOT NULL;
   SELECT COUNT(*) FROM drawing_hatches WHERE project_id IS NOT NULL;
   SELECT COUNT(*) FROM block_inserts WHERE project_id IS NOT NULL;
   ```

**DO NOT PROCEED** to Phase 2 if DXF imports are still failing!

### After Phase 2: Verify No drawing_id Columns

```sql
-- Should return 0 rows
SELECT table_name
FROM information_schema.columns
WHERE column_name = 'drawing_id'
  AND table_schema = 'public'
  AND table_name NOT LIKE 'pg_%';
```

### After Phase 3: Verify Obsolete Tables Dropped

```sql
-- Should return 0 rows
SELECT table_name
FROM information_schema.tables
WHERE table_name IN ('drawing_materials', 'drawing_references', 'drawings')
  AND table_schema = 'public';
```

## Manual Verification Queries

### Check project_id columns (after Phase 1):
```sql
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE column_name = 'project_id'
  AND table_schema = 'public'
ORDER BY table_name;
```

### Check for remaining drawing_id columns (after Phase 2):
```sql
SELECT table_name, column_name
FROM information_schema.columns
WHERE column_name = 'drawing_id'
  AND table_schema = 'public'
  AND table_name NOT LIKE 'pg_%'
ORDER BY table_name;
```

### List all drawing-related tables (for reference):
```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name LIKE '%drawing%'
ORDER BY table_name;
```

## Troubleshooting

### Issue: Migration fails with "column already exists"

This means the migration was partially run before. You can either:
1. Check which columns exist and manually run the missing ALTER TABLE statements
2. Use `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` (already in migrations 019+)

### Issue: DXF import still fails after Phase 1

Check the error message carefully. Common issues:
- Database credentials not configured correctly
- Migration didn't actually run (check logs)
- Different table needs project_id (check error for table name)

### Issue: Cannot connect to database

Ensure `.env` file has correct credentials:
```bash
DB_HOST=your-project.supabase.co
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your-password-here
```

## Rollback Instructions

If you need to rollback:

### Rollback Phase 3:
```sql
-- Recreate tables from backup
-- (This is why you made a backup first!)
```

### Rollback Phase 2:
```sql
-- Re-add drawing_id columns
-- Example:
ALTER TABLE drawing_text ADD COLUMN drawing_id UUID;
-- Repeat for all tables...
```

### Rollback Phase 1:
```sql
-- Remove project_id columns
ALTER TABLE drawing_text DROP COLUMN project_id;
ALTER TABLE drawing_dimensions DROP COLUMN project_id;
ALTER TABLE drawing_hatches DROP COLUMN project_id;
ALTER TABLE block_inserts DROP COLUMN project_id;
```

## Success Criteria

After completing all three phases:

✅ All DXF imports work correctly
✅ No `drawing_id` columns exist in the database
✅ All entity tables use `project_id` exclusively
✅ Obsolete drawing tables are dropped
✅ Application functions normally

## Timeline

- **Phase 1:** 5 minutes (includes testing DXF import)
- **Phase 2:** 2 minutes
- **Phase 3:** 1 minute

**Total estimated time:** ~10 minutes

## Related Migrations

Previous related migrations that have already been run:
- Migration 011: Removed `drawing_id` from `layers` table
- Migration 012: Dropped `drawings` table (partial cleanup)

## Questions or Issues?

If you encounter any issues:
1. Check the error message carefully
2. Review the verification script output
3. Check database logs
4. Restore from backup if needed
5. Document the issue for future reference

---

**Last Updated:** 2025-11-18
**Migrations:** 018, 019, 020
**Status:** Ready for execution
