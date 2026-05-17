-- Migration: add email_sent_at to pro_invoices
-- Track when an invoice was sent via email to the client

ALTER TABLE pro_invoices ADD COLUMN email_sent_at TEXT;
