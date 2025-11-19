-- ============================================================================
-- CSI MASTERFORMAT SEED DATA - Civil Engineering Focus
-- ============================================================================
-- Version: 011
-- Date: 2025-11-18
-- Description: Populates CSI MasterFormat taxonomy with civil/survey divisions
--              Focus on Division 02 (Sitework), 33 (Utilities), 34 (Transportation)
-- Source: CSI MasterFormat 2020 Edition
-- ============================================================================

-- ============================================================================
-- DIVISION 02 - EXISTING CONDITIONS
-- ============================================================================

-- Level 1: Division
INSERT INTO csi_masterformat (csi_code, csi_title, division, section, subsection, parent_code, level, description, is_civil_engineering, is_active)
VALUES
('02 00 00', 'Existing Conditions', 2, 0, 0, NULL, 1, 'Division covering site assessment, selective demolition, and structure moving', TRUE, TRUE);

-- Level 2: Sections
INSERT INTO csi_masterformat (csi_code, csi_title, division, section, subsection, parent_code, level, description, is_civil_engineering, is_active)
VALUES
('02 20 00', 'Assessment', 2, 20, 0, '02 00 00', 2, 'Site surveys, geotechnical investigations, environmental assessments', TRUE, TRUE),
('02 30 00', 'Subsurface Investigation', 2, 30, 0, '02 00 00', 2, 'Test borings, soil sampling, core drilling', TRUE, TRUE),
('02 40 00', 'Demolition and Structure Moving', 2, 40, 0, '02 00 00', 2, 'Building and structure demolition', TRUE, TRUE),
('02 50 00', 'Containment and Disposal of Hazardous Materials', 2, 50, 0, '02 00 00', 2, 'Hazmat abatement and removal', TRUE, TRUE),
('02 60 00', 'Contaminated Site Material Removal', 2, 60, 0, '02 00 00', 2, 'Contaminated soil and groundwater remediation', TRUE, TRUE),
('02 70 00', 'Water and Energy Distribution Removal', 2, 70, 0, '02 00 00', 2, 'Removal of existing utility systems', TRUE, TRUE),
('02 80 00', 'Facility Remediation', 2, 80, 0, '02 00 00', 2, 'Mold, lead, asbestos remediation', TRUE, TRUE),
('02 90 00', 'Monitoring Chemical Sampling and Testing', 2, 90, 0, '02 00 00', 2, 'Environmental monitoring programs', TRUE, TRUE);

-- Level 3: Key Subsections for Civil Engineering
INSERT INTO csi_masterformat (csi_code, csi_title, division, section, subsection, parent_code, level, description, is_civil_engineering, is_active)
VALUES
-- Assessment subsections
('02 21 00', 'Surveys', 2, 21, 0, '02 20 00', 3, 'Boundary, topographic, construction surveys', TRUE, TRUE),
('02 21 13', 'Site Surveys', 2, 21, 13, '02 21 00', 3, 'Topographic and boundary surveys', TRUE, TRUE),
('02 21 16', 'Hydrographic Surveys', 2, 21, 16, '02 21 00', 3, 'Underwater and bathymetric surveys', TRUE, TRUE),
('02 22 00', 'Geotechnical Investigations', 2, 22, 0, '02 20 00', 3, 'Soil borings, SPT, CPT testing', TRUE, TRUE),

-- Subsurface Investigation
('02 32 00', 'Geotechnical Investigations', 2, 32, 0, '02 30 00', 3, 'Borings, test pits, soil analysis', TRUE, TRUE),
('02 32 13', 'Subsurface Drilling and Sampling', 2, 32, 13, '02 32 00', 3, 'Core drilling, soil sampling', TRUE, TRUE);

-- ============================================================================
-- DIVISION 31 - EARTHWORK
-- ============================================================================

INSERT INTO csi_masterformat (csi_code, csi_title, division, section, subsection, parent_code, level, description, is_civil_engineering, is_active)
VALUES
('31 00 00', 'Earthwork', 31, 0, 0, NULL, 1, 'Site grading, excavation, embankments, stabilization', TRUE, TRUE);

