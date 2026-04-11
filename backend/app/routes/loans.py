# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Loan management routes."""

from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user
from ..database import get_db
from ..models.loan import (
    Loan, CreateLoan, UpdateLoan,
    LoanRepayment, CreateLoanRepayment, LoanSummary
)

router = APIRouter()


@router.get("", response_model=list[Loan])
async def get_loans(
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Get all loans for the current user."""
    result = await db.execute(
        text("""
            SELECT id, user_id, person_name, amount, direction, date,
                   description, status, created_at, updated_at
            FROM loans WHERE user_id = :user_id ORDER BY date DESC
        """),
        {"user_id": user_id}
    )
    loan_rows = result.fetchall()

    loans = []
    for row in loan_rows:
        # Get repayments
        rep_result = await db.execute(
            text("""
                SELECT id, loan_id, amount, date, comment, created_at
                FROM loan_repayments WHERE loan_id = :loan_id ORDER BY date ASC
            """),
            {"loan_id": row.id}
        )
        repayments = [
            LoanRepayment(
                id=r.id, loan_id=r.loan_id, amount=r.amount,
                date=r.date, comment=r.comment, created_at=r.created_at
            )
            for r in rep_result.fetchall()
        ]
        total_repaid = sum(r.amount for r in repayments)

        loans.append(Loan(
            id=row.id, user_id=row.user_id, person_name=row.person_name,
            amount=row.amount, direction=row.direction, date=row.date,
            description=row.description, status=row.status,
            created_at=row.created_at, updated_at=row.updated_at,
            total_repaid=round(total_repaid, 2),
            remaining=round(row.amount - total_repaid, 2),
            repayments=repayments,
        ))

    return loans


@router.get("/summary", response_model=LoanSummary)
async def get_loan_summary(
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Get aggregated loan summary."""
    result = await db.execute(
        text("""
            SELECT l.direction,
                   COALESCE(SUM(l.amount), 0) as total,
                   COALESCE(SUM(l.amount), 0) - COALESCE(SUM(rep.total_repaid), 0) as remaining
            FROM loans l
            LEFT JOIN (
                SELECT loan_id, SUM(amount) as total_repaid
                FROM loan_repayments GROUP BY loan_id
            ) rep ON l.id = rep.loan_id
            WHERE l.user_id = :user_id
            GROUP BY l.direction
        """),
        {"user_id": user_id}
    )
    rows = result.fetchall()

    total_lent = 0.0
    total_borrowed = 0.0
    total_lent_remaining = 0.0
    total_borrowed_remaining = 0.0

    for row in rows:
        if row.direction == "lent":
            total_lent = row.total
            total_lent_remaining = max(row.remaining, 0)
        elif row.direction == "borrowed":
            total_borrowed = row.total
            total_borrowed_remaining = max(row.remaining, 0)

    return LoanSummary(
        total_lent=round(total_lent, 2),
        total_borrowed=round(total_borrowed, 2),
        total_lent_remaining=round(total_lent_remaining, 2),
        total_borrowed_remaining=round(total_borrowed_remaining, 2),
        net_position=round(total_lent_remaining - total_borrowed_remaining, 2),
    )


@router.post("", response_model=Loan)
async def create_loan(
    payload: CreateLoan,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Create a new loan."""
    loan_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    await db.execute(
        text("""
            INSERT INTO loans (id, user_id, person_name, amount, direction, date,
                               description, status, created_at, updated_at)
            VALUES (:id, :user_id, :person_name, :amount, :direction, :date,
                    :description, 'active', :created_at, :updated_at)
        """),
        {
            "id": loan_id, "user_id": user_id,
            "person_name": payload.person_name, "amount": payload.amount,
            "direction": payload.direction, "date": payload.date,
            "description": payload.description,
            "created_at": now, "updated_at": now,
        }
    )
    await db.commit()

    return Loan(
        id=loan_id, user_id=user_id, person_name=payload.person_name,
        amount=payload.amount, direction=payload.direction, date=payload.date,
        description=payload.description, status="active",
        created_at=now, updated_at=now,
        total_repaid=0, remaining=payload.amount, repayments=[],
    )


@router.put("/{loan_id}", response_model=Loan)
async def update_loan(
    loan_id: str,
    payload: UpdateLoan,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Update a loan."""
    result = await db.execute(
        text("SELECT id FROM loans WHERE id = :id AND user_id = :user_id"),
        {"id": loan_id, "user_id": user_id}
    )
    if not result.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")

    updates = []
    params: dict = {"id": loan_id}
    now = datetime.now(timezone.utc).isoformat()

    for field in ["person_name", "amount", "direction", "date", "description", "status"]:
        value = getattr(payload, field, None)
        if value is not None:
            updates.append(f"{field} = :{field}")
            params[field] = value

    if updates:
        updates.append("updated_at = :updated_at")
        params["updated_at"] = now
        query = f"UPDATE loans SET {', '.join(updates)} WHERE id = :id"
        await db.execute(text(query), params)
        await db.commit()

    # Fetch updated loan with repayments
    result = await db.execute(
        text("SELECT * FROM loans WHERE id = :id"),
        {"id": loan_id}
    )
    row = result.fetchone()

    rep_result = await db.execute(
        text("SELECT * FROM loan_repayments WHERE loan_id = :loan_id ORDER BY date ASC"),
        {"loan_id": loan_id}
    )
    repayments = [
        LoanRepayment(id=r.id, loan_id=r.loan_id, amount=r.amount,
                      date=r.date, comment=r.comment, created_at=r.created_at)
        for r in rep_result.fetchall()
    ]
    total_repaid = sum(r.amount for r in repayments)

    return Loan(
        id=row.id, user_id=row.user_id, person_name=row.person_name,
        amount=row.amount, direction=row.direction, date=row.date,
        description=row.description, status=row.status,
        created_at=row.created_at, updated_at=row.updated_at,
        total_repaid=round(total_repaid, 2),
        remaining=round(row.amount - total_repaid, 2),
        repayments=repayments,
    )


@router.delete("/{loan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_loan(
    loan_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Delete a loan and its repayments."""
    result = await db.execute(
        text("SELECT id FROM loans WHERE id = :id AND user_id = :user_id"),
        {"id": loan_id, "user_id": user_id}
    )
    if not result.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")

    await db.execute(text("DELETE FROM loan_repayments WHERE loan_id = :loan_id"), {"loan_id": loan_id})
    await db.execute(text("DELETE FROM loans WHERE id = :id"), {"id": loan_id})
    await db.commit()


@router.post("/{loan_id}/repayments", response_model=LoanRepayment)
async def add_repayment(
    loan_id: str,
    payload: CreateLoanRepayment,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Add a repayment to a loan. Auto-marks as repaid if fully paid."""
    result = await db.execute(
        text("SELECT id, amount FROM loans WHERE id = :id AND user_id = :user_id"),
        {"id": loan_id, "user_id": user_id}
    )
    loan = result.fetchone()
    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")

    repayment_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    await db.execute(
        text("""
            INSERT INTO loan_repayments (id, loan_id, amount, date, comment, created_at)
            VALUES (:id, :loan_id, :amount, :date, :comment, :created_at)
        """),
        {
            "id": repayment_id, "loan_id": loan_id,
            "amount": payload.amount, "date": payload.date,
            "comment": payload.comment, "created_at": now,
        }
    )

    # Check if fully repaid
    result = await db.execute(
        text("SELECT COALESCE(SUM(amount), 0) as total FROM loan_repayments WHERE loan_id = :loan_id"),
        {"loan_id": loan_id}
    )
    total_repaid = result.fetchone().total

    if total_repaid >= loan.amount:
        await db.execute(
            text("UPDATE loans SET status = 'repaid', updated_at = :now WHERE id = :id"),
            {"id": loan_id, "now": now}
        )

    await db.commit()

    return LoanRepayment(
        id=repayment_id, loan_id=loan_id,
        amount=payload.amount, date=payload.date,
        comment=payload.comment, created_at=now,
    )


@router.delete("/{loan_id}/repayments/{repayment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repayment(
    loan_id: str,
    repayment_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Delete a repayment. Re-activates loan if no longer fully repaid."""
    result = await db.execute(
        text("SELECT id, amount FROM loans WHERE id = :id AND user_id = :user_id"),
        {"id": loan_id, "user_id": user_id}
    )
    loan = result.fetchone()
    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")

    await db.execute(
        text("DELETE FROM loan_repayments WHERE id = :id AND loan_id = :loan_id"),
        {"id": repayment_id, "loan_id": loan_id}
    )

    # Re-check if still fully repaid
    result = await db.execute(
        text("SELECT COALESCE(SUM(amount), 0) as total FROM loan_repayments WHERE loan_id = :loan_id"),
        {"loan_id": loan_id}
    )
    total_repaid = result.fetchone().total
    now = datetime.now(timezone.utc).isoformat()

    if total_repaid < loan.amount:
        await db.execute(
            text("UPDATE loans SET status = 'active', updated_at = :now WHERE id = :id"),
            {"id": loan_id, "now": now}
        )

    await db.commit()
