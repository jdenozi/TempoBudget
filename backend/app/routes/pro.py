# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Pro (auto-entrepreneur) routes."""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user
from ..database import get_db
from ..models import (
    ProProfile, UpdateProProfile,
    ProClient, CreateProClient, UpdateProClient,
    ProCategory, CreateProCategory, UpdateProCategory,
    ProTransaction, CreateProTransaction, UpdateProTransaction,
    ProProduct, CreateProProduct, UpdateProProduct,
    ProTransactionItem, CreateProTransactionItem,
    ProCoupon, CreateProCoupon, UpdateProCoupon,
    ProGiftCard, CreateProGiftCard, ProGiftCardUsage,
    ProDashboardSummary,
    BatchToggleDeclared, DeclarationPeriodSummary,
    ProInvoiceSettings, UpdateProInvoiceSettings,
    ProInvoice, CreateProInvoice, UpdateProInvoice, UpdateProInvoiceStatus,
    ProInvoiceItem, CreateProInvoiceItem,
    ProQuote, CreateProQuote, UpdateProQuote, UpdateProQuoteStatus,
    ProQuoteItem, CreateProQuoteItem,
)
from ..pdf_generator import generate_invoice_pdf, generate_quote_pdf

router = APIRouter()

# Default pro categories seeded on first profile creation
DEFAULT_PRO_CATEGORIES = [
    ("Matériel", "expense"),
    ("Déplacement", "expense"),
    ("Logiciel / Abonnements", "expense"),
    ("Sous-traitance", "expense"),
    ("Fournitures", "expense"),
    ("Formation", "expense"),
    ("Téléphone / Internet", "expense"),
    ("Loyer pro", "expense"),
    ("Prestation de service", "income"),
    ("Vente de marchandises", "income"),
]


# ────────────────────────────── Profile ──────────────────────────────