INSERT INTO csi_masterformat (csi_code, csi_title, division, section, subsection, parent_code, level, description, is_civil_engineering, is_active)
VALUES
('31 10 00', 'Site Clearing', 31, 10, 0, '31 00 00', 2, 'Tree and shrub removal, site stripping', TRUE, TRUE),
('31 20 00', 'Earth Moving', 31, 20, 0, '31 00 00', 2, 'Cut and fill, grading, excavation', TRUE, TRUE),
('31 30 00', 'Earthwork Methods', 31, 30, 0, '31 00 00', 2, 'Blasting, soil stabilization, dewatering', TRUE, TRUE),
('31 40 00', 'Shoring and Underpinning', 31, 40, 0, '31 00 00', 2, 'Temporary support systems', TRUE, TRUE),
('31 50 00', 'Excavation Support and Protection', 31, 50, 0, '31 00 00', 2, 'Slope protection, soil nailing', TRUE, TRUE),
('31 60 00', 'Special Foundations and Load-Bearing Elements', 31, 60, 0, '31 00 00', 2, 'Driven piles, drilled piers', TRUE, TRUE),
('31 70 00', 'Tunneling and Mining', 31, 70, 0, '31 00 00', 2, 'Tunnel construction', TRUE, TRUE);

INSERT INTO csi_masterformat (csi_code, csi_title, division, section, subsection, parent_code, level, description, is_civil_engineering, is_active)
VALUES
('31 11 00', 'Clearing and Grubbing', 31, 11, 0, '31 10 00', 3, 'Vegetation and obstruction removal', TRUE, TRUE),
('31 23 00', 'Excavation and Fill', 31, 23, 0, '31 20 00', 3, 'Mass excavation, embankment construction', TRUE, TRUE),
('31 25 00', 'Erosion and Sedimentation Controls', 31, 25, 0, '31 20 00', 3, 'BMPs, silt fencing, sediment basins', TRUE, TRUE),
('31 31 00', 'Soil Treatment', 31, 31, 0, '31 30 00', 3, 'Chemical stabilization, lime treatment', TRUE, TRUE),
('31 32 00', 'Soil Stabilization', 31, 32, 0, '31 30 00', 3, 'Geotextiles, geogrids, mechanical stabilization', TRUE, TRUE),
('31 33 00', 'Rock Stabilization', 31, 33, 0, '31 30 00', 3, 'Rock bolts, shotcrete, mesh', TRUE, TRUE);

-- ============================================================================
-- DIVISION 32 - EXTERIOR IMPROVEMENTS
-- ============================================================================

INSERT INTO csi_masterformat (csi_code, csi_title, division, section, subsection, parent_code, level, description, is_civil_engineering, is_active)
VALUES
('32 00 00', 'Exterior Improvements', 32, 0, 0, NULL, 1, 'Paving, curbs, walks, landscape improvements', TRUE, TRUE);

INSERT INTO csi_masterformat (csi_code, csi_title, division, section, subsection, parent_code, level, description, is_civil_engineering, is_active)
VALUES
('32 10 00', 'Bases, Ballasts, and Paving', 32, 10, 0, '32 00 00', 2, 'Pavement base courses and surfacing', TRUE, TRUE),
('32 30 00', 'Site Improvements', 32, 30, 0, '32 00 00', 2, 'Curbs, gutters, walks, fencing', TRUE, TRUE),
('32 70 00', 'Wetlands', 32, 70, 0, '32 00 00', 2, 'Wetland creation and restoration', TRUE, TRUE),
('32 80 00', 'Irrigation', 32, 80, 0, '32 00 00', 2, 'Landscape irrigation systems', TRUE, TRUE),
('32 90 00', 'Planting', 32, 90, 0, '32 00 00', 2, 'Trees, shrubs, groundcover', TRUE, TRUE);

INSERT INTO csi_masterformat (csi_code, csi_title, division, section, subsection, parent_code, level, description, is_civil_engineering, is_active)
VALUES
('32 11 00', 'Base Courses', 32, 11, 0, '32 10 00', 3, 'Aggregate base, subbase materials', TRUE, TRUE),
('32 12 00', 'Flexible Paving', 32, 12, 0, '32 10 00', 3, 'Asphalt concrete paving', TRUE, TRUE),
('32 13 00', 'Rigid Paving', 32, 13, 0, '32 10 00', 3, 'Portland cement concrete paving', TRUE, TRUE),
('32 14 00', 'Unit Paving', 32, 14, 0, '32 10 00', 3, 'Pavers, permeable pavement', TRUE, TRUE),
('32 31 00', 'Fences and Gates', 32, 31, 0, '32 30 00', 3, 'Chain link, ornamental, security fencing', TRUE, TRUE),
('32 32 00', 'Retaining Walls', 32, 32, 0, '32 30 00', 3, 'Modular block, cast-in-place, MSE walls', TRUE, TRUE),
('32 33 00', 'Site Furnishings', 32, 33, 0, '32 30 00', 3, 'Benches, trash receptacles, bike racks', TRUE, TRUE);

