-- ============================================================================
-- Seed Data for Advanced Search Templates
-- Pre-built search configurations for common use cases
-- ============================================================================

INSERT INTO saved_search_templates
(template_name, template_description, entity_type, filter_config, enabled_facets, default_sort, visible_columns, category, tags, is_public, is_system_template)
VALUES

-- QUALITY CONTROL TEMPLATES

(
    'Orphaned Structures',
    'Find utility structures with no connected pipes - common QA/QC issue',
    'utility_structures',
    '{
        "has_no_connections": true,
        "exclude_null_projects": true
    }'::jsonb,
    '["structure_type", "project", "municipality"]'::jsonb,
    'structure_number ASC',
    '["structure_number", "structure_type", "rim_elevation", "project_name", "municipality"]'::jsonb,
    'Quality Control',
    '["qa", "qc", "data quality", "validation"]'::jsonb,
    TRUE,
    TRUE
),

(
    'Missing Elevations',
    'Find survey points or structures without elevation data',
    'survey_points',
    '{
        "elevation_null": true,
        "is_active": true
    }'::jsonb,
    '["point_description", "survey_method", "surveyed_by"]'::jsonb,
    'point_number ASC',
    '["point_number", "point_description", "northing", "easting", "survey_date"]'::jsonb,
    'Quality Control',
    '["qa", "qc", "elevation", "missing data"]'::jsonb,
    TRUE,
    TRUE
),

(
    'Duplicate Structure Numbers',
    'Identify potential duplicate structure numbers within projects',
    'utility_structures',
    '{
        "find_duplicates": "structure_number",
        "group_by": "project_id"
    }'::jsonb,
    '["project", "structure_type"]'::jsonb,
    'structure_number ASC',
    '["structure_number", "structure_type", "project_name", "rim_elevation"]'::jsonb,
    'Quality Control',
    '["qa", "qc", "duplicates"]'::jsonb,
    TRUE,
    TRUE
),

-- SPATIAL SEARCH TEMPLATES

(
    'Structures Near Location',
    'Find all structures within a radius of coordinates',
    'utility_structures',
    '{
        "spatial_search": {
            "type": "radius",
            "center_lon": null,
            "center_lat": null,
            "radius_feet": 100
        }
    }'::jsonb,
    '["structure_type", "municipality"]'::jsonb,
    'distance ASC',
    '["structure_number", "structure_type", "distance", "rim_elevation", "project_name"]'::jsonb,
    'Spatial Analysis',
    '["spatial", "proximity", "location"]'::jsonb,
    TRUE,
    TRUE
),

(
    'Points in Bounding Box',
    'Find survey points within a rectangular area',
    'survey_points',
    '{
        "spatial_search": {
            "type": "bbox",
            "min_northing": null,
            "max_northing": null,
            "min_easting": null,
            "max_easting": null
        }
    }'::jsonb,
    '["point_description", "survey_method"]'::jsonb,
    'northing ASC, easting ASC',
    '["point_number", "point_description", "northing", "easting", "elevation"]'::jsonb,
    'Spatial Analysis',
    '["spatial", "bbox", "survey"]'::jsonb,
    TRUE,
    TRUE
),

-- INVENTORY TEMPLATES

(
    'Material Inventory',
    'Search utility lines by material type',
    'utility_lines',
    '{
        "material": null,
        "is_active": true
    }'::jsonb,
    '["material", "line_type", "municipality"]'::jsonb,
    'material ASC',
    '["line_number", "line_type", "material", "diameter", "length_ft", "project_name"]'::jsonb,
    'Inventory',
    '["inventory", "materials", "utilities"]'::jsonb,
    TRUE,
    TRUE
),

(
    'Structure Type Inventory',
    'Count and list structures by type',
    'utility_structures',
    '{
        "structure_type_id": null,
        "is_active": true
    }'::jsonb,
    '["structure_type", "municipality", "project"]'::jsonb,
    'structure_type ASC',
    '["structure_number", "structure_type", "rim_elevation", "municipality", "project_name"]'::jsonb,
    'Inventory',
    '["inventory", "structures", "count"]'::jsonb,
    TRUE,
    TRUE
),

-- TEMPORAL TEMPLATES

