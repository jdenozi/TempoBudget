-- Migration: Add pro discounts, coupons, and gift cards
-- Date: 2026-03-08

-- New columns on pro_transactions
ALTER TABLE pro_transactions ADD COLUMN discount_type TEXT;
ALTER TABLE pro_transactions ADD COLUMN discount_value REAL;
ALTER TABLE pro_transactions ADD COLUMN coupon_id TEXT REFERENCES pro_coupons(id);
ALTER TABLE pro_transactions ADD COLUMN gift_card_payment REAL DEFAULT 0;

-- Pro Coupons
CREATE TABLE IF NOT EXISTS pro_coupons (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    discount_type TEXT NOT NULL DEFAULT 'percentage',
    discount_value REAL NOT NULL DEFAULT 0,
    valid_from TEXT,
    valid_until TEXT,
    max_uses INTEGER DEFAULT 0,
    used_count INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_pro_coupons_user ON pro_coupons(user_id);
CREATE INDEX IF NOT EXISTS idx_pro_coupons_code ON pro_coupons(user_id, code);

-- Pro Gift Cards
CREATE TABLE IF NOT EXISTS pro_gift_cards (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    code TEXT NOT NULL,
    initial_amount REAL NOT NULL,
    remaining_balance REAL NOT NULL,
    client_id TEXT,
    purchase_transaction_id TEXT,
    purchase_date TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (client_id) REFERENCES pro_clients(id) ON DELETE SET NULL,
    FOREIGN KEY (purchase_transaction_id) REFERENCES pro_transactions(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_pro_gift_cards_user ON pro_gift_cards(user_id);

-- Pro Gift Card Usages
CREATE TABLE IF NOT EXISTS pro_gift_card_usages (
    id TEXT PRIMARY KEY,
    gift_card_id TEXT NOT NULL,
    transaction_id TEXT NOT NULL,
    amount_used REAL NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (gift_card_id) REFERENCES pro_gift_cards(id) ON DELETE CASCADE,
    FOREIGN KEY (transaction_id) REFERENCES pro_transactions(id) ON DELETE CASCADE
);
