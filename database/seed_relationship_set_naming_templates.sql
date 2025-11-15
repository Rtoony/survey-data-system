-- Seed data for Relationship Set Naming Templates
-- Provides initial standard naming conventions

INSERT INTO relationship_set_naming_templates 
(template_name, category, name_format, short_code_format, description, usage_instructions, example_name, example_code, example_tokens, required_tokens, optional_tokens, is_default)
VALUES

-- Storm/Drainage Systems
(
    'Storm System Compliance',
    'Drainage Infrastructure',
    '{PROJECT_CODE} - Storm System - {LOCATION}',
    'STORM-{PROJECT_CODE}-{SEQ}',
    'Standard template for storm drainage system relationship sets',
    'Use for tracking storm pipes, structures, details, and specs. PROJECT_CODE should match your project identifier. LOCATION describes the geographic area (e.g., "Main St & 5th Ave"). SEQ is a 2-digit sequence number.',
    'PRJ-2024-001 - Storm System - Main St & 5th Ave',
    'STORM-PRJ-2024-001-01',
    '{"PROJECT_CODE": "PRJ-2024-001", "LOCATION": "Main St & 5th Ave", "SEQ": "01"}'::jsonb,
    '["PROJECT_CODE", "LOCATION", "SEQ"]'::jsonb,
    '[]'::jsonb,
    true
),

-- Material Compliance
(
    'Material Compliance Check',
    'Materials & Specifications',
    '{MATERIAL} Compliance - {PROJECT_CODE}',
    'MAT-{MATERIAL}-{SEQ}',
    'Template for tracking compliance of specific materials across project elements',
    'Use when verifying all elements using a specific material (e.g., PVC) have proper specs, details, and notes. MATERIAL should be a standard material code (PVC, HDPE, RCP, etc.). SEQ is a 2-digit sequence.',
    'PVC Compliance - PRJ-2024-001',
    'MAT-PVC-01',
    '{"MATERIAL": "PVC", "PROJECT_CODE": "PRJ-2024-001", "SEQ": "01"}'::jsonb,
    '["MATERIAL", "PROJECT_CODE", "SEQ"]'::jsonb,
    '[]'::jsonb,
    true
),

-- Utility Networks
(
    'Utility Network Package',
    'Utilities',
    '{UTILITY_TYPE} Network - {PROJECT_CODE} - {LOCATION}',
    '{UTILITY_TYPE}-NET-{SEQ}',
    'Template for complete utility system packages (water, sewer, storm, gas, etc.)',
    'Use for grouping all elements of a specific utility type. UTILITY_TYPE should be one of: WATER, SEWER, STORM, GAS, ELEC, TELE. LOCATION is the geographic area. SEQ is a 2-digit sequence.',
    'WATER Network - PRJ-2024-001 - Downtown District',
    'WATER-NET-01',
    '{"UTILITY_TYPE": "WATER", "PROJECT_CODE": "PRJ-2024-001", "LOCATION": "Downtown District", "SEQ": "01"}'::jsonb,
    '["UTILITY_TYPE", "PROJECT_CODE", "LOCATION", "SEQ"]'::jsonb,
    '[]'::jsonb,
    false
),

-- Survey Control
(
    'Survey Control Network',
    'Survey & Mapping',
    'Survey Control - {PROJECT_CODE} - {CONTROL_TYPE}',
    'SURV-{CONTROL_TYPE}-{SEQ}',
    'Template for survey control point relationship sets',
    'Use for tracking survey control networks, benchmarks, and reference points. CONTROL_TYPE should be: HORIZONTAL, VERTICAL, or BOTH. SEQ is a 2-digit sequence.',
    'Survey Control - PRJ-2024-001 - HORIZONTAL',
    'SURV-HORIZONTAL-01',
    '{"PROJECT_CODE": "PRJ-2024-001", "CONTROL_TYPE": "HORIZONTAL", "SEQ": "01"}'::jsonb,
    '["PROJECT_CODE", "CONTROL_TYPE", "SEQ"]'::jsonb,
    '[]'::jsonb,
    true
),

-- ADA Compliance
(
    'ADA Compliance Package',
    'Accessibility',
    'ADA Compliance - {PROJECT_CODE} - {FEATURE_TYPE}',
    'ADA-{FEATURE_TYPE}-{SEQ}',
    'Template for ADA accessibility feature compliance tracking',
    'Use for ensuring all ADA elements (ramps, crosswalks, parking, etc.) meet standards. FEATURE_TYPE describes the ADA feature category (RAMPS, PARKING, PATHS, etc.). SEQ is a 2-digit sequence.',
    'ADA Compliance - PRJ-2024-001 - RAMPS',
    'ADA-RAMPS-01',
    '{"PROJECT_CODE": "PRJ-2024-001", "FEATURE_TYPE": "RAMPS", "SEQ": "01"}'::jsonb,
    '["PROJECT_CODE", "FEATURE_TYPE", "SEQ"]'::jsonb,
    '[]'::jsonb,
    true
),

