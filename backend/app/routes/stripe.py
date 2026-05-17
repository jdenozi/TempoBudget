# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Stripe subscription routes."""

import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user
from ..database import get_db
from ..models.subscription import (
    Subscription,
    SubscriptionStatus,
    CreateCheckoutRequest,
    CheckoutResponse,
    PortalResponse,
)
from ..notifications import (
    send_payment_confirmation,
    send_payment_reminder,
    send_invoice,
)

router = APIRouter()

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_MONTHLY = os.getenv("STRIPE_PRICE_MONTHLY", "")
STRIPE_PRICE_ANNUAL = os.getenv("STRIPE_PRICE_ANNUAL", "")

# Lazy import stripe to avoid startup errors if not configured
_stripe = None


def get_stripe():
    """Get or initialize Stripe SDK."""
    global _stripe
    if _stripe is None:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
        _stripe = stripe
    return _stripe


async def get_or_create_stripe_customer(
    user_id: str,
    db: AsyncSession,
) -> str:
    """Get existing or create new Stripe customer for user."""
    result = await db.execute(
        text("SELECT stripe_customer_id FROM stripe_customers WHERE user_id = :user_id"),
        {"user_id": user_id},
    )
    row = result.fetchone()
    if row:
        return row.stripe_customer_id

    # Get user email
    user_result = await db.execute(
        text("SELECT email, name FROM users WHERE id = :id"),
        {"id": user_id},
    )
    user_row = user_result.fetchone()
    if not user_row:
        raise HTTPException(status_code=404, detail="User not found")

    # Create Stripe customer
    stripe = get_stripe()
    customer = stripe.Customer.create(
        email=user_row.email,
        name=user_row.name,
        metadata={"user_id": user_id},
    )

    # Save mapping
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        text("""
            INSERT INTO stripe_customers (id, user_id, stripe_customer_id, created_at)
            VALUES (:id, :user_id, :stripe_customer_id, :created_at)
        """),
        {
            "id": str(uuid4()),
            "user_id": user_id,
            "stripe_customer_id": customer.id,
            "created_at": now,
        },
    )
    await db.commit()

    return customer.id


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    request: CreateCheckoutRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a Stripe Checkout session for subscription."""
    if not STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe is not configured",
        )

    # Check if user already has active subscription
    result = await db.execute(
        text("""
            SELECT id FROM subscriptions
            WHERE user_id = :user_id AND status IN ('active', 'trialing')
        """),
        {"user_id": user_id},
    )
    if result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has an active subscription",
        )

    # Get or create Stripe customer
    customer_id = await get_or_create_stripe_customer(user_id, db)

    # Determine price
    price_id = STRIPE_PRICE_MONTHLY if request.plan_type == "monthly" else STRIPE_PRICE_ANNUAL
    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Price for {request.plan_type} plan is not configured",
        )

    # Create checkout session
    stripe = get_stripe()
    session = stripe.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=request.success_url,
        cancel_url=request.cancel_url,
        metadata={"user_id": user_id, "plan_type": request.plan_type},
    )

    return CheckoutResponse(checkout_url=session.url, session_id=session.id)


@router.get("/subscription", response_model=SubscriptionStatus)
async def get_subscription_status(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's subscription status."""
    result = await db.execute(
        text("""
            SELECT * FROM subscriptions
            WHERE user_id = :user_id
            ORDER BY created_at DESC LIMIT 1
        """),
        {"user_id": user_id},
    )
    row = result.fetchone()

    if not row:
        return SubscriptionStatus(has_subscription=False)

    subscription = Subscription(
        id=row.id,
        user_id=row.user_id,
        stripe_subscription_id=row.stripe_subscription_id,
        stripe_price_id=row.stripe_price_id,
        plan_type=row.plan_type,
        status=row.status,
        current_period_start=row.current_period_start,
        current_period_end=row.current_period_end,
        cancel_at_period_end=bool(row.cancel_at_period_end),
        canceled_at=row.canceled_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )

    return SubscriptionStatus(
        has_subscription=True,
        subscription=subscription,
        plan_type=subscription.plan_type,
        status=subscription.status,
        current_period_end=subscription.current_period_end,
        cancel_at_period_end=subscription.cancel_at_period_end,
    )


