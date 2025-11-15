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
-- Note: This uses the existing registry_id values from the query results

-- Utility Lines (registry_id=1)
INSERT INTO entity_registry_object_types (registry_id, object_type_code, priority) VALUES
(1, 'STORM', 10),
(1, 'SANIT', 20),
(1, 'WATER', 30),
(1, 'RECYC', 40),
(1, 'GAS', 50),
(1, 'ELEC', 60),
(1, 'TELE', 70),
(1, 'FIBER', 80)
ON CONFLICT (registry_id, object_type_code) DO NOTHING;

-- Utility Structures (registry_id=2)
INSERT INTO entity_registry_object_types (registry_id, object_type_code, priority) VALUES
(2, 'MH', 10),
(2, 'INLET', 20),
(2, 'CB', 30),
(2, 'CLNOUT', 40),
(2, 'VALVE', 50),
(2, 'METER', 60),
(2, 'HYDRA', 70),
(2, 'PUMP', 80)
ON CONFLICT (registry_id, object_type_code) DO NOTHING;

-- Survey Points (registry_id=3)
INSERT INTO entity_registry_object_types (registry_id, object_type_code, priority) VALUES
(3, 'MONUMENT', 10),
(3, 'BENCH', 20),
(3, 'SHOT', 30)
ON CONFLICT (registry_id, object_type_code) DO NOTHING;

-- Horizontal Alignments (registry_id=9)
INSERT INTO entity_registry_object_types (registry_id, object_type_code, priority) VALUES
(9, 'CL', 10)
ON CONFLICT (registry_id, object_type_code) DO NOTHING;

-- Parcels (registry_id=10)
INSERT INTO entity_registry_object_types (registry_id, object_type_code, priority) VALUES
(10, 'PROP', 10)
ON CONFLICT (registry_id, object_type_code) DO NOTHING;

-- Site Trees (registry_id=12)
INSERT INTO entity_registry_object_types (registry_id, object_type_code, priority) VALUES
(12, 'TREE', 10)
ON CONFLICT (registry_id, object_type_code) DO NOTHING;

-- Surface Features (registry_id=14)
INSERT INTO entity_registry_object_types (registry_id, object_type_code, priority) VALUES
(14, 'CURB', 10),
(14, 'SDWK', 20),
(14, 'STRP', 30),
(14, 'RAMP', 40),
(14, 'PATH', 50)
ON CONFLICT (registry_id, object_type_code) DO NOTHING;

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
BEGIN
    -- Get tool IDs
    SELECT tool_id INTO gravity_tool_id FROM specialized_tools WHERE tool_name = 'Gravity Pipe Manager';
    SELECT tool_id INTO pressure_tool_id FROM specialized_tools WHERE tool_name = 'Pressure Pipe Manager';
    SELECT tool_id INTO bmp_tool_id FROM specialized_tools WHERE tool_name = 'BMP Manager';
    SELECT tool_id INTO survey_tool_id FROM specialized_tools WHERE tool_name = 'Survey Point Manager';
    SELECT tool_id INTO viewer_tool_id FROM specialized_tools WHERE tool_name = 'Entity Viewer';
    
    -- Link Utility Lines to tools
    IF gravity_tool_id IS NOT NULL THEN
        INSERT INTO entity_registry_tool_links (registry_id, tool_id, relationship_type, is_primary) VALUES
        (1, gravity_tool_id, 'manages', TRUE)
        ON CONFLICT (registry_id, tool_id) DO NOTHING;
    END IF;
    
    IF pressure_tool_id IS NOT NULL THEN
        INSERT INTO entity_registry_tool_links (registry_id, tool_id, relationship_type, is_primary) VALUES
        (1, pressure_tool_id, 'manages', TRUE)
        ON CONFLICT (registry_id, tool_id) DO NOTHING;
    END IF;
    
    -- Link Survey Points to Survey Point Manager
    IF survey_tool_id IS NOT NULL THEN
        INSERT INTO entity_registry_tool_links (registry_id, tool_id, relationship_type, is_primary) VALUES
        (3, survey_tool_id, 'manages', TRUE)
        ON CONFLICT (registry_id, tool_id) DO NOTHING;
    END IF;
    
    -- Link BMPs to BMP Manager
    IF bmp_tool_id IS NOT NULL THEN
        DECLARE
            bmp_registry_id INTEGER;
        BEGIN
            SELECT registry_id INTO bmp_registry_id FROM entity_registry WHERE table_name = 'storm_bmps';
            IF bmp_registry_id IS NOT NULL THEN
                INSERT INTO entity_registry_tool_links (registry_id, tool_id, relationship_type, is_primary) VALUES
                (bmp_registry_id, bmp_tool_id, 'manages', TRUE)
                ON CONFLICT (registry_id, tool_id) DO NOTHING;
            END IF;
        END;
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

