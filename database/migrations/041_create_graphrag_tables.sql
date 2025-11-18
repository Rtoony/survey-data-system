-- Migration 041: Create GraphRAG Supporting Tables
-- Purpose: Add tables for embedding job tracking, query caching, and quality history
-- Author: AI Agent Toolkit
-- Date: 2025-11-18

-- ============================================================================
-- EMBEDDING JOB TRACKING
-- ============================================================================

-- Track embedding generation jobs for monitoring and debugging
CREATE TABLE IF NOT EXISTS embedding_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL,
    entity_count INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    model_id UUID REFERENCES embedding_models(model_id),
    model_version VARCHAR(50),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER,
    tokens_used INTEGER DEFAULT 0,
    cost_usd DECIMAL(10,4) DEFAULT 0.0000,
    error_message TEXT,
    result_summary JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID,
    CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    CONSTRAINT valid_entity_count CHECK (entity_count >= 0),
    CONSTRAINT valid_duration CHECK (duration_seconds IS NULL OR duration_seconds >= 0),
    CONSTRAINT valid_tokens CHECK (tokens_used >= 0),
    CONSTRAINT valid_cost CHECK (cost_usd >= 0)
);

-- Index for querying jobs by status and entity type
CREATE INDEX idx_embedding_jobs_status ON embedding_jobs(status);
CREATE INDEX idx_embedding_jobs_entity_type ON embedding_jobs(entity_type);
CREATE INDEX idx_embedding_jobs_created_at ON embedding_jobs(created_at DESC);

-- Comments
COMMENT ON TABLE embedding_jobs IS 'Tracks batch embedding generation jobs with cost and performance metrics';
COMMENT ON COLUMN embedding_jobs.job_id IS 'Unique identifier for the embedding job';
COMMENT ON COLUMN embedding_jobs.entity_type IS 'Type of entities being embedded (e.g., survey_point, utility_structure)';
COMMENT ON COLUMN embedding_jobs.entity_count IS 'Number of entities in this job';
COMMENT ON COLUMN embedding_jobs.status IS 'Job status: pending, running, completed, failed, cancelled';
COMMENT ON COLUMN embedding_jobs.result_summary IS 'JSON summary with stats: {success_count, failure_count, skipped_count, entities: [...]}';

-- ============================================================================
-- AI QUERY CACHING
-- ============================================================================

-- Cache results of natural language queries for performance
CREATE TABLE IF NOT EXISTS ai_query_cache (
    cache_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_hash VARCHAR(64) UNIQUE NOT NULL,
    query_text TEXT NOT NULL,
    query_type VARCHAR(50),
    result_json JSONB NOT NULL,
    entity_count INTEGER,
    relationship_count INTEGER,
    execution_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    last_accessed_at TIMESTAMP DEFAULT NOW(),
    hit_count INTEGER DEFAULT 0,
    expires_at TIMESTAMP,
    is_valid BOOLEAN DEFAULT TRUE,
    invalidation_reason TEXT,
    CONSTRAINT valid_hit_count CHECK (hit_count >= 0),
    CONSTRAINT valid_execution_time CHECK (execution_time_ms IS NULL OR execution_time_ms >= 0),
    CONSTRAINT valid_entity_count CHECK (entity_count IS NULL OR entity_count >= 0)
);

