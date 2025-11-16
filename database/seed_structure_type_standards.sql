-- ============================================================================
-- Seed Data for Structure Type Standards
-- Provides initial standard structure types for civil/survey workflows
-- ============================================================================

INSERT INTO structure_type_standards
(type_code, type_name, type_description, category, subcategory, icon_class, color_hex, common_materials, typical_depth_range, typical_diameter_range, requires_inspection, inspection_frequency, related_standards)
VALUES

-- ============================================================================
-- STORM DRAINAGE STRUCTURES
-- ============================================================================
(
    'MH',
    'Manhole',
    'Standard manhole structure for storm drainage system access and maintenance',
    'Storm Drainage',
    'Access Structures',
    'fa-circle-dot',
    '#00BCD4',
    '["Precast Concrete", "Brick", "Cast-in-Place Concrete"]'::jsonb,
    '4-20 feet',
    '48-120 inches',
    true,
    'Annual',
    'ASTM C478, Local Agency Standard Plans'
),
(
    'CB',
    'Catch Basin',
    'Surface drainage inlet with sump for sediment collection',
    'Storm Drainage',
    'Inlet Structures',
    'fa-square',
    '#00BCD4',
    '["Precast Concrete", "Cast-in-Place Concrete"]'::jsonb,
    '4-8 feet',
    '24-72 inches',
    true,
    'Annual',
    'Caltrans Standard Plans, Local Standards'
),
(
    'INLET',
    'Storm Drain Inlet',
    'Surface water collection point without sump',
    'Storm Drainage',
    'Inlet Structures',
    'fa-square-full',
    '#00BCD4',
    '["Precast Concrete", "Plastic"]'::jsonb,
    '2-6 feet',
    '12-48 inches',
    false,
    'Biennial',
    'Local Standard Details'
),
(
    'CLNOUT',
    'Cleanout',
    'Access point for maintenance and inspection of storm drain lines',
    'Storm Drainage',
    'Access Structures',
    'fa-circle',
    '#00BCD4',
    '["PVC", "HDPE", "Precast Concrete"]'::jsonb,
    '3-8 feet',
    '12-24 inches',
    false,
    null,
    'Local Standards'
),
(
    'JBOX',
    'Junction Box',
    'Structure where multiple storm drain pipes connect',
    'Storm Drainage',
    'Junction Structures',
    'fa-square-check',
    '#00BCD4',
    '["Precast Concrete", "Cast-in-Place Concrete"]'::jsonb,
    '4-12 feet',
    '48-96 inches',
    true,
    'Annual',
    'Local Standard Plans'
),

-- ============================================================================
-- SANITARY SEWER STRUCTURES
-- ============================================================================
(
    'SMH',
    'Sanitary Manhole',
    'Manhole structure for sanitary sewer system access and maintenance',
    'Sanitary Sewer',
    'Access Structures',
    'fa-circle-dot',
    '#9C27B0',
    '["Precast Concrete", "Brick", "Fiberglass"]'::jsonb,
    '6-25 feet',
    '48-120 inches',
    true,
    'Annual',
    'ASTM C478, SSMP Requirements'
),
(
    'SCLNOUT',
    'Sanitary Cleanout',
    'Access point for sanitary sewer maintenance',
    'Sanitary Sewer',
    'Access Structures',
    'fa-circle',
    '#9C27B0',
    '["PVC", "ABS"]'::jsonb,
    '2-6 feet',
    '6-12 inches',
    false,
    null,
    'UPC, Local Standards'
),
(
    'LIFTSTATION',
    'Lift Station',
    'Pumping station for sanitary sewer flow',
    'Sanitary Sewer',
    'Pump Stations',
    'fa-pump',
    '#9C27B0',
    '["Precast Concrete", "Fiberglass", "Steel"]'::jsonb,
    '10-30 feet',
    '72-180 inches',
    true,
    'Monthly',
    'SSMP, Ten States Standards'
),

