-- Migration: Add pro products/services catalogue and transaction items
-- Date: 2026-03-08

CREATE TABLE IF NOT EXISTS pro_products (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'service',
    default_price REAL NOT NULL DEFAULT 0,
    category_id TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES pro_categories(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS pro_transaction_items (
    id TEXT PRIMARY KEY,
    transaction_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price REAL NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (transaction_id) REFERENCES pro_transactions(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES pro_products(id)
);

CREATE INDEX IF NOT EXISTS idx_pro_products_user ON pro_products(user_id);
CREATE INDEX IF NOT EXISTS idx_pro_transaction_items_tx ON pro_transaction_items(transaction_id);
CREATE INDEX IF NOT EXISTS idx_pro_transaction_items_product ON pro_transaction_items(product_id);
