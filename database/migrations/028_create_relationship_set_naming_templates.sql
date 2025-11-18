-- Migration 028: Create Relationship Set Naming Templates Truth Table

CREATE TABLE relationship_set_naming_templates (
    template_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    template_name VARCHAR(255) NOT NULL,
    name_format VARCHAR(500) NOT NULL,
    short_code_format VARCHAR(100) NOT NULL,
    category VARCHAR(100),
    description TEXT,
    token_definitions JSONB,
    usage_instructions TEXT,
    example_name VARCHAR(255),
    example_short_code VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed with standard templates
INSERT INTO relationship_set_naming_templates
(template_name, name_format, short_code_format, category, description, example_name, example_short_code)
VALUES
('Storm System Compliance', '{DISC}-{CAT}-{PROJECT_CODE}-{SEQ}', 'STORM-{PROJECT_CODE}-{SEQ}', 'Utilities', 'Storm drain system compliance tracking', 'CIV-STORM-PR001-01', 'STORM-PR001-01'),
('Material Compliance Check', 'MAT-{MATERIAL}-{PROJECT_CODE}', 'MAT-{MATERIAL}-{SEQ}', 'Materials', 'Material standards compliance', 'MAT-PVC-PR001', 'MAT-PVC-01'),
('Layer Standard Set', 'LAYER-{DISCIPLINE}-{PROJECT_CODE}', 'LYR-{DISC}-{SEQ}', 'CAD Standards', 'CAD layer compliance set', 'LAYER-CIV-PR001', 'LYR-CIV-01'),
('Detail Reference Set', 'DTL-{CATEGORY}-{PROJECT_CODE}', 'DTL-{CAT}-{SEQ}', 'Details', 'Detail standards tracking', 'DTL-UTIL-PR001', 'DTL-UTIL-01'),
('Pavement Material Set', 'PAVE-MAT-{PROJECT_CODE}', 'PAVE-{SEQ}', 'Pavement', 'Pavement material compliance', 'PAVE-MAT-PR001', 'PAVE-01');

-- Create indexes
CREATE INDEX idx_template_category ON relationship_set_naming_templates(category);
CREATE INDEX idx_template_active ON relationship_set_naming_templates(is_active);
