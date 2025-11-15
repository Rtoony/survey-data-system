-- Seed Filterable Entity Columns
-- Initial configuration for common entity types

-- Utility Lines
INSERT INTO filterable_entity_columns (entity_type, entity_table, column_name, display_name, data_type, operators_supported, description, sort_order) VALUES
('utility_line', 'utility_lines', 'material', 'Pipe Material', 'text', '["equals"]', 'Material type of the utility line (PVC, DI, HDPE, etc.)', 1),
('utility_line', 'utility_lines', 'diameter', 'Diameter', 'numeric', '["equals", "gt", "gte", "lt", "lte"]', 'Pipe diameter in inches', 2),
('utility_line', 'utility_lines', 'line_type', 'Line Type', 'text', '["equals"]', 'Type of utility line (storm, sewer, water, etc.)', 3),
('utility_line', 'utility_lines', 'install_year', 'Installation Year', 'numeric', '["equals", "gt", "gte", "lt", "lte"]', 'Year the line was installed', 4),
('utility_line', 'utility_lines', 'owner', 'Owner', 'text', '["equals"]', 'Entity responsible for the utility', 5);

-- Utility Structures
INSERT INTO filterable_entity_columns (entity_type, entity_table, column_name, display_name, data_type, operators_supported, description, sort_order) VALUES
('utility_structure', 'utility_structures', 'structure_type', 'Structure Type', 'text', '["equals"]', 'Type of structure (MH, CB, INLET, etc.)', 1),
('utility_structure', 'utility_structures', 'material', 'Material', 'text', '["equals"]', 'Structure material', 2),
('utility_structure', 'utility_structures', 'rim_elevation', 'Rim Elevation', 'numeric', '["equals", "gt", "gte", "lt", "lte"]', 'Top of structure elevation', 3),
('utility_structure', 'utility_structures', 'invert_elevation', 'Invert Elevation', 'numeric', '["equals", "gt", "gte", "lt", "lte"]', 'Bottom of structure elevation', 4);

-- BMPs
INSERT INTO filterable_entity_columns (entity_type, entity_table, column_name, display_name, data_type, operators_supported, description, sort_order) VALUES
('bmp', 'bmps', 'bmp_type', 'BMP Type', 'text', '["equals"]', 'Type of Best Management Practice', 1),
('bmp', 'bmps', 'treatment_type', 'Treatment Type', 'text', '["equals"]', 'Treatment method category', 2),
('bmp', 'bmps', 'drainage_area', 'Drainage Area', 'numeric', '["equals", "gt", "gte", "lt", "lte"]', 'Contributing drainage area in acres', 3),
('bmp', 'bmps', 'design_storm', 'Design Storm', 'text', '["equals"]', 'Design storm event (10-yr, 25-yr, etc.)', 4);

-- Survey Points
INSERT INTO filterable_entity_columns (entity_type, entity_table, column_name, display_name, data_type, operators_supported, description, sort_order) VALUES
('survey_point', 'survey_points', 'point_code', 'Point Code', 'text', '["equals"]', 'Survey point code from field data', 1),
('survey_point', 'survey_points', 'feature_type', 'Feature Type', 'text', '["equals"]', 'Type of surveyed feature', 2),
('survey_point', 'survey_points', 'elevation', 'Elevation', 'numeric', '["equals", "gt", "gte", "lt", "lte"]', 'Point elevation', 3);

-- Detail Standards
INSERT INTO filterable_entity_columns (entity_type, entity_table, column_name, display_name, data_type, operators_supported, description, sort_order) VALUES
('detail_standard', 'detail_standards', 'detail_code', 'Detail Code', 'text', '["equals"]', 'Standard detail identifier', 1),
('detail_standard', 'detail_standards', 'detail_type', 'Detail Type', 'text', '["equals"]', 'Category of detail', 2),
('detail_standard', 'detail_standards', 'category', 'Category', 'text', '["equals"]', 'Detail category grouping', 3);

-- CAD Block Standards
INSERT INTO filterable_entity_columns (entity_type, entity_table, column_name, display_name, data_type, operators_supported, description, sort_order) VALUES
('block_standard', 'block_standards', 'block_name', 'Block Name', 'text', '["equals"]', 'CAD block name', 1),
('block_standard', 'block_standards', 'block_type', 'Block Type', 'text', '["equals"]', 'Type/category of block', 2),
('block_standard', 'block_standards', 'layer_name', 'Layer', 'text', '["equals"]', 'Default layer for block', 3);

-- Note Standards
INSERT INTO filterable_entity_columns (entity_type, entity_table, column_name, display_name, data_type, operators_supported, description, sort_order) VALUES
('note_standard', 'note_standards', 'note_code', 'Note Code', 'text', '["equals"]', 'Standard note identifier', 1),
('note_standard', 'note_standards', 'category', 'Category', 'text', '["equals"]', 'Note category', 2),
('note_standard', 'note_standards', 'discipline', 'Discipline', 'text', '["equals"]', 'Engineering discipline', 3);

-- Hatch Standards
INSERT INTO filterable_entity_columns (entity_type, entity_table, column_name, display_name, data_type, operators_supported, description, sort_order) VALUES
('hatch_standard', 'hatch_standards', 'hatch_name', 'Hatch Name', 'text', '["equals"]', 'Standard hatch pattern name', 1),
('hatch_standard', 'hatch_standards', 'pattern_type', 'Pattern Type', 'text', '["equals"]', 'Type of hatch pattern', 2);

-- Material Standards
INSERT INTO filterable_entity_columns (entity_type, entity_table, column_name, display_name, data_type, operators_supported, description, sort_order) VALUES
('material_standard', 'material_standards', 'material_code', 'Material Code', 'text', '["equals"]', 'Standard material identifier', 1),
('material_standard', 'material_standards', 'material_type', 'Material Type', 'text', '["equals"]', 'Category of material', 2),
('material_standard', 'material_standards', 'category', 'Category', 'text', '["equals"]', 'Material grouping', 3);

-- Project Notes
INSERT INTO filterable_entity_columns (entity_type, entity_table, column_name, display_name, data_type, operators_supported, description, sort_order) VALUES
('project_note', 'project_notes', 'note_code', 'Note Code', 'text', '["equals"]', 'Note identifier', 1),
('project_note', 'project_notes', 'category', 'Category', 'text', '["equals"]', 'Note category', 2),
('project_note', 'project_notes', 'is_custom', 'Is Custom', 'boolean', '["equals"]', 'Custom vs standard note', 3);

-- Sheets
INSERT INTO filterable_entity_columns (entity_type, entity_table, column_name, display_name, data_type, operators_supported, description, sort_order) VALUES
('sheet', 'sheets', 'sheet_number', 'Sheet Number', 'text', '["equals"]', 'Sheet number in set', 1),
('sheet', 'sheets', 'sheet_type', 'Sheet Type', 'text', '["equals"]', 'Type of sheet (plan, profile, detail)', 2),
('sheet', 'sheets', 'discipline', 'Discipline', 'text', '["equals"]', 'Engineering discipline', 3);
