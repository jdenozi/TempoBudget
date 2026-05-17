-- ACRE support: 50% reduction on cotisations for first year
ALTER TABLE pro_profiles ADD COLUMN acre_enabled INTEGER DEFAULT 0;
ALTER TABLE pro_profiles ADD COLUMN acre_start_date TEXT;
