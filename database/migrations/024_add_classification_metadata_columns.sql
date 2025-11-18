-- Migration 024: Add classification metadata columns to standards_entities
-- Purpose: Support intelligent DXF import with classification confidence tracking
-- Date: 2025-11-18

-- Add classification metadata columns to standards_entities table
ALTER TABLE standards_entities 
ADD COLUMN IF NOT EXISTS classification_state VARCHAR(50),
ADD COLUMN IF NOT EXISTS classification_confidence NUMERIC(3,2),
ADD COLUMN IF NOT EXISTS classification_metadata JSONB,
ADD COLUMN IF NOT EXISTS target_table VARCHAR(100),
ADD COLUMN IF NOT EXISTS target_id UUID,
ADD COLUMN IF NOT EXISTS project_id UUID;

-- Add check constraint for classification_state values
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'standards_entities_classification_state_check'
    ) THEN
        ALTER TABLE standards_entities 
        ADD CONSTRAINT standards_entities_classification_state_check 
        CHECK (classification_state IN ('auto_classified', 'needs_review', 'manually_classified', 'rejected'));
    END IF;
END $$;

-- Create index on classification_state for faster queries
CREATE INDEX IF NOT EXISTS idx_standards_entities_classification_state 
ON standards_entities(classification_state);

-- Create index on project_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_standards_entities_project_id 
ON standards_entities(project_id);

-- Add comments for documentation
COMMENT ON COLUMN standards_entities.classification_state IS 'Current classification state: auto_classified, needs_review, manually_classified, rejected';
COMMENT ON COLUMN standards_entities.classification_confidence IS 'Classification confidence score (0.00-1.00)';
COMMENT ON COLUMN standards_entities.classification_metadata IS 'Additional classification metadata including suggestions and spatial context';
COMMENT ON COLUMN standards_entities.target_table IS 'Target intelligent object table name';
COMMENT ON COLUMN standards_entities.target_id IS 'Target intelligent object ID';
COMMENT ON COLUMN standards_entities.project_id IS 'Associated project ID';
