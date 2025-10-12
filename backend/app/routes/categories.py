# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Category management routes."""

import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Category, CreateCategory, UpdateCategory

router = APIRouter()


async def update_parent_amount(db: AsyncSession, parent_id: str | None):
    """Recalculate parent category amount from subcategories."""
    if not parent_id:
        return
    await db.execute(
        text("""
            UPDATE categories
            SET amount = (
                SELECT COALESCE(SUM(sub.amount), 0)
                FROM categories sub
                WHERE sub.parent_id = :parent_id
            )
            WHERE id = :parent_id
        """),
        {"parent_id": parent_id}
    )


def parse_tags(tags_json: str | None) -> list[str]:
    """Parse tags from JSON string."""
    if not tags_json:
        return []
    try:
        return json.loads(tags_json)
    except json.JSONDecodeError:
        return []


@router.get("/budgets/{budget_id}/categories", response_model=list[Category])
async def get_categories(budget_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve all categories for a specific budget."""
    result = await db.execute(
        text("SELECT id, budget_id, parent_id, name, amount, tags, created_at FROM categories WHERE budget_id = :budget_id"),
        {"budget_id": budget_id}
    )
    rows = result.fetchall()
    return [Category(
        id=row.id,
        budget_id=row.budget_id,
        parent_id=row.parent_id,
        name=row.name,
        amount=row.amount,
        tags=parse_tags(row.tags),
        created_at=row.created_at,
    ) for row in rows]


@router.post("/budgets/{budget_id}/categories", response_model=Category)
async def create_category(
    budget_id: str,
    payload: CreateCategory,
    db: AsyncSession = Depends(get_db)
):
    """Create a new category within a budget."""
    category_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()
    tags_json = json.dumps(payload.tags) if payload.tags else None

    await db.execute(
        text("""
            INSERT INTO categories (id, budget_id, parent_id, name, amount, tags, created_at)
            VALUES (:id, :budget_id, :parent_id, :name, :amount, :tags, :created_at)
        """),
        {
            "id": category_id,
            "budget_id": budget_id,
            "parent_id": payload.parent_id,
            "name": payload.name,
            "amount": payload.amount,
            "tags": tags_json,
            "created_at": now,
        }
    )

    # Update parent amount if this is a subcategory
    if payload.parent_id:
        await update_parent_amount(db, payload.parent_id)

    await db.commit()

    result = await db.execute(
        text("SELECT id, budget_id, parent_id, name, amount, tags, created_at FROM categories WHERE id = :id"),
        {"id": category_id}
    )
    row = result.fetchone()
    return Category(
        id=row.id,
        budget_id=row.budget_id,
        parent_id=row.parent_id,
        name=row.name,
        amount=row.amount,
        tags=parse_tags(row.tags),
        created_at=row.created_at,
    )


@router.put("/categories/{category_id}", response_model=Category)
async def update_category(
    category_id: str,
    payload: UpdateCategory,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing category."""
    # Get current category to find parent_id
    current = await db.execute(
        text("SELECT parent_id FROM categories WHERE id = :id"),
        {"id": category_id}
    )
    current_row = current.fetchone()
    if not current_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    parent_id = current_row.parent_id

    updates = []
    params = {"id": category_id}

    if payload.name is not None:
        updates.append("name = :name")
        params["name"] = payload.name

    if payload.amount is not None:
        updates.append("amount = :amount")
        params["amount"] = payload.amount

    if payload.tags is not None:
        updates.append("tags = :tags")
        params["tags"] = json.dumps(payload.tags)

    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    query = f"UPDATE categories SET {', '.join(updates)} WHERE id = :id"
    await db.execute(text(query), params)

    # Update parent amount if this is a subcategory and amount changed
    if parent_id and payload.amount is not None:
        await update_parent_amount(db, parent_id)

    await db.commit()

    result = await db.execute(
        text("SELECT id, budget_id, parent_id, name, amount, tags, created_at FROM categories WHERE id = :id"),
        {"id": category_id}
    )
    row = result.fetchone()

    return Category(
        id=row.id,
        budget_id=row.budget_id,
        parent_id=row.parent_id,
        name=row.name,
        amount=row.amount,
        tags=parse_tags(row.tags),
        created_at=row.created_at,
    )


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a category."""
    # Get parent_id before deleting
    result = await db.execute(
        text("SELECT parent_id FROM categories WHERE id = :id"),
        {"id": category_id}
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    parent_id = row.parent_id

    # Check for subcategories
    result = await db.execute(
        text("SELECT COUNT(*) as count FROM categories WHERE parent_id = :id"),
        {"id": category_id}
    )
    if result.fetchone().count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category with subcategories"
        )

    await db.execute(text("DELETE FROM categories WHERE id = :id"), {"id": category_id})

    # Update parent amount if this was a subcategory
    if parent_id:
        await update_parent_amount(db, parent_id)

    await db.commit()
