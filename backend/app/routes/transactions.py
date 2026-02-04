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
    Transaction, CreateTransaction, UpdateTransaction,
    RecurringTransaction, CreateRecurringTransaction,
    UpdateRecurringTransaction, RecurringTransactionVersion,
    RecurringTransactionWithCategory
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


@router.put("/transactions/{transaction_id}", response_model=Transaction)
async def update_transaction(
    transaction_id: str,
    payload: UpdateTransaction,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing transaction."""
    # Check if transaction exists
    result = await db.execute(
        text("SELECT id FROM transactions WHERE id = :id"),
        {"id": transaction_id}
    )
    if not result.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    # Build dynamic update query based on provided fields
    updates = []
    params = {"id": transaction_id}

    if payload.category_id is not None:
        updates.append("category_id = :category_id")
        params["category_id"] = payload.category_id
    if payload.title is not None:
        updates.append("title = :title")
        params["title"] = payload.title
    if payload.amount is not None:
        updates.append("amount = :amount")
        params["amount"] = payload.amount
    if payload.transaction_type is not None:
        updates.append("transaction_type = :transaction_type")
        params["transaction_type"] = payload.transaction_type
    if payload.date is not None:
        updates.append("date = :date")
        params["date"] = payload.date
    if payload.comment is not None:
        updates.append("comment = :comment")
        params["comment"] = payload.comment
    if payload.paid_by_user_id is not None:
        updates.append("paid_by_user_id = :paid_by_user_id")
        params["paid_by_user_id"] = payload.paid_by_user_id

    if updates:
        query = f"UPDATE transactions SET {', '.join(updates)} WHERE id = :id"
        await db.execute(text(query), params)
        await db.commit()

    # Fetch and return the updated transaction
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


@router.get("/budgets/{budget_id}/recurring", response_model=list[RecurringTransactionWithCategory])
async def get_recurring_transactions(budget_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve all recurring transactions for a specific budget with category info."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    result = await db.execute(
        text("""
            SELECT r.id, r.budget_id, r.category_id, r.title, r.amount, r.transaction_type,
                   r.frequency, r.day, r.active, r.created_at,
                   c.name as category_name, c.parent_id as parent_category_id,
                   pc.name as parent_category_name
            FROM recurring_transactions r
            LEFT JOIN categories c ON r.category_id = c.id
            LEFT JOIN categories pc ON c.parent_id = pc.id
            WHERE r.budget_id = :budget_id
        """),
        {"budget_id": budget_id}
    )
    rows = result.fetchall()

    results = []
    for row in rows:
        # Check for pending future version
        pending_result = await db.execute(
            text("""
                SELECT id, recurring_transaction_id, title, amount, category_id,
                       frequency, day, effective_from, effective_until, created_at, change_reason
                FROM recurring_transaction_versions
                WHERE recurring_transaction_id = :recurring_id
                AND effective_from > :today
                AND effective_until IS NULL
                ORDER BY effective_from ASC
                LIMIT 1
            """),
            {"recurring_id": row.id, "today": today}
        )
        pending_row = pending_result.fetchone()
        pending_version = None
        if pending_row:
            pending_version = RecurringTransactionVersion(
                id=pending_row.id,
                recurring_transaction_id=pending_row.recurring_transaction_id,
                title=pending_row.title,
                amount=pending_row.amount,
                category_id=pending_row.category_id,
                frequency=pending_row.frequency,
                day=pending_row.day,
                effective_from=pending_row.effective_from,
                effective_until=pending_row.effective_until,
                created_at=pending_row.created_at,
                change_reason=pending_row.change_reason,
            )

        results.append(RecurringTransactionWithCategory(
            id=row.id,
            budget_id=row.budget_id,
            category_id=row.category_id,
            category_name=row.category_name or "Unknown",
            parent_category_id=row.parent_category_id,
            parent_category_name=row.parent_category_name,
            title=row.title,
            amount=row.amount,
            transaction_type=row.transaction_type,
            frequency=row.frequency,
            day=row.day,
            active=row.active,
            created_at=row.created_at,
            pending_version=pending_version,
        ))

    return results


@router.post("/budgets/{budget_id}/recurring", response_model=RecurringTransactionWithCategory)
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
            SELECT r.id, r.budget_id, r.category_id, r.title, r.amount, r.transaction_type,
                   r.frequency, r.day, r.active, r.created_at,
                   c.name as category_name, c.parent_id as parent_category_id,
                   pc.name as parent_category_name
            FROM recurring_transactions r
            LEFT JOIN categories c ON r.category_id = c.id
            LEFT JOIN categories pc ON c.parent_id = pc.id
            WHERE r.id = :id
        """),
        {"id": recurring_id}
    )
    row = result.fetchone()
    return RecurringTransactionWithCategory(
        id=row.id,
        budget_id=row.budget_id,
        category_id=row.category_id,
        category_name=row.category_name or "Unknown",
        parent_category_id=row.parent_category_id,
        parent_category_name=row.parent_category_name,
        title=row.title,
        amount=row.amount,
        transaction_type=row.transaction_type,
        frequency=row.frequency,
        day=row.day,
        active=row.active,
        created_at=row.created_at,
        pending_version=None,
    )


