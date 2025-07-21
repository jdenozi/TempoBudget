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
                                            created_at TEXT NOT NULL,
                                            FOREIGN KEY (budget_id) REFERENCES budgets(id),
    FOREIGN KEY (category_id) REFERENCES categories(id)
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