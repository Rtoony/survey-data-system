-- Add missing project_id column to utility_service_connections
-- Fixes error: column "project_id" of relation "utility_service_connections" does not exist

BEGIN;

-- Add project_id column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'utility_service_connections'
        AND column_name = 'project_id'
    ) THEN
        ALTER TABLE utility_service_connections
        ADD COLUMN project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE;

        -- Create index for performance
        CREATE INDEX idx_utility_service_connections_project
        ON utility_service_connections(project_id);

        RAISE NOTICE 'Added project_id column to utility_service_connections';
    ELSE
        RAISE NOTICE 'project_id column already exists in utility_service_connections';
    END IF;
END $$;

COMMIT;
