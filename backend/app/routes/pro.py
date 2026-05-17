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
    BatchToggleDeclared, DeclarationPeriodSummary, UrssafScheduleItem,
    ProInvoiceSettings, UpdateProInvoiceSettings,
    ProInvoice, CreateProInvoice, UpdateProInvoice, UpdateProInvoiceStatus,
    ProInvoiceItem, CreateProInvoiceItem,
    ProQuote, CreateProQuote, UpdateProQuote, UpdateProQuoteStatus,
    ProQuoteItem, CreateProQuoteItem,
    ProRecurringTransaction, CreateProRecurringTransaction, UpdateProRecurringTransaction,
    ProThreshold, CreateProThreshold, UpdateProThreshold,
    TaxBreakdown, RegimeComparisonRow, VatSummary,
)
from ..services.tax_engines import get_engine, PeriodInput
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

def _row_to_pro_profile(r) -> ProProfile:
    """Map a pro_profiles row to a ProProfile model, with safe defaults for new columns."""
    return ProProfile(
        id=r["id"], user_id=r["user_id"], siret=r.get("siret"),
        legal_form=r.get("legal_form") or "micro",
        activity_type=r.get("activity_type") or "services",
        cotisation_rate=r.get("cotisation_rate") or 21.1,
        declaration_frequency=r.get("declaration_frequency") or "quarterly",
        revenue_threshold=r.get("revenue_threshold") or 77700,
        cfp_rate=r.get("cfp_rate"),
        versement_liberatoire_enabled=r.get("versement_liberatoire_enabled") or 0,
        versement_liberatoire_rate=r.get("versement_liberatoire_rate"),
        ir_abattement_rate=r.get("ir_abattement_rate"),
        foyer_tmi=r.get("foyer_tmi"),
        tns_cotisations_rate=r.get("tns_cotisations_rate") if r.get("tns_cotisations_rate") is not None else 45.0,
        salary_gross_monthly=r.get("salary_gross_monthly") or 0,
        dividends_yearly=r.get("dividends_yearly") or 0,
        eurl_tax_option=r.get("eurl_tax_option") or "ir",
        is_subject_to_vat=r.get("is_subject_to_vat") or 0,
        vat_rate=r.get("vat_rate") or 20.0,
        vat_number=r.get("vat_number"),
        company_name=r.get("company_name"),
        company_address=r.get("company_address"),
        company_email=r.get("company_email"),
        company_phone=r.get("company_phone"),
        street=r.get("street"),
        postal_code=r.get("postal_code"),
        city=r.get("city"),
        country=r.get("country") or "FR",
        created_at=r["created_at"], updated_at=r["updated_at"],
    )


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
        return _row_to_pro_profile(row._mapping)

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

    refetch = await db.execute(
        text("SELECT * FROM pro_profiles WHERE user_id = :user_id"),
        {"user_id": user_id},
    )
    return _row_to_pro_profile(refetch.fetchone()._mapping)


