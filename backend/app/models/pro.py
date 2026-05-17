# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Pro (auto-entrepreneur) data models."""

from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class ProProfile(BaseModel):
    """Pro profile (any legal form: micro-entrepreneur, EI, EURL, SASU, SAS)."""
    id: str = Field(..., description="Unique identifier (UUID)")
    user_id: str = Field(..., description="User ID")
    siret: str | None = Field(None, description="SIRET number")
    legal_form: str = Field("micro", description="Legal form: micro/ei_reel/eurl/sasu/sas")
    activity_type: str = Field("services", description="Activity type (micro: services/vente/...)")
    cotisation_rate: float = Field(21.1, description="Social cotisation rate (%) — micro")
    declaration_frequency: str = Field("quarterly", description="Declaration frequency")
    revenue_threshold: float = Field(77700, description="Annual revenue threshold")
    cfp_rate: float | None = Field(None, description="CFP rate (%) — micro; null = use activity default")
    versement_liberatoire_enabled: int = Field(0, description="Whether IR versement libératoire is opted-in")
    versement_liberatoire_rate: float | None = Field(None, description="VL rate (%) — micro; null = use activity default")
    ir_abattement_rate: float | None = Field(None, description="IR abattement (%) — micro; null = use activity default")
    foyer_tmi: float | None = Field(None, description="Marginal tax rate of the household (%), used for IR estimation")
    tns_cotisations_rate: float = Field(45.0, description="TNS social cotisations rate (%) — used for EI/EURL")
    salary_gross_monthly: float = Field(0, description="Monthly gross salary (SASU/SAS/EURL-IS)")
    dividends_yearly: float = Field(0, description="Estimated yearly dividends to distribute (SASU/SAS/EURL-IS)")
    eurl_tax_option: str = Field("ir", description="EURL tax option: 'ir' or 'is'")
    is_subject_to_vat: int = Field(0, description="Whether subject to VAT (0/1)")
    vat_rate: float = Field(20.0, description="VAT rate (%)")
    vat_number: str | None = Field(None, description="VAT intra-community number")
    company_name: str | None = Field(None, description="Company/business name")
    company_address: str | None = Field(None, description="Company address (legacy free-text)")
    company_email: str | None = Field(None, description="Company email")
    company_phone: str | None = Field(None, description="Company phone")
    street: str | None = Field(None, description="Street address (Factur-X)")
    postal_code: str | None = Field(None, description="Postal code (Factur-X)")
    city: str | None = Field(None, description="City (Factur-X)")
    country: str = Field("FR", description="Country code ISO 3166-1 alpha-2 (Factur-X)")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class UpdateProProfile(BaseModel):
    """Request payload for updating a pro profile."""
    siret: str | None = None
    legal_form: Literal["micro", "ei_reel", "eurl", "sasu", "sas"] | None = None
    activity_type: Literal[
        "services", "liberal", "vente", "artisan", "commercant",
        "agent_commercial", "location_meublee", "restauration",
        "transport", "activite_mixte"
    ] | None = None
    cotisation_rate: float | None = Field(None, gt=0, le=100)
    declaration_frequency: Literal["monthly", "quarterly"] | None = None
    revenue_threshold: float | None = Field(None, gt=0)
    cfp_rate: float | None = Field(None, ge=0, le=10)
    versement_liberatoire_enabled: int | None = Field(None, ge=0, le=1)
    versement_liberatoire_rate: float | None = Field(None, ge=0, le=10)
    ir_abattement_rate: float | None = Field(None, ge=0, le=100)
    foyer_tmi: float | None = Field(None, ge=0, le=50)
    tns_cotisations_rate: float | None = Field(None, ge=0, le=100)
    salary_gross_monthly: float | None = Field(None, ge=0)
    dividends_yearly: float | None = Field(None, ge=0)
    eurl_tax_option: Literal["ir", "is"] | None = None
    is_subject_to_vat: int | None = Field(None, ge=0, le=1)
    vat_rate: float | None = Field(None, gt=0, le=100)
    vat_number: str | None = None
    company_name: str | None = None
    company_address: str | None = None
    company_email: str | None = None
    company_phone: str | None = None
    street: str | None = None
    postal_code: str | None = None
    city: str | None = None
    country: str | None = None