@router.put("/recurring/{recurring_id}/toggle", response_model=RecurringTransactionWithCategory)
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

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    result = await db.execute(
        text("""
            SELECT r.id, r.budget_id, r.category_id, r.title, r.amount, r.transaction_type,
                   r.frequency, r.day, r.active, r.created_at,
                   c.name as category_name, c.parent_id as parent_category_id,
                   pc.name as parent_category_name
            FROM recurring_transactions r
            LEFT JOIN categories c ON r.category_id = c.id
            LEFT JOIN categories pc ON c.parent_id = pc.id
            WHERE r.id = :id
        """),
        {"id": recurring_id}
    )
    row = result.fetchone()

    # Check for pending future version
    pending_result = await db.execute(
        text("""
            SELECT id, recurring_transaction_id, title, amount, category_id,
                   frequency, day, effective_from, effective_until, created_at, change_reason
            FROM recurring_transaction_versions
            WHERE recurring_transaction_id = :recurring_id
            AND effective_from > :today
            AND effective_until IS NULL
            ORDER BY effective_from ASC
            LIMIT 1
        """),
        {"recurring_id": recurring_id, "today": today}
    )
    pending_row = pending_result.fetchone()
    pending_version = None
    if pending_row:
        pending_version = RecurringTransactionVersion(
            id=pending_row.id,
            recurring_transaction_id=pending_row.recurring_transaction_id,
            title=pending_row.title,
            amount=pending_row.amount,
            category_id=pending_row.category_id,
            frequency=pending_row.frequency,
            day=pending_row.day,
            effective_from=pending_row.effective_from,
            effective_until=pending_row.effective_until,
            created_at=pending_row.created_at,
            change_reason=pending_row.change_reason,
        )

    return RecurringTransactionWithCategory(
        id=row.id,
        budget_id=row.budget_id,
        category_id=row.category_id,
        category_name=row.category_name or "Unknown",
        parent_category_id=row.parent_category_id,
        parent_category_name=row.parent_category_name,
        title=row.title,
        amount=row.amount,
        transaction_type=row.transaction_type,
        frequency=row.frequency,
        day=row.day,
        active=row.active,
        created_at=row.created_at,
        pending_version=pending_version,
    )


