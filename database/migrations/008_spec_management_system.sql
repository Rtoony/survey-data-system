-- ============================================================================
-- UNIVERSAL SPECIFICATION MANAGEMENT SYSTEM
-- Phase 1: Core Schema
-- ============================================================================

-- Step 1: Create spec_standards_registry (The "WHO" - Reference Data Hub table)
CREATE TABLE IF NOT EXISTS spec_standards_registry (
    spec_standard_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID UNIQUE, -- For AI, FTS, and Graph linking

    standard_name VARCHAR(100) NOT NULL UNIQUE, -- e.g., 'Caltrans', 'DSA', 'AWWA'
    governing_body VARCHAR(255), -- e.g., 'California Dept. of Transportation'
    description TEXT,
    abbreviation VARCHAR(20), -- e.g., 'CT', 'DSA', 'AWWA'
    website_url VARCHAR(500),

    -- Standard AI/Audit Columns
    search_vector TSVECTOR,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_spec_standards_entity_id ON spec_standards_registry(entity_id);
CREATE INDEX idx_spec_standards_search_vector ON spec_standards_registry USING GIN(search_vector);

-- Step 2: Create ENUM for source tracking
CREATE TYPE spec_source_type AS ENUM (
    'standard',          -- Used as-is from the library
    'modified_standard', -- Based on a library spec, but with edits
    'custom'             -- Created from scratch for this project
);

-- Step 3: Create spec_library (The "WHAT" - Master Content Library)
CREATE TABLE IF NOT EXISTS spec_library (
    spec_library_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID UNIQUE, -- FK to standards_entities

    -- Link to governing body (KEY: NOT an ENUM, links to registry table)
    spec_standard_id UUID NOT NULL REFERENCES spec_standards_registry(spec_standard_id) ON DELETE RESTRICT,

    -- Flexible identification (supports all systems)
    spec_number VARCHAR(50) NOT NULL, -- e.g., '19-3.03', '05A', 'C110'
    spec_title VARCHAR(500) NOT NULL,
    source_document VARCHAR(255), -- e.g., 'Caltrans 2023 Standard Specs'

    -- Flexible content structure
    content_structure VARCHAR(50) DEFAULT 'narrative', -- '3-part', 'narrative', 'tabular', 'reference'
    content_json JSONB, -- Structured content (flexible based on content_structure)
    content_text TEXT,  -- Full text for FTS and AI embedding

    -- Metadata
    revision_date DATE,
    effective_date DATE,
    supersedes_spec_id UUID REFERENCES spec_library(spec_library_id), -- Version history tracking

    -- Standard AI/Audit Columns
    quality_score NUMERIC(2,1) DEFAULT 0.0,
    search_vector TSVECTOR,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(spec_standard_id, spec_number, source_document)
);

CREATE INDEX idx_spec_library_entity_id ON spec_library(entity_id);
CREATE INDEX idx_spec_library_standard_id ON spec_library(spec_standard_id);
CREATE INDEX idx_spec_library_spec_number ON spec_library(spec_number);
CREATE INDEX idx_spec_library_search_vector ON spec_library USING GIN(search_vector);
CREATE INDEX idx_spec_library_content_json ON spec_library USING GIN(content_json);

-- Step 4: Create project_specs (The "HOW" - Variance Tracking Instance)
CREATE TABLE IF NOT EXISTS project_specs (
    project_spec_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID UNIQUE NOT NULL, -- The *project-level* entity for Relationship Sets
    project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,

    -- Link to the "parent" standard, if any (NULL if 'custom')
    spec_library_id UUID REFERENCES spec_library(spec_library_id) ON DELETE SET NULL,

    -- Variance tracking (follows Sheet Notes pattern)
    source_type spec_source_type NOT NULL,

    -- Project-specific content (NULL if 'standard', populated if 'modified' or 'custom')
    project_content_json JSONB NULL,

    -- Denormalized data for custom specs (for faster queries)
    project_spec_number VARCHAR(50),
    project_spec_title VARCHAR(500),

    -- Deviation tracking (WHY was this modified/custom?)
    deviation_reason TEXT,
    modified_by VARCHAR(255), -- User who made the modification

    -- Standard audit columns
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_project_specs_entity_id ON project_specs(entity_id);
CREATE INDEX idx_project_specs_project_id ON project_specs(project_id);
CREATE INDEX idx_project_specs_spec_library_id ON project_specs(spec_library_id);
CREATE INDEX idx_project_specs_source_type ON project_specs(source_type);

-- Step 5: Create entity_spec_requirements (The "WHERE" - Golden Link table)
CREATE TABLE IF NOT EXISTS entity_spec_requirements (
    requirement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Source entity (utility line, structure, layer, detail, etc.)
    entity_id UUID NOT NULL, -- Links to standards_entities
    entity_type VARCHAR(50) NOT NULL, -- 'utility_line', 'layer', 'utility_structure', etc.

    -- Target spec from library
    spec_library_id UUID NOT NULL REFERENCES spec_library(spec_library_id) ON DELETE CASCADE,

    -- Relationship context
    requirement_type VARCHAR(50) DEFAULT 'general', -- 'material', 'installation', 'testing', 'inspection', 'general'
    is_mandatory BOOLEAN DEFAULT true,

    -- Optional conditional matching (when does this apply?)
    applies_when JSONB, -- e.g., {"material": "PVC", "diameter_inches_gte": 12}

    -- Documentation
    notes TEXT,
    created_by VARCHAR(255),

    -- Standard audit
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_entity_spec_req_entity ON entity_spec_requirements(entity_id);
CREATE INDEX idx_entity_spec_req_spec ON entity_spec_requirements(spec_library_id);
CREATE INDEX idx_entity_spec_req_entity_type ON entity_spec_requirements(entity_type);
CREATE INDEX idx_entity_spec_req_applies_when ON entity_spec_requirements USING GIN(applies_when);

-- Step 6: Create view for "effective content" (simplifies project spec queries)
CREATE OR REPLACE VIEW vw_project_spec_content AS
SELECT
    ps.project_spec_id,
    ps.entity_id AS project_entity_id,
    ps.project_id,
    ps.source_type,
    ps.spec_library_id,

    -- Effective content (project content if exists, else library content)
    COALESCE(ps.project_content_json, sl.content_json) AS effective_content_json,
    COALESCE(ps.project_content_json::text, sl.content_text) AS effective_content_text,

    -- Effective identifiers
    COALESCE(ps.project_spec_number, sl.spec_number) AS effective_spec_number,
    COALESCE(ps.project_spec_title, sl.spec_title) AS effective_spec_title,

    -- Library reference info
    sl.entity_id AS library_entity_id,
    sr.standard_name,
    sr.abbreviation AS standard_abbreviation,
    sl.source_document,
    sl.content_structure,

    -- Metadata
    ps.deviation_reason,
    ps.modified_by,
    ps.created_at,
    ps.updated_at
FROM
    project_specs ps
LEFT JOIN
    spec_library sl ON ps.spec_library_id = sl.spec_library_id
LEFT JOIN
    spec_standards_registry sr ON sl.spec_standard_id = sr.spec_standard_id;

-- Step 7: Seed spec_standards_registry with common California standards
INSERT INTO spec_standards_registry (standard_name, governing_body, description, abbreviation, website_url) VALUES
    ('Caltrans', 'California Department of Transportation', 'State highway and transportation construction standards', 'CT', 'https://dot.ca.gov/programs/design'),
    ('APWA - Greenbook', 'American Public Works Association', 'Public works construction standards (Greenbook)', 'APWA', 'https://www.apwa.org/'),
    ('DSA', 'Division of the State Architect', 'School and community college construction standards', 'DSA', 'https://www.dgs.ca.gov/DSA'),
    ('AWWA', 'American Water Works Association', 'Water system design and construction standards', 'AWWA', 'https://www.awwa.org/'),
    ('ASCE', 'American Society of Civil Engineers', 'General civil engineering standards', 'ASCE', 'https://www.asce.org/'),
    ('Firm Standard', 'Internal Company Standards', 'Company-specific design and construction standards', 'FIRM', NULL)
ON CONFLICT (standard_name) DO NOTHING;

-- Step 8: Create sample specs for testing (Caltrans examples)
DO $$
DECLARE
    caltrans_id UUID;
BEGIN
    SELECT spec_standard_id INTO caltrans_id FROM spec_standards_registry WHERE standard_name = 'Caltrans';

    INSERT INTO spec_library (spec_standard_id, spec_number, spec_title, content_structure, content_text, source_document) VALUES
        (caltrans_id, '19-3.03', 'Storm Drain Pipe Installation', 'narrative', 'Install storm drain pipe on approved bedding material. Backfill and compact per Section 19-3. Maintain alignment and grade per plan requirements.', 'Caltrans 2023 Standard Specifications'),
        (caltrans_id, '19-3.02', 'Sanitary Sewer Installation', 'narrative', 'Install sanitary sewer pipe with watertight joints. Test per Section 19-6. Maintain minimum cover and slopes per plan.', 'Caltrans 2023 Standard Specifications'),
        (caltrans_id, '39-2', 'Asphalt Concrete Pavement', 'narrative', 'Place hot mix asphalt concrete per specified thickness and temperature requirements. Compact to 95% density minimum.', 'Caltrans 2023 Standard Specifications'),
        (caltrans_id, '52-1', 'Reinforcing Steel', 'narrative', 'Furnish and install reinforcing steel per ASTM specifications. Maintain required concrete cover and spacing.', 'Caltrans 2023 Standard Specifications'),
        (caltrans_id, '4-1.03', 'Survey Monuments', 'narrative', 'Set permanent survey monuments at all key control points. Monuments shall meet county surveyor standards.', 'Caltrans 2023 Standard Specifications')
    ON CONFLICT DO NOTHING;
END $$;

COMMENT ON TABLE spec_standards_registry IS 'Reference Data Hub table: Defines governing bodies and standards organizations (Caltrans, DSA, AWWA, etc.). Fully UI-editable.';
COMMENT ON TABLE spec_library IS 'Master library of specification sections. Links to spec_standards_registry. Project-agnostic reference data.';
COMMENT ON TABLE project_specs IS 'Project-specific spec instances. Tracks variance (standard/modified/custom) following Sheet Notes pattern.';
COMMENT ON TABLE entity_spec_requirements IS 'Links CAD/GIS entities to required specs. The "golden link" enabling automated compliance checking.';