-- ============================================================================
-- DIVISION 33 - UTILITIES
-- ============================================================================

-- Level 1: Division
INSERT INTO csi_masterformat (csi_code, csi_title, division, section, subsection, parent_code, level, description, is_civil_engineering, is_active)
VALUES
('33 00 00', 'Utilities', 33, 0, 0, NULL, 1, 'Water supply, sanitary sewer, storm drainage, electrical, gas, communications', TRUE, TRUE);

-- Level 2: Major Sections
INSERT INTO csi_masterformat (csi_code, csi_title, division, section, subsection, parent_code, level, description, is_civil_engineering, is_active)
VALUES
('33 10 00', 'Water Utilities', 33, 10, 0, '33 00 00', 2, 'Water supply systems, mains, services', TRUE, TRUE),
('33 20 00', 'Wells', 33, 20, 0, '33 00 00', 2, 'Water wells, monitoring wells', TRUE, TRUE),
('33 30 00', 'Sanitary Sewerage', 33, 30, 0, '33 00 00', 2, 'Wastewater collection and treatment', TRUE, TRUE),
('33 40 00', 'Storm Drainage', 33, 40, 0, '33 00 00', 2, 'Stormwater management systems', TRUE, TRUE),
('33 50 00', 'Fuel Distribution', 33, 50, 0, '33 00 00', 2, 'Gas and fuel piping systems', TRUE, TRUE),
('33 60 00', 'Hydronic and Steam Energy Distribution', 33, 60, 0, '33 00 00', 2, 'District heating/cooling', TRUE, TRUE),
('33 70 00', 'Electrical Utilities', 33, 70, 0, '33 00 00', 2, 'Electrical distribution', TRUE, TRUE),
('33 80 00', 'Communications Utilities', 33, 80, 0, '33 00 00', 2, 'Telecom, fiber optic, CATV', TRUE, TRUE);

-- Level 3: Water Utilities Subsections
INSERT INTO csi_masterformat (csi_code, csi_title, division, section, subsection, parent_code, level, description, is_civil_engineering, is_active)
VALUES
('33 11 00', 'Water Utility Distribution Piping', 33, 11, 0, '33 10 00', 3, 'Water mains, distribution piping', TRUE, TRUE),
('33 12 00', 'Water Utility Distribution Equipment', 33, 12, 0, '33 10 00', 3, 'Valves, hydrants, meters', TRUE, TRUE),
('33 12 13', 'Watermain Gate Valves', 33, 12, 13, '33 12 00', 3, 'Gate valves for water distribution', TRUE, TRUE),
('33 12 16', 'Fire Hydrants', 33, 12, 16, '33 12 00', 3, 'Dry barrel and wet barrel hydrants', TRUE, TRUE),
('33 14 00', 'Water Utility Transmission and Distribution', 33, 14, 0, '33 10 00', 3, 'Large diameter transmission mains', TRUE, TRUE);

-- Level 3: Sanitary Sewer Subsections
INSERT INTO csi_masterformat (csi_code, csi_title, division, section, subsection, parent_code, level, description, is_civil_engineering, is_active)
VALUES
('33 31 00', 'Sanitary Utility Sewerage Piping', 33, 31, 0, '33 30 00', 3, 'Gravity sewer mains, force mains', TRUE, TRUE),
('33 32 00', 'Sanitary Utility Sewerage Equipment', 33, 32, 0, '33 30 00', 3, 'Manholes, pump stations', TRUE, TRUE),
('33 32 13', 'Sanitary Utility Sewerage Manholes', 33, 32, 13, '33 32 00', 3, 'Precast and cast-in-place manholes', TRUE, TRUE),
('33 32 16', 'Sanitary Utility Sewerage Pumps', 33, 32, 16, '33 32 00', 3, 'Sewage lift stations and pumps', TRUE, TRUE),
('33 36 00', 'Utility Septic Tanks', 33, 36, 0, '33 30 00', 3, 'Septic systems and drain fields', TRUE, TRUE);