@router.put("/profile", response_model=ProProfile)
async def update_profile(
    payload: UpdateProProfile,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the pro profile."""
    updates = []
    params: dict = {"user_id": user_id, "updated_at": datetime.now(timezone.utc).isoformat()}

    for field in ("siret", "legal_form", "activity_type", "cotisation_rate", "declaration_frequency",
                   "revenue_threshold", "cfp_rate", "versement_liberatoire_enabled",
                   "versement_liberatoire_rate", "ir_abattement_rate", "foyer_tmi",
                   "tns_cotisations_rate", "salary_gross_monthly", "dividends_yearly", "eurl_tax_option",
                   "is_subject_to_vat", "vat_rate", "vat_number",
                   "company_name", "company_address", "company_email", "company_phone",
                   "street", "postal_code", "city", "country",
                   "acre_enabled", "acre_start_date"):
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
    return _row_to_pro_profile(result.fetchone()._mapping)


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
        phone=r.phone, address=r.address, notes=r.notes,
        siren=r.siren, siret=r.siret, vat_number=r.vat_number,
        street=r.street, postal_code=r.postal_code, city=r.city,
        country=r.country or "FR", is_professional=r.is_professional if r.is_professional is not None else 1,
        created_at=r.created_at,
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
            INSERT INTO pro_clients (id, user_id, name, email, phone, address, notes,
                siren, siret, vat_number, street, postal_code, city, country, is_professional, created_at)
            VALUES (:id, :user_id, :name, :email, :phone, :address, :notes,
                :siren, :siret, :vat_number, :street, :postal_code, :city, :country, :is_professional, :created_at)
        """),
        {
            "id": client_id, "user_id": user_id,
            "name": payload.name, "email": payload.email,
            "phone": payload.phone, "address": payload.address,
            "notes": payload.notes, "siren": payload.siren, "siret": payload.siret,
            "vat_number": payload.vat_number, "street": payload.street,
            "postal_code": payload.postal_code, "city": payload.city,
            "country": payload.country, "is_professional": payload.is_professional,
            "created_at": now,
        },
    )
    await db.commit()

    return ProClient(
        id=client_id, user_id=user_id, name=payload.name,
        email=payload.email, phone=payload.phone, address=payload.address,
        notes=payload.notes, siren=payload.siren, siret=payload.siret,
        vat_number=payload.vat_number, street=payload.street,
        postal_code=payload.postal_code, city=payload.city,
        country=payload.country, is_professional=payload.is_professional,
        created_at=now,
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
    for field in ("name", "email", "phone", "address", "notes", "siren", "siret",
                  "vat_number", "street", "postal_code", "city", "country", "is_professional"):
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
        phone=r.phone, address=r.address, notes=r.notes,
        siren=r.siren, siret=r.siret, vat_number=r.vat_number,
        street=r.street, postal_code=r.postal_code, city=r.city,
        country=r.country or "FR", is_professional=r.is_professional if r.is_professional is not None else 1,
        created_at=r.created_at,
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
            invoice_id=r.invoice_id if hasattr(r, 'invoice_id') else None,
            project_category_id=r.project_category_id if hasattr(r, 'project_category_id') else None,
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
                                          discount_type, discount_value, coupon_id, gift_card_payment, project_category_id,
                                          is_declared, is_deductible, vat_rate, created_at)
            VALUES (:id, :user_id, :client_id, :category_id, :title,
                    :amount, :transaction_type, :date, :payment_method, :comment,
                    :discount_type, :discount_value, :coupon_id, :gift_card_payment, :project_category_id,
                    :is_declared, :is_deductible, :vat_rate, :created_at)
        """),
        {
            "id": tx_id, "user_id": user_id,
            "client_id": payload.client_id, "category_id": payload.category_id,
            "title": title, "amount": round(amount, 2),
            "transaction_type": payload.transaction_type, "date": payload.date,
            "payment_method": payload.payment_method, "comment": payload.comment,
            "discount_type": discount_type, "discount_value": discount_value,
            "coupon_id": coupon_id, "gift_card_payment": round(gift_card_payment, 2),
            "project_category_id": payload.project_category_id,
            "is_declared": payload.is_declared if payload.transaction_type == "income" else 0,
            "is_deductible": payload.is_deductible if payload.transaction_type == "expense" else 1,
            "vat_rate": payload.vat_rate,
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
        project_category_id=r.project_category_id if hasattr(r, 'project_category_id') else None,
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
    for field in ("client_id", "category_id", "title", "amount", "transaction_type", "date", "payment_method", "comment", "project_category_id", "is_declared", "is_deductible", "vat_rate"):
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
        project_category_id=r.project_category_id if hasattr(r, 'project_category_id') else None,
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
                COALESCE(SUM(CASE WHEN transaction_type = 'expense' AND date >= :year_start THEN amount END), 0) as expenses_year,
                COALESCE(SUM(CASE WHEN transaction_type = 'expense' AND is_deductible = 1 AND date >= :year_start THEN amount END), 0) as expenses_year_deductible
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

    # Get full profile to dispatch to the right tax engine for cotisations estimation
    profile_result = await db.execute(
        text("SELECT * FROM pro_profiles WHERE user_id = :user_id"),
        {"user_id": user_id},
    )
    profile_row = profile_result.fetchone()
    profile_dict = dict(profile_row._mapping) if profile_row else {}
    threshold = profile_dict.get("revenue_threshold") or 77700

    ca_year = row.ca_year

    # Declared income for the year (for engines that gate cotisations on declared CA)
    declared_result = await db.execute(
        text("""
            SELECT COALESCE(SUM(amount), 0) AS declared
            FROM pro_transactions
            WHERE user_id = :user_id AND transaction_type = 'income'
              AND date >= :year_start AND is_declared = 1
        """),
        {"user_id": user_id, "year_start": year_start},
    )
    declared_year = float(declared_result.fetchone().declared)

    engine = get_engine(profile_dict.get("legal_form") or "micro")
    yearly_breakdown = engine.compute(
        PeriodInput(
            turnover=float(ca_year),
            declared_turnover=declared_year,
            expenses=float(row.expenses_year_deductible),
            period="year",
        ),
        profile_dict,
    )
    cotisations = yearly_breakdown.cotisations_sociales
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


# ────────────────────────────── URSSAF Schedule ──────────────────────────────


# URSSAF declaration deadlines (day of month after period ends)
# Quarterly: last day of month following the quarter end (M+1)
# Monthly: last day of month following the activity month
URSSAF_DEADLINE_DAY = 30  # Generally last working day; simplified to 30


def _get_urssaf_deadline(period_end: str, frequency: str) -> str:
    """Calculate URSSAF declaration deadline for a period."""
    from datetime import date, timedelta
    import calendar

    end_date = date.fromisoformat(period_end)
    # Deadline is end of month following the period end
    # period_end is exclusive (first day of next period), so we go one month further
    deadline_year = end_date.year
    deadline_month = end_date.month
    # Get last day of that month
    last_day = calendar.monthrange(deadline_year, deadline_month)[1]
    return f"{deadline_year}-{deadline_month:02d}-{last_day:02d}"


@router.get("/urssaf/schedule", response_model=list[UrssafScheduleItem])
async def get_urssaf_schedule(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get URSSAF declaration schedule with deadlines and estimated amounts.
    Includes past periods (current year), current period, and projections for future periods.
    """
    from datetime import date, timedelta

    today = date.today()
    current_year = today.year

    # Get full profile
    profile_result = await db.execute(
        text("SELECT * FROM pro_profiles WHERE user_id = :user_id"),
        {"user_id": user_id},
    )
    profile = profile_result.fetchone()
    if not profile:
        return []

    frequency = profile.declaration_frequency or "quarterly"
    rate = profile.cotisation_rate or 21.1
    cfp_rate = profile.cfp_rate or 0.1  # Default CFP
    vl_enabled = profile.versement_liberatoire_enabled == 1
    vl_rate = profile.versement_liberatoire_rate or 1.0  # Default VL rate for services

    # Build periods for current year and next year (for projections)
    def build_periods(year: int, freq: str):
        periods = []
        if freq == "monthly":
            for m in range(1, 13):
                start = f"{year}-{m:02d}-01"
                if m == 12:
                    end = f"{year + 1}-01-01"
                else:
                    end = f"{year}-{m + 1:02d}-01"
                label = f"{MONTH_LABELS_FR[m]} {year}"
                periods.append((start, end, label))
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
        return periods

    all_periods = build_periods(current_year, frequency) + build_periods(current_year + 1, frequency)

    # Get actual turnover for current year per period
    turnover_result = await db.execute(
        text("""
            SELECT
                strftime('%Y-%m', date) as month,
                COALESCE(SUM(amount), 0) as turnover
            FROM pro_transactions
            WHERE user_id = :user_id
              AND transaction_type = 'income'
              AND date >= :year_start
            GROUP BY month
        """),
        {"user_id": user_id, "year_start": f"{current_year}-01-01"},
    )
    monthly_turnover = {row.month: row.turnover for row in turnover_result.fetchall()}

    # Calculate average monthly turnover for projections (based on last 6 months with data)
    avg_result = await db.execute(
        text("""
            SELECT COALESCE(AVG(monthly_total), 0) as avg_monthly
            FROM (
                SELECT strftime('%Y-%m', date) as month, SUM(amount) as monthly_total
                FROM pro_transactions
                WHERE user_id = :user_id
                  AND transaction_type = 'income'
                  AND date >= date('now', '-6 months')
                GROUP BY month
                HAVING monthly_total > 0
            )
        """),
        {"user_id": user_id},
    )
    avg_row = avg_result.fetchone()
    avg_monthly = avg_row.avg_monthly if avg_row else 0

    schedule = []
    for p_start, p_end, label in all_periods:
        deadline = _get_urssaf_deadline(p_end, frequency)
        deadline_date = date.fromisoformat(deadline)
        start_date = date.fromisoformat(p_start)
        end_date = date.fromisoformat(p_end)

        days_remaining = (deadline_date - today).days

        # Determine status
        if deadline_date < today:
            status = "past"
        elif start_date <= today < end_date:
            status = "current"
        else:
            status = "upcoming"

        # Calculate turnover
        is_projection = False
        if status == "past" or status == "current":
            # Sum actual turnover for months in this period
            turnover = 0.0
            m = start_date
            while m < end_date:
                month_key = m.strftime("%Y-%m")
                turnover += monthly_turnover.get(month_key, 0)
                # Move to next month
                if m.month == 12:
                    m = date(m.year + 1, 1, 1)
                else:
                    m = date(m.year, m.month + 1, 1)
        else:
            # Projection: use average monthly turnover
            is_projection = True
            months_in_period = 3 if frequency == "quarterly" else 1
            turnover = avg_monthly * months_in_period

        # Calculate contributions
        cotisations = round(turnover * (rate / 100), 2)
        cfp = round(turnover * (cfp_rate / 100), 2)
        ir_vl = round(turnover * (vl_rate / 100), 2) if vl_enabled else 0.0
        total_due = round(cotisations + cfp + ir_vl, 2)

        # Only include relevant periods (current year + next 2 periods for projections)
        if start_date.year < current_year:
            continue
        if is_projection and len([s for s in schedule if s.is_projection]) >= 4:
            continue

        schedule.append(UrssafScheduleItem(
            period_label=label,
            period_start=p_start,
            period_end=p_end,
            deadline=deadline,
            days_remaining=days_remaining,
            status=status,
            turnover=round(turnover, 2),
            cotisations=cotisations,
            cfp=cfp,
            ir_vl=ir_vl,
            total_due=total_due,
            is_projection=is_projection,
        ))

    return schedule


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


