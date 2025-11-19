-- =====================================================
-- GIS SNAPSHOT INTEGRATOR - DATABASE SCHEMA
-- Phase 1: Create tables for GIS data layer catalog and project snapshots
-- =====================================================

-- Ensure uuid extension is available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- TABLE 1: gis_data_layers (Reference Data Hub)
-- Catalog of external GIS data sources available for project snapshots
-- =====================================================
CREATE TABLE IF NOT EXISTS gis_data_layers (
    layer_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    layer_name VARCHAR(200) NOT NULL UNIQUE, -- e.g., "County Assessor Parcels"
    layer_description TEXT,
    service_url TEXT NOT NULL, -- e.g., "https://gis.county.gov/arcgis/rest/services/Parcels/MapServer/0"
    service_type VARCHAR(50) NOT NULL, -- 'arcgis_rest', 'wfs', 'geojson_url'
    target_entity_type VARCHAR(100) NOT NULL, -- 'parcel', 'utility_line', 'utility_structure'
    target_table_name VARCHAR(100) NOT NULL, -- 'parcels', 'utility_lines', etc.
    attribute_mapping JSONB, -- Maps external field names to internal columns
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    notes TEXT
);

-- Indexes for gis_data_layers
CREATE INDEX IF NOT EXISTS idx_gis_data_layers_active ON gis_data_layers(is_active);
CREATE INDEX IF NOT EXISTS idx_gis_data_layers_target ON gis_data_layers(target_entity_type);
CREATE INDEX IF NOT EXISTS idx_gis_data_layers_service_type ON gis_data_layers(service_type);

-- Comments for documentation
COMMENT ON TABLE gis_data_layers IS 'Reference Data Hub: Catalog of external GIS data sources available for project snapshots';
COMMENT ON COLUMN gis_data_layers.layer_id IS 'Unique identifier for this GIS data layer';
COMMENT ON COLUMN gis_data_layers.layer_name IS 'Human-readable name for the layer (e.g., "County Assessor Parcels")';
COMMENT ON COLUMN gis_data_layers.service_url IS 'URL endpoint for the external GIS service';
COMMENT ON COLUMN gis_data_layers.service_type IS 'Type of GIS service: arcgis_rest, wfs, geojson_url';
COMMENT ON COLUMN gis_data_layers.target_entity_type IS 'Type of entity this layer imports (parcel, utility_line, etc.)';
COMMENT ON COLUMN gis_data_layers.target_table_name IS 'Target database table name for imported entities';
COMMENT ON COLUMN gis_data_layers.attribute_mapping IS 'JSONB structure: {"source_field": "target_column", ...} e.g., {"APN": "parcel_number", "OWNER": "owner_name"}';

-- =====================================================
-- TABLE 2: project_gis_snapshots (Junction/History)
-- Tracks which GIS layers are assigned to which projects and snapshot history
-- =====================================================
CREATE TABLE IF NOT EXISTS project_gis_snapshots (
    snapshot_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    gis_data_layer_id UUID NOT NULL REFERENCES gis_data_layers(layer_id) ON DELETE CASCADE,
    snapshot_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    last_snapshot_at TIMESTAMP,
    snapshot_boundary GEOMETRY(Polygon, 2226), -- The buffered project area used for import
    entity_count INTEGER DEFAULT 0, -- How many entities were imported
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, gis_data_layer_id) -- One snapshot per layer per project
);

-- Indexes for project_gis_snapshots
CREATE INDEX IF NOT EXISTS idx_project_gis_snapshots_project ON project_gis_snapshots(project_id);
CREATE INDEX IF NOT EXISTS idx_project_gis_snapshots_layer ON project_gis_snapshots(gis_data_layer_id);
CREATE INDEX IF NOT EXISTS idx_project_gis_snapshots_status ON project_gis_snapshots(snapshot_status);
CREATE INDEX IF NOT EXISTS idx_project_gis_snapshots_boundary ON project_gis_snapshots USING GIST(snapshot_boundary);

