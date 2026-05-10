-- Migration: User-defined revenue limits/thresholds (e.g. CAF prime d'activité,
-- micro-entrepreneur ceiling, AAH limits, custom personal goals).

CREATE TABLE IF NOT EXISTS pro_thresholds (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    period TEXT NOT NULL,
    amount REAL NOT NULL,
    color TEXT DEFAULT '#f0a020',
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_pro_thresholds_user ON pro_thresholds(user_id, active);
