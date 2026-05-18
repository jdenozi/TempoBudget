-- Add trial_ends_at column to users table for automatic 7-day free trial
ALTER TABLE users ADD COLUMN trial_ends_at TEXT;
