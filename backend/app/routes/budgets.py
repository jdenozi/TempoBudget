# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Budget management routes."""

from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user
from ..database import get_db
from ..models import Budget, CreateBudget

router = APIRouter()


@router.get("", response_model=list[Budget])
async def get_budgets(
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Retrieve all budgets for the authenticated user."""
    result = await db.execute(
        text("""
            SELECT id, user_id, name, budget_type, is_active, created_at, updated_at
            FROM budgets WHERE user_id = :user_id
        """),
        {"user_id": user_id}
    )
    rows = result.fetchall()
    return [Budget(
        id=row.id,
        user_id=row.user_id,
        name=row.name,
        budget_type=row.budget_type,
        is_active=row.is_active,
        created_at=row.created_at,
        updated_at=row.updated_at,
    ) for row in rows]


@router.post("", response_model=Budget)
async def create_budget(
    payload: CreateBudget,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Create a new budget."""
    budget_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    await db.execute(
        text("""
            INSERT INTO budgets (id, user_id, name, budget_type, is_active, created_at, updated_at)
            VALUES (:id, :user_id, :name, :budget_type, 0, :created_at, :updated_at)
        """),
        {
            "id": budget_id,
            "user_id": user_id,
            "name": payload.name,
            "budget_type": payload.budget_type,
            "created_at": now,
            "updated_at": now,
        }
    )

    # For group budgets, add creator as owner
    if payload.budget_type == "group":
        member_id = str(uuid4())
        await db.execute(
            text("""
                INSERT INTO budget_members (id, budget_id, user_id, role, created_at)
                VALUES (:id, :budget_id, :user_id, 'owner', :created_at)
            """),
            {
                "id": member_id,
                "budget_id": budget_id,
                "user_id": user_id,
                "created_at": now,
            }
        )

    await db.commit()

    result = await db.execute(
        text("SELECT id, user_id, name, budget_type, is_active, created_at, updated_at FROM budgets WHERE id = :id"),
        {"id": budget_id}
    )
    row = result.fetchone()
    return Budget(
        id=row.id,
        user_id=row.user_id,
        name=row.name,
        budget_type=row.budget_type,
        is_active=row.is_active,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("/{budget_id}", response_model=Budget)
async def get_budget(budget_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve a specific budget by ID."""
    result = await db.execute(
        text("SELECT id, user_id, name, budget_type, is_active, created_at, updated_at FROM budgets WHERE id = :id"),
        {"id": budget_id}
    )
    row = result.fetchone()

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")

    return Budget(
        id=row.id,
        user_id=row.user_id,
        name=row.name,
        budget_type=row.budget_type,
        is_active=row.is_active,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(
    budget_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Delete a budget."""
    # Check if user is owner (for group budgets)
    result = await db.execute(
        text("SELECT COUNT(*) as cnt FROM budget_members WHERE budget_id = :budget_id AND user_id = :user_id AND role = 'owner'"),
        {"budget_id": budget_id, "user_id": user_id}
    )
    is_owner = result.fetchone().cnt > 0

    # Check if it's the user's own budget (for personal budgets)
    result = await db.execute(
        text("SELECT COUNT(*) as cnt FROM budgets WHERE id = :id AND user_id = :user_id"),
        {"id": budget_id, "user_id": user_id}
    )
    is_my_budget = result.fetchone().cnt > 0

    if not is_owner and not is_my_budget:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    await db.execute(text("DELETE FROM budgets WHERE id = :id"), {"id": budget_id})
    await db.commit()