class ProClient(BaseModel):
    """A pro client."""
    id: str = Field(..., description="Unique identifier (UUID)")
    user_id: str = Field(..., description="User ID")
    name: str = Field(..., description="Client name")
    email: str | None = Field(None, description="Client email")
    phone: str | None = Field(None, description="Client phone")
    address: str | None = Field(None, description="Client address (legacy free-text)")
    notes: str | None = Field(None, description="Notes")
    siren: str | None = Field(None, description="SIREN (9 digits) for Factur-X B2B")
    siret: str | None = Field(None, description="SIRET (14 digits) for Factur-X B2B")
    vat_number: str | None = Field(None, description="VAT intra-community number")
    street: str | None = Field(None, description="Street address (Factur-X)")
    postal_code: str | None = Field(None, description="Postal code (Factur-X)")
    city: str | None = Field(None, description="City (Factur-X)")
    country: str = Field("FR", description="Country code ISO 3166-1 alpha-2")
    is_professional: int = Field(1, description="1=B2B (requires SIREN), 0=B2C")
    created_at: str = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class CreateProClient(BaseModel):
    """Request payload for creating a pro client."""
    name: str = Field(..., min_length=1, description="Client name")
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    notes: str | None = None
    siren: str | None = Field(None, pattern=r"^\d{9}$")
    siret: str | None = Field(None, pattern=r"^\d{14}$")
    vat_number: str | None = None
    street: str | None = None
    postal_code: str | None = None
    city: str | None = None
    country: str = "FR"
    is_professional: int = Field(1, ge=0, le=1)


class UpdateProClient(BaseModel):
    """Request payload for updating a pro client."""
    name: str | None = Field(None, min_length=1)
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    notes: str | None = None
    siren: str | None = Field(None, pattern=r"^\d{9}$")
    siret: str | None = Field(None, pattern=r"^\d{14}$")
    vat_number: str | None = None
    street: str | None = None
    postal_code: str | None = None
    city: str | None = None
    country: str | None = None
    is_professional: int | None = Field(None, ge=0, le=1)


class ProCategory(BaseModel):
    """A pro category."""
    id: str = Field(..., description="Unique identifier (UUID)")
    user_id: str = Field(..., description="User ID")
    name: str = Field(..., description="Category name")
    type: str = Field(..., description="Type: income or expense")
    is_default: int = Field(0, description="Whether default category (0/1)")
    created_at: str = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class CreateProCategory(BaseModel):
    """Request payload for creating a pro category."""
    name: str = Field(..., min_length=1, description="Category name")
    type: Literal["income", "expense"] = Field(..., description="Type")


class UpdateProCategory(BaseModel):
    """Request payload for updating a pro category."""
    name: str | None = Field(None, min_length=1)
    type: Literal["income", "expense"] | None = None


