# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Project budget management routes."""

from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import BaseModel, EmailStr, Field

from ..auth import get_current_user
from ..database import get_db
from ..models.project import (
    Project, CreateProject, UpdateProject,
    ProjectCategory, ProjectCategoryWithSpent,
    CreateProjectCategory, UpdateProjectCategory,
    ProjectPlannedExpense, CreatePlannedExpense, UpdatePlannedExpense,
    ProjectSummary, ProjectReminder,
)

router = APIRouter()


# ────────────────────────────── Member models ──────────────────────────────


class ProjectMemberWithUser(BaseModel):
    id: str
    project_id: str
    user_id: str
    role: str
    created_at: str
    user_name: str
    user_email: str
    user_avatar: str | None = None


class InviteProjectMemberRequest(BaseModel):
    email: EmailStr
    role: str = Field("member", pattern="^(member|owner)$")


class ProjectInvitationWithDetails(BaseModel):
    id: str
    project_id: str
    project_name: str
    inviter_id: str
    inviter_name: str
    invitee_email: str
    role: str
    status: str
    created_at: str


# ────────────────────────────── Helpers ──────────────────────────────


async def _get_category_spent(db: AsyncSession, category_id: str) -> float:
    """Get total spent for a project category across personal + pro transactions."""
    result = await db.execute(
        text("""
            SELECT COALESCE(SUM(amount), 0) as total FROM (
                SELECT amount FROM transactions WHERE project_category_id = :cid
                UNION ALL
                SELECT amount FROM pro_transactions WHERE project_category_id = :cid
            )
        """),
        {"cid": category_id}
    )
    return result.fetchone().total


async def _get_project_categories_with_spent(
    db: AsyncSession, project_id: str
) -> list[ProjectCategoryWithSpent]:
    """Get all categories for a project with spent amounts."""
    result = await db.execute(
        text("""
            SELECT id, project_id, name, planned_amount, created_at
            FROM project_categories WHERE project_id = :pid ORDER BY created_at ASC
        """),
        {"pid": project_id}
    )
    categories = []
    for row in result.fetchall():
        spent = await _get_category_spent(db, row.id)
        categories.append(ProjectCategoryWithSpent(
            id=row.id, project_id=row.project_id,
            name=row.name, planned_amount=row.planned_amount,
            created_at=row.created_at,
            total_spent=round(spent, 2),
            remaining=round(row.planned_amount - spent, 2),
        ))
    return categories


