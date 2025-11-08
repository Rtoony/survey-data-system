-- Migration: Create CAD Standards Vocabulary Schema
-- Purpose: Revolutionary database-optimized CAD naming system
-- Date: 2025-11-08

-- 1. Discipline codes table
CREATE TABLE IF NOT EXISTS discipline_codes (
    discipline_id SERIAL PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Category codes table (belong to disciplines)
CREATE TABLE IF NOT EXISTS category_codes (
    category_id SERIAL PRIMARY KEY,
    discipline_id INTEGER REFERENCES discipline_codes(discipline_id) ON DELETE CASCADE,
    code VARCHAR(10) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(discipline_id, code)
);

-- 3. Object type codes table (belong to categories)
CREATE TABLE IF NOT EXISTS object_type_codes (
    type_id SERIAL PRIMARY KEY,
    category_id INTEGER REFERENCES category_codes(category_id) ON DELETE CASCADE,
    code VARCHAR(10) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    description TEXT,
    database_table VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category_id, code)
);

-- 4. Attribute codes table (sizes, materials, types)
CREATE TABLE IF NOT EXISTS attribute_codes (
    attribute_id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,
    full_name VARCHAR(100),
    attribute_category VARCHAR(50),
    description TEXT,
    pattern VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Phase codes table
CREATE TABLE IF NOT EXISTS phase_codes (
    phase_id SERIAL PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    description TEXT,
    color_rgb VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Geometry codes table
CREATE TABLE IF NOT EXISTS geometry_codes (
    geometry_id SERIAL PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    description TEXT,
    dxf_entity_types TEXT[],
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Standard layer patterns table (the complete template)
CREATE TABLE IF NOT EXISTS standard_layer_patterns (
    pattern_id SERIAL PRIMARY KEY,
    discipline_id INTEGER REFERENCES discipline_codes(discipline_id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES category_codes(category_id) ON DELETE CASCADE,
    type_id INTEGER REFERENCES object_type_codes(type_id) ON DELETE CASCADE,
    phase_id INTEGER REFERENCES phase_codes(phase_id) ON DELETE CASCADE,
    geometry_id INTEGER REFERENCES geometry_codes(geometry_id) ON DELETE CASCADE,
    full_layer_name VARCHAR(200) NOT NULL UNIQUE,
    description TEXT,
    database_table VARCHAR(100),
    example_attributes JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. Import mapping patterns table (client variations)
CREATE TABLE IF NOT EXISTS import_mapping_patterns (
    mapping_id SERIAL PRIMARY KEY,
    client_name VARCHAR(100),
    source_pattern VARCHAR(200) NOT NULL,
    regex_pattern TEXT NOT NULL,
    target_discipline_id INTEGER REFERENCES discipline_codes(discipline_id) ON DELETE CASCADE,
    target_category_id INTEGER REFERENCES category_codes(category_id) ON DELETE CASCADE,
    target_type_id INTEGER REFERENCES object_type_codes(type_id) ON DELETE CASCADE,
    extraction_rules JSONB,
    confidence_score INTEGER DEFAULT 80,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_category_codes_discipline ON category_codes(discipline_id);
CREATE INDEX IF NOT EXISTS idx_object_type_codes_category ON object_type_codes(category_id);
CREATE INDEX IF NOT EXISTS idx_standard_layer_patterns_lookup ON standard_layer_patterns(discipline_id, category_id, type_id);
CREATE INDEX IF NOT EXISTS idx_import_mapping_patterns_client ON import_mapping_patterns(client_name);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to all standards tables
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_discipline_codes_updated_at') THEN
        CREATE TRIGGER update_discipline_codes_updated_at BEFORE UPDATE ON discipline_codes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_category_codes_updated_at') THEN
        CREATE TRIGGER update_category_codes_updated_at BEFORE UPDATE ON category_codes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_object_type_codes_updated_at') THEN
        CREATE TRIGGER update_object_type_codes_updated_at BEFORE UPDATE ON object_type_codes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_attribute_codes_updated_at') THEN
        CREATE TRIGGER update_attribute_codes_updated_at BEFORE UPDATE ON attribute_codes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_phase_codes_updated_at') THEN
        CREATE TRIGGER update_phase_codes_updated_at BEFORE UPDATE ON phase_codes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_geometry_codes_updated_at') THEN
        CREATE TRIGGER update_geometry_codes_updated_at BEFORE UPDATE ON geometry_codes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- Add comments for documentation
COMMENT ON TABLE discipline_codes IS 'Top-level discipline classification (CIV, SITE, SURV, LAND, etc.)';
COMMENT ON TABLE category_codes IS 'Category within discipline (UTIL, ROAD, GRAD, STOR, etc.)';
COMMENT ON TABLE object_type_codes IS 'Specific object types (STORM, MH, CNTR, etc.) - maps to database tables';
COMMENT ON TABLE attribute_codes IS 'Reusable attribute codes for layer names (sizes, materials, types)';
COMMENT ON TABLE phase_codes IS 'Construction phase codes (NEW, EXIST, DEMO, FUTR, etc.)';
COMMENT ON TABLE geometry_codes IS 'CAD geometry type codes (LN, PT, PG, TX, etc.)';
COMMENT ON TABLE standard_layer_patterns IS 'Complete layer name templates for validation';
COMMENT ON TABLE import_mapping_patterns IS 'Regex patterns for mapping client CAD layers to standard format';