@router.post("/portal", response_model=PortalResponse)
async def create_portal_session(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a Stripe Customer Portal session."""
    if not STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe is not configured",
        )

    # Get customer ID
    result = await db.execute(
        text("SELECT stripe_customer_id FROM stripe_customers WHERE user_id = :user_id"),
        {"user_id": user_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Stripe customer found",
        )

    stripe = get_stripe()
    session = stripe.billing_portal.Session.create(
        customer=row.stripe_customer_id,
        return_url=os.getenv("FRONTEND_URL", "http://localhost:5173") + "/profile",
    )

    return PortalResponse(portal_url=session.url)


@router.post("/send-reminders")
async def send_subscription_reminders(
    db: AsyncSession = Depends(get_db),
    x_cron_secret: str | None = Header(default=None),
):
    """Send renewal reminders for subscriptions expiring soon.

    This endpoint should be called by a cron job (e.g., n8n scheduled workflow).
    It sends reminders for:
    - Subscriptions renewing in 7 days
    - Subscriptions renewing in 3 days
    - Subscriptions expiring soon (cancel_at_period_end=true)
    """
    import os
    cron_secret = os.getenv("N8N_WEBHOOK_SECRET", "")
    if cron_secret and x_cron_secret != cron_secret:
        raise HTTPException(status_code=403, detail="Invalid cron secret")

    now = datetime.now(timezone.utc)
    results = {"reminders_sent": 0, "errors": 0}

    # Get subscriptions expiring in 3 or 7 days
    for days in [7, 3]:
        target_date = (now + timedelta(days=days)).date().isoformat()
        next_day = (now + timedelta(days=days + 1)).date().isoformat()

        result = await db.execute(
            text("""
                SELECT u.email, u.name, s.plan_type, s.current_period_end,
                       s.cancel_at_period_end
                FROM subscriptions s
                JOIN users u ON u.id = s.user_id
                WHERE s.status = 'active'
                  AND date(s.current_period_end) >= :target_date
                  AND date(s.current_period_end) < :next_day
            """),
            {"target_date": target_date, "next_day": next_day},
        )
        rows = result.fetchall()

        for row in rows:
            reminder_type = "expiring_soon" if row.cancel_at_period_end else "upcoming_renewal"
            amount = 45.0 if row.plan_type == "annual" else 5.99

            success = await send_payment_reminder(
                user_email=row.email,
                user_name=row.name,
                plan_type=row.plan_type,
                amount_due=amount,
                due_date=row.current_period_end,
                days_until_due=days,
                reminder_type=reminder_type,
            )

            if success:
                results["reminders_sent"] += 1
            else:
                results["errors"] += 1

    return results


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle Stripe webhook events."""
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook secret not configured",
        )

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    stripe = get_stripe()
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        await handle_checkout_completed(data, db)
    elif event_type == "customer.subscription.created":
        await handle_subscription_created(data, db)
    elif event_type == "customer.subscription.updated":
        await handle_subscription_updated(data, db)
    elif event_type == "customer.subscription.deleted":
        await handle_subscription_deleted(data, db)
    elif event_type == "invoice.paid":
        await handle_invoice_paid(data, db)
    elif event_type == "invoice.payment_failed":
        await handle_payment_failed(data, db)

    return {"status": "success"}


async def handle_checkout_completed(data: dict, db: AsyncSession):
    """Handle checkout.session.completed event."""
    # Subscription is created via customer.subscription.created
    pass


async def handle_subscription_created(data: dict, db: AsyncSession):
    """Handle customer.subscription.created event."""
    customer_id = data["customer"]

    # Get user_id from stripe_customers
    result = await db.execute(
        text("SELECT user_id FROM stripe_customers WHERE stripe_customer_id = :customer_id"),
        {"customer_id": customer_id},
    )
    row = result.fetchone()
    if not row:
        return

    user_id = row.user_id
    now = datetime.now(timezone.utc).isoformat()

    # Determine plan type from price
    price_id = data["items"]["data"][0]["price"]["id"]
    plan_type = "annual" if price_id == STRIPE_PRICE_ANNUAL else "monthly"

    # Insert subscription
    await db.execute(
        text("""
            INSERT INTO subscriptions (
                id, user_id, stripe_subscription_id, stripe_price_id, plan_type,
                status, current_period_start, current_period_end,
                cancel_at_period_end, created_at, updated_at
            ) VALUES (
                :id, :user_id, :stripe_subscription_id, :stripe_price_id, :plan_type,
                :status, :current_period_start, :current_period_end,
                :cancel_at_period_end, :created_at, :updated_at
            )
        """),
        {
            "id": str(uuid4()),
            "user_id": user_id,
            "stripe_subscription_id": data["id"],
            "stripe_price_id": price_id,
            "plan_type": plan_type,
            "status": data["status"],
            "current_period_start": datetime.fromtimestamp(
                data["current_period_start"], tz=timezone.utc
            ).isoformat(),
            "current_period_end": datetime.fromtimestamp(
                data["current_period_end"], tz=timezone.utc
            ).isoformat(),
            "cancel_at_period_end": 1 if data.get("cancel_at_period_end") else 0,
            "created_at": now,
            "updated_at": now,
        },
    )
    await db.commit()


