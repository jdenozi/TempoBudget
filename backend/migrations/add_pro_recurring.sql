-- Migration: Add Pro recurring transactions (subscriptions, etc.)

CREATE TABLE IF NOT EXISTS pro_recurring_transactions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    client_id TEXT,
    category_id TEXT NOT NULL,
    title TEXT NOT NULL,
    amount REAL NOT NULL,
    transaction_type TEXT NOT NULL,
    frequency TEXT NOT NULL,
    day INTEGER,
    payment_method TEXT DEFAULT 'cash',
    comment TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (client_id) REFERENCES pro_clients(id) ON DELETE SET NULL,
    FOREIGN KEY (category_id) REFERENCES pro_categories(id)
);

CREATE INDEX IF NOT EXISTS idx_pro_recurring_user ON pro_recurring_transactions(user_id, active);
CREATE INDEX IF NOT EXISTS idx_pro_recurring_client ON pro_recurring_transactions(client_id);
