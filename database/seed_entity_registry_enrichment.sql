-- ==============================================================================
-- Seed Data for Entity Registry Enrichment
-- ==============================================================================
-- Purpose: Populate object type mappings, specialized tools, and examples
-- Created: 2025-11-15
--
-- This seed data is extracted from the hardcoded mappings in layer_classifier_v2.py
-- and represents the current "as-built" system configuration.
-- ==============================================================================

-- ==============================================================================
-- 1. Seed CAD Object Types (from layer_classifier_v2.py obj_type_map)
-- ==============================================================================

-- Utility Object Types
INSERT INTO cad_object_types (code, name, description, discipline_code, category_code, geometry_hint, sort_order) VALUES
('STORM', 'Storm Drain Lines', 'Storm drainage piping and channels', 'CIV', 'UTIL', 'line', 10),
('SANIT', 'Sanitary Sewer Lines', 'Sanitary sewer piping systems', 'CIV', 'UTIL', 'line', 20),
('WATER', 'Water Lines', 'Potable water distribution piping', 'CIV', 'UTIL', 'line', 30),
('RECYC', 'Recycled Water Lines', 'Recycled/reclaimed water piping', 'CIV', 'UTIL', 'line', 40),
('GAS', 'Gas Lines', 'Natural gas distribution piping', 'CIV', 'UTIL', 'line', 50),
('ELEC', 'Electric Lines', 'Electrical conduit and wiring', 'CIV', 'UTIL', 'line', 60),
('TELE', 'Telecom Lines', 'Telecommunication conduit and cables', 'CIV', 'UTIL', 'line', 70),
('FIBER', 'Fiber Optic Lines', 'Fiber optic cable runs', 'CIV', 'UTIL', 'line', 80),

-- Utility Structure Object Types
('MH', 'Manholes', 'Manhole structures for sewer/storm access', 'CIV', 'UTIL', 'point', 110),
('INLET', 'Storm Inlets', 'Storm drain inlet structures', 'CIV', 'UTIL', 'point', 120),
('CB', 'Catch Basins', 'Catch basin structures', 'CIV', 'UTIL', 'point', 130),
('CLNOUT', 'Cleanouts', 'Sewer cleanout structures', 'CIV', 'UTIL', 'point', 140),
('VALVE', 'Valves', 'Control valve structures', 'CIV', 'UTIL', 'point', 150),
('METER', 'Meters', 'Utility meter installations', 'CIV', 'UTIL', 'point', 160),
('HYDRA', 'Fire Hydrants', 'Fire hydrant installations', 'CIV', 'UTIL', 'point', 170),
('PUMP', 'Pump Stations', 'Utility pump station structures', 'CIV', 'UTIL', 'point', 180),

-- Survey Object Types
('MONUMENT', 'Survey Monuments', 'Survey control monuments', 'CIV', 'SURV', 'point', 210),
('BENCH', 'Benchmarks', 'Survey benchmark points', 'CIV', 'SURV', 'point', 220),
('SHOT', 'Survey Shots', 'Topographic survey shots', 'CIV', 'SURV', 'point', 230),

-- Alignment Object Types
('CL', 'Centerlines', 'Horizontal alignment centerlines', 'CIV', 'ALGN', 'line', 310),

-- Terrain Object Types
('CNTR', 'Contours', 'Elevation contour lines', 'CIV', 'TOPO', 'line', 410),
('SPOT', 'Spot Elevations', 'Spot elevation points', 'CIV', 'TOPO', 'point', 420),

-- Property Object Types
('PROP', 'Property Lines', 'Property/parcel boundaries', 'CIV', 'PROP', 'polygon', 510),

