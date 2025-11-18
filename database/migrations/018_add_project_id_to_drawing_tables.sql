-- Migration 018: Add project_id column to drawing tables
-- This fixes DXF import failures caused by missing project_id columns
-- The dxf_importer.py code was updated to INSERT with project_id, but these tables
-- were never migrated to include the project_id column.

-- Add project_id to drawing_text
ALTER TABLE drawing_text
ADD COLUMN project_id UUID;

-- Add project_id to drawing_dimensions
ALTER TABLE drawing_dimensions
ADD COLUMN project_id UUID;

-- Add project_id to drawing_hatches
ALTER TABLE drawing_hatches
ADD COLUMN project_id UUID;

-- Add project_id to block_inserts
ALTER TABLE block_inserts
ADD COLUMN project_id UUID;

-- Note: We don't add NOT NULL constraint because there may be existing rows
-- Note: drawing_entities already has project_id column (was partially migrated earlier)
