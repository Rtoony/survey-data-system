-- Seed Validation Rules for Validation Engine
-- 15 validation rules across 5 categories

-- ============================================
-- GEOMETRY VALIDATION (3 rules)
-- ============================================

-- 1. Points Must Have Elevations
INSERT INTO validation_rules (
    rule_name,
    rule_description,
    entity_type,
    rule_type,
    severity,
    sql_check_query,
    auto_fix_query,
    parameters
) VALUES (
    'Points Must Have Elevations',
    'All survey points should have valid elevation values',
    'survey_points',
    'geometry',
    'error',
    'SELECT id FROM survey_points WHERE elevation IS NULL AND is_active = TRUE',
    NULL,
    '{}'
) ON CONFLICT DO NOTHING;

-- 2. Lines Must Have Positive Length
INSERT INTO validation_rules (
    rule_name,
    rule_description,
    entity_type,
    rule_type,
    severity,
    sql_check_query,
    auto_fix_query,
    parameters
) VALUES (
    'Lines Must Have Positive Length',
    'Utility lines must have geometry with length greater than zero',
    'utility_lines',
    'geometry',
    'error',
    'SELECT id FROM utility_lines WHERE ST_Length(geometry) <= 0 AND is_active = TRUE',
    NULL,
    '{}'
) ON CONFLICT DO NOTHING;

-- 3. Rim Above Invert
INSERT INTO validation_rules (
    rule_name,
    rule_description,
    entity_type,
    rule_type,
    severity,
    sql_check_query,
    auto_fix_query,
    parameters
) VALUES (
    'Rim Elevation Above Invert',
    'Structure rim elevation must be greater than invert elevation',
    'utility_structures',
    'geometry',
    'error',
    'SELECT id FROM utility_structures WHERE rim_elevation IS NOT NULL AND invert_elevation IS NOT NULL AND rim_elevation <= invert_elevation AND is_active = TRUE',
    NULL,
    '{}'
) ON CONFLICT DO NOTHING;

-- ============================================
-- CONNECTIVITY VALIDATION (3 rules)
-- ============================================

-- 4. Orphaned Structures
INSERT INTO validation_rules (
    rule_name,
    rule_description,
    entity_type,
    rule_type,
    severity,
    sql_check_query,
    auto_fix_query,
    parameters
) VALUES (
    'Orphaned Structures',
    'Structures should be connected to at least one utility line',
    'utility_structures',
    'connectivity',
    'warning',
    'SELECT s.id FROM utility_structures s LEFT JOIN utility_lines l ON s.id IN (l.upstream_structure_id, l.downstream_structure_id) WHERE l.id IS NULL AND s.is_active = TRUE',
    NULL,
    '{}'
) ON CONFLICT DO NOTHING;

-- 5. Disconnected Pipes
INSERT INTO validation_rules (
    rule_name,
    rule_description,
    entity_type,
    rule_type,
    severity,
    sql_check_query,
    auto_fix_query,
    parameters
) VALUES (
    'Disconnected Pipes',
    'Utility lines should have both upstream and downstream structure connections',
    'utility_lines',
    'connectivity',
    'warning',
    'SELECT id FROM utility_lines WHERE (upstream_structure_id IS NULL OR downstream_structure_id IS NULL) AND is_active = TRUE',
    NULL,
    '{}'
) ON CONFLICT DO NOTHING;

-- 6. Network Continuity Check
INSERT INTO validation_rules (
    rule_name,
    rule_description,
    entity_type,
    rule_type,
    severity,
    sql_check_query,
    auto_fix_query,
    parameters
) VALUES (
    'Network Continuity',
    'Check for gaps in network connectivity and flow direction',
    'utility_lines',
    'connectivity',
    'info',
    'SELECT id FROM utility_lines WHERE upstream_structure_id = downstream_structure_id AND is_active = TRUE',
    NULL,
    '{}'
) ON CONFLICT DO NOTHING;

-- ============================================
-- COMPLETENESS VALIDATION (3 rules)
-- ============================================

-- 7. Missing Material
INSERT INTO validation_rules (
    rule_name,
    rule_description,
    entity_type,
    rule_type,
    severity,
    sql_check_query,
    auto_fix_query,
    parameters
) VALUES (
    'Missing Material',
    'Utility lines should have material specified',
    'utility_lines',
    'completeness',
    'warning',
    'SELECT id FROM utility_lines WHERE material IS NULL AND is_active = TRUE',
    NULL,
    '{}'
) ON CONFLICT DO NOTHING;

