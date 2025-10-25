-- Sheet Set Manager Database Schema
-- Creates tables for managing construction document sheet sets, sheets, and related data

-- Project Details table (metadata for projects)
CREATE TABLE IF NOT EXISTS project_details (
    project_id UUID PRIMARY KEY REFERENCES projects(project_id) ON DELETE CASCADE,
    project_address TEXT,
    project_city VARCHAR(100),
    project_state VARCHAR(2),
    project_zip VARCHAR(10),
    engineer_name VARCHAR(200),
    engineer_license VARCHAR(50),
    jurisdiction VARCHAR(200),
    permit_number VARCHAR(100),
    contact_name VARCHAR(200),
    contact_phone VARCHAR(20),
    contact_email VARCHAR(200),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Standard sheet categories (COVER, DEMO, GRAD, UTIL, etc.)
CREATE TABLE IF NOT EXISTS sheet_category_standards (
    category_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_code VARCHAR(20) UNIQUE NOT NULL,
    category_name VARCHAR(100) NOT NULL,
    default_hierarchy_number INTEGER NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sheet Sets (deliverable packages like "100% Civil Plans")
CREATE TABLE IF NOT EXISTS sheet_sets (
    set_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    set_name VARCHAR(200) NOT NULL,
    set_number VARCHAR(50),
    phase VARCHAR(100),
    discipline VARCHAR(100),
    issue_date DATE,
    status VARCHAR(50) DEFAULT 'draft',
    recipient TEXT,
    transmittal_notes TEXT,
    sheet_note_set_id UUID REFERENCES sheet_note_sets(set_id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Individual sheets within a set
CREATE TABLE IF NOT EXISTS sheets (
    sheet_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    set_id UUID NOT NULL REFERENCES sheet_sets(set_id) ON DELETE CASCADE,
    sheet_number INTEGER,
    sheet_code VARCHAR(50) NOT NULL,
    sheet_title VARCHAR(300) NOT NULL,
    discipline_code VARCHAR(10),
    sheet_type VARCHAR(50),
    category_code VARCHAR(20) REFERENCES sheet_category_standards(category_code),
    sheet_hierarchy_number INTEGER,
    scale VARCHAR(50),
    sheet_size VARCHAR(20) DEFAULT '24x36',
    template_id UUID REFERENCES sheet_templates(template_id),
    revision_number INTEGER DEFAULT 0,
    revision_date DATE,
    notes TEXT,
    tags TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(set_id, sheet_code),
    UNIQUE(set_id, sheet_number)
);

-- Drawing assignments (linking sheets to DXF drawings and layouts)
CREATE TABLE IF NOT EXISTS sheet_drawing_assignments (
    assignment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sheet_id UUID NOT NULL REFERENCES sheets(sheet_id) ON DELETE CASCADE,
    drawing_id UUID REFERENCES drawings(drawing_id),
    layout_name VARCHAR(255),
    assigned_by VARCHAR(200),
    assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    UNIQUE(sheet_id)
);

-- Revision tracking for sheets
CREATE TABLE IF NOT EXISTS sheet_revisions (
    revision_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sheet_id UUID NOT NULL REFERENCES sheets(sheet_id) ON DELETE CASCADE,
    revision_number INTEGER NOT NULL,
    revision_date DATE NOT NULL,
    description TEXT,
    revised_by VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Relationships between sheets (references, details, etc.)
CREATE TABLE IF NOT EXISTS sheet_relationships (
    relationship_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_sheet_id UUID NOT NULL REFERENCES sheets(sheet_id) ON DELETE CASCADE,
    target_sheet_id UUID NOT NULL REFERENCES sheets(sheet_id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_sheet_id, target_sheet_id, relationship_type)
);

-- Sample standard categories
INSERT INTO sheet_category_standards (category_code, category_name, default_hierarchy_number, description) VALUES
('COVER', 'Cover Sheet', 0, 'Title and index sheet'),
('DEMO', 'Demolition Plans', 10, 'Demolition and removal plans'),
('GRAD', 'Grading Plans', 20, 'Grading and earthwork plans'),
('UTIL', 'Utility Plans', 30, 'Water, sewer, storm drain utilities'),
('PAVE', 'Paving Plans', 40, 'Street and parking lot paving'),
('DETAIL', 'Details', 90, 'Construction details and notes'),
('PROF', 'Profiles', 50, 'Street and utility profiles'),
('XSEC', 'Cross Sections', 60, 'Roadway cross sections'),
('LAND', 'Landscape Plans', 70, 'Landscaping and irrigation'),
('NOTES', 'General Notes', 95, 'General notes and specifications')
ON CONFLICT (category_code) DO NOTHING;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_sheet_sets_project ON sheet_sets(project_id);
CREATE INDEX IF NOT EXISTS idx_sheets_set ON sheets(set_id);
CREATE INDEX IF NOT EXISTS idx_sheets_hierarchy ON sheets(set_id, sheet_hierarchy_number, sheet_code);
CREATE INDEX IF NOT EXISTS idx_drawing_assignments_sheet ON sheet_drawing_assignments(sheet_id);
CREATE INDEX IF NOT EXISTS idx_revisions_sheet ON sheet_revisions(sheet_id);
CREATE INDEX IF NOT EXISTS idx_relationships_source ON sheet_relationships(source_sheet_id);

COMMENT ON TABLE sheet_sets IS 'Deliverable packages of construction documents';
COMMENT ON TABLE sheets IS 'Individual sheets within a sheet set';
COMMENT ON TABLE sheet_category_standards IS 'Standard sheet categories with hierarchy ordering';
COMMENT ON TABLE sheet_drawing_assignments IS 'Links sheets to DXF drawings and layout tabs';
