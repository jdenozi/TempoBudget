# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Category-related data models."""

from pydantic import BaseModel, Field


class Category(BaseModel):
    """Represents a category within a budget."""
    id: str = Field(..., description="Unique identifier (UUID)")
    budget_id: str = Field(..., description="ID of the budget")
    name: str = Field(..., description="Category name")
    amount: float = Field(..., description="Allocated amount")
    created_at: str = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class CreateCategory(BaseModel):
    """Request payload for creating a new category."""
    name: str = Field(..., min_length=1, description="Name for the category")
    amount: float = Field(..., ge=0, description="Initial allocated amount")


class UpdateCategory(BaseModel):
    """Request payload for updating an existing category."""
    name: str | None = Field(None, description="New name for the category")
    amount: float | None = Field(None, ge=0, description="New allocated amount")
