-- ==============================================================================
-- Project-Level Context Mapping Tables
-- ==============================================================================
-- Purpose: Create semantic relationships between CAD elements within projects
-- Created: 2025-11-09
--
-- These tables enable project-specific cross-element mappings like:
-- - Keynotes → Blocks (e.g., "Note 5" references "Type D Catch Basin")
-- - Keynotes → Details (e.g., "Note 10" references "Detail Sheet C-3")
-- - Hatches → Materials (e.g., "AC-2 Pattern" represents "AC Type II Material")
-- - Details → Materials (e.g., "Pavement Detail shows AC, PCC, Base materials")
-- - Blocks → Specifications (e.g., "Fire Hydrant" → "AWWA C502 Spec")
-- ==============================================================================

-- ==============================================================================
-- 1. Project Keynote-to-Block Mappings
-- ==============================================================================
-- Links keynotes to specific blocks within a project
CREATE TABLE IF NOT EXISTS project_keynote_block_mappings (
    mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    
    -- Keynote reference
    note_id UUID REFERENCES standard_notes(note_id) ON DELETE CASCADE,
    keynote_number VARCHAR(50),  -- e.g., "5", "G-12", "CIV-001"
    
    -- Block reference
    block_id UUID REFERENCES block_definitions(block_id) ON DELETE CASCADE,
    block_instance_reference VARCHAR(255),  -- Specific instance if applicable
    
    -- Relationship context
    relationship_type VARCHAR(50) DEFAULT 'references',  -- references, defines, specifies
    usage_context TEXT,  -- "Use this block when calling out this keynote"
    sheet_references TEXT[],  -- Sheets where this mapping applies
    
    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    display_order INTEGER,
    
    -- AI-friendly attributes
    tags TEXT[],
    attributes JSONB DEFAULT '{}'::jsonb,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    
    -- One keynote can map to multiple blocks and vice versa
    UNIQUE(project_id, note_id, block_id)
);

CREATE INDEX idx_keynote_block_project ON project_keynote_block_mappings(project_id);
CREATE INDEX idx_keynote_block_note ON project_keynote_block_mappings(note_id);
CREATE INDEX idx_keynote_block_block ON project_keynote_block_mappings(block_id);
CREATE INDEX idx_keynote_block_keynote_num ON project_keynote_block_mappings(keynote_number);

-- ==============================================================================
-- 2. Project Keynote-to-Detail Mappings
-- ==============================================================================
-- Links keynotes to specific construction details
CREATE TABLE IF NOT EXISTS project_keynote_detail_mappings (
    mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    
    -- Keynote reference
    note_id UUID REFERENCES standard_notes(note_id) ON DELETE CASCADE,
    keynote_number VARCHAR(50),
    
    -- Detail reference
    detail_id UUID REFERENCES detail_standards(detail_id) ON DELETE CASCADE,
    detail_callout VARCHAR(100),  -- e.g., "Detail 5/C-3.1", "Typ. Detail A"
    
    -- Sheet context
    sheet_number VARCHAR(50),
    detail_reference_type VARCHAR(50) DEFAULT 'see_detail',  -- see_detail, as_shown, typical
    
    -- Relationship metadata
    usage_context TEXT,
    is_primary_reference BOOLEAN DEFAULT TRUE,  -- If FALSE, this is an alternate/supplementary detail
    
    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    display_order INTEGER,
    
    -- AI-friendly attributes
    tags TEXT[],
    attributes JSONB DEFAULT '{}'::jsonb,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    
    UNIQUE(project_id, note_id, detail_id, sheet_number)
);

CREATE INDEX idx_keynote_detail_project ON project_keynote_detail_mappings(project_id);
CREATE INDEX idx_keynote_detail_note ON project_keynote_detail_mappings(note_id);
CREATE INDEX idx_keynote_detail_detail ON project_keynote_detail_mappings(detail_id);
CREATE INDEX idx_keynote_detail_keynote_num ON project_keynote_detail_mappings(keynote_number);
CREATE INDEX idx_keynote_detail_sheet ON project_keynote_detail_mappings(sheet_number);