class ProTransaction(BaseModel):
    """A pro transaction."""
    id: str = Field(..., description="Unique identifier (UUID)")
    user_id: str = Field(..., description="User ID")
    client_id: str | None = Field(None, description="Client ID")
    category_id: str = Field(..., description="Category ID")
    title: str = Field(..., description="Transaction title")
    amount: float = Field(..., description="Amount")
    transaction_type: str = Field(..., description="Type: income or expense")
    date: str = Field(..., description="Date")
    payment_method: str | None = Field(None, description="Payment method")
    comment: str | None = Field(None, description="Comment")
    discount_type: str | None = Field(None, description="Discount type: percentage or fixed")
    discount_value: float | None = Field(None, description="Discount value")
    coupon_id: str | None = Field(None, description="Coupon ID if applied")
    gift_card_payment: float = Field(0, description="Amount paid by gift card")
    is_declared: int = Field(0, description="Whether declared to URSSAF (0/1)")
    is_deductible: int = Field(1, description="Whether the expense is tax-deductible (0/1) — only meaningful for expenses on non-micro regimes")
    vat_rate: float | None = Field(None, description="VAT rate (%) used for this transaction. Null = inherit profile.vat_rate at display time.")
    invoice_id: str | None = Field(None, description="Linked invoice ID (auto-created from paid invoice)")
    project_category_id: str | None = Field(None, description="Linked project category ID")
    created_at: str = Field(..., description="Creation timestamp")
    client_name: str | None = Field(None, description="Client name (joined)")
    category_name: str | None = Field(None, description="Category name (joined)")
    items: list["ProTransactionItem"] = Field(default_factory=list, description="Transaction line items")

    class Config:
        from_attributes = True


class CreateProTransaction(BaseModel):
    """Request payload for creating a pro transaction."""
    client_id: str | None = None
    category_id: str = Field(..., description="Category ID")
    title: str = Field("", description="Title (auto-generated if items provided)")
    amount: float = Field(0, ge=0, description="Amount (auto-calculated if items provided)")
    transaction_type: Literal["income", "expense"] = Field(..., description="Type")
    date: str = Field(..., description="Date (ISO 8601)")
    payment_method: str | None = Field("cash", description="Payment method")
    comment: str | None = None
    items: list[CreateProTransactionItem] = Field(default_factory=list, description="Line items")
    discount_type: Literal["percentage", "fixed"] | None = None
    discount_value: float | None = None
    coupon_id: str | None = None
    gift_card_id: str | None = None
    gift_card_amount: float | None = None
    project_category_id: str | None = None
    is_declared: int = Field(0, ge=0, le=1, description="Whether to mark as accounted (0/1) — income only")
    is_deductible: int = Field(1, ge=0, le=1, description="Whether the expense is tax-deductible (0/1) — expense only")
    vat_rate: float | None = Field(None, ge=0, le=100, description="VAT rate (%) for this transaction; null = inherit profile.vat_rate")


class UpdateProTransaction(BaseModel):
    """Request payload for updating a pro transaction."""
    client_id: str | None = None
    category_id: str | None = None
    title: str | None = Field(None, min_length=1)
    amount: float | None = Field(None, gt=0)
    transaction_type: Literal["income", "expense"] | None = None
    date: str | None = None
    payment_method: str | None = None
    comment: str | None = None
    project_category_id: str | None = None
    is_declared: int | None = Field(None, ge=0, le=1)
    is_deductible: int | None = Field(None, ge=0, le=1)
    vat_rate: float | None = Field(None, ge=0, le=100)


class ProProduct(BaseModel):
    """A pro product or service in the catalogue."""
    id: str = Field(..., description="Unique identifier (UUID)")
    user_id: str = Field(..., description="User ID")
    name: str = Field(..., description="Product/service name")
    type: str = Field("service", description="Type: product or service")
    default_price: float = Field(0, description="Default price")
    category_id: str | None = Field(None, description="Category ID")
    created_at: str = Field(..., description="Creation timestamp")
    category_name: str | None = Field(None, description="Category name (joined)")

    class Config:
        from_attributes = True


class CreateProProduct(BaseModel):
    """Request payload for creating a pro product."""
    name: str = Field(..., min_length=1, description="Product/service name")
    type: Literal["product", "service", "gift_card"] = Field("service", description="Type")
    default_price: float = Field(..., ge=0, description="Default price")
    category_id: str | None = None


class UpdateProProduct(BaseModel):
    """Request payload for updating a pro product."""
    name: str | None = Field(None, min_length=1)
    type: Literal["product", "service", "gift_card"] | None = None
    default_price: float | None = Field(None, ge=0)
    category_id: str | None = None


