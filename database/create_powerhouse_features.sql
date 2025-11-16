-- Powerhouse Package Database Schema
-- Creates tables for Report Builder, Executive Dashboard, Validation Engine, and Enhanced Map Viewer
-- Author: ACAD-GIS Development Team
-- Date: 2025-11-16

-- ============================================
-- FEATURE 1: REPORT BUILDER
-- ============================================

-- Report Templates
CREATE TABLE IF NOT EXISTS report_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(100), -- Project, Survey, QA/QC, Utility, Custom
    template_type VARCHAR(20), -- pdf, excel, both
    jinja_template_path VARCHAR(500), -- e.g., reports/project_summary.html
    sql_query TEXT NOT NULL, -- Query to fetch data
    parameters JSONB, -- {project_id: {type: uuid, required: true}, date_range: {...}}
    chart_config JSONB, -- Chart.js configuration
    is_active BOOLEAN DEFAULT TRUE,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Report Generation History
CREATE TABLE IF NOT EXISTS report_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID REFERENCES report_templates(id),
    parameters_used JSONB,
    file_path VARCHAR(500),
    file_format VARCHAR(10), -- pdf or excel
    status VARCHAR(20), -- pending, completed, failed
    execution_time_ms INTEGER,
    generated_by_user_id UUID,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_report_history_template ON report_history(template_id);
CREATE INDEX IF NOT EXISTS idx_report_history_created ON report_history(created_at DESC);

-- ============================================
-- FEATURE 2: EXECUTIVE DASHBOARD
-- ============================================

CREATE TABLE IF NOT EXISTS dashboard_widgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    widget_name VARCHAR(200),
    widget_type VARCHAR(50), -- metric, chart, table, map
    data_source_query TEXT,
    refresh_interval_seconds INTEGER DEFAULT 30,
    position_x INTEGER,
    position_y INTEGER,
    width INTEGER,
    height INTEGER,
    config JSONB,
    is_active BOOLEAN DEFAULT TRUE
);

-- ============================================
-- FEATURE 3: VALIDATION ENGINE
-- ============================================

-- Validation Rules
CREATE TABLE IF NOT EXISTS validation_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_name VARCHAR(200) NOT NULL,
    rule_description TEXT,
    entity_type VARCHAR(50), -- survey_points, utility_structures, utility_lines
    rule_type VARCHAR(50), -- geometry, connectivity, completeness, survey, cad_standards
    severity VARCHAR(20), -- error, warning, info
    sql_check_query TEXT NOT NULL, -- Returns IDs of failing entities
    auto_fix_query TEXT, -- Optional SQL to fix issue
    parameters JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Validation Results
CREATE TABLE IF NOT EXISTS validation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id UUID REFERENCES validation_rules(id),
    entity_type VARCHAR(50),
    entity_id UUID,
    status VARCHAR(20), -- pass or fail
    error_message TEXT,
    detected_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP,
    resolved_by_user_id UUID,
    auto_fixed BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_validation_results_rule ON validation_results(rule_id);
CREATE INDEX IF NOT EXISTS idx_validation_results_entity ON validation_results(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_validation_results_status ON validation_results(status);

-- Validation Templates
CREATE TABLE IF NOT EXISTS validation_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_name VARCHAR(200),
    description TEXT,
    category VARCHAR(100),
    rule_ids UUID[], -- Array of rule IDs
    is_active BOOLEAN DEFAULT TRUE,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- FEATURE 4: ENHANCED MAP VIEWER
-- ============================================

CREATE TABLE IF NOT EXISTS map_layer_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    layer_name VARCHAR(200),
    entity_type VARCHAR(50),
    color_scheme VARCHAR(50), -- type, material, status, elevation
    filter_config JSONB,
    style_config JSONB,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_report_templates_category ON report_templates(category);
CREATE INDEX IF NOT EXISTS idx_report_templates_active ON report_templates(is_active);
CREATE INDEX IF NOT EXISTS idx_validation_rules_type ON validation_rules(rule_type);
CREATE INDEX IF NOT EXISTS idx_validation_rules_entity ON validation_rules(entity_type);
CREATE INDEX IF NOT EXISTS idx_validation_rules_active ON validation_rules(is_active);

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Powerhouse Package tables created successfully!';
END $$;