-- Utility Lines examples
INSERT INTO entity_registry_examples (registry_id, example_layer_name, description, is_recommended, sort_order) VALUES
(1, 'CIV-UTIL-STORM-12IN-NEW-LN', '12-inch new storm drain line', TRUE, 10),
(1, 'CIV-UTIL-WATER-8IN-EXIST-LN', '8-inch existing water line', TRUE, 20),
(1, 'CIV-UTIL-SANIT-8IN-DEMO-LN', '8-inch sanitary sewer line to be removed', TRUE, 30)
ON CONFLICT DO NOTHING;

-- Utility Structures examples
INSERT INTO entity_registry_examples (registry_id, example_layer_name, description, is_recommended, sort_order) VALUES
(2, 'CIV-UTIL-MH-NEW-PT', 'New manhole structure', TRUE, 10),
(2, 'CIV-UTIL-INLET-EXIST-PT', 'Existing storm inlet', TRUE, 20),
(2, 'CIV-UTIL-VALVE-NEW-PT', 'New water valve', TRUE, 30)
ON CONFLICT DO NOTHING;

-- Survey Points examples
INSERT INTO entity_registry_examples (registry_id, example_layer_name, description, is_recommended, sort_order) VALUES
(3, 'CIV-SURV-SHOT-TOPO-PT', 'Topographic survey shot', TRUE, 10),
(3, 'CIV-SURV-BENCH-CONTROL-PT', 'Survey benchmark control point', TRUE, 20)
ON CONFLICT DO NOTHING;

-- Alignments examples
INSERT INTO entity_registry_examples (registry_id, example_layer_name, description, is_recommended, sort_order) VALUES
(9, 'CIV-ALGN-CL-ROAD-LN', 'Road centerline alignment', TRUE, 10)
ON CONFLICT DO NOTHING;

-- Parcels examples
INSERT INTO entity_registry_examples (registry_id, example_layer_name, description, is_recommended, sort_order) VALUES
(10, 'CIV-PROP-PROP-EXISTING-PL', 'Existing property boundary', TRUE, 10)
ON CONFLICT DO NOTHING;

-- Trees examples
INSERT INTO entity_registry_examples (registry_id, example_layer_name, description, is_recommended, sort_order) VALUES
(12, 'CIV-LAND-TREE-EXIST-PT', 'Existing tree location', TRUE, 10),
(12, 'CIV-LAND-TREE-PROPOSED-PT', 'Proposed tree location', TRUE, 20)
ON CONFLICT DO NOTHING;

-- Surface Features examples
INSERT INTO entity_registry_examples (registry_id, example_layer_name, description, is_recommended, sort_order) VALUES
(14, 'CIV-ROAD-CURB-NEW-LN', 'New curb and gutter', TRUE, 10),
(14, 'CIV-ROAD-SDWK-PROPOSED-PL', 'Proposed sidewalk', TRUE, 20),
(14, 'CIV-ROAD-RAMP-ADA-PL', 'ADA-compliant ramp', TRUE, 30)
ON CONFLICT DO NOTHING;
