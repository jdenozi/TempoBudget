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
from ..models import Budget, CreateBudget, BudgetSummary

router = APIRouter()


@router.get("", response_model=list[Budget])
async def get_budgets(
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Retrieve all budgets for the authenticated user (owned + shared)."""
    result = await db.execute(
        text("""
            SELECT DISTINCT b.id, b.user_id, b.name, b.budget_type, b.is_active, b.created_at, b.updated_at
            FROM budgets b
            LEFT JOIN budget_members bm ON b.id = bm.budget_id
            WHERE b.user_id = :user_id OR bm.user_id = :user_id
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


@router.get("/summaries", response_model=list[BudgetSummary])
async def get_budget_summaries(
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Get summary statistics for all user budgets (current month only)."""
    # Calculate current month date range
    now = datetime.now(timezone.utc)
    month_start = f"{now.year}-{now.month:02d}-01"
    # Calculate next month for end range
    if now.month == 12:
        month_end = f"{now.year + 1}-01-01"
    else:
        month_end = f"{now.year}-{now.month + 1:02d}-01"

    # Get all budgets for the user (owned + group member)
    result = await db.execute(
        text("""
            SELECT DISTINCT b.id, b.name, b.budget_type
            FROM budgets b
            LEFT JOIN budget_members bm ON b.id = bm.budget_id
            WHERE b.user_id = :user_id OR bm.user_id = :user_id
        """),
        {"user_id": user_id}
    )
    budgets = result.fetchall()

    summaries = []
    for budget in budgets:
        # Get expense budget (sum of parent categories WITHOUT "revenu" tag)
        result = await db.execute(
            text("""
                SELECT COALESCE(SUM(amount), 0) as total
                FROM categories
                WHERE budget_id = :budget_id
                AND parent_id IS NULL
                AND (tags IS NULL OR tags NOT LIKE '%"revenu"%')
            """),
            {"budget_id": budget.id}
        )
        total_budget = result.fetchone().total

        # Get income budget (sum of parent categories WITH "revenu" tag)
        result = await db.execute(
            text("""
                SELECT COALESCE(SUM(amount), 0) as total
                FROM categories
                WHERE budget_id = :budget_id
                AND parent_id IS NULL
                AND tags LIKE '%"revenu"%'
            """),
            {"budget_id": budget.id}
        )
        income_budget = result.fetchone().total

        # Get total spent (expenses) for CURRENT MONTH ONLY
        result = await db.execute(
            text("""
                SELECT COALESCE(SUM(amount), 0) as total
                FROM transactions
                WHERE budget_id = :budget_id
                AND transaction_type = 'expense'
                AND date >= :month_start
                AND date < :month_end
            """),
            {"budget_id": budget.id, "month_start": month_start, "month_end": month_end}
        )
        total_spent = result.fetchone().total

        # Get total income for CURRENT MONTH ONLY
        result = await db.execute(
            text("""
                SELECT COALESCE(SUM(amount), 0) as total
                FROM transactions
                WHERE budget_id = :budget_id
                AND transaction_type = 'income'
                AND date >= :month_start
                AND date < :month_end
            """),
            {"budget_id": budget.id, "month_start": month_start, "month_end": month_end}
        )
        total_income = result.fetchone().total

        # Get category count
        result = await db.execute(
            text("SELECT COUNT(*) as cnt FROM categories WHERE budget_id = :budget_id"),
            {"budget_id": budget.id}
        )
        category_count = result.fetchone().cnt

        # Get transaction count for CURRENT MONTH ONLY
        result = await db.execute(
            text("""
                SELECT COUNT(*) as cnt FROM transactions
                WHERE budget_id = :budget_id
                AND date >= :month_start
                AND date < :month_end
            """),
            {"budget_id": budget.id, "month_start": month_start, "month_end": month_end}
        )
        transaction_count = result.fetchone().cnt

        remaining = total_budget - total_spent
        percentage = (total_spent / total_budget * 100) if total_budget > 0 else 0
        balance = income_budget - total_budget

        summaries.append(BudgetSummary(
            id=budget.id,
            name=budget.name,
            budget_type=budget.budget_type,
            total_budget=round(total_budget, 2),
            income_budget=round(income_budget, 2),
            total_spent=round(total_spent, 2),
            total_income=round(total_income, 2),
            remaining=round(remaining, 2),
            percentage=round(percentage, 2),
            category_count=category_count,
            transaction_count=transaction_count,
            balance=round(balance, 2),
        ))

    return summaries


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
