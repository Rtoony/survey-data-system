-- ============================================================================
-- Seed Data for Batch Operation Templates
-- Pre-configured batch operation templates for common tasks
-- ============================================================================

INSERT INTO batch_operation_templates
(template_name, template_description, operation_type, entity_type, default_config, parameter_schema, category, tags, requires_approval, is_destructive, max_items_warning_threshold, is_public, is_system_template)
VALUES

-- EXPORT OPERATIONS

(
    'Bulk Export to Excel',
    'Export selected entities to Excel spreadsheet with all fields',
    'bulk_export',
    'utility_structures',
    '{
        "format": "excel",
        "include_related": true,
        "include_geometry": false
    }'::jsonb,
    '{
        "type": "object",
        "properties": {
            "format": {"type": "string", "enum": ["excel", "csv"], "default": "excel"},
            "include_related": {"type": "boolean", "default": true},
            "include_geometry": {"type": "boolean", "default": false}
        }
    }'::jsonb,
    'Export',
    '["export", "excel", "bulk"]'::jsonb,
    FALSE,
    FALSE,
    1000,
    TRUE,
    TRUE
),

(
    'Export to DXF',
    'Export selected entities to AutoCAD DXF file',
    'bulk_export',
    'utility_structures',
    '{
        "format": "dxf",
        "coordinate_system": "2226",
        "include_labels": true,
        "layer_by_type": true
    }'::jsonb,
    '{
        "type": "object",
        "properties": {
            "coordinate_system": {"type": "string", "default": "2226"},
            "include_labels": {"type": "boolean", "default": true},
            "layer_by_type": {"type": "boolean", "default": true},
            "scale_factor": {"type": "number", "default": 1.0}
        }
    }'::jsonb,
    'Export',
    '["export", "dxf", "cad"]'::jsonb,
    FALSE,
    FALSE,
    500,
    TRUE,
    TRUE
),

-- UPDATE OPERATIONS

(
    'Bulk Update Project Assignment',
    'Assign multiple entities to a different project',
    'bulk_update',
    'utility_structures',
    '{
        "field": "project_id",
        "create_audit_log": true
    }'::jsonb,
    '{
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "format": "uuid", "required": true},
            "create_audit_log": {"type": "boolean", "default": true}
        }
    }'::jsonb,
    'Update',
    '["project", "assignment", "bulk"]'::jsonb,
    FALSE,
    FALSE,
    100,
    TRUE,
    TRUE
),

(
    'Bulk Update Structure Type',
    'Update structure type for multiple structures',
    'bulk_update',
    'utility_structures',
    '{
        "field": "structure_type_id",
        "validate_connections": true
    }'::jsonb,
    '{
        "type": "object",
        "properties": {
            "structure_type_id": {"type": "string", "format": "uuid", "required": true},
            "validate_connections": {"type": "boolean", "default": true}
        }
    }'::jsonb,
    'Update',
    '["structure", "type", "classification"]'::jsonb,
    FALSE,
    FALSE,
    50,
    TRUE,
    TRUE
),

(
    'Bulk Update Survey Method',
    'Update survey method for multiple survey points',
    'bulk_update',
    'survey_points',
    '{
        "field": "survey_method_id",
        "update_accuracy": true
    }'::jsonb,
    '{
        "type": "object",
        "properties": {
            "survey_method_id": {"type": "string", "format": "uuid", "required": true},
            "update_accuracy": {"type": "boolean", "default": true}
        }
    }'::jsonb,
    'Update',
    '["survey", "method", "metadata"]'::jsonb,
    FALSE,
    FALSE,
    200,
    TRUE,
    TRUE
),

(
    'Bulk Elevation Adjustment',
    'Apply elevation offset to multiple survey points',
    'bulk_update',
    'survey_points',
    '{
        "field": "elevation",
        "operation": "add_offset",
        "create_backup": true
    }'::jsonb,
    '{
        "type": "object",
        "properties": {
            "offset": {"type": "number", "required": true, "description": "Elevation offset in feet"},
            "create_backup": {"type": "boolean", "default": true}
        }
    }'::jsonb,
    'Update',
    '["elevation", "adjustment", "survey"]'::jsonb,
    TRUE,
    FALSE,
    100,
    TRUE,
    TRUE
),

-- DATA CLEANUP OPERATIONS

(
    'Bulk Archive Old Records',
    'Archive (soft-delete) entities older than specified date',
    'bulk_update',
    'utility_structures',
    '{
        "field": "is_active",
        "value": false,
        "create_backup": true
    }'::jsonb,
    '{
        "type": "object",
        "properties": {
            "archive_before_date": {"type": "string", "format": "date", "required": true},
            "create_backup": {"type": "boolean", "default": true}
        }
    }'::jsonb,
    'Data Cleanup',
    '["archive", "cleanup", "maintenance"]'::jsonb,
    TRUE,
    FALSE,
    500,
    TRUE,
    TRUE
),