async def handle_subscription_updated(data: dict, db: AsyncSession):
    """Handle customer.subscription.updated event."""
    stripe_sub_id = data["id"]
    now = datetime.now(timezone.utc).isoformat()

    # Determine plan type from price
    price_id = data["items"]["data"][0]["price"]["id"]
    plan_type = "annual" if price_id == STRIPE_PRICE_ANNUAL else "monthly"

    await db.execute(
        text("""
            UPDATE subscriptions SET
                stripe_price_id = :stripe_price_id,
                plan_type = :plan_type,
                status = :status,
                current_period_start = :current_period_start,
                current_period_end = :current_period_end,
                cancel_at_period_end = :cancel_at_period_end,
                canceled_at = :canceled_at,
                updated_at = :updated_at
            WHERE stripe_subscription_id = :stripe_subscription_id
        """),
        {
            "stripe_subscription_id": stripe_sub_id,
            "stripe_price_id": price_id,
            "plan_type": plan_type,
            "status": data["status"],
            "current_period_start": datetime.fromtimestamp(
                data["current_period_start"], tz=timezone.utc
            ).isoformat(),
            "current_period_end": datetime.fromtimestamp(
                data["current_period_end"], tz=timezone.utc
            ).isoformat(),
            "cancel_at_period_end": 1 if data.get("cancel_at_period_end") else 0,
            "canceled_at": datetime.fromtimestamp(
                data["canceled_at"], tz=timezone.utc
            ).isoformat() if data.get("canceled_at") else None,
            "updated_at": now,
        },
    )
    await db.commit()


async def handle_subscription_deleted(data: dict, db: AsyncSession):
    """Handle customer.subscription.deleted event."""
    stripe_sub_id = data["id"]
    now = datetime.now(timezone.utc).isoformat()

    await db.execute(
        text("""
            UPDATE subscriptions SET
                status = 'canceled',
                canceled_at = :canceled_at,
                updated_at = :updated_at
            WHERE stripe_subscription_id = :stripe_subscription_id
        """),
        {
            "stripe_subscription_id": stripe_sub_id,
            "canceled_at": now,
            "updated_at": now,
        },
    )
    await db.commit()


async def handle_invoice_paid(data: dict, db: AsyncSession):
    """Handle invoice.paid event - send confirmation and invoice emails."""
    customer_id = data.get("customer")
    subscription_id = data.get("subscription")

    if not customer_id or not subscription_id:
        return

    # Get user info
    result = await db.execute(
        text("""
            SELECT u.email, u.name, sc.user_id
            FROM stripe_customers sc
            JOIN users u ON u.id = sc.user_id
            WHERE sc.stripe_customer_id = :customer_id
        """),
        {"customer_id": customer_id},
    )
    row = result.fetchone()
    if not row:
        return

    # Get subscription info
    sub_result = await db.execute(
        text("SELECT plan_type FROM subscriptions WHERE stripe_subscription_id = :sub_id"),
        {"sub_id": subscription_id},
    )
    sub_row = sub_result.fetchone()
    plan_type = sub_row.plan_type if sub_row else "monthly"

    # Extract invoice details
    amount = data.get("amount_paid", 0) / 100  # Convert from cents
    currency = data.get("currency", "eur").upper()
    invoice_number = data.get("number", "")
    invoice_pdf_url = data.get("invoice_pdf", "")
    period_start = datetime.fromtimestamp(
        data.get("period_start", 0), tz=timezone.utc
    ).isoformat() if data.get("period_start") else None
    period_end = datetime.fromtimestamp(
        data.get("period_end", 0), tz=timezone.utc
    ).isoformat() if data.get("period_end") else None

    # Send payment confirmation
    await send_payment_confirmation(
        user_email=row.email,
        user_name=row.name,
        plan_type=plan_type,
        amount=amount,
        currency=currency,
        subscription_id=subscription_id,
        period_end=period_end,
    )

    # Send invoice
    await send_invoice(
        user_email=row.email,
        user_name=row.name,
        plan_type=plan_type,
        invoice_number=invoice_number,
        amount=amount,
        currency=currency,
        period_start=period_start,
        period_end=period_end,
        invoice_pdf_url=invoice_pdf_url,
        stripe_invoice_id=data.get("id"),
    )


async def handle_payment_failed(data: dict, db: AsyncSession):
    """Handle invoice.payment_failed event."""
    subscription_id = data.get("subscription")
    customer_id = data.get("customer")

    if not subscription_id:
        return

    now = datetime.now(timezone.utc).isoformat()

    await db.execute(
        text("""
            UPDATE subscriptions SET
                status = 'past_due',
                updated_at = :updated_at
            WHERE stripe_subscription_id = :stripe_subscription_id
        """),
        {
            "stripe_subscription_id": subscription_id,
            "updated_at": now,
        },
    )
    await db.commit()

    # Send payment failed reminder
    if customer_id:
        result = await db.execute(
            text("""
                SELECT u.email, u.name, s.plan_type
                FROM stripe_customers sc
                JOIN users u ON u.id = sc.user_id
                LEFT JOIN subscriptions s ON s.stripe_subscription_id = :sub_id
                WHERE sc.stripe_customer_id = :customer_id
            """),
            {"customer_id": customer_id, "sub_id": subscription_id},
        )
        row = result.fetchone()
        if row:
            amount_due = data.get("amount_due", 0) / 100
            await send_payment_reminder(
                user_email=row.email,
                user_name=row.name,
                plan_type=row.plan_type or "monthly",
                amount_due=amount_due,
                reminder_type="payment_failed",
            )