class ProTransactionItem(BaseModel):
    """A line item in a pro transaction."""
    id: str = Field(..., description="Unique identifier (UUID)")
    transaction_id: str = Field(..., description="Transaction ID")
    product_id: str = Field(..., description="Product ID")
    quantity: int = Field(1, description="Quantity")
    unit_price: float = Field(..., description="Unit price")
    created_at: str = Field(..., description="Creation timestamp")
    product_name: str | None = Field(None, description="Product name (joined)")

    class Config:
        from_attributes = True


class CreateProTransactionItem(BaseModel):
    """Request payload for a transaction line item."""
    product_id: str = Field(..., description="Product ID")
    quantity: int = Field(1, ge=1, description="Quantity")
    unit_price: float = Field(..., ge=0, description="Unit price")


class ProCoupon(BaseModel):
    """A pro coupon."""
    id: str = Field(..., description="Unique identifier (UUID)")
    user_id: str = Field(..., description="User ID")
    code: str = Field(..., description="Coupon code")
    name: str = Field(..., description="Coupon name")
    discount_type: str = Field("percentage", description="Discount type: percentage or fixed")
    discount_value: float = Field(0, description="Discount value")
    valid_from: str | None = Field(None, description="Valid from date")
    valid_until: str | None = Field(None, description="Valid until date")
    max_uses: int = Field(0, description="Max uses (0 = unlimited)")
    used_count: int = Field(0, description="Current use count")
    is_active: int = Field(1, description="Whether active (0/1)")
    created_at: str = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class CreateProCoupon(BaseModel):
    """Request payload for creating a pro coupon."""
    code: str = Field(..., min_length=1, description="Coupon code")
    name: str = Field(..., min_length=1, description="Coupon name")
    discount_type: Literal["percentage", "fixed"] = Field("percentage", description="Discount type")
    discount_value: float = Field(..., gt=0, description="Discount value")
    valid_from: str | None = None
    valid_until: str | None = None
    max_uses: int = Field(0, ge=0, description="Max uses (0 = unlimited)")


class UpdateProCoupon(BaseModel):
    """Request payload for updating a pro coupon."""
    code: str | None = Field(None, min_length=1)
    name: str | None = Field(None, min_length=1)
    discount_type: Literal["percentage", "fixed"] | None = None
    discount_value: float | None = Field(None, gt=0)
    valid_from: str | None = None
    valid_until: str | None = None
    max_uses: int | None = Field(None, ge=0)
    is_active: int | None = Field(None, ge=0, le=1)


class ProGiftCard(BaseModel):
    """A pro gift card."""
    id: str = Field(..., description="Unique identifier (UUID)")
    user_id: str = Field(..., description="User ID")
    code: str = Field(..., description="Gift card code")
    initial_amount: float = Field(..., description="Initial amount")
    remaining_balance: float = Field(..., description="Remaining balance")
    client_id: str | None = Field(None, description="Purchaser client ID")
    purchase_transaction_id: str | None = Field(None, description="Purchase transaction ID")
    purchase_date: str = Field(..., description="Purchase date")
    is_active: int = Field(1, description="Whether active (0/1)")
    created_at: str = Field(..., description="Creation timestamp")
    client_name: str | None = Field(None, description="Client name (joined)")

    class Config:
        from_attributes = True


class CreateProGiftCard(BaseModel):
    """Request payload for creating a pro gift card."""
    code: str = Field(..., min_length=1, description="Gift card code")
    initial_amount: float = Field(..., gt=0, description="Initial amount")
    client_id: str | None = None
    purchase_date: str = Field(..., description="Purchase date (ISO 8601)")


