-- Add share percentage to project members for expense splitting
ALTER TABLE project_members ADD COLUMN share REAL NOT NULL DEFAULT 50.0;
