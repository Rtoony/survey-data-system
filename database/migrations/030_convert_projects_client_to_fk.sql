-- Migration 030: Convert Projects Client Name to Foreign Key

-- Add client_id column
ALTER TABLE projects
ADD COLUMN IF NOT EXISTS client_id INTEGER;

-- Add foreign key constraint
ALTER TABLE projects
ADD CONSTRAINT fk_projects_client
FOREIGN KEY (client_id) REFERENCES clients(client_id)
ON DELETE SET NULL
ON UPDATE CASCADE;

-- Create index
CREATE INDEX IF NOT EXISTS idx_projects_client_id ON projects(client_id);

-- Note: Manual data migration required to map client_name to client_id
-- After migration is complete, client_name column can be dropped