class ProGiftCardUsage(BaseModel):
    """A gift card usage record."""
    id: str = Field(..., description="Unique identifier (UUID)")
    gift_card_id: str = Field(..., description="Gift card ID")
    transaction_id: str = Field(..., description="Transaction ID")
    amount_used: float = Field(..., description="Amount used")
    created_at: str = Field(..., description="Creation timestamp")
    transaction_title: str | None = Field(None, description="Transaction title (joined)")

    class Config:
        from_attributes = True


class ProDashboardSummary(BaseModel):
    """Dashboard summary for pro mode."""
    ca_month: float = Field(0, description="Revenue this month")
    ca_quarter: float = Field(0, description="Revenue this quarter")
    ca_year: float = Field(0, description="Revenue this year")
    expenses_month: float = Field(0, description="Expenses this month")
    expenses_quarter: float = Field(0, description="Expenses this quarter")
    expenses_year: float = Field(0, description="Expenses this year")
    net_month: float = Field(0, description="Net this month")
    cotisations_estimated: float = Field(0, description="Estimated cotisations")
    threshold_percentage: float = Field(0, description="% of revenue threshold used")


# ────────────────────────────── Declaration ──────────────────────────────


class BatchToggleDeclared(BaseModel):
    """Request payload for batch toggling declaration status."""
    transaction_ids: list[str] = Field(..., min_length=1, description="Transaction IDs to toggle")
    is_declared: int = Field(..., ge=0, le=1, description="0 or 1")


class DeclarationPeriodSummary(BaseModel):
    """Summary for a declaration period."""
    period_start: str = Field(..., description="Period start date")
    period_end: str = Field(..., description="Period end date")
    period_label: str = Field(..., description="Human label e.g. 'Janvier 2026' or 'T1 2026'")
    total_income: float = Field(0, description="Total income for the period")
    declared_income: float = Field(0, description="Declared income for the period")
    undeclared_income: float = Field(0, description="Undeclared income for the period")
    total_transactions: int = Field(0, description="Total income transactions")
    declared_transactions: int = Field(0, description="Number of declared transactions")
    cotisations_estimated: float = Field(0, description="Estimated cotisations on declared income")


# ────────────────────────────── Invoice Settings ──────────────────────────────


class ProInvoiceSettings(BaseModel):
    """Invoice/quote settings per user."""
    id: str
    user_id: str
    invoice_prefix: str = "F"
    quote_prefix: str = "D"
    next_invoice_number: int = 1
    next_quote_number: int = 1
    payment_terms_days: int = 30
    late_penalty_rate: float = 3.0
    bank_name: str | None = None
    bank_iban: str | None = None
    bank_bic: str | None = None
    default_notes: str | None = None
    logo_path: str | None = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class UpdateProInvoiceSettings(BaseModel):
    """Update invoice settings."""
    invoice_prefix: str | None = None
    quote_prefix: str | None = None
    payment_terms_days: int | None = Field(None, ge=0)
    late_penalty_rate: float | None = Field(None, ge=0)
    bank_name: str | None = None
    bank_iban: str | None = None
    bank_bic: str | None = None
    default_notes: str | None = None
    logo_path: str | None = None


# ────────────────────────────── Invoice Items ──────────────────────────────


class ProInvoiceItem(BaseModel):
    """A line item in an invoice."""
    id: str
    invoice_id: str
    product_id: str | None = None
    description: str
    quantity: float = 1
    unit_price: float = 0
    total: float = 0
    sort_order: int = 0

    class Config:
        from_attributes = True


class CreateProInvoiceItem(BaseModel):
    """Create payload for an invoice line item."""
    product_id: str | None = None
    description: str = Field(..., min_length=1)
    quantity: float = Field(1, gt=0)
    unit_price: float = Field(0, ge=0)


# ────────────────────────────── Invoices ──────────────────────────────


