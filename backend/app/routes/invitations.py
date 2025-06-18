# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Budget invitation routes."""

from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user
from ..database import get_db
from ..models import BudgetInvitationWithDetails

router = APIRouter()


@router.get("", response_model=list[BudgetInvitationWithDetails])
async def get_my_invitations(
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Retrieve all pending invitations for the authenticated user."""
    # Get user's email
    result = await db.execute(
        text("SELECT email FROM users WHERE id = :id"),
        {"id": user_id}
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user_email = row.email

    # Fetch pending invitations
    result = await db.execute(
        text("""
            SELECT
                bi.id, bi.budget_id, b.name as budget_name, bi.inviter_id, u.name as inviter_name,
                bi.invitee_email, bi.role, bi.status, bi.created_at
            FROM budget_invitations bi
            JOIN budgets b ON bi.budget_id = b.id
            JOIN users u ON bi.inviter_id = u.id
            WHERE bi.invitee_email = :email AND bi.status = 'pending'
        """),
        {"email": user_email}
    )
    rows = result.fetchall()
    return [BudgetInvitationWithDetails(
        id=row.id,
        budget_id=row.budget_id,
        budget_name=row.budget_name,
        inviter_id=row.inviter_id,
        inviter_name=row.inviter_name,
        invitee_email=row.invitee_email,
        role=row.role,
        status=row.status,
        created_at=row.created_at,
    ) for row in rows]


@router.post("/{invitation_id}/accept")
async def accept_invitation(
    invitation_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Accept a budget invitation."""
    # Get the invitation details
    result = await db.execute(
        text("SELECT budget_id, invitee_email, role, status FROM budget_invitations WHERE id = :id"),
        {"id": invitation_id}
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")

    if row.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation is not pending")

    # Verify that the invitation is for this user
    result = await db.execute(
        text("SELECT email FROM users WHERE id = :id"),
        {"id": user_id}
    )
    user_row = result.fetchone()
    if user_row.email != row.invitee_email:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the intended recipient")

    # Add the member to the budget
    member_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    await db.execute(
        text("""
            INSERT INTO budget_members (id, budget_id, user_id, role, created_at)
            VALUES (:id, :budget_id, :user_id, :role, :created_at)
        """),
        {
            "id": member_id,
            "budget_id": row.budget_id,
            "user_id": user_id,
            "role": row.role,
            "created_at": now,
        }
    )

    # Mark the invitation as accepted
    await db.execute(
        text("UPDATE budget_invitations SET status = 'accepted' WHERE id = :id"),
        {"id": invitation_id}
    )
    await db.commit()

    return {"message": "Invitation accepted"}


@router.post("/{invitation_id}/reject")
async def reject_invitation(
    invitation_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Reject a budget invitation."""
    # Get the invitation details
    result = await db.execute(
        text("SELECT invitee_email, status FROM budget_invitations WHERE id = :id"),
        {"id": invitation_id}
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")

    if row.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation is not pending")

    # Verify that the invitation is for this user
    result = await db.execute(
        text("SELECT email FROM users WHERE id = :id"),
        {"id": user_id}
    )
    user_row = result.fetchone()
    if user_row.email != row.invitee_email:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the intended recipient")

    # Mark the invitation as rejected
    await db.execute(
        text("UPDATE budget_invitations SET status = 'rejected' WHERE id = :id"),
        {"id": invitation_id}
    )
    await db.commit()

    return {"message": "Invitation rejected"}