-- Grading Object Types
('PAD', 'Building Pads', 'Graded building pad areas', 'CIV', 'GRAD', 'polygon', 610),
('BERM', 'Berms', 'Graded berm features', 'CIV', 'GRAD', 'polygon', 620),
('SWALE', 'Swales', 'Drainage swale features', 'CIV', 'GRAD', 'line', 630),
('SWAL', 'Swales (Alt)', 'Drainage swale features (alternate code)', 'CIV', 'GRAD', 'line', 631),

-- Surface Feature Object Types
('CURB', 'Curb & Gutter', 'Curb and gutter features', 'CIV', 'ROAD', 'line', 710),
('SDWK', 'Sidewalks', 'Sidewalk surface features', 'CIV', 'ROAD', 'polygon', 720),
('STRP', 'Striping', 'Pavement striping and markings', 'CIV', 'ROAD', 'line', 730),

-- ADA Object Types
('RAMP', 'ADA Ramps', 'ADA-compliant ramps', 'CIV', 'ROAD', 'polygon', 810),
('PATH', 'Accessible Paths', 'ADA-compliant pedestrian paths', 'CIV', 'ROAD', 'line', 820),

-- BMP Object Types
('BIORT', 'Bioretention Areas', 'Bioretention BMP features', 'CIV', 'LAND', 'polygon', 910),
('BIOR', 'Bioretention (Alt)', 'Bioretention BMP features (alternate)', 'CIV', 'LAND', 'polygon', 911),
('BIOF', 'Biofilter', 'Biofilter BMP features', 'CIV', 'LAND', 'polygon', 920),
('RAIN', 'Rain Gardens', 'Rain garden BMP features', 'CIV', 'LAND', 'polygon', 930),
('BASIN', 'Detention Basins', 'Stormwater detention basins', 'CIV', 'LAND', 'polygon', 940),
('POND', 'Retention Ponds', 'Stormwater retention ponds', 'CIV', 'LAND', 'polygon', 950),
('INFIL', 'Infiltration Features', 'Infiltration BMP features', 'CIV', 'LAND', 'polygon', 960),

-- Trees/Vegetation Object Types
('TREE', 'Trees', 'Individual tree locations', 'CIV', 'LAND', 'point', 1010)

ON CONFLICT (code) DO NOTHING;

-- ==============================================================================
-- 2. Add Missing Entity Registry Entries for Unmapped Tables
-- ==============================================================================
-- Some object types map to tables that don't exist in entity_registry yet
-- Based on intelligent_object_creator.py actual table mappings

INSERT INTO entity_registry (table_name, display_name, description, icon, category, sort_order, is_active) VALUES
('storm_bmps', 'Stormwater BMPs', 'Best Management Practice features for stormwater treatment', 'fa-leaf', 'Stormwater', 200, TRUE),
('grading_limits', 'Grading Features', 'Graded pads, berms, swales, and earthwork features', 'fa-mountain', 'Grading', 300, TRUE),
('surface_models', 'Surface Models', 'Terrain surfaces, contours, and spot elevations', 'fa-layer-group', 'Terrain', 400, TRUE)
ON CONFLICT (table_name) DO NOTHING;

-- ==============================================================================
-- 3. Map Object Types to Entity Registry Tables
-- ==============================================================================
-- Note: Dynamically resolves registry_id values to ensure portability across environments

-- Map object types for each table using dynamic ID resolution
DO $$
DECLARE
    utility_lines_id INTEGER;
    utility_structures_id INTEGER;
    survey_points_id INTEGER;
    alignments_id INTEGER;
    parcels_id INTEGER;
    trees_id INTEGER;
    surface_features_id INTEGER;
