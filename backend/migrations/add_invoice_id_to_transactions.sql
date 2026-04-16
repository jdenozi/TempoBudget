-- Link pro_transactions to pro_invoices
ALTER TABLE pro_transactions ADD COLUMN invoice_id TEXT REFERENCES pro_invoices(id) ON DELETE SET NULL;
