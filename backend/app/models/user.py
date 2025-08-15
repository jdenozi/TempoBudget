# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""User-related data models."""

from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
    """Represents a user account in the system."""
    id: str = Field(..., description="Unique identifier (UUID)")
    email: str = Field(..., description="User's email address")
    name: str = Field(..., description="User's display name")
    avatar: str | None = Field(None, description="Optional avatar URL")
    phone: str | None = Field(None, description="Optional phone number")
    created_at: str = Field(..., description="Timestamp when user was created")
    updated_at: str = Field(..., description="Timestamp when user was last updated")

    class Config:
        from_attributes = True


class UserInDB(User):
    """User model with password hash for internal use."""
    password_hash: str


class CreateUser(BaseModel):
    """Request payload for user registration."""
    email: EmailStr = Field(..., description="Email address for the new account")
    name: str = Field(..., min_length=1, description="Display name")
    password: str = Field(..., min_length=6, description="Plain-text password")


class LoginRequest(BaseModel):
    """Request payload for user login."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's plain-text password")


class AuthResponse(BaseModel):
    """Response payload for successful authentication."""
    token: str = Field(..., description="JWT token for authenticated requests")
    user: User = Field(..., description="The authenticated user's details")


class ChangePasswordRequest(BaseModel):
    """Request payload for changing password."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=6, description="New password")