-- ==============================================================================
-- 3. Project Hatch-to-Material Mappings
-- ==============================================================================
-- Links hatch patterns to specific materials within a project
CREATE TABLE IF NOT EXISTS project_hatch_material_mappings (
    mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    
    -- Hatch pattern reference
    hatch_id UUID REFERENCES hatch_patterns(hatch_id) ON DELETE CASCADE,
    hatch_name VARCHAR(255),  -- DXF hatch pattern name as used in drawings
    
    -- Material reference
    material_id UUID REFERENCES material_standards(material_id) ON DELETE CASCADE,
    
    -- Material quantity/thickness context
    material_thickness VARCHAR(50),  -- e.g., "4 inch", "6 inch", "varies"
    material_notes TEXT,  -- Additional specifications
    
    -- Optional detail reference showing this material
    detail_id UUID REFERENCES detail_standards(detail_id) ON DELETE SET NULL,
    detail_reference VARCHAR(100),  -- "See Detail X/Y"
    
    -- Color/Display override for project
    display_color_rgb VARCHAR(20),  -- e.g., "255,255,0" for yellow
    hatch_scale_override NUMERIC(10, 2),  -- Project-specific scale factor
    
    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    is_legend_item BOOLEAN DEFAULT TRUE,  -- Show in drawing legend
    legend_order INTEGER,
    
    -- AI-friendly attributes
    tags TEXT[],
    attributes JSONB DEFAULT '{}'::jsonb,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    
    UNIQUE(project_id, hatch_id, material_id)
);

CREATE INDEX idx_hatch_material_project ON project_hatch_material_mappings(project_id);
CREATE INDEX idx_hatch_material_hatch ON project_hatch_material_mappings(hatch_id);
CREATE INDEX idx_hatch_material_material ON project_hatch_material_mappings(material_id);
CREATE INDEX idx_hatch_material_detail ON project_hatch_material_mappings(detail_id) WHERE detail_id IS NOT NULL;

-- ==============================================================================
-- 4. Project Detail-to-Material Mappings
-- ==============================================================================
-- Tracks which materials are shown/specified in which details
CREATE TABLE IF NOT EXISTS project_detail_material_mappings (
    mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    
    -- Detail reference
    detail_id UUID REFERENCES detail_standards(detail_id) ON DELETE CASCADE,
    
    -- Material reference
    material_id UUID REFERENCES material_standards(material_id) ON DELETE CASCADE,
    
    -- Material context within detail
    material_role VARCHAR(50),  -- primary, secondary, alternate, background
    material_layer_order INTEGER,  -- Stacking order (1 = bottom, higher = top)
    material_thickness VARCHAR(50),
    material_notes TEXT,
    
    -- Callout/labeling
    detail_callout_label VARCHAR(100),  -- How material is labeled in detail (e.g., "6\" PCC")
    has_leader_line BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    
    -- AI-friendly attributes
    tags TEXT[],
    attributes JSONB DEFAULT '{}'::jsonb,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    
    UNIQUE(project_id, detail_id, material_id)
);

CREATE INDEX idx_detail_material_project ON project_detail_material_mappings(project_id);
CREATE INDEX idx_detail_material_detail ON project_detail_material_mappings(detail_id);
CREATE INDEX idx_detail_material_material ON project_detail_material_mappings(material_id);
CREATE INDEX idx_detail_material_layer ON project_detail_material_mappings(material_layer_order);

-- ==============================================================================
-- 5. Project Block-to-Specification Mappings
-- ==============================================================================
-- Links blocks/symbols to their governing specifications and notes
CREATE TABLE IF NOT EXISTS project_block_specification_mappings (
    mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    
    -- Block reference
    block_id UUID REFERENCES block_definitions(block_id) ON DELETE CASCADE,
    
    -- Specification/Note reference
    note_id UUID REFERENCES standard_notes(note_id) ON DELETE SET NULL,
    spec_section VARCHAR(100),  -- e.g., "Section 33 11 00", "AWWA C502"
    spec_description TEXT,  -- Full specification text
    
    -- Manufacturer/Product information
    manufacturer VARCHAR(255),
    model_number VARCHAR(255),
    product_url TEXT,
    
    -- Authority having jurisdiction requirements
    jurisdiction VARCHAR(255),  -- e.g., "City of Los Angeles", "County Standard"
    standard_reference VARCHAR(255),  -- e.g., "City Standard Type A"
    approval_required BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    is_primary_spec BOOLEAN DEFAULT TRUE,
    
    -- AI-friendly attributes
    tags TEXT[],
    attributes JSONB DEFAULT '{}'::jsonb,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255)
);

CREATE INDEX idx_block_spec_project ON project_block_specification_mappings(project_id);
CREATE INDEX idx_block_spec_block ON project_block_specification_mappings(block_id);
CREATE INDEX idx_block_spec_note ON project_block_specification_mappings(note_id) WHERE note_id IS NOT NULL;
CREATE INDEX idx_block_spec_section ON project_block_specification_mappings(spec_section);
CREATE INDEX idx_block_spec_jurisdiction ON project_block_specification_mappings(jurisdiction);

