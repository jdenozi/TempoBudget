# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Pro (auto-entrepreneur) data models."""

from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class ProProfile(BaseModel):
    """Auto-entrepreneur profile."""
    id: str = Field(..., description="Unique identifier (UUID)")
    user_id: str = Field(..., description="User ID")
    siret: str | None = Field(None, description="SIRET number")
    activity_type: str = Field("services", description="Activity type")
    cotisation_rate: float = Field(21.1, description="Cotisation rate (%)")
    declaration_frequency: str = Field("quarterly", description="Declaration frequency")
    revenue_threshold: float = Field(77700, description="Annual revenue threshold")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class UpdateProProfile(BaseModel):
    """Request payload for updating a pro profile."""
    siret: str | None = None
    activity_type: Literal[
        "services", "liberal", "vente", "artisan", "commercant",
        "agent_commercial", "location_meublee", "restauration",
        "transport", "activite_mixte"
    ] | None = None
    cotisation_rate: float | None = Field(None, gt=0, le=100)
    declaration_frequency: Literal["monthly", "quarterly"] | None = None
    revenue_threshold: float | None = Field(None, gt=0)


class ProClient(BaseModel):
    """A pro client."""
    id: str = Field(..., description="Unique identifier (UUID)")
    user_id: str = Field(..., description="User ID")
    name: str = Field(..., description="Client name")
    email: str | None = Field(None, description="Client email")
    phone: str | None = Field(None, description="Client phone")
    address: str | None = Field(None, description="Client address")
    notes: str | None = Field(None, description="Notes")
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


class UpdateProClient(BaseModel):
    """Request payload for updating a pro client."""
    name: str | None = Field(None, min_length=1)
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    notes: str | None = None


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
