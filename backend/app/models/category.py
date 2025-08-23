# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Category-related data models."""

from pydantic import BaseModel, Field

VALID_TAGS = ["crédit", "besoin", "loisir", "épargne"]


class Category(BaseModel):
    """Represents a category within a budget."""
    id: str = Field(..., description="Unique identifier (UUID)")
    budget_id: str = Field(..., description="ID of the budget")
    parent_id: str | None = Field(None, description="ID of the parent category")
    name: str = Field(..., description="Category name")
    amount: float = Field(..., description="Allocated amount")
    tags: list[str] = Field(default_factory=list, description="Category tags")
    created_at: str = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class CreateCategory(BaseModel):
    """Request payload for creating a new category."""
    name: str = Field(..., min_length=1, description="Name for the category")
    amount: float = Field(0, ge=0, description="Initial allocated amount")
    parent_id: str | None = Field(None, description="Parent category ID for subcategories")
    tags: list[str] = Field(default_factory=list, description="Category tags")


class UpdateCategory(BaseModel):
    """Request payload for updating an existing category."""
    name: str | None = Field(None, description="New name for the category")
    amount: float | None = Field(None, ge=0, description="New allocated amount")
    tags: list[str] | None = Field(None, description="New tags for the category")
