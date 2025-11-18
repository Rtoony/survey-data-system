-- Data Migration for Migration 030: Map projects.client_name to clients.client_id
-- This must run BEFORE adding FK constraints

-- Step 1: Add the client_id column (already in 030_convert_projects_client_to_fk.sql)
-- We're just doing the data migration here

-- Step 2: Map client_name VARCHAR to client_id INT
-- Since all client_name values are currently NULL, no mapping is needed
-- This script is for future reference if client_name had values

-- Example mapping logic (not needed now since all NULL):
-- UPDATE projects p
-- SET client_id = c.client_id
-- FROM clients c
-- WHERE p.client_name = c.client_name;

-- Step 3: Verify the migration
SELECT 
    'Projects with client_name but no client_id' as check_type,
    COUNT(*) as count
FROM projects
WHERE client_name IS NOT NULL 
  AND client_id IS NULL;

-- Step 4: Summary
SELECT 
    'Total projects' as metric,
    COUNT(*) as count
FROM projects

UNION ALL

SELECT 
    'Projects with client_id' as metric,
    COUNT(*) as count
FROM projects
WHERE client_id IS NOT NULL

UNION ALL

SELECT 
    'Projects with client_name' as metric,
    COUNT(*) as count
FROM projects
WHERE client_name IS NOT NULL;
