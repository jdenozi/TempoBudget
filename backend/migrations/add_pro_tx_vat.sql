-- Migration: Add vat_rate on pro_transactions for users subject to VAT.
-- NULL = inherit from profile.vat_rate at compute time.

ALTER TABLE pro_transactions ADD COLUMN vat_rate REAL;