@router.get("/profile", response_model=ProProfile)
async def get_or_create_profile(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the pro profile, creating it with default categories if it doesn't exist."""
    result = await db.execute(
        text("SELECT * FROM pro_profiles WHERE user_id = :user_id"),
        {"user_id": user_id},
    )
    row = result.fetchone()

    if row:
        return ProProfile(
            id=row.id, user_id=row.user_id, siret=row.siret,
            activity_type=row.activity_type, cotisation_rate=row.cotisation_rate,
            declaration_frequency=row.declaration_frequency,
            revenue_threshold=row.revenue_threshold,
            created_at=row.created_at, updated_at=row.updated_at,
        )

    # Create profile
    profile_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    await db.execute(
        text("""
            INSERT INTO pro_profiles (id, user_id, activity_type, cotisation_rate,
                                      declaration_frequency, revenue_threshold, created_at, updated_at)
            VALUES (:id, :user_id, 'services', 21.1, 'quarterly', 77700, :now, :now)
        """),
        {"id": profile_id, "user_id": user_id, "now": now},
    )

    # Seed default categories
    for name, cat_type in DEFAULT_PRO_CATEGORIES:
        await db.execute(
            text("""
                INSERT INTO pro_categories (id, user_id, name, type, is_default, created_at)
                VALUES (:id, :user_id, :name, :type, 1, :now)
            """),
            {"id": str(uuid4()), "user_id": user_id, "name": name, "type": cat_type, "now": now},
        )

    await db.commit()

    return ProProfile(
        id=profile_id, user_id=user_id, siret=None,
        activity_type="services", cotisation_rate=21.1,
        declaration_frequency="quarterly", revenue_threshold=77700,
        created_at=now, updated_at=now,
    )


@router.put("/profile", response_model=ProProfile)
async def update_profile(
    payload: UpdateProProfile,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the pro profile."""
    updates = []
    params: dict = {"user_id": user_id, "updated_at": datetime.now(timezone.utc).isoformat()}

    for field in ("siret", "activity_type", "cotisation_rate", "declaration_frequency", "revenue_threshold"):
        value = getattr(payload, field)
        if value is not None:
            updates.append(f"{field} = :{field}")
            params[field] = value

    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    updates.append("updated_at = :updated_at")
    query = f"UPDATE pro_profiles SET {', '.join(updates)} WHERE user_id = :user_id"
    await db.execute(text(query), params)
    await db.commit()

    result = await db.execute(
        text("SELECT * FROM pro_profiles WHERE user_id = :user_id"),
        {"user_id": user_id},
    )
    row = result.fetchone()
    return ProProfile(
        id=row.id, user_id=row.user_id, siret=row.siret,
        activity_type=row.activity_type, cotisation_rate=row.cotisation_rate,
        declaration_frequency=row.declaration_frequency,
        revenue_threshold=row.revenue_threshold,
        created_at=row.created_at, updated_at=row.updated_at,
    )


# ────────────────────────────── Clients ──────────────────────────────

@router.get("/clients", response_model=list[ProClient])
async def get_clients(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all pro clients."""
    result = await db.execute(
        text("SELECT * FROM pro_clients WHERE user_id = :user_id ORDER BY name"),
        {"user_id": user_id},
    )
    return [ProClient(
        id=r.id, user_id=r.user_id, name=r.name, email=r.email,
        phone=r.phone, address=r.address, notes=r.notes, created_at=r.created_at,
    ) for r in result.fetchall()]


@router.post("/clients", response_model=ProClient, status_code=status.HTTP_201_CREATED)
async def create_client(
    payload: CreateProClient,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new pro client."""
    client_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    await db.execute(
        text("""
            INSERT INTO pro_clients (id, user_id, name, email, phone, address, notes, created_at)
            VALUES (:id, :user_id, :name, :email, :phone, :address, :notes, :created_at)
        """),
        {
            "id": client_id, "user_id": user_id,
            "name": payload.name, "email": payload.email,
            "phone": payload.phone, "address": payload.address,
            "notes": payload.notes, "created_at": now,
        },
    )
    await db.commit()

    return ProClient(
        id=client_id, user_id=user_id, name=payload.name,
        email=payload.email, phone=payload.phone, address=payload.address,
        notes=payload.notes, created_at=now,
    )


@router.put("/clients/{client_id}", response_model=ProClient)
async def update_client(
    client_id: str,
    payload: UpdateProClient,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a pro client."""
    result = await db.execute(
        text("SELECT id FROM pro_clients WHERE id = :id AND user_id = :user_id"),
        {"id": client_id, "user_id": user_id},
    )
    if not result.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    updates = []
    params: dict = {"id": client_id, "user_id": user_id}
    for field in ("name", "email", "phone", "address", "notes"):
        value = getattr(payload, field)
        if value is not None:
            updates.append(f"{field} = :{field}")
            params[field] = value

    if updates:
        query = f"UPDATE pro_clients SET {', '.join(updates)} WHERE id = :id AND user_id = :user_id"
        await db.execute(text(query), params)
        await db.commit()

    result = await db.execute(
        text("SELECT * FROM pro_clients WHERE id = :id"),
        {"id": client_id},
    )
    r = result.fetchone()
    return ProClient(
        id=r.id, user_id=r.user_id, name=r.name, email=r.email,
        phone=r.phone, address=r.address, notes=r.notes, created_at=r.created_at,
    )


@router.delete("/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a pro client."""
    await db.execute(
        text("DELETE FROM pro_clients WHERE id = :id AND user_id = :user_id"),
        {"id": client_id, "user_id": user_id},
    )
    await db.commit()


# ────────────────────────────── Categories ──────────────────────────────

@router.get("/categories", response_model=list[ProCategory])
async def get_categories(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all pro categories."""
    result = await db.execute(
        text("SELECT * FROM pro_categories WHERE user_id = :user_id ORDER BY type, name"),
        {"user_id": user_id},
    )
    return [ProCategory(
        id=r.id, user_id=r.user_id, name=r.name, type=r.type,
        is_default=r.is_default, created_at=r.created_at,
    ) for r in result.fetchall()]


@router.post("/categories", response_model=ProCategory, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CreateProCategory,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new pro category."""
    cat_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    await db.execute(
        text("""
            INSERT INTO pro_categories (id, user_id, name, type, is_default, created_at)
            VALUES (:id, :user_id, :name, :type, 0, :created_at)
        """),
        {"id": cat_id, "user_id": user_id, "name": payload.name, "type": payload.type, "created_at": now},
    )
    await db.commit()

    return ProCategory(
        id=cat_id, user_id=user_id, name=payload.name,
        type=payload.type, is_default=0, created_at=now,
    )


@router.put("/categories/{category_id}", response_model=ProCategory)
async def update_category(
    category_id: str,
    payload: UpdateProCategory,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a pro category."""
    result = await db.execute(
        text("SELECT id FROM pro_categories WHERE id = :id AND user_id = :user_id"),
        {"id": category_id, "user_id": user_id},
    )
    if not result.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    updates = []
    params: dict = {"id": category_id, "user_id": user_id}
    for field in ("name", "type"):
        value = getattr(payload, field)
        if value is not None:
            updates.append(f"{field} = :{field}")
            params[field] = value

    if updates:
        query = f"UPDATE pro_categories SET {', '.join(updates)} WHERE id = :id AND user_id = :user_id"
        await db.execute(text(query), params)
        await db.commit()

    result = await db.execute(
        text("SELECT * FROM pro_categories WHERE id = :id"),
        {"id": category_id},
    )
    r = result.fetchone()
    return ProCategory(
        id=r.id, user_id=r.user_id, name=r.name, type=r.type,
        is_default=r.is_default, created_at=r.created_at,
    )


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a pro category (non-default only)."""
    result = await db.execute(
        text("SELECT is_default FROM pro_categories WHERE id = :id AND user_id = :user_id"),
        {"id": category_id, "user_id": user_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    if row.is_default:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete default category")

    await db.execute(
        text("DELETE FROM pro_categories WHERE id = :id AND user_id = :user_id"),
        {"id": category_id, "user_id": user_id},
    )
    await db.commit()


# ────────────────────────────── Products ──────────────────────────────

@router.get("/products", response_model=list[ProProduct])
async def get_products(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all pro products/services."""
    result = await db.execute(
        text("""
            SELECT p.*, c.name as category_name
            FROM pro_products p
            LEFT JOIN pro_categories c ON p.category_id = c.id
            WHERE p.user_id = :user_id
            ORDER BY p.name
        """),
        {"user_id": user_id},
    )
    return [ProProduct(
        id=r.id, user_id=r.user_id, name=r.name, type=r.type,
        default_price=r.default_price, category_id=r.category_id,
        created_at=r.created_at, category_name=r.category_name,
    ) for r in result.fetchall()]


@router.post("/products", response_model=ProProduct, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: CreateProProduct,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new pro product/service."""
    product_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    await db.execute(
        text("""
            INSERT INTO pro_products (id, user_id, name, type, default_price, category_id, created_at)
            VALUES (:id, :user_id, :name, :type, :default_price, :category_id, :created_at)
        """),
        {
            "id": product_id, "user_id": user_id,
            "name": payload.name, "type": payload.type,
            "default_price": payload.default_price,
            "category_id": payload.category_id, "created_at": now,
        },
    )
    await db.commit()

    # Fetch with join
    result = await db.execute(
        text("""
            SELECT p.*, c.name as category_name
            FROM pro_products p
            LEFT JOIN pro_categories c ON p.category_id = c.id
            WHERE p.id = :id
        """),
        {"id": product_id},
    )
    r = result.fetchone()
    return ProProduct(
        id=r.id, user_id=r.user_id, name=r.name, type=r.type,
        default_price=r.default_price, category_id=r.category_id,
        created_at=r.created_at, category_name=r.category_name,
    )


@router.put("/products/{product_id}", response_model=ProProduct)
async def update_product(
    product_id: str,
    payload: UpdateProProduct,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a pro product/service."""
    result = await db.execute(
        text("SELECT id FROM pro_products WHERE id = :id AND user_id = :user_id"),
        {"id": product_id, "user_id": user_id},
    )
    if not result.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    updates = []
    params: dict = {"id": product_id, "user_id": user_id}
    for field in ("name", "type", "default_price", "category_id"):
        value = getattr(payload, field)
        if value is not None:
            updates.append(f"{field} = :{field}")
            params[field] = value

    if updates:
        query = f"UPDATE pro_products SET {', '.join(updates)} WHERE id = :id AND user_id = :user_id"
        await db.execute(text(query), params)
        await db.commit()

    result = await db.execute(
        text("""
            SELECT p.*, c.name as category_name
            FROM pro_products p
            LEFT JOIN pro_categories c ON p.category_id = c.id
            WHERE p.id = :id
        """),
        {"id": product_id},
    )
    r = result.fetchone()
    return ProProduct(
        id=r.id, user_id=r.user_id, name=r.name, type=r.type,
        default_price=r.default_price, category_id=r.category_id,
        created_at=r.created_at, category_name=r.category_name,
    )


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a pro product/service."""
    await db.execute(
        text("DELETE FROM pro_products WHERE id = :id AND user_id = :user_id"),
        {"id": product_id, "user_id": user_id},
    )
    await db.commit()


# ────────────────────────────── Coupons ──────────────────────────────

@router.get("/coupons", response_model=list[ProCoupon])
async def get_coupons(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all pro coupons."""
    result = await db.execute(
        text("SELECT * FROM pro_coupons WHERE user_id = :user_id ORDER BY created_at DESC"),
        {"user_id": user_id},
    )
    return [ProCoupon(
        id=r.id, user_id=r.user_id, code=r.code, name=r.name,
        discount_type=r.discount_type, discount_value=r.discount_value,
        valid_from=r.valid_from, valid_until=r.valid_until,
        max_uses=r.max_uses, used_count=r.used_count,
        is_active=r.is_active, created_at=r.created_at,
    ) for r in result.fetchall()]


@router.post("/coupons", response_model=ProCoupon, status_code=status.HTTP_201_CREATED)
async def create_coupon(
    payload: CreateProCoupon,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new pro coupon."""
    coupon_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    await db.execute(
        text("""
            INSERT INTO pro_coupons (id, user_id, code, name, discount_type, discount_value,
                                     valid_from, valid_until, max_uses, used_count, is_active, created_at)
            VALUES (:id, :user_id, :code, :name, :discount_type, :discount_value,
                    :valid_from, :valid_until, :max_uses, 0, 1, :created_at)
        """),
        {
            "id": coupon_id, "user_id": user_id,
            "code": payload.code, "name": payload.name,
            "discount_type": payload.discount_type,
            "discount_value": payload.discount_value,
            "valid_from": payload.valid_from,
            "valid_until": payload.valid_until,
            "max_uses": payload.max_uses,
            "created_at": now,
        },
    )
    await db.commit()

    return ProCoupon(
        id=coupon_id, user_id=user_id, code=payload.code, name=payload.name,
        discount_type=payload.discount_type, discount_value=payload.discount_value,
        valid_from=payload.valid_from, valid_until=payload.valid_until,
        max_uses=payload.max_uses, used_count=0, is_active=1, created_at=now,
    )


@router.put("/coupons/{coupon_id}", response_model=ProCoupon)
async def update_coupon(
    coupon_id: str,
    payload: UpdateProCoupon,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a pro coupon."""
    result = await db.execute(
        text("SELECT id FROM pro_coupons WHERE id = :id AND user_id = :user_id"),
        {"id": coupon_id, "user_id": user_id},
    )
    if not result.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found")

    updates = []
    params: dict = {"id": coupon_id, "user_id": user_id}
    for field in ("code", "name", "discount_type", "discount_value", "valid_from", "valid_until", "max_uses", "is_active"):
        value = getattr(payload, field)
        if value is not None:
            updates.append(f"{field} = :{field}")
            params[field] = value

    if updates:
        query = f"UPDATE pro_coupons SET {', '.join(updates)} WHERE id = :id AND user_id = :user_id"
        await db.execute(text(query), params)
        await db.commit()

    result = await db.execute(
        text("SELECT * FROM pro_coupons WHERE id = :id"),
        {"id": coupon_id},
    )
    r = result.fetchone()
    return ProCoupon(
        id=r.id, user_id=r.user_id, code=r.code, name=r.name,
        discount_type=r.discount_type, discount_value=r.discount_value,
        valid_from=r.valid_from, valid_until=r.valid_until,
        max_uses=r.max_uses, used_count=r.used_count,
        is_active=r.is_active, created_at=r.created_at,
    )


@router.delete("/coupons/{coupon_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_coupon(
    coupon_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a pro coupon."""
    await db.execute(
        text("DELETE FROM pro_coupons WHERE id = :id AND user_id = :user_id"),
        {"id": coupon_id, "user_id": user_id},
    )
    await db.commit()


# ────────────────────────────── Gift Cards ──────────────────────────────

@router.get("/gift-cards", response_model=list[ProGiftCard])
async def get_gift_cards(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all pro gift cards."""
    result = await db.execute(
        text("""
            SELECT gc.*, c.name as client_name
            FROM pro_gift_cards gc
            LEFT JOIN pro_clients c ON gc.client_id = c.id
            WHERE gc.user_id = :user_id
            ORDER BY gc.created_at DESC
        """),
        {"user_id": user_id},
    )
    return [ProGiftCard(
        id=r.id, user_id=r.user_id, code=r.code,
        initial_amount=r.initial_amount, remaining_balance=r.remaining_balance,
        client_id=r.client_id, purchase_transaction_id=r.purchase_transaction_id,
        purchase_date=r.purchase_date, is_active=r.is_active,
        created_at=r.created_at, client_name=r.client_name,
    ) for r in result.fetchall()]


@router.post("/gift-cards", response_model=ProGiftCard, status_code=status.HTTP_201_CREATED)
async def create_gift_card(
    payload: CreateProGiftCard,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new pro gift card."""
    gc_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    await db.execute(
        text("""
            INSERT INTO pro_gift_cards (id, user_id, code, initial_amount, remaining_balance,
                                        client_id, purchase_date, is_active, created_at)
            VALUES (:id, :user_id, :code, :initial_amount, :remaining_balance,
                    :client_id, :purchase_date, 1, :created_at)
        """),
        {
            "id": gc_id, "user_id": user_id,
            "code": payload.code, "initial_amount": payload.initial_amount,
            "remaining_balance": payload.initial_amount,
            "client_id": payload.client_id,
            "purchase_date": payload.purchase_date,
            "created_at": now,
        },
    )
    await db.commit()

    return ProGiftCard(
        id=gc_id, user_id=user_id, code=payload.code,
        initial_amount=payload.initial_amount, remaining_balance=payload.initial_amount,
        client_id=payload.client_id, purchase_transaction_id=None,
        purchase_date=payload.purchase_date, is_active=1, created_at=now,
    )


@router.get("/gift-cards/{gift_card_id}", response_model=ProGiftCard)
async def get_gift_card(
    gift_card_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single gift card."""
    result = await db.execute(
        text("""
            SELECT gc.*, c.name as client_name
            FROM pro_gift_cards gc
            LEFT JOIN pro_clients c ON gc.client_id = c.id
            WHERE gc.id = :id AND gc.user_id = :user_id
        """),
        {"id": gift_card_id, "user_id": user_id},
    )
    r = result.fetchone()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gift card not found")
    return ProGiftCard(
        id=r.id, user_id=r.user_id, code=r.code,
        initial_amount=r.initial_amount, remaining_balance=r.remaining_balance,
        client_id=r.client_id, purchase_transaction_id=r.purchase_transaction_id,
        purchase_date=r.purchase_date, is_active=r.is_active,
        created_at=r.created_at, client_name=r.client_name,
    )


@router.get("/gift-cards/{gift_card_id}/usages", response_model=list[ProGiftCardUsage])
async def get_gift_card_usages(
    gift_card_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get usage history for a gift card."""
    # Verify ownership
    check = await db.execute(
        text("SELECT id FROM pro_gift_cards WHERE id = :id AND user_id = :user_id"),
        {"id": gift_card_id, "user_id": user_id},
    )
    if not check.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gift card not found")

    result = await db.execute(
        text("""
            SELECT u.*, t.title as transaction_title
            FROM pro_gift_card_usages u
            JOIN pro_transactions t ON u.transaction_id = t.id
            WHERE u.gift_card_id = :gift_card_id
            ORDER BY u.created_at DESC
        """),
        {"gift_card_id": gift_card_id},
    )
    return [ProGiftCardUsage(
        id=r.id, gift_card_id=r.gift_card_id, transaction_id=r.transaction_id,
        amount_used=r.amount_used, created_at=r.created_at,
        transaction_title=r.transaction_title,
    ) for r in result.fetchall()]


@router.delete("/gift-cards/{gift_card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_gift_card(
    gift_card_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a pro gift card."""
    await db.execute(
        text("DELETE FROM pro_gift_cards WHERE id = :id AND user_id = :user_id"),
        {"id": gift_card_id, "user_id": user_id},
    )
    await db.commit()


# ────────────────────────────── Transactions ──────────────────────────────

@router.get("/transactions", response_model=list[ProTransaction])
async def get_transactions(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    client_id: str | None = Query(None),
    category_id: str | None = Query(None),
    payment_method: str | None = Query(None),
    product_id: str | None = Query(None),
):
    """List pro transactions with optional filters."""
    conditions = ["t.user_id = :user_id"]
    params: dict = {"user_id": user_id}
    joins = ""

    if start_date:
        conditions.append("t.date >= :start_date")
        params["start_date"] = start_date
    if end_date:
        conditions.append("t.date <= :end_date")
        params["end_date"] = end_date
    if client_id:
        conditions.append("t.client_id = :client_id")
        params["client_id"] = client_id
    if category_id:
        conditions.append("t.category_id = :category_id")
        params["category_id"] = category_id
    if payment_method:
        conditions.append("t.payment_method = :payment_method")
        params["payment_method"] = payment_method
    if product_id:
        joins = "JOIN pro_transaction_items pti ON pti.transaction_id = t.id"
        conditions.append("pti.product_id = :product_id")
        params["product_id"] = product_id

    where = " AND ".join(conditions)
    result = await db.execute(
        text(f"""
            SELECT DISTINCT t.*, c.name as client_name, cat.name as category_name
            FROM pro_transactions t
            LEFT JOIN pro_clients c ON t.client_id = c.id
            LEFT JOIN pro_categories cat ON t.category_id = cat.id
            {joins}
            WHERE {where}
            ORDER BY t.date DESC
        """),
        params,
    )

    transactions = []
    for r in result.fetchall():
        # Fetch items for this transaction
        items_result = await db.execute(
            text("""
                SELECT ti.*, p.name as product_name
                FROM pro_transaction_items ti
                JOIN pro_products p ON ti.product_id = p.id
                WHERE ti.transaction_id = :tx_id
            """),
            {"tx_id": r.id},
        )
        items = [ProTransactionItem(
            id=i.id, transaction_id=i.transaction_id, product_id=i.product_id,
            quantity=i.quantity, unit_price=i.unit_price, created_at=i.created_at,
            product_name=i.product_name,
        ) for i in items_result.fetchall()]

        transactions.append(ProTransaction(
            id=r.id, user_id=r.user_id, client_id=r.client_id,
            category_id=r.category_id, title=r.title, amount=r.amount,
            transaction_type=r.transaction_type, date=r.date,
            payment_method=r.payment_method, comment=r.comment,
            discount_type=r.discount_type, discount_value=r.discount_value,
            coupon_id=r.coupon_id, gift_card_payment=r.gift_card_payment or 0,
            is_declared=r.is_declared if hasattr(r, 'is_declared') else 0,
            created_at=r.created_at, client_name=r.client_name,
            category_name=r.category_name, items=items,
        ))

    return transactions


@router.post("/transactions", response_model=ProTransaction, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    payload: CreateProTransaction,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new pro transaction. If items are provided, title and amount are auto-calculated."""
    tx_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    title = payload.title
    amount = payload.amount

    # If items provided, auto-generate title and calculate amount
    if payload.items:
        # Fetch product names for title generation
        product_ids = [item.product_id for item in payload.items]
        placeholders = ", ".join(f":pid{i}" for i in range(len(product_ids)))
        pparams = {f"pid{i}": pid for i, pid in enumerate(product_ids)}
        products_result = await db.execute(
            text(f"SELECT id, name FROM pro_products WHERE id IN ({placeholders})"),
            pparams,
        )
        product_names = {r.id: r.name for r in products_result.fetchall()}

        amount = sum(item.quantity * item.unit_price for item in payload.items)
        if not title:
            title = " + ".join(
                f"{product_names.get(item.product_id, '?')}" +
                (f" x{item.quantity}" if item.quantity > 1 else "")
                for item in payload.items
            )

    if amount <= 0 and not payload.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be positive")
    if not title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title is required")

    subtotal = amount
    discount_type = None
    discount_value = None
    coupon_id = None
    gift_card_payment = 0.0

    # 1. Apply coupon if provided
    if payload.coupon_id:
        coupon_result = await db.execute(
            text("SELECT * FROM pro_coupons WHERE id = :id AND user_id = :user_id"),
            {"id": payload.coupon_id, "user_id": user_id},
        )
        coupon = coupon_result.fetchone()
        if not coupon:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon not found")
        if not coupon.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon is inactive")
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if coupon.valid_from and today < coupon.valid_from:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon not yet valid")
        if coupon.valid_until and today > coupon.valid_until:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon has expired")
        if coupon.max_uses > 0 and coupon.used_count >= coupon.max_uses:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon max uses reached")

        discount_type = coupon.discount_type
        discount_value = coupon.discount_value
        coupon_id = coupon.id

        if coupon.discount_type == "percentage":
            subtotal -= subtotal * coupon.discount_value / 100
        else:
            subtotal -= coupon.discount_value

        # Increment used_count
        await db.execute(
            text("UPDATE pro_coupons SET used_count = used_count + 1 WHERE id = :id"),
            {"id": coupon.id},
        )

    # 2. Apply manual discount if no coupon
    elif payload.discount_type and payload.discount_value:
        discount_type = payload.discount_type
        discount_value = payload.discount_value
        if payload.discount_type == "percentage":
            subtotal -= subtotal * payload.discount_value / 100
        else:
            subtotal -= payload.discount_value

    subtotal = max(subtotal, 0)

    # 3. Apply gift card payment if provided
    if payload.gift_card_id and payload.gift_card_amount:
        gc_result = await db.execute(
            text("SELECT * FROM pro_gift_cards WHERE id = :id AND user_id = :user_id"),
            {"id": payload.gift_card_id, "user_id": user_id},
        )
        gc = gc_result.fetchone()
        if not gc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Gift card not found")
        if not gc.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Gift card is inactive")
        if gc.remaining_balance <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Gift card has no remaining balance")

        gift_card_payment = min(payload.gift_card_amount, gc.remaining_balance, subtotal)

        # Deduct from gift card balance
        new_balance = gc.remaining_balance - gift_card_payment
        await db.execute(
            text("UPDATE pro_gift_cards SET remaining_balance = :balance WHERE id = :id"),
            {"balance": round(new_balance, 2), "id": gc.id},
        )

    amount = max(subtotal, 0)

    await db.execute(
        text("""
            INSERT INTO pro_transactions (id, user_id, client_id, category_id, title,
                                          amount, transaction_type, date, payment_method, comment,
                                          discount_type, discount_value, coupon_id, gift_card_payment, created_at)
            VALUES (:id, :user_id, :client_id, :category_id, :title,
                    :amount, :transaction_type, :date, :payment_method, :comment,
                    :discount_type, :discount_value, :coupon_id, :gift_card_payment, :created_at)
        """),
        {
            "id": tx_id, "user_id": user_id,
            "client_id": payload.client_id, "category_id": payload.category_id,
            "title": title, "amount": round(amount, 2),
            "transaction_type": payload.transaction_type, "date": payload.date,
            "payment_method": payload.payment_method, "comment": payload.comment,
            "discount_type": discount_type, "discount_value": discount_value,
            "coupon_id": coupon_id, "gift_card_payment": round(gift_card_payment, 2),
            "created_at": now,
        },
    )

    # Insert items if provided
    for item in payload.items:
        await db.execute(
            text("""
                INSERT INTO pro_transaction_items (id, transaction_id, product_id, quantity, unit_price, created_at)
                VALUES (:id, :transaction_id, :product_id, :quantity, :unit_price, :created_at)
            """),
            {
                "id": str(uuid4()), "transaction_id": tx_id,
                "product_id": item.product_id, "quantity": item.quantity,
                "unit_price": item.unit_price, "created_at": now,
            },
        )

    # Record gift card usage if applicable
    if gift_card_payment > 0 and payload.gift_card_id:
        await db.execute(
            text("""
                INSERT INTO pro_gift_card_usages (id, gift_card_id, transaction_id, amount_used, created_at)
                VALUES (:id, :gift_card_id, :transaction_id, :amount_used, :created_at)
            """),
            {
                "id": str(uuid4()), "gift_card_id": payload.gift_card_id,
                "transaction_id": tx_id, "amount_used": round(gift_card_payment, 2),
                "created_at": now,
            },
        )

    await db.commit()

    # Fetch with joins + items
    result = await db.execute(
        text("""
            SELECT t.*, c.name as client_name, cat.name as category_name
            FROM pro_transactions t
            LEFT JOIN pro_clients c ON t.client_id = c.id
            LEFT JOIN pro_categories cat ON t.category_id = cat.id
            WHERE t.id = :id
        """),
        {"id": tx_id},
    )
    r = result.fetchone()

    items_result = await db.execute(
        text("""
            SELECT ti.*, p.name as product_name
            FROM pro_transaction_items ti
            JOIN pro_products p ON ti.product_id = p.id
            WHERE ti.transaction_id = :tx_id
        """),
        {"tx_id": tx_id},
    )
    items = [ProTransactionItem(
        id=i.id, transaction_id=i.transaction_id, product_id=i.product_id,
        quantity=i.quantity, unit_price=i.unit_price, created_at=i.created_at,
        product_name=i.product_name,
    ) for i in items_result.fetchall()]

    return ProTransaction(
        id=r.id, user_id=r.user_id, client_id=r.client_id,
        category_id=r.category_id, title=r.title, amount=r.amount,
        transaction_type=r.transaction_type, date=r.date,
        payment_method=r.payment_method, comment=r.comment,
        discount_type=r.discount_type, discount_value=r.discount_value,
        coupon_id=r.coupon_id, gift_card_payment=r.gift_card_payment or 0,
        created_at=r.created_at, client_name=r.client_name,
        category_name=r.category_name, items=items,
    )


@router.put("/transactions/declare", response_model=dict)
async def batch_toggle_declared(
    payload: BatchToggleDeclared,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Batch toggle is_declared on transactions."""
    placeholders = ", ".join(f":id{i}" for i in range(len(payload.transaction_ids)))
    params = {f"id{i}": tid for i, tid in enumerate(payload.transaction_ids)}
    params["user_id"] = user_id
    params["is_declared"] = payload.is_declared

    await db.execute(
        text(f"""
            UPDATE pro_transactions SET is_declared = :is_declared
            WHERE user_id = :user_id AND id IN ({placeholders})
        """),
        params,
    )
    await db.commit()
    return {"updated": len(payload.transaction_ids)}


@router.put("/transactions/{transaction_id}", response_model=ProTransaction)
async def update_transaction(
    transaction_id: str,
    payload: UpdateProTransaction,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a pro transaction."""
    result = await db.execute(
        text("SELECT id FROM pro_transactions WHERE id = :id AND user_id = :user_id"),
        {"id": transaction_id, "user_id": user_id},
    )
    if not result.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    updates = []
    params: dict = {"id": transaction_id, "user_id": user_id}
    for field in ("client_id", "category_id", "title", "amount", "transaction_type", "date", "payment_method", "comment"):
        value = getattr(payload, field)
        if value is not None:
            updates.append(f"{field} = :{field}")
            params[field] = value

    if updates:
        query = f"UPDATE pro_transactions SET {', '.join(updates)} WHERE id = :id AND user_id = :user_id"
        await db.execute(text(query), params)
        await db.commit()

    result = await db.execute(
        text("""
            SELECT t.*, c.name as client_name, cat.name as category_name
            FROM pro_transactions t
            LEFT JOIN pro_clients c ON t.client_id = c.id
            LEFT JOIN pro_categories cat ON t.category_id = cat.id
            WHERE t.id = :id
        """),
        {"id": transaction_id},
    )
    r = result.fetchone()
    return ProTransaction(
        id=r.id, user_id=r.user_id, client_id=r.client_id,
        category_id=r.category_id, title=r.title, amount=r.amount,
        transaction_type=r.transaction_type, date=r.date,
        payment_method=r.payment_method, comment=r.comment,
        discount_type=r.discount_type, discount_value=r.discount_value,
        coupon_id=r.coupon_id, gift_card_payment=r.gift_card_payment or 0,
        created_at=r.created_at, client_name=r.client_name,
        category_name=r.category_name,
    )


@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a pro transaction."""
    await db.execute(
        text("DELETE FROM pro_transactions WHERE id = :id AND user_id = :user_id"),
        {"id": transaction_id, "user_id": user_id},
    )
    await db.commit()


# ────────────────────────────── Dashboard ──────────────────────────────

@router.get("/dashboard", response_model=ProDashboardSummary)
async def get_dashboard(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get pro dashboard summary with aggregated data."""
    now = datetime.now(timezone.utc)
    year_start = f"{now.year}-01-01"
    month_start = f"{now.year}-{now.month:02d}-01"

    # Quarter start
    quarter_month = ((now.month - 1) // 3) * 3 + 1
    quarter_start = f"{now.year}-{quarter_month:02d}-01"

    result = await db.execute(
        text("""
            SELECT
                COALESCE(SUM(CASE WHEN transaction_type = 'income' AND date >= :month_start THEN amount END), 0) as ca_month,
                COALESCE(SUM(CASE WHEN transaction_type = 'income' AND date >= :quarter_start THEN amount END), 0) as ca_quarter,
                COALESCE(SUM(CASE WHEN transaction_type = 'income' AND date >= :year_start THEN amount END), 0) as ca_year,
                COALESCE(SUM(CASE WHEN transaction_type = 'expense' AND date >= :month_start THEN amount END), 0) as expenses_month,
                COALESCE(SUM(CASE WHEN transaction_type = 'expense' AND date >= :quarter_start THEN amount END), 0) as expenses_quarter,
                COALESCE(SUM(CASE WHEN transaction_type = 'expense' AND date >= :year_start THEN amount END), 0) as expenses_year
            FROM pro_transactions
            WHERE user_id = :user_id AND date >= :year_start
        """),
        {
            "user_id": user_id,
            "year_start": year_start,
            "quarter_start": quarter_start,
            "month_start": month_start,
        },
    )
    row = result.fetchone()

    # Get cotisation rate and threshold from profile
    profile_result = await db.execute(
        text("SELECT cotisation_rate, revenue_threshold FROM pro_profiles WHERE user_id = :user_id"),
        {"user_id": user_id},
    )
    profile = profile_result.fetchone()
    rate = profile.cotisation_rate if profile else 21.1
    threshold = profile.revenue_threshold if profile else 77700

    ca_year = row.ca_year
    cotisations = ca_year * (rate / 100)
    threshold_pct = (ca_year / threshold * 100) if threshold > 0 else 0

    return ProDashboardSummary(
        ca_month=row.ca_month,
        ca_quarter=row.ca_quarter,
        ca_year=ca_year,
        expenses_month=row.expenses_month,
        expenses_quarter=row.expenses_quarter,
        expenses_year=row.expenses_year,
        net_month=row.ca_month - row.expenses_month,
        cotisations_estimated=round(cotisations, 2),
        threshold_percentage=round(threshold_pct, 1),
    )


# ────────────────────────────── Declaration Periods ──────────────────────────────


MONTH_LABELS_FR = [
    "", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
]


@router.get("/declaration/periods", response_model=list[DeclarationPeriodSummary])
async def get_declaration_periods(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    year: int | None = Query(None),
):
    """Get declaration period summaries for the given year (defaults to current year)."""
    from datetime import date
    if year is None:
        year = date.today().year

    # Get profile for frequency and cotisation rate
    profile_result = await db.execute(
        text("SELECT declaration_frequency, cotisation_rate FROM pro_profiles WHERE user_id = :user_id"),
        {"user_id": user_id},
    )
    profile = profile_result.fetchone()
    frequency = profile.declaration_frequency if profile else "quarterly"
    rate = profile.cotisation_rate if profile else 21.1

    # Build periods
    periods = []
    if frequency == "monthly":
        for m in range(1, 13):
            start = f"{year}-{m:02d}-01"
            if m == 12:
                end = f"{year}-12-31"
            else:
                end = f"{year}-{m + 1:02d}-01"
            periods.append((start, end, f"{MONTH_LABELS_FR[m]} {year}"))
    else:
        for q in range(1, 5):
            sm = (q - 1) * 3 + 1
            start = f"{year}-{sm:02d}-01"
            if q == 4:
                end = f"{year + 1}-01-01"
            else:
                em = sm + 3
                end = f"{year}-{em:02d}-01"
            periods.append((start, end, f"T{q} {year}"))

    summaries = []
    for p_start, p_end, label in periods:
        result = await db.execute(
            text("""
                SELECT
                    COUNT(*) as total_tx,
                    COALESCE(SUM(amount), 0) as total_income,
                    COALESCE(SUM(CASE WHEN is_declared = 1 THEN amount END), 0) as declared_income,
                    COALESCE(SUM(CASE WHEN is_declared = 1 THEN 1 ELSE 0 END), 0) as declared_tx
                FROM pro_transactions
                WHERE user_id = :user_id
                  AND transaction_type = 'income'
                  AND date >= :start AND date < :end
            """),
            {"user_id": user_id, "start": p_start, "end": p_end},
        )
        row = result.fetchone()
        summaries.append(DeclarationPeriodSummary(
            period_start=p_start,
            period_end=p_end,
            period_label=label,
            total_income=row.total_income,
            declared_income=row.declared_income,
            undeclared_income=row.total_income - row.declared_income,
            total_transactions=row.total_tx,
            declared_transactions=row.declared_tx,
            cotisations_estimated=round(row.declared_income * (rate / 100), 2),
        ))

    return summaries


# ────────────────────────────── Invoice Helpers ──────────────────────────────


async def _get_or_create_invoice_settings(db: AsyncSession, user_id: str) -> dict:
    """Get or create default invoice settings for a user."""
    result = await db.execute(
        text("SELECT * FROM pro_invoice_settings WHERE user_id = :user_id"),
        {"user_id": user_id},
    )
    row = result.fetchone()
    if row:
        return dict(row._mapping)
    now = datetime.now(timezone.utc).isoformat()
    settings_id = str(uuid4())
    await db.execute(
        text("""INSERT INTO pro_invoice_settings (id, user_id, created_at, updated_at)
                VALUES (:id, :user_id, :now, :now)"""),
        {"id": settings_id, "user_id": user_id, "now": now},
    )
    await db.commit()
    result = await db.execute(
        text("SELECT * FROM pro_invoice_settings WHERE id = :id"),
        {"id": settings_id},
    )
    return dict(result.fetchone()._mapping)


async def _generate_number(db: AsyncSession, user_id: str, doc_type: str) -> str:
    """Generate next document number like F-2026-001 and increment counter."""
    settings = await _get_or_create_invoice_settings(db, user_id)
    year = datetime.now(timezone.utc).year
    if doc_type == "invoice":
        prefix = settings["invoice_prefix"]
        seq = settings["next_invoice_number"]
        await db.execute(
            text("UPDATE pro_invoice_settings SET next_invoice_number = next_invoice_number + 1, updated_at = :now WHERE user_id = :user_id"),
            {"user_id": user_id, "now": datetime.now(timezone.utc).isoformat()},
        )
    else:
        prefix = settings["quote_prefix"]
        seq = settings["next_quote_number"]
        await db.execute(
            text("UPDATE pro_invoice_settings SET next_quote_number = next_quote_number + 1, updated_at = :now WHERE user_id = :user_id"),
            {"user_id": user_id, "now": datetime.now(timezone.utc).isoformat()},
        )
    return f"{prefix}-{year}-{seq:03d}"


def _calc_totals(items: list, discount_type: str | None, discount_value: float) -> tuple[float, float]:
    """Calculate subtotal and total from items and discount."""
    subtotal = sum(i.quantity * i.unit_price for i in items)
    total = subtotal
    if discount_type == "percentage" and discount_value:
        total = subtotal * (1 - discount_value / 100)
    elif discount_type == "fixed" and discount_value:
        total = subtotal - discount_value
    return round(subtotal, 2), round(max(total, 0), 2)


async def _get_profile_for_pdf(db: AsyncSession, user_id: str) -> dict:
    """Get profile + user info for PDF generation."""
    result = await db.execute(
        text("""SELECT u.name, u.email, u.phone, p.siret
                FROM users u LEFT JOIN pro_profiles p ON p.user_id = u.id
                WHERE u.id = :user_id"""),
        {"user_id": user_id},
    )
    row = result.fetchone()
    if not row:
        return {}
    return dict(row._mapping)


async def _get_client_dict(db: AsyncSession, client_id: str) -> dict:
    result = await db.execute(
        text("SELECT * FROM pro_clients WHERE id = :id"), {"id": client_id}
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Client not found")
    return dict(row._mapping)


# ────────────────────────────── Invoice Settings ──────────────────────────────


@router.get("/invoice-settings", response_model=ProInvoiceSettings)
async def get_invoice_settings(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get or create invoice settings."""
    settings = await _get_or_create_invoice_settings(db, user_id)
    return ProInvoiceSettings(**settings)


@router.put("/invoice-settings", response_model=ProInvoiceSettings)
async def update_invoice_settings(
    payload: UpdateProInvoiceSettings,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update invoice settings."""
    await _get_or_create_invoice_settings(db, user_id)
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    set_clause = ", ".join(f"{k} = :{k}" for k in updates)
    updates["user_id"] = user_id
    await db.execute(
        text(f"UPDATE pro_invoice_settings SET {set_clause} WHERE user_id = :user_id"),
        updates,
    )
    await db.commit()
    result = await db.execute(
        text("SELECT * FROM pro_invoice_settings WHERE user_id = :user_id"),
        {"user_id": user_id},
    )
    return ProInvoiceSettings(**dict(result.fetchone()._mapping))


# ────────────────────────────── Invoices ──────────────────────────────


@router.get("/invoices", response_model=list[ProInvoice])
async def list_invoices(
    status_filter: str | None = Query(None, alias="status"),
    client_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List invoices with optional filters."""
    query = """
        SELECT i.*, c.name as client_name, c.email as client_email, c.address as client_address
        FROM pro_invoices i
        LEFT JOIN pro_clients c ON c.id = i.client_id
        WHERE i.user_id = :user_id
    """
    params: dict = {"user_id": user_id}
    if status_filter:
        query += " AND i.status = :status"
        params["status"] = status_filter
    if client_id:
        query += " AND i.client_id = :client_id"
        params["client_id"] = client_id
    if start_date:
        query += " AND i.issue_date >= :start_date"
        params["start_date"] = start_date
    if end_date:
        query += " AND i.issue_date <= :end_date"
        params["end_date"] = end_date
    query += " ORDER BY i.issue_date DESC"

    result = await db.execute(text(query), params)
    invoices = []
    for row in result.fetchall():
        inv = dict(row._mapping)
        # Fetch items
        items_result = await db.execute(
            text("SELECT * FROM pro_invoice_items WHERE invoice_id = :id ORDER BY sort_order"),
            {"id": inv["id"]},
        )
        inv["items"] = [dict(r._mapping) for r in items_result.fetchall()]
        invoices.append(ProInvoice(**inv))
    return invoices


@router.get("/invoices/{invoice_id}", response_model=ProInvoice)
async def get_invoice(
    invoice_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single invoice with items."""
    result = await db.execute(
        text("""SELECT i.*, c.name as client_name, c.email as client_email, c.address as client_address
                FROM pro_invoices i
                LEFT JOIN pro_clients c ON c.id = i.client_id
                WHERE i.id = :id AND i.user_id = :user_id"""),
        {"id": invoice_id, "user_id": user_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Invoice not found")
    inv = dict(row._mapping)
    items_result = await db.execute(
        text("SELECT * FROM pro_invoice_items WHERE invoice_id = :id ORDER BY sort_order"),
        {"id": invoice_id},
    )
    inv["items"] = [dict(r._mapping) for r in items_result.fetchall()]
    return ProInvoice(**inv)


@router.post("/invoices", response_model=ProInvoice, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    payload: CreateProInvoice,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new invoice with auto-numbered ID."""
    invoice_number = await _generate_number(db, user_id, "invoice")
    subtotal, total = _calc_totals(payload.items, payload.discount_type, payload.discount_value)
    now = datetime.now(timezone.utc).isoformat()
    invoice_id = str(uuid4())

    await db.execute(
        text("""INSERT INTO pro_invoices
                (id, user_id, client_id, invoice_number, status, issue_date, due_date,
                 subtotal, total, discount_type, discount_value, notes, created_at, updated_at)
                VALUES (:id, :user_id, :client_id, :invoice_number, 'draft', :issue_date, :due_date,
                        :subtotal, :total, :discount_type, :discount_value, :notes, :now, :now)"""),
        {
            "id": invoice_id, "user_id": user_id, "client_id": payload.client_id,
            "invoice_number": invoice_number, "issue_date": payload.issue_date,
            "due_date": payload.due_date, "subtotal": subtotal, "total": total,
            "discount_type": payload.discount_type, "discount_value": payload.discount_value,
            "notes": payload.notes, "now": now,
        },
    )

    for idx, item in enumerate(payload.items):
        item_total = round(item.quantity * item.unit_price, 2)
        await db.execute(
            text("""INSERT INTO pro_invoice_items
                    (id, invoice_id, product_id, description, quantity, unit_price, total, sort_order)
                    VALUES (:id, :invoice_id, :product_id, :description, :quantity, :unit_price, :total, :sort_order)"""),
            {
                "id": str(uuid4()), "invoice_id": invoice_id, "product_id": item.product_id,
                "description": item.description, "quantity": item.quantity,
                "unit_price": item.unit_price, "total": item_total, "sort_order": idx,
            },
        )
    await db.commit()
    return await get_invoice(invoice_id, user_id, db)


@router.put("/invoices/{invoice_id}", response_model=ProInvoice)
async def update_invoice(
    invoice_id: str,
    payload: UpdateProInvoice,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a draft invoice."""
    result = await db.execute(
        text("SELECT status FROM pro_invoices WHERE id = :id AND user_id = :user_id"),
        {"id": invoice_id, "user_id": user_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if row.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft invoices can be edited")

    updates = payload.model_dump(exclude_unset=True, exclude={"items"})
    now = datetime.now(timezone.utc).isoformat()

    # If items are provided, recalculate totals
    if payload.items is not None:
        subtotal, total = _calc_totals(
            payload.items,
            payload.discount_type or updates.get("discount_type"),
            payload.discount_value if payload.discount_value is not None else 0,
        )
        updates["subtotal"] = subtotal
        updates["total"] = total

        # Replace items
        await db.execute(
            text("DELETE FROM pro_invoice_items WHERE invoice_id = :id"),
            {"id": invoice_id},
        )
        for idx, item in enumerate(payload.items):
            item_total = round(item.quantity * item.unit_price, 2)
            await db.execute(
                text("""INSERT INTO pro_invoice_items
                        (id, invoice_id, product_id, description, quantity, unit_price, total, sort_order)
                        VALUES (:id, :invoice_id, :product_id, :description, :quantity, :unit_price, :total, :sort_order)"""),
                {
                    "id": str(uuid4()), "invoice_id": invoice_id, "product_id": item.product_id,
                    "description": item.description, "quantity": item.quantity,
                    "unit_price": item.unit_price, "total": item_total, "sort_order": idx,
                },
            )

    if updates:
        updates["updated_at"] = now
        set_clause = ", ".join(f"{k} = :{k}" for k in updates)
        updates["id"] = invoice_id
        updates["user_id"] = user_id
        await db.execute(
            text(f"UPDATE pro_invoices SET {set_clause} WHERE id = :id AND user_id = :user_id"),
            updates,
        )
    await db.commit()
    return await get_invoice(invoice_id, user_id, db)


@router.delete("/invoices/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a draft invoice."""
    result = await db.execute(
        text("SELECT status FROM pro_invoices WHERE id = :id AND user_id = :user_id"),
        {"id": invoice_id, "user_id": user_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if row.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft invoices can be deleted")
    await db.execute(text("DELETE FROM pro_invoices WHERE id = :id"), {"id": invoice_id})
    await db.commit()


@router.put("/invoices/{invoice_id}/status", response_model=ProInvoice)
async def update_invoice_status(
    invoice_id: str,
    payload: UpdateProInvoiceStatus,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update invoice status with transition validation."""
    result = await db.execute(
        text("SELECT status FROM pro_invoices WHERE id = :id AND user_id = :user_id"),
        {"id": invoice_id, "user_id": user_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Invoice not found")

    current = row.status
    new = payload.status
    valid_transitions = {
        "draft": ["sent", "cancelled"],
        "sent": ["paid", "cancelled"],
        "paid": ["cancelled"],
    }
    if new not in valid_transitions.get(current, []):
        raise HTTPException(status_code=400, detail=f"Cannot transition from {current} to {new}")

    now = datetime.now(timezone.utc).isoformat()
    params: dict = {"id": invoice_id, "status": new, "now": now}
    extra_set = ""
    if new == "paid":
        params["payment_method"] = payload.payment_method
        params["paid_date"] = payload.paid_date or now[:10]
        extra_set = ", payment_method = :payment_method, paid_date = :paid_date"

    await db.execute(
        text(f"UPDATE pro_invoices SET status = :status, updated_at = :now{extra_set} WHERE id = :id"),
        params,
    )
    await db.commit()
    return await get_invoice(invoice_id, user_id, db)


@router.put("/invoices/{invoice_id}/reminder", response_model=ProInvoice)
async def mark_invoice_reminder(
    invoice_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark reminder sent on an invoice."""
    now = datetime.now(timezone.utc).isoformat()
    result = await db.execute(
        text("UPDATE pro_invoices SET reminder_sent_at = :now, updated_at = :now WHERE id = :id AND user_id = :user_id RETURNING id"),
        {"id": invoice_id, "user_id": user_id, "now": now},
    )
    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Invoice not found")
    await db.commit()
    return await get_invoice(invoice_id, user_id, db)


@router.get("/invoices/{invoice_id}/pdf")
async def download_invoice_pdf(
    invoice_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download invoice as PDF."""
    result = await db.execute(
        text("SELECT * FROM pro_invoices WHERE id = :id AND user_id = :user_id"),
        {"id": invoice_id, "user_id": user_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Invoice not found")
    invoice = dict(row._mapping)

    items_result = await db.execute(
        text("SELECT * FROM pro_invoice_items WHERE invoice_id = :id ORDER BY sort_order"),
        {"id": invoice_id},
    )
    items = [dict(r._mapping) for r in items_result.fetchall()]

    profile = await _get_profile_for_pdf(db, user_id)
    settings = await _get_or_create_invoice_settings(db, user_id)
    client = await _get_client_dict(db, invoice["client_id"])

    pdf_bytes = generate_invoice_pdf(
        invoice=invoice, items=items, profile=profile, settings=settings, client=client,
    )
    filename = f"{invoice['invoice_number']}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ────────────────────────────── Quotes ──────────────────────────────


@router.get("/quotes", response_model=list[ProQuote])
async def list_quotes(
    status_filter: str | None = Query(None, alias="status"),
    client_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List quotes with optional filters."""
    query = """
        SELECT q.*, c.name as client_name, c.email as client_email, c.address as client_address
        FROM pro_quotes q
        LEFT JOIN pro_clients c ON c.id = q.client_id
        WHERE q.user_id = :user_id
    """
    params: dict = {"user_id": user_id}
    if status_filter:
        query += " AND q.status = :status"
        params["status"] = status_filter
    if client_id:
        query += " AND q.client_id = :client_id"
        params["client_id"] = client_id
    if start_date:
        query += " AND q.issue_date >= :start_date"
        params["start_date"] = start_date
    if end_date:
        query += " AND q.issue_date <= :end_date"
        params["end_date"] = end_date
    query += " ORDER BY q.issue_date DESC"

    result = await db.execute(text(query), params)
    quotes = []
    for row in result.fetchall():
        q = dict(row._mapping)
        items_result = await db.execute(
            text("SELECT * FROM pro_quote_items WHERE quote_id = :id ORDER BY sort_order"),
            {"id": q["id"]},
        )
        q["items"] = [dict(r._mapping) for r in items_result.fetchall()]
        quotes.append(ProQuote(**q))
    return quotes


@router.get("/quotes/{quote_id}", response_model=ProQuote)
async def get_quote(
    quote_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single quote with items."""
    result = await db.execute(
        text("""SELECT q.*, c.name as client_name, c.email as client_email, c.address as client_address
                FROM pro_quotes q
                LEFT JOIN pro_clients c ON c.id = q.client_id
                WHERE q.id = :id AND q.user_id = :user_id"""),
        {"id": quote_id, "user_id": user_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Quote not found")
    q = dict(row._mapping)
    items_result = await db.execute(
        text("SELECT * FROM pro_quote_items WHERE quote_id = :id ORDER BY sort_order"),
        {"id": quote_id},
    )
    q["items"] = [dict(r._mapping) for r in items_result.fetchall()]
    return ProQuote(**q)


@router.post("/quotes", response_model=ProQuote, status_code=status.HTTP_201_CREATED)
async def create_quote(
    payload: CreateProQuote,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new quote."""
    quote_number = await _generate_number(db, user_id, "quote")
    subtotal, total = _calc_totals(payload.items, payload.discount_type, payload.discount_value)
    now = datetime.now(timezone.utc).isoformat()
    quote_id = str(uuid4())

    await db.execute(
        text("""INSERT INTO pro_quotes
                (id, user_id, client_id, quote_number, status, issue_date, validity_date,
                 subtotal, total, discount_type, discount_value, notes, created_at, updated_at)
                VALUES (:id, :user_id, :client_id, :quote_number, 'draft', :issue_date, :validity_date,
                        :subtotal, :total, :discount_type, :discount_value, :notes, :now, :now)"""),
        {
            "id": quote_id, "user_id": user_id, "client_id": payload.client_id,
            "quote_number": quote_number, "issue_date": payload.issue_date,
            "validity_date": payload.validity_date, "subtotal": subtotal, "total": total,
            "discount_type": payload.discount_type, "discount_value": payload.discount_value,
            "notes": payload.notes, "now": now,
        },
    )

    for idx, item in enumerate(payload.items):
        item_total = round(item.quantity * item.unit_price, 2)
        await db.execute(
            text("""INSERT INTO pro_quote_items
                    (id, quote_id, product_id, description, quantity, unit_price, total, sort_order)
                    VALUES (:id, :quote_id, :product_id, :description, :quantity, :unit_price, :total, :sort_order)"""),
            {
                "id": str(uuid4()), "quote_id": quote_id, "product_id": item.product_id,
                "description": item.description, "quantity": item.quantity,
                "unit_price": item.unit_price, "total": item_total, "sort_order": idx,
            },
        )
    await db.commit()
    return await get_quote(quote_id, user_id, db)


@router.put("/quotes/{quote_id}", response_model=ProQuote)
async def update_quote(
    quote_id: str,
    payload: UpdateProQuote,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a draft quote."""
    result = await db.execute(
        text("SELECT status FROM pro_quotes WHERE id = :id AND user_id = :user_id"),
        {"id": quote_id, "user_id": user_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Quote not found")
    if row.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft quotes can be edited")

    updates = payload.model_dump(exclude_unset=True, exclude={"items"})
    now = datetime.now(timezone.utc).isoformat()

    if payload.items is not None:
        subtotal, total = _calc_totals(
            payload.items,
            payload.discount_type or updates.get("discount_type"),
            payload.discount_value if payload.discount_value is not None else 0,
        )
        updates["subtotal"] = subtotal
        updates["total"] = total

        await db.execute(
            text("DELETE FROM pro_quote_items WHERE quote_id = :id"),
            {"id": quote_id},
        )
        for idx, item in enumerate(payload.items):
            item_total = round(item.quantity * item.unit_price, 2)
            await db.execute(
                text("""INSERT INTO pro_quote_items
                        (id, quote_id, product_id, description, quantity, unit_price, total, sort_order)
                        VALUES (:id, :quote_id, :product_id, :description, :quantity, :unit_price, :total, :sort_order)"""),
                {
                    "id": str(uuid4()), "quote_id": quote_id, "product_id": item.product_id,
                    "description": item.description, "quantity": item.quantity,
                    "unit_price": item.unit_price, "total": item_total, "sort_order": idx,
                },
            )

    if updates:
        updates["updated_at"] = now
        set_clause = ", ".join(f"{k} = :{k}" for k in updates)
        updates["id"] = quote_id
        updates["user_id"] = user_id
        await db.execute(
            text(f"UPDATE pro_quotes SET {set_clause} WHERE id = :id AND user_id = :user_id"),
            updates,
        )
    await db.commit()
    return await get_quote(quote_id, user_id, db)


@router.delete("/quotes/{quote_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quote(
    quote_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a draft quote."""
    result = await db.execute(
        text("SELECT status FROM pro_quotes WHERE id = :id AND user_id = :user_id"),
        {"id": quote_id, "user_id": user_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Quote not found")
    if row.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft quotes can be deleted")
    await db.execute(text("DELETE FROM pro_quotes WHERE id = :id"), {"id": quote_id})
    await db.commit()


@router.put("/quotes/{quote_id}/status", response_model=ProQuote)
async def update_quote_status(
    quote_id: str,
    payload: UpdateProQuoteStatus,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update quote status."""
    result = await db.execute(
        text("SELECT status FROM pro_quotes WHERE id = :id AND user_id = :user_id"),
        {"id": quote_id, "user_id": user_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Quote not found")

    current = row.status
    new = payload.status
    valid_transitions = {
        "draft": ["sent", "expired"],
        "sent": ["accepted", "rejected", "expired"],
        "accepted": ["expired"],
    }
    if new not in valid_transitions.get(current, []):
        raise HTTPException(status_code=400, detail=f"Cannot transition from {current} to {new}")

    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        text("UPDATE pro_quotes SET status = :status, updated_at = :now WHERE id = :id"),
        {"id": quote_id, "status": new, "now": now},
    )
    await db.commit()
    return await get_quote(quote_id, user_id, db)


@router.post("/quotes/{quote_id}/convert-to-invoice", response_model=ProInvoice)
async def convert_quote_to_invoice(
    quote_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Convert a quote to an invoice, linking both."""
    result = await db.execute(
        text("SELECT * FROM pro_quotes WHERE id = :id AND user_id = :user_id"),
        {"id": quote_id, "user_id": user_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Quote not found")
    quote = dict(row._mapping)
    if quote.get("invoice_id"):
        raise HTTPException(status_code=400, detail="Quote already converted")

    # Get quote items
    items_result = await db.execute(
        text("SELECT * FROM pro_quote_items WHERE quote_id = :id ORDER BY sort_order"),
        {"id": quote_id},
    )
    quote_items = [dict(r._mapping) for r in items_result.fetchall()]

    # Generate invoice number
    invoice_number = await _generate_number(db, user_id, "invoice")
    now = datetime.now(timezone.utc).isoformat()
    invoice_id = str(uuid4())

    # Get payment terms for due_date
    settings = await _get_or_create_invoice_settings(db, user_id)
    from datetime import timedelta
    issue_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    due_date = (datetime.now(timezone.utc) + timedelta(days=settings["payment_terms_days"])).strftime("%Y-%m-%d")

    await db.execute(
        text("""INSERT INTO pro_invoices
                (id, user_id, client_id, invoice_number, status, issue_date, due_date,
                 subtotal, total, discount_type, discount_value, notes, quote_id, created_at, updated_at)
                VALUES (:id, :user_id, :client_id, :invoice_number, 'draft', :issue_date, :due_date,
                        :subtotal, :total, :discount_type, :discount_value, :notes, :quote_id, :now, :now)"""),
        {
            "id": invoice_id, "user_id": user_id, "client_id": quote["client_id"],
            "invoice_number": invoice_number, "issue_date": issue_date, "due_date": due_date,
            "subtotal": quote["subtotal"], "total": quote["total"],
            "discount_type": quote.get("discount_type"), "discount_value": quote.get("discount_value", 0),
            "notes": quote.get("notes"), "quote_id": quote_id, "now": now,
        },
    )

    # Copy items
    for item in quote_items:
        await db.execute(
            text("""INSERT INTO pro_invoice_items
                    (id, invoice_id, product_id, description, quantity, unit_price, total, sort_order)
                    VALUES (:id, :invoice_id, :product_id, :description, :quantity, :unit_price, :total, :sort_order)"""),
            {
                "id": str(uuid4()), "invoice_id": invoice_id, "product_id": item.get("product_id"),
                "description": item["description"], "quantity": item["quantity"],
                "unit_price": item["unit_price"], "total": item["total"], "sort_order": item["sort_order"],
            },
        )

    # Link quote to invoice
    await db.execute(
        text("UPDATE pro_quotes SET invoice_id = :invoice_id, updated_at = :now WHERE id = :id"),
        {"invoice_id": invoice_id, "id": quote_id, "now": now},
    )
    await db.commit()
    return await get_invoice(invoice_id, user_id, db)


@router.get("/quotes/{quote_id}/pdf")
async def download_quote_pdf(
    quote_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download quote as PDF."""
    result = await db.execute(
        text("SELECT * FROM pro_quotes WHERE id = :id AND user_id = :user_id"),
        {"id": quote_id, "user_id": user_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Quote not found")
    quote = dict(row._mapping)

    items_result = await db.execute(
        text("SELECT * FROM pro_quote_items WHERE quote_id = :id ORDER BY sort_order"),
        {"id": quote_id},
    )
    items = [dict(r._mapping) for r in items_result.fetchall()]

    profile = await _get_profile_for_pdf(db, user_id)
    settings = await _get_or_create_invoice_settings(db, user_id)
    client = await _get_client_dict(db, quote["client_id"])

    pdf_bytes = generate_quote_pdf(
        quote=quote, items=items, profile=profile, settings=settings, client=client,
    )
    filename = f"{quote['quote_number']}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