(
    'Recent Survey Work',
    'Find survey points collected within a date range',
    'survey_points',
    '{
        "date_range": {
            "field": "survey_date",
            "start": null,
            "end": null
        }
    }'::jsonb,
    '["survey_method", "surveyed_by", "point_description"]'::jsonb,
    'survey_date DESC',
    '["point_number", "point_description", "survey_date", "survey_method", "surveyed_by"]'::jsonb,
    'Temporal Analysis',
    '["temporal", "date range", "survey"]'::jsonb,
    TRUE,
    TRUE
),

(
    'Active Projects',
    'Find projects by status and date range',
    'projects',
    '{
        "status": "Active",
        "date_range": {
            "field": "start_date",
            "start": null,
            "end": null
        }
    }'::jsonb,
    '["status", "municipality", "client"]'::jsonb,
    'start_date DESC',
    '["project_number", "project_name", "client", "municipality", "status", "start_date"]'::jsonb,
    'Project Management',
    '["projects", "active", "temporal"]'::jsonb,
    TRUE,
    TRUE
),

-- COMPLIANCE TEMPLATES

(
    'Inspection Due Soon',
    'Find structures requiring inspection within next 30 days',
    'utility_structures',
    '{
        "requires_inspection": true,
        "inspection_due_days": 30
    }'::jsonb,
    '["structure_type", "municipality", "project"]'::jsonb,
    'last_inspection_date ASC',
    '["structure_number", "structure_type", "last_inspection_date", "municipality"]'::jsonb,
    'Compliance',
    '["compliance", "inspection", "temporal"]'::jsonb,
    TRUE,
    TRUE
),

(
    'High Elevation Points',
    'Find survey points above elevation threshold',
    'survey_points',
    '{
        "elevation_range": {
            "min": null,
            "max": null
        }
    }'::jsonb,
    '["point_description", "survey_method"]'::jsonb,
    'elevation DESC',
    '["point_number", "point_description", "elevation", "northing", "easting"]'::jsonb,
    'Analysis',
    '["elevation", "filtering", "survey"]'::jsonb,
    TRUE,
    TRUE
),

-- PROJECT-SPECIFIC TEMPLATES

(
    'Project Asset Summary',
    'Complete inventory of all assets in a project',
    'utility_structures',
    '{
        "project_id": null,
        "is_active": true,
        "include_related": ["survey_points", "utility_lines"]
    }'::jsonb,
    '["structure_type", "material"]'::jsonb,
    'structure_number ASC',
    '["structure_number", "structure_type", "rim_elevation", "invert_elevation"]'::jsonb,
    'Project Management',
    '["project", "inventory", "comprehensive"]'::jsonb,
    TRUE,
    TRUE
),

(
    'Client Projects',
    'Find all projects for a specific client',
    'projects',
    '{
        "client_name": null
    }'::jsonb,
    '["status", "municipality"]'::jsonb,
    'start_date DESC',
    '["project_number", "project_name", "client", "municipality", "status", "start_date"]'::jsonb,
    'Project Management',
    '["client", "projects", "search"]'::jsonb,
    TRUE,
    TRUE
),

-- DATA ANALYSIS TEMPLATES

(
    'Large Diameter Pipes',
    'Find utility lines above diameter threshold',
    'utility_lines',
    '{
        "diameter_range": {
            "min": 24,
            "max": null
        },
        "is_active": true
    }'::jsonb,
    '["material", "line_type", "municipality"]'::jsonb,
    'diameter DESC',
    '["line_number", "line_type", "material", "diameter", "length_ft", "slope"]'::jsonb,
    'Analysis',
    '["diameter", "filtering", "utilities"]'::jsonb,
    TRUE,
    TRUE
),

(
    'Steep Slope Analysis',
    'Find utility lines with slope above threshold',
    'utility_lines',
    '{
        "slope_range": {
            "min": 5.0,
            "max": null
        },
        "is_active": true
    }'::jsonb,
    '["line_type", "material"]'::jsonb,
    'slope DESC',
    '["line_number", "line_type", "slope", "length_ft", "upstream_invert", "downstream_invert"]'::jsonb,
    'Analysis',
    '["slope", "hydraulics", "utilities"]'::jsonb,
    TRUE,
    TRUE
);

-- Initialize usage counts
UPDATE saved_search_templates SET usage_count = 0 WHERE is_system_template = TRUE;

-- Build initial facet cache for common entity types
SELECT rebuild_facet_cache('utility_structures');
SELECT rebuild_facet_cache('survey_points');
