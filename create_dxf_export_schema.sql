-- DXF/GIS Export Schema for ACAD-GIS Companion Tools
-- Creates tables for storing CAD drawing content and enabling DXF/DWG round-trip workflows

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS postgis;

-- 1. Projects table (parent container)
CREATE TABLE IF NOT EXISTS projects (
    project_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_name VARCHAR(255) NOT NULL,
    client_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Drawings table (individual CAD files)
CREATE TABLE IF NOT EXISTS drawings (
    drawing_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    drawing_name VARCHAR(255) NOT NULL,
    drawing_number VARCHAR(100),
    cad_units VARCHAR(50) DEFAULT 'Feet',
    scale_factor NUMERIC(10, 4) DEFAULT 1.0,
    coordinate_system VARCHAR(100),
    georef_point GEOMETRY(PointZ, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Layers table (drawing layers)
CREATE TABLE IF NOT EXISTS layers (
    layer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    layer_name VARCHAR(255) NOT NULL,
    layer_standard_id UUID,
    color INTEGER,
    linetype VARCHAR(100),
    lineweight INTEGER,
    is_frozen BOOLEAN DEFAULT FALSE,
    is_locked BOOLEAN DEFAULT FALSE
);

-- 4. Layer Standards table (CAD standards reference)
CREATE TABLE IF NOT EXISTS layer_standards (
    layer_standard_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    layer_name VARCHAR(255) UNIQUE NOT NULL,
    discipline VARCHAR(100),
    color_rgb VARCHAR(50),
    color_hex VARCHAR(7),
    linetype VARCHAR(100),
    lineweight INTEGER,
    description TEXT
);

-- 5. Block Standards table (symbol definitions)
CREATE TABLE IF NOT EXISTS block_standards (
    block_standard_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    block_name VARCHAR(255) UNIQUE NOT NULL,
    category VARCHAR(100),
    description TEXT,
    svg_preview TEXT,
    discipline VARCHAR(100)
);

-- 6. Block Inserts table (block instances in drawings)
CREATE TABLE IF NOT EXISTS block_inserts (
    insert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    block_name VARCHAR(255) NOT NULL,
    insertion_point GEOMETRY(PointZ) NOT NULL,
    scale_x NUMERIC(10, 4) DEFAULT 1.0,
    scale_y NUMERIC(10, 4) DEFAULT 1.0,
    scale_z NUMERIC(10, 4) DEFAULT 1.0,
    rotation NUMERIC(10, 4) DEFAULT 0.0,
    attributes JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Drawing Entities table (CAD primitives: lines, polylines, arcs, circles, etc.)
CREATE TABLE IF NOT EXISTS drawing_entities (
    entity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    layer_id UUID REFERENCES layers(layer_id),
    entity_type VARCHAR(50) NOT NULL,
    space_type VARCHAR(20) DEFAULT 'MODEL',
    geometry GEOMETRY(GeometryZ) NOT NULL,
    dxf_handle VARCHAR(100),
    color_aci INTEGER,
    linetype VARCHAR(100),
    lineweight INTEGER,
    transparency INTEGER,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. Drawing Text table (text annotations)
CREATE TABLE IF NOT EXISTS drawing_text (
    text_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    layer_id UUID REFERENCES layers(layer_id),
    space_type VARCHAR(20) DEFAULT 'MODEL',
    text_content TEXT NOT NULL,
    insertion_point GEOMETRY(PointZ) NOT NULL,
    text_height NUMERIC(10, 4),
    rotation_angle NUMERIC(10, 4) DEFAULT 0.0,
    text_style VARCHAR(100),
    horizontal_justification VARCHAR(50),
    vertical_justification VARCHAR(50),
    dxf_handle VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. Dimension Styles table (dimension formatting standards)
CREATE TABLE IF NOT EXISTS dimension_styles (
    dimension_style_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    style_name VARCHAR(255) UNIQUE NOT NULL,
    text_height NUMERIC(10, 4),
    arrow_size NUMERIC(10, 4),
    extension_line_offset NUMERIC(10, 4),
    dimension_line_color INTEGER,
    text_color INTEGER,
    description TEXT
);

-- 10. Drawing Dimensions table (dimension annotations)
CREATE TABLE IF NOT EXISTS drawing_dimensions (
    dimension_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    layer_id UUID REFERENCES layers(layer_id),
    dimension_style_id UUID REFERENCES dimension_styles(dimension_style_id),
    space_type VARCHAR(20) DEFAULT 'MODEL',
    dimension_type VARCHAR(50) NOT NULL,
    geometry GEOMETRY(GeometryZ) NOT NULL,
    override_value VARCHAR(100),
    dimension_style VARCHAR(100),
    dxf_handle VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 11. Hatch Patterns table (fill pattern standards)
CREATE TABLE IF NOT EXISTS hatch_patterns (
    pattern_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_name VARCHAR(255) UNIQUE NOT NULL,
    pattern_type VARCHAR(50),
    description TEXT,
    material_type VARCHAR(100)
);

-- 12. Drawing Hatches table (hatch/fill instances)
CREATE TABLE IF NOT EXISTS drawing_hatches (
    hatch_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    layer_id UUID REFERENCES layers(layer_id),
    pattern_id UUID REFERENCES hatch_patterns(pattern_id),
    space_type VARCHAR(20) DEFAULT 'MODEL',
    boundary_geometry GEOMETRY(PolygonZ) NOT NULL,
    pattern_name VARCHAR(255),
    pattern_scale NUMERIC(10, 4) DEFAULT 1.0,
    pattern_angle NUMERIC(10, 4) DEFAULT 0.0,
    dxf_handle VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 13. Layout Viewports table (paperspace viewport configurations)
CREATE TABLE IF NOT EXISTS layout_viewports (
    viewport_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    layout_name VARCHAR(255) NOT NULL,
    viewport_geometry GEOMETRY(PolygonZ) NOT NULL,
    view_center GEOMETRY(PointZ),
    scale_factor NUMERIC(10, 4) DEFAULT 1.0,
    view_twist_angle NUMERIC(10, 4) DEFAULT 0.0,
    frozen_layers TEXT[],
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 14. Export Jobs table (DXF/DWG export operation tracking)
CREATE TABLE IF NOT EXISTS export_jobs (
    export_job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    export_format VARCHAR(20) NOT NULL,
    dxf_version VARCHAR(20),
    output_file_path TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    entities_exported INTEGER DEFAULT 0,
    text_exported INTEGER DEFAULT 0,
    dimensions_exported INTEGER DEFAULT 0,
    hatches_exported INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- 15. Drawing Layer Usage table (track active layers per drawing)
CREATE TABLE IF NOT EXISTS drawing_layer_usage (
    usage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    layer_name VARCHAR(255) NOT NULL,
    entity_count INTEGER DEFAULT 0
);

-- 16. Drawing Linetype Usage table (track active linetypes per drawing)
CREATE TABLE IF NOT EXISTS drawing_linetype_usage (
    usage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    linetype_name VARCHAR(255) NOT NULL,
    entity_count INTEGER DEFAULT 0
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_drawings_project ON drawings(project_id);
CREATE INDEX IF NOT EXISTS idx_entities_layer ON drawing_entities(layer_id);
CREATE INDEX IF NOT EXISTS idx_entities_geometry ON drawing_entities USING GIST(geometry);
CREATE INDEX IF NOT EXISTS idx_text_geometry ON drawing_text USING GIST(insertion_point);
CREATE INDEX IF NOT EXISTS idx_hatches_geometry ON drawing_hatches USING GIST(boundary_geometry);

-- Insert sample data for testing
INSERT INTO projects (project_name, client_name) 
VALUES ('Test Project', 'Test Client')
ON CONFLICT DO NOTHING;

INSERT INTO drawings (project_id, drawing_name, drawing_number, cad_units)
SELECT project_id, 'Test Drawing', 'A-001', 'Feet'
FROM projects
WHERE project_name = 'Test Project'
ON CONFLICT DO NOTHING;

COMMENT ON TABLE drawing_entities IS 'Stores CAD primitives: lines, polylines, arcs, circles, ellipses, splines with PostGIS geometry';
COMMENT ON TABLE drawing_text IS 'Stores text annotations with insertion points, styles, rotation, and justification';
COMMENT ON TABLE drawing_dimensions IS 'Stores dimension annotations: linear, aligned, angular, radial, diametric, ordinate';
COMMENT ON TABLE drawing_hatches IS 'Stores hatch pattern instances with boundary geometry';
COMMENT ON TABLE layout_viewports IS 'Stores paperspace viewport configurations with scale and view settings';
COMMENT ON TABLE export_jobs IS 'Tracks DXF/DWG export operations with status and metrics';
COMMENT ON TABLE drawing_layer_usage IS 'Tracks which layers are actively used in each drawing';
COMMENT ON TABLE drawing_linetype_usage IS 'Tracks which linetypes are actively used in each drawing';
