-- ============================================================================
-- Seed Data for Natural Language Query Templates
-- Common queries users might want to run
-- ============================================================================

INSERT INTO nl_query_templates
(template_name, template_description, category, natural_language_template, sql_template, sql_explanation, parameters, example_values, tags)
VALUES

-- SPATIAL QUERIES
(
    'Find Nearby Utilities',
    'Find all utility structures within a specified distance of a point or area',
    'Spatial',
    'Show me all {structure_type} within {distance} feet of {location}',
    'SELECT us.structure_number, us.structure_type, sts.type_name, ST_Distance(us.rim_geometry, ST_SetSRID(ST_MakePoint({lon}, {lat}), 2226)) as distance_ft FROM utility_structures us LEFT JOIN structure_type_standards sts ON us.structure_type_id = sts.type_id WHERE ST_DWithin(us.rim_geometry, ST_SetSRID(ST_MakePoint({lon}, {lat}), 2226), {distance}) ORDER BY distance_ft',
    'Finds utility structures within a specified radius using PostGIS spatial functions',
    '[{"name": "structure_type", "type": "string", "default": "manholes"}, {"name": "distance", "type": "number", "default": 100}, {"name": "location", "type": "string", "default": "project area"}, {"name": "lat", "type": "number"}, {"name": "lon", "type": "number"}]'::jsonb,
    '{"structure_type": "manholes", "distance": 100, "lat": 37.7749, "lon": -122.4194}'::jsonb,
    '["spatial", "utilities", "proximity"]'::jsonb
),

(
    'Count Features by Type',
    'Count all features of a specific type in the system',
    'Aggregation',
    'How many {feature_type} are in the system?',
    'SELECT COUNT(*) as total FROM {table_name} WHERE is_active = TRUE',
    'Simple count of active features in a specified table',
    '[{"name": "feature_type", "type": "string", "default": "storm drains"}, {"name": "table_name", "type": "string", "default": "utility_structures"}]'::jsonb,
    '{"feature_type": "storm drains", "table_name": "utility_structures"}'::jsonb,
    '["count", "statistics", "inventory"]'::jsonb
),

(
    'Project Summary',
    'Get comprehensive statistics for a specific project',
    'Project Management',
    'Give me a summary of project {project_name}',
    'SELECT p.project_name, p.project_number, p.client, COUNT(DISTINCT us.structure_id) as total_structures, COUNT(DISTINCT sp.point_id) as total_survey_points, COUNT(DISTINCT ul.line_id) as total_utility_lines FROM projects p LEFT JOIN utility_structures us ON us.project_id = p.project_id LEFT JOIN survey_points sp ON sp.project_id = p.project_id LEFT JOIN utility_lines ul ON ul.project_id = p.project_id WHERE p.project_name ILIKE ''%{project_name}%'' GROUP BY p.project_id, p.project_name, p.project_number, p.client',
    'Aggregates all project data including structures, survey points, and utility lines',
    '[{"name": "project_name", "type": "string", "default": "Main Street"}]'::jsonb,
    '{"project_name": "Main Street"}'::jsonb,
    '["project", "summary", "statistics"]'::jsonb
),

(
    'Find Survey Points by Description',
    'Search for survey points with specific descriptions',
    'Survey',
    'Show me all survey points that are {description}',
    'SELECT sp.point_number, sp.point_description, spd.description_text, sp.northing, sp.easting, sp.elevation FROM survey_points sp LEFT JOIN survey_point_description_standards spd ON sp.point_description_id = spd.description_id WHERE spd.description_text ILIKE ''%{description}%'' OR sp.point_description ILIKE ''%{description}%'' ORDER BY sp.point_number',
    'Searches survey points by description text with fuzzy matching',
    '[{"name": "description", "type": "string", "default": "edge of pavement"}]'::jsonb,
    '{"description": "edge of pavement"}'::jsonb,
    '["survey", "search", "points"]'::jsonb
),