async def _get_vat_rate(db: AsyncSession, user_id: str) -> float:
    """Get the VAT rate for a user (0 if not subject to VAT)."""
    result = await db.execute(
        text("SELECT is_subject_to_vat, vat_rate FROM pro_profiles WHERE user_id = :user_id"),
        {"user_id": user_id},
    )
    row = result.fetchone()
    if row and row.is_subject_to_vat:
        return row.vat_rate or 20.0
    return 0


def _calc_totals(items: list, discount_type: str | None, discount_value: float, tva_rate: float = 0) -> tuple[float, float, float, float]:
    """Calculate subtotal HT, tva_amount, and total TTC from items, discount and TVA rate.
    Returns (subtotal_ht, tva_amount, total_ttc, tva_rate)."""
    subtotal = sum(i.quantity * i.unit_price for i in items)
    total_ht = subtotal
    if discount_type == "percentage" and discount_value:
        total_ht = subtotal * (1 - discount_value / 100)
    elif discount_type == "fixed" and discount_value:
        total_ht = subtotal - discount_value
    total_ht = round(max(total_ht, 0), 2)
    subtotal = round(subtotal, 2)
    tva_amount = round(total_ht * tva_rate / 100, 2) if tva_rate else 0
    total_ttc = round(total_ht + tva_amount, 2)
    return subtotal, tva_amount, total_ttc, tva_rate


