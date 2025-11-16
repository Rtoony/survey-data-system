-- ============================================================================
-- Seed Data for Survey Standards
-- Provides initial standard survey descriptions and methods
-- ============================================================================

-- ============================================================================
-- SURVEY POINT DESCRIPTION STANDARDS
-- ============================================================================

INSERT INTO survey_point_description_standards
(description_code, description_text, description_full, category, subcategory, feature_type, point_code, cad_symbol, color_hex, is_control_point, requires_elevation)
VALUES

-- PAVEMENT FEATURES
('EP', 'Edge of Pavement', 'Edge of paved surface (asphalt or concrete)', 'Pavement', 'Edges', 'Line', 'EP', 'POINT', '#FF0000', false, true),
('CL', 'Centerline', 'Centerline of roadway or lane', 'Pavement', 'Centerlines', 'Line', 'CL', 'POINT', '#FFFF00', false, true),
('PC', 'Pavement Crown', 'High point of pavement cross-slope', 'Pavement', 'Profiles', 'Point', 'PC', 'POINT', '#FFA500', false, true),
('CRACK', 'Pavement Crack', 'Crack in pavement surface', 'Pavement', 'Condition', 'Line', 'CRACK', 'X-MARK', '#FF0000', false, false),
('STRIPE', 'Pavement Stripe', 'Painted pavement marking', 'Pavement', 'Markings', 'Line', 'STRIPE', 'POINT', '#FFFFFF', false, false),

-- CURB & GUTTER
('FG', 'Face of Curb', 'Face of vertical curb', 'Curb & Gutter', 'Vertical', 'Line', 'FG', 'POINT', '#00FFFF', false, true),
('BC', 'Back of Curb', 'Back edge of curb', 'Curb & Gutter', 'Edges', 'Line', 'BC', 'POINT', '#00FFFF', false, true),
('TG', 'Top of Gutter', 'Top edge of gutter pan', 'Curb & Gutter', 'Edges', 'Line', 'TG', 'POINT', '#00FF00', false, true),
('FL', 'Flowline', 'Low point of gutter or drainage path', 'Curb & Gutter', 'Drainage', 'Line', 'FL', 'POINT', '#0000FF', false, true),

-- STRUCTURES & WALLS
('TW', 'Top of Wall', 'Top of retaining wall or similar structure', 'Structures', 'Walls', 'Line', 'TW', 'POINT', '#A52A2A', false, true),
('BW', 'Bottom of Wall', 'Base/toe of wall', 'Structures', 'Walls', 'Line', 'BW', 'POINT', '#8B4513', false, true),
('FW', 'Face of Wall', 'Face of wall (vertical surface)', 'Structures', 'Walls', 'Line', 'FW', 'POINT', '#CD853F', false, true),
('BLDG', 'Building Corner', 'Corner of building or structure', 'Structures', 'Buildings', 'Point', 'BLDG', 'SQUARE', '#FF00FF', false, true),
('FENCE', 'Fence Line', 'Chain link, wood, or other fence', 'Structures', 'Fences', 'Line', 'FENCE', 'POINT', '#808080', false, false),

-- UTILITIES
('MH', 'Manhole', 'Utility manhole (storm, sewer, etc.)', 'Utilities', 'Structures', 'Point', 'MH', 'CIRCLE-FILLED', '#00BCD4', false, true),
('CB', 'Catch Basin', 'Storm drain catch basin', 'Utilities', 'Storm', 'Point', 'CB', 'SQUARE', '#0000FF', false, true),
('WV', 'Water Valve', 'Water distribution valve', 'Utilities', 'Water', 'Point', 'WV', 'VALVE', '#00BFFF', false, true),
('HYDRANT', 'Fire Hydrant', 'Fire hydrant', 'Utilities', 'Water', 'Point', 'HYDRANT', 'HYDRANT', '#FF0000', false, true),
('POLE', 'Utility Pole', 'Electric, telephone, or other utility pole', 'Utilities', 'Overhead', 'Point', 'POLE', 'CIRCLE', '#FFD700', false, false),

