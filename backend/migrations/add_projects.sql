-- Migration: Add project_category_id to transactions and pro_transactions
ALTER TABLE transactions ADD COLUMN project_category_id TEXT REFERENCES project_categories(id) ON DELETE SET NULL;
ALTER TABLE pro_transactions ADD COLUMN project_category_id TEXT REFERENCES project_categories(id) ON DELETE SET NULL;
