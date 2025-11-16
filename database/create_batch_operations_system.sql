-- ============================================================================
-- Batch Operations System
-- Enables bulk operations on multiple entities with job tracking
-- ============================================================================

-- Batch Operation Jobs
-- Tracks all batch operations with status and progress
CREATE TABLE IF NOT EXISTS batch_operation_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Job Details
    job_name VARCHAR(255) NOT NULL,
    job_description TEXT,
    operation_type VARCHAR(100) NOT NULL, -- 'bulk_edit', 'bulk_delete', 'bulk_export', 'bulk_update'

    -- Target Configuration
    entity_type VARCHAR(100) NOT NULL, -- 'utility_structures', 'survey_points', etc.
    target_filter JSONB, -- Filter config to identify target entities
    target_entity_ids JSONB, -- Array of specific entity IDs

    -- Operation Configuration
    operation_config JSONB NOT NULL, -- Operation-specific configuration

    -- Status and Progress
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed', 'cancelled'
    total_items INTEGER DEFAULT 0,
    processed_items INTEGER DEFAULT 0,
    successful_items INTEGER DEFAULT 0,
    failed_items INTEGER DEFAULT 0,

    -- Execution Details
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    execution_time_ms INTEGER,

    -- Error Tracking
    error_summary JSONB, -- Summary of errors by type
    failed_entity_ids JSONB, -- Array of entity IDs that failed

    -- Results
    result_summary JSONB, -- Summary of what was changed
    export_file_path TEXT, -- For export operations
    export_format VARCHAR(50), -- 'csv', 'excel', 'dxf', 'pdf'

    -- Metadata
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Rollback Support
    is_reversible BOOLEAN DEFAULT FALSE,
    rollback_data JSONB, -- Stores original values for rollback
    rolled_back_at TIMESTAMP WITH TIME ZONE,

    -- Approval Workflow (for destructive operations)
    requires_approval BOOLEAN DEFAULT FALSE,
    approved_by VARCHAR(255),
    approved_at TIMESTAMP WITH TIME ZONE,

    is_active BOOLEAN DEFAULT TRUE
);

-- Batch Operation Items
-- Individual items within a batch operation
CREATE TABLE IF NOT EXISTS batch_operation_items (
    item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES batch_operation_jobs(job_id) ON DELETE CASCADE,

    -- Item Details
    entity_type VARCHAR(100) NOT NULL,
    entity_id UUID NOT NULL,
    entity_identifier VARCHAR(255), -- Human-readable ID (structure_number, point_number, etc.)

    -- Processing Status
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'processing', 'success', 'failed', 'skipped'
    processed_at TIMESTAMP WITH TIME ZONE,

    -- Changes Made
    original_values JSONB, -- Original values before change
    new_values JSONB, -- New values after change
    changes_applied JSONB, -- Specific changes made

    -- Error Details
    error_message TEXT,
    error_code VARCHAR(100),

    -- Validation
    validation_warnings JSONB, -- Non-fatal warnings

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Batch Operation Templates
-- Pre-configured batch operation templates
CREATE TABLE IF NOT EXISTS batch_operation_templates (
    template_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    template_name VARCHAR(255) NOT NULL,
    template_description TEXT,

    operation_type VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,

    -- Default Configuration
    default_config JSONB,

    -- UI Configuration
    parameter_schema JSONB, -- JSON Schema for parameters
    ui_hints JSONB, -- UI display hints

    -- Safety Settings
    requires_approval BOOLEAN DEFAULT FALSE,
    max_items_warning_threshold INTEGER DEFAULT 100, -- Warn if affecting more items
    is_destructive BOOLEAN DEFAULT FALSE,

    -- Metadata
    category VARCHAR(100), -- 'Data Cleanup', 'Export', 'Update', 'Archive'
    tags JSONB,
    usage_count INTEGER DEFAULT 0,

    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    is_public BOOLEAN DEFAULT FALSE,
    is_system_template BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE
);

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_batch_jobs_status
    ON batch_operation_jobs(status) WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_batch_jobs_created
    ON batch_operation_jobs(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_batch_jobs_entity_type
    ON batch_operation_jobs(entity_type) WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_batch_items_job
    ON batch_operation_items(job_id);

CREATE INDEX IF NOT EXISTS idx_batch_items_status
    ON batch_operation_items(status);

CREATE INDEX IF NOT EXISTS idx_batch_items_entity
    ON batch_operation_items(entity_type, entity_id);

CREATE INDEX IF NOT EXISTS idx_batch_templates_type
    ON batch_operation_templates(entity_type) WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_batch_templates_category
    ON batch_operation_templates(category) WHERE is_active = TRUE;

-- Triggers
CREATE OR REPLACE FUNCTION update_batch_job_progress()
RETURNS TRIGGER AS $$
BEGIN
    -- Update parent job progress when item status changes
    UPDATE batch_operation_jobs
    SET processed_items = (
            SELECT COUNT(*) FROM batch_operation_items
            WHERE job_id = NEW.job_id
              AND status IN ('success', 'failed', 'skipped')
        ),
        successful_items = (
            SELECT COUNT(*) FROM batch_operation_items
            WHERE job_id = NEW.job_id AND status = 'success'
        ),
        failed_items = (
            SELECT COUNT(*) FROM batch_operation_items
            WHERE job_id = NEW.job_id AND status = 'failed'
        )
    WHERE job_id = NEW.job_id;

    -- Auto-complete job if all items processed
    UPDATE batch_operation_jobs
    SET status = 'completed',
        completed_at = CURRENT_TIMESTAMP,
        execution_time_ms = EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - started_at)) * 1000
    WHERE job_id = NEW.job_id
      AND status = 'running'
      AND processed_items >= total_items;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_batch_job_progress
    AFTER INSERT OR UPDATE OF status ON batch_operation_items
    FOR EACH ROW
    EXECUTE FUNCTION update_batch_job_progress();

