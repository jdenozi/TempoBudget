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
                   date, comment, is_recurring, paid_by_user_id, created_at
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
        paid_by_user_id=row.paid_by_user_id,
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
                                       transaction_type, date, comment, is_recurring, paid_by_user_id, created_at)
            VALUES (:id, :budget_id, :category_id, :title, :amount,
                    :transaction_type, :date, :comment, 0, :paid_by_user_id, :created_at)
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
            "paid_by_user_id": payload.paid_by_user_id,
            "created_at": now,
        }
    )
    await db.commit()

    result = await db.execute(
        text("""
            SELECT id, budget_id, category_id, title, amount, transaction_type,
                   date, comment, is_recurring, paid_by_user_id, created_at
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
        paid_by_user_id=row.paid_by_user_id,
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


@router.post("/budgets/{budget_id}/recurring/process", response_model=list[Transaction])
async def process_recurring_transactions(budget_id: str, db: AsyncSession = Depends(get_db)):
    """
    Process recurring transactions and generate actual transactions.

    For each active recurring transaction, checks if transactions should have been
    created for the current month and creates them if missing.
    """
    from calendar import monthrange

    now = datetime.now(timezone.utc)
    current_year = now.year
    current_month = now.month
    current_day = now.day

    # Get first and last day of current month
    first_day_of_month = datetime(current_year, current_month, 1, tzinfo=timezone.utc)
    last_day_of_month = monthrange(current_year, current_month)[1]

    # Get all active recurring transactions for this budget
    result = await db.execute(
        text("""
            SELECT id, budget_id, category_id, title, amount, transaction_type,
                   frequency, day, active, created_at
            FROM recurring_transactions
            WHERE budget_id = :budget_id AND active = 1
        """),
        {"budget_id": budget_id}
    )
    recurring_rows = result.fetchall()

    created_transactions = []

    for rec in recurring_rows:
        dates_to_create = []

        if rec.frequency == 'monthly':
            # Monthly: create on the specified day (or last day if day > days in month)
            target_day = min(rec.day or 1, last_day_of_month)
            if target_day <= current_day:
                dates_to_create.append(f"{current_year}-{current_month:02d}-{target_day:02d}")

        elif rec.frequency == 'weekly':
            # Weekly: create for each week of the month that has passed
            # Find all occurrences of the recurring day this month
            rec_day_of_week = rec.day or 0  # 0 = Monday, 6 = Sunday

            for day in range(1, current_day + 1):
                date = datetime(current_year, current_month, day, tzinfo=timezone.utc)
                if date.weekday() == rec_day_of_week:
                    dates_to_create.append(f"{current_year}-{current_month:02d}-{day:02d}")

        elif rec.frequency == 'yearly':
            # Yearly: check if the day/month matches current month
            target_day = min(rec.day or 1, last_day_of_month)
            # For yearly, we only create if we're in the right month (assume created month)
            rec_created = datetime.fromisoformat(rec.created_at.replace('Z', '+00:00'))
            if rec_created.month == current_month and target_day <= current_day:
                dates_to_create.append(f"{current_year}-{current_month:02d}-{target_day:02d}")

        # Check which transactions already exist
        for date_str in dates_to_create:
            # Check if transaction already exists for this date and recurring template
            existing = await db.execute(
                text("""
                    SELECT id FROM transactions
                    WHERE budget_id = :budget_id
                    AND category_id = :category_id
                    AND title = :title
                    AND amount = :amount
                    AND date = :date
                    AND is_recurring = 1
                """),
                {
                    "budget_id": budget_id,
                    "category_id": rec.category_id,
                    "title": rec.title,
                    "amount": rec.amount,
                    "date": date_str,
                }
            )

            if existing.fetchone() is None:
                # Create the transaction
                transaction_id = str(uuid4())
                created_at = datetime.now(timezone.utc).isoformat()

                await db.execute(
                    text("""
                        INSERT INTO transactions (id, budget_id, category_id, title, amount,
                                                   transaction_type, date, comment, is_recurring, created_at)
                        VALUES (:id, :budget_id, :category_id, :title, :amount,
                                :transaction_type, :date, :comment, 1, :created_at)
                    """),
                    {
                        "id": transaction_id,
                        "budget_id": budget_id,
                        "category_id": rec.category_id,
                        "title": rec.title,
                        "amount": rec.amount,
                        "transaction_type": rec.transaction_type,
                        "date": date_str,
                        "comment": f"Auto-generated from recurring: {rec.title}",
                        "created_at": created_at,
                    }
                )

                created_transactions.append(Transaction(
                    id=transaction_id,
                    budget_id=budget_id,
                    category_id=rec.category_id,
                    title=rec.title,
                    amount=rec.amount,
                    transaction_type=rec.transaction_type,
                    date=date_str,
                    comment=f"Auto-generated from recurring: {rec.title}",
                    is_recurring=1,
                    created_at=created_at,
                ))

    await db.commit()
    return created_transactions