-- ==============================================================================
-- 6. Project Element Cross-Reference Table (Master Relationship Index)
-- ==============================================================================
-- Comprehensive cross-reference table for querying all element relationships
CREATE TABLE IF NOT EXISTS project_element_cross_references (
    xref_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    
    -- Source element
    source_element_type VARCHAR(50) NOT NULL,  -- keynote, block, detail, hatch, material
    source_element_id UUID NOT NULL,
    source_element_name VARCHAR(255),
    
    -- Target element
    target_element_type VARCHAR(50) NOT NULL,
    target_element_id UUID NOT NULL,
    target_element_name VARCHAR(255),
    
    -- Relationship metadata
    relationship_type VARCHAR(50) NOT NULL,  -- references, uses, shows, specifies, etc.
    relationship_strength VARCHAR(20) DEFAULT 'normal',  -- primary, secondary, weak
    
    -- Context
    context_description TEXT,
    sheet_references TEXT[],
    
    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    
    -- AI-friendly
    tags TEXT[],
    attributes JSONB DEFAULT '{}'::jsonb,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255)
);

CREATE INDEX idx_xref_project ON project_element_cross_references(project_id);
CREATE INDEX idx_xref_source ON project_element_cross_references(source_element_type, source_element_id);
CREATE INDEX idx_xref_target ON project_element_cross_references(target_element_type, target_element_id);
CREATE INDEX idx_xref_relationship ON project_element_cross_references(relationship_type);
CREATE INDEX idx_xref_strength ON project_element_cross_references(relationship_strength);

-- ==============================================================================
-- Update Triggers
-- ==============================================================================

-- Updated_at triggers for all tables
CREATE OR REPLACE FUNCTION update_project_mapping_updated_at() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER keynote_block_mapping_updated_at
    BEFORE UPDATE ON project_keynote_block_mappings
    FOR EACH ROW EXECUTE FUNCTION update_project_mapping_updated_at();

CREATE TRIGGER keynote_detail_mapping_updated_at
    BEFORE UPDATE ON project_keynote_detail_mappings
    FOR EACH ROW EXECUTE FUNCTION update_project_mapping_updated_at();

CREATE TRIGGER hatch_material_mapping_updated_at
    BEFORE UPDATE ON project_hatch_material_mappings
    FOR EACH ROW EXECUTE FUNCTION update_project_mapping_updated_at();

CREATE TRIGGER detail_material_mapping_updated_at
    BEFORE UPDATE ON project_detail_material_mappings
    FOR EACH ROW EXECUTE FUNCTION update_project_mapping_updated_at();

CREATE TRIGGER block_spec_mapping_updated_at
    BEFORE UPDATE ON project_block_specification_mappings
    FOR EACH ROW EXECUTE FUNCTION update_project_mapping_updated_at();

CREATE TRIGGER element_xref_updated_at
    BEFORE UPDATE ON project_element_cross_references
    FOR EACH ROW EXECUTE FUNCTION update_project_mapping_updated_at();

-- ==============================================================================
-- Comments for documentation
-- ==============================================================================

COMMENT ON TABLE project_keynote_block_mappings IS 'Links keynotes to specific blocks within projects (e.g., Note 5 → Type D Catch Basin Block)';
COMMENT ON TABLE project_keynote_detail_mappings IS 'Links keynotes to construction details (e.g., Note 10 → See Detail C-3.1)';
COMMENT ON TABLE project_hatch_material_mappings IS 'Maps hatch patterns to materials with thickness and detail references';
COMMENT ON TABLE project_detail_material_mappings IS 'Tracks which materials are shown in which details with layer ordering';
COMMENT ON TABLE project_block_specification_mappings IS 'Links blocks to governing specifications, standards, and manufacturer data';
COMMENT ON TABLE project_element_cross_references IS 'Master index of all cross-element relationships for comprehensive querying';

COMMENT ON COLUMN project_hatch_material_mappings.hatch_scale_override IS 'Project-specific hatch pattern scale override';
COMMENT ON COLUMN project_detail_material_mappings.material_layer_order IS 'Vertical stacking order in section views (1=bottom layer)';
COMMENT ON COLUMN project_block_specification_mappings.jurisdiction IS 'Authority having jurisdiction (City, County, State, etc.)';
COMMENT ON COLUMN project_element_cross_references.relationship_strength IS 'Importance/strength of relationship: primary, secondary, or weak';