-- VEGETATION
('TREE', 'Tree Trunk', 'Tree trunk at DBH height', 'Vegetation', 'Trees', 'Point', 'TREE', 'TREE', '#228B22', false, false),
('CANOPY', 'Tree Canopy Edge', 'Drip line / canopy extent', 'Vegetation', 'Trees', 'Line', 'CANOPY', 'POINT', '#90EE90', false, false),
('SHRUB', 'Shrub', 'Shrub or bush', 'Vegetation', 'Shrubs', 'Point', 'SHRUB', 'X-MARK', '#32CD32', false, false),

-- TERRAIN
('TOB', 'Top of Bank', 'Top edge of slope or creek bank', 'Terrain', 'Slopes', 'Line', 'TOB', 'POINT', '#8B4513', false, true),
('BOB', 'Bottom of Bank', 'Toe of slope or creek bottom', 'Terrain', 'Slopes', 'Line', 'BOB', 'POINT', '#654321', false, true),
('TOS', 'Top of Slope', 'Top of designed or natural slope', 'Terrain', 'Slopes', 'Line', 'TOS', 'POINT', '#D2691E', false, true),
('BOS', 'Bottom of Slope', 'Toe of designed or natural slope', 'Terrain', 'Slopes', 'Line', 'BOS', 'POINT', '#8B7355', false, true),
('TOPO', 'Topographic Point', 'General ground surface point', 'Terrain', 'Surface', 'Point', 'TOPO', 'POINT', '#00FF00', false, true),

-- CONTROL POINTS
('BENCHMARK', 'Benchmark', 'Vertical control monument', 'Control', 'Vertical', 'Point', 'BM', 'BENCHMARK', '#FF0000', true, true),
('CONTROL', 'Control Point', 'Horizontal/3D control monument', 'Control', 'Horizontal', 'Point', 'CTRL', 'CONTROL', '#FF00FF', true, true),
('MONUMENT', 'Survey Monument', 'Property corner monument', 'Control', 'Property', 'Point', 'MON', 'MONUMENT', '#FFD700', true, true);

-- ============================================================================
-- SURVEY METHOD TYPES
-- ============================================================================

INSERT INTO survey_method_types
(method_code, method_name, method_description, category, subcategory, equipment_type, typical_horizontal_accuracy, typical_vertical_accuracy, accuracy_units, accuracy_class, requires_base_station, requires_line_of_sight, effective_range_ft, typical_time_per_point, related_standards)
VALUES

-- GNSS METHODS
(
    'RTK-GPS',
    'Real-Time Kinematic GPS',
    'High-precision GPS using real-time corrections from base station',
    'GNSS',
    'RTK',
    'RTK GPS Receiver',
    0.02,
    0.03,
    'Feet',
    'Survey Grade',
    true,
    false,
    32000,
    '1-5 seconds',
    'NGS Guidelines, ALTA/NSPS Standards'
),
(
    'PPK-GPS',
    'Post-Processed Kinematic GPS',
    'High-precision GPS with post-processing of base station data',
    'GNSS',
    'PPK',
    'GPS Receiver',
    0.03,
    0.05,
    'Feet',
    'Survey Grade',
    true,
    false,
    32000,
    '10-30 seconds',
    'NGS Guidelines'
),
(
    'GPS-STATIC',
    'Static GPS',
    'Highest precision GPS for control networks using long observations',
    'GNSS',
    'Static',
    'Dual-Frequency GPS',
    0.01,
    0.02,
    'Feet',
    'Survey Grade',
    true,
    false,
    65000,
    '15-60 minutes',
    'NGS-58, FGCS Standards'
),
(
    'GPS-NAV',
    'GPS Navigation',
    'Standard GPS without corrections (low accuracy)',
    'GNSS',
    'Navigation',
    'GPS Receiver',
    10.0,
    30.0,
    'Feet',
    'Navigation Grade',
    false,
    false,
    NULL,
    '1 second',
    'N/A'
),

