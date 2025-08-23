# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Transaction-related data models."""

from typing import Literal
from pydantic import BaseModel, Field


class Transaction(BaseModel):
    """Represents a financial transaction."""
    id: str = Field(..., description="Unique identifier (UUID)")
    budget_id: str = Field(..., description="ID of the budget")
    category_id: str = Field(..., description="ID of the category")
    title: str = Field(..., description="Transaction title/description")
    amount: float = Field(..., description="Transaction amount")
    transaction_type: str = Field(..., description="Type: 'income' or 'expense'")
    date: str = Field(..., description="Date of the transaction")
    comment: str | None = Field(None, description="Optional comment")
    is_recurring: int = Field(..., description="Whether from recurring template (0/1)")
    paid_by_user_id: str | None = Field(None, description="ID of user who paid (for group budgets)")
    created_at: str = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class CreateTransaction(BaseModel):
    """Request payload for creating a new transaction."""
    category_id: str = Field(..., description="ID of the category")
    title: str = Field(..., min_length=1, description="Transaction title")
    amount: float = Field(..., gt=0, description="Transaction amount")
    transaction_type: Literal["income", "expense"] = Field(..., description="Type")
    date: str = Field(..., description="Date (ISO 8601 format)")
    comment: str | None = Field(None, description="Optional comment")
    paid_by_user_id: str | None = Field(None, description="ID of user who paid (for group budgets)")


class RecurringTransaction(BaseModel):
    """Represents a recurring transaction template."""
    id: str = Field(..., description="Unique identifier (UUID)")
    budget_id: str = Field(..., description="ID of the budget")
    category_id: str = Field(..., description="ID of the category")
    title: str = Field(..., description="Transaction title")
    amount: float = Field(..., description="Transaction amount")
    transaction_type: str = Field(..., description="Type: 'income' or 'expense'")
    frequency: str = Field(..., description="Frequency: daily/weekly/monthly/yearly")
    day: int | None = Field(None, description="Day of the period")
    active: int = Field(..., description="Whether active (0/1)")
    created_at: str = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class CreateRecurringTransaction(BaseModel):
    """Request payload for creating a recurring transaction."""
    category_id: str = Field(..., description="ID of the category")
    title: str = Field(..., min_length=1, description="Transaction title")
    amount: float = Field(..., gt=0, description="Transaction amount")
    transaction_type: Literal["income", "expense"] = Field(..., description="Type")
    frequency: Literal["daily", "weekly", "monthly", "yearly"] = Field(..., description="Frequency")
    day: int | None = Field(None, description="Day of the period")
