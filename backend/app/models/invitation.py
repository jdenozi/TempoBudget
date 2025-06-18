# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Budget invitation data models."""

from pydantic import BaseModel, Field


class BudgetInvitation(BaseModel):
    """Represents an invitation to join a group budget."""
    id: str = Field(..., description="Unique identifier (UUID)")
    budget_id: str = Field(..., description="ID of the budget")
    inviter_id: str = Field(..., description="ID of the inviter")
    invitee_email: str = Field(..., description="Email of the invitee")
    role: str = Field(..., description="Role to be assigned")
    status: str = Field(..., description="Status: pending/accepted/rejected")
    created_at: str = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class BudgetInvitationWithDetails(BaseModel):
    """Budget invitation with additional context details."""
    id: str = Field(..., description="Unique identifier (UUID)")
    budget_id: str = Field(..., description="ID of the budget")
    budget_name: str = Field(..., description="Name of the budget")
    inviter_id: str = Field(..., description="ID of the inviter")
    inviter_name: str = Field(..., description="Name of the inviter")
    invitee_email: str = Field(..., description="Email of the invitee")
    role: str = Field(..., description="Role to be assigned")
    status: str = Field(..., description="Invitation status")
    created_at: str = Field(..., description="Creation timestamp")