@router.delete("/recurring/{recurring_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recurring_transaction(recurring_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a recurring transaction."""
    await db.execute(text("DELETE FROM recurring_transactions WHERE id = :id"), {"id": recurring_id})
    await db.commit()


@router.put("/recurring/{recurring_id}", response_model=RecurringTransactionWithCategory)
async def update_recurring_transaction(
    recurring_id: str,
    payload: UpdateRecurringTransaction,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a recurring transaction.

    If effective_date is today or in the past, changes are applied immediately.
    If effective_date is in the future, a new version is scheduled.
    """
    # Check if recurring transaction exists
    result = await db.execute(
        text("""
            SELECT id, budget_id, category_id, title, amount, transaction_type,
                   frequency, day, active, created_at
            FROM recurring_transactions WHERE id = :id
        """),
        {"id": recurring_id}
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring transaction not found")

    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    effective_date = payload.effective_date or today

    # Determine new values (use payload if provided, else keep existing)
    new_title = payload.title if payload.title is not None else row.title
    new_amount = payload.amount if payload.amount is not None else row.amount
    new_category_id = payload.category_id if payload.category_id is not None else row.category_id
    new_frequency = payload.frequency if payload.frequency is not None else row.frequency
    new_day = payload.day if payload.day is not None else row.day

    version_id = str(uuid4())
    created_at = now.isoformat()

    if effective_date <= today:
        # Apply changes immediately
        # First, close any current active version
        await db.execute(
            text("""
                UPDATE recurring_transaction_versions
                SET effective_until = :today
                WHERE recurring_transaction_id = :recurring_id
                AND effective_until IS NULL
                AND effective_from <= :today
            """),
            {"recurring_id": recurring_id, "today": today}
        )

        # Create new version record
        await db.execute(
            text("""
                INSERT INTO recurring_transaction_versions
                (id, recurring_transaction_id, title, amount, category_id, frequency, day,
                 effective_from, effective_until, created_at, change_reason)
                VALUES (:id, :recurring_id, :title, :amount, :category_id, :frequency, :day,
                        :effective_from, NULL, :created_at, :change_reason)
            """),
            {
                "id": version_id,
                "recurring_id": recurring_id,
                "title": new_title,
                "amount": new_amount,
                "category_id": new_category_id,
                "frequency": new_frequency,
                "day": new_day,
                "effective_from": effective_date,
                "created_at": created_at,
                "change_reason": payload.change_reason,
            }
        )

        # Update the base recurring transaction
        await db.execute(
            text("""
                UPDATE recurring_transactions
                SET title = :title, amount = :amount, category_id = :category_id,
                    frequency = :frequency, day = :day
                WHERE id = :id
            """),
            {
                "id": recurring_id,
                "title": new_title,
                "amount": new_amount,
                "category_id": new_category_id,
                "frequency": new_frequency,
                "day": new_day,
            }
        )
    else:
        # Schedule future change - create version with future effective_from
        await db.execute(
            text("""
                INSERT INTO recurring_transaction_versions
                (id, recurring_transaction_id, title, amount, category_id, frequency, day,
                 effective_from, effective_until, created_at, change_reason)
                VALUES (:id, :recurring_id, :title, :amount, :category_id, :frequency, :day,
                        :effective_from, NULL, :created_at, :change_reason)
            """),
            {
                "id": version_id,
                "recurring_id": recurring_id,
                "title": new_title,
                "amount": new_amount,
                "category_id": new_category_id,
                "frequency": new_frequency,
                "day": new_day,
                "effective_from": effective_date,
                "created_at": created_at,
                "change_reason": payload.change_reason,
            }
        )

    await db.commit()

    # Fetch and return the updated recurring transaction with category info
    result = await db.execute(
        text("""
            SELECT r.id, r.budget_id, r.category_id, r.title, r.amount, r.transaction_type,
                   r.frequency, r.day, r.active, r.created_at,
                   c.name as category_name, c.parent_id as parent_category_id,
                   pc.name as parent_category_name
            FROM recurring_transactions r
            LEFT JOIN categories c ON r.category_id = c.id
            LEFT JOIN categories pc ON c.parent_id = pc.id
            WHERE r.id = :id
        """),
        {"id": recurring_id}
    )
    row = result.fetchone()

    # Check for pending future version
    pending_result = await db.execute(
        text("""
            SELECT id, recurring_transaction_id, title, amount, category_id,
                   frequency, day, effective_from, effective_until, created_at, change_reason
            FROM recurring_transaction_versions
            WHERE recurring_transaction_id = :recurring_id
            AND effective_from > :today
            AND effective_until IS NULL
            ORDER BY effective_from ASC
            LIMIT 1
        """),
        {"recurring_id": recurring_id, "today": today}
    )
    pending_row = pending_result.fetchone()
    pending_version = None
    if pending_row:
        pending_version = RecurringTransactionVersion(
            id=pending_row.id,
            recurring_transaction_id=pending_row.recurring_transaction_id,
            title=pending_row.title,
            amount=pending_row.amount,
            category_id=pending_row.category_id,
            frequency=pending_row.frequency,
            day=pending_row.day,
            effective_from=pending_row.effective_from,
            effective_until=pending_row.effective_until,
            created_at=pending_row.created_at,
            change_reason=pending_row.change_reason,
        )

    return RecurringTransactionWithCategory(
        id=row.id,
        budget_id=row.budget_id,
        category_id=row.category_id,
        category_name=row.category_name or "Unknown",
        parent_category_id=row.parent_category_id,
        parent_category_name=row.parent_category_name,
        title=row.title,
        amount=row.amount,
        transaction_type=row.transaction_type,
        frequency=row.frequency,
        day=row.day,
        active=row.active,
        created_at=row.created_at,
        pending_version=pending_version,
    )


@router.get("/recurring/{recurring_id}/versions", response_model=list[RecurringTransactionVersion])
async def get_recurring_versions(recurring_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve version history for a recurring transaction."""
    # Check if recurring transaction exists
    result = await db.execute(
        text("SELECT id FROM recurring_transactions WHERE id = :id"),
        {"id": recurring_id}
    )
    if not result.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring transaction not found")

    result = await db.execute(
        text("""
            SELECT id, recurring_transaction_id, title, amount, category_id,
                   frequency, day, effective_from, effective_until, created_at, change_reason
            FROM recurring_transaction_versions
            WHERE recurring_transaction_id = :recurring_id
            ORDER BY effective_from DESC
        """),
        {"recurring_id": recurring_id}
    )
    rows = result.fetchall()

    return [RecurringTransactionVersion(
        id=row.id,
        recurring_transaction_id=row.recurring_transaction_id,
        title=row.title,
        amount=row.amount,
        category_id=row.category_id,
        frequency=row.frequency,
        day=row.day,
        effective_from=row.effective_from,
        effective_until=row.effective_until,
        created_at=row.created_at,
        change_reason=row.change_reason,
    ) for row in rows]


@router.delete("/recurring/versions/{version_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recurring_version(version_id: str, db: AsyncSession = Depends(get_db)):
    """Cancel a scheduled (future) version. Only future versions can be deleted."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Check if version exists and is in the future
    result = await db.execute(
        text("""
            SELECT id, effective_from FROM recurring_transaction_versions
            WHERE id = :id
        """),
        {"id": version_id}
    )
    row = result.fetchone()

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")

    if row.effective_from <= today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete past or current versions"
        )

    await db.execute(
        text("DELETE FROM recurring_transaction_versions WHERE id = :id"),
        {"id": version_id}
    )
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
