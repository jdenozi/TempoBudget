-- Migration: Add Factur-X compliance fields to pro_clients and pro_profiles

-- Client fields for B2B e-invoicing
ALTER TABLE pro_clients ADD COLUMN siren TEXT;
ALTER TABLE pro_clients ADD COLUMN siret TEXT;
ALTER TABLE pro_clients ADD COLUMN vat_number TEXT;
ALTER TABLE pro_clients ADD COLUMN street TEXT;
ALTER TABLE pro_clients ADD COLUMN postal_code TEXT;
ALTER TABLE pro_clients ADD COLUMN city TEXT;
ALTER TABLE pro_clients ADD COLUMN country TEXT DEFAULT 'FR';
ALTER TABLE pro_clients ADD COLUMN is_professional INTEGER DEFAULT 1;

-- Seller fields for complete Factur-X compliance
ALTER TABLE pro_profiles ADD COLUMN vat_number TEXT;
ALTER TABLE pro_profiles ADD COLUMN street TEXT;
ALTER TABLE pro_profiles ADD COLUMN postal_code TEXT;
ALTER TABLE pro_profiles ADD COLUMN city TEXT;
ALTER TABLE pro_profiles ADD COLUMN country TEXT DEFAULT 'FR';
ALTER TABLE pro_profiles ADD COLUMN legal_form TEXT;
ALTER TABLE pro_profiles ADD COLUMN company_name TEXT;

-- Index for SIREN lookups
CREATE INDEX IF NOT EXISTS idx_pro_clients_siren ON pro_clients(siren);
