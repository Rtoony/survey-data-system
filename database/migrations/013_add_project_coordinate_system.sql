-- Migration 013: Add Coordinate System Support to Projects
-- COORDINATE SYSTEM ARCHITECTURE OVERHAUL - PHASE 1: California Zones
--
-- Purpose: Add dynamic coordinate system selection to projects
-- - Each project gets a canonical coordinate system (default: EPSG:2226 for backward compatibility)
-- - Supports all 6 California State Plane zones
-- - Architecture scales to US-wide support later

-- Step 1: Add coordinate system ID to projects table
ALTER TABLE projects
ADD COLUMN default_coordinate_system_id UUID
REFERENCES coordinate_systems(system_id);

-- Step 2: Backfill existing projects to use EPSG:2226 (Zone 2)
-- This ensures backward compatibility - all existing projects default to Zone 2
UPDATE projects
SET default_coordinate_system_id = (
    SELECT system_id
    FROM coordinate_systems
    WHERE epsg_code = 'EPSG:2226'
    LIMIT 1
);

-- Step 3: Make it NOT NULL after backfill
-- This ensures every project MUST have a coordinate system
ALTER TABLE projects
ALTER COLUMN default_coordinate_system_id SET NOT NULL;

-- Step 4: Add helpful index for query performance
CREATE INDEX idx_projects_coordinate_system
ON projects(default_coordinate_system_id);

-- Step 5: Verify/Create the project_coordinate_systems table
-- This table allows projects to support MULTIPLE coordinate systems
-- (one primary, others for reference/import transformations)
CREATE TABLE IF NOT EXISTS project_coordinate_systems (
    mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    system_id UUID REFERENCES coordinate_systems(system_id),
    is_primary BOOLEAN DEFAULT FALSE,
    usage_type VARCHAR(100),  -- "Survey", "Design", "Construction", "Import", "Export"
    relationship_notes TEXT,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Step 6: Add indexes for project_coordinate_systems
CREATE INDEX IF NOT EXISTS idx_project_coordinate_systems_project
ON project_coordinate_systems(project_id);

CREATE INDEX IF NOT EXISTS idx_project_coordinate_systems_system
ON project_coordinate_systems(system_id);

CREATE INDEX IF NOT EXISTS idx_project_coordinate_systems_primary
ON project_coordinate_systems(project_id, is_primary)
WHERE is_primary = true;

-- Step 7: Add unique constraint to ensure only one primary CRS per project
CREATE UNIQUE INDEX IF NOT EXISTS idx_project_coordinate_systems_unique_primary
ON project_coordinate_systems(project_id)
WHERE is_primary = true;

-- Step 8: Add comment to document the schema change
COMMENT ON COLUMN projects.default_coordinate_system_id IS
'Primary coordinate reference system for this project. All imports/exports/transformations use this CRS unless explicitly overridden.';

COMMENT ON TABLE project_coordinate_systems IS
'Allows projects to reference multiple coordinate systems (e.g., one for survey data, another for construction, etc.). The is_primary flag indicates the canonical CRS.';

-- Step 9: Update the updated_at timestamp trigger
-- (Assumes you have a trigger function update_updated_at_column)
-- If the trigger doesn't exist, this will be ignored
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'update_updated_at_column') THEN
        DROP TRIGGER IF EXISTS update_project_coordinate_systems_updated_at ON project_coordinate_systems;
        CREATE TRIGGER update_project_coordinate_systems_updated_at
            BEFORE UPDATE ON project_coordinate_systems
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- Migration complete
-- All existing projects now default to EPSG:2226 (California State Plane Zone 2)
-- New projects can select from any of the 6 California zones during creation
