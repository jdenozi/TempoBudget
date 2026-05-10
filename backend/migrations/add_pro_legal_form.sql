-- Migration: Add legal form + tax-related fields for multi-regime support.
-- Default values keep existing micro-entrepreneur behaviour intact.

ALTER TABLE pro_profiles ADD COLUMN legal_form TEXT NOT NULL DEFAULT 'micro';
ALTER TABLE pro_profiles ADD COLUMN cfp_rate REAL;
ALTER TABLE pro_profiles ADD COLUMN versement_liberatoire_enabled INTEGER NOT NULL DEFAULT 0;
ALTER TABLE pro_profiles ADD COLUMN versement_liberatoire_rate REAL;
ALTER TABLE pro_profiles ADD COLUMN ir_abattement_rate REAL;
ALTER TABLE pro_profiles ADD COLUMN foyer_tmi REAL;