BEGIN
    -- Resolve registry IDs dynamically
    SELECT registry_id INTO utility_lines_id FROM entity_registry WHERE table_name = 'utility_lines';
    SELECT registry_id INTO utility_structures_id FROM entity_registry WHERE table_name = 'utility_structures';
    SELECT registry_id INTO survey_points_id FROM entity_registry WHERE table_name = 'survey_points';
    SELECT registry_id INTO alignments_id FROM entity_registry WHERE table_name = 'horizontal_alignments';
    SELECT registry_id INTO parcels_id FROM entity_registry WHERE table_name = 'parcels';
    SELECT registry_id INTO trees_id FROM entity_registry WHERE table_name = 'site_trees';
    SELECT registry_id INTO surface_features_id FROM entity_registry WHERE table_name = 'surface_features';
    
    -- Verify required registry entries exist before proceeding
    IF utility_lines_id IS NULL THEN
        RAISE EXCEPTION 'Required entity_registry entry missing: utility_lines';
    END IF;
    IF utility_structures_id IS NULL THEN
        RAISE EXCEPTION 'Required entity_registry entry missing: utility_structures';
    END IF;
    IF survey_points_id IS NULL THEN
        RAISE EXCEPTION 'Required entity_registry entry missing: survey_points';
    END IF;
    IF alignments_id IS NULL THEN
        RAISE EXCEPTION 'Required entity_registry entry missing: horizontal_alignments';
    END IF;
    IF parcels_id IS NULL THEN
        RAISE EXCEPTION 'Required entity_registry entry missing: parcels';
    END IF;
    IF trees_id IS NULL THEN
        RAISE EXCEPTION 'Required entity_registry entry missing: site_trees';
    END IF;
    IF surface_features_id IS NULL THEN
        RAISE EXCEPTION 'Required entity_registry entry missing: surface_features';
    END IF;
    
    -- Utility Lines
    IF utility_lines_id IS NOT NULL THEN
        INSERT INTO entity_registry_object_types (registry_id, object_type_code, priority) VALUES
        (utility_lines_id, 'STORM', 10),
        (utility_lines_id, 'SANIT', 20),
        (utility_lines_id, 'WATER', 30),
        (utility_lines_id, 'RECYC', 40),
        (utility_lines_id, 'GAS', 50),
        (utility_lines_id, 'ELEC', 60),
        (utility_lines_id, 'TELE', 70),
        (utility_lines_id, 'FIBER', 80)
        ON CONFLICT (registry_id, object_type_code) DO NOTHING;
    END IF;
    
    -- Utility Structures
    IF utility_structures_id IS NOT NULL THEN
        INSERT INTO entity_registry_object_types (registry_id, object_type_code, priority) VALUES
        (utility_structures_id, 'MH', 10),
        (utility_structures_id, 'INLET', 20),
        (utility_structures_id, 'CB', 30),
        (utility_structures_id, 'CLNOUT', 40),
        (utility_structures_id, 'VALVE', 50),
        (utility_structures_id, 'METER', 60),
        (utility_structures_id, 'HYDRA', 70),
        (utility_structures_id, 'PUMP', 80)
        ON CONFLICT (registry_id, object_type_code) DO NOTHING;
    END IF;
    
    -- Survey Points
    IF survey_points_id IS NOT NULL THEN
        INSERT INTO entity_registry_object_types (registry_id, object_type_code, priority) VALUES
        (survey_points_id, 'MONUMENT', 10),
        (survey_points_id, 'BENCH', 20),
        (survey_points_id, 'SHOT', 30)
        ON CONFLICT (registry_id, object_type_code) DO NOTHING;
    END IF;
    
    -- Horizontal Alignments
    IF alignments_id IS NOT NULL THEN
        INSERT INTO entity_registry_object_types (registry_id, object_type_code, priority) VALUES
        (alignments_id, 'CL', 10)
        ON CONFLICT (registry_id, object_type_code) DO NOTHING;
    END IF;
    
    -- Parcels
    IF parcels_id IS NOT NULL THEN
        INSERT INTO entity_registry_object_types (registry_id, object_type_code, priority) VALUES
        (parcels_id, 'PROP', 10)
        ON CONFLICT (registry_id, object_type_code) DO NOTHING;
    END IF;
    
    -- Site Trees
    IF trees_id IS NOT NULL THEN
        INSERT INTO entity_registry_object_types (registry_id, object_type_code, priority) VALUES
        (trees_id, 'TREE', 10)
        ON CONFLICT (registry_id, object_type_code) DO NOTHING;
    END IF;
    
    -- Surface Features (includes CURB, SDWK, STRP, and ADA features RAMP, PATH)
    IF surface_features_id IS NOT NULL THEN
        INSERT INTO entity_registry_object_types (registry_id, object_type_code, priority) VALUES
        (surface_features_id, 'CURB', 10),
        (surface_features_id, 'SDWK', 20),
        (surface_features_id, 'STRP', 30),
        (surface_features_id, 'RAMP', 40),
        (surface_features_id, 'PATH', 50)
        ON CONFLICT (registry_id, object_type_code) DO NOTHING;
    END IF;
