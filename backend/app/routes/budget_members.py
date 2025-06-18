# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Budget member management routes."""

from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user
from ..database import get_db
from ..models import BudgetMemberWithUser, InviteMemberRequest

router = APIRouter()


@router.get("/budgets/{budget_id}/members", response_model=list[BudgetMemberWithUser])
async def get_budget_members(
    budget_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Retrieve all members of a group budget."""
    # Verify that the user has access to the budget
    result = await db.execute(
        text("SELECT COUNT(*) as cnt FROM budget_members WHERE budget_id = :budget_id AND user_id = :user_id"),
        {"budget_id": budget_id, "user_id": user_id}
    )
    if result.fetchone().cnt == 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this budget")

    # Retrieve members with user information
    result = await db.execute(
        text("""
            SELECT
                bm.id, bm.budget_id, bm.user_id, bm.role, bm.created_at,
                u.name as user_name, u.email as user_email, u.avatar as user_avatar
            FROM budget_members bm
            JOIN users u ON bm.user_id = u.id
            WHERE bm.budget_id = :budget_id
        """),
        {"budget_id": budget_id}
    )
    rows = result.fetchall()
    return [BudgetMemberWithUser(
        id=row.id,
        budget_id=row.budget_id,
        user_id=row.user_id,
        role=row.role,
        created_at=row.created_at,
        user_name=row.user_name,
        user_email=row.user_email,
        user_avatar=row.user_avatar,
    ) for row in rows]


@router.post("/budgets/{budget_id}/members", status_code=status.HTTP_201_CREATED)
async def invite_member(
    budget_id: str,
    payload: InviteMemberRequest,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Invite a new member to a group budget."""
    # Verify that the user is the owner
    result = await db.execute(
        text("SELECT COUNT(*) as cnt FROM budget_members WHERE budget_id = :budget_id AND user_id = :user_id AND role = 'owner'"),
        {"budget_id": budget_id, "user_id": user_id}
    )
    if result.fetchone().cnt == 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to invite members")

    # Verify that the email exists in the system
    result = await db.execute(
        text("SELECT COUNT(*) as cnt FROM users WHERE email = :email"),
        {"email": payload.email}
    )
    if result.fetchone().cnt == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check if the user is already a member
    result = await db.execute(
        text("""
            SELECT COUNT(*) as cnt FROM budget_members bm
            JOIN users u ON bm.user_id = u.id
            WHERE bm.budget_id = :budget_id AND u.email = :email
        """),
        {"budget_id": budget_id, "email": payload.email}
    )
    if result.fetchone().cnt > 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already a member")

    # Create the invitation
    invitation_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    await db.execute(
        text("""
            INSERT INTO budget_invitations (id, budget_id, inviter_id, invitee_email, role, status, created_at)
            VALUES (:id, :budget_id, :inviter_id, :invitee_email, :role, 'pending', :created_at)
        """),
        {
            "id": invitation_id,
            "budget_id": budget_id,
            "inviter_id": user_id,
            "invitee_email": payload.email,
            "role": payload.role,
            "created_at": now,
        }
    )
    await db.commit()


@router.delete("/budgets/{budget_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    budget_id: str,
    member_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Remove a member from a group budget."""
    # Verify that the user is the owner
    result = await db.execute(
        text("SELECT COUNT(*) as cnt FROM budget_members WHERE budget_id = :budget_id AND user_id = :user_id AND role = 'owner'"),
        {"budget_id": budget_id, "user_id": user_id}
    )
    if result.fetchone().cnt == 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to remove members")

    await db.execute(
        text("DELETE FROM budget_members WHERE id = :id AND budget_id = :budget_id"),
        {"id": member_id, "budget_id": budget_id}
    )
    await db.commit()
