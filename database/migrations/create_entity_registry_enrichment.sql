-- ==============================================================================
-- Entity Registry Enrichment Tables
-- ==============================================================================
-- Purpose: Make Entity Registry dynamic and maintainable by storing object type
--          mappings, specialized tool associations, and example layer names in database
-- Created: 2025-11-15
--
-- These tables eliminate hardcoded mappings and enable the Entity Registry to show:
-- - Which CAD object type codes (STORM, MH, SURVEY) map to each database table
-- - Which specialized tools (Gravity Pipe Manager, etc.) use each table
-- - Example layer names for each entity registry entry
-- ==============================================================================

-- ==============================================================================
-- 1. CAD Object Types Reference Table
-- ==============================================================================
-- Canonical list of all CAD object type codes used in layer classification
CREATE TABLE IF NOT EXISTS cad_object_types (
    object_type_id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    discipline_code VARCHAR(10),
    category_code VARCHAR(10),
    geometry_hint VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 100,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_code_uppercase CHECK (code = UPPER(code))
);

CREATE INDEX idx_cad_object_types_code ON cad_object_types(code);
CREATE INDEX idx_cad_object_types_active ON cad_object_types(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_cad_object_types_discipline ON cad_object_types(discipline_code) WHERE discipline_code IS NOT NULL;

COMMENT ON TABLE cad_object_types IS 'Reference table for all CAD object type codes (STORM, MH, SURVEY, etc.)';
COMMENT ON COLUMN cad_object_types.code IS 'Object type code as used in layer names (e.g., STORM, MH, INLET)';
COMMENT ON COLUMN cad_object_types.geometry_hint IS 'Expected geometry type (point, line, polygon, text, etc.)';

-- ==============================================================================
-- 2. Entity Registry ↔ Object Type Mappings (Many-to-Many)
-- ==============================================================================
-- Links CAD object type codes to their database storage tables
CREATE TABLE IF NOT EXISTS entity_registry_object_types (
    mapping_id SERIAL PRIMARY KEY,
    registry_id INTEGER NOT NULL REFERENCES entity_registry(registry_id) ON DELETE CASCADE,
    object_type_code VARCHAR(50) NOT NULL REFERENCES cad_object_types(code) ON DELETE CASCADE,
    
    -- Priority (for cases where one object type could map to multiple tables)
    priority INTEGER DEFAULT 10,
    
    -- Notes
    mapping_notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_registry_object_type UNIQUE(registry_id, object_type_code)
);

CREATE INDEX idx_entity_registry_object_types_registry ON entity_registry_object_types(registry_id);
CREATE INDEX idx_entity_registry_object_types_code ON entity_registry_object_types(object_type_code);
CREATE INDEX idx_entity_registry_object_types_active ON entity_registry_object_types(is_active) WHERE is_active = TRUE;

COMMENT ON TABLE entity_registry_object_types IS 'Maps CAD object type codes to their database storage tables';
COMMENT ON COLUMN entity_registry_object_types.priority IS 'Lower number = higher priority when multiple mappings exist';

-- ==============================================================================
-- 3. Specialized Tools Registry
-- ==============================================================================
-- Catalog of all specialized management tools in the system
CREATE TABLE IF NOT EXISTS specialized_tools (
    tool_id SERIAL PRIMARY KEY,
    tool_name VARCHAR(255) NOT NULL UNIQUE,
    tool_route VARCHAR(500) NOT NULL,
    description TEXT,
    icon VARCHAR(100),
    category VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 100,
    
    -- Tool capabilities (JSON metadata)
    capabilities JSONB DEFAULT '{}'::jsonb,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_specialized_tools_name ON specialized_tools(tool_name);
CREATE INDEX idx_specialized_tools_active ON specialized_tools(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_specialized_tools_category ON specialized_tools(category) WHERE category IS NOT NULL;

COMMENT ON TABLE specialized_tools IS 'Registry of all specialized management tools (Gravity Pipe Manager, BMP Manager, etc.)';
COMMENT ON COLUMN specialized_tools.tool_route IS 'URL route to access the tool (e.g., /tools/gravity-pipes)';
COMMENT ON COLUMN specialized_tools.capabilities IS 'JSON metadata describing tool features (supports_bulk_edit, etc.)';

-- ==============================================================================
-- 4. Entity Registry ↔ Specialized Tools Mappings (Many-to-Many)
-- ==============================================================================
-- Links database tables to the specialized tools that manage them
CREATE TABLE IF NOT EXISTS entity_registry_tool_links (
    link_id SERIAL PRIMARY KEY,
    registry_id INTEGER NOT NULL REFERENCES entity_registry(registry_id) ON DELETE CASCADE,
    tool_id INTEGER NOT NULL REFERENCES specialized_tools(tool_id) ON DELETE CASCADE,
    
    -- Relationship metadata
    relationship_type VARCHAR(50) DEFAULT 'manages',
    capabilities_override JSONB,
    is_primary BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_registry_tool UNIQUE(registry_id, tool_id)
);

CREATE INDEX idx_entity_registry_tool_links_registry ON entity_registry_tool_links(registry_id);
CREATE INDEX idx_entity_registry_tool_links_tool ON entity_registry_tool_links(tool_id);
CREATE INDEX idx_entity_registry_tool_links_active ON entity_registry_tool_links(is_active) WHERE is_active = TRUE;

COMMENT ON TABLE entity_registry_tool_links IS 'Links database tables to the specialized tools that manage them';
COMMENT ON COLUMN entity_registry_tool_links.relationship_type IS 'Type of relationship (manages, views, exports, etc.)';
COMMENT ON COLUMN entity_registry_tool_links.is_primary IS 'Whether this is the primary tool for managing this entity type';

-- ==============================================================================
-- 5. Entity Registry Example Layer Names
-- ==============================================================================
-- Curated example layer names for each entity registry entry
CREATE TABLE IF NOT EXISTS entity_registry_examples (
    example_id SERIAL PRIMARY KEY,
    registry_id INTEGER NOT NULL REFERENCES entity_registry(registry_id) ON DELETE CASCADE,
    
    -- Example layer name
    example_layer_name VARCHAR(255) NOT NULL,
    description TEXT,
    is_recommended BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 100,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_entity_registry_examples_registry ON entity_registry_examples(registry_id);
CREATE INDEX idx_entity_registry_examples_recommended ON entity_registry_examples(is_recommended) WHERE is_recommended = TRUE;

COMMENT ON TABLE entity_registry_examples IS 'Curated example layer names demonstrating how each entity type is used';
COMMENT ON COLUMN entity_registry_examples.example_layer_name IS 'Sample layer name (e.g., CIV-UTIL-STORM-12IN-NEW-LN)';

-- ==============================================================================
-- Triggers for updated_at timestamps
-- ==============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply to all new tables
DO $$
DECLARE
    t TEXT;
BEGIN
    FOR t IN 
        SELECT table_name::text 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN (
            'cad_object_types',
            'entity_registry_object_types', 
            'specialized_tools',
            'entity_registry_tool_links',
            'entity_registry_examples'
        )
    LOOP
        EXECUTE format('
            DROP TRIGGER IF EXISTS update_%I_updated_at ON %I;
            CREATE TRIGGER update_%I_updated_at
            BEFORE UPDATE ON %I
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        ', t, t, t, t);
    END LOOP;
END;
$$;
