# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Transaction management routes."""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import (
    Transaction, CreateTransaction,
    RecurringTransaction, CreateRecurringTransaction
)

router = APIRouter()


@router.get("/budgets/{budget_id}/transactions", response_model=list[Transaction])
async def get_transactions(budget_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve all transactions for a specific budget."""
    result = await db.execute(
        text("""
            SELECT id, budget_id, category_id, title, amount, transaction_type,
                   date, comment, is_recurring, created_at
            FROM transactions WHERE budget_id = :budget_id ORDER BY date DESC
        """),
        {"budget_id": budget_id}
    )
    rows = result.fetchall()
    return [Transaction(
        id=row.id,
        budget_id=row.budget_id,
        category_id=row.category_id,
        title=row.title,
        amount=row.amount,
        transaction_type=row.transaction_type,
        date=row.date,
        comment=row.comment,
        is_recurring=row.is_recurring,
        created_at=row.created_at,
    ) for row in rows]


@router.post("/budgets/{budget_id}/transactions", response_model=Transaction)
async def create_transaction(
    budget_id: str,
    payload: CreateTransaction,
    db: AsyncSession = Depends(get_db)
):
    """Create a new transaction."""
    transaction_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    await db.execute(
        text("""
            INSERT INTO transactions (id, budget_id, category_id, title, amount,
                                       transaction_type, date, comment, is_recurring, created_at)
            VALUES (:id, :budget_id, :category_id, :title, :amount,
                    :transaction_type, :date, :comment, 0, :created_at)
        """),
        {
            "id": transaction_id,
            "budget_id": budget_id,
            "category_id": payload.category_id,
            "title": payload.title,
            "amount": payload.amount,
            "transaction_type": payload.transaction_type,
            "date": payload.date,
            "comment": payload.comment,
            "created_at": now,
        }
    )
    await db.commit()

    result = await db.execute(
        text("""
            SELECT id, budget_id, category_id, title, amount, transaction_type,
                   date, comment, is_recurring, created_at
            FROM transactions WHERE id = :id
        """),
        {"id": transaction_id}
    )
    row = result.fetchone()
    return Transaction(
        id=row.id,
        budget_id=row.budget_id,
        category_id=row.category_id,
        title=row.title,
        amount=row.amount,
        transaction_type=row.transaction_type,
        date=row.date,
        comment=row.comment,
        is_recurring=row.is_recurring,
        created_at=row.created_at,
    )


@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(transaction_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a transaction."""
    await db.execute(text("DELETE FROM transactions WHERE id = :id"), {"id": transaction_id})
    await db.commit()


@router.get("/budgets/{budget_id}/recurring", response_model=list[RecurringTransaction])
async def get_recurring_transactions(budget_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve all recurring transactions for a specific budget."""
    result = await db.execute(
        text("""
            SELECT id, budget_id, category_id, title, amount, transaction_type,
                   frequency, day, active, created_at
            FROM recurring_transactions WHERE budget_id = :budget_id
        """),
        {"budget_id": budget_id}
    )
    rows = result.fetchall()
    return [RecurringTransaction(
        id=row.id,
        budget_id=row.budget_id,
        category_id=row.category_id,
        title=row.title,
        amount=row.amount,
        transaction_type=row.transaction_type,
        frequency=row.frequency,
        day=row.day,
        active=row.active,
        created_at=row.created_at,
    ) for row in rows]


@router.post("/budgets/{budget_id}/recurring", response_model=RecurringTransaction)
async def create_recurring_transaction(
    budget_id: str,
    payload: CreateRecurringTransaction,
    db: AsyncSession = Depends(get_db)
):
    """Create a new recurring transaction."""
    recurring_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    await db.execute(
        text("""
            INSERT INTO recurring_transactions (id, budget_id, category_id, title, amount,
                                                 transaction_type, frequency, day, active, created_at)
            VALUES (:id, :budget_id, :category_id, :title, :amount,
                    :transaction_type, :frequency, :day, 1, :created_at)
        """),
        {
            "id": recurring_id,
            "budget_id": budget_id,
            "category_id": payload.category_id,
            "title": payload.title,
            "amount": payload.amount,
            "transaction_type": payload.transaction_type,
            "frequency": payload.frequency,
            "day": payload.day,
            "created_at": now,
        }
    )
    await db.commit()

    result = await db.execute(
        text("""
            SELECT id, budget_id, category_id, title, amount, transaction_type,
                   frequency, day, active, created_at
            FROM recurring_transactions WHERE id = :id
        """),
        {"id": recurring_id}
    )
    row = result.fetchone()
    return RecurringTransaction(
        id=row.id,
        budget_id=row.budget_id,
        category_id=row.category_id,
        title=row.title,
        amount=row.amount,
        transaction_type=row.transaction_type,
        frequency=row.frequency,
        day=row.day,
        active=row.active,
        created_at=row.created_at,
    )


@router.put("/recurring/{recurring_id}/toggle", response_model=RecurringTransaction)
async def toggle_recurring_transaction(recurring_id: str, db: AsyncSession = Depends(get_db)):
    """Toggle the active status of a recurring transaction."""
    result = await db.execute(
        text("SELECT active FROM recurring_transactions WHERE id = :id"),
        {"id": recurring_id}
    )
    row = result.fetchone()

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring transaction not found")

    new_active = 0 if row.active else 1

    await db.execute(
        text("UPDATE recurring_transactions SET active = :active WHERE id = :id"),
        {"active": new_active, "id": recurring_id}
    )
    await db.commit()

    result = await db.execute(
        text("""
            SELECT id, budget_id, category_id, title, amount, transaction_type,
                   frequency, day, active, created_at
            FROM recurring_transactions WHERE id = :id
        """),
        {"id": recurring_id}
    )
    row = result.fetchone()
    return RecurringTransaction(
        id=row.id,
        budget_id=row.budget_id,
        category_id=row.category_id,
        title=row.title,
        amount=row.amount,
        transaction_type=row.transaction_type,
        frequency=row.frequency,
        day=row.day,
        active=row.active,
        created_at=row.created_at,
    )


@router.delete("/recurring/{recurring_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recurring_transaction(recurring_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a recurring transaction."""
    await db.execute(text("DELETE FROM recurring_transactions WHERE id = :id"), {"id": recurring_id})
    await db.commit()
