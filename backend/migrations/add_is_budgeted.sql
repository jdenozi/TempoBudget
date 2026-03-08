-- Add is_budgeted column to transactions table
-- 1 = budgeted (default), 0 = exceptional (excluded from budget calculations)
ALTER TABLE transactions ADD COLUMN is_budgeted INTEGER NOT NULL DEFAULT 1;