async def _get_profile_for_pdf(db: AsyncSession, user_id: str) -> dict:
    """Get profile + user info for PDF generation. Company fields override user fields."""
    result = await db.execute(
        text("""SELECT u.name, u.email, u.phone, p.siret,
                       p.is_subject_to_vat, p.vat_rate, p.vat_number,
                       p.company_name, p.company_address, p.company_email, p.company_phone,
                       p.street, p.postal_code, p.city, p.country
                FROM users u LEFT JOIN pro_profiles p ON p.user_id = u.id
                WHERE u.id = :user_id"""),
        {"user_id": user_id},
    )
    row = result.fetchone()
    if not row:
        return {}
    d = dict(row._mapping)
    # Use company info if available, fallback to user info
    d["name"] = d.get("company_name") or d.get("name", "")
    d["email"] = d.get("company_email") or d.get("email")
    d["phone"] = d.get("company_phone") or d.get("phone")
    d["address"] = d.get("company_address")
    d["country"] = d.get("country") or "FR"
    return d


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
    vat_rate = await _get_vat_rate(db, user_id)
    subtotal, tva_amount, total, tva_rate = _calc_totals(payload.items, payload.discount_type, payload.discount_value, vat_rate)
    now = datetime.now(timezone.utc).isoformat()
    invoice_id = str(uuid4())

    await db.execute(
        text("""INSERT INTO pro_invoices
                (id, user_id, client_id, invoice_number, status, issue_date, due_date,
                 subtotal, tva_rate, tva_amount, total, discount_type, discount_value, notes, created_at, updated_at)
                VALUES (:id, :user_id, :client_id, :invoice_number, 'draft', :issue_date, :due_date,
                        :subtotal, :tva_rate, :tva_amount, :total, :discount_type, :discount_value, :notes, :now, :now)"""),
        {
            "id": invoice_id, "user_id": user_id, "client_id": payload.client_id,
            "invoice_number": invoice_number, "issue_date": payload.issue_date,
            "due_date": payload.due_date, "subtotal": subtotal, "tva_rate": tva_rate,
            "tva_amount": tva_amount, "total": total,
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
        vat_rate = await _get_vat_rate(db, user_id)
        subtotal, tva_amount, total, tva_rate = _calc_totals(
            payload.items,
            payload.discount_type or updates.get("discount_type"),
            payload.discount_value if payload.discount_value is not None else 0,
            vat_rate,
        )
        updates["subtotal"] = subtotal
        updates["tva_rate"] = tva_rate
        updates["tva_amount"] = tva_amount
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
        text("SELECT * FROM pro_invoices WHERE id = :id AND user_id = :user_id"),
        {"id": invoice_id, "user_id": user_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Invoice not found")
    invoice = dict(row._mapping)

    current = invoice["status"]
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

    # Create linked pro_transaction when invoice is paid
    if new == "paid":
        # Find default income category for this user
        cat_result = await db.execute(
            text("""SELECT id FROM pro_categories
                    WHERE user_id = :user_id AND type = 'income' AND is_default = 1
                    ORDER BY name LIMIT 1"""),
            {"user_id": user_id},
        )
        cat_row = cat_result.fetchone()
        if not cat_row:
            # Fallback: any income category
            cat_result = await db.execute(
                text("SELECT id FROM pro_categories WHERE user_id = :user_id AND type = 'income' LIMIT 1"),
                {"user_id": user_id},
            )
            cat_row = cat_result.fetchone()
        if not cat_row:
            raise HTTPException(status_code=400, detail="No income category found — create one first")

        paid_date = payload.paid_date or now[:10]
        payment_method = payload.payment_method or "transfer"
        await db.execute(
            text("""INSERT INTO pro_transactions
                    (id, user_id, client_id, category_id, title, amount, transaction_type,
                     date, payment_method, comment, is_declared, invoice_id, created_at)
                    VALUES (:id, :user_id, :client_id, :category_id, :title, :amount, 'income',
                            :date, :payment_method, :comment, 0, :invoice_id, :now)"""),
            {
                "id": str(uuid4()),
                "user_id": user_id,
                "client_id": invoice["client_id"],
                "category_id": cat_row.id,
                "title": f"Facture {invoice['invoice_number']}",
                "amount": invoice["total"],
                "date": paid_date,
                "payment_method": payment_method,
                "comment": f"Transaction auto-créée depuis la facture {invoice['invoice_number']}",
                "is_declared": 0,
                "invoice_id": invoice_id,
                "now": now,
            },
        )

    # If going to cancelled from paid, remove the linked transaction
    if new == "cancelled" and current == "paid":
        await db.execute(
            text("DELETE FROM pro_transactions WHERE invoice_id = :invoice_id AND user_id = :user_id"),
            {"invoice_id": invoice_id, "user_id": user_id},
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
    facturx: bool = False,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download invoice as PDF.

    Args:
        invoice_id: Invoice UUID
        facturx: If True, generate Factur-X compliant PDF/A-3 with embedded XML
    """
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
        facturx=facturx,
    )
    suffix = "-facturx" if facturx else ""
    filename = f"{invoice['invoice_number']}{suffix}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/invoices/{invoice_id}/export")
async def export_invoice_for_pdp(
    invoice_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export invoice data for PDP transmission via n8n.

    Returns structured JSON compatible with French e-invoicing platforms.
    """
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

    # Calculate discount
    discount_amount = 0.0
    if invoice.get("discount_type") and invoice.get("discount_value"):
        if invoice["discount_type"] == "percentage":
            discount_amount = invoice["subtotal"] * invoice["discount_value"] / 100
        else:
            discount_amount = invoice["discount_value"]

    return {
        "format": "factur-x",
        "profile": "BASIC",
        "invoice": {
            "number": invoice["invoice_number"],
            "issue_date": invoice["issue_date"],
            "due_date": invoice["due_date"],
            "status": invoice["status"],
            "currency": "EUR",
        },
        "seller": {
            "name": profile.get("company_name") or profile.get("name"),
            "siret": profile.get("siret"),
            "vat_number": profile.get("vat_number"),
            "email": profile.get("email"),
            "phone": profile.get("phone"),
            "address": {
                "street": profile.get("street"),
                "postal_code": profile.get("postal_code"),
                "city": profile.get("city"),
                "country": profile.get("country", "FR"),
            },
        },
        "buyer": {
            "name": client["name"],
            "siren": client.get("siren"),
            "siret": client.get("siret"),
            "vat_number": client.get("vat_number"),
            "email": client.get("email"),
            "is_professional": bool(client.get("is_professional", 1)),
            "address": {
                "street": client.get("street"),
                "postal_code": client.get("postal_code"),
                "city": client.get("city"),
                "country": client.get("country", "FR"),
            },
        },
        "lines": [
            {
                "description": item["description"],
                "quantity": item["quantity"],
                "unit_price": item["unit_price"],
                "total": item["total"],
            }
            for item in items
        ],
        "totals": {
            "subtotal": invoice["subtotal"],
            "discount_type": invoice.get("discount_type"),
            "discount_value": invoice.get("discount_value", 0),
            "discount_amount": discount_amount,
            "tax_basis": invoice["subtotal"] - discount_amount,
            "vat_rate": invoice.get("tva_rate", 0),
            "vat_amount": invoice.get("tva_amount", 0),
            "total": invoice["total"],
        },
        "payment": {
            "terms_days": settings.get("payment_terms_days", 30),
            "bank_iban": settings.get("bank_iban"),
            "bank_bic": settings.get("bank_bic"),
        },
        "notes": invoice.get("notes"),
    }


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
    vat_rate = await _get_vat_rate(db, user_id)
    subtotal, tva_amount, total, tva_rate = _calc_totals(payload.items, payload.discount_type, payload.discount_value, vat_rate)
    now = datetime.now(timezone.utc).isoformat()
    quote_id = str(uuid4())

    await db.execute(
        text("""INSERT INTO pro_quotes
                (id, user_id, client_id, quote_number, status, issue_date, validity_date,
                 subtotal, tva_rate, tva_amount, total, discount_type, discount_value, notes, created_at, updated_at)
                VALUES (:id, :user_id, :client_id, :quote_number, 'draft', :issue_date, :validity_date,
                        :subtotal, :tva_rate, :tva_amount, :total, :discount_type, :discount_value, :notes, :now, :now)"""),
        {
            "id": quote_id, "user_id": user_id, "client_id": payload.client_id,
            "quote_number": quote_number, "issue_date": payload.issue_date,
            "validity_date": payload.validity_date, "subtotal": subtotal, "tva_rate": tva_rate,
            "tva_amount": tva_amount, "total": total,
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
        vat_rate = await _get_vat_rate(db, user_id)
        subtotal, tva_amount, total, tva_rate = _calc_totals(
            payload.items,
            payload.discount_type or updates.get("discount_type"),
            payload.discount_value if payload.discount_value is not None else 0,
            vat_rate,
        )
        updates["subtotal"] = subtotal
        updates["tva_rate"] = tva_rate
        updates["tva_amount"] = tva_amount
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
    """Delete a quote."""
    result = await db.execute(
        text("SELECT id FROM pro_quotes WHERE id = :id AND user_id = :user_id"),
        {"id": quote_id, "user_id": user_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Quote not found")
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


# ── Pro recurring transactions ──


@router.get("/recurring", response_model=list[ProRecurringTransaction])
async def list_recurring(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all recurring pro transactions for the current user."""
    result = await db.execute(
        text("""
            SELECT r.*, c.name as client_name, cat.name as category_name
            FROM pro_recurring_transactions r
            LEFT JOIN pro_clients c ON r.client_id = c.id
            LEFT JOIN pro_categories cat ON r.category_id = cat.id
            WHERE r.user_id = :user_id
            ORDER BY r.created_at DESC
        """),
        {"user_id": user_id},
    )
    return [ProRecurringTransaction(**dict(r._mapping)) for r in result.fetchall()]


@router.post("/recurring", response_model=ProRecurringTransaction, status_code=status.HTTP_201_CREATED)
async def create_recurring(
    payload: CreateProRecurringTransaction,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a recurring pro transaction template."""
    rec_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        text("""
            INSERT INTO pro_recurring_transactions (id, user_id, client_id, category_id, title,
                                                    amount, transaction_type, frequency, day,
                                                    payment_method, comment, active, created_at)
            VALUES (:id, :user_id, :client_id, :category_id, :title,
                    :amount, :transaction_type, :frequency, :day,
                    :payment_method, :comment, 1, :created_at)
        """),
        {
            "id": rec_id, "user_id": user_id,
            "client_id": payload.client_id, "category_id": payload.category_id,
            "title": payload.title, "amount": payload.amount,
            "transaction_type": payload.transaction_type, "frequency": payload.frequency,
            "day": payload.day, "payment_method": payload.payment_method,
            "comment": payload.comment, "created_at": now,
        },
    )
    await db.commit()

    result = await db.execute(
        text("""
            SELECT r.*, c.name as client_name, cat.name as category_name
            FROM pro_recurring_transactions r
            LEFT JOIN pro_clients c ON r.client_id = c.id
            LEFT JOIN pro_categories cat ON r.category_id = cat.id
            WHERE r.id = :id
        """),
        {"id": rec_id},
    )
    return ProRecurringTransaction(**dict(result.fetchone()._mapping))


@router.put("/recurring/{recurring_id}", response_model=ProRecurringTransaction)
async def update_recurring(
    recurring_id: str,
    payload: UpdateProRecurringTransaction,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a recurring pro transaction template."""
    existing = await db.execute(
        text("SELECT id FROM pro_recurring_transactions WHERE id = :id AND user_id = :user_id"),
        {"id": recurring_id, "user_id": user_id},
    )
    if not existing.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring transaction not found")

    updates = []
    params: dict = {"id": recurring_id, "user_id": user_id}
    for field in ("client_id", "category_id", "title", "amount", "transaction_type",
                  "frequency", "day", "payment_method", "comment", "active"):
        value = getattr(payload, field)
        if value is not None:
            updates.append(f"{field} = :{field}")
            params[field] = value

    if updates:
        query = f"UPDATE pro_recurring_transactions SET {', '.join(updates)} WHERE id = :id AND user_id = :user_id"
        await db.execute(text(query), params)
        await db.commit()

    result = await db.execute(
        text("""
            SELECT r.*, c.name as client_name, cat.name as category_name
            FROM pro_recurring_transactions r
            LEFT JOIN pro_clients c ON r.client_id = c.id
            LEFT JOIN pro_categories cat ON r.category_id = cat.id
            WHERE r.id = :id
        """),
        {"id": recurring_id},
    )
    return ProRecurringTransaction(**dict(result.fetchone()._mapping))


@router.put("/recurring/{recurring_id}/toggle", response_model=ProRecurringTransaction)
async def toggle_recurring(
    recurring_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle active state of a recurring pro transaction."""
    result = await db.execute(
        text("SELECT active FROM pro_recurring_transactions WHERE id = :id AND user_id = :user_id"),
        {"id": recurring_id, "user_id": user_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring transaction not found")

    new_active = 0 if row.active == 1 else 1
    await db.execute(
        text("UPDATE pro_recurring_transactions SET active = :active WHERE id = :id"),
        {"active": new_active, "id": recurring_id},
    )
    await db.commit()

    result = await db.execute(
        text("""
            SELECT r.*, c.name as client_name, cat.name as category_name
            FROM pro_recurring_transactions r
            LEFT JOIN pro_clients c ON r.client_id = c.id
            LEFT JOIN pro_categories cat ON r.category_id = cat.id
            WHERE r.id = :id
        """),
        {"id": recurring_id},
    )
    return ProRecurringTransaction(**dict(result.fetchone()._mapping))


@router.delete("/recurring/{recurring_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recurring(
    recurring_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a recurring pro transaction template."""
    result = await db.execute(
        text("DELETE FROM pro_recurring_transactions WHERE id = :id AND user_id = :user_id"),
        {"id": recurring_id, "user_id": user_id},
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring transaction not found")
    await db.commit()


@router.post("/recurring/process", response_model=list[ProTransaction])
async def process_recurring(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Materialize due recurring pro transactions into real pro transactions.

    For each active template, creates pro_transactions for any due dates in the current month
    that don't already have a matching transaction (same category/title/amount/date).
    """
    from calendar import monthrange

    now = datetime.now(timezone.utc)
    current_year = now.year
    current_month = now.month
    current_day = now.day
    last_day_of_month = monthrange(current_year, current_month)[1]

    result = await db.execute(
        text("""
            SELECT id, user_id, client_id, category_id, title, amount, transaction_type,
                   frequency, day, payment_method, comment, created_at
            FROM pro_recurring_transactions
            WHERE user_id = :user_id AND active = 1
        """),
        {"user_id": user_id},
    )
    recurring_rows = result.fetchall()

    created: list[ProTransaction] = []

    for rec in recurring_rows:
        dates_to_create: list[str] = []

        if rec.frequency == "monthly":
            target_day = min(rec.day or 1, last_day_of_month)
            if target_day <= current_day:
                dates_to_create.append(f"{current_year}-{current_month:02d}-{target_day:02d}")

        elif rec.frequency == "weekly":
            rec_dow = rec.day if rec.day is not None else 0
            for d in range(1, current_day + 1):
                if datetime(current_year, current_month, d, tzinfo=timezone.utc).weekday() == rec_dow:
                    dates_to_create.append(f"{current_year}-{current_month:02d}-{d:02d}")

        elif rec.frequency == "yearly":
            target_day = min(rec.day or 1, last_day_of_month)
            rec_created = datetime.fromisoformat(rec.created_at.replace("Z", "+00:00"))
            if rec_created.month == current_month and target_day <= current_day:
                dates_to_create.append(f"{current_year}-{current_month:02d}-{target_day:02d}")

        elif rec.frequency == "daily":
            for d in range(1, current_day + 1):
                dates_to_create.append(f"{current_year}-{current_month:02d}-{d:02d}")

        for date_str in dates_to_create:
            existing = await db.execute(
                text("""
                    SELECT id FROM pro_transactions
                    WHERE user_id = :user_id
                    AND category_id = :category_id
                    AND title = :title
                    AND amount = :amount
                    AND date = :date
                """),
                {
                    "user_id": user_id,
                    "category_id": rec.category_id,
                    "title": rec.title,
                    "amount": rec.amount,
                    "date": date_str,
                },
            )
            if existing.fetchone() is not None:
                continue

            tx_id = str(uuid4())
            created_at = datetime.now(timezone.utc).isoformat()
            await db.execute(
                text("""
                    INSERT INTO pro_transactions (id, user_id, client_id, category_id, title,
                                                  amount, transaction_type, date, payment_method,
                                                  comment, created_at)
                    VALUES (:id, :user_id, :client_id, :category_id, :title,
                            :amount, :transaction_type, :date, :payment_method,
                            :comment, :created_at)
                """),
                {
                    "id": tx_id, "user_id": user_id,
                    "client_id": rec.client_id, "category_id": rec.category_id,
                    "title": rec.title, "amount": rec.amount,
                    "transaction_type": rec.transaction_type, "date": date_str,
                    "payment_method": rec.payment_method or "cash",
                    "comment": rec.comment,
                    "created_at": created_at,
                },
            )
            created.append(ProTransaction(
                id=tx_id, user_id=user_id, client_id=rec.client_id,
                category_id=rec.category_id, title=rec.title, amount=rec.amount,
                transaction_type=rec.transaction_type, date=date_str,
                payment_method=rec.payment_method or "cash", comment=rec.comment,
                created_at=created_at,
            ))

    await db.commit()
    return created


# ── Revenue thresholds (user-defined limits, ceilings, goals) ──


@router.get("/thresholds", response_model=list[ProThreshold])
async def list_thresholds(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all revenue thresholds for the current user."""
    result = await db.execute(
        text("SELECT * FROM pro_thresholds WHERE user_id = :user_id ORDER BY created_at DESC"),
        {"user_id": user_id},
    )
    return [ProThreshold(**dict(r._mapping)) for r in result.fetchall()]


@router.post("/thresholds", response_model=ProThreshold, status_code=status.HTTP_201_CREATED)
async def create_threshold(
    payload: CreateProThreshold,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new revenue threshold."""
    threshold_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        text("""
            INSERT INTO pro_thresholds (id, user_id, name, period, amount, color, active, created_at)
            VALUES (:id, :user_id, :name, :period, :amount, :color, 1, :created_at)
        """),
        {
            "id": threshold_id, "user_id": user_id,
            "name": payload.name, "period": payload.period,
            "amount": payload.amount, "color": payload.color,
            "created_at": now,
        },
    )
    await db.commit()
    result = await db.execute(
        text("SELECT * FROM pro_thresholds WHERE id = :id"),
        {"id": threshold_id},
    )
    return ProThreshold(**dict(result.fetchone()._mapping))


@router.put("/thresholds/{threshold_id}", response_model=ProThreshold)
async def update_threshold(
    threshold_id: str,
    payload: UpdateProThreshold,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing threshold."""
    existing = await db.execute(
        text("SELECT id FROM pro_thresholds WHERE id = :id AND user_id = :user_id"),
        {"id": threshold_id, "user_id": user_id},
    )
    if not existing.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Threshold not found")

    updates = []
    params: dict = {"id": threshold_id, "user_id": user_id}
    for field in ("name", "period", "amount", "color", "active"):
        value = getattr(payload, field)
        if value is not None:
            updates.append(f"{field} = :{field}")
            params[field] = value

    if updates:
        query = f"UPDATE pro_thresholds SET {', '.join(updates)} WHERE id = :id AND user_id = :user_id"
        await db.execute(text(query), params)
        await db.commit()

    result = await db.execute(
        text("SELECT * FROM pro_thresholds WHERE id = :id"),
        {"id": threshold_id},
    )
    return ProThreshold(**dict(result.fetchone()._mapping))


@router.delete("/thresholds/{threshold_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_threshold(
    threshold_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a threshold."""
    result = await db.execute(
        text("DELETE FROM pro_thresholds WHERE id = :id AND user_id = :user_id"),
        {"id": threshold_id, "user_id": user_id},
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Threshold not found")
    await db.commit()


# ── Tax breakdown (multi-regime) ──


@router.get("/tax-breakdown", response_model=TaxBreakdown)
async def tax_breakdown(
    period: str = "month",
    year: int | None = None,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return a tax breakdown for the requested period using the user's regime.

    Period: 'month' | 'quarter' | 'year'. The optional `year` param lets the
    caller scope the result to a past year (only meaningful for period='year';
    monthly/quarterly views always use the current month/quarter for now).
    """
    if period not in ("month", "quarter", "year"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid period")

    # Resolve profile
    p = await db.execute(
        text("SELECT * FROM pro_profiles WHERE user_id = :user_id"),
        {"user_id": user_id},
    )
    prow = p.fetchone()
    if not prow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pro profile not found")
    profile = dict(prow._mapping)
    legal_form = profile.get("legal_form") or "micro"

    # Resolve period start/end
    now = datetime.now(timezone.utc)
    target_year = year if (year is not None and period == "year") else now.year
    if period == "month":
        start = f"{target_year}-{now.month:02d}-01"
        next_month = now.month % 12 + 1
        next_year = target_year + 1 if now.month == 12 else target_year
        end = f"{next_year}-{next_month:02d}-01"
        period_label = f"{target_year}-{now.month:02d}"
    elif period == "quarter":
        q_start_month = ((now.month - 1) // 3) * 3 + 1
        start = f"{target_year}-{q_start_month:02d}-01"
        end_month = q_start_month + 3
        end_year = target_year + 1 if end_month > 12 else target_year
        end_month = end_month if end_month <= 12 else end_month - 12
        end = f"{end_year}-{end_month:02d}-01"
        period_label = f"Q{(q_start_month - 1) // 3 + 1} {target_year}"
    else:  # year
        start = f"{target_year}-01-01"
        end = f"{target_year + 1}-01-01"
        period_label = str(target_year)

    # Aggregate turnover and expenses for the period
    sums = await db.execute(
        text("""
            SELECT
              COALESCE(SUM(CASE WHEN transaction_type='income' THEN amount ELSE 0 END), 0) AS turnover,
              COALESCE(SUM(CASE WHEN transaction_type='income' AND is_declared=1 THEN amount ELSE 0 END), 0) AS declared_turnover,
              COALESCE(SUM(CASE WHEN transaction_type='expense' AND is_deductible=1 THEN amount ELSE 0 END), 0) AS expenses
            FROM pro_transactions
            WHERE user_id = :user_id AND date >= :start AND date < :end
        """),
        {"user_id": user_id, "start": start, "end": end},
    )
    s = sums.fetchone()
    period_input = PeriodInput(
        turnover=float(s.turnover),
        declared_turnover=float(s.declared_turnover),
        expenses=float(s.expenses),
        period=period,
    )

    engine = get_engine(legal_form)
    result = engine.compute(period_input, profile)

    return TaxBreakdown(
        legal_form=legal_form,
        period=period,
        period_label=period_label,
        turnover=result.turnover,
        deductible_expenses=result.deductible_expenses,
        benefice_imposable=None if result.benefice_imposable is None else round(result.benefice_imposable, 2),
        cotisations_sociales=round(result.cotisations_sociales, 2),
        cfp=round(result.cfp, 2),
        ir_versement_liberatoire=None if result.ir_versement_liberatoire is None else round(result.ir_versement_liberatoire, 2),
        ir_classique_estime=None if result.ir_classique_estime is None else round(result.ir_classique_estime, 2),
        impot_societes=None if result.impot_societes is None else round(result.impot_societes, 2),
        dividendes_taxes=None if result.dividendes_taxes is None else round(result.dividendes_taxes, 2),
        net_salary=None if result.net_salary is None else round(result.net_salary, 2),
        total_prelevements=round(result.total_prelevements, 2),
        net_after_taxes=round(result.net_after_taxes, 2),
        personal_take_home=round(result.personal_take_home, 2),
        notes=result.notes,
    )


# Comparison spec: regime key (returned to frontend) → engine inputs override
_REGIME_COMPARISON_SPEC: list[tuple[str, dict]] = [
    ("micro",   {"legal_form": "micro"}),
    ("ei_reel", {"legal_form": "ei_reel"}),
    ("eurl_ir", {"legal_form": "eurl", "eurl_tax_option": "ir"}),
    ("eurl_is", {"legal_form": "eurl", "eurl_tax_option": "is"}),
    ("sasu",    {"legal_form": "sasu"}),
    ("sas",     {"legal_form": "sas"}),
]


@router.get("/regime-comparison", response_model=list[RegimeComparisonRow])
async def regime_comparison(
    period: str = "year",
    year: int | None = None,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return a side-by-side breakdown of every regime, computed from the user's
    current CA, expenses, salary and dividends. Helps decide which legal form
    minimises total prélèvements for the given activity level.
    """
    if period not in ("month", "quarter", "year"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid period")

    p = await db.execute(
        text("SELECT * FROM pro_profiles WHERE user_id = :user_id"),
        {"user_id": user_id},
    )
    prow = p.fetchone()
    if not prow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pro profile not found")
    base_profile = dict(prow._mapping)

    now = datetime.now(timezone.utc)
    target_year = year if (year is not None and period == "year") else now.year
    if period == "month":
        start = f"{target_year}-{now.month:02d}-01"
        next_month = now.month % 12 + 1
        next_year = target_year + 1 if now.month == 12 else target_year
        end = f"{next_year}-{next_month:02d}-01"
        period_label = f"{target_year}-{now.month:02d}"
    elif period == "quarter":
        q_start_month = ((now.month - 1) // 3) * 3 + 1
        start = f"{target_year}-{q_start_month:02d}-01"
        end_month = q_start_month + 3
        end_year = target_year + 1 if end_month > 12 else target_year
        end_month = end_month if end_month <= 12 else end_month - 12
        end = f"{end_year}-{end_month:02d}-01"
        period_label = f"Q{(q_start_month - 1) // 3 + 1} {target_year}"
    else:
        start = f"{target_year}-01-01"
        end = f"{target_year + 1}-01-01"
        period_label = str(target_year)

    sums = await db.execute(
        text("""
            SELECT
              COALESCE(SUM(CASE WHEN transaction_type='income' THEN amount ELSE 0 END), 0) AS turnover,
              COALESCE(SUM(CASE WHEN transaction_type='income' AND is_declared=1 THEN amount ELSE 0 END), 0) AS declared_turnover,
              COALESCE(SUM(CASE WHEN transaction_type='expense' AND is_deductible=1 THEN amount ELSE 0 END), 0) AS expenses
            FROM pro_transactions
            WHERE user_id = :user_id AND date >= :start AND date < :end
        """),
        {"user_id": user_id, "start": start, "end": end},
    )
    s = sums.fetchone()
    period_input = PeriodInput(
        turnover=float(s.turnover),
        declared_turnover=float(s.declared_turnover),
        expenses=float(s.expenses),
        period=period,
    )

    rows: list[RegimeComparisonRow] = []
    for regime_key, overrides in _REGIME_COMPARISON_SPEC:
        scoped_profile = {**base_profile, **overrides}
        # Make sure micro-style declared CA is meaningful even if user is currently elsewhere:
        # if profile has no declared transactions, treat all turnover as declared for the comparison.
        if regime_key == "micro" and period_input.declared_turnover == 0 and period_input.turnover > 0:
            scoped_input = PeriodInput(
                turnover=period_input.turnover,
                declared_turnover=period_input.turnover,
                expenses=period_input.expenses,
                period=period_input.period,
            )
        else:
            scoped_input = period_input

        engine_form = overrides["legal_form"]
        engine = get_engine(engine_form)
        result = engine.compute(scoped_input, scoped_profile)

        rows.append(RegimeComparisonRow(
            regime=regime_key,
            breakdown=TaxBreakdown(
                legal_form=engine_form,
                period=period,
                period_label=period_label,
                turnover=result.turnover,
                deductible_expenses=result.deductible_expenses,
                benefice_imposable=None if result.benefice_imposable is None else round(result.benefice_imposable, 2),
                cotisations_sociales=round(result.cotisations_sociales, 2),
                cfp=round(result.cfp, 2),
                ir_versement_liberatoire=None if result.ir_versement_liberatoire is None else round(result.ir_versement_liberatoire, 2),
                ir_classique_estime=None if result.ir_classique_estime is None else round(result.ir_classique_estime, 2),
                impot_societes=None if result.impot_societes is None else round(result.impot_societes, 2),
                dividendes_taxes=None if result.dividendes_taxes is None else round(result.dividendes_taxes, 2),
                net_salary=None if result.net_salary is None else round(result.net_salary, 2),
                total_prelevements=round(result.total_prelevements, 2),
                net_after_taxes=round(result.net_after_taxes, 2),
                personal_take_home=round(result.personal_take_home, 2),
                notes=result.notes,
            ),
        ))
    return rows


# ── VAT (TVA) summary ──


def _resolve_period_window(period: str, year_override: int | None):
    """Return (start_iso, end_iso, label) for the requested period.

    Mirrors the logic used by /tax-breakdown so the VAT summary stays aligned.
    """
    if period not in ("month", "quarter", "year"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid period")

    now = datetime.now(timezone.utc)
    target_year = year_override if (year_override is not None and period == "year") else now.year
    if period == "month":
        start = f"{target_year}-{now.month:02d}-01"
        next_month = now.month % 12 + 1
        next_year = target_year + 1 if now.month == 12 else target_year
        end = f"{next_year}-{next_month:02d}-01"
        label = f"{target_year}-{now.month:02d}"
    elif period == "quarter":
        q_start_month = ((now.month - 1) // 3) * 3 + 1
        start = f"{target_year}-{q_start_month:02d}-01"
        end_month = q_start_month + 3
        end_year = target_year + 1 if end_month > 12 else target_year
        end_month = end_month if end_month <= 12 else end_month - 12
        end = f"{end_year}-{end_month:02d}-01"
        label = f"Q{(q_start_month - 1) // 3 + 1} {target_year}"
    else:
        start = f"{target_year}-01-01"
        end = f"{target_year + 1}-01-01"
        label = str(target_year)
    return start, end, label


@router.get("/vat-summary", response_model=VatSummary)
async def vat_summary(
    period: str = "month",
    year: int | None = None,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return TVA collected vs deductible for the requested period.

    Computation:
      - Per transaction VAT = amount × rate / (100 + rate), where rate is the
        transaction's vat_rate or, if null, the profile's vat_rate.
      - Collected = sum of VAT over income transactions
      - Deductible = sum of VAT over expense transactions where is_deductible=1
      - Balance = collected − deductible (positive = owed to DGFiP)
    """
    p = await db.execute(
        text("SELECT is_subject_to_vat, vat_rate FROM pro_profiles WHERE user_id = :user_id"),
        {"user_id": user_id},
    )
    prow = p.fetchone()
    if not prow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pro profile not found")
    is_subject = int(prow.is_subject_to_vat or 0)
    default_rate = float(prow.vat_rate or 20.0)

    start, end, label = _resolve_period_window(period, year)

    notes: list[str] = []
    if not is_subject:
        notes.append("Le profil n'est pas assujetti à la TVA. Les chiffres restent à 0 jusqu'à activation dans le profil.")

    # Aggregate VAT amounts using SQL math; coalesce(vat_rate, default) per row.
    result = await db.execute(
        text(f"""
            SELECT
              COALESCE(SUM(CASE WHEN transaction_type='income'
                                THEN amount * COALESCE(vat_rate, :default_rate) / (100 + COALESCE(vat_rate, :default_rate))
                                ELSE 0 END), 0) AS collected,
              COALESCE(SUM(CASE WHEN transaction_type='expense' AND is_deductible=1
                                THEN amount * COALESCE(vat_rate, :default_rate) / (100 + COALESCE(vat_rate, :default_rate))
                                ELSE 0 END), 0) AS deductible
            FROM pro_transactions
            WHERE user_id = :user_id AND date >= :start AND date < :end
        """),
        {"user_id": user_id, "start": start, "end": end, "default_rate": default_rate},
    )
    row = result.fetchone()
    collected = float(row.collected) if is_subject else 0.0
    deductible = float(row.deductible) if is_subject else 0.0
    balance = collected - deductible

    return VatSummary(
        period=period,
        period_label=label,
        is_subject_to_vat=is_subject,
        default_rate=default_rate,
        collected=round(collected, 2),
        deductible=round(deductible, 2),
        balance=round(balance, 2),
        notes=notes,
    )