-- Pavement/Road Systems
(
    'Pavement System Package',
    'Road Infrastructure',
    'Pavement System - {PROJECT_CODE} - {STREET_NAME}',
    'PAVE-{PROJECT_CODE}-{SEQ}',
    'Template for pavement and road construction compliance',
    'Use for tracking pavement, curb, gutter, striping, and related elements. STREET_NAME identifies the roadway. SEQ is a 2-digit sequence.',
    'Pavement System - PRJ-2024-001 - Main Street',
    'PAVE-PRJ-2024-001-01',
    '{"PROJECT_CODE": "PRJ-2024-001", "STREET_NAME": "Main Street", "SEQ": "01"}'::jsonb,
    '["PROJECT_CODE", "STREET_NAME", "SEQ"]'::jsonb,
    '[]'::jsonb,
    false
),

-- General Compliance
(
    'General Compliance Set',
    'General',
    '{CATEGORY} Compliance - {PROJECT_CODE}',
    '{CATEGORY}-COMP-{SEQ}',
    'Generic template for any compliance tracking need',
    'Use when no specific template fits your needs. CATEGORY describes what you are tracking (e.g., "Erosion Control", "Traffic Control", "Landscaping"). SEQ is a 2-digit sequence.',
    'Erosion Control Compliance - PRJ-2024-001',
    'EROSION-COMP-01',
    '{"CATEGORY": "Erosion Control", "PROJECT_CODE": "PRJ-2024-001", "SEQ": "01"}'::jsonb,
    '["CATEGORY", "PROJECT_CODE", "SEQ"]'::jsonb,
    '[]'::jsonb,
    false
),

-- Construction Phase
(
    'Construction Phase Package',
    'Phasing',
    'Phase {PHASE_NUM} - {PROJECT_CODE} - {DESCRIPTION}',
    'PH{PHASE_NUM}-{SEQ}',
    'Template for tracking elements by construction phase',
    'Use when organizing work by construction phases. PHASE_NUM is the phase number (1, 2, 3, etc.). DESCRIPTION is a brief phase description. SEQ is a 2-digit sequence.',
    'Phase 1 - PRJ-2024-001 - Underground Utilities',
    'PH1-01',
    '{"PHASE_NUM": "1", "PROJECT_CODE": "PRJ-2024-001", "DESCRIPTION": "Underground Utilities", "SEQ": "01"}'::jsonb,
    '["PHASE_NUM", "PROJECT_CODE", "DESCRIPTION", "SEQ"]'::jsonb,
    '[]'::jsonb,
    false
),

-- BMP/Water Quality
(
    'BMP & Water Quality Package',
    'Stormwater Quality',
    'BMP System - {PROJECT_CODE} - {BMP_TYPE}',
    'BMP-{BMP_TYPE}-{SEQ}',
    'Template for Best Management Practice and water quality compliance',
    'Use for tracking bioretention, swales, filters, and other BMPs. BMP_TYPE should describe the BMP category (BIORET, SWALE, FILTER, etc.). SEQ is a 2-digit sequence.',
    'BMP System - PRJ-2024-001 - BIORET',
    'BMP-BIORET-01',
    '{"PROJECT_CODE": "PRJ-2024-001", "BMP_TYPE": "BIORET", "SEQ": "01"}'::jsonb,
    '["PROJECT_CODE", "BMP_TYPE", "SEQ"]'::jsonb,
    '[]'::jsonb,
    false
),

-- Detail Cross-Reference
(
    'Detail Cross-Reference Set',
    'Documentation',
    'Detail References - {DETAIL_FAMILY} - {PROJECT_CODE}',
    'DTL-{DETAIL_FAMILY}-{SEQ}',
    'Template for tracking all elements that reference specific detail families',
    'Use to ensure all elements that should reference a detail actually do. DETAIL_FAMILY is the detail type (STORM, CURB, PAVE, etc.). SEQ is a 2-digit sequence.',
    'Detail References - STORM - PRJ-2024-001',
    'DTL-STORM-01',
    '{"DETAIL_FAMILY": "STORM", "PROJECT_CODE": "PRJ-2024-001", "SEQ": "01"}'::jsonb,
    '["DETAIL_FAMILY", "PROJECT_CODE", "SEQ"]'::jsonb,
    '[]'::jsonb,
    false
);

-- Set usage_count for demonstration (in production, this would be tracked by actual usage)
UPDATE relationship_set_naming_templates SET usage_count = 0;
