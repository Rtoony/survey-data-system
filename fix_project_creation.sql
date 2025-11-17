-- Fix for Project Creation Issue
-- This script adds the missing default_coordinate_system_id column to the projects table
--
-- Problem: The application cannot create projects because the column doesn't exist in the database
-- Solution: Add the missing column with proper foreign key constraint
--
-- SAFE TO RUN MULTIPLE TIMES - Script is idempotent (checks if column exists first)

-- Step 1: Check if column already exists and add it if missing
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'projects'
        AND column_name = 'default_coordinate_system_id'
    ) THEN
        -- Add the column
        ALTER TABLE projects
        ADD COLUMN default_coordinate_system_id UUID
        REFERENCES coordinate_systems(system_id)
        ON DELETE SET NULL;

        RAISE NOTICE 'Column default_coordinate_system_id added to projects table';
    ELSE
        RAISE NOTICE 'Column default_coordinate_system_id already exists in projects table';
    END IF;
END $$;

-- Step 2: Verify the column was added successfully
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'projects'
AND column_name = 'default_coordinate_system_id';

-- Step 3: Show the coordinate systems available for reference
SELECT
    system_id,
    epsg_code,
    system_name,
    region,
    zone_number
FROM coordinate_systems
WHERE is_active = true
ORDER BY zone_number;

-- Expected output after running this script:
-- 1. A notice message confirming the column was added or already exists
-- 2. Column details showing:
--    - column_name: default_coordinate_system_id
--    - data_type: uuid
--    - is_nullable: YES
-- 3. List of available coordinate systems (should include EPSG:2226 as default)
