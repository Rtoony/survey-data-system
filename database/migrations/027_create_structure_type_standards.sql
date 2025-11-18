-- Migration 027: Create Structure Type Standards Truth Table

CREATE TABLE structure_type_standards (
    structure_type_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    type_code VARCHAR(50) UNIQUE NOT NULL,
    type_name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    icon VARCHAR(100),
    specialized_tool_id UUID,
    required_attributes JSONB,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed with standard structure types
INSERT INTO structure_type_standards (type_code, type_name, category, description) VALUES
('MH', 'Manhole', 'Sanitary/Storm', 'Standard manhole structure'),
('CB', 'Catch Basin', 'Storm', 'Surface water inlet structure'),
('INLET', 'Inlet', 'Storm', 'Storm drain inlet'),
('OUTLET', 'Outlet', 'Storm', 'Storm drain outlet'),
('JUNCTION', 'Junction', 'Utilities', 'Junction structure'),
('CLEANOUT', 'Cleanout', 'Sanitary', 'Sewer cleanout'),
('VALVE', 'Valve', 'Water/Gas', 'Shutoff valve structure'),
('METER', 'Meter', 'Water', 'Water meter vault'),
('PUMP', 'Pump Station', 'Utilities', 'Pumping station'),
('TANK', 'Tank', 'Water', 'Storage tank'),
('VAULT', 'Vault', 'Utilities', 'Underground vault');

-- Add foreign key constraint to utility_structures
ALTER TABLE utility_structures
ADD CONSTRAINT fk_utility_structures_type
FOREIGN KEY (structure_type) REFERENCES structure_type_standards(type_code)
ON DELETE SET NULL
ON UPDATE CASCADE;

-- Create indexes
CREATE INDEX idx_structure_type_code ON structure_type_standards(type_code);
CREATE INDEX idx_structure_type_category ON structure_type_standards(category);
