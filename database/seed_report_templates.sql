-- Seed Report Templates for Report Builder
-- 5 pre-configured report templates

-- 1. Project Summary Report (PDF+Excel)
INSERT INTO report_templates (
    name,
    description,
    category,
    template_type,
    jinja_template_path,
    sql_query,
    parameters,
    chart_config
) VALUES (
    'Project Summary Report',
    'Comprehensive project overview with entity counts, metadata, and visualizations',
    'Project',
    'both',
    'reports/project_summary.html',
    'SELECT p.*, COUNT(DISTINCT ge.id) as entity_count FROM projects p LEFT JOIN generic_entities ge ON p.id = ge.project_id WHERE p.id = %(project_id)s GROUP BY p.id',
    '{"project_id": {"type": "uuid", "required": true, "label": "Project"}}',
    '{"type": "bar", "label": "Entity Distribution"}'
) ON CONFLICT DO NOTHING;

-- 2. Survey Data Report (Excel)
INSERT INTO report_templates (
    name,
    description,
    category,
    template_type,
    jinja_template_path,
    sql_query,
    parameters,
    chart_config
) VALUES (
    'Survey Data Report',
    'Detailed survey point data with PNEZD information and accuracy statistics',
    'Survey',
    'excel',
    'reports/survey_data.html',
    'SELECT point_number, northing, easting, elevation, description, survey_method FROM survey_points WHERE project_id = %(project_id)s ORDER BY created_at',
    '{"project_id": {"type": "uuid", "required": true, "label": "Project"}}',
    '{"type": "line", "label": "Points Over Time"}'
) ON CONFLICT DO NOTHING;

-- 3. QA/QC Report (PDF)
INSERT INTO report_templates (
    name,
    description,
    category,
    template_type,
    jinja_template_path,
    sql_query,
    parameters,
    chart_config
) VALUES (
    'QA/QC Validation Report',
    'Quality assurance report showing validation failures by rule and entity type',
    'QA/QC',
    'pdf',
    'reports/qa_qc.html',
    'SELECT vr.rule_name, vr.entity_type, COUNT(*) as failure_count FROM validation_results vres JOIN validation_rules vr ON vres.rule_id = vr.id WHERE vres.status = ''fail'' GROUP BY vr.rule_name, vr.entity_type ORDER BY failure_count DESC',
    '{}',
    '{"type": "pie", "label": "Issues by Type"}'
) ON CONFLICT DO NOTHING;

-- 4. Utility Network Report (Excel)
INSERT INTO report_templates (
    name,
    description,
    category,
    template_type,
    jinja_template_path,
    sql_query,
    parameters,
    chart_config
) VALUES (
    'Utility Network Inventory',
    'Pipe and structure inventory with material distribution and total lengths',
    'Utility',
    'excel',
    'reports/utility_network.html',
    'SELECT material, COUNT(*) as count, SUM(ST_Length(geometry)) as total_length FROM utility_lines WHERE project_id = %(project_id)s AND is_active = TRUE GROUP BY material ORDER BY total_length DESC',
    '{"project_id": {"type": "uuid", "required": true, "label": "Project"}}',
    '{"type": "pie", "label": "Material Distribution"}'
) ON CONFLICT DO NOTHING;

-- 5. As-Built Summary (PDF)
INSERT INTO report_templates (
    name,
    description,
    category,
    template_type,
    jinja_template_path,
    sql_query,
    parameters,
    chart_config
) VALUES (
    'As-Built Summary',
    'Complete as-built summary with all entities by type for project closeout',
    'Project',
    'pdf',
    'reports/as_built.html',
    'SELECT entity_type, COUNT(*) as count FROM generic_entities WHERE project_id = %(project_id)s AND is_active = TRUE GROUP BY entity_type ORDER BY count DESC',
    '{"project_id": {"type": "uuid", "required": true, "label": "Project"}}',
    '{"type": "bar", "label": "Entity Type Distribution"}'
) ON CONFLICT DO NOTHING;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Report templates seeded successfully!';
END $$;
