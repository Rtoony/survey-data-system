-- ============================================================================
-- SEED STANDARD CATEGORIES
-- ============================================================================
-- Pre-populates standard_categories with common CAD discipline categories
-- Based on standards/cad_standards_vocabulary.md
-- ============================================================================

-- Insert base categories
INSERT INTO standard_categories (category_code, category_name, description, sort_order) VALUES
('CIVIL', 'Civil Engineering', 'Civil engineering elements (streets, curbs, sidewalks)', 10),
('SURVEY', 'Survey & Monuments', 'Survey control points, monuments, benchmarks', 20),
('UTILITIES', 'Utilities', 'Water, sewer, gas, electric, telecom utilities', 30),
('LANDSCAPE', 'Landscape & Planting', 'Trees, shrubs, plants, irrigation', 40),
('GRADING', 'Grading & Earthwork', 'Contours, spot elevations, grading plans', 50),
('DRAINAGE', 'Drainage & Stormwater', 'Storm drains, catch basins, channels', 60),
('ADA', 'ADA Compliance', 'Accessibility features (ramps, paths, parking)', 70),
('TRAFFIC', 'Traffic & Signage', 'Signs, striping, traffic control', 80),
('ANNOTATION', 'Annotations & Notes', 'Text, callouts, dimensions, notes', 90),
('GENERAL', 'General', 'General/miscellaneous elements', 100)
ON CONFLICT (category_code) DO NOTHING;

-- Map categories to standard types
WITH inserted_categories AS (
    SELECT category_id, category_code FROM standard_categories
)
INSERT INTO standard_category_applications (category_id, standard_type, is_primary)
SELECT 
    ic.category_id,
    st.standard_type,
    CASE WHEN st.standard_type IN ('layers', 'blocks', 'notes') THEN TRUE ELSE FALSE END
FROM inserted_categories ic
CROSS JOIN (
    VALUES 
        ('layers'),
        ('blocks'),
        ('details'),
        ('hatches'),
        ('materials'),
        ('notes'),
        ('linetypes'),
        ('abbreviations')
) AS st(standard_type)
ON CONFLICT (category_id, standard_type) DO NOTHING;

COMMENT ON TABLE standard_categories IS 'Seeded with 10 standard CAD discipline categories from vocabulary guide';