END $$;

-- Get registry_id for newly added tables and map their object types
DO $$
DECLARE
    bmp_id INTEGER;
    grading_id INTEGER;
    surface_id INTEGER;
BEGIN
    -- Get IDs for newly created entries
    SELECT registry_id INTO bmp_id FROM entity_registry WHERE table_name = 'storm_bmps';
    SELECT registry_id INTO grading_id FROM entity_registry WHERE table_name = 'grading_limits';
    SELECT registry_id INTO surface_id FROM entity_registry WHERE table_name = 'surface_models';
    
    -- Storm BMPs
    IF bmp_id IS NOT NULL THEN
        INSERT INTO entity_registry_object_types (registry_id, object_type_code, priority) VALUES
        (bmp_id, 'BIORT', 10),
        (bmp_id, 'BIOR', 11),
        (bmp_id, 'BIOF', 20),
        (bmp_id, 'RAIN', 30),
        (bmp_id, 'BASIN', 40),
        (bmp_id, 'POND', 50),
        (bmp_id, 'INFIL', 60)
        ON CONFLICT (registry_id, object_type_code) DO NOTHING;
    END IF;
    
    -- Grading Features
    IF grading_id IS NOT NULL THEN
        INSERT INTO entity_registry_object_types (registry_id, object_type_code, priority) VALUES
        (grading_id, 'PAD', 10),
        (grading_id, 'BERM', 20),
        (grading_id, 'SWALE', 30),
        (grading_id, 'SWAL', 31)
        ON CONFLICT (registry_id, object_type_code) DO NOTHING;
    END IF;
    
    -- Surface Models (includes both contours and spot elevations)
    IF surface_id IS NOT NULL THEN
        INSERT INTO entity_registry_object_types (registry_id, object_type_code, priority) VALUES
        (surface_id, 'CNTR', 10),
        (surface_id, 'SPOT', 20)
        ON CONFLICT (registry_id, object_type_code) DO NOTHING;
    END IF;
END $$;

-- ==============================================================================
-- 4. Seed Specialized Tools Registry
-- ==============================================================================

INSERT INTO specialized_tools (tool_name, tool_route, description, icon, category, sort_order, capabilities) VALUES
('Gravity Pipe Manager', '/tools/gravity-pipes', 'Manage gravity-flow utility pipes (storm, sanitary)', 'fa-water', 'Utilities', 10, '{"supports_bulk_edit": true, "supports_profile_generation": true}'::jsonb),
('Pressure Pipe Manager', '/tools/pressure-pipes', 'Manage pressure utility pipes (water, recycled water)', 'fa-droplet', 'Utilities', 20, '{"supports_bulk_edit": true, "supports_pressure_analysis": true}'::jsonb),
('BMP Manager', '/tools/bmps', 'Manage stormwater Best Management Practice features', 'fa-leaf', 'Stormwater', 30, '{"supports_bulk_edit": true, "supports_sizing_calculations": true}'::jsonb),
('Survey Point Manager', '/tools/survey-points', 'Comprehensive survey point management and analysis', 'fa-location-dot', 'Survey', 40, '{"supports_bulk_edit": true, "supports_coordinate_transformation": true}'::jsonb),
('Entity Viewer', '/tools/entity-viewer', 'Lightweight 2D viewer for project entities', 'fa-eye', 'Visualization', 50, '{"supports_multi_select": true, "supports_svg_export": true}'::jsonb)
ON CONFLICT (tool_name) DO NOTHING;

