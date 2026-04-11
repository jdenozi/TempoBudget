-- Pro Invoice Settings
CREATE TABLE IF NOT EXISTS pro_invoice_settings (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,
    invoice_prefix TEXT NOT NULL DEFAULT 'F',
    quote_prefix TEXT NOT NULL DEFAULT 'D',
    next_invoice_number INTEGER NOT NULL DEFAULT 1,
    next_quote_number INTEGER NOT NULL DEFAULT 1,
    payment_terms_days INTEGER NOT NULL DEFAULT 30,
    late_penalty_rate REAL NOT NULL DEFAULT 3.0,
    bank_name TEXT,
    bank_iban TEXT,
    bank_bic TEXT,
    default_notes TEXT,
    logo_path TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Pro Invoices
CREATE TABLE IF NOT EXISTS pro_invoices (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    client_id TEXT NOT NULL,
    invoice_number TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft', 'sent', 'paid', 'cancelled')),
    issue_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    subtotal REAL NOT NULL DEFAULT 0,
    total REAL NOT NULL DEFAULT 0,
    discount_type TEXT CHECK(discount_type IN ('percentage', 'fixed')),
    discount_value REAL DEFAULT 0,
    notes TEXT,
    payment_method TEXT,
    paid_date TEXT,
    quote_id TEXT,
    reminder_sent_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (client_id) REFERENCES pro_clients(id),
    FOREIGN KEY (quote_id) REFERENCES pro_quotes(id) ON DELETE SET NULL,
    UNIQUE(user_id, invoice_number)
);

CREATE INDEX IF NOT EXISTS idx_pro_invoices_user ON pro_invoices(user_id, status);
CREATE INDEX IF NOT EXISTS idx_pro_invoices_client ON pro_invoices(client_id);

-- Pro Invoice Items
CREATE TABLE IF NOT EXISTS pro_invoice_items (
    id TEXT PRIMARY KEY,
    invoice_id TEXT NOT NULL,
    product_id TEXT,
    description TEXT NOT NULL,
    quantity REAL NOT NULL DEFAULT 1,
    unit_price REAL NOT NULL DEFAULT 0,
    total REAL NOT NULL DEFAULT 0,
    sort_order INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (invoice_id) REFERENCES pro_invoices(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES pro_products(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_pro_invoice_items ON pro_invoice_items(invoice_id);

-- Pro Quotes
CREATE TABLE IF NOT EXISTS pro_quotes (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    client_id TEXT NOT NULL,
    quote_number TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft', 'sent', 'accepted', 'rejected', 'expired')),
    issue_date TEXT NOT NULL,
    validity_date TEXT NOT NULL,
    subtotal REAL NOT NULL DEFAULT 0,
    total REAL NOT NULL DEFAULT 0,
    discount_type TEXT CHECK(discount_type IN ('percentage', 'fixed')),
    discount_value REAL DEFAULT 0,
    notes TEXT,
    invoice_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (client_id) REFERENCES pro_clients(id),
    FOREIGN KEY (invoice_id) REFERENCES pro_invoices(id) ON DELETE SET NULL,
    UNIQUE(user_id, quote_number)
);

CREATE INDEX IF NOT EXISTS idx_pro_quotes_user ON pro_quotes(user_id, status);
CREATE INDEX IF NOT EXISTS idx_pro_quotes_client ON pro_quotes(client_id);

-- Pro Quote Items
CREATE TABLE IF NOT EXISTS pro_quote_items (
    id TEXT PRIMARY KEY,
    quote_id TEXT NOT NULL,
    product_id TEXT,
    description TEXT NOT NULL,
    quantity REAL NOT NULL DEFAULT 1,
    unit_price REAL NOT NULL DEFAULT 0,
    total REAL NOT NULL DEFAULT 0,
    sort_order INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (quote_id) REFERENCES pro_quotes(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES pro_products(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_pro_quote_items ON pro_quote_items(quote_id);
