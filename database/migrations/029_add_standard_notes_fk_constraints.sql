-- Migration 029: Add Foreign Key Constraints to Standard Notes

-- Add category_id column
ALTER TABLE standard_notes
ADD COLUMN IF NOT EXISTS category_id INTEGER;

-- Add discipline_id column
ALTER TABLE standard_notes
ADD COLUMN IF NOT EXISTS discipline_id INTEGER;

-- Add foreign key constraints
ALTER TABLE standard_notes
ADD CONSTRAINT fk_standard_notes_category
FOREIGN KEY (category_id) REFERENCES category_codes(category_id)
ON DELETE SET NULL
ON UPDATE CASCADE;

ALTER TABLE standard_notes
ADD CONSTRAINT fk_standard_notes_discipline
FOREIGN KEY (discipline_id) REFERENCES discipline_codes(discipline_id)
ON DELETE SET NULL
ON UPDATE CASCADE;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_standard_notes_category_id ON standard_notes(category_id);
CREATE INDEX IF NOT EXISTS idx_standard_notes_discipline_id ON standard_notes(discipline_id);

-- Note: Manual data migration required to populate category_id and discipline_id
-- from existing note_category and discipline VARCHAR columns
