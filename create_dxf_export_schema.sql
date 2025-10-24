-- ============================================================================
-- ACAD-GIS DXF Export Schema Enhancement
-- Adds missing tables for complete DXF/DWG export capability
-- ============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. DRAWING_ENTITIES - Generic CAD Primitives
-- ============================================================================
-- Stores basic CAD entities: lines, polylines, arcs, circles, ellipses, splines
CREATE TABLE IF NOT EXISTS drawing_entities (
    entity_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    drawing_id UUID NOT NULL REFERENCES drawings(drawing_id) ON DELETE CASCADE,
    layer_id UUID REFERENCES layers(layer_id),
    
    -- Entity type and handle
    entity_type VARCHAR(50) NOT NULL, -- LINE, POLYLINE, ARC, CIRCLE, ELLIPSE, SPLINE, POINT
    dxf_handle VARCHAR(50), -- DXF handle for round-trip consistency
    
    -- Geometry (PostGIS)
    geometry GEOMETRY(GeometryZ, 4326), -- 3D geometry with Z values
    
    -- Visual properties
    color_aci INTEGER, -- AutoCAD Color Index
    linetype VARCHAR(100),
    lineweight NUMERIC(10, 2),
    transparency INTEGER DEFAULT 0, -- 0-255
    
    -- Entity-specific properties (JSONB for flexibility)
    properties JSONB, -- Stores entity-specific data:
                      -- For ARC: start_angle, end_angle, radius
                      -- For CIRCLE: radius
                      -- For POLYLINE: is_closed, vertices
                      -- For ELLIPSE: major_axis, minor_axis
    
    -- Attributes and metadata
    space_type VARCHAR(20) DEFAULT 'MODEL', -- MODEL or PAPER
    layout_name VARCHAR(100),
    visibility BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Metadata
    metadata JSONB
);

CREATE INDEX idx_drawing_entities_drawing ON drawing_entities(drawing_id);
CREATE INDEX idx_drawing_entities_layer ON drawing_entities(layer_id);
CREATE INDEX idx_drawing_entities_type ON drawing_entities(entity_type);
CREATE INDEX idx_drawing_entities_geom ON drawing_entities USING GIST(geometry);

