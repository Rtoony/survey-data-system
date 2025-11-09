-- ==============================================================================
-- Add Search Vector Support to Project Context Mapping Tables
-- ==============================================================================
-- Purpose: Add full-text search capability to all project context mapping tables
-- Created: 2025-11-09
-- ==============================================================================

-- Add search_vector columns
ALTER TABLE project_keynote_block_mappings ADD COLUMN IF NOT EXISTS search_vector TSVECTOR;
ALTER TABLE project_keynote_detail_mappings ADD COLUMN IF NOT EXISTS search_vector TSVECTOR;
ALTER TABLE project_hatch_material_mappings ADD COLUMN IF NOT EXISTS search_vector TSVECTOR;
ALTER TABLE project_detail_material_mappings ADD COLUMN IF NOT EXISTS search_vector TSVECTOR;
ALTER TABLE project_block_specification_mappings ADD COLUMN IF NOT EXISTS search_vector TSVECTOR;
ALTER TABLE project_element_cross_references ADD COLUMN IF NOT EXISTS search_vector TSVECTOR;

-- Create GIN indexes for full-text search
CREATE INDEX IF NOT EXISTS idx_keynote_block_search ON project_keynote_block_mappings USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS idx_keynote_detail_search ON project_keynote_detail_mappings USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS idx_hatch_material_search ON project_hatch_material_mappings USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS idx_detail_material_search ON project_detail_material_mappings USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS idx_block_spec_search ON project_block_specification_mappings USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS idx_element_xref_search ON project_element_cross_references USING GIN(search_vector);

-- ==============================================================================
-- Search Vector Update Functions
-- ==============================================================================

-- Keynote-Block search vector
CREATE OR REPLACE FUNCTION update_keynote_block_search_vector() RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.keynote_number, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.block_instance_reference, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.usage_context, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(array_to_string(NEW.tags, ' '), '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER keynote_block_search_vector_update
    BEFORE INSERT OR UPDATE ON project_keynote_block_mappings
    FOR EACH ROW EXECUTE FUNCTION update_keynote_block_search_vector();

-- Keynote-Detail search vector
CREATE OR REPLACE FUNCTION update_keynote_detail_search_vector() RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.keynote_number, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.detail_callout, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.sheet_number, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.usage_context, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(array_to_string(NEW.tags, ' '), '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER keynote_detail_search_vector_update
    BEFORE INSERT OR UPDATE ON project_keynote_detail_mappings
    FOR EACH ROW EXECUTE FUNCTION update_keynote_detail_search_vector();

-- Hatch-Material search vector
CREATE OR REPLACE FUNCTION update_hatch_material_search_vector() RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.hatch_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.material_thickness, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.material_notes, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(NEW.detail_reference, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(array_to_string(NEW.tags, ' '), '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER hatch_material_search_vector_update
    BEFORE INSERT OR UPDATE ON project_hatch_material_mappings
    FOR EACH ROW EXECUTE FUNCTION update_hatch_material_search_vector();

-- Detail-Material search vector
CREATE OR REPLACE FUNCTION update_detail_material_search_vector() RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.detail_callout_label, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.material_thickness, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.material_notes, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(NEW.material_role, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(array_to_string(NEW.tags, ' '), '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER detail_material_search_vector_update
    BEFORE INSERT OR UPDATE ON project_detail_material_mappings
    FOR EACH ROW EXECUTE FUNCTION update_detail_material_search_vector();

-- Block-Specification search vector
CREATE OR REPLACE FUNCTION update_block_spec_search_vector() RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.spec_section, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.spec_description, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.manufacturer, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.model_number, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.jurisdiction, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(NEW.standard_reference, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(array_to_string(NEW.tags, ' '), '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER block_spec_search_vector_update
    BEFORE INSERT OR UPDATE ON project_block_specification_mappings
    FOR EACH ROW EXECUTE FUNCTION update_block_spec_search_vector();

-- Element Cross-Reference search vector
CREATE OR REPLACE FUNCTION update_element_xref_search_vector() RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.source_element_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.target_element_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.source_element_type, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.target_element_type, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.relationship_type, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.context_description, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(array_to_string(NEW.tags, ' '), '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER element_xref_search_vector_update
    BEFORE INSERT OR UPDATE ON project_element_cross_references
    FOR EACH ROW EXECUTE FUNCTION update_element_xref_search_vector();

-- ==============================================================================
-- Backfill existing data (if any)
-- ==============================================================================
UPDATE project_keynote_block_mappings SET updated_at = updated_at WHERE search_vector IS NULL;
UPDATE project_keynote_detail_mappings SET updated_at = updated_at WHERE search_vector IS NULL;
UPDATE project_hatch_material_mappings SET updated_at = updated_at WHERE search_vector IS NULL;
UPDATE project_detail_material_mappings SET updated_at = updated_at WHERE search_vector IS NULL;
UPDATE project_block_specification_mappings SET updated_at = updated_at WHERE search_vector IS NULL;
UPDATE project_element_cross_references SET updated_at = updated_at WHERE search_vector IS NULL;