-- Indexes for cache lookup and cleanup
CREATE INDEX idx_ai_query_cache_hash ON ai_query_cache(query_hash);
CREATE INDEX idx_ai_query_cache_type ON ai_query_cache(query_type);
CREATE INDEX idx_ai_query_cache_expires_at ON ai_query_cache(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX idx_ai_query_cache_last_accessed ON ai_query_cache(last_accessed_at);
CREATE INDEX idx_ai_query_cache_hit_count ON ai_query_cache(hit_count DESC);

-- Comments
COMMENT ON TABLE ai_query_cache IS 'Caches natural language query results for improved performance';
COMMENT ON COLUMN ai_query_cache.query_hash IS 'SHA-256 hash of normalized query text for fast lookup';
COMMENT ON COLUMN ai_query_cache.query_text IS 'Original natural language query text';
COMMENT ON COLUMN ai_query_cache.query_type IS 'Type of query: graph_traversal, semantic_search, hybrid, etc.';
COMMENT ON COLUMN ai_query_cache.result_json IS 'Cached query results in JSON format';
COMMENT ON COLUMN ai_query_cache.hit_count IS 'Number of times this cached result has been used';
COMMENT ON COLUMN ai_query_cache.expires_at IS 'Expiration timestamp (NULL = never expires)';

-- ============================================================================
-- QUALITY SCORE HISTORY
-- ============================================================================

-- Track quality score changes over time for analysis
CREATE TABLE IF NOT EXISTS quality_history (
    history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    quality_score DECIMAL(5,2) NOT NULL,
    previous_score DECIMAL(5,2),
    score_delta DECIMAL(5,2),
    score_factors JSONB,
    trigger_event VARCHAR(50),
    calculated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT valid_quality_score CHECK (quality_score >= 0.0 AND quality_score <= 1.0),
    CONSTRAINT valid_previous_score CHECK (previous_score IS NULL OR (previous_score >= 0.0 AND previous_score <= 1.0))
);

-- Indexes for querying history
CREATE INDEX idx_quality_history_entity ON quality_history(entity_id, entity_type);
CREATE INDEX idx_quality_history_calculated_at ON quality_history(calculated_at DESC);
CREATE INDEX idx_quality_history_score ON quality_history(quality_score);
CREATE INDEX idx_quality_history_entity_type ON quality_history(entity_type);

-- Comments
COMMENT ON TABLE quality_history IS 'Tracks quality score changes over time for trend analysis';
COMMENT ON COLUMN quality_history.entity_id IS 'ID of the entity whose quality was scored';
COMMENT ON COLUMN quality_history.entity_type IS 'Type of entity (survey_point, utility_line, etc.)';
COMMENT ON COLUMN quality_history.quality_score IS 'New quality score (0.0-1.0)';
COMMENT ON COLUMN quality_history.previous_score IS 'Previous quality score for comparison';
COMMENT ON COLUMN quality_history.score_delta IS 'Change in score (positive = improvement)';
COMMENT ON COLUMN quality_history.score_factors IS 'JSON breakdown: {completeness: 0.8, has_embedding: true, relationship_count: 5}';
COMMENT ON COLUMN quality_history.trigger_event IS 'What triggered the recalculation: insert, update, embedding_added, relationship_added';

-- ============================================================================
-- QUERY HISTORY
-- ============================================================================

-- Track user query patterns for analytics and improvement
CREATE TABLE IF NOT EXISTS ai_query_history (
    query_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    session_id VARCHAR(100),
    query_text TEXT NOT NULL,
    query_type VARCHAR(50),
    was_successful BOOLEAN DEFAULT TRUE,
    result_count INTEGER,
    execution_time_ms INTEGER,
    used_cache BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    query_metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT valid_result_count CHECK (result_count IS NULL OR result_count >= 0),
    CONSTRAINT valid_execution_time CHECK (execution_time_ms IS NULL OR execution_time_ms >= 0)
);

-- Indexes for analytics
CREATE INDEX idx_ai_query_history_user ON ai_query_history(user_id);
CREATE INDEX idx_ai_query_history_session ON ai_query_history(session_id);
CREATE INDEX idx_ai_query_history_created_at ON ai_query_history(created_at DESC);
CREATE INDEX idx_ai_query_history_type ON ai_query_history(query_type);
CREATE INDEX idx_ai_query_history_successful ON ai_query_history(was_successful);

-- Comments
COMMENT ON TABLE ai_query_history IS 'Tracks all natural language queries for analytics and debugging';
COMMENT ON COLUMN ai_query_history.query_text IS 'Original user query text';
COMMENT ON COLUMN ai_query_history.query_type IS 'Classified query type: find_connections, similar_search, etc.';
COMMENT ON COLUMN ai_query_history.was_successful IS 'Whether the query returned results';
COMMENT ON COLUMN ai_query_history.used_cache IS 'Whether results came from cache';
COMMENT ON COLUMN ai_query_history.query_metadata IS 'Additional query context and parameters';

-- ============================================================================
-- GRAPH ANALYTICS CACHE
-- ============================================================================

-- Cache computationally expensive graph analytics results
CREATE TABLE IF NOT EXISTS graph_analytics_cache (
    cache_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_type VARCHAR(50) NOT NULL,
    scope_type VARCHAR(50),
    scope_id UUID,
    result_data JSONB NOT NULL,
    node_count INTEGER,
    edge_count INTEGER,
    computation_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    is_valid BOOLEAN DEFAULT TRUE,
    CONSTRAINT valid_node_count CHECK (node_count IS NULL OR node_count >= 0),
    CONSTRAINT valid_edge_count CHECK (edge_count IS NULL OR edge_count >= 0)
);

-- Indexes for cache lookup
CREATE INDEX idx_graph_analytics_type ON graph_analytics_cache(analysis_type);
CREATE INDEX idx_graph_analytics_scope ON graph_analytics_cache(scope_type, scope_id);
CREATE INDEX idx_graph_analytics_expires ON graph_analytics_cache(expires_at) WHERE is_valid = TRUE;

-- Comments
COMMENT ON TABLE graph_analytics_cache IS 'Caches graph analytics results (PageRank, communities, etc.)';
COMMENT ON COLUMN graph_analytics_cache.analysis_type IS 'Type: pagerank, community_detection, centrality, clustering, etc.';
COMMENT ON COLUMN graph_analytics_cache.scope_type IS 'Scope: project, entity_type, global, etc.';
COMMENT ON COLUMN graph_analytics_cache.scope_id IS 'ID of the scope (project_id, etc.)';
COMMENT ON COLUMN graph_analytics_cache.result_data IS 'Analytics results in JSON format';

-- ============================================================================
-- SEMANTIC SIMILARITY CACHE
-- ============================================================================

-- Cache frequently requested similarity computations
CREATE TABLE IF NOT EXISTS semantic_similarity_cache (
    cache_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_entity_id UUID NOT NULL,
    source_entity_type VARCHAR(50) NOT NULL,
    target_entity_id UUID NOT NULL,
    target_entity_type VARCHAR(50) NOT NULL,
    similarity_score DECIMAL(5,4) NOT NULL,
    similarity_method VARCHAR(50) DEFAULT 'cosine',
    model_id UUID REFERENCES embedding_models(model_id),
    created_at TIMESTAMP DEFAULT NOW(),
    is_valid BOOLEAN DEFAULT TRUE,
    CONSTRAINT valid_similarity_score CHECK (similarity_score >= 0.0 AND similarity_score <= 1.0),
    CONSTRAINT no_self_similarity CHECK (source_entity_id != target_entity_id OR source_entity_type != target_entity_type)
);

-- Unique index to prevent duplicate cache entries
CREATE UNIQUE INDEX idx_semantic_similarity_unique ON semantic_similarity_cache(
    source_entity_id, source_entity_type, target_entity_id, target_entity_type
) WHERE is_valid = TRUE;

-- Indexes for lookup
CREATE INDEX idx_semantic_similarity_source ON semantic_similarity_cache(source_entity_id, source_entity_type);
CREATE INDEX idx_semantic_similarity_score ON semantic_similarity_cache(similarity_score DESC);

-- Comments
COMMENT ON TABLE semantic_similarity_cache IS 'Caches pairwise semantic similarity scores between entities';
COMMENT ON COLUMN semantic_similarity_cache.similarity_score IS 'Similarity score (0.0-1.0, higher = more similar)';
COMMENT ON COLUMN semantic_similarity_cache.similarity_method IS 'Method used: cosine, euclidean, dot_product';

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to invalidate cache entries when entities change
CREATE OR REPLACE FUNCTION invalidate_entity_caches()
RETURNS TRIGGER AS $$
BEGIN
    -- Invalidate query cache entries that might reference this entity
    UPDATE ai_query_cache
    SET is_valid = FALSE,
        invalidation_reason = 'entity_modified'
    WHERE is_valid = TRUE
      AND created_at < NOW();

    -- Invalidate similarity cache for this entity
    UPDATE semantic_similarity_cache
    SET is_valid = FALSE
    WHERE (source_entity_id = NEW.entity_id OR target_entity_id = NEW.entity_id);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to update query cache hit count and last accessed time
CREATE OR REPLACE FUNCTION update_cache_hit(p_cache_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE ai_query_cache
    SET hit_count = hit_count + 1,
        last_accessed_at = NOW()
    WHERE cache_id = p_cache_id;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up expired cache entries
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete expired query cache entries
    DELETE FROM ai_query_cache
    WHERE expires_at IS NOT NULL
      AND expires_at < NOW();

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    -- Delete old, unused cache entries (not accessed in 30 days, hit count = 0)
    DELETE FROM ai_query_cache
    WHERE last_accessed_at < NOW() - INTERVAL '30 days'
      AND hit_count = 0;

    GET DIAGNOSTICS deleted_count = deleted_count + ROW_COUNT;

    -- Clean up graph analytics cache
    DELETE FROM graph_analytics_cache
    WHERE expires_at IS NOT NULL
      AND expires_at < NOW();

    GET DIAGNOSTICS deleted_count = deleted_count + ROW_COUNT;

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to track quality score changes
CREATE OR REPLACE FUNCTION track_quality_score_change()
RETURNS TRIGGER AS $$
DECLARE
    old_score DECIMAL(5,2);
    new_score DECIMAL(5,2);
    score_diff DECIMAL(5,2);
BEGIN
    -- Get old and new scores (if they exist)
    old_score := OLD.quality_score;
    new_score := NEW.quality_score;

    -- Only track if score actually changed
    IF old_score IS DISTINCT FROM new_score THEN
        score_diff := COALESCE(new_score, 0.0) - COALESCE(old_score, 0.0);

        INSERT INTO quality_history (
            entity_id,
            entity_type,
            quality_score,
            previous_score,
            score_delta,
            trigger_event,
            calculated_at
        ) VALUES (
            NEW.entity_id,
            TG_TABLE_NAME,
            new_score,
            old_score,
            score_diff,
            CASE TG_OP
                WHEN 'INSERT' THEN 'insert'
                WHEN 'UPDATE' THEN 'update'
                ELSE 'unknown'
            END,
            NOW()
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- ANALYTICS VIEWS
-- ============================================================================

-- View for embedding job statistics
CREATE OR REPLACE VIEW embedding_job_stats AS
SELECT
    entity_type,
    COUNT(*) as total_jobs,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_jobs,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_jobs,
    SUM(entity_count) as total_entities_processed,
    SUM(tokens_used) as total_tokens,
    SUM(cost_usd) as total_cost,
    AVG(duration_seconds) as avg_duration_seconds,
    MAX(completed_at) as last_completed_at
FROM embedding_jobs
GROUP BY entity_type;

COMMENT ON VIEW embedding_job_stats IS 'Summary statistics for embedding generation jobs by entity type';

-- View for query cache performance
CREATE OR REPLACE VIEW query_cache_stats AS
SELECT
    query_type,
    COUNT(*) as total_cached_queries,
    SUM(hit_count) as total_hits,
    AVG(hit_count) as avg_hits_per_query,
    AVG(execution_time_ms) as avg_execution_time_ms,
    SUM(CASE WHEN is_valid THEN 1 ELSE 0 END) as valid_cache_entries,
    MAX(last_accessed_at) as last_used_at
FROM ai_query_cache
GROUP BY query_type;

COMMENT ON VIEW query_cache_stats IS 'Performance metrics for query cache by type';

-- View for quality score trends
CREATE OR REPLACE VIEW quality_score_trends AS
SELECT
    entity_type,
    DATE_TRUNC('day', calculated_at) as date,
    COUNT(*) as score_changes,
    AVG(quality_score) as avg_score,
    AVG(score_delta) as avg_improvement,
    COUNT(CASE WHEN score_delta > 0 THEN 1 END) as improvements,
    COUNT(CASE WHEN score_delta < 0 THEN 1 END) as degradations
FROM quality_history
GROUP BY entity_type, DATE_TRUNC('day', calculated_at)
ORDER BY date DESC;

COMMENT ON VIEW quality_score_trends IS 'Daily quality score trends by entity type';

-- ============================================================================
-- PERMISSIONS
-- ============================================================================

-- Grant appropriate permissions (adjust as needed for your security model)
GRANT SELECT ON embedding_jobs TO PUBLIC;
GRANT SELECT ON ai_query_cache TO PUBLIC;
GRANT SELECT ON quality_history TO PUBLIC;
GRANT SELECT ON ai_query_history TO PUBLIC;
GRANT SELECT ON graph_analytics_cache TO PUBLIC;
GRANT SELECT ON semantic_similarity_cache TO PUBLIC;

GRANT SELECT ON embedding_job_stats TO PUBLIC;
GRANT SELECT ON query_cache_stats TO PUBLIC;
GRANT SELECT ON quality_score_trends TO PUBLIC;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Verify tables were created
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
      AND table_name IN (
          'embedding_jobs',
          'ai_query_cache',
          'quality_history',
          'ai_query_history',
          'graph_analytics_cache',
          'semantic_similarity_cache'
      );

    IF table_count = 6 THEN
        RAISE NOTICE 'SUCCESS: All 6 GraphRAG tables created successfully';
    ELSE
        RAISE WARNING 'WARNING: Expected 6 tables but found %', table_count;
    END IF;
END $$;

-- Show summary
SELECT
    'embedding_jobs' as table_name,
    COUNT(*) as row_count
FROM embedding_jobs
UNION ALL
SELECT 'ai_query_cache', COUNT(*) FROM ai_query_cache
UNION ALL
SELECT 'quality_history', COUNT(*) FROM quality_history
UNION ALL
SELECT 'ai_query_history', COUNT(*) FROM ai_query_history
UNION ALL
SELECT 'graph_analytics_cache', COUNT(*) FROM graph_analytics_cache
UNION ALL
SELECT 'semantic_similarity_cache', COUNT(*) FROM semantic_similarity_cache;