-- 8. Missing Structure Type
INSERT INTO validation_rules (
    rule_name,
    rule_description,
    entity_type,
    rule_type,
    severity,
    sql_check_query,
    auto_fix_query,
    parameters
) VALUES (
    'Missing Structure Type',
    'Utility structures should have a structure type specified',
    'utility_structures',
    'completeness',
    'warning',
    'SELECT id FROM utility_structures WHERE structure_type IS NULL AND is_active = TRUE',
    NULL,
    '{}'
) ON CONFLICT DO NOTHING;

-- 9. Missing Survey Method
INSERT INTO validation_rules (
    rule_name,
    rule_description,
    entity_type,
    rule_type,
    severity,
    sql_check_query,
    auto_fix_query,
    parameters
) VALUES (
    'Missing Survey Method',
    'Survey points should have collection method specified',
    'survey_points',
    'completeness',
    'info',
    'SELECT id FROM survey_points WHERE survey_method_id IS NULL AND is_active = TRUE',
    NULL,
    '{}'
) ON CONFLICT DO NOTHING;

-- ============================================
-- SURVEY VALIDATION (3 rules)
-- ============================================

-- 10. Elevation Range Check
INSERT INTO validation_rules (
    rule_name,
    rule_description,
    entity_type,
    rule_type,
    severity,
    sql_check_query,
    auto_fix_query,
    parameters
) VALUES (
    'Elevation Range Check',
    'Survey points should have realistic elevation values',
    'survey_points',
    'survey',
    'error',
    'SELECT id FROM survey_points WHERE elevation < -100 OR elevation > 10000 AND is_active = TRUE',
    NULL,
    '{"min_elevation": -100, "max_elevation": 10000}'
) ON CONFLICT DO NOTHING;

-- 11. Duplicate Point Numbers
INSERT INTO validation_rules (
    rule_name,
    rule_description,
    entity_type,
    rule_type,
    severity,
    sql_check_query,
    auto_fix_query,
    parameters
) VALUES (
    'Duplicate Point Numbers',
    'Point numbers should be unique within a project',
    'survey_points',
    'survey',
    'warning',
    'SELECT id FROM survey_points WHERE point_number IN (SELECT point_number FROM survey_points WHERE is_active = TRUE GROUP BY point_number, project_id HAVING COUNT(*) > 1) AND is_active = TRUE',
    NULL,
    '{}'
) ON CONFLICT DO NOTHING;

-- 12. Missing Control Points
INSERT INTO validation_rules (
    rule_name,
    rule_description,
    entity_type,
    rule_type,
    severity,
    sql_check_query,
    auto_fix_query,
    parameters
) VALUES (
    'Project Has Control Points',
    'Projects should have at least one control point',
    'survey_points',
    'survey',
    'warning',
    'SELECT DISTINCT project_id FROM projects p WHERE NOT EXISTS (SELECT 1 FROM survey_points sp WHERE sp.project_id = p.id AND sp.point_type = ''control'' AND sp.is_active = TRUE) AND p.is_active = TRUE',
    NULL,
    '{}'
) ON CONFLICT DO NOTHING;

-- ============================================
-- CAD STANDARDS VALIDATION (3 rules)
-- ============================================

-- 13. Invalid Layer Names
INSERT INTO validation_rules (
    rule_name,
    rule_description,
    entity_type,
    rule_type,
    severity,
    sql_check_query,
    auto_fix_query,
    parameters
) VALUES (
    'Invalid Layer Names',
    'Entities should use standard layer naming conventions',
    'generic_entities',
    'cad_standards',
    'warning',
    'SELECT id FROM generic_entities WHERE layer_name NOT SIMILAR TO ''[A-Z]+-[A-Z]+-[A-Z0-9]+'' AND is_active = TRUE',
    NULL,
    '{}'
) ON CONFLICT DO NOTHING;

-- 14. Missing Project Assignment
INSERT INTO validation_rules (
    rule_name,
    rule_description,
    entity_type,
    rule_type,
    severity,
    sql_check_query,
    auto_fix_query,
    parameters
) VALUES (
    'Missing Project Assignment',
    'All entities should be assigned to a project',
    'generic_entities',
    'cad_standards',
    'error',
    'SELECT id FROM generic_entities WHERE project_id IS NULL AND is_active = TRUE',
    NULL,
    '{}'
) ON CONFLICT DO NOTHING;

-- 15. Geometry Validation
INSERT INTO validation_rules (
    rule_name,
    rule_description,
    entity_type,
    rule_type,
    severity,
    sql_check_query,
    auto_fix_query,
    parameters
) VALUES (
    'Valid Geometry',
    'All spatial entities must have valid PostGIS geometry',
    'generic_entities',
    'cad_standards',
    'error',
    'SELECT id FROM generic_entities WHERE geometry IS NOT NULL AND NOT ST_IsValid(geometry) AND is_active = TRUE',
    NULL,
    '{}'
) ON CONFLICT DO NOTHING;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Validation rules seeded successfully! Total: 15 rules';
END $$;
