# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Loan-related data models."""

from typing import Literal
from pydantic import BaseModel, Field


class LoanRepayment(BaseModel):
    """A repayment towards a loan."""
    id: str = Field(..., description="Unique identifier")
    loan_id: str = Field(..., description="Loan ID")
    amount: float = Field(..., description="Repayment amount")
    date: str = Field(..., description="Repayment date")
    comment: str | None = Field(None, description="Optional comment")
    created_at: str = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class Loan(BaseModel):
    """A loan (lent or borrowed)."""
    id: str = Field(..., description="Unique identifier")
    user_id: str = Field(..., description="Owner user ID")
    person_name: str = Field(..., description="Person name")
    amount: float = Field(..., description="Original loan amount")
    direction: str = Field(..., description="lent or borrowed")
    date: str = Field(..., description="Loan date")
    description: str | None = Field(None, description="Description")
    status: str = Field(..., description="active or repaid")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    total_repaid: float = Field(0, description="Total amount repaid")
    remaining: float = Field(0, description="Amount remaining")
    repayments: list[LoanRepayment] = Field(default_factory=list, description="Repayment history")

    class Config:
        from_attributes = True


class CreateLoan(BaseModel):
    """Request payload for creating a loan."""
    person_name: str = Field(..., min_length=1, description="Person name")
    amount: float = Field(..., gt=0, description="Loan amount")
    direction: Literal["lent", "borrowed"] = Field(..., description="Direction")
    date: str = Field(..., description="Loan date")
    description: str | None = Field(None, description="Description")


class UpdateLoan(BaseModel):
    """Request payload for updating a loan."""
    person_name: str | None = Field(None, min_length=1, description="Person name")
    amount: float | None = Field(None, gt=0, description="Loan amount")
    direction: Literal["lent", "borrowed"] | None = Field(None, description="Direction")
    date: str | None = Field(None, description="Loan date")
    description: str | None = Field(None, description="Description")
    status: Literal["active", "repaid"] | None = Field(None, description="Status")


class CreateLoanRepayment(BaseModel):
    """Request payload for adding a repayment."""
    amount: float = Field(..., gt=0, description="Repayment amount")
    date: str = Field(..., description="Repayment date")
    comment: str | None = Field(None, description="Optional comment")


class LoanSummary(BaseModel):
    """Summary of all loans."""
    total_lent: float = Field(..., description="Total amount lent")
    total_borrowed: float = Field(..., description="Total amount borrowed")
    total_lent_remaining: float = Field(..., description="Remaining lent")
    total_borrowed_remaining: float = Field(..., description="Remaining borrowed")
    net_position: float = Field(..., description="Net position (lent_remaining - borrowed_remaining)")
