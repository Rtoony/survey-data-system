-- ==============================================================================
-- CAD Standards Name Mapping Tables
-- ==============================================================================
-- Purpose: Enable bidirectional DXF ↔ Database name translation
-- Created: 2025-11-09
--
-- These tables map canonical naming convention names (stored in standards tables)
-- to client-specific DXF aliases, supporting:
-- - Import mapping (client CAD → database)
-- - Export mapping (database → client CAD)
-- - Multiple aliases per canonical name
-- - Project-specific overrides
-- ==============================================================================

-- ==============================================================================
-- 1. Block Name Mappings
-- ==============================================================================
-- Maps canonical block names to client-specific DXF block names
CREATE TABLE IF NOT EXISTS block_name_mappings (
    mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    block_id UUID NOT NULL REFERENCES block_definitions(block_id) ON DELETE CASCADE,
    
    -- Canonical name (follows DISCIPLINE-CATEGORY-TYPE-[ATTRIBUTES]-PHASE-FORM)
    canonical_name VARCHAR(255) NOT NULL,
    
    -- DXF alias (client-specific or legacy name)
    dxf_alias VARCHAR(255) NOT NULL,
    
    -- Mapping direction
    direction VARCHAR(20) CHECK (direction IN ('import', 'export', 'both')) NOT NULL DEFAULT 'both',
    
    -- Client/project context
    client_name VARCHAR(255),
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    
    -- Metadata
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    confidence_score NUMERIC(3, 2) DEFAULT 1.0,
    
    -- AI-friendly search
    search_vector TSVECTOR,
    tags TEXT[],
    attributes JSONB DEFAULT '{}'::jsonb,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255)
);

CREATE INDEX idx_block_name_mappings_block_id ON block_name_mappings(block_id);
CREATE INDEX idx_block_name_mappings_dxf_alias ON block_name_mappings(dxf_alias);
CREATE INDEX idx_block_name_mappings_canonical ON block_name_mappings(canonical_name);
CREATE INDEX idx_block_name_mappings_client ON block_name_mappings(client_name) WHERE client_name IS NOT NULL;
CREATE INDEX idx_block_name_mappings_project ON block_name_mappings(project_id) WHERE project_id IS NOT NULL;
CREATE INDEX idx_block_name_mappings_search ON block_name_mappings USING GIN(search_vector);

-- Unique constraints with partial indexes for different scenarios
CREATE UNIQUE INDEX idx_block_name_mapping_unique_global 
    ON block_name_mappings(dxf_alias, direction) 
    WHERE client_name IS NULL AND project_id IS NULL;

CREATE UNIQUE INDEX idx_block_name_mapping_unique_client 
    ON block_name_mappings(dxf_alias, direction, client_name) 
    WHERE client_name IS NOT NULL AND project_id IS NULL;

CREATE UNIQUE INDEX idx_block_name_mapping_unique_project 
    ON block_name_mappings(dxf_alias, direction, project_id) 
    WHERE project_id IS NOT NULL;

-- ==============================================================================
-- 2. Detail Name Mappings
-- ==============================================================================
-- Maps canonical detail names to client-specific detail callout names
CREATE TABLE IF NOT EXISTS detail_name_mappings (
    mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    detail_id UUID NOT NULL REFERENCES detail_standards(detail_id) ON DELETE CASCADE,
    
    -- Canonical name (follows DISCIPLINE-DETAIL-FAMILY-SEQUENCE-[ATTRIBUTES]-PHASE-VIEW)
    canonical_name VARCHAR(255) NOT NULL,
    
    -- DXF/Drawing alias (client-specific detail number/name)
    dxf_alias VARCHAR(255) NOT NULL,
    
    -- Mapping direction
    direction VARCHAR(20) CHECK (direction IN ('import', 'export', 'both')) NOT NULL DEFAULT 'both',
    
    -- Client/project context
    client_name VARCHAR(255),
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    
    -- Detail sheet context
    sheet_number VARCHAR(50),
    detail_reference VARCHAR(100),  -- e.g., "Detail 5/C-3.1"
    
    -- Metadata
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    confidence_score NUMERIC(3, 2) DEFAULT 1.0,
    
    -- AI-friendly search
    search_vector TSVECTOR,
    tags TEXT[],
    attributes JSONB DEFAULT '{}'::jsonb,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255)
);

