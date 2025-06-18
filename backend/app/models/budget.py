# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Budget-related data models."""

from typing import Literal
from pydantic import BaseModel, Field


class Budget(BaseModel):
    """Represents a budget in the system."""
    id: str = Field(..., description="Unique identifier (UUID)")
    user_id: str = Field(..., description="ID of the user who created the budget")
    name: str = Field(..., description="Budget name/title")
    budget_type: str = Field(..., description="Type: 'personal' or 'group'")
    is_active: int = Field(..., description="Whether budget is active (0/1)")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class CreateBudget(BaseModel):
    """Request payload for creating a new budget."""
    name: str = Field(..., min_length=1, description="Name/title for the budget")
    budget_type: Literal["personal", "group"] = Field(..., description="Type of budget")


class UpdateBudget(BaseModel):
    """Request payload for updating an existing budget."""
    name: str | None = Field(None, description="New name for the budget")
    is_active: int | None = Field(None, ge=0, le=1, description="New active status")
