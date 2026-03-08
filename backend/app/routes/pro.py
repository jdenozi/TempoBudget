# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Pro (auto-entrepreneur) routes."""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
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
)

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