-- TERRESTRIAL METHODS
(
    'TS-MANUAL',
    'Manual Total Station',
    'Conventional total station with manual pointing',
    'Terrestrial',
    'Total Station',
    'Total Station',
    0.02,
    0.02,
    'Feet',
    'Survey Grade',
    false,
    true,
    3000,
    '10-30 seconds',
    'ALTA/NSPS, State Survey Standards'
),
(
    'TS-ROBOTIC',
    'Robotic Total Station',
    'Robotic total station with automatic pointing and tracking',
    'Terrestrial',
    'Total Station',
    'Robotic Total Station',
    0.02,
    0.02,
    'Feet',
    'Survey Grade',
    false,
    true,
    3000,
    '5-10 seconds',
    'ALTA/NSPS, State Survey Standards'
),
(
    'SCANNER-3D',
    '3D Laser Scanner',
    'Terrestrial laser scanner for high-density point clouds',
    'Terrestrial',
    'Laser Scanning',
    '3D Laser Scanner',
    0.05,
    0.05,
    'Feet',
    'Survey Grade',
    false,
    true,
    1000,
    '1000+ pts/sec',
    'ASTM E2544, ASTM E3125'
),

-- LEVELING METHODS
(
    'LEVEL-DIGI',
    'Digital Level',
    'Electronic level with barcode rod reading',
    'Leveling',
    'Differential',
    'Digital Level',
    NULL,
    0.01,
    'Feet',
    'Survey Grade',
    false,
    true,
    300,
    '5-15 seconds',
    'FGCS, NGS-3'
),
(
    'LEVEL-AUTO',
    'Automatic Level',
    'Self-leveling optical level',
    'Leveling',
    'Differential',
    'Automatic Level',
    NULL,
    0.02,
    'Feet',
    'Survey Grade',
    false,
    true,
    300,
    '15-30 seconds',
    'State Survey Standards'
),
(
    'LEVEL-LASER',
    'Laser Level',
    'Rotating laser level for construction layout',
    'Leveling',
    'Construction',
    'Rotating Laser',
    NULL,
    0.10,
    'Feet',
    'Mapping Grade',
    false,
    true,
    1000,
    '1-2 seconds',
    'Construction Standards'
),

-- PHOTOGRAMMETRY/REMOTE SENSING
(
    'DRONE-RTK',
    'RTK Drone Survey',
    'UAV with RTK GNSS for high-accuracy photogrammetry',
    'Photogrammetry',
    'UAV',
    'RTK Drone',
    0.10,
    0.15,
    'Feet',
    'Mapping Grade',
    true,
    false,
    NULL,
    'Variable',
    'FAA Part 107, ASPRS Standards'
),
(
    'DRONE-PPK',
    'PPK Drone Survey',
    'UAV with post-processed GNSS for photogrammetry',
    'Photogrammetry',
    'UAV',
    'PPK Drone',
    0.15,
    0.20,
    'Feet',
    'Mapping Grade',
    true,
    false,
    NULL,
    'Variable',
    'FAA Part 107, ASPRS Standards'
),
(
    'AERIAL-PHOTO',
    'Aerial Photogrammetry',
    'Manned aircraft photogrammetry',
    'Photogrammetry',
    'Manned Aircraft',
    'Aerial Camera',
    0.25,
    0.50,
    'Feet',
    'Mapping Grade',
    false,
    false,
    NULL,
    'Variable',
    'ASPRS Standards'
),

-- OTHER/LEGACY
(
    'TAPE-MEASURE',
    'Tape Measurement',
    'Manual measurement with surveyor''s tape',
    'Manual',
    'Direct Measurement',
    'Surveyor Tape',
    0.05,
    NULL,
    'Feet',
    'Construction Grade',
    false,
    true,
    300,
    '1-5 minutes',
    'Basic Survey Practice'
),
(
    'HANDHELD-GPS',
    'Handheld GPS',
    'Consumer-grade GPS device',
    'GNSS',
    'Handheld',
    'Handheld GPS',
    5.0,
    15.0,
    'Feet',
    'Recreation Grade',
    false,
    false,
    NULL,
    '1-2 seconds',
    'N/A'
);

-- Set initial usage counts to 0
UPDATE survey_point_description_standards SET usage_count = 0;
UPDATE survey_method_types SET usage_count = 0;
