-- Stripe webhook events idempotence table
-- Prevents duplicate processing of the same webhook event

CREATE TABLE IF NOT EXISTS stripe_webhook_events (
    id TEXT PRIMARY KEY,
    stripe_event_id TEXT NOT NULL UNIQUE,
    event_type TEXT NOT NULL,
    processed_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_stripe_webhook_events_stripe_event_id
    ON stripe_webhook_events(stripe_event_id);