class ProInvoice(BaseModel):
    """A pro invoice."""
    id: str
    user_id: str
    client_id: str
    invoice_number: str
    status: str = "draft"
    issue_date: str
    due_date: str
    subtotal: float = 0
    tva_rate: float = 0
    tva_amount: float = 0
    total: float = 0
    discount_type: str | None = None
    discount_value: float = 0
    notes: str | None = None
    payment_method: str | None = None
    paid_date: str | None = None
    quote_id: str | None = None
    reminder_sent_at: str | None = None
    created_at: str
    updated_at: str
    client_name: str | None = None
    client_email: str | None = None
    client_address: str | None = None
    items: list[ProInvoiceItem] = Field(default_factory=list)

    class Config:
        from_attributes = True


class CreateProInvoice(BaseModel):
    """Create payload for an invoice."""
    client_id: str
    issue_date: str
    due_date: str
    discount_type: Literal["percentage", "fixed"] | None = None
    discount_value: float = 0
    notes: str | None = None
    items: list[CreateProInvoiceItem] = Field(default_factory=list)


class UpdateProInvoice(BaseModel):
    """Update payload for an invoice."""
    client_id: str | None = None
    issue_date: str | None = None
    due_date: str | None = None
    discount_type: Literal["percentage", "fixed"] | None = None
    discount_value: float | None = None
    notes: str | None = None
    items: list[CreateProInvoiceItem] | None = None


class UpdateProInvoiceStatus(BaseModel):
    """Update invoice status."""
    status: Literal["draft", "sent", "paid", "cancelled"]
    payment_method: str | None = None
    paid_date: str | None = None


# ────────────────────────────── Quote Items ──────────────────────────────


class ProQuoteItem(BaseModel):
    """A line item in a quote."""
    id: str
    quote_id: str
    product_id: str | None = None
    description: str
    quantity: float = 1
    unit_price: float = 0
    total: float = 0
    sort_order: int = 0

    class Config:
        from_attributes = True


class CreateProQuoteItem(BaseModel):
    """Create payload for a quote line item."""
    product_id: str | None = None
    description: str = Field(..., min_length=1)
    quantity: float = Field(1, gt=0)
    unit_price: float = Field(0, ge=0)


# ────────────────────────────── Quotes ──────────────────────────────


class ProQuote(BaseModel):
    """A pro quote (devis)."""
    id: str
    user_id: str
    client_id: str
    quote_number: str
    status: str = "draft"
    issue_date: str
    validity_date: str
    subtotal: float = 0
    tva_rate: float = 0
    tva_amount: float = 0
    total: float = 0
    discount_type: str | None = None
    discount_value: float = 0
    notes: str | None = None
    invoice_id: str | None = None
    created_at: str
    updated_at: str
    client_name: str | None = None
    client_email: str | None = None
    client_address: str | None = None
    items: list[ProQuoteItem] = Field(default_factory=list)

    class Config:
        from_attributes = True


class CreateProQuote(BaseModel):
    """Create payload for a quote."""
    client_id: str
    issue_date: str
    validity_date: str
    discount_type: Literal["percentage", "fixed"] | None = None
    discount_value: float = 0
    notes: str | None = None
    items: list[CreateProQuoteItem] = Field(default_factory=list)


class UpdateProQuote(BaseModel):
    """Update payload for a quote."""
    client_id: str | None = None
    issue_date: str | None = None
    validity_date: str | None = None
    discount_type: Literal["percentage", "fixed"] | None = None
    discount_value: float | None = None
    notes: str | None = None
    items: list[CreateProQuoteItem] | None = None


class UpdateProQuoteStatus(BaseModel):
    """Update quote status."""
    status: Literal["draft", "sent", "accepted", "rejected", "expired"]


# ── Pro recurring transactions (subscriptions, fixed costs, etc.) ──


class ProRecurringTransaction(BaseModel):
    """A recurring pro transaction template (subscription, monthly bill, etc.)."""
    id: str
    user_id: str
    client_id: str | None = None
    category_id: str
    title: str
    amount: float
    transaction_type: str
    frequency: str
    day: int | None = None
    payment_method: str | None = "cash"
    comment: str | None = None
    active: int = 1
    created_at: str
    client_name: str | None = None
    category_name: str | None = None

    class Config:
        from_attributes = True