-- ==============================================================================
-- 5. Link Entity Registry to Specialized Tools
-- ==============================================================================

DO $$
DECLARE
    gravity_tool_id INTEGER;
    pressure_tool_id INTEGER;
    bmp_tool_id INTEGER;
    survey_tool_id INTEGER;
    viewer_tool_id INTEGER;
    utility_lines_id INTEGER;
    survey_points_id INTEGER;
    bmp_registry_id INTEGER;
BEGIN
    -- Get tool IDs
    SELECT tool_id INTO gravity_tool_id FROM specialized_tools WHERE tool_name = 'Gravity Pipe Manager';
    SELECT tool_id INTO pressure_tool_id FROM specialized_tools WHERE tool_name = 'Pressure Pipe Manager';
    SELECT tool_id INTO bmp_tool_id FROM specialized_tools WHERE tool_name = 'BMP Manager';
    SELECT tool_id INTO survey_tool_id FROM specialized_tools WHERE tool_name = 'Survey Point Manager';
    SELECT tool_id INTO viewer_tool_id FROM specialized_tools WHERE tool_name = 'Entity Viewer';
    
    -- Get registry IDs dynamically
    SELECT registry_id INTO utility_lines_id FROM entity_registry WHERE table_name = 'utility_lines';
    SELECT registry_id INTO survey_points_id FROM entity_registry WHERE table_name = 'survey_points';
    SELECT registry_id INTO bmp_registry_id FROM entity_registry WHERE table_name = 'storm_bmps';
    
    -- Verify required entities exist before linking
    IF utility_lines_id IS NULL THEN
        RAISE EXCEPTION 'Required entity_registry entry missing: utility_lines (needed for tool links)';
    END IF;
    IF survey_points_id IS NULL THEN
        RAISE EXCEPTION 'Required entity_registry entry missing: survey_points (needed for tool links)';
    END IF;
    IF bmp_registry_id IS NULL THEN
        RAISE EXCEPTION 'Required entity_registry entry missing: storm_bmps (needed for tool links)';
    END IF;
    
    -- Verify required tools exist before linking
    IF gravity_tool_id IS NULL THEN
        RAISE EXCEPTION 'Required specialized_tools entry missing: Gravity Pipe Manager';
    END IF;
    IF pressure_tool_id IS NULL THEN
        RAISE EXCEPTION 'Required specialized_tools entry missing: Pressure Pipe Manager';
    END IF;
    IF bmp_tool_id IS NULL THEN
        RAISE EXCEPTION 'Required specialized_tools entry missing: BMP Manager';
    END IF;
    IF survey_tool_id IS NULL THEN
        RAISE EXCEPTION 'Required specialized_tools entry missing: Survey Point Manager';
    END IF;
    IF viewer_tool_id IS NULL THEN
        RAISE EXCEPTION 'Required specialized_tools entry missing: Entity Viewer';
    END IF;
    
    -- Link Utility Lines to tools
    IF utility_lines_id IS NOT NULL AND gravity_tool_id IS NOT NULL THEN
        INSERT INTO entity_registry_tool_links (registry_id, tool_id, relationship_type, is_primary) VALUES
        (utility_lines_id, gravity_tool_id, 'manages', TRUE)
        ON CONFLICT (registry_id, tool_id) DO NOTHING;
    END IF;
    
    IF utility_lines_id IS NOT NULL AND pressure_tool_id IS NOT NULL THEN
        INSERT INTO entity_registry_tool_links (registry_id, tool_id, relationship_type, is_primary) VALUES
        (utility_lines_id, pressure_tool_id, 'manages', TRUE)
        ON CONFLICT (registry_id, tool_id) DO NOTHING;
    END IF;
    
    -- Link Survey Points to Survey Point Manager
    IF survey_points_id IS NOT NULL AND survey_tool_id IS NOT NULL THEN
        INSERT INTO entity_registry_tool_links (registry_id, tool_id, relationship_type, is_primary) VALUES
        (survey_points_id, survey_tool_id, 'manages', TRUE)
        ON CONFLICT (registry_id, tool_id) DO NOTHING;
    END IF;
    
    -- Link BMPs to BMP Manager
    IF bmp_registry_id IS NOT NULL AND bmp_tool_id IS NOT NULL THEN
        INSERT INTO entity_registry_tool_links (registry_id, tool_id, relationship_type, is_primary) VALUES
        (bmp_registry_id, bmp_tool_id, 'manages', TRUE)
        ON CONFLICT (registry_id, tool_id) DO NOTHING;
    END IF;
    
    -- Link Entity Viewer to all entity types (as secondary tool)
    IF viewer_tool_id IS NOT NULL THEN
        INSERT INTO entity_registry_tool_links (registry_id, tool_id, relationship_type, is_primary)
        SELECT registry_id, viewer_tool_id, 'views', FALSE
        FROM entity_registry
        WHERE is_active = TRUE
        ON CONFLICT (registry_id, tool_id) DO NOTHING;
    END IF;
