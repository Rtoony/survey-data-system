-- Seed standard disciplines
INSERT INTO standard_disciplines (discipline_code, discipline_name, description, sort_order) VALUES
('CIVIL', 'Civil Engineering', 'Civil engineering and infrastructure', 10),
('SURVEY', 'Survey', 'Land surveying and geodetic control', 20),
('LANDSCAPE', 'Landscape Architecture', 'Landscape design and planting', 30),
('ELECTRICAL', 'Electrical', 'Electrical systems and power distribution', 40),
('MECHANICAL', 'Mechanical', 'HVAC and mechanical systems', 50),
('PLUMBING', 'Plumbing', 'Plumbing and water distribution', 60),
('STRUCTURAL', 'Structural', 'Structural engineering', 70),
('ARCHITECTURAL', 'Architectural', 'Architectural design', 80),
('GENERAL', 'General', 'General/multi-discipline', 90)
ON CONFLICT (discipline_code) DO NOTHING;

-- Map disciplines to standard types
WITH inserted_disciplines AS (
    SELECT discipline_id, discipline_code FROM standard_disciplines
)
INSERT INTO standard_discipline_applications (discipline_id, standard_type, is_primary)
SELECT 
    id.discipline_id,
    st.standard_type,
    TRUE
FROM inserted_disciplines id
CROSS JOIN (
    VALUES 
        ('layers'), ('blocks'), ('details'), ('hatches'),
        ('materials'), ('notes'), ('linetypes'), ('abbreviations')
) AS st(standard_type)
ON CONFLICT (discipline_id, standard_type) DO NOTHING;
