-- Migration 016: Add Projects Client FK Constraint
-- This fixes Critical Violation #1 from Truth-Driven Architecture Audit Report
-- Date: 2025-11-18
--
-- Purpose: Enforce truth-driven architecture by adding FK constraint
-- from projects.client_id to clients.client_id
-- This eliminates free-text client_name entry in favor of controlled vocabulary

-- Step 1: Add client_id column to projects if it doesn't exist
ALTER TABLE projects
ADD COLUMN IF NOT EXISTS client_id INTEGER;

-- Step 2: Create an index on client_id for performance
CREATE INDEX IF NOT EXISTS idx_projects_client_id
ON projects(client_id);

-- Step 3: Attempt to map existing client_name values to client_id
-- This performs fuzzy matching (case-insensitive, trimmed)
UPDATE projects p
SET client_id = (
    SELECT c.client_id
    FROM clients c
    WHERE LOWER(TRIM(p.client_name)) = LOWER(TRIM(c.client_name))
    LIMIT 1
)
WHERE p.client_id IS NULL
  AND p.client_name IS NOT NULL
  AND p.client_name != '';

-- Step 4: Report unmapped client names that need manual review
DO $$
DECLARE
    unmapped_count INT;
    unmapped_names TEXT;
BEGIN
    SELECT COUNT(DISTINCT client_name) INTO unmapped_count
    FROM projects
    WHERE client_id IS NULL
      AND client_name IS NOT NULL
      AND client_name != '';

    IF unmapped_count > 0 THEN
        RAISE WARNING 'Found % distinct client_name values in projects not mapped to clients table', unmapped_count;
        RAISE NOTICE 'Run this query to see unmapped client names:';
        RAISE NOTICE 'SELECT DISTINCT client_name, COUNT(*) as project_count FROM projects WHERE client_id IS NULL AND client_name IS NOT NULL AND client_name != '''' GROUP BY client_name ORDER BY project_count DESC;';
        RAISE NOTICE '';
        RAISE NOTICE 'To fix: Add missing clients to the clients table via /data-manager/clients, then re-run this migration.';
    ELSE
        RAISE NOTICE 'SUCCESS: All existing client_name values successfully mapped to client_id';
    END IF;
END $$;

-- Step 5: Add FK constraint to projects.client_id
-- NOTE: This allows NULL values (projects without clients are OK for now)
-- ON DELETE SET NULL: If a client is deleted, set project's client_id to NULL (preserve project)
-- ON UPDATE CASCADE: If client_id changes, update all project references
ALTER TABLE projects
DROP CONSTRAINT IF EXISTS fk_projects_client;

ALTER TABLE projects
ADD CONSTRAINT fk_projects_client
FOREIGN KEY (client_id) REFERENCES clients(client_id)
ON DELETE SET NULL
ON UPDATE CASCADE;

-- Step 6: Add comments to document the new architecture
COMMENT ON COLUMN projects.client_id IS 'Client organization ID - must match clients.client_id. Replaces free-text client_name field to enforce truth-driven architecture.';
COMMENT ON COLUMN projects.client_name IS 'DEPRECATED: Free-text client name field. Use client_id instead. This column will be removed in a future migration after validation.';

-- Step 7: Create a view for backward compatibility
-- This allows existing queries using client_name to continue working
CREATE OR REPLACE VIEW projects_with_client_name AS
SELECT
    p.*,
    COALESCE(c.client_name, p.client_name) as resolved_client_name
FROM projects p
LEFT JOIN clients c ON p.client_id = c.client_id;

COMMENT ON VIEW projects_with_client_name IS 'Compatibility view that resolves client_id to client_name. Use this during migration period.';

-- Step 8: Verify constraint was added
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_projects_client'
          AND table_name = 'projects'
    ) THEN
        RAISE NOTICE 'SUCCESS: FK constraint fk_projects_client added to projects table';
    ELSE
        RAISE WARNING 'FAILED: FK constraint fk_projects_client was not added';
    END IF;
END $$;

-- Step 9: Report statistics
DO $$
DECLARE
    total_projects INT;
    projects_with_client INT;
    projects_without_client INT;
BEGIN
    SELECT COUNT(*) INTO total_projects FROM projects;
    SELECT COUNT(*) INTO projects_with_client FROM projects WHERE client_id IS NOT NULL;
    SELECT COUNT(*) INTO projects_without_client FROM projects WHERE client_id IS NULL;

    RAISE NOTICE '';
    RAISE NOTICE '=== Migration 016 Statistics ===';
    RAISE NOTICE 'Total projects: %', total_projects;
    RAISE NOTICE 'Projects with client_id: % (%%)', projects_with_client,
                 CASE WHEN total_projects > 0 THEN ROUND(projects_with_client::NUMERIC / total_projects * 100, 1) ELSE 0 END;
    RAISE NOTICE 'Projects without client_id: % (%%)', projects_without_client,
                 CASE WHEN total_projects > 0 THEN ROUND(projects_without_client::NUMERIC / total_projects * 100, 1) ELSE 0 END;
    RAISE NOTICE '================================';
END $$;

-- Migration complete
-- Next steps:
-- 1. Review unmapped client names and add missing clients to clients table
-- 2. Verify projects display correctly with new client dropdown
-- 3. After validation period, run migration to drop client_name column
