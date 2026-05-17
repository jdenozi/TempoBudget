# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""PDF generation for invoices and quotes using WeasyPrint."""

from __future__ import annotations

from weasyprint import HTML


def _build_items_rows(items: list[dict]) -> str:
    rows = ""
    for item in items:
        rows += f"""
        <tr>
            <td>{item['description']}</td>
            <td class="right">{item['quantity']:.2f}</td>
            <td class="right">{item['unit_price']:.2f} €</td>
            <td class="right">{item['total']:.2f} €</td>
        </tr>"""
    return rows


def _build_html(
    *,
    doc_type: str,
    doc_number: str,
    status: str,
    issue_date: str,
    due_or_validity_label: str,
    due_or_validity_date: str,
    profile_name: str,
    profile_siret: str | None,
    profile_email: str | None,
    profile_phone: str | None,
    profile_address: str | None,
    profile_vat_number: str | None,
    is_subject_to_vat: bool,
    client_name: str,
    client_email: str | None,
    client_address: str | None,
    items: list[dict],
    subtotal: float,
    discount_type: str | None,
    discount_value: float,
    tva_rate: float,
    tva_amount: float,
    total: float,
    notes: str | None,
    payment_terms_days: int,
    late_penalty_rate: float,
    bank_name: str | None,
    bank_iban: str | None,
    bank_bic: str | None,
) -> str:
    items_rows = _build_items_rows(items)

    # Calculate total HT (after discount, before TVA)
    total_ht = total - tva_amount if is_subject_to_vat else total

    discount_row = ""
    if discount_type and discount_value:
        if discount_type == "percentage":
            discount_row = f'<tr><td colspan="3" class="right"><strong>Remise ({discount_value:.1f}%)</strong></td><td class="right">-{subtotal * discount_value / 100:.2f} €</td></tr>'
        else:
            discount_row = f'<tr><td colspan="3" class="right"><strong>Remise</strong></td><td class="right">-{discount_value:.2f} €</td></tr>'

    # Build totals section
    if is_subject_to_vat:
        totals_rows = f"""
            <tr><td>Sous-total HT</td><td class="right">{subtotal:.2f} €</td></tr>
            {discount_row}
            <tr><td><strong>Total HT</strong></td><td class="right"><strong>{total_ht:.2f} €</strong></td></tr>
            <tr><td>TVA ({tva_rate:.1f}%)</td><td class="right">{tva_amount:.2f} €</td></tr>
            <tr class="total-row"><td>Total TTC</td><td class="right">{total:.2f} €</td></tr>"""
    else:
        totals_rows = f"""
            <tr><td>Sous-total</td><td class="right">{subtotal:.2f} €</td></tr>
            {discount_row}
            <tr class="total-row"><td>Total</td><td class="right">{total:.2f} €</td></tr>"""

    bank_section = ""
    if bank_iban:
        bank_section = f"""
        <div class="bank-info">
            <h3>Coordonnées bancaires</h3>
            <p>{f'Banque : {bank_name}<br/>' if bank_name else ''}IBAN : {bank_iban}{f'<br/>BIC : {bank_bic}' if bank_bic else ''}</p>
        </div>"""

    notes_section = ""
    if notes:
        notes_section = f'<div class="notes"><h3>Notes</h3><p>{notes}</p></div>'

    siret_line = f"SIRET : {profile_siret}" if profile_siret else ""
    vat_number_line = f"<br/>N° TVA : {profile_vat_number}" if profile_vat_number else ""

    client_address_line = f"<br/>{client_address}" if client_address else ""
    client_email_line = f"<br/>{client_email}" if client_email else ""

    profile_contact = ""
    if profile_email:
        profile_contact += f"<br/>{profile_email}"
    if profile_phone:
        profile_contact += f"<br/>{profile_phone}"
    if profile_address:
        profile_contact += f"<br/>{profile_address}"

    # Legal mention about TVA
    if is_subject_to_vat:
        tva_legal = f"TVA applicable : {tva_rate:.1f}%"
        if profile_vat_number:
            tva_legal += f" — N° TVA intracommunautaire : {profile_vat_number}"
    else:
        tva_legal = "TVA non applicable, art. 293 B du CGI"

    # Column headers
    price_header = "Prix unit. HT" if is_subject_to_vat else "Prix unitaire"
    total_col_header = "Total HT" if is_subject_to_vat else "Total"

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
    @page {{ size: A4; margin: 2cm; }}
    body {{ font-family: Helvetica, Arial, sans-serif; font-size: 10pt; color: #000; line-height: 1.4; }}
    .header {{ display: flex; justify-content: space-between; margin-bottom: 30px; }}
    .header-left {{ max-width: 50%; }}
    .header-left h1 {{ margin: 0; font-size: 22pt; color: #000; }}
    .header-left .company {{ margin-top: 8px; font-size: 9pt; color: #444; }}
    .header-right {{ text-align: right; }}
    .doc-info {{ margin-bottom: 24px; }}
    .doc-info table {{ border-collapse: collapse; }}
    .doc-info td {{ padding: 3px 12px 3px 0; }}
    .doc-info td:first-child {{ font-weight: bold; color: #333; }}
    .client-box {{ border: 1px solid #999; border-radius: 4px; padding: 16px; margin-bottom: 24px; }}
    .client-box h3 {{ margin: 0 0 8px; font-size: 9pt; text-transform: uppercase; color: #555; }}
    .client-box p {{ margin: 0; }}
    table.items {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
    table.items th {{ background: #333; color: white; padding: 8px 12px; text-align: left; font-size: 9pt; }}
    table.items th:last-child, table.items th:nth-child(2), table.items th:nth-child(3) {{ text-align: right; }}
    table.items td {{ padding: 8px 12px; border-bottom: 1px solid #ccc; }}
    table.items tr:nth-child(even) {{ background: #f5f5f5; }}
    .right {{ text-align: right; }}
    .totals {{ margin-left: auto; width: 300px; }}
    .totals table {{ width: 100%; border-collapse: collapse; }}
    .totals td {{ padding: 6px 12px; }}
    .totals .total-row {{ font-size: 13pt; font-weight: bold; border-top: 2px solid #000; color: #000; }}
    .notes {{ margin-top: 20px; padding: 12px; border: 1px solid #ccc; border-radius: 4px; border-left: 3px solid #999; }}
    .notes h3 {{ margin: 0 0 6px; font-size: 9pt; color: #333; }}
    .notes p {{ margin: 0; font-size: 9pt; }}
    .bank-info {{ margin-top: 20px; padding: 12px; border: 1px solid #ccc; border-radius: 4px; }}
    .bank-info h3 {{ margin: 0 0 6px; font-size: 9pt; color: #333; }}
    .bank-info p {{ margin: 0; font-size: 9pt; }}
    .legal {{ margin-top: 30px; padding-top: 16px; border-top: 1px solid #ccc; font-size: 7.5pt; color: #666; line-height: 1.6; }}
</style>
</head>
<body>
    <div class="header">
        <div class="header-left">
            <h1>{doc_type} {doc_number}</h1>
            <div class="company">
                {profile_name}<br/>
                {siret_line}
                {vat_number_line}
                {profile_contact}
            </div>
        </div>
    </div>

    <div class="doc-info">
        <table>
            <tr><td>Date d'émission :</td><td>{issue_date}</td></tr>
            <tr><td>{due_or_validity_label} :</td><td>{due_or_validity_date}</td></tr>
            <tr><td>Statut :</td><td>{status}</td></tr>
        </table>
    </div>

    <div class="client-box">
        <h3>Client</h3>
        <p><strong>{client_name}</strong>{client_address_line}{client_email_line}</p>
    </div>

    <table class="items">
        <thead>
            <tr>
                <th>Description</th>
                <th>Quantité</th>
                <th>{price_header}</th>
                <th>{total_col_header}</th>
            </tr>
        </thead>
        <tbody>
            {items_rows}
        </tbody>
    </table>

    <div class="totals">
        <table>
            {totals_rows}
        </table>
    </div>

    {notes_section}
    {bank_section}

    <div class="legal">
        {tva_legal}<br/>
        Conditions de paiement : {payment_terms_days} jours à compter de la date d'émission<br/>
        Pas d'escompte pour paiement anticipé<br/>
        En cas de retard de paiement, pénalités de retard : {late_penalty_rate:.1f}% par an<br/>
        Indemnité forfaitaire pour frais de recouvrement : 40,00 €
    </div>
</body>
</html>"""


def generate_invoice_pdf(
    *,
    invoice: dict,
    items: list[dict],
    profile: dict,
    settings: dict,
    client: dict,
    facturx: bool = False,
) -> bytes:
    """Generate a PDF for an invoice.

    Args:
        invoice: Invoice data
        items: Line items
        profile: Seller profile
        settings: Invoice settings
        client: Client/buyer data
        facturx: If True, generate Factur-X compliant PDF/A-3 with embedded XML

    Returns:
        PDF bytes (standard or Factur-X compliant)
    """
    status_map = {"draft": "Brouillon", "sent": "Envoyée", "paid": "Payée", "cancelled": "Annulée"}
    is_vat = bool(profile.get("is_subject_to_vat"))

    # Build client address from structured fields if available
    client_address = client.get("address")
    if client.get("street") or client.get("city"):
        parts = []
        if client.get("street"):
            parts.append(client["street"])
        if client.get("postal_code") or client.get("city"):
            parts.append(f"{client.get('postal_code', '')} {client.get('city', '')}".strip())
        if client.get("country") and client.get("country") != "FR":
            parts.append(client["country"])
        if parts:
            client_address = ", ".join(parts)

    # Build profile address from structured fields if available
    profile_address = profile.get("address")
    if profile.get("street") or profile.get("city"):
        parts = []
        if profile.get("street"):
            parts.append(profile["street"])
        if profile.get("postal_code") or profile.get("city"):
            parts.append(f"{profile.get('postal_code', '')} {profile.get('city', '')}".strip())
        if parts:
            profile_address = ", ".join(parts)

    html_str = _build_html(
        doc_type="Facture",
        doc_number=invoice["invoice_number"],
        status=status_map.get(invoice["status"], invoice["status"]),
        issue_date=invoice["issue_date"],
        due_or_validity_label="Date d'échéance",
        due_or_validity_date=invoice["due_date"],
        profile_name=profile.get("company_name") or profile.get("name", ""),
        profile_siret=profile.get("siret"),
        profile_email=profile.get("email"),
        profile_phone=profile.get("phone"),
        profile_address=profile_address,
        profile_vat_number=profile.get("vat_number"),
        is_subject_to_vat=is_vat,
        client_name=client["name"],
        client_email=client.get("email"),
        client_address=client_address,
        items=items,
        subtotal=invoice["subtotal"],
        discount_type=invoice.get("discount_type"),
        discount_value=invoice.get("discount_value", 0),
        tva_rate=invoice.get("tva_rate", 0),
        tva_amount=invoice.get("tva_amount", 0),
        total=invoice["total"],
        notes=invoice.get("notes"),
        payment_terms_days=settings.get("payment_terms_days", 30),
        late_penalty_rate=settings.get("late_penalty_rate", 3.0),
        bank_name=settings.get("bank_name"),
        bank_iban=settings.get("bank_iban"),
        bank_bic=settings.get("bank_bic"),
    )

    pdf_bytes = HTML(string=html_str).write_pdf()

    if facturx:
        from app.facturx_generator import generate_facturx_pdf
        return generate_facturx_pdf(
            invoice=invoice,
            items=items,
            profile=profile,
            settings=settings,
            client=client,
            html_pdf_bytes=pdf_bytes,
        )

    return pdf_bytes


def generate_quote_pdf(
    *,
    quote: dict,
    items: list[dict],
    profile: dict,
    settings: dict,
    client: dict,
) -> bytes:
    """Generate a PDF for a quote."""
    status_map = {"draft": "Brouillon", "sent": "Envoyé", "accepted": "Accepté", "rejected": "Rejeté", "expired": "Expiré"}
    is_vat = bool(profile.get("is_subject_to_vat"))
    html_str = _build_html(
        doc_type="Devis",
        doc_number=quote["quote_number"],
        status=status_map.get(quote["status"], quote["status"]),
        issue_date=quote["issue_date"],
        due_or_validity_label="Date de validité",
        due_or_validity_date=quote["validity_date"],
        profile_name=profile.get("name", ""),
        profile_siret=profile.get("siret"),
        profile_email=profile.get("email"),
        profile_phone=profile.get("phone"),
        profile_address=profile.get("address"),
        profile_vat_number=profile.get("vat_number"),
        is_subject_to_vat=is_vat,
        client_name=client["name"],
        client_email=client.get("email"),
        client_address=client.get("address"),
        items=items,
        subtotal=quote["subtotal"],
        discount_type=quote.get("discount_type"),
        discount_value=quote.get("discount_value", 0),
        tva_rate=quote.get("tva_rate", 0),
        tva_amount=quote.get("tva_amount", 0),
        total=quote["total"],
        notes=quote.get("notes"),
        payment_terms_days=settings.get("payment_terms_days", 30),
        late_penalty_rate=settings.get("late_penalty_rate", 3.0),
        bank_name=settings.get("bank_name"),
        bank_iban=settings.get("bank_iban"),
        bank_bic=settings.get("bank_bic"),
    )
    return HTML(string=html_str).write_pdf()
