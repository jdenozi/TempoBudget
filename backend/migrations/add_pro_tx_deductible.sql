-- Migration: Add is_deductible flag on pro_transactions, used by non-micro regimes
-- to exclude non tax-deductible expenses from the bénéfice calculation.
-- Default = 1 (deductible) so existing rows are unchanged.

ALTER TABLE pro_transactions ADD COLUMN is_deductible INTEGER NOT NULL DEFAULT 1;