-- ============================================================================
-- 2. DRAWING_TEXT - Text Annotations
-- ============================================================================
CREATE TABLE IF NOT EXISTS drawing_text (
    text_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    drawing_id UUID NOT NULL REFERENCES drawings(drawing_id) ON DELETE CASCADE,
    layer_id UUID REFERENCES layers(layer_id),
    
    -- Text content and handle
    text_content TEXT NOT NULL,
    dxf_handle VARCHAR(50),
    
    -- Position (PostGIS Point with Z)
    insertion_point GEOMETRY(PointZ, 4326),
    alignment_point GEOMETRY(PointZ, 4326), -- For different text alignments
    
    -- Text properties
    text_height NUMERIC(10, 4),
    rotation_angle NUMERIC(10, 4) DEFAULT 0,
    width_factor NUMERIC(10, 4) DEFAULT 1.0,
    oblique_angle NUMERIC(10, 4) DEFAULT 0,
    
    -- Style and formatting
    text_style VARCHAR(100),
    font_name VARCHAR(100),
    horizontal_justification VARCHAR(20), -- LEFT, CENTER, RIGHT, ALIGNED, FIT
    vertical_justification VARCHAR(20), -- BASELINE, BOTTOM, MIDDLE, TOP
    
    -- Visual properties
    color_aci INTEGER,
    layer_name VARCHAR(100),
    
    -- Space and layout
    space_type VARCHAR(20) DEFAULT 'MODEL',
    layout_name VARCHAR(100),
    
    -- Timestamps and metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE INDEX idx_drawing_text_drawing ON drawing_text(drawing_id);
CREATE INDEX idx_drawing_text_layer ON drawing_text(layer_id);
CREATE INDEX idx_drawing_text_insertion ON drawing_text USING GIST(insertion_point);

-- ============================================================================
-- 3. DRAWING_DIMENSIONS - Dimension Annotations
-- ============================================================================
CREATE TABLE IF NOT EXISTS drawing_dimensions (
    dimension_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    drawing_id UUID NOT NULL REFERENCES drawings(drawing_id) ON DELETE CASCADE,
    layer_id UUID REFERENCES layers(layer_id),
    
    -- Dimension type and handle
    dimension_type VARCHAR(50) NOT NULL, -- LINEAR, ALIGNED, ANGULAR, RADIAL, DIAMETRIC, ORDINATE
    dxf_handle VARCHAR(50),
    
    -- Dimension geometry
    definition_point GEOMETRY(PointZ, 4326), -- Primary definition point
    text_position GEOMETRY(PointZ, 4326), -- Dimension text position
    geometry GEOMETRY(GeometryZ, 4326), -- Full dimension geometry (lines + arrows)
    
    -- Measurement
    measured_value NUMERIC(15, 6),
    override_value VARCHAR(100), -- User override text
    
    -- Dimension style reference
    dimension_style VARCHAR(100),
    dimension_style_id UUID REFERENCES dimension_styles(dimstyle_id),
    
    -- Visual properties
    color_aci INTEGER,
    text_height NUMERIC(10, 4),
    arrow_size NUMERIC(10, 4),
    
    -- Dimension-specific properties (JSONB for flexibility)
    properties JSONB, -- Stores dimension-specific data:
                      -- For LINEAR: extension_line_1, extension_line_2
                      -- For ANGULAR: angle_value, vertex_point
                      -- For RADIAL: center_point, radius_point
    
    -- Space and layout
    space_type VARCHAR(20) DEFAULT 'MODEL',
    layout_name VARCHAR(100),
    
    -- Timestamps and metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE INDEX idx_drawing_dimensions_drawing ON drawing_dimensions(drawing_id);
CREATE INDEX idx_drawing_dimensions_layer ON drawing_dimensions(layer_id);
CREATE INDEX idx_drawing_dimensions_style ON drawing_dimensions(dimension_style_id);
CREATE INDEX idx_drawing_dimensions_geom ON drawing_dimensions USING GIST(geometry);

-- ============================================================================
-- 4. DRAWING_HATCHES - Hatch Pattern Instances
-- ============================================================================
CREATE TABLE IF NOT EXISTS drawing_hatches (
    hatch_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    drawing_id UUID NOT NULL REFERENCES drawings(drawing_id) ON DELETE CASCADE,
    layer_id UUID REFERENCES layers(layer_id),
    
    -- Hatch pattern and handle
    pattern_name VARCHAR(100),
    pattern_id UUID REFERENCES hatch_patterns(hatch_id),
    dxf_handle VARCHAR(50),
    
    -- Boundary geometry (can be multiple closed loops)
    boundary_geometry GEOMETRY(Polygon, 4326),
    
    -- Hatch properties
    pattern_type VARCHAR(20), -- PREDEFINED, USER_DEFINED, CUSTOM
    pattern_scale NUMERIC(10, 4) DEFAULT 1.0,
    pattern_angle NUMERIC(10, 4) DEFAULT 0,
    pattern_spacing NUMERIC(10, 4),
    
    -- Visual properties
    color_aci INTEGER,
    is_solid BOOLEAN DEFAULT FALSE,
    transparency INTEGER DEFAULT 0,
    
    -- Associativity (links to boundary entities)
    is_associative BOOLEAN DEFAULT TRUE,
    associated_entities UUID[], -- Array of entity IDs that form the boundary
    
    -- Space and layout
    space_type VARCHAR(20) DEFAULT 'MODEL',
    layout_name VARCHAR(100),
    
    -- Timestamps and metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE INDEX idx_drawing_hatches_drawing ON drawing_hatches(drawing_id);
CREATE INDEX idx_drawing_hatches_layer ON drawing_hatches(layer_id);
CREATE INDEX idx_drawing_hatches_pattern ON drawing_hatches(pattern_id);
CREATE INDEX idx_drawing_hatches_boundary ON drawing_hatches USING GIST(boundary_geometry);

-- ============================================================================
-- 5. LAYOUT_VIEWPORTS - Paperspace Viewport Configuration
-- ============================================================================
CREATE TABLE IF NOT EXISTS layout_viewports (
    viewport_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    drawing_id UUID NOT NULL REFERENCES drawings(drawing_id) ON DELETE CASCADE,
    
    -- Layout and viewport identification
    layout_name VARCHAR(100) NOT NULL,
    viewport_number INTEGER,
    dxf_handle VARCHAR(50),
    
    -- Viewport geometry in paperspace
    center_point GEOMETRY(Point, 4326), -- Viewport center in paperspace
    width NUMERIC(10, 4),
    height NUMERIC(10, 4),
    
    -- View target in modelspace
    view_center GEOMETRY(PointZ, 4326), -- What point in modelspace is centered
    view_height NUMERIC(15, 6), -- Height of the view in modelspace units
    
    -- Scale and display
    scale_factor NUMERIC(15, 8), -- Paperspace to modelspace scale
    viewport_scale VARCHAR(50), -- e.g., "1:100", "1/4\" = 1'-0\""
    viewport_standard_id INTEGER REFERENCES viewport_standards(viewport_id),
    
    -- View properties
    view_twist_angle NUMERIC(10, 4) DEFAULT 0,
    lens_length NUMERIC(10, 4),
    front_clip NUMERIC(15, 6),
    back_clip NUMERIC(15, 6),
    
    -- Status and visibility
    is_active BOOLEAN DEFAULT TRUE,
    display_locked BOOLEAN DEFAULT FALSE,
    layers_frozen TEXT[], -- Array of layer names frozen in this viewport
    
    -- Visual style and rendering
    visual_style VARCHAR(50), -- 2DWIREFRAME, 3DWIREFRAME, REALISTIC, etc.
    grid_on BOOLEAN DEFAULT FALSE,
    snap_on BOOLEAN DEFAULT FALSE,
    
    -- Timestamps and metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE INDEX idx_layout_viewports_drawing ON layout_viewports(drawing_id);
CREATE INDEX idx_layout_viewports_layout ON layout_viewports(layout_name);
CREATE INDEX idx_layout_viewports_standard ON layout_viewports(viewport_standard_id);

-- ============================================================================
-- 6. EXPORT_JOBS - Track DXF/DWG Export Operations
-- ============================================================================
CREATE TABLE IF NOT EXISTS export_jobs (
    job_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    drawing_id UUID REFERENCES drawings(drawing_id) ON DELETE SET NULL,
    project_id UUID REFERENCES projects(project_id) ON DELETE SET NULL,
    
    -- Export configuration
    export_format VARCHAR(20) NOT NULL, -- DXF, DWG
    dxf_version VARCHAR(20), -- AC1027 (AutoCAD 2013), AC1032 (AutoCAD 2018), etc.
    export_scope VARCHAR(50), -- SINGLE_DRAWING, MULTIPLE_DRAWINGS, FULL_PROJECT
    
    -- Selection criteria
    selected_drawings UUID[], -- Array of drawing IDs if exporting multiple
    layer_filter TEXT[], -- Export only these layers (NULL = all)
    entity_types_filter TEXT[], -- Export only these entity types (NULL = all)
    
    -- Coordinate transformation
    coordinate_system VARCHAR(100),
    apply_georeferencing BOOLEAN DEFAULT TRUE,
    include_spatial_index BOOLEAN DEFAULT FALSE,
    
    -- Export options
    include_layouts BOOLEAN DEFAULT TRUE,
    include_blocks BOOLEAN DEFAULT TRUE,
    include_xrefs BOOLEAN DEFAULT FALSE,
    merge_layers BOOLEAN DEFAULT FALSE,
    
    -- Job status and timing
    status VARCHAR(50) DEFAULT 'PENDING', -- PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_by VARCHAR(100), -- User who created the export
    
    -- Output file information
    output_file_path VARCHAR(500),
    output_file_size BIGINT, -- Size in bytes
    output_file_hash VARCHAR(64), -- SHA-256 hash for integrity
    
    -- Statistics and metrics
    entities_exported INTEGER,
    layers_exported INTEGER,
    blocks_exported INTEGER,
    processing_time_ms INTEGER,
    
    -- Error handling
    error_message TEXT,
    warnings TEXT[],
    
    -- Metadata and logs
    export_parameters JSONB, -- Full export configuration
    processing_log JSONB, -- Detailed processing steps
    metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_export_jobs_drawing ON export_jobs(drawing_id);
CREATE INDEX idx_export_jobs_project ON export_jobs(project_id);
CREATE INDEX idx_export_jobs_status ON export_jobs(status);
CREATE INDEX idx_export_jobs_created ON export_jobs(created_at);

-- ============================================================================
-- 7. DRAWING_LAYER_USAGE - Track which layers are used in each drawing
-- ============================================================================
CREATE TABLE IF NOT EXISTS drawing_layer_usage (
    usage_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    drawing_id UUID NOT NULL REFERENCES drawings(drawing_id) ON DELETE CASCADE,
    layer_id UUID NOT NULL REFERENCES layers(layer_id) ON DELETE CASCADE,
    layer_standard_id UUID REFERENCES layer_standards(layer_standard_id),
    
    -- Usage statistics
    entity_count INTEGER DEFAULT 0, -- Number of entities on this layer
    last_used_at TIMESTAMP,
    
    -- Layer overrides for this drawing (if different from standard)
    override_color INTEGER,
    override_linetype VARCHAR(100),
    override_lineweight NUMERIC(10, 2),
    
    -- Status in this drawing
    is_frozen BOOLEAN DEFAULT FALSE,
    is_locked BOOLEAN DEFAULT FALSE,
    is_plottable BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure unique layer per drawing
    UNIQUE(drawing_id, layer_id)
);

CREATE INDEX idx_drawing_layer_usage_drawing ON drawing_layer_usage(drawing_id);
CREATE INDEX idx_drawing_layer_usage_layer ON drawing_layer_usage(layer_id);
CREATE INDEX idx_drawing_layer_usage_standard ON drawing_layer_usage(layer_standard_id);

-- ============================================================================
-- 8. DRAWING_LINETYPE_USAGE - Track which linetypes are used in each drawing
-- ============================================================================
CREATE TABLE IF NOT EXISTS drawing_linetype_usage (
    usage_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    drawing_id UUID NOT NULL REFERENCES drawings(drawing_id) ON DELETE CASCADE,
    linetype_name VARCHAR(100) NOT NULL,
    linetype_standard_id UUID REFERENCES linetype_standards(linetype_id),
    
    -- Usage statistics
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure unique linetype per drawing
    UNIQUE(drawing_id, linetype_name)
);

CREATE INDEX idx_drawing_linetype_usage_drawing ON drawing_linetype_usage(drawing_id);
CREATE INDEX idx_drawing_linetype_usage_standard ON drawing_linetype_usage(linetype_standard_id);

-- ============================================================================
-- Add helpful comments to tables
-- ============================================================================
COMMENT ON TABLE drawing_entities IS 'Stores generic CAD primitives (lines, arcs, circles, polylines, etc.) for DXF export';
COMMENT ON TABLE drawing_text IS 'Stores text annotations with positioning and formatting for CAD drawings';
COMMENT ON TABLE drawing_dimensions IS 'Stores dimension annotations (linear, angular, radial, etc.) for CAD drawings';
COMMENT ON TABLE drawing_hatches IS 'Stores hatch pattern instances with boundaries for CAD drawings';
COMMENT ON TABLE layout_viewports IS 'Stores paperspace viewport configurations for multi-sheet layouts';
COMMENT ON TABLE export_jobs IS 'Tracks DXF/DWG export operations, status, and output files';
COMMENT ON TABLE drawing_layer_usage IS 'Tracks which layers are actively used in each drawing';
COMMENT ON TABLE drawing_linetype_usage IS 'Tracks which linetypes are actively used in each drawing';

-- ============================================================================
-- Success message
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE 'DXF Export Schema Enhancement Complete!';
    RAISE NOTICE 'Created 8 new tables for full CAD export capability:';
    RAISE NOTICE '  1. drawing_entities - Generic CAD primitives';
    RAISE NOTICE '  2. drawing_text - Text annotations';
    RAISE NOTICE '  3. drawing_dimensions - Dimension annotations';
    RAISE NOTICE '  4. drawing_hatches - Hatch instances';
    RAISE NOTICE '  5. layout_viewports - Paperspace viewports';
    RAISE NOTICE '  6. export_jobs - Export tracking';
    RAISE NOTICE '  7. drawing_layer_usage - Layer usage tracking';
    RAISE NOTICE '  8. drawing_linetype_usage - Linetype usage tracking';
END $$;