-- ============================================================================
-- WATER SYSTEM STRUCTURES
-- ============================================================================
(
    'VALVE',
    'Water Valve',
    'Control valve for water distribution system',
    'Water Distribution',
    'Valve Structures',
    'fa-valve',
    '#2196F3',
    '["Ductile Iron", "Cast Iron", "Bronze"]'::jsonb,
    '3-8 feet',
    '24-60 inches',
    true,
    'Annual',
    'AWWA C500, AWWA C509'
),
(
    'HYDRANT',
    'Fire Hydrant',
    'Fire protection water supply point',
    'Water Distribution',
    'Fire Protection',
    'fa-fire-extinguisher',
    '#FF5722',
    '["Ductile Iron", "Cast Iron"]'::jsonb,
    '4-6 feet',
    '24-36 inches',
    true,
    'Annual',
    'AWWA C502, NFPA 291'
),
(
    'METER',
    'Water Meter Vault',
    'Vault housing water meter for service connection',
    'Water Distribution',
    'Metering',
    'fa-gauge',
    '#2196F3',
    '["Precast Concrete", 'Plastic", "Composite"]'::jsonb,
    '2-5 feet',
    '24-48 inches',
    true,
    'Annual',
    'AWWA M6, Local Standards'
),
(
    'AIR_VALVE',
    'Air Release Valve',
    'Valve assembly for releasing trapped air in water mains',
    'Water Distribution',
    'Valve Structures',
    'fa-wind',
    '#2196F3',
    '["Ductile Iron", "Cast Iron"]'::jsonb,
    '4-8 feet',
    '24-48 inches',
    true,
    'Annual',
    'AWWA C512'
),

-- ============================================================================
-- BMP / WATER QUALITY STRUCTURES
-- ============================================================================
(
    'BIORET',
    'Bioretention Basin',
    'Vegetated depression for stormwater treatment',
    'Stormwater Quality',
    'BMP Structures',
    'fa-leaf',
    '#4CAF50',
    '["Engineered Soil", "Underdrain Pipe", "Gravel"]'::jsonb,
    '2-6 feet',
    'Variable',
    true,
    'Quarterly',
    'Local NPDES Requirements, CA Stormwater BMP Handbook'
),
(
    'FILTER',
    'Media Filter',
    'Sand or other media filtration system for stormwater treatment',
    'Stormwater Quality',
    'BMP Structures',
    'fa-filter',
    '#4CAF50',
    '["Sand", "Perlite", "Precast Concrete Vault"]'::jsonb,
    '4-8 feet',
    '48-96 inches',
    true,
    'Quarterly',
    'CA Stormwater BMP Handbook'
),
(
    'SEPARATOR',
    'Oil/Water Separator',
    'Structure for separating oil and sediment from stormwater',
    'Stormwater Quality',
    'BMP Structures',
    'fa-oil-can',
    '#4CAF50',
    '["Precast Concrete", "Fiberglass", "Steel"]'::jsonb,
    '4-8 feet',
    '48-96 inches',
    true,
    'Quarterly',
    'Local Industrial Pretreatment Standards'
),

-- ============================================================================
-- GENERAL / OTHER
-- ============================================================================
(
    'VAULT',
    'Underground Vault',
    'Generic underground vault or chamber',
    'General',
    'Storage/Access',
    'fa-box',
    '#607D8B',
    '["Precast Concrete", "Cast-in-Place Concrete"]'::jsonb,
    '4-12 feet',
    '48-120 inches',
    false,
    null,
    'Project-Specific'
),
(
    'PULLBOX',
    'Pull Box',
    'Electrical or communications pull box',
    'Utilities - Dry',
    'Electrical/Comm',
    'fa-box-open',
    '#FF9800',
    '["Precast Concrete", "Plastic", "Fiberglass"]'::jsonb,
    '2-6 feet',
    '24-48 inches',
    false,
    null,
    'NEC, Local Standards'
),
(
    'HANDHOLE',
    'Handhole',
    'Small access point for utilities',
    'General',
    'Access Structures',
    'fa-hand',
    '#607D8B',
    '["Plastic", "Fiberglass", "Precast Concrete"]'::jsonb,
    '1-3 feet',
    '12-24 inches',
    false,
    null,
    'Local Standards'
);

-- Set initial usage counts to 0 (will be updated as structures are created)
UPDATE structure_type_standards SET usage_count = 0;