CREATE INDEX idx_detail_name_mappings_detail_id ON detail_name_mappings(detail_id);
CREATE INDEX idx_detail_name_mappings_dxf_alias ON detail_name_mappings(dxf_alias);
CREATE INDEX idx_detail_name_mappings_canonical ON detail_name_mappings(canonical_name);
CREATE INDEX idx_detail_name_mappings_client ON detail_name_mappings(client_name) WHERE client_name IS NOT NULL;
CREATE INDEX idx_detail_name_mappings_project ON detail_name_mappings(project_id) WHERE project_id IS NOT NULL;
CREATE INDEX idx_detail_name_mappings_search ON detail_name_mappings USING GIN(search_vector);

-- Unique constraints with partial indexes
CREATE UNIQUE INDEX idx_detail_name_mapping_unique_global 
    ON detail_name_mappings(dxf_alias, direction) 
    WHERE client_name IS NULL AND project_id IS NULL;

CREATE UNIQUE INDEX idx_detail_name_mapping_unique_client 
    ON detail_name_mappings(dxf_alias, direction, client_name) 
    WHERE client_name IS NOT NULL AND project_id IS NULL;

CREATE UNIQUE INDEX idx_detail_name_mapping_unique_project 
    ON detail_name_mappings(dxf_alias, direction, project_id) 
    WHERE project_id IS NOT NULL;

-- ==============================================================================
-- 3. Hatch Pattern Name Mappings
-- ==============================================================================
-- Maps canonical hatch pattern names to DXF hatch pattern names
CREATE TABLE IF NOT EXISTS hatch_pattern_name_mappings (
    mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hatch_id UUID NOT NULL REFERENCES hatch_patterns(hatch_id) ON DELETE CASCADE,
    
    -- Canonical name (follows MAT-CATEGORY-TEXTURE-[SCALE]-PHASE-HT)
    canonical_name VARCHAR(255) NOT NULL,
    
    -- DXF pattern name (as it appears in PAT files or DXF)
    dxf_alias VARCHAR(255) NOT NULL,
    
    -- Mapping direction
    direction VARCHAR(20) CHECK (direction IN ('import', 'export', 'both')) NOT NULL DEFAULT 'both',
    
    -- Client/project context
    client_name VARCHAR(255),
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    
    -- Pattern file context
    pat_file_name VARCHAR(255),  -- e.g., "acad.pat", "client_custom.pat"
    
    -- Metadata
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    confidence_score NUMERIC(3, 2) DEFAULT 1.0,
    
    -- AI-friendly search
    search_vector TSVECTOR,
    tags TEXT[],
    attributes JSONB DEFAULT '{}'::jsonb,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255)
);

CREATE INDEX idx_hatch_name_mappings_hatch_id ON hatch_pattern_name_mappings(hatch_id);
CREATE INDEX idx_hatch_name_mappings_dxf_alias ON hatch_pattern_name_mappings(dxf_alias);
CREATE INDEX idx_hatch_name_mappings_canonical ON hatch_pattern_name_mappings(canonical_name);
CREATE INDEX idx_hatch_name_mappings_client ON hatch_pattern_name_mappings(client_name) WHERE client_name IS NOT NULL;
CREATE INDEX idx_hatch_name_mappings_project ON hatch_pattern_name_mappings(project_id) WHERE project_id IS NOT NULL;
CREATE INDEX idx_hatch_name_mappings_search ON hatch_pattern_name_mappings USING GIN(search_vector);

-- Unique constraints with partial indexes
CREATE UNIQUE INDEX idx_hatch_name_mapping_unique_global 
    ON hatch_pattern_name_mappings(dxf_alias, direction) 
    WHERE client_name IS NULL AND project_id IS NULL;

CREATE UNIQUE INDEX idx_hatch_name_mapping_unique_client 
    ON hatch_pattern_name_mappings(dxf_alias, direction, client_name) 
    WHERE client_name IS NOT NULL AND project_id IS NULL;

CREATE UNIQUE INDEX idx_hatch_name_mapping_unique_project 
    ON hatch_pattern_name_mappings(dxf_alias, direction, project_id) 
    WHERE project_id IS NOT NULL;

