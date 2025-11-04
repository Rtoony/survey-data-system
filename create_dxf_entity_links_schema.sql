-- =====================================================================
-- DXF Entity Links Table
-- =====================================================================
-- Bidirectional mapping between DXF entities and intelligent database objects
-- Enables change tracking and round-trip CAD workflow

CREATE TABLE IF NOT EXISTS dxf_entity_links (
    link_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- DXF Entity Reference
    drawing_id UUID REFERENCES drawings(drawing_id) ON DELETE CASCADE,
    dxf_handle VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    layer_name VARCHAR(255),
    geometry_hash VARCHAR(64),
    
    -- Intelligent Object Reference (polymorphic)
    object_type VARCHAR(50) NOT NULL,
    object_id UUID NOT NULL,
    object_table_name VARCHAR(100) NOT NULL,
    
    -- Metadata
    created_from_import BOOLEAN DEFAULT TRUE,
    last_synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_status VARCHAR(50) DEFAULT 'synced',
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(drawing_id, dxf_handle)
);

CREATE INDEX IF NOT EXISTS idx_dxf_entity_links_drawing ON dxf_entity_links(drawing_id);
CREATE INDEX IF NOT EXISTS idx_dxf_entity_links_handle ON dxf_entity_links(dxf_handle);
CREATE INDEX IF NOT EXISTS idx_dxf_entity_links_object ON dxf_entity_links(object_type, object_id);
CREATE INDEX IF NOT EXISTS idx_dxf_entity_links_geometry_hash ON dxf_entity_links(geometry_hash);

COMMENT ON TABLE dxf_entity_links IS 'Links DXF entities to intelligent database objects for bidirectional sync';
COMMENT ON COLUMN dxf_entity_links.dxf_handle IS 'DXF entity handle for unique identification';
COMMENT ON COLUMN dxf_entity_links.geometry_hash IS 'SHA256 hash of geometry for change detection';
COMMENT ON COLUMN dxf_entity_links.object_type IS 'Type of intelligent object: utility_line, bmp, alignment, etc.';
COMMENT ON COLUMN dxf_entity_links.object_id IS 'UUID of the intelligent object';
COMMENT ON COLUMN dxf_entity_links.object_table_name IS 'Database table containing the intelligent object';
COMMENT ON COLUMN dxf_entity_links.sync_status IS 'Sync status: synced, modified, deleted, conflict';
