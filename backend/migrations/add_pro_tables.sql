-- Migration: Add Pro (auto-entrepreneur) tables

CREATE TABLE IF NOT EXISTS pro_profiles (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,
    siret TEXT,
    activity_type TEXT DEFAULT 'services',
    cotisation_rate REAL DEFAULT 21.1,
    declaration_frequency TEXT DEFAULT 'quarterly',
    revenue_threshold REAL DEFAULT 77700,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS pro_clients (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    address TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS pro_categories (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'expense',
    is_default INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS pro_transactions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    client_id TEXT,
    category_id TEXT NOT NULL,
    title TEXT NOT NULL,
    amount REAL NOT NULL,
    transaction_type TEXT NOT NULL,
    date TEXT NOT NULL,
    payment_method TEXT DEFAULT 'cash',
    comment TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (client_id) REFERENCES pro_clients(id) ON DELETE SET NULL,
    FOREIGN KEY (category_id) REFERENCES pro_categories(id)
);

CREATE INDEX IF NOT EXISTS idx_pro_transactions_user ON pro_transactions(user_id, date);
CREATE INDEX IF NOT EXISTS idx_pro_transactions_client ON pro_transactions(client_id);
