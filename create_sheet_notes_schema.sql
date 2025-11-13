-- Sheet Note Manager Database Schema
-- This schema supports construction drawing note management

-- Standard Notes Library (company-wide note templates)
CREATE TABLE IF NOT EXISTS standard_notes (
    note_id SERIAL PRIMARY KEY,
    note_title VARCHAR(255) NOT NULL,
    note_text TEXT NOT NULL,
    note_category VARCHAR(100),
    discipline VARCHAR(50),
    tags TEXT[],
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sheet Note Sets (project-specific note collections)
CREATE TABLE IF NOT EXISTS sheet_note_sets (
    set_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    set_name VARCHAR(255) NOT NULL,
    description TEXT,
    discipline VARCHAR(50),
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Project Sheet Notes (notes within a set, either from standards or custom)
CREATE TABLE IF NOT EXISTS project_sheet_notes (
    project_note_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    set_id UUID NOT NULL REFERENCES sheet_note_sets(set_id) ON DELETE CASCADE,
    standard_note_id INTEGER REFERENCES standard_notes(note_id),
    display_code VARCHAR(20) NOT NULL,
    custom_title VARCHAR(255),
    custom_text TEXT,
    is_modified BOOLEAN DEFAULT FALSE,
    usage_count INTEGER DEFAULT 0,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sheet Note Assignments (which notes appear on which sheets)
CREATE TABLE IF NOT EXISTS sheet_note_assignments (
    assignment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_note_id UUID NOT NULL REFERENCES project_sheet_notes(project_note_id) ON DELETE CASCADE,
    layout_name VARCHAR(100) DEFAULT 'Model',
    legend_sequence INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Note Callouts (for future use - linking notes to specific drawing locations)
CREATE TABLE IF NOT EXISTS note_callouts (
    callout_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assignment_id UUID NOT NULL REFERENCES sheet_note_assignments(assignment_id) ON DELETE CASCADE,
    location_x DOUBLE PRECISION,
    location_y DOUBLE PRECISION,
    callout_style VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Note Block Type Associations (for future use - linking notes to block types)
CREATE TABLE IF NOT EXISTS note_block_type_associations (
    association_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    note_id INTEGER NOT NULL REFERENCES standard_notes(note_id) ON DELETE CASCADE,
    block_type VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_sheet_note_sets_project ON sheet_note_sets(project_id);
CREATE INDEX IF NOT EXISTS idx_project_sheet_notes_set ON project_sheet_notes(set_id);
CREATE INDEX IF NOT EXISTS idx_project_sheet_notes_note ON project_sheet_notes(standard_note_id);
CREATE INDEX IF NOT EXISTS idx_sheet_note_assignments_note ON sheet_note_assignments(project_note_id);
CREATE INDEX IF NOT EXISTS idx_standard_notes_category ON standard_notes(note_category);
CREATE INDEX IF NOT EXISTS idx_standard_notes_discipline ON standard_notes(discipline);

-- Add some sample standard notes for testing
INSERT INTO standard_notes (note_title, note_text, note_category, discipline, sort_order) VALUES
('General Contractor Note', 'General contractor shall verify all dimensions and conditions in the field before proceeding with work.', 'General', 'All', 1),
('Utility Coordination', 'Contractor shall coordinate with all utility companies before excavation.', 'Utilities', 'Civil', 2),
('Survey Control', 'Survey control points shown are based on GPS observations and should be verified by contractor.', 'Survey', 'Survey', 3),
('Erosion Control', 'Erosion and sediment control measures shall be in place prior to any grading operations.', 'Environmental', 'Civil', 4),
('As-Built Requirement', 'Contractor shall provide as-built drawings within 30 days of project completion.', 'General', 'All', 5),
('Materials Testing', 'All materials shall be tested and approved before installation.', 'Quality Control', 'All', 6),
('Traffic Control', 'Contractor shall maintain traffic control in accordance with MUTCD standards.', 'Safety', 'Civil', 7),
('Landscape Protection', 'Existing trees and landscaping within the drip line shall be protected during construction.', 'Landscape', 'Landscape', 8),
('Underground Utilities', 'Call before you dig - Contact utility locating service 811 at least 48 hours before excavation.', 'Utilities', 'Civil', 9),
('Demolition Safety', 'All demolition work shall comply with OSHA safety standards.', 'Safety', 'Demo', 10)
ON CONFLICT DO NOTHING;

COMMENT ON TABLE standard_notes IS 'Company-wide library of standard construction drawing notes';
COMMENT ON TABLE sheet_note_sets IS 'Project-specific collections of notes organized by discipline or purpose';
COMMENT ON TABLE project_sheet_notes IS 'Individual notes within a set, can reference standard notes or be custom';
COMMENT ON TABLE sheet_note_assignments IS 'Assignment of notes to specific drawings and layouts with legend sequence';
COMMENT ON TABLE note_callouts IS 'Spatial locations on drawings where notes are called out (future feature)';
COMMENT ON TABLE note_block_type_associations IS 'Links standard notes to specific CAD block types (future feature)';
