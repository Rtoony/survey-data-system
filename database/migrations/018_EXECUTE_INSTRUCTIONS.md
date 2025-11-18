# Migration 018: Add project_id Columns to Drawing Tables

## Problem
DXF imports are completely broken because the `dxf_importer.py` code tries to INSERT with `project_id`, but these tables are missing the column:
- `drawing_text`
- `drawing_dimensions`
- `drawing_hatches`

## Solution
This migration adds the missing `project_id` column to all three tables.

## How to Execute This Migration

### Option 1: Using the Migration Script (Recommended)
If you have database credentials configured in your `.env` file:

```bash
python run_migration.py
```

### Option 2: Using psql Command Line
```bash
psql "$DATABASE_URL" -f database/migrations/018_add_project_id_to_drawing_tables.sql
```

### Option 3: Direct SQL Execution
Connect to your PostgreSQL database and run these commands:

```sql
-- Add project_id to drawing_text
ALTER TABLE drawing_text
ADD COLUMN project_id UUID;

-- Add project_id to drawing_dimensions
ALTER TABLE drawing_dimensions
ADD COLUMN project_id UUID;

-- Add project_id to drawing_hatches
ALTER TABLE drawing_hatches
ADD COLUMN project_id UUID;
```

### Option 4: Via Supabase SQL Editor
1. Log into your Supabase dashboard
2. Go to SQL Editor
3. Copy and paste the SQL from `018_add_project_id_to_drawing_tables.sql`
4. Click "Run"

## Verification

After running the migration, verify the columns were added:

```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name IN ('drawing_text', 'drawing_dimensions', 'drawing_hatches')
  AND column_name = 'project_id'
ORDER BY table_name;
```

You should see 3 rows returned:
```
 column_name | data_type
-------------+-----------
 project_id  | uuid
 project_id  | uuid
 project_id  | uuid
```

Or use the verification script:
```bash
python database/migrations/verify_018.py
```

## Expected Result
After this migration, DXF imports will work correctly because the INSERT statements in `dxf_importer.py` will match the database schema.
