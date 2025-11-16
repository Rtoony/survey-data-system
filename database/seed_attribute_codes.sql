-- ==============================================================================
-- Seed Data for Attribute Codes
-- ==============================================================================
-- Purpose: Populate common attribute codes used in civil engineering CAD standards
-- Created: 2025-11-16
-- ==============================================================================

-- ==============================================================================
-- 1. Size/Dimension Attributes (Pipe Diameters, Common Sizes)
-- ==============================================================================
INSERT INTO attribute_codes (code, name, description, attribute_type, is_locked, sort_order) VALUES
-- Pipe sizes (inches)
('4IN', '4 Inch', '4-inch diameter pipe', 'size', TRUE, 10),
('6IN', '6 Inch', '6-inch diameter pipe', 'size', TRUE, 20),
('8IN', '8 Inch', '8-inch diameter pipe', 'size', TRUE, 30),
('10IN', '10 Inch', '10-inch diameter pipe', 'size', TRUE, 40),
('12IN', '12 Inch', '12-inch diameter pipe', 'size', TRUE, 50),
('15IN', '15 Inch', '15-inch diameter pipe', 'size', TRUE, 60),
('18IN', '18 Inch', '18-inch diameter pipe', 'size', TRUE, 70),
('21IN', '21 Inch', '21-inch diameter pipe', 'size', TRUE, 80),
('24IN', '24 Inch', '24-inch diameter pipe', 'size', TRUE, 90),
('30IN', '30 Inch', '30-inch diameter pipe', 'size', TRUE, 100),
('36IN', '36 Inch', '36-inch diameter pipe', 'size', TRUE, 110),
('42IN', '42 Inch', '42-inch diameter pipe', 'size', TRUE, 120),
('48IN', '48 Inch', '48-inch diameter pipe', 'size', TRUE, 130),

-- Dimensional sizes (feet)
('2FT', '2 Foot', '2-foot dimension', 'size', FALSE, 210),
('4FT', '4 Foot', '4-foot dimension', 'size', FALSE, 220),
('6FT', '6 Foot', '6-foot dimension', 'size', FALSE, 230),
('8FT', '8 Foot', '8-foot dimension', 'size', FALSE, 240),
('10FT', '10 Foot', '10-foot dimension', 'size', FALSE, 250)

ON CONFLICT (code) DO NOTHING;

-- ==============================================================================
-- 2. Material Attributes
-- ==============================================================================
INSERT INTO attribute_codes (code, name, description, attribute_type, is_locked, sort_order) VALUES
-- Pipe materials
('PVC', 'PVC', 'Polyvinyl chloride pipe', 'material', TRUE, 310),
('HDPE', 'HDPE', 'High-density polyethylene pipe', 'material', TRUE, 320),
('RCP', 'Reinforced Concrete Pipe', 'Reinforced concrete pipe', 'material', TRUE, 330),
('VCP', 'Vitrified Clay Pipe', 'Vitrified clay pipe', 'material', TRUE, 340),
('DI', 'Ductile Iron', 'Ductile iron pipe', 'material', TRUE, 350),
('STEEL', 'Steel', 'Steel pipe', 'material', TRUE, 360),

-- Construction materials
('CONC', 'Concrete', 'Concrete material', 'material', TRUE, 410),
('AC', 'Asphalt Concrete', 'Asphalt concrete pavement', 'material', TRUE, 420),
('PVMT', 'Pavement', 'Generic pavement material', 'material', FALSE, 430)

ON CONFLICT (code) DO NOTHING;

-- ==============================================================================
-- 3. Function/Type Attributes (for BMPs, basins, survey points)
-- ==============================================================================
INSERT INTO attribute_codes (code, name, description, attribute_type, is_locked, sort_order) VALUES
-- BMP/Basin functions
('STORAGE', 'Storage', 'Storage function (detention, retention)', 'function', TRUE, 510),
('TREATMENT', 'Treatment', 'Water quality treatment function', 'function', TRUE, 520),
('DETENTION', 'Detention', 'Stormwater detention (temporary storage)', 'function', TRUE, 530),
('RETENTION', 'Retention', 'Stormwater retention (permanent pool)', 'function', TRUE, 540),
('INFILTRATION', 'Infiltration', 'Infiltration/percolation function', 'function', TRUE, 550),
('BIOTREAT', 'Biotreatment', 'Biological treatment system', 'function', FALSE, 560),

-- Survey point types
('TOPO', 'Topographic', 'Topographic survey point', 'function', TRUE, 610),
('CONTROL', 'Control', 'Survey control point', 'function', TRUE, 620),
('BNDY', 'Boundary', 'Property boundary point', 'function', FALSE, 630),

-- Generic type modifiers
('STD', 'Standard', 'Standard type/configuration', 'type', FALSE, 710),
('CUST', 'Custom', 'Custom type/configuration', 'type', FALSE, 720),
('TYP', 'Typical', 'Typical detail or configuration', 'type', FALSE, 730)

ON CONFLICT (code) DO NOTHING;

-- ==============================================================================
-- 4. Surface Type Attributes
-- ==============================================================================
INSERT INTO attribute_codes (code, name, description, attribute_type, is_locked, sort_order) VALUES
('PERVIOUS', 'Pervious', 'Pervious surface (water permeable)', 'type', FALSE, 810),
('IMPERVIOUS', 'Impervious', 'Impervious surface (no water infiltration)', 'type', FALSE, 820),
('POROUS', 'Porous', 'Porous pavement or surface', 'type', FALSE, 830)

ON CONFLICT (code) DO NOTHING;

-- ==============================================================================
-- Summary
-- ==============================================================================
-- This seed data includes:
-- - 18 pipe sizes (4" to 48")
-- - 9 materials (PVC, RCP, CONC, etc.)
-- - 9 function types (STORAGE, TREATMENT, TOPO, CONTROL, etc.)
-- - 3 generic type modifiers (STD, CUST, TYP)
-- - 3 surface types (PERVIOUS, IMPERVIOUS, POROUS)
--
-- Total: ~42 attribute codes
-- 
-- Locked attributes (is_locked=TRUE) are system-critical and cannot be deleted
-- Unlocked attributes can be customized per client requirements
-- ==============================================================================
