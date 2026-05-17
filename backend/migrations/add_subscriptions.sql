-- Add is_admin column to users
ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0;

-- Stripe customer mapping
CREATE TABLE IF NOT EXISTS stripe_customers (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,
    stripe_customer_id TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Subscriptions
CREATE TABLE IF NOT EXISTS subscriptions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    stripe_subscription_id TEXT UNIQUE,
    stripe_price_id TEXT NOT NULL,
    plan_type TEXT NOT NULL CHECK(plan_type IN ('monthly', 'annual')),
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'past_due', 'canceled', 'incomplete', 'trialing')),
    current_period_start TEXT NOT NULL,
    current_period_end TEXT NOT NULL,
    cancel_at_period_end INTEGER NOT NULL DEFAULT 0,
    canceled_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Admin quotes for prospects
CREATE TABLE IF NOT EXISTS admin_quotes (
    id TEXT PRIMARY KEY,
    created_by_user_id TEXT NOT NULL,
    prospect_name TEXT NOT NULL,
    prospect_email TEXT NOT NULL,
    prospect_company TEXT,
    plan_type TEXT NOT NULL CHECK(plan_type IN ('monthly', 'annual')),
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price REAL NOT NULL,
    total REAL NOT NULL,
    valid_until TEXT NOT NULL,
    notes TEXT,
    status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft', 'sent', 'accepted', 'expired')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_stripe_customers_user_id ON stripe_customers(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_admin_quotes_status ON admin_quotes(status);