class CreateProRecurringTransaction(BaseModel):
    """Request payload for creating a recurring pro transaction."""
    client_id: str | None = None
    category_id: str
    title: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)
    transaction_type: Literal["income", "expense"]
    frequency: Literal["daily", "weekly", "monthly", "yearly"]
    day: int | None = Field(None, ge=0, le=31)
    payment_method: str | None = "cash"
    comment: str | None = None


class UpdateProRecurringTransaction(BaseModel):
    """Request payload for updating a recurring pro transaction."""
    client_id: str | None = None
    category_id: str | None = None
    title: str | None = Field(None, min_length=1)
    amount: float | None = Field(None, gt=0)
    transaction_type: Literal["income", "expense"] | None = None
    frequency: Literal["daily", "weekly", "monthly", "yearly"] | None = None
    day: int | None = Field(None, ge=0, le=31)
    payment_method: str | None = None
    comment: str | None = None
    active: int | None = Field(None, ge=0, le=1)


# ── User-defined revenue limits / thresholds ──


class ProThreshold(BaseModel):
    """A user-defined revenue threshold (e.g. CAF benefit ceiling, fiscal limit, custom goal)."""
    id: str
    user_id: str
    name: str
    period: str  # 'monthly' | 'quarterly' | 'yearly'
    amount: float
    color: str = "#f0a020"
    active: int = 1
    created_at: str

    class Config:
        from_attributes = True


class CreateProThreshold(BaseModel):
    """Request payload for creating a threshold."""
    name: str = Field(..., min_length=1, max_length=80)
    period: Literal["monthly", "quarterly", "yearly"]
    amount: float = Field(..., gt=0)
    color: str = Field("#f0a020", min_length=4, max_length=9)


class UpdateProThreshold(BaseModel):
    """Request payload for updating a threshold."""
    name: str | None = Field(None, min_length=1, max_length=80)
    period: Literal["monthly", "quarterly", "yearly"] | None = None
    amount: float | None = Field(None, gt=0)
    color: str | None = Field(None, min_length=4, max_length=9)
    active: int | None = Field(None, ge=0, le=1)


# ── Tax breakdown (multi-regime) ──


class TaxBreakdown(BaseModel):
    """Detailed view of all prélèvements (cotisations + taxes) for one period.

    Shape kept stable across regimes: fields irrelevant to a given regime are
    null. The `notes` array carries human-readable explanations or warnings
    (e.g. "TMI non renseigné, IR classique non estimé").
    """
    legal_form: str
    period: str  # 'month' | 'quarter' | 'year'
    period_label: str
    turnover: float
    deductible_expenses: float = 0.0
    benefice_imposable: float | None = None
    cotisations_sociales: float = 0.0
    cfp: float = 0.0
    ir_versement_liberatoire: float | None = None
    ir_classique_estime: float | None = None
    impot_societes: float | None = None
    dividendes_taxes: float | None = None
    net_salary: float | None = None
    total_prelevements: float = 0.0
    net_after_taxes: float = 0.0
    personal_take_home: float = 0.0
    notes: list[str] = []


class RegimeComparisonRow(BaseModel):
    """One row of the regime comparison table — same inputs, different regime."""
    regime: str  # 'micro' | 'ei_reel' | 'eurl_ir' | 'eurl_is' | 'sasu' | 'sas'
    breakdown: TaxBreakdown


class VatSummary(BaseModel):
    """VAT (TVA) summary for one period."""
    period: str  # 'month' | 'quarter' | 'year'
    period_label: str
    is_subject_to_vat: int
    default_rate: float
    collected: float          # TVA collectée (on income)
    deductible: float         # TVA déductible (on deductible expenses)
    balance: float            # collected - deductible (positive = owed to DGFiP)
    notes: list[str] = []