END $$;

-- ==============================================================================
-- 6. Seed Example Layer Names
-- ==============================================================================
-- Note: Dynamically resolves registry_id values to ensure portability across environments

DO $$
DECLARE
    utility_lines_id INTEGER;
    utility_structures_id INTEGER;
    survey_points_id INTEGER;
    alignments_id INTEGER;
    parcels_id INTEGER;
    trees_id INTEGER;
    surface_features_id INTEGER;
BEGIN
    -- Resolve registry IDs dynamically
    SELECT registry_id INTO utility_lines_id FROM entity_registry WHERE table_name = 'utility_lines';
    SELECT registry_id INTO utility_structures_id FROM entity_registry WHERE table_name = 'utility_structures';
    SELECT registry_id INTO survey_points_id FROM entity_registry WHERE table_name = 'survey_points';
    SELECT registry_id INTO alignments_id FROM entity_registry WHERE table_name = 'horizontal_alignments';
    SELECT registry_id INTO parcels_id FROM entity_registry WHERE table_name = 'parcels';
    SELECT registry_id INTO trees_id FROM entity_registry WHERE table_name = 'site_trees';
    SELECT registry_id INTO surface_features_id FROM entity_registry WHERE table_name = 'surface_features';
    
    -- Verify required registry entries exist before adding examples
    IF utility_lines_id IS NULL THEN
        RAISE EXCEPTION 'Required entity_registry entry missing: utility_lines (needed for examples)';
    END IF;
    IF utility_structures_id IS NULL THEN
        RAISE EXCEPTION 'Required entity_registry entry missing: utility_structures (needed for examples)';
    END IF;
    IF survey_points_id IS NULL THEN
        RAISE EXCEPTION 'Required entity_registry entry missing: survey_points (needed for examples)';
    END IF;
    IF alignments_id IS NULL THEN
        RAISE EXCEPTION 'Required entity_registry entry missing: horizontal_alignments (needed for examples)';
    END IF;
    IF parcels_id IS NULL THEN
        RAISE EXCEPTION 'Required entity_registry entry missing: parcels (needed for examples)';
    END IF;
    IF trees_id IS NULL THEN
        RAISE EXCEPTION 'Required entity_registry entry missing: site_trees (needed for examples)';
    END IF;
    IF surface_features_id IS NULL THEN
        RAISE EXCEPTION 'Required entity_registry entry missing: surface_features (needed for examples)';
    END IF;
    
    -- Utility Lines examples
    IF utility_lines_id IS NOT NULL THEN
        INSERT INTO entity_registry_examples (registry_id, example_layer_name, description, is_recommended, sort_order) VALUES
        (utility_lines_id, 'CIV-UTIL-STORM-12IN-NEW-LN', '12-inch new storm drain line', TRUE, 10),
        (utility_lines_id, 'CIV-UTIL-WATER-8IN-EXIST-LN', '8-inch existing water line', TRUE, 20),
        (utility_lines_id, 'CIV-UTIL-SANIT-8IN-DEMO-LN', '8-inch sanitary sewer line to be removed', TRUE, 30)
        ON CONFLICT DO NOTHING;
    END IF;
    
    -- Utility Structures examples
    IF utility_structures_id IS NOT NULL THEN
        INSERT INTO entity_registry_examples (registry_id, example_layer_name, description, is_recommended, sort_order) VALUES
        (utility_structures_id, 'CIV-UTIL-MH-NEW-PT', 'New manhole structure', TRUE, 10),
        (utility_structures_id, 'CIV-UTIL-INLET-EXIST-PT', 'Existing storm inlet', TRUE, 20),
        (utility_structures_id, 'CIV-UTIL-VALVE-NEW-PT', 'New water valve', TRUE, 30)
        ON CONFLICT DO NOTHING;
    END IF;
    
    -- Survey Points examples
    IF survey_points_id IS NOT NULL THEN
        INSERT INTO entity_registry_examples (registry_id, example_layer_name, description, is_recommended, sort_order) VALUES
        (survey_points_id, 'CIV-SURV-SHOT-TOPO-PT', 'Topographic survey shot', TRUE, 10),
        (survey_points_id, 'CIV-SURV-BENCH-CONTROL-PT', 'Survey benchmark control point', TRUE, 20)
        ON CONFLICT DO NOTHING;
    END IF;
    
    -- Alignments examples
    IF alignments_id IS NOT NULL THEN
        INSERT INTO entity_registry_examples (registry_id, example_layer_name, description, is_recommended, sort_order) VALUES
        (alignments_id, 'CIV-ALGN-CL-ROAD-LN', 'Road centerline alignment', TRUE, 10)
        ON CONFLICT DO NOTHING;
    END IF;
    
    -- Parcels examples
    IF parcels_id IS NOT NULL THEN
        INSERT INTO entity_registry_examples (registry_id, example_layer_name, description, is_recommended, sort_order) VALUES
        (parcels_id, 'CIV-PROP-PROP-EXISTING-PL', 'Existing property boundary', TRUE, 10)
        ON CONFLICT DO NOTHING;
    END IF;
    
    -- Trees examples
    IF trees_id IS NOT NULL THEN
        INSERT INTO entity_registry_examples (registry_id, example_layer_name, description, is_recommended, sort_order) VALUES
        (trees_id, 'CIV-LAND-TREE-EXIST-PT', 'Existing tree location', TRUE, 10),
        (trees_id, 'CIV-LAND-TREE-PROPOSED-PT', 'Proposed tree location', TRUE, 20)
        ON CONFLICT DO NOTHING;
    END IF;
    
    -- Surface Features examples
    IF surface_features_id IS NOT NULL THEN
        INSERT INTO entity_registry_examples (registry_id, example_layer_name, description, is_recommended, sort_order) VALUES
        (surface_features_id, 'CIV-ROAD-CURB-NEW-LN', 'New curb and gutter', TRUE, 10),
        (surface_features_id, 'CIV-ROAD-SDWK-PROPOSED-PL', 'Proposed sidewalk', TRUE, 20),
        (surface_features_id, 'CIV-ROAD-RAMP-ADA-PL', 'ADA-compliant ramp', TRUE, 30)
        ON CONFLICT DO NOTHING;
    END IF;
END $$;