-- ==============================================================================
-- 4. Material Name Mappings
-- ==============================================================================
-- Maps canonical material names to client-specific material specifications
CREATE TABLE IF NOT EXISTS material_name_mappings (
    mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    material_id UUID NOT NULL REFERENCES material_standards(material_id) ON DELETE CASCADE,
    
    -- Canonical name (follows MAT-DISCIPLINE-CATEGORY-COMPOSITION-[FINISH]-PHASE)
    canonical_name VARCHAR(255) NOT NULL,
    
    -- Client-specific material name/code
    dxf_alias VARCHAR(255) NOT NULL,
    
    -- Mapping direction
    direction VARCHAR(20) CHECK (direction IN ('import', 'export', 'both')) NOT NULL DEFAULT 'both',
    
    -- Client/project context
    client_name VARCHAR(255),
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    
    -- Material specification context
    spec_section VARCHAR(50),  -- e.g., "Section 02315" for earthwork specs
    manufacturer_equivalent VARCHAR(255),  -- Manufacturer-specific product name
    
    -- Metadata
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    confidence_score NUMERIC(3, 2) DEFAULT 1.0,
    
    -- AI-friendly search
    search_vector TSVECTOR,
    tags TEXT[],
    attributes JSONB DEFAULT '{}'::jsonb,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255)
);

CREATE INDEX idx_material_name_mappings_material_id ON material_name_mappings(material_id);
CREATE INDEX idx_material_name_mappings_dxf_alias ON material_name_mappings(dxf_alias);
CREATE INDEX idx_material_name_mappings_canonical ON material_name_mappings(canonical_name);
CREATE INDEX idx_material_name_mappings_client ON material_name_mappings(client_name) WHERE client_name IS NOT NULL;
CREATE INDEX idx_material_name_mappings_project ON material_name_mappings(project_id) WHERE project_id IS NOT NULL;
CREATE INDEX idx_material_name_mappings_search ON material_name_mappings USING GIN(search_vector);

-- Unique constraints with partial indexes
CREATE UNIQUE INDEX idx_material_name_mapping_unique_global 
    ON material_name_mappings(dxf_alias, direction) 
    WHERE client_name IS NULL AND project_id IS NULL;

CREATE UNIQUE INDEX idx_material_name_mapping_unique_client 
    ON material_name_mappings(dxf_alias, direction, client_name) 
    WHERE client_name IS NOT NULL AND project_id IS NULL;

CREATE UNIQUE INDEX idx_material_name_mapping_unique_project 
    ON material_name_mappings(dxf_alias, direction, project_id) 
    WHERE project_id IS NOT NULL;

-- ==============================================================================
-- 5. Keynote/Note Mappings
-- ==============================================================================
-- Maps canonical keynote names to client-specific keynote numbering systems
CREATE TABLE IF NOT EXISTS note_name_mappings (
    mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    note_id UUID NOT NULL REFERENCES standard_notes(note_id) ON DELETE CASCADE,
    
    -- Canonical name (follows DISCIPLINE-SYSTEM-THEME-SEQUENCE-PHASE-TX)
    canonical_name VARCHAR(255) NOT NULL,
    
    -- Client-specific keynote number/identifier
    dxf_alias VARCHAR(255) NOT NULL,
    
    -- Mapping direction
    direction VARCHAR(20) CHECK (direction IN ('import', 'export', 'both')) NOT NULL DEFAULT 'both',
    
    -- Client/project context
    client_name VARCHAR(255),
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    
    -- Note numbering context
    keynote_legend VARCHAR(50),  -- e.g., "General Notes", "Civil Notes Sheet 1"
    display_format VARCHAR(100),  -- e.g., "G-{number}", "{division}-{sequence}"
    
    -- Metadata
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    confidence_score NUMERIC(3, 2) DEFAULT 1.0,
    
    -- AI-friendly search
    search_vector TSVECTOR,
    tags TEXT[],
    attributes JSONB DEFAULT '{}'::jsonb,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255)
);

CREATE INDEX idx_note_name_mappings_note_id ON note_name_mappings(note_id);
CREATE INDEX idx_note_name_mappings_dxf_alias ON note_name_mappings(dxf_alias);
CREATE INDEX idx_note_name_mappings_canonical ON note_name_mappings(canonical_name);
CREATE INDEX idx_note_name_mappings_client ON note_name_mappings(client_name) WHERE client_name IS NOT NULL;
CREATE INDEX idx_note_name_mappings_project ON note_name_mappings(project_id) WHERE project_id IS NOT NULL;
CREATE INDEX idx_note_name_mappings_search ON note_name_mappings USING GIN(search_vector);

-- Unique constraints with partial indexes
CREATE UNIQUE INDEX idx_note_name_mapping_unique_global 
    ON note_name_mappings(dxf_alias, direction) 
    WHERE client_name IS NULL AND project_id IS NULL;

CREATE UNIQUE INDEX idx_note_name_mapping_unique_client 
    ON note_name_mappings(dxf_alias, direction, client_name) 
    WHERE client_name IS NOT NULL AND project_id IS NULL;

