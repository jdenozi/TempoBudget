# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Subscription and billing models."""

from pydantic import BaseModel, EmailStr, Field


class Invitation(BaseModel):
    """Invitation for user registration."""
    id: str
    email: str
    token: str
    invited_by_user_id: str
    created_at: str
    expires_at: str
    used_at: str | None = None
    used_by_user_id: str | None = None

    class Config:
        from_attributes = True


class CreateInvitationRequest(BaseModel):
    """Request to create an invitation."""
    email: EmailStr


class InvitationValidation(BaseModel):
    """Result of invitation token validation."""
    valid: bool
    email: str | None = None
    expired: bool = False
    already_used: bool = False


class ProAccessStatus(BaseModel):
    """Pro access status for a user."""
    has_pro_access: bool
    reason: str  # 'subscription', 'admin_override', 'none'


class SetProOverrideRequest(BaseModel):
    """Request to set pro override for a user."""
    pro_override: bool


class StripeCustomer(BaseModel):
    """Stripe customer mapping."""
    id: str
    user_id: str
    stripe_customer_id: str
    created_at: str

    class Config:
        from_attributes = True


class Subscription(BaseModel):
    """User subscription."""
    id: str
    user_id: str
    stripe_subscription_id: str | None = None
    stripe_price_id: str
    plan_type: str = Field(..., pattern="^(monthly|annual)$")
    status: str = Field(default="active")
    current_period_start: str
    current_period_end: str
    cancel_at_period_end: bool = False
    canceled_at: str | None = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class SubscriptionStatus(BaseModel):
    """Subscription status response."""
    has_subscription: bool = False
    subscription: Subscription | None = None
    plan_type: str | None = None
    status: str | None = None
    current_period_end: str | None = None
    cancel_at_period_end: bool = False


class CreateCheckoutRequest(BaseModel):
    """Request to create a Stripe checkout session."""
    plan_type: str = Field(..., pattern="^(monthly|annual)$")
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    """Checkout session response."""
    checkout_url: str
    session_id: str


class PortalResponse(BaseModel):
    """Customer portal response."""
    portal_url: str


class AdminQuote(BaseModel):
    """Admin quote for prospects."""
    id: str
    created_by_user_id: str
    prospect_name: str
    prospect_email: str
    prospect_company: str | None = None
    plan_type: str = Field(..., pattern="^(monthly|annual)$")
    quantity: int = 1
    unit_price: float
    total: float
    valid_until: str
    notes: str | None = None
    status: str = Field(default="draft")
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class CreateQuoteRequest(BaseModel):
    """Request to create a quote."""
    prospect_name: str = Field(..., min_length=1)
    prospect_email: str = Field(..., min_length=1)
    prospect_company: str | None = None
    plan_type: str = Field(..., pattern="^(monthly|annual)$")
    quantity: int = Field(default=1, ge=1)
    unit_price: float = Field(..., gt=0)
    valid_days: int = Field(default=30, ge=1, le=365)
    notes: str | None = None


class UpdateQuoteRequest(BaseModel):
    """Request to update a quote."""
    prospect_name: str | None = None
    prospect_email: str | None = None
    prospect_company: str | None = None
    plan_type: str | None = Field(default=None, pattern="^(monthly|annual)$")
    quantity: int | None = Field(default=None, ge=1)
    unit_price: float | None = Field(default=None, gt=0)
    valid_until: str | None = None
    notes: str | None = None
    status: str | None = Field(default=None, pattern="^(draft|sent|accepted|expired)$")


class AdminUserInfo(BaseModel):
    """User info for admin panel."""
    id: str
    email: str
    name: str
    is_admin: bool
    pro_override: bool = False
    created_at: str
    subscription: Subscription | None = None


class SubscriptionStats(BaseModel):
    """Subscription statistics for admin."""
    total_users: int
    total_subscribers: int
    active_subscriptions: int
    monthly_subscribers: int
    annual_subscribers: int
    mrr: float
    arr: float
    churn_rate: float
