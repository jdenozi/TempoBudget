# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Factur-X (EN 16931) XML generation and PDF/A-3 embedding."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from io import BytesIO
from xml.etree.ElementTree import Element, SubElement, tostring

# Factur-X namespaces
NAMESPACES = {
    "rsm": "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
    "ram": "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100",
    "qdt": "urn:un:unece:uncefact:data:standard:QualifiedDataType:100",
    "udt": "urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100",
}


def _ns(prefix: str, tag: str) -> str:
    return f"{{{NAMESPACES[prefix]}}}{tag}"


def _add_text(parent: Element, ns: str, tag: str, text: str | None) -> Element | None:
    if text is None:
        return None
    el = SubElement(parent, _ns(ns, tag))
    el.text = str(text)
    return el


def _format_date(date_str: str) -> str:
    """Convert YYYY-MM-DD to YYYYMMDD format required by Factur-X."""
    return date_str.replace("-", "")


def _format_amount(amount: float) -> str:
    """Format amount with 2 decimal places."""
    return f"{Decimal(str(amount)):.2f}"


def generate_facturx_xml(
    *,
    invoice_number: str,
    issue_date: str,
    due_date: str,
    seller_name: str,
    seller_siret: str | None,
    seller_vat_number: str | None,
    seller_street: str | None,
    seller_postal_code: str | None,
    seller_city: str | None,
    seller_country: str,
    seller_email: str | None,
    buyer_name: str,
    buyer_siren: str | None,
    buyer_vat_number: str | None,
    buyer_street: str | None,
    buyer_postal_code: str | None,
    buyer_city: str | None,
    buyer_country: str,
    buyer_email: str | None,
    is_professional: bool,
    currency: str,
    items: list[dict],
    subtotal: float,
    discount_amount: float,
    vat_rate: float,
    vat_amount: float,
    total: float,
    payment_terms_days: int,
    bank_iban: str | None,
    bank_bic: str | None,
    notes: str | None,
) -> bytes:
    """
    Generate Factur-X XML (BASIC profile) compliant with EN 16931.

    Returns XML as UTF-8 encoded bytes.
    """
    # Register namespaces
    for prefix, uri in NAMESPACES.items():
        import xml.etree.ElementTree as ET
        ET.register_namespace(prefix, uri)

    # Root element
    root = Element(_ns("rsm", "CrossIndustryInvoice"))

    # ExchangedDocumentContext
    ctx = SubElement(root, _ns("rsm", "ExchangedDocumentContext"))
    guideline = SubElement(ctx, _ns("ram", "GuidelineSpecifiedDocumentContextParameter"))
    _add_text(guideline, "ram", "ID", "urn:factur-x.eu:1p0:basic")

    # ExchangedDocument
    doc = SubElement(root, _ns("rsm", "ExchangedDocument"))
    _add_text(doc, "ram", "ID", invoice_number)
    _add_text(doc, "ram", "TypeCode", "380")  # 380 = Commercial invoice
    issue_dt = SubElement(doc, _ns("ram", "IssueDateTime"))
    dt_str = SubElement(issue_dt, _ns("udt", "DateTimeString"))
    dt_str.text = _format_date(issue_date)
    dt_str.set("format", "102")  # YYYYMMDD format

    if notes:
        note = SubElement(doc, _ns("ram", "IncludedNote"))
        _add_text(note, "ram", "Content", notes)

    # SupplyChainTradeTransaction
    transaction = SubElement(root, _ns("rsm", "SupplyChainTradeTransaction"))

    # Line items
    for idx, item in enumerate(items, 1):
        line = SubElement(transaction, _ns("ram", "IncludedSupplyChainTradeLineItem"))

        # Line document
        line_doc = SubElement(line, _ns("ram", "AssociatedDocumentLineDocument"))
        _add_text(line_doc, "ram", "LineID", str(idx))

        # Product
        product = SubElement(line, _ns("ram", "SpecifiedTradeProduct"))
        _add_text(product, "ram", "Name", item["description"])

        # Line agreement (price)
        agreement = SubElement(line, _ns("ram", "SpecifiedLineTradeAgreement"))
        net_price = SubElement(agreement, _ns("ram", "NetPriceProductTradePrice"))
        charge = SubElement(net_price, _ns("ram", "ChargeAmount"))
        charge.text = _format_amount(item["unit_price"])

        # Line delivery (quantity)
        delivery = SubElement(line, _ns("ram", "SpecifiedLineTradeDelivery"))
        qty = SubElement(delivery, _ns("ram", "BilledQuantity"))
        qty.text = _format_amount(item["quantity"])
        qty.set("unitCode", "C62")  # Unit (piece)

        # Line settlement (totals)
        settlement = SubElement(line, _ns("ram", "SpecifiedLineTradeSettlement"))

        # VAT for line
        line_tax = SubElement(settlement, _ns("ram", "ApplicableTradeTax"))
        _add_text(line_tax, "ram", "TypeCode", "VAT")
        _add_text(line_tax, "ram", "CategoryCode", "S" if vat_rate > 0 else "E")
        rate_el = SubElement(line_tax, _ns("ram", "RateApplicablePercent"))
        rate_el.text = _format_amount(vat_rate)

        # Line total
        line_monetary = SubElement(settlement, _ns("ram", "SpecifiedTradeSettlementLineMonetarySummation"))
        line_total = SubElement(line_monetary, _ns("ram", "LineTotalAmount"))
        line_total.text = _format_amount(item["total"])

    # ApplicableHeaderTradeAgreement (seller/buyer info)
    agreement = SubElement(transaction, _ns("ram", "ApplicableHeaderTradeAgreement"))

    # Seller
    seller = SubElement(agreement, _ns("ram", "SellerTradeParty"))
    _add_text(seller, "ram", "Name", seller_name)

    if seller_siret:
        seller_id = SubElement(seller, _ns("ram", "SpecifiedLegalOrganization"))
        id_el = SubElement(seller_id, _ns("ram", "ID"))
        id_el.text = seller_siret
        id_el.set("schemeID", "0002")  # SIRET scheme

    if seller_street or seller_postal_code or seller_city:
        seller_addr = SubElement(seller, _ns("ram", "PostalTradeAddress"))
        _add_text(seller_addr, "ram", "LineOne", seller_street)
        _add_text(seller_addr, "ram", "PostcodeCode", seller_postal_code)
        _add_text(seller_addr, "ram", "CityName", seller_city)
        _add_text(seller_addr, "ram", "CountryID", seller_country)

    if seller_email:
        seller_contact = SubElement(seller, _ns("ram", "URIUniversalCommunication"))
        uri = SubElement(seller_contact, _ns("ram", "URIID"))
        uri.text = seller_email
        uri.set("schemeID", "EM")

    if seller_vat_number:
        seller_tax = SubElement(seller, _ns("ram", "SpecifiedTaxRegistration"))
        tax_id = SubElement(seller_tax, _ns("ram", "ID"))
        tax_id.text = seller_vat_number
        tax_id.set("schemeID", "VA")

    # Buyer
    buyer = SubElement(agreement, _ns("ram", "BuyerTradeParty"))
    _add_text(buyer, "ram", "Name", buyer_name)

    if is_professional and buyer_siren:
        buyer_id = SubElement(buyer, _ns("ram", "SpecifiedLegalOrganization"))
        id_el = SubElement(buyer_id, _ns("ram", "ID"))
        id_el.text = buyer_siren
        id_el.set("schemeID", "0002")

    if buyer_street or buyer_postal_code or buyer_city:
        buyer_addr = SubElement(buyer, _ns("ram", "PostalTradeAddress"))
        _add_text(buyer_addr, "ram", "LineOne", buyer_street)
        _add_text(buyer_addr, "ram", "PostcodeCode", buyer_postal_code)
        _add_text(buyer_addr, "ram", "CityName", buyer_city)
        _add_text(buyer_addr, "ram", "CountryID", buyer_country)

    if buyer_email:
        buyer_contact = SubElement(buyer, _ns("ram", "URIUniversalCommunication"))
        uri = SubElement(buyer_contact, _ns("ram", "URIID"))
        uri.text = buyer_email
        uri.set("schemeID", "EM")

    if buyer_vat_number:
        buyer_tax = SubElement(buyer, _ns("ram", "SpecifiedTaxRegistration"))
        tax_id = SubElement(buyer_tax, _ns("ram", "ID"))
        tax_id.text = buyer_vat_number
        tax_id.set("schemeID", "VA")

    # ApplicableHeaderTradeDelivery (empty for services)
    SubElement(transaction, _ns("ram", "ApplicableHeaderTradeDelivery"))

    # ApplicableHeaderTradeSettlement (payment, tax, totals)
    settlement = SubElement(transaction, _ns("ram", "ApplicableHeaderTradeSettlement"))
    _add_text(settlement, "ram", "InvoiceCurrencyCode", currency)

    # Payment terms
    terms = SubElement(settlement, _ns("ram", "SpecifiedTradePaymentTerms"))
    _add_text(terms, "ram", "Description", f"Paiement à {payment_terms_days} jours")
    if due_date:
        due_dt = SubElement(terms, _ns("ram", "DueDateDateTime"))
        due_str = SubElement(due_dt, _ns("udt", "DateTimeString"))
        due_str.text = _format_date(due_date)
        due_str.set("format", "102")

    # Payment means (bank transfer)
    if bank_iban:
        means = SubElement(settlement, _ns("ram", "SpecifiedTradeSettlementPaymentMeans"))
        _add_text(means, "ram", "TypeCode", "30")  # Credit transfer
        payee_account = SubElement(means, _ns("ram", "PayeePartyCreditorFinancialAccount"))
        _add_text(payee_account, "ram", "IBANID", bank_iban)
        if bank_bic:
            payee_institution = SubElement(means, _ns("ram", "PayeeSpecifiedCreditorFinancialInstitution"))
            _add_text(payee_institution, "ram", "BICID", bank_bic)

    # Tax summary
    tax = SubElement(settlement, _ns("ram", "ApplicableTradeTax"))
    calc_amount = SubElement(tax, _ns("ram", "CalculatedAmount"))
    calc_amount.text = _format_amount(vat_amount)
    _add_text(tax, "ram", "TypeCode", "VAT")
    basis = SubElement(tax, _ns("ram", "BasisAmount"))
    basis.text = _format_amount(subtotal - discount_amount)
    _add_text(tax, "ram", "CategoryCode", "S" if vat_rate > 0 else "E")
    rate_pct = SubElement(tax, _ns("ram", "RateApplicablePercent"))
    rate_pct.text = _format_amount(vat_rate)

    # Monetary summation
    monetary = SubElement(settlement, _ns("ram", "SpecifiedTradeSettlementHeaderMonetarySummation"))
    line_total_el = SubElement(monetary, _ns("ram", "LineTotalAmount"))
    line_total_el.text = _format_amount(subtotal)

    if discount_amount > 0:
        allowance = SubElement(monetary, _ns("ram", "AllowanceTotalAmount"))
        allowance.text = _format_amount(discount_amount)

    tax_basis = SubElement(monetary, _ns("ram", "TaxBasisTotalAmount"))
    tax_basis.text = _format_amount(subtotal - discount_amount)

    tax_total = SubElement(monetary, _ns("ram", "TaxTotalAmount"))
    tax_total.text = _format_amount(vat_amount)
    tax_total.set("currencyID", currency)

    grand_total = SubElement(monetary, _ns("ram", "GrandTotalAmount"))
    grand_total.text = _format_amount(total)

    due_payable = SubElement(monetary, _ns("ram", "DuePayableAmount"))
    due_payable.text = _format_amount(total)

    # Generate XML bytes
    xml_declaration = b'<?xml version="1.0" encoding="UTF-8"?>\n'
    return xml_declaration + tostring(root, encoding="utf-8")


