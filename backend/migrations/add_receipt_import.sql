-- Receipt import feature: add import_status and receipt_image_path to transactions
ALTER TABLE transactions ADD COLUMN import_status TEXT CHECK(import_status IN (NULL, 'pending', 'confirmed'));
ALTER TABLE transactions ADD COLUMN receipt_image_path TEXT;
CREATE INDEX IF NOT EXISTS idx_transactions_import_status ON transactions(budget_id, import_status);
