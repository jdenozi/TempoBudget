# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Budget member data models."""

from typing import Literal
from pydantic import BaseModel, EmailStr, Field


class BudgetMember(BaseModel):
    """Represents a member of a group budget."""
    id: str = Field(..., description="Unique identifier (UUID)")
    budget_id: str = Field(..., description="ID of the budget")
    user_id: str = Field(..., description="ID of the user")
    role: str = Field(..., description="Role: 'owner' or 'member'")
    created_at: str = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class BudgetMemberWithUser(BaseModel):
    """Budget member with associated user information."""
    id: str = Field(..., description="Unique identifier (UUID)")
    budget_id: str = Field(..., description="ID of the budget")
    user_id: str = Field(..., description="ID of the user")
    role: str = Field(..., description="Role of the member")
    created_at: str = Field(..., description="Creation timestamp")
    user_name: str = Field(..., description="User's display name")
    user_email: str = Field(..., description="User's email address")
    user_avatar: str | None = Field(None, description="User's avatar URL")


class InviteMemberRequest(BaseModel):
    """Request payload for inviting a member to a budget."""
    email: EmailStr = Field(..., description="Email address of the user to invite")
    role: Literal["member"] = Field("member", description="Role to assign")