async def _verify_project_access(
    db: AsyncSession, project_id: str, user_id: str
):
    """Verify project exists and user has access (owner or member). Returns row or raises 404."""
    result = await db.execute(
        text("""
            SELECT p.* FROM projects p
            WHERE p.id = :id AND (
                p.user_id = :uid
                OR EXISTS (SELECT 1 FROM project_members pm WHERE pm.project_id = p.id AND pm.user_id = :uid)
            )
        """),
        {"id": project_id, "uid": user_id}
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return row


async def _verify_project_owner(
    db: AsyncSession, project_id: str, user_id: str
):
    """Verify user is the project owner. Returns row or raises 403."""
    result = await db.execute(
        text("SELECT * FROM projects WHERE id = :id AND user_id = :uid"),
        {"id": project_id, "uid": user_id}
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return row


# ────────────────────────────── Projects CRUD ──────────────────────────────


@router.get("", response_model=list[Project])
async def get_projects(
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    project_status: str | None = Query(None, alias="status"),
    mode: str | None = Query(None),
):
    """Get all projects for the current user (owned + shared)."""
    query = """
        SELECT DISTINCT p.* FROM projects p
        LEFT JOIN project_members pm ON pm.project_id = p.id
        WHERE (p.user_id = :uid OR pm.user_id = :uid)
    """
    params: dict = {"uid": user_id}

    if project_status:
        query += " AND p.status = :status"
        params["status"] = project_status
    if mode:
        query += " AND p.mode = :mode"
        params["mode"] = mode

    query += " ORDER BY p.created_at DESC"

    result = await db.execute(text(query), params)
    projects = []
    for row in result.fetchall():
        categories = await _get_project_categories_with_spent(db, row.id)
        total_spent = sum(c.total_spent for c in categories)
        projects.append(Project(
            id=row.id, user_id=row.user_id, name=row.name,
            description=row.description, target_date=row.target_date,
            total_budget=row.total_budget, status=row.status, mode=row.mode,
            created_at=row.created_at, updated_at=row.updated_at,
            total_spent=round(total_spent, 2),
            remaining=round(row.total_budget - total_spent, 2),
            categories=categories,
        ))
    return projects


@router.get("/summaries", response_model=list[ProjectSummary])
async def get_project_summaries(
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Get lightweight summaries for all projects (owned + shared)."""
    result = await db.execute(
        text("""
            SELECT DISTINCT p.* FROM projects p
            LEFT JOIN project_members pm ON pm.project_id = p.id
            WHERE (p.user_id = :uid OR pm.user_id = :uid)
            ORDER BY p.created_at DESC
        """),
        {"uid": user_id}
    )
    summaries = []
    for row in result.fetchall():
        categories = await _get_project_categories_with_spent(db, row.id)
        total_spent = sum(c.total_spent for c in categories)

        # Count planned expenses
        exp_result = await db.execute(
            text("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending
                FROM project_planned_expenses WHERE project_id = :pid
            """),
            {"pid": row.id}
        )
        exp_row = exp_result.fetchone()

        percentage = (total_spent / row.total_budget * 100) if row.total_budget > 0 else 0

        summaries.append(ProjectSummary(
            id=row.id, name=row.name, mode=row.mode, status=row.status,
            total_budget=row.total_budget,
            total_spent=round(total_spent, 2),
            remaining=round(row.total_budget - total_spent, 2),
            percentage=round(percentage, 1),
            category_count=len(categories),
            planned_expense_count=exp_row.total,
            pending_expense_count=exp_row.pending or 0,
            target_date=row.target_date,
        ))
    return summaries


@router.get("/reminders", response_model=list[ProjectReminder])
async def get_reminders(
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Get pending reminders (planned expenses with reminder_date <= today)."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    result = await db.execute(
        text("""
            SELECT pe.id, pe.project_id, p.name as project_name,
                   pe.description, pe.amount, pe.due_date,
                   pe.reminder_date, pc.name as category_name
            FROM project_planned_expenses pe
            JOIN projects p ON pe.project_id = p.id
            JOIN project_categories pc ON pe.project_category_id = pc.id
            LEFT JOIN project_members pm ON pm.project_id = p.id
            WHERE (p.user_id = :uid OR pm.user_id = :uid)
              AND pe.status = 'pending'
              AND pe.reminder_date IS NOT NULL
              AND pe.reminder_date <= :today
            ORDER BY pe.reminder_date ASC
        """),
        {"uid": user_id, "today": today}
    )
    return [
        ProjectReminder(
            id=row.id, project_id=row.project_id,
            project_name=row.project_name,
            description=row.description, amount=row.amount,
            due_date=row.due_date, reminder_date=row.reminder_date,
            category_name=row.category_name,
        )
        for row in result.fetchall()
    ]


@router.post("", response_model=Project)
async def create_project(
    payload: CreateProject,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Create a new project."""
    project_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    await db.execute(
        text("""
            INSERT INTO projects (id, user_id, name, description, target_date,
                                  total_budget, status, mode, created_at, updated_at)
            VALUES (:id, :uid, :name, :description, :target_date,
                    :total_budget, 'active', :mode, :created_at, :updated_at)
        """),
        {
            "id": project_id, "uid": user_id,
            "name": payload.name, "description": payload.description,
            "target_date": payload.target_date,
            "total_budget": payload.total_budget, "mode": payload.mode,
            "created_at": now, "updated_at": now,
        }
    )
    # Auto-add creator as owner member
    await db.execute(
        text("""
            INSERT INTO project_members (id, project_id, user_id, role, created_at)
            VALUES (:id, :pid, :uid, 'owner', :created_at)
        """),
        {"id": str(uuid4()), "pid": project_id, "uid": user_id, "created_at": now}
    )
    await db.commit()

    return Project(
        id=project_id, user_id=user_id, name=payload.name,
        description=payload.description, target_date=payload.target_date,
        total_budget=payload.total_budget, status="active", mode=payload.mode,
        created_at=now, updated_at=now,
        total_spent=0, remaining=payload.total_budget, categories=[],
    )


@router.get("/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Get a project with its categories and spent totals."""
    row = await _verify_project_access(db, project_id, user_id)
    categories = await _get_project_categories_with_spent(db, project_id)
    total_spent = sum(c.total_spent for c in categories)

    return Project(
        id=row.id, user_id=row.user_id, name=row.name,
        description=row.description, target_date=row.target_date,
        total_budget=row.total_budget, status=row.status, mode=row.mode,
        created_at=row.created_at, updated_at=row.updated_at,
        total_spent=round(total_spent, 2),
        remaining=round(row.total_budget - total_spent, 2),
        categories=categories,
    )


@router.put("/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    payload: UpdateProject,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Update a project."""
    await _verify_project_access(db, project_id, user_id)

    updates = []
    params: dict = {"id": project_id}
    now = datetime.now(timezone.utc).isoformat()

    for field in ["name", "description", "target_date", "total_budget", "status"]:
        value = getattr(payload, field, None)
        if value is not None:
            updates.append(f"{field} = :{field}")
            params[field] = value

    if updates:
        updates.append("updated_at = :updated_at")
        params["updated_at"] = now
        query = f"UPDATE projects SET {', '.join(updates)} WHERE id = :id"
        await db.execute(text(query), params)
        await db.commit()

    # Return updated project
    result = await db.execute(
        text("SELECT * FROM projects WHERE id = :id"), {"id": project_id}
    )
    row = result.fetchone()
    categories = await _get_project_categories_with_spent(db, project_id)
    total_spent = sum(c.total_spent for c in categories)

    return Project(
        id=row.id, user_id=row.user_id, name=row.name,
        description=row.description, target_date=row.target_date,
        total_budget=row.total_budget, status=row.status, mode=row.mode,
        created_at=row.created_at, updated_at=row.updated_at,
        total_spent=round(total_spent, 2),
        remaining=round(row.total_budget - total_spent, 2),
        categories=categories,
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Delete a project (cascades to categories, planned expenses, and members)."""
    await _verify_project_owner(db, project_id, user_id)

    # Unlink transactions before deleting (SET NULL would be handled by FK, but explicit is safer)
    await db.execute(
        text("""
            UPDATE transactions SET project_category_id = NULL
            WHERE project_category_id IN (
                SELECT id FROM project_categories WHERE project_id = :pid
            )
        """),
        {"pid": project_id}
    )
    await db.execute(
        text("""
            UPDATE pro_transactions SET project_category_id = NULL
            WHERE project_category_id IN (
                SELECT id FROM project_categories WHERE project_id = :pid
            )
        """),
        {"pid": project_id}
    )

    await db.execute(
        text("DELETE FROM project_planned_expenses WHERE project_id = :pid"),
        {"pid": project_id}
    )
    await db.execute(
        text("DELETE FROM project_categories WHERE project_id = :pid"),
        {"pid": project_id}
    )
    await db.execute(
        text("DELETE FROM projects WHERE id = :id"), {"id": project_id}
    )
    await db.commit()


# ────────────────────────────── Project Categories ──────────────────────────────


@router.get("/{project_id}/categories", response_model=list[ProjectCategoryWithSpent])
async def get_project_categories(
    project_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Get project categories with spent amounts."""
    await _verify_project_access(db, project_id, user_id)
    return await _get_project_categories_with_spent(db, project_id)


@router.post("/{project_id}/categories", response_model=ProjectCategory)
async def create_project_category(
    project_id: str,
    payload: CreateProjectCategory,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Add a category to a project."""
    await _verify_project_access(db, project_id, user_id)

    cat_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    await db.execute(
        text("""
            INSERT INTO project_categories (id, project_id, name, planned_amount, created_at)
            VALUES (:id, :pid, :name, :planned_amount, :created_at)
        """),
        {
            "id": cat_id, "pid": project_id,
            "name": payload.name, "planned_amount": payload.planned_amount,
            "created_at": now,
        }
    )
    await db.commit()

    return ProjectCategory(
        id=cat_id, project_id=project_id,
        name=payload.name, planned_amount=payload.planned_amount,
        created_at=now,
    )


@router.put("/{project_id}/categories/{category_id}", response_model=ProjectCategory)
async def update_project_category(
    project_id: str,
    category_id: str,
    payload: UpdateProjectCategory,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Update a project category."""
    await _verify_project_access(db, project_id, user_id)

    updates = []
    params: dict = {"id": category_id, "pid": project_id}

    for field in ["name", "planned_amount"]:
        value = getattr(payload, field, None)
        if value is not None:
            updates.append(f"{field} = :{field}")
            params[field] = value

    if updates:
        query = f"UPDATE project_categories SET {', '.join(updates)} WHERE id = :id AND project_id = :pid"
        await db.execute(text(query), params)
        await db.commit()

    result = await db.execute(
        text("SELECT * FROM project_categories WHERE id = :id AND project_id = :pid"),
        {"id": category_id, "pid": project_id}
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    return ProjectCategory(
        id=row.id, project_id=row.project_id,
        name=row.name, planned_amount=row.planned_amount,
        created_at=row.created_at,
    )


@router.delete("/{project_id}/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_category(
    project_id: str,
    category_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Delete a project category."""
    await _verify_project_access(db, project_id, user_id)

    # Unlink transactions
    await db.execute(
        text("UPDATE transactions SET project_category_id = NULL WHERE project_category_id = :cid"),
        {"cid": category_id}
    )
    await db.execute(
        text("UPDATE pro_transactions SET project_category_id = NULL WHERE project_category_id = :cid"),
        {"cid": category_id}
    )

    # Delete planned expenses for this category
    await db.execute(
        text("DELETE FROM project_planned_expenses WHERE project_category_id = :cid"),
        {"cid": category_id}
    )

    await db.execute(
        text("DELETE FROM project_categories WHERE id = :id AND project_id = :pid"),
        {"id": category_id, "pid": project_id}
    )
    await db.commit()


# ────────────────────────────── Planned Expenses ──────────────────────────────


@router.get("/{project_id}/planned-expenses", response_model=list[ProjectPlannedExpense])
async def get_planned_expenses(
    project_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Get all planned expenses for a project."""
    await _verify_project_access(db, project_id, user_id)

    result = await db.execute(
        text("""
            SELECT pe.*, pc.name as category_name
            FROM project_planned_expenses pe
            JOIN project_categories pc ON pe.project_category_id = pc.id
            WHERE pe.project_id = :pid
            ORDER BY pe.due_date ASC NULLS LAST, pe.created_at ASC
        """),
        {"pid": project_id}
    )
    return [
        ProjectPlannedExpense(
            id=row.id, project_id=row.project_id,
            project_category_id=row.project_category_id,
            description=row.description, amount=row.amount,
            due_date=row.due_date, reminder_date=row.reminder_date,
            status=row.status,
            transaction_id=row.transaction_id,
            pro_transaction_id=row.pro_transaction_id,
            created_at=row.created_at, updated_at=row.updated_at,
            category_name=row.category_name,
        )
        for row in result.fetchall()
    ]


@router.post("/{project_id}/planned-expenses", response_model=ProjectPlannedExpense)
async def create_planned_expense(
    project_id: str,
    payload: CreatePlannedExpense,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Add a planned expense to a project."""
    await _verify_project_access(db, project_id, user_id)

    # Verify category belongs to this project
    cat_result = await db.execute(
        text("SELECT id, name FROM project_categories WHERE id = :cid AND project_id = :pid"),
        {"cid": payload.project_category_id, "pid": project_id}
    )
    cat_row = cat_result.fetchone()
    if not cat_row:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found in this project")

    expense_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    await db.execute(
        text("""
            INSERT INTO project_planned_expenses
                (id, project_id, project_category_id, description, amount,
                 due_date, reminder_date, status, created_at, updated_at)
            VALUES (:id, :pid, :cid, :description, :amount,
                    :due_date, :reminder_date, 'pending', :created_at, :updated_at)
        """),
        {
            "id": expense_id, "pid": project_id,
            "cid": payload.project_category_id,
            "description": payload.description, "amount": payload.amount,
            "due_date": payload.due_date, "reminder_date": payload.reminder_date,
            "created_at": now, "updated_at": now,
        }
    )
    await db.commit()

    return ProjectPlannedExpense(
        id=expense_id, project_id=project_id,
        project_category_id=payload.project_category_id,
        description=payload.description, amount=payload.amount,
        due_date=payload.due_date, reminder_date=payload.reminder_date,
        status="pending", transaction_id=None, pro_transaction_id=None,
        created_at=now, updated_at=now,
        category_name=cat_row.name,
    )


@router.put("/{project_id}/planned-expenses/{expense_id}", response_model=ProjectPlannedExpense)
async def update_planned_expense(
    project_id: str,
    expense_id: str,
    payload: UpdatePlannedExpense,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Update a planned expense (including marking as paid and linking transaction)."""
    await _verify_project_access(db, project_id, user_id)

    result = await db.execute(
        text("SELECT id FROM project_planned_expenses WHERE id = :id AND project_id = :pid"),
        {"id": expense_id, "pid": project_id}
    )
    if not result.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Planned expense not found")

    updates = []
    params: dict = {"id": expense_id}
    now = datetime.now(timezone.utc).isoformat()

    for field in ["project_category_id", "description", "amount", "due_date",
                   "reminder_date", "status", "transaction_id", "pro_transaction_id"]:
        value = getattr(payload, field, None)
        if value is not None:
            updates.append(f"{field} = :{field}")
            params[field] = value

    if updates:
        updates.append("updated_at = :updated_at")
        params["updated_at"] = now
        query = f"UPDATE project_planned_expenses SET {', '.join(updates)} WHERE id = :id"
        await db.execute(text(query), params)
        await db.commit()

    # Return updated
    result = await db.execute(
        text("""
            SELECT pe.*, pc.name as category_name
            FROM project_planned_expenses pe
            JOIN project_categories pc ON pe.project_category_id = pc.id
            WHERE pe.id = :id
        """),
        {"id": expense_id}
    )
    row = result.fetchone()

    return ProjectPlannedExpense(
        id=row.id, project_id=row.project_id,
        project_category_id=row.project_category_id,
        description=row.description, amount=row.amount,
        due_date=row.due_date, reminder_date=row.reminder_date,
        status=row.status,
        transaction_id=row.transaction_id,
        pro_transaction_id=row.pro_transaction_id,
        created_at=row.created_at, updated_at=row.updated_at,
        category_name=row.category_name,
    )


@router.delete("/{project_id}/planned-expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_planned_expense(
    project_id: str,
    expense_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Delete a planned expense."""
    await _verify_project_access(db, project_id, user_id)

    result = await db.execute(
        text("SELECT id FROM project_planned_expenses WHERE id = :id AND project_id = :pid"),
        {"id": expense_id, "pid": project_id}
    )
    if not result.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Planned expense not found")

    await db.execute(
        text("DELETE FROM project_planned_expenses WHERE id = :id"),
        {"id": expense_id}
    )
    await db.commit()


# ────────────────────────────── Project Transactions ──────────────────────────────


@router.get("/{project_id}/transactions")
async def get_project_transactions(
    project_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Get all transactions linked to this project (personal + pro)."""
    await _verify_project_access(db, project_id, user_id)

    # Get category IDs for this project
    cat_result = await db.execute(
        text("SELECT id FROM project_categories WHERE project_id = :pid"),
        {"pid": project_id}
    )
    cat_ids = [row.id for row in cat_result.fetchall()]

    if not cat_ids:
        return []

    placeholders = ", ".join(f":cid{i}" for i in range(len(cat_ids)))
    params = {f"cid{i}": cid for i, cid in enumerate(cat_ids)}

    # Personal transactions
    personal_result = await db.execute(
        text(f"""
            SELECT t.id, t.title, t.amount, t.transaction_type, t.date, t.comment,
                   t.project_category_id, c.name as category_name,
                   pc.name as project_category_name, 'personal' as source
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            LEFT JOIN project_categories pc ON t.project_category_id = pc.id
            WHERE t.project_category_id IN ({placeholders})
        """),
        params
    )
    personal = [dict(row._mapping) for row in personal_result.fetchall()]

    # Pro transactions
    pro_result = await db.execute(
        text(f"""
            SELECT t.id, t.title, t.amount, t.transaction_type, t.date, t.comment,
                   t.project_category_id, pc2.name as category_name,
                   pc.name as project_category_name, 'pro' as source
            FROM pro_transactions t
            LEFT JOIN pro_categories pc2 ON t.category_id = pc2.id
            LEFT JOIN project_categories pc ON t.project_category_id = pc.id
            WHERE t.project_category_id IN ({placeholders})
        """),
        params
    )
    pro = [dict(row._mapping) for row in pro_result.fetchall()]

    # Merge and sort by date
    all_transactions = personal + pro
    all_transactions.sort(key=lambda t: t["date"], reverse=True)

    return all_transactions


# ────────────────────────────── Project Members ──────────────────────────────


@router.get("/{project_id}/members", response_model=list[ProjectMemberWithUser])
async def get_project_members(
    project_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Get all members of a project."""
    await _verify_project_access(db, project_id, user_id)

    result = await db.execute(
        text("""
            SELECT pm.id, pm.project_id, pm.user_id, pm.role, pm.created_at,
                   u.name as user_name, u.email as user_email, u.avatar as user_avatar
            FROM project_members pm
            JOIN users u ON pm.user_id = u.id
            WHERE pm.project_id = :pid
            ORDER BY pm.created_at ASC
        """),
        {"pid": project_id}
    )
    return [
        ProjectMemberWithUser(
            id=row.id, project_id=row.project_id, user_id=row.user_id,
            role=row.role, created_at=row.created_at,
            user_name=row.user_name, user_email=row.user_email,
            user_avatar=row.user_avatar,
        )
        for row in result.fetchall()
    ]


@router.post("/{project_id}/members", status_code=status.HTTP_201_CREATED)
async def invite_project_member(
    project_id: str,
    payload: InviteProjectMemberRequest,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Invite a member to a project."""
    await _verify_project_owner(db, project_id, user_id)

    # Verify email exists in system
    result = await db.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": payload.email}
    )
    if not result.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check not already a member
    result = await db.execute(
        text("""
            SELECT COUNT(*) as cnt FROM project_members pm
            JOIN users u ON pm.user_id = u.id
            WHERE pm.project_id = :pid AND u.email = :email
        """),
        {"pid": project_id, "email": payload.email}
    )
    if result.fetchone().cnt > 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already a member")

    # Check no pending invitation
    result = await db.execute(
        text("""
            SELECT COUNT(*) as cnt FROM project_invitations
            WHERE project_id = :pid AND invitee_email = :email AND status = 'pending'
        """),
        {"pid": project_id, "email": payload.email}
    )
    if result.fetchone().cnt > 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invitation already pending")

    invitation_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    await db.execute(
        text("""
            INSERT INTO project_invitations (id, project_id, inviter_id, invitee_email, role, status, created_at)
            VALUES (:id, :pid, :inviter_id, :email, :role, 'pending', :created_at)
        """),
        {
            "id": invitation_id, "pid": project_id,
            "inviter_id": user_id, "email": payload.email,
            "role": payload.role, "created_at": now,
        }
    )
    await db.commit()
    return {"message": "Invitation sent"}


@router.delete("/{project_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_project_member(
    project_id: str,
    member_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Remove a member from a project (owner only, cannot remove self)."""
    await _verify_project_owner(db, project_id, user_id)

    # Don't allow removing the owner
    result = await db.execute(
        text("SELECT user_id, role FROM project_members WHERE id = :id AND project_id = :pid"),
        {"id": member_id, "pid": project_id}
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    if row.role == "owner" and row.user_id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove yourself as owner")

    await db.execute(
        text("DELETE FROM project_members WHERE id = :id AND project_id = :pid"),
        {"id": member_id, "pid": project_id}
    )
    await db.commit()


# ────────────────────────────── Project Invitations ──────────────────────────────


@router.get("/invitations/pending", response_model=list[ProjectInvitationWithDetails])
async def get_my_project_invitations(
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Get all pending project invitations for the current user."""
    result = await db.execute(
        text("SELECT email FROM users WHERE id = :id"),
        {"id": user_id}
    )
    user_row = result.fetchone()
    if not user_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    result = await db.execute(
        text("""
            SELECT pi.id, pi.project_id, p.name as project_name,
                   pi.inviter_id, u.name as inviter_name,
                   pi.invitee_email, pi.role, pi.status, pi.created_at
            FROM project_invitations pi
            JOIN projects p ON pi.project_id = p.id
            JOIN users u ON pi.inviter_id = u.id
            WHERE pi.invitee_email = :email AND pi.status = 'pending'
            ORDER BY pi.created_at DESC
        """),
        {"email": user_row.email}
    )
    return [
        ProjectInvitationWithDetails(
            id=row.id, project_id=row.project_id, project_name=row.project_name,
            inviter_id=row.inviter_id, inviter_name=row.inviter_name,
            invitee_email=row.invitee_email, role=row.role,
            status=row.status, created_at=row.created_at,
        )
        for row in result.fetchall()
    ]


@router.post("/invitations/{invitation_id}/accept")
async def accept_project_invitation(
    invitation_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Accept a project invitation."""
    result = await db.execute(
        text("SELECT project_id, invitee_email, role, status FROM project_invitations WHERE id = :id"),
        {"id": invitation_id}
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")
    if row.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation is not pending")

    # Verify recipient
    result = await db.execute(
        text("SELECT email FROM users WHERE id = :id"),
        {"id": user_id}
    )
    user_row = result.fetchone()
    if user_row.email != row.invitee_email:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the intended recipient")

    # Add member
    member_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    await db.execute(
        text("""
            INSERT INTO project_members (id, project_id, user_id, role, created_at)
            VALUES (:id, :pid, :uid, :role, :created_at)
        """),
        {"id": member_id, "pid": row.project_id, "uid": user_id, "role": row.role, "created_at": now}
    )
    await db.execute(
        text("UPDATE project_invitations SET status = 'accepted' WHERE id = :id"),
        {"id": invitation_id}
    )
    await db.commit()
    return {"message": "Invitation accepted"}


@router.post("/invitations/{invitation_id}/reject")
async def reject_project_invitation(
    invitation_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Reject a project invitation."""
    result = await db.execute(
        text("SELECT invitee_email, status FROM project_invitations WHERE id = :id"),
        {"id": invitation_id}
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")
    if row.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation is not pending")

    result = await db.execute(
        text("SELECT email FROM users WHERE id = :id"),
        {"id": user_id}
    )
    user_row = result.fetchone()
    if user_row.email != row.invitee_email:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the intended recipient")

    await db.execute(
        text("UPDATE project_invitations SET status = 'rejected' WHERE id = :id"),
        {"id": invitation_id}
    )
    await db.commit()
    return {"message": "Invitation rejected"}
