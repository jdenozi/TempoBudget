#!/usr/bin/env python3
"""
Script to update category amounts from budget files.
Run on the server: python3 scripts/update_category_amounts.py
"""

import sqlite3
import re
import sys

# Budget data - Julie
JULIE_DATA = """
Personnel	7eme tradition	10.00
Personnel	Abonnement Google Drive	2.00
Santé 	Analyses	20.00
Logement	Assurance habitation	5.60
Véhicule	Assurance moto	88.00
Epargne	Assurance vie	100.00
Véhicule	Assurance voiture	45.00
Santé 	Autres soins	10.00
Personnel	Cadeaux	5.00
Véhicule	Carburant auto	30.00
Véhicule	Carburant moto	20.00
Education	Chamane	280.00
Logement	Charges copropriété	19.29
Crédit	Chomage	1636.00
Loisir	Ciné/concerts/spectacles	0.00
Personnel	Coiffeur	5.00
Course	Course	145.55
Course	Décoration	10.92
Personnel	Démarches administratives	5.00
Transport	Déplacement (Paris, formation, ..)	20.00
Logement	Electricité	30.06
Véhicule	Entretien & équipement moto	20.00
Course	Entretien de la maison	18.19
Course	Equipement de la maison	7.28
Sport	Equipement sport	2.00
Loisir	Films (netflix)	0.00
Education	Formation	100.00
Logement	Frais de courtage	2.55
Logement	Garage	32.75
Personnel	Habillement & bijoux	5.00
Logement	Internet	6.55
Personnel	Laser / microblading	5.00
Education	Livres	0.00
Logement	Loyer	282.73
Crédit	Missions	40.00
Transport	Parking / péages	2.00
Personnel	Produits de beauté	5.00
Personnel	Produits d'hygiène	5.00
Loisir	Restaurants 	50.00
Sport	Salle de sport / escalade	25.00
Santé 	Spécialistes	50.00
Loisir	Spotify	0.00
Personnel	Téléphone	10.00
Animaux	Yin	10.00
Sport	Yoga	0.00
Couple	Sortie couple	36.39
Personnel	Tabac	50.00
Santé	Mutuelle	45.00
"""

# Budget data - Julien
JULIEN_DATA = """
Personnel	7eme tradition	5.00
Personnel	Abonnement serveur	29.99
Personnel	Achats divers	50.00
Course	Alimentation	254.45
Assurance	Assurance corporelle	6.88
Assurance	Assurance des accidents de la vie courante	10.14
Logement	Assurance habitation	15.40
Véhicule	Assurance moto	205.71
Véhicule	Assurance voiture	101.30
Personnel	Cadeaux	30.00
Véhicule	Carburant auto	60.00
Véhicule	Carburant moto	60.00
Logement	Charges copropriété	53.00
Loisir	Ciné/concerts/spectacles	50.00
Crédit banque	Crédit étudiant	224.72
Crédit banque	Crédit voiture	182.68
Animaux	Croquette	35.00
Personnel	Démarches administratives	15.00
Logement	Eau	15.58
Logement	Electricité	52.54
Véhicule	Entretien & équipement moto	50.00
Course	Entretien de la maison	31.81
Course	Equipement de la maison	19.08
Logement	Garage	90.00
Logement	Internet	11.45
Education	Livres	30.00
Logement	Loyer	777.00
Transport	Péage	15.00
Assurance	Protection juridique	7.31
Loisir	Restaurants 	63.61
Crédit	Salaire	2730.00
Personnel	Téléphone	9.99
Santé 	Thérapie	50.00
Crédit	Virement Julie	287.84
"""


def parse_budget_data(data: str) -> list[tuple[str, str, float]]:
    """Parse budget data into (parent_category, subcategory, amount) tuples."""
    result = []
    for line in data.strip().split('\n'):
        if not line.strip():
            continue
        parts = line.split('\t')
        if len(parts) >= 3:
            parent = parts[0].strip()
            name = parts[1].strip()
            try:
                amount = float(parts[2].replace(',', '.').replace(' ', '').replace('€', ''))
            except ValueError:
                amount = 0.0
            result.append((parent, name, amount))
    return result


def update_categories(db_path: str, budget_name: str, data: str):
    """Update category amounts for a specific budget."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Find the budget by name (case-insensitive partial match)
    cursor.execute(
        "SELECT id, name FROM budgets WHERE LOWER(name) LIKE ?",
        (f"%{budget_name.lower()}%",)
    )
    budgets = cursor.fetchall()

    if not budgets:
        print(f"No budget found matching '{budget_name}'")
        return

    if len(budgets) > 1:
        print(f"Multiple budgets found matching '{budget_name}':")
        for b in budgets:
            print(f"  - {b[1]} (id: {b[0]})")
        print("Please be more specific.")
        return

    budget_id, budget_full_name = budgets[0]
    print(f"\nUpdating budget: {budget_full_name} (id: {budget_id})")

    # Parse the data
    entries = parse_budget_data(data)

    updated = 0
    not_found = []

    for parent_name, subcategory_name, amount in entries:
        # Try to find the subcategory
        cursor.execute("""
            SELECT c.id, c.name, c.amount, p.name as parent_name
            FROM categories c
            LEFT JOIN categories p ON c.parent_id = p.id
            WHERE c.budget_id = ? AND LOWER(c.name) = LOWER(?)
        """, (budget_id, subcategory_name))

        rows = cursor.fetchall()

        if not rows:
            not_found.append(f"{parent_name} > {subcategory_name}: {amount}€")
            continue

        # If multiple matches, try to match by parent
        target_row = None
        for row in rows:
            if row[3] and row[3].lower().strip() == parent_name.lower().strip():
                target_row = row
                break

        if not target_row and len(rows) == 1:
            target_row = rows[0]

        if target_row:
            cat_id, cat_name, old_amount, _ = target_row
            if old_amount != amount:
                cursor.execute(
                    "UPDATE categories SET amount = ? WHERE id = ?",
                    (amount, cat_id)
                )
                print(f"  Updated '{cat_name}': {old_amount}€ -> {amount}€")
                updated += 1
            else:
                print(f"  '{cat_name}' already has amount {amount}€")
        else:
            not_found.append(f"{parent_name} > {subcategory_name}: {amount}€")

    conn.commit()
    conn.close()

    print(f"\nUpdated {updated} categories")

    if not_found:
        print(f"\nNot found ({len(not_found)}):")
        for item in not_found:
            print(f"  - {item}")


def main():
    # Default database path
    db_path = "/app/data/budget.db"

    # Allow override via command line
    if len(sys.argv) > 1:
        db_path = sys.argv[1]

    print(f"Using database: {db_path}")

    # Update Julie's budget
    print("\n" + "="*50)
    print("JULIE'S BUDGET")
    print("="*50)
    update_categories(db_path, "julie", JULIE_DATA)

    # Update Julien's budget
    print("\n" + "="*50)
    print("JULIEN'S BUDGET")
    print("="*50)
    update_categories(db_path, "julien", JULIEN_DATA)


if __name__ == "__main__":
    main()