(
    'Bulk Delete Duplicate Points',
    'Remove duplicate survey points within tolerance',
    'bulk_delete',
    'survey_points',
    '{
        "tolerance_feet": 0.01,
        "keep_newest": true,
        "requires_confirmation": true
    }'::jsonb,
    '{
        "type": "object",
        "properties": {
            "tolerance_feet": {"type": "number", "default": 0.01},
            "keep_newest": {"type": "boolean", "default": true}
        }
    }'::jsonb,
    'Data Cleanup',
    '["duplicates", "cleanup", "qa"]'::jsonb,
    TRUE,
    TRUE,
    100,
    TRUE,
    TRUE
),

(
    'Normalize Text Fields',
    'Standardize text field formatting (trim, case, etc.)',
    'bulk_update',
    'utility_structures',
    '{
        "fields": ["structure_number", "structure_type"],
        "trim_whitespace": true,
        "uppercase": false
    }'::jsonb,
    '{
        "type": "object",
        "properties": {
            "trim_whitespace": {"type": "boolean", "default": true},
            "uppercase": {"type": "boolean", "default": false},
            "remove_special_chars": {"type": "boolean", "default": false}
        }
    }'::jsonb,
    'Data Cleanup',
    '["normalization", "text", "cleanup"]'::jsonb,
    FALSE,
    FALSE,
    200,
    TRUE,
    TRUE
),

-- QUALITY CONTROL OPERATIONS

(
    'Bulk Validation Check',
    'Run validation checks on selected entities',
    'bulk_edit',
    'utility_structures',
    '{
        "checks": ["geometry", "connections", "elevation", "required_fields"],
        "auto_fix": false,
        "generate_report": true
    }'::jsonb,
    '{
        "type": "object",
        "properties": {
            "auto_fix": {"type": "boolean", "default": false},
            "generate_report": {"type": "boolean", "default": true}
        }
    }'::jsonb,
    'Quality Control',
    '["validation", "qa", "qc"]'::jsonb,
    FALSE,
    FALSE,
    500,
    TRUE,
    TRUE
),

(
    'Recalculate Computed Fields',
    'Recalculate derived fields (lengths, slopes, distances, etc.)',
    'bulk_update',
    'utility_lines',
    '{
        "fields": ["length_ft", "slope"],
        "update_metadata": true
    }'::jsonb,
    '{
        "type": "object",
        "properties": {
            "recalculate_length": {"type": "boolean", "default": true},
            "recalculate_slope": {"type": "boolean", "default": true}
        }
    }'::jsonb,
    'Quality Control',
    '["recalculation", "computed", "qa"]'::jsonb,
    FALSE,
    FALSE,
    300,
    TRUE,
    TRUE
),

-- METADATA OPERATIONS

(
    'Bulk Tag Assignment',
    'Add tags to multiple entities',
    'bulk_update',
    'utility_structures',
    '{
        "operation": "add_tags",
        "merge_existing": true
    }'::jsonb,
    '{
        "type": "object",
        "properties": {
            "tags": {"type": "array", "items": {"type": "string"}, "required": true},
            "merge_existing": {"type": "boolean", "default": true}
        }
    }'::jsonb,
    'Metadata',
    '["tags", "metadata", "organization"]'::jsonb,
    FALSE,
    FALSE,
    500,
    TRUE,
    TRUE
),

(
    'Bulk Set Inspection Status',
    'Update inspection status for multiple structures',
    'bulk_update',
    'utility_structures',
    '{
        "field": "inspection_status",
        "update_timestamp": true
    }'::jsonb,
    '{
        "type": "object",
        "properties": {
            "inspection_status": {"type": "string", "enum": ["pending", "completed", "overdue"], "required": true},
            "inspection_date": {"type": "string", "format": "date"},
            "inspector": {"type": "string"}
        }
    }'::jsonb,
    'Metadata',
    '["inspection", "status", "compliance"]'::jsonb,
    FALSE,
    FALSE,
    100,
    TRUE,
    TRUE
),

-- TRANSFORMATION OPERATIONS

(
    'Coordinate System Transform',
    'Transform coordinates between coordinate systems',
    'bulk_update',
    'survey_points',
    '{
        "from_srid": 2226,
        "to_srid": 4326,
        "create_backup": true
    }'::jsonb,
    '{
        "type": "object",
        "properties": {
            "from_srid": {"type": "integer", "required": true},
            "to_srid": {"type": "integer", "required": true},
            "create_backup": {"type": "boolean", "default": true}
        }
    }'::jsonb,
    'Transformation',
    '["coordinates", "projection", "gis"]'::jsonb,
    TRUE,
    FALSE,
    200,
    TRUE,
    TRUE
);

-- Initialize usage counts
UPDATE batch_operation_templates SET usage_count = 0 WHERE is_system_template = TRUE;