-- Function to create batch operation job
CREATE OR REPLACE FUNCTION create_batch_operation_job(
    p_job_name VARCHAR,
    p_operation_type VARCHAR,
    p_entity_type VARCHAR,
    p_entity_ids JSONB,
    p_operation_config JSONB,
    p_created_by VARCHAR DEFAULT 'system'
)
RETURNS UUID AS $$
DECLARE
    v_job_id UUID;
    v_entity_id TEXT;
    v_total_items INTEGER;
BEGIN
    -- Create job
    INSERT INTO batch_operation_jobs
        (job_name, operation_type, entity_type, target_entity_ids,
         operation_config, created_by, total_items)
    VALUES
        (p_job_name, p_operation_type, p_entity_type, p_entity_ids,
         p_operation_config, p_created_by, jsonb_array_length(p_entity_ids))
    RETURNING job_id INTO v_job_id;

    -- Create items for each entity
    FOR v_entity_id IN SELECT jsonb_array_elements_text(p_entity_ids)
    LOOP
        INSERT INTO batch_operation_items
            (job_id, entity_type, entity_id, status)
        VALUES
            (v_job_id, p_entity_type, v_entity_id::UUID, 'pending');
    END LOOP;

    RETURN v_job_id;
END;
$$ LANGUAGE plpgsql;

-- Function to rollback a batch operation
CREATE OR REPLACE FUNCTION rollback_batch_operation(p_job_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    v_job_record RECORD;
    v_item_record RECORD;
    v_rollback_sql TEXT;
BEGIN
    -- Get job details
    SELECT * INTO v_job_record
    FROM batch_operation_jobs
    WHERE job_id = p_job_id AND is_reversible = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Job not found or not reversible';
    END IF;

    -- Process each successful item
    FOR v_item_record IN
        SELECT * FROM batch_operation_items
        WHERE job_id = p_job_id
          AND status = 'success'
          AND original_values IS NOT NULL
    LOOP
        -- Here you would restore original values
        -- This is a template - actual implementation would vary by entity type
        RAISE NOTICE 'Rolling back item % for entity %', v_item_record.item_id, v_item_record.entity_id;
    END LOOP;

    -- Mark job as rolled back
    UPDATE batch_operation_jobs
    SET rolled_back_at = CURRENT_TIMESTAMP
    WHERE job_id = p_job_id;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;
