-- Map Viewer Schema for ACAD-GIS
-- Stores GIS layer configurations and export job tracking

-- Table: gis_layers
-- Stores configuration for available GIS layers (WFS/WMS sources)
CREATE TABLE IF NOT EXISTS gis_layers (
    id TEXT PRIMARY KEY,
    county_id TEXT NOT NULL DEFAULT 'sonoma',
    name TEXT NOT NULL,
    layer_type TEXT NOT NULL CHECK (layer_type IN ('WFS', 'WMS', 'GEOJSON')),
    url TEXT,
    layer_name TEXT,
    style JSONB DEFAULT '{}',
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Table: export_jobs
-- Tracks export job status and download links
CREATE TABLE IF NOT EXISTS export_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status TEXT NOT NULL CHECK (status IN ('pending', 'processing', 'complete', 'failed')),
    params JSONB NOT NULL,
    download_url TEXT,
    file_size_mb FLOAT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    email TEXT,
    project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    drawing_id INTEGER REFERENCES drawings(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_export_jobs_status ON export_jobs(status);
CREATE INDEX IF NOT EXISTS idx_export_jobs_created_at ON export_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_export_jobs_project_id ON export_jobs(project_id);

-- Insert default Sonoma County layers
INSERT INTO gis_layers (id, name, layer_type, url, layer_name, style, enabled) VALUES
('parcels', 'Parcels', 'WFS', 'https://gis.sonomacounty.ca.gov/geoserver/wfs', 'parcels', '{"color": "#FF5733", "weight": 2, "fillOpacity": 0.1}', true),
('buildings', 'Buildings', 'WFS', 'https://gis.sonomacounty.ca.gov/geoserver/wfs', 'buildings', '{"color": "#333333", "weight": 1, "fillOpacity": 0.6}', true),
('roads', 'Roads', 'WFS', 'https://gis.sonomacounty.ca.gov/geoserver/wfs', 'roads', '{"color": "#FFC300", "weight": 2}', true)
ON CONFLICT (id) DO NOTHING;

COMMENT ON TABLE gis_layers IS 'Configuration for available GIS layers (WFS/WMS sources)';
COMMENT ON TABLE export_jobs IS 'Tracks export job status and download links';
