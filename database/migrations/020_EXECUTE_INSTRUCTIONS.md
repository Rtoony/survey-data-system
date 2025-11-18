# Migration 020: Drop Obsolete Drawing Tables

## Problem
Even though the application has migrated away from the "drawings" concept, several drawing-related tables still exist:
- `drawing_materials` - Tracked materials used in specific drawings
- `drawing_references` - Tracked reference relationships between drawings
- `drawings` - Main drawings table (may have been partially removed in migration 012)

These tables:
- Are no longer referenced by the code
- Contain obsolete data from the old architecture
- Take up database space
- Create confusion about the current data model

## Solution
This migration drops all obsolete drawing-related tables, completing the cleanup of the drawing → project migration.

## Prerequisites

**CRITICAL:** Run migrations 018 and 019 first!

- Migration 018: Adds project_id to necessary tables
- Migration 019: Removes all drawing_id columns

If you run this migration first, you'll lose the obsolete tables but still have drawing_id columns scattered throughout the database.

## What This Migration Does

Drops 3 obsolete tables:
1. `drawing_materials` - No longer needed (materials are tracked at project level)
2. `drawing_references` - No longer needed (no drawing-to-drawing relationships)
3. `drawings` - No longer needed (may have been dropped in migration 012)

All drops use `DROP TABLE IF EXISTS CASCADE` for safety.

## How to Execute This Migration

### Option 1: Using psql Command Line (Recommended)
```bash
psql "$DATABASE_URL" -f database/migrations/020_drop_obsolete_drawing_tables.sql
```

### Option 2: Via Supabase SQL Editor
1. Log into your Supabase dashboard
2. Go to SQL Editor
3. Copy and paste the SQL from `020_drop_obsolete_drawing_tables.sql`
4. Click "Run"

### Option 3: Using Python Migration Runner
Update `run_migration.py` to point to migration 020:
```python
migration_file = 'database/migrations/020_drop_obsolete_drawing_tables.sql'
```

Then run:
```bash
python run_migration.py
```

## Verification

### Automated Verification
```bash
python database/migrations/verify_020.py
```

This will check:
- ✅ All 3 obsolete tables are dropped
- ✅ No drawing_id columns exist (from migration 019)
- ✅ All 4 core DXF tables have project_id (from migration 018)
- ℹ️ Lists remaining tables with "drawing" in the name (entity tables are OK)

### Manual Verification
After running the migration, verify the obsolete tables are gone:

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_name IN ('drawing_materials', 'drawing_references', 'drawings')
  AND table_schema = 'public';
```

**Expected result:** 0 rows (no obsolete tables found)

## Data Impact

### Tables Being Dropped

**drawing_materials:**
- Purpose: Tracked which materials were used in each drawing
- Why obsolete: Materials are now tracked at project level, not drawing level

**drawing_references:**
- Purpose: Tracked references between drawings (e.g., detail drawings referenced from plan drawings)
- Why obsolete: No more drawing-to-drawing relationships in new architecture

**drawings:**
- Purpose: Main table for drawings (metadata, file paths, etc.)
- Why obsolete: DXF files are imported directly to projects, no intermediate drawing entity
- Note: May have been dropped already in migration 012

## Safety Features

The migration includes:
- `DROP TABLE IF EXISTS` - won't fail if table doesn't exist
- `CASCADE` - automatically drops dependent objects
- Data count checks before dropping (logs warnings if tables contain data)
- Comprehensive verification at the end
- Transaction wrapping (BEGIN/COMMIT) for atomicity

## Expected Result

After this migration:
- ✅ Obsolete drawing tables are removed
- ✅ Database schema is clean and matches current architecture
- ✅ No breaking changes (these tables were already unused)
- ✅ Disk space reclaimed

## Impact on Remaining Tables

Tables that will **remain** (these are still used):
- `drawing_text` - DXF text entities (project-level, not drawing-level)
- `drawing_dimensions` - DXF dimension entities
- `drawing_entities` - Core DXF entities
- `drawing_hatches` - DXF hatch patterns
- All other entity tables

These tables have "drawing" in their name because they represent drawing entities (lines, text, etc. from DXF files), but they are now associated with projects, not drawings.

## Complete Migration Summary

After running all three migrations (018, 019, 020):

### Migration 018 (Phase 1)
✅ Added `project_id` to 4 tables

### Migration 019 (Phase 2)
✅ Removed `drawing_id` from 24+ tables

### Migration 020 (Phase 3)
✅ Dropped 3 obsolete drawing tables

### Final State
- Architecture: Projects → Entities (no intermediate "drawings")
- All entity tables use `project_id`
- No `drawing_id` columns anywhere
- No obsolete drawing metadata tables
- DXF imports work correctly
- Application fully migrated to new architecture

## Rollback

To rollback this migration, you would need to:
1. Restore the tables from your pre-migration backup
2. Restore any data they contained

**This is why you should backup before running migrations!**

## Next Steps

After this migration:
1. Run the verification script to confirm success
2. Test your application thoroughly
3. Monitor for any issues
4. Document the completion of the drawing → project migration

🎉 **Migration complete! Your application is now fully migrated to the Projects → Entities architecture.**
