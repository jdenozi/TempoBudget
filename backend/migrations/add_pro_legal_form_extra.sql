-- Migration: Additional fields for non-micro regimes (EI au réel, EURL, SASU, SAS).

ALTER TABLE pro_profiles ADD COLUMN tns_cotisations_rate REAL DEFAULT 45.0;
ALTER TABLE pro_profiles ADD COLUMN salary_gross_monthly REAL DEFAULT 0;
ALTER TABLE pro_profiles ADD COLUMN dividends_yearly REAL DEFAULT 0;
ALTER TABLE pro_profiles ADD COLUMN eurl_tax_option TEXT DEFAULT 'ir';