def embed_facturx_in_pdf(pdf_bytes: bytes, xml_bytes: bytes, profile: str = "BASIC") -> bytes:
    """
    Embed Factur-X XML into a PDF to create a PDF/A-3 compliant document.

    Args:
        pdf_bytes: The original PDF content
        xml_bytes: The Factur-X XML content
        profile: Factur-X profile (MINIMUM, BASIC, EN16931)

    Returns:
        PDF/A-3 bytes with embedded XML
    """
    from facturx import generate_from_binary

    pdf_buffer = BytesIO(pdf_bytes)
    xml_buffer = BytesIO(xml_bytes)

    output_buffer = BytesIO()
    generate_from_binary(
        pdf_buffer,
        xml_buffer,
        output_pdf=output_buffer,
        flavor="factur-x",
        level=profile.lower(),
    )

    return output_buffer.getvalue()


def generate_facturx_pdf(
    *,
    invoice: dict,
    items: list[dict],
    profile: dict,
    settings: dict,
    client: dict,
    html_pdf_bytes: bytes,
) -> bytes:
    """
    Generate a complete Factur-X PDF from invoice data.

    Args:
        invoice: Invoice data dict
        items: List of line items
        profile: Seller profile dict
        settings: Invoice settings dict
        client: Client/buyer dict
        html_pdf_bytes: Pre-generated PDF from WeasyPrint

    Returns:
        Factur-X compliant PDF/A-3 bytes
    """
    # Calculate discount amount
    discount_amount = 0.0
    if invoice.get("discount_type") and invoice.get("discount_value"):
        if invoice["discount_type"] == "percentage":
            discount_amount = invoice["subtotal"] * invoice["discount_value"] / 100
        else:
            discount_amount = invoice["discount_value"]

    # Generate XML
    xml_bytes = generate_facturx_xml(
        invoice_number=invoice["invoice_number"],
        issue_date=invoice["issue_date"],
        due_date=invoice["due_date"],
        seller_name=profile.get("company_name") or profile.get("name", ""),
        seller_siret=profile.get("siret"),
        seller_vat_number=profile.get("vat_number"),
        seller_street=profile.get("street"),
        seller_postal_code=profile.get("postal_code"),
        seller_city=profile.get("city"),
        seller_country=profile.get("country", "FR"),
        seller_email=profile.get("email"),
        buyer_name=client["name"],
        buyer_siren=client.get("siren"),
        buyer_vat_number=client.get("vat_number"),
        buyer_street=client.get("street"),
        buyer_postal_code=client.get("postal_code"),
        buyer_city=client.get("city"),
        buyer_country=client.get("country", "FR"),
        buyer_email=client.get("email"),
        is_professional=bool(client.get("is_professional", 1)),
        currency="EUR",
        items=items,
        subtotal=invoice["subtotal"],
        discount_amount=discount_amount,
        vat_rate=invoice.get("tva_rate", 0),
        vat_amount=invoice.get("tva_amount", 0),
        total=invoice["total"],
        payment_terms_days=settings.get("payment_terms_days", 30),
        bank_iban=settings.get("bank_iban"),
        bank_bic=settings.get("bank_bic"),
        notes=invoice.get("notes"),
    )

    # Embed XML in PDF
    return embed_facturx_in_pdf(html_pdf_bytes, xml_bytes)
