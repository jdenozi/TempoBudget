# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Project-related data models."""

from typing import Literal
from pydantic import BaseModel, Field


class ProjectCategory(BaseModel):
    """A category within a project with a planned budget amount."""
    id: str = Field(..., description="Unique identifier")
    project_id: str = Field(..., description="Project ID")
    name: str = Field(..., description="Category name")
    planned_amount: float = Field(..., description="Planned budget amount")
    created_at: str = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class ProjectCategoryWithSpent(ProjectCategory):
    """Project category with computed spent totals."""
    total_spent: float = Field(0, description="Total spent in this category")
    remaining: float = Field(0, description="Remaining budget")


class Project(BaseModel):
    """A budget project (e.g. wedding, renovation)."""
    id: str = Field(..., description="Unique identifier")
    user_id: str = Field(..., description="Owner user ID")
    name: str = Field(..., description="Project name")
    description: str | None = Field(None, description="Project description")
    target_date: str | None = Field(None, description="Target completion date")
    total_budget: float = Field(..., description="Total planned budget")
    status: str = Field(..., description="active, completed, or abandoned")
    mode: str = Field(..., description="personal or pro")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    total_spent: float = Field(0, description="Total spent across all categories")
    remaining: float = Field(0, description="Remaining budget")
    categories: list[ProjectCategoryWithSpent] = Field(default_factory=list, description="Project categories with spent")

    class Config:
        from_attributes = True


class CreateProject(BaseModel):
    """Request payload for creating a project."""
    name: str = Field(..., min_length=1, description="Project name")
    description: str | None = Field(None, description="Project description")
    target_date: str | None = Field(None, description="Target completion date")
    total_budget: float = Field(..., ge=0, description="Total planned budget")
    mode: Literal["personal", "pro"] = Field(..., description="Project mode")


class UpdateProject(BaseModel):
    """Request payload for updating a project."""
    name: str | None = Field(None, min_length=1, description="Project name")
    description: str | None = Field(None, description="Project description")
    target_date: str | None = Field(None, description="Target completion date")
    total_budget: float | None = Field(None, ge=0, description="Total planned budget")
    status: Literal["active", "completed", "abandoned"] | None = Field(None, description="Project status")


class CreateProjectCategory(BaseModel):
    """Request payload for creating a project category."""
    name: str = Field(..., min_length=1, description="Category name")
    planned_amount: float = Field(..., ge=0, description="Planned budget amount")


class UpdateProjectCategory(BaseModel):
    """Request payload for updating a project category."""
    name: str | None = Field(None, min_length=1, description="Category name")
    planned_amount: float | None = Field(None, ge=0, description="Planned budget amount")


class ProjectPlannedExpense(BaseModel):
    """A planned/future expense within a project."""
    id: str = Field(..., description="Unique identifier")
    project_id: str = Field(..., description="Project ID")
    project_category_id: str = Field(..., description="Project category ID")
    description: str = Field(..., description="Expense description")
    amount: float = Field(..., description="Planned amount")
    due_date: str | None = Field(None, description="Due date")
    reminder_date: str | None = Field(None, description="Reminder date")
    status: str = Field(..., description="pending or paid")
    transaction_id: str | None = Field(None, description="Linked personal transaction ID")
    pro_transaction_id: str | None = Field(None, description="Linked pro transaction ID")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    category_name: str | None = Field(None, description="Resolved category name")

    class Config:
        from_attributes = True


class CreatePlannedExpense(BaseModel):
    """Request payload for creating a planned expense."""
    project_category_id: str = Field(..., description="Project category ID")
    description: str = Field(..., min_length=1, description="Expense description")
    amount: float = Field(..., gt=0, description="Planned amount")
    due_date: str | None = Field(None, description="Due date")
    reminder_date: str | None = Field(None, description="Reminder date")


class UpdatePlannedExpense(BaseModel):
    """Request payload for updating a planned expense."""
    project_category_id: str | None = Field(None, description="Project category ID")
    description: str | None = Field(None, min_length=1, description="Expense description")
    amount: float | None = Field(None, gt=0, description="Planned amount")
    due_date: str | None = Field(None, description="Due date")
    reminder_date: str | None = Field(None, description="Reminder date")
    status: Literal["pending", "paid"] | None = Field(None, description="Expense status")
    transaction_id: str | None = Field(None, description="Linked personal transaction ID")
    pro_transaction_id: str | None = Field(None, description="Linked pro transaction ID")


class ProjectSummary(BaseModel):
    """Summary of a project for list views."""
    id: str = Field(..., description="Project ID")
    name: str = Field(..., description="Project name")
    mode: str = Field(..., description="personal or pro")
    status: str = Field(..., description="Project status")
    total_budget: float = Field(..., description="Total planned budget")
    total_spent: float = Field(0, description="Total spent")
    remaining: float = Field(0, description="Remaining budget")
    percentage: float = Field(0, description="Percentage spent")
    category_count: int = Field(0, description="Number of categories")
    planned_expense_count: int = Field(0, description="Total planned expenses")
    pending_expense_count: int = Field(0, description="Pending planned expenses")
    target_date: str | None = Field(None, description="Target completion date")


class ProjectReminder(BaseModel):
    """A reminder for an upcoming planned expense."""
    id: str = Field(..., description="Planned expense ID")
    project_id: str = Field(..., description="Project ID")
    project_name: str = Field(..., description="Project name")
    description: str = Field(..., description="Expense description")
    amount: float = Field(..., description="Planned amount")
    due_date: str | None = Field(None, description="Due date")
    reminder_date: str = Field(..., description="Reminder date")
    category_name: str | None = Field(None, description="Category name")
