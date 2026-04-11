-- Users
CREATE TABLE IF NOT EXISTS users (
                                     id TEXT PRIMARY KEY,
                                     email TEXT NOT NULL UNIQUE,
                                     name TEXT NOT NULL,
                                     password_hash TEXT NOT NULL,
                                     avatar TEXT,
                                     phone TEXT,
                                     created_at TEXT NOT NULL,
                                     updated_at TEXT NOT NULL
);

-- Budgets
CREATE TABLE IF NOT EXISTS budgets (
                                       id TEXT PRIMARY KEY,
                                       user_id TEXT NOT NULL,
                                       name TEXT NOT NULL,
                                       budget_type TEXT NOT NULL,
                                       is_active INTEGER NOT NULL DEFAULT 0,
                                       created_at TEXT NOT NULL,
                                       updated_at TEXT NOT NULL,
                                       FOREIGN KEY (user_id) REFERENCES users(id)
    );

-- Categories
CREATE TABLE IF NOT EXISTS categories (
                                          id TEXT PRIMARY KEY,
                                          budget_id TEXT NOT NULL,
                                          parent_id TEXT,
                                          name TEXT NOT NULL,
                                          amount REAL NOT NULL,
                                          tags TEXT,
                                          created_at TEXT NOT NULL,
                                          FOREIGN KEY (budget_id) REFERENCES budgets(id),
                                          FOREIGN KEY (parent_id) REFERENCES categories(id)
    );

-- Transactions
CREATE TABLE IF NOT EXISTS transactions (
                                            id TEXT PRIMARY KEY,
                                            budget_id TEXT NOT NULL,
                                            category_id TEXT NOT NULL,
                                            title TEXT NOT NULL,
                                            amount REAL NOT NULL,
                                            transaction_type TEXT NOT NULL,
                                            date TEXT NOT NULL,
                                            comment TEXT,
                                            is_recurring INTEGER NOT NULL DEFAULT 0,
                                            is_budgeted INTEGER NOT NULL DEFAULT 1,
                                            paid_by_user_id TEXT,
                                            created_at TEXT NOT NULL,
                                            FOREIGN KEY (budget_id) REFERENCES budgets(id),
    FOREIGN KEY (category_id) REFERENCES categories(id),
    FOREIGN KEY (paid_by_user_id) REFERENCES users(id)
    );

-- Recurring Transactions
CREATE TABLE IF NOT EXISTS recurring_transactions (
                                                      id TEXT PRIMARY KEY,
                                                      budget_id TEXT NOT NULL,
                                                      category_id TEXT NOT NULL,
                                                      title TEXT NOT NULL,
                                                      amount REAL NOT NULL,
                                                      transaction_type TEXT NOT NULL,
                                                      frequency TEXT NOT NULL,
                                                      day INTEGER,
                                                      active INTEGER NOT NULL DEFAULT 1,
                                                      created_at TEXT NOT NULL,
                                                      FOREIGN KEY (budget_id) REFERENCES budgets(id),
    FOREIGN KEY (category_id) REFERENCES categories(id)
    );

-- Recurring Transaction Versions (historique des modifications avec dates d'effet)
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

CREATE INDEX IF NOT EXISTS idx_recurring_versions_lookup
    ON recurring_transaction_versions(recurring_transaction_id, effective_from);
CREATE INDEX IF NOT EXISTS idx_recurring_versions_active
    ON recurring_transaction_versions(recurring_transaction_id, effective_until);


-- Budget Profiles
CREATE TABLE IF NOT EXISTS budget_profiles (
                                               id TEXT PRIMARY KEY,
                                               user_id TEXT NOT NULL,
                                               name TEXT NOT NULL,
                                               created_at TEXT NOT NULL,
                                               FOREIGN KEY (user_id) REFERENCES users(id)
    );

-- Budget Profile Categories
CREATE TABLE IF NOT EXISTS budget_profile_categories (
                                                         id TEXT PRIMARY KEY,
                                                         profile_id TEXT NOT NULL,
                                                         name TEXT NOT NULL,
                                                         amount REAL NOT NULL,
                                                         FOREIGN KEY (profile_id) REFERENCES budget_profiles(id)
    );

-- Budget Members (pour les budgets de groupe)
CREATE TABLE IF NOT EXISTS budget_members (
                                              id TEXT PRIMARY KEY,
                                              budget_id TEXT NOT NULL,
                                              user_id TEXT NOT NULL,
                                              role TEXT NOT NULL CHECK(role IN ('owner', 'member')),
    share REAL NOT NULL DEFAULT 50.0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (budget_id) REFERENCES budgets(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(budget_id, user_id)
    );

-- Budget Invitations
CREATE TABLE IF NOT EXISTS budget_invitations (
                                                  id TEXT PRIMARY KEY,
                                                  budget_id TEXT NOT NULL,
                                                  inviter_id TEXT NOT NULL,
                                                  invitee_email TEXT NOT NULL,
                                                  role TEXT NOT NULL CHECK(role IN ('owner', 'member')),
    status TEXT NOT NULL CHECK(status IN ('pending', 'accepted', 'rejected')) DEFAULT 'pending',
    created_at TEXT NOT NULL,
    FOREIGN KEY (budget_id) REFERENCES budgets(id) ON DELETE CASCADE,
    FOREIGN KEY (inviter_id) REFERENCES users(id) ON DELETE CASCADE
    );

CREATE INDEX IF NOT EXISTS idx_invitations_email ON budget_invitations(invitee_email);
CREATE INDEX IF NOT EXISTS idx_invitations_status ON budget_invitations(status);

-- Loans
CREATE TABLE IF NOT EXISTS loans (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    person_name TEXT NOT NULL,
    amount REAL NOT NULL,
    direction TEXT NOT NULL CHECK(direction IN ('lent', 'borrowed')),
    date TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'repaid')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Loan Repayments
CREATE TABLE IF NOT EXISTS loan_repayments (
    id TEXT PRIMARY KEY,
    loan_id TEXT NOT NULL,
    amount REAL NOT NULL,
    date TEXT NOT NULL,
    comment TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (loan_id) REFERENCES loans(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_loans_user ON loans(user_id);
CREATE INDEX IF NOT EXISTS idx_loan_repayments_loan ON loan_repayments(loan_id);

-- Pro Profiles (auto-entrepreneur)
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

-- Pro Clients
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

-- Pro Categories
CREATE TABLE IF NOT EXISTS pro_categories (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'expense',
    is_default INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Pro Transactions
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
    is_declared INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (client_id) REFERENCES pro_clients(id) ON DELETE SET NULL,
    FOREIGN KEY (category_id) REFERENCES pro_categories(id)
);

CREATE INDEX IF NOT EXISTS idx_pro_transactions_user ON pro_transactions(user_id, date);
CREATE INDEX IF NOT EXISTS idx_pro_transactions_client ON pro_transactions(client_id);
CREATE INDEX IF NOT EXISTS idx_pro_transactions_declared ON pro_transactions(user_id, is_declared, date);

-- Pro Products/Services Catalogue
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

-- Pro Transaction Items (line items)
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