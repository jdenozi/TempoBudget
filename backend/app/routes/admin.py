# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Admin routes for user and subscription management."""

import io
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_admin
from ..database import get_db
from ..models.subscription import (
    AdminQuote,
    AdminUserInfo,
    CreateQuoteRequest,
    Subscription,
    SubscriptionStats,
    UpdateQuoteRequest,
)

router = APIRouter()


# ────────────────────────────── Users ──────────────────────────────


@router.get("/users", response_model=list[AdminUserInfo])
async def list_users(
    admin_id: str = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all users with their subscription status."""
    result = await db.execute(
        text("""
            SELECT u.id, u.email, u.name, u.is_admin, u.created_at,
                   s.id as sub_id, s.stripe_subscription_id, s.stripe_price_id,
                   s.plan_type, s.status as sub_status, s.current_period_start,
                   s.current_period_end, s.cancel_at_period_end, s.canceled_at,
                   s.created_at as sub_created_at, s.updated_at as sub_updated_at
            FROM users u
            LEFT JOIN subscriptions s ON u.id = s.user_id
                AND s.id = (
                    SELECT id FROM subscriptions
                    WHERE user_id = u.id
                    ORDER BY created_at DESC LIMIT 1
                )
            ORDER BY u.created_at DESC
        """)
    )
    rows = result.fetchall()

    users = []
    for row in rows:
        subscription = None
        if row.sub_id:
            subscription = Subscription(
                id=row.sub_id,
                user_id=row.id,
                stripe_subscription_id=row.stripe_subscription_id,
                stripe_price_id=row.stripe_price_id,
                plan_type=row.plan_type,
                status=row.sub_status,
                current_period_start=row.current_period_start,
                current_period_end=row.current_period_end,
                cancel_at_period_end=bool(row.cancel_at_period_end),
                canceled_at=row.canceled_at,
                created_at=row.sub_created_at,
                updated_at=row.sub_updated_at,
            )

        users.append(AdminUserInfo(
            id=row.id,
            email=row.email,
            name=row.name,
            is_admin=bool(row.is_admin),
            created_at=row.created_at,
            subscription=subscription,
        ))

    return users


@router.get("/users/{user_id}", response_model=AdminUserInfo)
async def get_user(
    user_id: str,
    admin_id: str = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific user's details."""
    result = await db.execute(
        text("""
            SELECT u.id, u.email, u.name, u.is_admin, u.created_at,
                   s.id as sub_id, s.stripe_subscription_id, s.stripe_price_id,
                   s.plan_type, s.status as sub_status, s.current_period_start,
                   s.current_period_end, s.cancel_at_period_end, s.canceled_at,
                   s.created_at as sub_created_at, s.updated_at as sub_updated_at
            FROM users u
            LEFT JOIN subscriptions s ON u.id = s.user_id
                AND s.id = (
                    SELECT id FROM subscriptions
                    WHERE user_id = u.id
                    ORDER BY created_at DESC LIMIT 1
                )
            WHERE u.id = :user_id
        """),
        {"user_id": user_id},
    )
    row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    subscription = None
    if row.sub_id:
        subscription = Subscription(
            id=row.sub_id,
            user_id=row.id,
            stripe_subscription_id=row.stripe_subscription_id,
            stripe_price_id=row.stripe_price_id,
            plan_type=row.plan_type,
            status=row.sub_status,
            current_period_start=row.current_period_start,
            current_period_end=row.current_period_end,
            cancel_at_period_end=bool(row.cancel_at_period_end),
            canceled_at=row.canceled_at,
            created_at=row.sub_created_at,
            updated_at=row.sub_updated_at,
        )

    return AdminUserInfo(
        id=row.id,
        email=row.email,
        name=row.name,
        is_admin=bool(row.is_admin),
        created_at=row.created_at,
        subscription=subscription,
    )


# ────────────────────────────── Subscriptions ──────────────────────────────


@router.get("/subscriptions", response_model=list[Subscription])
async def list_subscriptions(
    admin_id: str = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all subscriptions."""
    result = await db.execute(
        text("""
            SELECT * FROM subscriptions
            ORDER BY created_at DESC
        """)
    )
    rows = result.fetchall()

    return [
        Subscription(
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
        for row in rows
    ]


@router.get("/subscriptions/stats", response_model=SubscriptionStats)
async def get_subscription_stats(
    admin_id: str = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get subscription statistics (MRR, ARR, etc.)."""
    # Total users
    result = await db.execute(text("SELECT COUNT(*) as count FROM users"))
    total_users = result.fetchone().count

    # Subscribers and active subscriptions
    result = await db.execute(
        text("""
            SELECT
                COUNT(DISTINCT user_id) as total_subscribers,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN status = 'active' AND plan_type = 'monthly' THEN 1 ELSE 0 END) as monthly,
                SUM(CASE WHEN status = 'active' AND plan_type = 'annual' THEN 1 ELSE 0 END) as annual
            FROM subscriptions
        """)
    )
    row = result.fetchone()
    total_subscribers = row.total_subscribers or 0
    active_subscriptions = row.active or 0
    monthly_subscribers = row.monthly or 0
    annual_subscribers = row.annual or 0

    # Calculate MRR (Monthly Recurring Revenue)
    monthly_price = 5.99
    annual_price = 45.0
    mrr = (monthly_subscribers * monthly_price) + (annual_subscribers * (annual_price / 12))
    arr = mrr * 12

    # Churn rate (canceled in last 30 days / active at start of period)
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    result = await db.execute(
        text("""
            SELECT COUNT(*) as churned FROM subscriptions
            WHERE status = 'canceled' AND canceled_at >= :since
        """),
        {"since": thirty_days_ago},
    )
    churned = result.fetchone().churned or 0

    base_for_churn = active_subscriptions + churned
    churn_rate = (churned / base_for_churn * 100) if base_for_churn > 0 else 0.0

    return SubscriptionStats(
        total_users=total_users,
        total_subscribers=total_subscribers,
        active_subscriptions=active_subscriptions,
        monthly_subscribers=monthly_subscribers,
        annual_subscribers=annual_subscribers,
        mrr=round(mrr, 2),
        arr=round(arr, 2),
        churn_rate=round(churn_rate, 2),
    )


# ────────────────────────────── Quotes ──────────────────────────────


def _row_to_quote(row) -> AdminQuote:
    """Map a database row to an AdminQuote model."""
    return AdminQuote(
        id=row.id,
        created_by_user_id=row.created_by_user_id,
        prospect_name=row.prospect_name,
        prospect_email=row.prospect_email,
        prospect_company=row.prospect_company,
        plan_type=row.plan_type,
        quantity=row.quantity,
        unit_price=row.unit_price,
        total=row.total,
        valid_until=row.valid_until,
        notes=row.notes,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("/quotes", response_model=list[AdminQuote])
async def list_quotes(
    admin_id: str = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all quotes."""
    result = await db.execute(
        text("SELECT * FROM admin_quotes ORDER BY created_at DESC")
    )
    return [_row_to_quote(row) for row in result.fetchall()]


@router.post("/quotes", response_model=AdminQuote, status_code=status.HTTP_201_CREATED)
async def create_quote(
    request: CreateQuoteRequest,
    admin_id: str = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new quote."""
    now = datetime.now(timezone.utc)
    quote_id = str(uuid4())
    total = request.unit_price * request.quantity
    valid_until = (now + timedelta(days=request.valid_days)).isoformat()

    await db.execute(
        text("""
            INSERT INTO admin_quotes (
                id, created_by_user_id, prospect_name, prospect_email,
                prospect_company, plan_type, quantity, unit_price, total,
                valid_until, notes, status, created_at, updated_at
            ) VALUES (
                :id, :created_by_user_id, :prospect_name, :prospect_email,
                :prospect_company, :plan_type, :quantity, :unit_price, :total,
                :valid_until, :notes, 'draft', :created_at, :updated_at
            )
        """),
        {
            "id": quote_id,
            "created_by_user_id": admin_id,
            "prospect_name": request.prospect_name,
            "prospect_email": request.prospect_email,
            "prospect_company": request.prospect_company,
            "plan_type": request.plan_type,
            "quantity": request.quantity,
            "unit_price": request.unit_price,
            "total": total,
            "valid_until": valid_until,
            "notes": request.notes,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        },
    )
    await db.commit()

    result = await db.execute(
        text("SELECT * FROM admin_quotes WHERE id = :id"),
        {"id": quote_id},
    )
    return _row_to_quote(result.fetchone())


@router.get("/quotes/{quote_id}", response_model=AdminQuote)
async def get_quote(
    quote_id: str,
    admin_id: str = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific quote."""
    result = await db.execute(
        text("SELECT * FROM admin_quotes WHERE id = :id"),
        {"id": quote_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Quote not found")
    return _row_to_quote(row)


@router.put("/quotes/{quote_id}", response_model=AdminQuote)
async def update_quote(
    quote_id: str,
    request: UpdateQuoteRequest,
    admin_id: str = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a quote."""
    # Get existing quote
    result = await db.execute(
        text("SELECT * FROM admin_quotes WHERE id = :id"),
        {"id": quote_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Quote not found")

    # Build update fields
    updates = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if request.prospect_name is not None:
        updates["prospect_name"] = request.prospect_name
    if request.prospect_email is not None:
        updates["prospect_email"] = request.prospect_email
    if request.prospect_company is not None:
        updates["prospect_company"] = request.prospect_company
    if request.plan_type is not None:
        updates["plan_type"] = request.plan_type
    if request.quantity is not None:
        updates["quantity"] = request.quantity
    if request.unit_price is not None:
        updates["unit_price"] = request.unit_price
    if request.valid_until is not None:
        updates["valid_until"] = request.valid_until
    if request.notes is not None:
        updates["notes"] = request.notes
    if request.status is not None:
        updates["status"] = request.status

    # Recalculate total if quantity or unit_price changed
    quantity = updates.get("quantity", row.quantity)
    unit_price = updates.get("unit_price", row.unit_price)
    updates["total"] = quantity * unit_price

    # Build SET clause
    set_clause = ", ".join(f"{k} = :{k}" for k in updates.keys())
    updates["id"] = quote_id

    await db.execute(
        text(f"UPDATE admin_quotes SET {set_clause} WHERE id = :id"),
        updates,
    )
    await db.commit()

    result = await db.execute(
        text("SELECT * FROM admin_quotes WHERE id = :id"),
        {"id": quote_id},
    )
    return _row_to_quote(result.fetchone())


@router.delete("/quotes/{quote_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quote(
    quote_id: str,
    admin_id: str = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a quote."""
    result = await db.execute(
        text("SELECT id FROM admin_quotes WHERE id = :id"),
        {"id": quote_id},
    )
    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Quote not found")

    await db.execute(
        text("DELETE FROM admin_quotes WHERE id = :id"),
        {"id": quote_id},
    )
    await db.commit()


@router.get("/quotes/{quote_id}/pdf")
async def download_quote_pdf(
    quote_id: str,
    admin_id: str = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Generate and download a quote PDF."""
    result = await db.execute(
        text("SELECT * FROM admin_quotes WHERE id = :id"),
        {"id": quote_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Quote not found")

    quote = _row_to_quote(row)

    # Generate simple HTML for the quote
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .header {{ text-align: center; margin-bottom: 40px; }}
            .header h1 {{ color: #2563eb; margin-bottom: 5px; }}
            .info {{ margin-bottom: 30px; }}
            .info p {{ margin: 5px 0; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #f8f9fa; }}
            .total {{ font-size: 1.2em; font-weight: bold; text-align: right; }}
            .footer {{ margin-top: 40px; font-size: 0.9em; color: #666; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Tempo Budget</h1>
            <p>Devis #{quote.id[:8]}</p>
        </div>

        <div class="info">
            <p><strong>Client:</strong> {quote.prospect_name}</p>
            <p><strong>Email:</strong> {quote.prospect_email}</p>
            {"<p><strong>Société:</strong> " + quote.prospect_company + "</p>" if quote.prospect_company else ""}
            <p><strong>Date:</strong> {quote.created_at[:10]}</p>
            <p><strong>Valide jusqu'au:</strong> {quote.valid_until[:10]}</p>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Description</th>
                    <th>Qté</th>
                    <th>Prix unitaire</th>
                    <th>Total</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Abonnement Tempo Budget ({quote.plan_type})</td>
                    <td>{quote.quantity}</td>
                    <td>{quote.unit_price:.2f} €</td>
                    <td>{quote.total:.2f} €</td>
                </tr>
            </tbody>
        </table>

        <p class="total">Total: {quote.total:.2f} €</p>

        {"<div class='footer'><p><strong>Notes:</strong> " + quote.notes + "</p></div>" if quote.notes else ""}
    </body>
    </html>
    """

    # Use WeasyPrint to generate PDF
    from weasyprint import HTML

    pdf_buffer = io.BytesIO()
    HTML(string=html).write_pdf(pdf_buffer)
    pdf_bytes = pdf_buffer.getvalue()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="devis-{quote.id[:8]}.pdf"'
        },
    )
