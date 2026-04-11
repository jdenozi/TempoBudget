-- Add is_declared field to pro_transactions for URSSAF declaration tracking
ALTER TABLE pro_transactions ADD COLUMN is_declared INTEGER NOT NULL DEFAULT 0;

-- Index for quick filtering on declaration status
CREATE INDEX IF NOT EXISTS idx_pro_transactions_declared ON pro_transactions(user_id, is_declared, date);
