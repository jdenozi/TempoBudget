#!/usr/bin/env python3
"""
Script to import bank transactions from output file into the database.
Supports two bank statement formats.
Usage: python import_transactions.py
"""

import sqlite3
import uuid
from datetime import datetime
import re

# Database path
DB_PATH = "backend/budget.db"

# Budget ID for couple budget
BUDGET_ID = "couple-budget-001"

# User ID who paid for these transactions
# Julien: 02e723e8-918b-4355-a6f2-625b1c68d504
# Julie: 235d9fb6-954b-4939-92b2-f1813bedfee1
PAID_BY_USER_ID = "02e723e8-918b-4355-a6f2-625b1c68d504"  # Julien

# Category mapping from bank categories to budget categories
CATEGORY_MAPPING = {
    # Format 1 categories (Boursorama style)
    "Alimentation": "cat-couple-007",
    "Entretien - réparation": "cat-couple-008",  # Garage
    "Restaurants, bars, discothèques…": "cat-couple-015",  # Sortie couple
    "Mobilier, électroménager, décoration…": "cat-couple-014",  # Equipement de la maison
    "Equipements sportifs et artistiques": "cat-couple-014",  # Equipement de la maison
    "Emprunt immobilier": "cat-couple-001",  # Loyer (for mortgage payments)
    "Retraits cash": None,  # Skip
    "Virements reçus": "INCOME",  # Special marker for income
    "Remboursements": "INCOME",  # Income
    "Vêtements et accessoires": None,  # Skip - not in budget
    "Multimedia à domicile (tv, internet, téléphonie…)": "cat-couple-004",  # Internet
    "Téléphonie (fixe et mobile)": "cat-couple-004",  # Internet (telecom)
    "Frais bancaires et de gestion (dont agios)": None,  # Skip
    "Non catégorisé": None,  # Skip
    "Virements émis": None,  # Skip - outgoing transfers

    # Format 2 categories (Société Générale style)
    "Vie quotidienne": None,  # Skip - Amazon, OVH etc (personal)
    "Loisirs": None,  # Skip - VIR INSTANTANE EMIS (transfers to Julie's account)
    "Services financiers / professionnels": None,  # Skip - bank fees
    "Dépots (cartes/chèques/espèces)": "INCOME",  # Deposits = income
    "Emprunts (hors immobilier)": None,  # Skip - personal loan
    "Auto et Moto": "cat-couple-008",  # Garage - car insurance
    "Logement": "cat-couple-001",  # Loyer
    "Dépenses d'épargne": None,  # Skip - savings/insurance
}

# French months
MONTHS_FR = {
    'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4,
    'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8,
    'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12
}

# Format 2 category list (only unique to Format 2 - NOT shared with Format 1)
FORMAT2_CATEGORIES = [
    'Vie quotidienne', 'Loisirs', 'Services financiers / professionnels',
    'Dépots (cartes/chèques/espèces)', 'Emprunts (hors immobilier)',
    'Auto et Moto', 'Logement', "Dépenses d'épargne"
]

# All Format 2 categories (for parsing)
ALL_FORMAT2_CATEGORIES = FORMAT2_CATEGORIES + ['Virements reçus']


def clean_line(line):
    """Remove line number prefix if present."""
    if '→' in line:
        return line.split('→', 1)[1]
    return line


def parse_date_full(date_str):
    """Parse French date string (with day name) to ISO format."""
    match = re.match(
        r'^(lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)\s+(\d+)\s+(\w+)\s+(\d{4})$',
        date_str.strip(),
        re.IGNORECASE
    )
    if match:
        day = int(match.group(2))
        month_name = match.group(3).lower()
        year = int(match.group(4))
        month = MONTHS_FR.get(month_name, 1)
        return f"{year}-{month:02d}-{day:02d}"
    return None


def parse_amount_format1(amount_str):
    """Parse Format 1 amount: '− 224,72 €' or '1 500,00 €'"""
    is_negative = '−' in amount_str
    clean = amount_str.replace('€', '').replace('−', '').replace(' ', '').replace('\xa0', '').replace(',', '.')
    try:
        amount = float(clean)
        return -amount if is_negative else amount
    except ValueError:
        return None


def parse_amount_format2(amount_str):
    """Parse Format 2 amount: 'moins 6,99 €- 6,99 €' or '600,00 €600,00 €'"""
    is_negative = 'moins' in amount_str.lower()
    # Take only the first amount (before duplication)
    clean = amount_str.replace('moins', '').replace('€', '').replace(' ', '').replace('\xa0', '').replace(',', '.').replace('-', '')
    # Handle duplicated amounts
    if clean.count('.') >= 2:
        parts = clean.split('.')
        clean = parts[0] + '.' + parts[1]
    try:
        amount = float(clean)
        return -amount if is_negative else amount
    except ValueError:
        return None


def parse_format1(lines):
    """Parse Format 1 (Boursorama): date → description → category → amount"""
    transactions = []
    current_date = None
    i = 0

    while i < len(lines):
        line = clean_line(lines[i].strip())

        if not line:
            i += 1
            continue

        # Check if we've hit Format 2 section
        if line in FORMAT2_CATEGORIES:
            break

        # Check for date
        date = parse_date_full(line)
        if date:
            current_date = date
            i += 1
            continue

        # Parse transaction if we have a date
        if current_date:
            description = line

            # Get next line
            i += 1
            if i >= len(lines):
                break
            next_line = clean_line(lines[i].strip())

            # Check for description continuation
            if next_line.startswith('Autorisation') or next_line.startswith('ECH PRET'):
                description += " " + next_line
                i += 1
                if i >= len(lines):
                    break
                next_line = clean_line(lines[i].strip())

            category = next_line

            # Get amount
            i += 1
            if i >= len(lines):
                break
            amount_line = clean_line(lines[i].strip())
            amount = parse_amount_format1(amount_line)

            if amount is not None:
                transactions.append({
                    'date': current_date,
                    'description': description,
                    'category': category,
                    'amount': amount
                })

        i += 1

    return transactions, i


