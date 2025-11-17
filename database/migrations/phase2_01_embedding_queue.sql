-- Phase 2: Embedding Queue System
-- This creates the infrastructure for automatic embedding generation

-- ============================================================================
-- EMBEDDING GENERATION QUEUE
-- ============================================================================

-- Queue table for async embedding generation
CREATE TABLE IF NOT EXISTS embedding_generation_queue (
    queue_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES standards_entities(entity_id) ON DELETE CASCADE,
    entity_type VARCHAR(100) NOT NULL,
    text_to_embed TEXT NOT NULL,
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('high', 'normal', 'low')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    attempt_count INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    UNIQUE(entity_id)  -- Prevent duplicates
);

-- Indexes for queue processing
CREATE INDEX IF NOT EXISTS idx_queue_status_priority
    ON embedding_generation_queue(status, priority, created_at)
    WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_queue_entity
    ON embedding_generation_queue(entity_id);

COMMENT ON TABLE embedding_generation_queue IS
    'Queue for async embedding generation. Populated by triggers on entity insert/update.';

-- ============================================================================
-- TRIGGER FUNCTION: Queue embeddings on entity creation/update
-- ============================================================================

CREATE OR REPLACE FUNCTION trigger_queue_embedding()
RETURNS TRIGGER AS $$
BEGIN
    -- Only queue if entity_id exists and text is non-empty
    IF NEW.entity_id IS NOT NULL AND
       (NEW.description IS NOT NULL OR NEW.name IS NOT NULL) THEN

        -- Insert into queue (ignore if already exists)
        INSERT INTO embedding_generation_queue (
            entity_id,
            entity_type,
            text_to_embed,
            priority
        ) VALUES (
            NEW.entity_id,
            TG_TABLE_NAME,
            COALESCE(NEW.description, '') || ' ' || COALESCE(NEW.name, ''),
            CASE
                WHEN TG_TABLE_NAME IN ('layer_standards', 'block_definitions') THEN 'high'
                ELSE 'normal'
            END
        )
        ON CONFLICT (entity_id) DO UPDATE SET
            text_to_embed = EXCLUDED.text_to_embed,
            status = CASE
                WHEN embedding_generation_queue.status = 'failed' THEN 'pending'
                ELSE embedding_generation_queue.status
            END;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION trigger_queue_embedding IS
    'Trigger function to queue entities for embedding generation';

-- ============================================================================
-- APPLY TRIGGERS TO TABLES
-- ============================================================================

-- Layer standards
DROP TRIGGER IF EXISTS layer_standards_embedding_queue ON layer_standards;
CREATE TRIGGER layer_standards_embedding_queue
    AFTER INSERT OR UPDATE ON layer_standards
    FOR EACH ROW
    WHEN (NEW.entity_id IS NOT NULL)
    EXECUTE FUNCTION trigger_queue_embedding();

-- Block definitions
DROP TRIGGER IF EXISTS block_definitions_embedding_queue ON block_definitions;
CREATE TRIGGER block_definitions_embedding_queue
    AFTER INSERT OR UPDATE ON block_definitions
    FOR EACH ROW
    WHEN (NEW.entity_id IS NOT NULL)
    EXECUTE FUNCTION trigger_queue_embedding();

-- Detail standards
DROP TRIGGER IF EXISTS detail_standards_embedding_queue ON detail_standards;
CREATE TRIGGER detail_standards_embedding_queue
    AFTER INSERT OR UPDATE ON detail_standards
    FOR EACH ROW
    WHEN (NEW.entity_id IS NOT NULL)
    EXECUTE FUNCTION trigger_queue_embedding();

-- Add more triggers for other entity types as needed...

-- ============================================================================
-- UTILITY FUNCTIONS
-- ============================================================================

-- Get queue statistics
CREATE OR REPLACE FUNCTION get_queue_stats()
RETURNS TABLE(
    status VARCHAR,
    priority VARCHAR,
    count BIGINT,
    oldest_timestamp TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        q.status,
        q.priority,
        COUNT(*) as count,
        MIN(q.created_at) as oldest_timestamp
    FROM embedding_generation_queue q
    GROUP BY q.status, q.priority
    ORDER BY q.status, q.priority;
END;
$$ LANGUAGE plpgsql;

-- Clean up old completed/failed items
CREATE OR REPLACE FUNCTION cleanup_embedding_queue(days_old INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM embedding_generation_queue
    WHERE status IN ('completed', 'failed')
      AND processed_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * days_old;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- QUALITY SCORE AUTO-UPDATE TRIGGERS
-- ============================================================================

-- Update quality score when embedding is added
CREATE OR REPLACE FUNCTION update_quality_on_embedding()
RETURNS TRIGGER AS $$
DECLARE
    relationship_count INTEGER;
    filled_fields INTEGER;
BEGIN
    -- Count relationships
    SELECT COUNT(*) INTO relationship_count
    FROM entity_relationships
    WHERE subject_entity_id = NEW.entity_id
       OR object_entity_id = NEW.entity_id;

    -- Update quality score
    UPDATE standards_entities
    SET quality_score = compute_quality_score(
        5,   -- Assume 5 filled fields (simplified)
        10,  -- Total required fields
        TRUE,  -- has_embedding (we're in the trigger)
        relationship_count > 0
    ),
    updated_at = CURRENT_TIMESTAMP
    WHERE entity_id = NEW.entity_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS embedding_quality_update ON entity_embeddings;
CREATE TRIGGER embedding_quality_update
    AFTER INSERT OR UPDATE ON entity_embeddings
    FOR EACH ROW
    WHEN (NEW.is_current = TRUE)
    EXECUTE FUNCTION update_quality_on_embedding();

-- Update quality score when relationship is added
CREATE OR REPLACE FUNCTION update_quality_on_relationship()
RETURNS TRIGGER AS $$
BEGIN
    -- Update both subject and object entities
    UPDATE standards_entities
    SET quality_score = compute_quality_score(
        5,
        10,
        EXISTS(SELECT 1 FROM entity_embeddings
               WHERE entity_id = standards_entities.entity_id
               AND is_current = TRUE),
        TRUE  -- has_relationships (we're adding one)
    ),
    updated_at = CURRENT_TIMESTAMP
    WHERE entity_id IN (NEW.subject_entity_id, NEW.object_entity_id);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS relationship_quality_update ON entity_relationships;
CREATE TRIGGER relationship_quality_update
    AFTER INSERT OR UPDATE ON entity_relationships
    FOR EACH ROW
    EXECUTE FUNCTION update_quality_on_relationship();

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Phase 2 Migration Complete!';
    RAISE NOTICE '';
    RAISE NOTICE 'Created:';
    RAISE NOTICE '  - embedding_generation_queue table';
    RAISE NOTICE '  - trigger_queue_embedding() function';
    RAISE NOTICE '  - Triggers on layer_standards, block_definitions, detail_standards';
    RAISE NOTICE '  - Quality score auto-update triggers';
    RAISE NOTICE '  - Queue statistics and cleanup functions';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '  1. Start background worker: python workers/embedding_worker.py';
    RAISE NOTICE '  2. Test by inserting a layer: INSERT INTO layer_standards (name, description) VALUES (...)';
    RAISE NOTICE '  3. Check queue: SELECT * FROM get_queue_stats();';
END $$;
