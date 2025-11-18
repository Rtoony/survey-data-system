-- Migration 026: Add missing columns to standards_entities table
-- These columns are required for DXF import and intelligent object classification
-- but may be missing if the database was created from an older schema

-- Add classification_state column if it doesn't exist
ALTER TABLE standards_entities
ADD COLUMN IF NOT EXISTS classification_state VARCHAR(50) DEFAULT 'auto_classified';

-- Add classification_confidence column if it doesn't exist
ALTER TABLE standards_entities
ADD COLUMN IF NOT EXISTS classification_confidence NUMERIC(4,3);

-- Add classification_metadata column if it doesn't exist
ALTER TABLE standards_entities
ADD COLUMN IF NOT EXISTS classification_metadata JSONB DEFAULT '{}'::jsonb;

-- Add target_table column if it doesn't exist
ALTER TABLE standards_entities
ADD COLUMN IF NOT EXISTS target_table VARCHAR(100);

-- Add target_id column if it doesn't exist
ALTER TABLE standards_entities
ADD COLUMN IF NOT EXISTS target_id UUID;

-- Add project_id column if it doesn't exist
ALTER TABLE standards_entities
ADD COLUMN IF NOT EXISTS project_id UUID;

-- Add comments to document the purpose of these columns
COMMENT ON COLUMN standards_entities.classification_state IS
    'Classification status: auto_classified, needs_review, user_classified, validated';

COMMENT ON COLUMN standards_entities.classification_confidence IS
    'ML confidence score for the classification (0.000-1.000)';

COMMENT ON COLUMN standards_entities.classification_metadata IS
    'Stores ML suggestions, spatial context, and reclassification history';

COMMENT ON COLUMN standards_entities.target_table IS
    'The target table where this entity maps to';

COMMENT ON COLUMN standards_entities.target_id IS
    'The ID of the record in the target table';

COMMENT ON COLUMN standards_entities.project_id IS
    'Foreign key to projects table for project-scoped entities';
