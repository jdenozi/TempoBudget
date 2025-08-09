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
from ..models import BudgetMemberWithUser, InviteMemberRequest, UpdateMemberShareRequest, MemberBalance

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
                bm.id, bm.budget_id, bm.user_id, bm.role, bm.share, bm.created_at,
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
        share=row.share,
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


@router.put("/budgets/{budget_id}/members/{member_id}/share", response_model=BudgetMemberWithUser)
async def update_member_share(
    budget_id: str,
    member_id: str,
    payload: UpdateMemberShareRequest,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Update a member's share percentage."""
    # Verify that the user is the owner
    result = await db.execute(
        text("SELECT COUNT(*) as cnt FROM budget_members WHERE budget_id = :budget_id AND user_id = :user_id AND role = 'owner'"),
        {"budget_id": budget_id, "user_id": user_id}
    )
    if result.fetchone().cnt == 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update shares")

    # Update the share
    await db.execute(
        text("UPDATE budget_members SET share = :share WHERE id = :id AND budget_id = :budget_id"),
        {"share": payload.share, "id": member_id, "budget_id": budget_id}
    )
    await db.commit()

    # Return updated member
    result = await db.execute(
        text("""
            SELECT
                bm.id, bm.budget_id, bm.user_id, bm.role, bm.share, bm.created_at,
                u.name as user_name, u.email as user_email, u.avatar as user_avatar
            FROM budget_members bm
            JOIN users u ON bm.user_id = u.id
            WHERE bm.id = :id
        """),
        {"id": member_id}
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    return BudgetMemberWithUser(
        id=row.id,
        budget_id=row.budget_id,
        user_id=row.user_id,
        role=row.role,
        share=row.share,
        created_at=row.created_at,
        user_name=row.user_name,
        user_email=row.user_email,
        user_avatar=row.user_avatar,
    )


@router.get("/budgets/{budget_id}/balances", response_model=list[MemberBalance])
async def get_budget_balances(
    budget_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Calculate balances for all members of a group budget."""
    # Verify that the user has access to the budget
    result = await db.execute(
        text("SELECT COUNT(*) as cnt FROM budget_members WHERE budget_id = :budget_id AND user_id = :user_id"),
        {"budget_id": budget_id, "user_id": user_id}
    )
    if result.fetchone().cnt == 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this budget")

    # Get all members with their shares
    result = await db.execute(
        text("""
            SELECT bm.user_id, u.name as user_name, bm.share
            FROM budget_members bm
            JOIN users u ON bm.user_id = u.id
            WHERE bm.budget_id = :budget_id
        """),
        {"budget_id": budget_id}
    )
    members = result.fetchall()

    # Get total budget from categories (parent categories only, to avoid double counting)
    result = await db.execute(
        text("""
            SELECT COALESCE(SUM(amount), 0) as total
            FROM categories
            WHERE budget_id = :budget_id AND parent_id IS NULL
        """),
        {"budget_id": budget_id}
    )
    total_budget = result.fetchone().total

    # Get amount paid by each member (income transactions they contributed)
    result = await db.execute(
        text("""
            SELECT paid_by_user_id, COALESCE(SUM(amount), 0) as total_paid
            FROM transactions
            WHERE budget_id = :budget_id AND transaction_type = 'income' AND paid_by_user_id IS NOT NULL
            GROUP BY paid_by_user_id
        """),
        {"budget_id": budget_id}
    )
    paid_by_member = {row.paid_by_user_id: row.total_paid for row in result.fetchall()}

    # Calculate balances
    balances = []
    for member in members:
        total_due = total_budget * (member.share / 100)
        total_paid = paid_by_member.get(member.user_id, 0)
        balance = total_paid - total_due  # Positive = overpaid (others owe them), Negative = underpaid (owes others)

        balances.append(MemberBalance(
            user_id=member.user_id,
            user_name=member.user_name,
            share=member.share,
            total_due=round(total_due, 2),
            total_paid=round(total_paid, 2),
            balance=round(balance, 2),
        ))

    return balances
