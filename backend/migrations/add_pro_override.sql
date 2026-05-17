-- Allow admin to manually grant Pro access to users
ALTER TABLE users ADD COLUMN pro_override INTEGER NOT NULL DEFAULT 0;
