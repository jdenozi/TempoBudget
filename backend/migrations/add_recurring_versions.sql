-- Migration: Add recurring_transaction_versions table
-- Date: 2024
-- Description: Adds version history support for recurring transactions

-- Create the versions table
CREATE TABLE IF NOT EXISTS recurring_transaction_versions (
    id TEXT PRIMARY KEY,
    recurring_transaction_id TEXT NOT NULL,
    title TEXT NOT NULL,
    amount REAL NOT NULL,
    category_id TEXT NOT NULL,
    frequency TEXT NOT NULL,
    day INTEGER,
    effective_from TEXT NOT NULL,
    effective_until TEXT,
    created_at TEXT NOT NULL,
    change_reason TEXT,
    FOREIGN KEY (recurring_transaction_id) REFERENCES recurring_transactions(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- Create indexes for efficient lookups
CREATE INDEX IF NOT EXISTS idx_recurring_versions_lookup
    ON recurring_transaction_versions(recurring_transaction_id, effective_from);
CREATE INDEX IF NOT EXISTS idx_recurring_versions_active
    ON recurring_transaction_versions(recurring_transaction_id, effective_until);

-- Migrate existing recurring transactions to have an initial version
-- This creates a version record for each existing recurring transaction
INSERT INTO recurring_transaction_versions (
    id, recurring_transaction_id, title, amount, category_id,
    frequency, day, effective_from, effective_until, created_at
)
SELECT
    lower(hex(randomblob(16))),
    id,
    title,
    amount,
    category_id,
    frequency,
    day,
    date(created_at),
    NULL,
    datetime('now')
FROM recurring_transactions
WHERE id NOT IN (
    SELECT recurring_transaction_id FROM recurring_transaction_versions
);
