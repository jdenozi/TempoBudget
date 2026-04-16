-- Add company info fields to pro_profiles
ALTER TABLE pro_profiles ADD COLUMN company_name TEXT;
ALTER TABLE pro_profiles ADD COLUMN company_address TEXT;
ALTER TABLE pro_profiles ADD COLUMN company_email TEXT;
ALTER TABLE pro_profiles ADD COLUMN company_phone TEXT;
