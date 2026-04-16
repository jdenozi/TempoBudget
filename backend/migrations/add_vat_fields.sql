-- Add VAT fields to pro_profiles
ALTER TABLE pro_profiles ADD COLUMN is_subject_to_vat INTEGER NOT NULL DEFAULT 0;
ALTER TABLE pro_profiles ADD COLUMN vat_rate REAL NOT NULL DEFAULT 20.0;
ALTER TABLE pro_profiles ADD COLUMN vat_number TEXT;

-- Add TVA fields to pro_invoices
ALTER TABLE pro_invoices ADD COLUMN tva_rate REAL NOT NULL DEFAULT 0;
ALTER TABLE pro_invoices ADD COLUMN tva_amount REAL NOT NULL DEFAULT 0;

-- Add TVA fields to pro_quotes
ALTER TABLE pro_quotes ADD COLUMN tva_rate REAL NOT NULL DEFAULT 0;
ALTER TABLE pro_quotes ADD COLUMN tva_amount REAL NOT NULL DEFAULT 0;