-- Comments for documentation
COMMENT ON TABLE project_gis_snapshots IS 'Tracks GIS layer assignments to projects and snapshot history';
COMMENT ON COLUMN project_gis_snapshots.snapshot_id IS 'Unique identifier for this snapshot instance';
COMMENT ON COLUMN project_gis_snapshots.snapshot_status IS 'Status: pending, processing, completed, failed';
COMMENT ON COLUMN project_gis_snapshots.snapshot_boundary IS 'Buffered project extent used for import (SRID 2226)';
COMMENT ON COLUMN project_gis_snapshots.entity_count IS 'Number of entities imported in this snapshot';

-- =====================================================
-- TABLE MODIFICATIONS: Add snapshot_metadata column to target tables
-- =====================================================

-- Add snapshot_metadata to parcels table
ALTER TABLE parcels
ADD COLUMN IF NOT EXISTS snapshot_metadata JSONB;

CREATE INDEX IF NOT EXISTS idx_parcels_snapshot_metadata ON parcels USING GIN(snapshot_metadata);

COMMENT ON COLUMN parcels.snapshot_metadata IS 'Provenance tracking: {"snapshot_id": "uuid", "source_gis_object_id": "external_id", "imported_at": "timestamp", "source_layer": "layer_name"}';

-- Add snapshot_metadata to utility_lines table
ALTER TABLE utility_lines
ADD COLUMN IF NOT EXISTS snapshot_metadata JSONB;

CREATE INDEX IF NOT EXISTS idx_utility_lines_snapshot_metadata ON utility_lines USING GIN(snapshot_metadata);

COMMENT ON COLUMN utility_lines.snapshot_metadata IS 'Provenance tracking: {"snapshot_id": "uuid", "source_gis_object_id": "external_id", "imported_at": "timestamp", "source_layer": "layer_name"}';

-- Add snapshot_metadata to utility_structures table
ALTER TABLE utility_structures
ADD COLUMN IF NOT EXISTS snapshot_metadata JSONB;

CREATE INDEX IF NOT EXISTS idx_utility_structures_snapshot_metadata ON utility_structures USING GIN(snapshot_metadata);

COMMENT ON COLUMN utility_structures.snapshot_metadata IS 'Provenance tracking: {"snapshot_id": "uuid", "source_gis_object_id": "external_id", "imported_at": "timestamp", "source_layer": "layer_name"}';

-- =====================================================
-- SAMPLE TEST DATA (Optional - for development/testing)
-- =====================================================

-- Insert a sample GIS layer for testing
-- Uncomment this when ready to test:
/*
INSERT INTO gis_data_layers (
    layer_name,
    layer_description,
    service_url,
    service_type,
    target_entity_type,
    target_table_name,
    attribute_mapping
) VALUES (
    'Sample County Parcels',
    'Test GIS layer for county parcel data',
    'https://example.com/arcgis/rest/services/Parcels/MapServer/0',
    'arcgis_rest',
    'parcel',
    'parcels',
    '{"APN": "parcel_number", "OWNER_NAME": "owner_name", "LEGAL_DESC": "legal_description", "ACREAGE": "area_acres", "SITUS_ADDR": "address"}'::jsonb
) ON CONFLICT (layer_name) DO NOTHING;
*/

-- =====================================================
-- VERIFICATION QUERIES
-- =====================================================

-- Verify tables were created
SELECT
    'gis_data_layers' AS table_name,
    COUNT(*) AS row_count
FROM gis_data_layers
UNION ALL
SELECT
    'project_gis_snapshots' AS table_name,
    COUNT(*) AS row_count
FROM project_gis_snapshots;

-- Verify snapshot_metadata columns were added
SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE column_name = 'snapshot_metadata'
    AND table_schema = 'public'
ORDER BY table_name;

COMMIT;