-- Level 3: Storm Drainage Subsections
INSERT INTO csi_masterformat (csi_code, csi_title, division, section, subsection, parent_code, level, description, is_civil_engineering, is_active)
VALUES
('33 41 00', 'Storm Utility Drainage Piping', 33, 41, 0, '33 40 00', 3, 'Storm drain pipes, culverts', TRUE, TRUE),
('33 42 00', 'Storm Utility Drainage Equipment', 33, 42, 0, '33 40 00', 3, 'Inlets, catch basins, manholes', TRUE, TRUE),
('33 44 00', 'Storm Utility Water Drains', 33, 44, 0, '33 40 00', 3, 'Area drains, trench drains', TRUE, TRUE),
('33 46 00', 'Subdrainage', 33, 46, 0, '33 40 00', 3, 'Foundation drains, underdrains', TRUE, TRUE),
('33 47 00', 'Stormwater Management', 33, 47, 0, '33 40 00', 3, 'Detention/retention basins, bioswales', TRUE, TRUE),
('33 49 00', 'Storm Drainage Utilities', 33, 49, 0, '33 40 00', 3, 'Stormwater utilities general', TRUE, TRUE);

-- Additional Level 4 detail for critical items
INSERT INTO csi_masterformat (csi_code, csi_title, division, section, subsection, parent_code, level, description, is_civil_engineering, is_active)
VALUES
-- Storm drainage detail
('33 42 11', 'Storm Utility Drainage Manholes', 33, 42, 11, '33 42 00', 3, 'Storm drain manholes and junction structures', TRUE, TRUE),
('33 42 13', 'Storm Drainage Inlets', 33, 42, 13, '33 42 00', 3, 'Curb inlets, grate inlets, combination inlets', TRUE, TRUE),
('33 42 16', 'Catch Basins', 33, 42, 16, '33 42 00', 3, 'Catch basins with sumps', TRUE, TRUE),

-- Water utility detail
('33 11 13', 'Ductile Iron Water Utility Distribution Piping', 33, 11, 13, '33 11 00', 3, 'DI pipe for water distribution', TRUE, TRUE),
('33 11 16', 'PVC Water Utility Distribution Piping', 33, 11, 16, '33 11 00', 3, 'PVC pipe for water distribution', TRUE, TRUE),
('33 11 19', 'HDPE Water Utility Distribution Piping', 33, 11, 19, '33 11 00', 3, 'HDPE pipe for water distribution', TRUE, TRUE),

-- Sanitary sewer detail
('33 31 13', 'PVC Sanitary Utility Sewerage Piping', 33, 31, 13, '33 31 00', 3, 'PVC gravity sewer pipe', TRUE, TRUE),
('33 31 16', 'Ductile Iron Sanitary Force Mains', 33, 31, 16, '33 31 00', 3, 'DI force main piping', TRUE, TRUE);

-- ============================================================================
-- DIVISION 34 - TRANSPORTATION
-- ============================================================================

-- Level 1: Division
INSERT INTO csi_masterformat (csi_code, csi_title, division, section, subsection, parent_code, level, description, is_civil_engineering, is_active)
VALUES
('34 00 00', 'Transportation', 34, 0, 0, NULL, 1, 'Roadways, railways, marine, airport facilities', TRUE, TRUE);

-- Level 2: Sections
INSERT INTO csi_masterformat (csi_code, csi_title, division, section, subsection, parent_code, level, description, is_civil_engineering, is_active)
VALUES
('34 10 00', 'Guideways and Railways', 34, 10, 0, '34 00 00', 2, 'Rail tracks, ties, ballast', TRUE, TRUE),
('34 20 00', 'Traction Power', 34, 20, 0, '34 00 00', 2, 'Overhead catenary, third rail', TRUE, TRUE),
('34 40 00', 'Traffic Signals', 34, 40, 0, '34 00 00', 2, 'Traffic signal systems and equipment', TRUE, TRUE),
('34 50 00', 'Transportation Control and Service Equipment', 34, 50, 0, '34 00 00', 2, 'Traffic monitoring, ITS equipment', TRUE, TRUE),
('34 70 00', 'Transportation Construction and Equipment', 34, 70, 0, '34 00 00', 2, 'Roadway construction', TRUE, TRUE);

