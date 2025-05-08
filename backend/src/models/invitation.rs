// Copyright (c) 2024 Tempo Budget
// SPDX-License-Identifier: MIT
//
// Budget invitation data models.

//! # Invitation Models
//!
//! This module defines data structures for the budget invitation system,
//! allowing users to invite others to join group budgets.

use serde::{Deserialize, Serialize};
use sqlx::FromRow;

/// Represents an invitation to join a group budget.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct BudgetInvitation {
    /// Unique identifier (UUID)
    pub id: String,
    /// ID of the budget the invitation is for
    pub budget_id: String,
    /// ID of the user who sent the invitation
    pub inviter_id: String,
    /// Email address of the invited user
    pub invitee_email: String,
    /// Role that will be assigned upon acceptance
    pub role: String,
    /// Invitation status: "pending", "accepted", or "rejected"
    pub status: String,
    /// Timestamp when the invitation was created (RFC 3339 format)
    pub created_at: String,
}

/// Budget invitation with additional context details.
///
/// This structure includes budget and inviter information for display purposes.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BudgetInvitationWithDetails {
    /// Unique identifier (UUID)
    pub id: String,
    /// ID of the budget
    pub budget_id: String,
    /// Name of the budget
    pub budget_name: String,
    /// ID of the user who sent the invitation
    pub inviter_id: String,
    /// Name of the user who sent the invitation
    pub inviter_name: String,
    /// Email address of the invited user
    pub invitee_email: String,
    /// Role that will be assigned upon acceptance
    pub role: String,
    /// Invitation status
    pub status: String,
    /// Timestamp when the invitation was created (RFC 3339 format)
    pub created_at: String,
}