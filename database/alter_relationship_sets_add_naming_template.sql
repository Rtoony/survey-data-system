-- ============================================================================
-- ALTER TABLE: Add naming_template_id to project_relationship_sets
-- 
-- Purpose: Link relationship sets to naming templates for truth-driven naming
-- ============================================================================

-- Add naming_template_id column
ALTER TABLE project_relationship_sets
ADD COLUMN IF NOT EXISTS naming_template_id UUID
REFERENCES relationship_set_naming_templates(template_id) ON DELETE SET NULL;

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_relationship_sets_naming_template
ON project_relationship_sets(naming_template_id);

-- Add comment
COMMENT ON COLUMN project_relationship_sets.naming_template_id IS 'References the naming template used to generate set_name and set_code (Truth-Driven Architecture)';