(
    'Utility Network Integrity Check',
    'Find utility structures without connected pipes',
    'Data Quality',
    'Find all {structure_type} that don''t have any connected pipes',
    'SELECT us.structure_number, us.structure_type, sts.type_name, us.rim_elevation FROM utility_structures us LEFT JOIN structure_type_standards sts ON us.structure_type_id = sts.type_id LEFT JOIN utility_lines ul1 ON ul1.upstream_structure_id = us.structure_id LEFT JOIN utility_lines ul2 ON ul2.downstream_structure_id = us.structure_id WHERE sts.type_name ILIKE ''%{structure_type}%'' AND ul1.line_id IS NULL AND ul2.line_id IS NULL AND us.project_id IS NOT NULL',
    'Identifies orphaned structures that have no pipe connections for QA/QC',
    '[{"name": "structure_type", "type": "string", "default": "manholes"}]'::jsonb,
    '{"structure_type": "manholes"}'::jsonb,
    '["qa/qc", "utilities", "data quality"]'::jsonb
),

(
    'Material Inventory',
    'Count utilities by material type',
    'Inventory',
    'How many utility lines are made of {material}?',
    'SELECT material, COUNT(*) as count, SUM(ST_Length(geometry)) as total_length_ft FROM utility_lines WHERE material ILIKE ''%{material}%'' GROUP BY material ORDER BY count DESC',
    'Aggregates utility lines by material with total length calculations',
    '[{"name": "material", "type": "string", "default": "PVC"}]'::jsonb,
    '{"material": "PVC"}'::jsonb,
    '["inventory", "materials", "utilities"]'::jsonb
),

(
    'Recent Survey Work',
    'Find recently surveyed points within a date range',
    'Survey',
    'Show me survey points collected in the last {days} days',
    'SELECT sp.point_number, sp.point_description, sp.survey_date, sp.survey_method, smt.method_name, sp.surveyed_by FROM survey_points sp LEFT JOIN survey_method_types smt ON sp.survey_method_id = smt.method_id WHERE sp.survey_date >= CURRENT_DATE - INTERVAL ''{days} days'' ORDER BY sp.survey_date DESC',
    'Lists recent survey points with method details',
    '[{"name": "days", "type": "number", "default": 30}]'::jsonb,
    '{"days": 30}'::jsonb,
    '["survey", "recent", "temporal"]'::jsonb
),

(
    'Compliance Check - Missing Details',
    'Find entities without required detail references',
    'Compliance',
    'Show me all {entity_type} that don''t have detail references',
    'SELECT entity_id, entity_name, entity_type FROM standards_entities WHERE entity_type = ''{entity_type}'' AND NOT EXISTS (SELECT 1 FROM entity_relationships er WHERE er.source_entity_id = standards_entities.entity_id AND er.relationship_type = ''requires_detail'') AND is_active = TRUE',
    'Identifies entities missing required detail cross-references for compliance',
    '[{"name": "entity_type", "type": "string", "default": "utility_line"}]'::jsonb,
    '{"entity_type": "utility_line"}'::jsonb,
    '["compliance", "qa/qc", "details"]'::jsonb
),

(
    'High Elevation Points',
    'Find survey points above a certain elevation',
    'Survey',
    'Show me all survey points above {elevation} feet elevation',
    'SELECT sp.point_number, sp.point_description, sp.elevation, sp.northing, sp.easting FROM survey_points sp WHERE sp.elevation > {elevation} ORDER BY sp.elevation DESC',
    'Filters survey points by minimum elevation threshold',
    '[{"name": "elevation", "type": "number", "default": 500}]'::jsonb,
    '{"elevation": 500}'::jsonb,
    '["survey", "elevation", "filtering"]'::jsonb
),

(
    'Project Search by Client',
    'Find all projects for a specific client',
    'Project Management',
    'Show me all projects for client {client_name}',
    'SELECT p.project_name, p.project_number, p.client, p.municipality, p.start_date, p.status FROM projects p WHERE p.client ILIKE ''%{client_name}%'' OR EXISTS (SELECT 1 FROM clients c WHERE c.client_id = p.client_id AND c.client_name ILIKE ''%{client_name}%'') ORDER BY p.start_date DESC',
    'Searches projects by client name with fuzzy matching',
    '[{"name": "client_name", "type": "string", "default": "City"}]'::jsonb,
    '{"client_name": "City"}'::jsonb,
    '["projects", "clients", "search"]'::jsonb
);

-- Set usage counts to 0 initially
UPDATE nl_query_templates SET usage_count = 0;
