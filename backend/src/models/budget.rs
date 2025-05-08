// Copyright (c) 2024 Tempo Budget
// SPDX-License-Identifier: MIT
//
// Budget-related data models.

//! # Budget Models
//!
//! This module defines budget-related data structures including the main `Budget` entity
//! and request types for creating and updating budgets.

use serde::{Deserialize, Serialize};
use sqlx::FromRow;

/// Represents a budget in the system.
///
/// A budget can be either personal (owned by a single user) or a group budget
/// (shared among multiple users via the budget_members table).
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Budget {
    /// Unique identifier (UUID)
    pub id: String,
    /// ID of the user who created the budget
    pub user_id: String,
    /// Budget name/title
    pub name: String,
    /// Type of budget: "personal" or "group"
    pub budget_type: String,
    /// Whether the budget is currently active (SQLite stores as i32: 0=inactive, 1=active)
    pub is_active: i32,
    /// Timestamp when the budget was created (RFC 3339 format)
    pub created_at: String,
    /// Timestamp when the budget was last updated (RFC 3339 format)
    pub updated_at: String,
}

/// Request payload for creating a new budget.
#[derive(Debug, Deserialize)]
pub struct CreateBudget {
    /// Name/title for the new budget
    pub name: String,
    /// Type of budget: "personal" or "group"
    pub budget_type: String,
}

/// Request payload for updating an existing budget.
///
/// All fields are optional; only provided fields will be updated.
#[derive(Debug, Deserialize)]
pub struct UpdateBudget {
    /// New name for the budget
    pub name: Option<String>,
    /// New active status (0=inactive, 1=active)
    pub is_active: Option<i32>,
}