def parse_format2(lines, start_idx):
    """Parse Format 2 (SG): category → description (multiline) → amount → 'Non pointée' → date"""
    transactions = []
    i = start_idx
    pending_tx = None  # Transaction waiting for a date

    while i < len(lines):
        line = clean_line(lines[i].strip())

        if not line:
            i += 1
            continue

        # Check for date line - this completes the pending transaction
        date = parse_date_full(line)
        if date:
            if pending_tx:
                pending_tx['date'] = date
                transactions.append(pending_tx)
                pending_tx = None
            i += 1
            continue

        # Check for category line - start new transaction
        if line in ALL_FORMAT2_CATEGORIES:
            category = line

            # Collect description lines until we hit amount
            description_parts = []
            i += 1
            while i < len(lines):
                desc_line = clean_line(lines[i].strip())

                # Check if this is an amount line
                if '€' in desc_line and ('moins' in desc_line.lower() or desc_line[0].isdigit()):
                    amount = parse_amount_format2(desc_line)
                    break

                if desc_line and desc_line != 'Non pointée':
                    description_parts.append(desc_line)
                i += 1

            if i >= len(lines):
                break

            description = ' '.join(description_parts)[:200]

            # Skip 'Non pointée' if present
            i += 1
            if i < len(lines):
                check = clean_line(lines[i].strip())
                if check == 'Non pointée':
                    i += 1

            # Store pending transaction (waiting for date)
            if amount is not None:
                pending_tx = {
                    'description': description,
                    'category': category,
                    'amount': amount
                }
            continue

        i += 1

    return transactions


def parse_transactions(filepath):
    """Parse the output file and extract transactions from both formats."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Parse Format 1
    transactions1, end_idx = parse_format1(lines)
    print(f"Format 1 (Boursorama): {len(transactions1)} transactions")

    # Parse Format 2
    transactions2 = parse_format2(lines, end_idx)
    print(f"Format 2 (SG): {len(transactions2)} transactions")

    return transactions1 + transactions2


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Verify budget exists
    cursor.execute("SELECT id FROM budgets WHERE id = ?", (BUDGET_ID,))
    if not cursor.fetchone():
        print(f"Budget {BUDGET_ID} not found!")
        return
    print(f"Using paid_by_user_id: {PAID_BY_USER_ID}")

    # Create/get income category
    cursor.execute("SELECT id FROM categories WHERE budget_id = ? AND name = 'Revenus'", (BUDGET_ID,))
    income_cat = cursor.fetchone()
    if not income_cat:
        income_cat_id = "cat-couple-revenus"
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO categories (id, budget_id, name, amount, parent_id, tags, created_at)
            VALUES (?, ?, 'Revenus', 0, NULL, '["revenu"]', ?)
        """, (income_cat_id, BUDGET_ID, now))
        print(f"Created income category: {income_cat_id}")
    else:
        income_cat_id = income_cat[0]
        print(f"Using existing income category: {income_cat_id}")

    # Update category mapping for income
    CATEGORY_MAPPING["Virements reçus"] = income_cat_id
    CATEGORY_MAPPING["Remboursements"] = income_cat_id
    CATEGORY_MAPPING["Dépots (cartes/chèques/espèces)"] = income_cat_id

    # Parse transactions
    transactions = parse_transactions("output")
    print(f"\nTotal: {len(transactions)} transactions")

    # Filter to January 2026
    january_transactions = [t for t in transactions if t.get('date', '').startswith('2026-01')]
    print(f"January 2026: {len(january_transactions)} transactions")

    # Get existing transactions to avoid duplicates
    cursor.execute("""
        SELECT title, date, amount FROM transactions
        WHERE budget_id = ? AND date LIKE '2026-01%'
    """, (BUDGET_ID,))
    existing = set()
    for row in cursor.fetchall():
        existing.add((row[0][:50], row[1], round(row[2], 2)))

    # Insert transactions
    inserted = 0
    skipped_no_cat = 0
    skipped_dup = 0

    for tx in january_transactions:
        category_id = CATEGORY_MAPPING.get(tx['category'])

        if category_id is None:
            print(f"  [SKIP] {tx['date']} | {tx['description'][:35]:<35} | {tx['category']}")
            skipped_no_cat += 1
            continue

        # Determine type
        if tx['amount'] >= 0:
            tx_type = 'income'
            amount = abs(tx['amount'])
        else:
            tx_type = 'expense'
            amount = abs(tx['amount'])

        # Check duplicate
        key = (tx['description'][:50], tx['date'], round(amount, 2))
        if key in existing:
            print(f"  [DUP]  {tx['date']} | {tx['description'][:35]:<35} | {amount:.2f}€")
            skipped_dup += 1
            continue

        # Insert
        tx_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO transactions (id, budget_id, category_id, title, amount, date, transaction_type, is_recurring, created_at, paid_by_user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
        """, (tx_id, BUDGET_ID, category_id, tx['description'], amount, tx['date'], tx_type, now, PAID_BY_USER_ID))

        existing.add(key)
        print(f"  [OK]   {tx['date']} | {tx['description'][:35]:<35} | {amount:.2f}€ ({tx_type})")
        inserted += 1

    conn.commit()
    conn.close()

    print(f"\n{'='*60}")
    print(f"✓ Inserted: {inserted}")
    print(f"✗ Skipped (no category): {skipped_no_cat}")
    print(f"✗ Skipped (duplicate): {skipped_dup}")


if __name__ == "__main__":
    main()
