# Project Creation Fix - Investigation Report

## Problem Confirmed

After investigating the codebase, I can confirm the issue:

**Root Cause:** The `default_coordinate_system_id` column is missing from the `projects` table in your database.

### Evidence Found

1. **Code expects the column** (app.py:734-742):
   ```python
   INSERT INTO projects (
       project_name, client_name, project_number, description,
       default_coordinate_system_id, quality_score, tags, attributes
   )
   VALUES (%s, %s, %s, %s, %s, 0.5, '{}', '{}')
   ```

2. **Migration exists but wasn't run**:
   - File: `database/migrations/013_add_project_coordinate_system.sql`
   - This migration should have added the column, but it appears not to have been executed on your database

3. **Schema file shows expected state**:
   - `database/schema/complete_schema.sql` shows the column SHOULD exist
   - This represents the target state, not the current database state

## Solution

I've created a safe, idempotent SQL script that will fix the issue.

### Quick Fix (Recommended)

Run this command to fix the database:

```bash
psql $DATABASE_URL -f fix_project_creation.sql
```

**OR** if you're using Supabase or have credentials in environment variables:

```bash
psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require" -f fix_project_creation.sql
```

### Manual Fix (Alternative)

If you prefer to run the SQL directly in your database console:

```sql
-- Add the missing column (safe to run - checks if exists first)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'projects'
        AND column_name = 'default_coordinate_system_id'
    ) THEN
        ALTER TABLE projects
        ADD COLUMN default_coordinate_system_id UUID
        REFERENCES coordinate_systems(system_id)
        ON DELETE SET NULL;

        RAISE NOTICE 'Column added successfully';
    ELSE
        RAISE NOTICE 'Column already exists';
    END IF;
END $$;
```

## Verification

After running the fix, verify it worked:

```sql
-- Check the column exists
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'projects'
AND column_name = 'default_coordinate_system_id';
```

Expected result:
- `column_name`: default_coordinate_system_id
- `data_type`: uuid
- `is_nullable`: YES

## Why This Column Is Needed

The application was recently refactored to support multiple California State Plane coordinate systems (EPSG:2225 through EPSG:2230). Previously, it only supported one system. This column stores which coordinate system is the default for each project.

### Related Files (Already Correct - No Changes Needed)
- `app.py` lines 717-756 (project creation endpoint)
- `app.py` lines 905-949 (project update endpoint)
- `services/coordinate_system_service.py`

## Safety Notes

✅ **Safe to run multiple times** - The script checks if the column exists first
✅ **Non-destructive** - Only adds a column, doesn't modify existing data
✅ **Nullable** - Existing projects won't break (NULL is allowed)
✅ **Foreign key constraint** - Ensures data integrity with coordinate_systems table

## Alternative: Run the Full Migration

If you want to run the complete migration that also backfills existing projects:

```bash
psql $DATABASE_URL -f database/migrations/013_add_project_coordinate_system.sql
```

**NOTE:** This will set the column to NOT NULL and backfill all existing projects with EPSG:2226 (California State Plane Zone 2). Only use this if you want existing projects to have a default coordinate system.

## Next Steps

1. Run the fix script: `psql $DATABASE_URL -f fix_project_creation.sql`
2. Verify the column was added (check the output)
3. Test creating a new project through your application
4. If successful, you can delete this instruction file
