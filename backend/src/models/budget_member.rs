// Copyright (c) 2024 Tempo Budget
// SPDX-License-Identifier: MIT
//
// Budget member data models for group budget functionality.

//! # Budget Member Models
//!
//! This module defines data structures for managing membership in group budgets,
//! including member roles and invitation requests.

use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use utoipa::ToSchema;

/// Represents a member of a group budget.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow, ToSchema)]
pub struct BudgetMember {
    /// Unique identifier (UUID)
    pub id: String,
    /// ID of the budget
    pub budget_id: String,
    /// ID of the user who is a member
    pub user_id: String,
    /// Role of the member: "owner", "admin", or "member"
    pub role: String,
    /// Timestamp when the membership was created (RFC 3339 format)
    pub created_at: String,
}

/// Request payload for inviting a member to a budget.
#[derive(Debug, Deserialize, ToSchema)]
pub struct InviteMemberRequest {
    /// Email address of the user to invite
    pub email: String,
    /// Role to assign: "admin" or "member" (owner cannot be assigned)
    pub role: String,
}

/// Budget member with associated user information.
///
/// This structure is used when displaying member lists with user details.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow, ToSchema)]
pub struct BudgetMemberWithUser {
    /// Unique identifier (UUID)
    pub id: String,
    /// ID of the budget
    pub budget_id: String,
    /// ID of the user
    pub user_id: String,
    /// Role of the member
    pub role: String,
    /// Timestamp when the membership was created (RFC 3339 format)
    pub created_at: String,
    /// User's display name
    pub user_name: String,
    /// User's email address
    pub user_email: String,
    /// User's avatar URL (optional)
    pub user_avatar: Option<String>,
}