-- Level 3: Transportation Subsections
INSERT INTO csi_masterformat (csi_code, csi_title, division, section, subsection, parent_code, level, description, is_civil_engineering, is_active)
VALUES
('34 41 00', 'Roadway Signaling and Control Equipment', 34, 41, 0, '34 40 00', 3, 'Traffic signals, controllers', TRUE, TRUE),
('34 42 00', 'Pedestrian and Parking Control Equipment', 34, 42, 0, '34 40 00', 3, 'Pedestrian signals, parking gates', TRUE, TRUE),
('34 71 00', 'Roadway Construction', 34, 71, 0, '34 70 00', 3, 'Highway and street construction', TRUE, TRUE),
('34 71 13', 'Roadway Pavement', 34, 71, 13, '34 71 00', 3, 'Asphalt and concrete pavement', TRUE, TRUE),
('34 71 16', 'Curbs and Gutters', 34, 71, 16, '34 71 00', 3, 'Concrete curb and gutter', TRUE, TRUE),
('34 71 19', 'Roadway Pavement Markings', 34, 71, 19, '34 71 00', 3, 'Striping, thermoplastic, RPMs', TRUE, TRUE),
('34 72 00', 'Railway Construction', 34, 72, 0, '34 70 00', 3, 'Track construction', TRUE, TRUE);

-- ============================================================================
-- COMMON CALTRANS SPECIFICATIONS (For reference/mapping)
-- ============================================================================
-- These aren't official CSI codes but are commonly referenced in California
-- We'll add them as custom codes with a different format

INSERT INTO csi_masterformat (csi_code, csi_title, division, section, subsection, parent_code, level, description, is_civil_engineering, is_active, notes)
VALUES
-- Note: Using 'CT-' prefix for Caltrans-specific codes
('CT-19-3', 'Storm Drain Systems (Caltrans)', NULL, NULL, NULL, '33 40 00', 3, 'Caltrans Standard Spec Section 19-3: Storm Drain Systems', TRUE, TRUE, 'Maps to CSI 33 40 00'),
('CT-19-4', 'Manholes (Caltrans)', NULL, NULL, NULL, '33 32 13', 3, 'Caltrans Standard Spec Section 19-4: Manholes', TRUE, TRUE, 'Maps to CSI 33 32 13'),
('CT-52', 'Reinforcing Steel (Caltrans)', NULL, NULL, NULL, NULL, 3, 'Caltrans Standard Spec Section 52: Reinforcing Steel', TRUE, TRUE, 'General structural spec'),
('CT-90', 'Concrete Structures (Caltrans)', NULL, NULL, NULL, NULL, 3, 'Caltrans Standard Spec Section 90: Concrete Structures', TRUE, TRUE, 'General concrete spec');

-- ============================================================================
-- SUMMARY AND VERIFICATION
-- ============================================================================

DO $$
DECLARE
    total_codes INTEGER;
    civil_codes INTEGER;
    div_02 INTEGER;
    div_33 INTEGER;
    div_34 INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_codes FROM csi_masterformat;
    SELECT COUNT(*) INTO civil_codes FROM csi_masterformat WHERE is_civil_engineering = TRUE;
    SELECT COUNT(*) INTO div_02 FROM csi_masterformat WHERE division = 2;
    SELECT COUNT(*) INTO div_33 FROM csi_masterformat WHERE division = 33;
    SELECT COUNT(*) INTO div_34 FROM csi_masterformat WHERE division = 34;

    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'CSI MasterFormat Seed Data Complete';
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'Total CSI Codes Loaded: %', total_codes;
    RAISE NOTICE 'Civil Engineering Codes: %', civil_codes;
    RAISE NOTICE '';
    RAISE NOTICE 'By Division:';
    RAISE NOTICE '  Division 02 (Existing Conditions): % codes', div_02;
    RAISE NOTICE '  Division 31 (Earthwork): % codes', (SELECT COUNT(*) FROM csi_masterformat WHERE division = 31);
    RAISE NOTICE '  Division 32 (Exterior Improvements): % codes', (SELECT COUNT(*) FROM csi_masterformat WHERE division = 32);
    RAISE NOTICE '  Division 33 (Utilities): % codes', div_33;
    RAISE NOTICE '  Division 34 (Transportation): % codes', div_34;
    RAISE NOTICE '';
    RAISE NOTICE 'Sample Queries:';
    RAISE NOTICE '  SELECT * FROM csi_masterformat WHERE division = 33 AND level = 2;';
    RAISE NOTICE '  SELECT * FROM get_csi_children(''33 00 00'');';
    RAISE NOTICE '============================================================================';
END $$;
