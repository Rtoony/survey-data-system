-- Phase 1 Schema Fix: Add Missing Columns to embedding_models
-- This migration adds columns that Phase 1 scripts expect but may be missing

-- Add cost tracking and token limit columns to embedding_models
ALTER TABLE embedding_models
  ADD COLUMN IF NOT EXISTS cost_per_1k_tokens NUMERIC(10, 6),
  ADD COLUMN IF NOT EXISTS max_input_tokens INTEGER;

-- Add helpful comment
COMMENT ON COLUMN embedding_models.cost_per_1k_tokens IS 'Cost in USD per 1,000 tokens for this embedding model';
COMMENT ON COLUMN embedding_models.max_input_tokens IS 'Maximum number of input tokens this model can process';

-- Optional: Set defaults for the OpenAI text-embedding-3-small model if it exists
-- This is what the Phase 1 script will try to insert
UPDATE embedding_models
SET
  cost_per_1k_tokens = 0.00002,  -- $0.02 per 1M tokens ($0.00002 per 1K tokens)
  max_input_tokens = 8191
WHERE provider = 'openai'
  AND model_name = 'text-embedding-3-small'
  AND cost_per_1k_tokens IS NULL;

-- Verify the columns were added
DO $$
DECLARE
    col_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO col_count
    FROM information_schema.columns
    WHERE table_name = 'embedding_models'
      AND column_name IN ('cost_per_1k_tokens', 'max_input_tokens');

    IF col_count = 2 THEN
        RAISE NOTICE '✓ Successfully added missing columns to embedding_models table';
    ELSE
        RAISE WARNING '⚠ Column addition may have failed. Expected 2 columns, found %', col_count;
    END IF;
END $$;

-- Display current schema for verification
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'embedding_models'
ORDER BY ordinal_position;