CREATE UNIQUE INDEX idx_note_name_mapping_unique_project 
    ON note_name_mappings(dxf_alias, direction, project_id) 
    WHERE project_id IS NOT NULL;

-- ==============================================================================
-- Update Triggers (for search_vector and updated_at)
-- ==============================================================================

-- Block name mappings search vector update
CREATE OR REPLACE FUNCTION update_block_name_mapping_search_vector() RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.canonical_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.dxf_alias, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.client_name, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER block_name_mapping_search_vector_update
    BEFORE INSERT OR UPDATE ON block_name_mappings
    FOR EACH ROW EXECUTE FUNCTION update_block_name_mapping_search_vector();

-- Detail name mappings search vector update
CREATE OR REPLACE FUNCTION update_detail_name_mapping_search_vector() RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.canonical_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.dxf_alias, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.client_name, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER detail_name_mapping_search_vector_update
    BEFORE INSERT OR UPDATE ON detail_name_mappings
    FOR EACH ROW EXECUTE FUNCTION update_detail_name_mapping_search_vector();

-- Hatch pattern name mappings search vector update
CREATE OR REPLACE FUNCTION update_hatch_name_mapping_search_vector() RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.canonical_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.dxf_alias, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.client_name, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER hatch_name_mapping_search_vector_update
    BEFORE INSERT OR UPDATE ON hatch_pattern_name_mappings
    FOR EACH ROW EXECUTE FUNCTION update_hatch_name_mapping_search_vector();

-- Material name mappings search vector update
CREATE OR REPLACE FUNCTION update_material_name_mapping_search_vector() RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.canonical_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.dxf_alias, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.client_name, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER material_name_mapping_search_vector_update
    BEFORE INSERT OR UPDATE ON material_name_mappings
    FOR EACH ROW EXECUTE FUNCTION update_material_name_mapping_search_vector();

-- Note name mappings search vector update
CREATE OR REPLACE FUNCTION update_note_name_mapping_search_vector() RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.canonical_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.dxf_alias, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.client_name, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER note_name_mapping_search_vector_update
    BEFORE INSERT OR UPDATE ON note_name_mappings
    FOR EACH ROW EXECUTE FUNCTION update_note_name_mapping_search_vector();

-- Updated_at triggers
CREATE OR REPLACE FUNCTION update_mapping_updated_at() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER block_name_mapping_updated_at
    BEFORE UPDATE ON block_name_mappings
    FOR EACH ROW EXECUTE FUNCTION update_mapping_updated_at();

CREATE TRIGGER detail_name_mapping_updated_at
    BEFORE UPDATE ON detail_name_mappings
    FOR EACH ROW EXECUTE FUNCTION update_mapping_updated_at();

CREATE TRIGGER hatch_name_mapping_updated_at
    BEFORE UPDATE ON hatch_pattern_name_mappings
    FOR EACH ROW EXECUTE FUNCTION update_mapping_updated_at();

CREATE TRIGGER material_name_mapping_updated_at
    BEFORE UPDATE ON material_name_mappings
    FOR EACH ROW EXECUTE FUNCTION update_mapping_updated_at();

CREATE TRIGGER note_name_mapping_updated_at
    BEFORE UPDATE ON note_name_mappings
    FOR EACH ROW EXECUTE FUNCTION update_mapping_updated_at();

-- ==============================================================================
-- Comments for documentation
-- ==============================================================================

COMMENT ON TABLE block_name_mappings IS 'Maps canonical block definition names to client-specific DXF block names for import/export';
COMMENT ON TABLE detail_name_mappings IS 'Maps canonical detail names to client-specific detail callout numbers and references';
COMMENT ON TABLE hatch_pattern_name_mappings IS 'Maps canonical hatch pattern names to DXF hatch pattern names in PAT files';
COMMENT ON TABLE material_name_mappings IS 'Maps canonical material names to client-specific material specifications and codes';
COMMENT ON TABLE note_name_mappings IS 'Maps canonical keynote names to client-specific keynote numbering systems';

COMMENT ON COLUMN block_name_mappings.direction IS 'Mapping direction: import (client→DB), export (DB→client), or both';
COMMENT ON COLUMN block_name_mappings.confidence_score IS 'AI confidence in the mapping accuracy (0.0-1.0)';
COMMENT ON COLUMN block_name_mappings.canonical_name IS 'Follows DISCIPLINE-CATEGORY-TYPE-[ATTRIBUTES]-PHASE-FORM naming convention';
