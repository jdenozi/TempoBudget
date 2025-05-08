// Copyright (c) 2024 Tempo Budget
// SPDX-License-Identifier: MIT
//
// Category and budget profile data models.

//! # Category Models
//!
//! This module defines category-related data structures including budget categories
//! and budget profile templates for reusable category configurations.

use serde::{Deserialize, Serialize};
use sqlx::FromRow;

/// Represents a category within a budget.
///
/// Categories are used to organize and track different types of expenses/income
/// within a budget (e.g., "Groceries", "Rent", "Salary").
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Category {
    /// Unique identifier (UUID)
    pub id: String,
    /// ID of the budget this category belongs to
    pub budget_id: String,
    /// Category name
    pub name: String,
    /// Allocated amount for this category
    pub amount: f64,
    /// Timestamp when the category was created (RFC 3339 format)
    pub created_at: String,
}

/// Request payload for creating a new category.
#[derive(Debug, Deserialize)]
pub struct CreateCategory {
    /// Name for the new category
    pub name: String,
    /// Initial allocated amount
    pub amount: f64,
}

/// Request payload for updating an existing category.
///
/// All fields are optional; only provided fields will be updated.
#[derive(Debug, Deserialize)]
pub struct UpdateCategory {
    /// New name for the category
    pub name: Option<String>,
    /// New allocated amount
    pub amount: Option<f64>,
}

/// Represents a budget profile template.
///
/// Budget profiles allow users to save and reuse category configurations
/// across multiple budgets.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct BudgetProfile {
    /// Unique identifier (UUID)
    pub id: String,
    /// ID of the user who owns this profile
    pub user_id: String,
    /// Profile name
    pub name: String,
    /// Timestamp when the profile was created (RFC 3339 format)
    pub created_at: String,
}

/// Represents a category within a budget profile template.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct BudgetProfileCategory {
    /// Unique identifier (UUID)
    pub id: String,
    /// ID of the profile this category belongs to
    pub profile_id: String,
    /// Category name
    pub name: String,
    /// Default allocated amount
    pub amount: f64,
}

/// Request payload for creating a new budget profile.
#[derive(Debug, Deserialize)]
pub struct CreateBudgetProfile {
    /// Name for the new profile
    pub name: String,
    /// Categories to include in the profile
    pub categories: Vec<CreateBudgetProfileCategory>,
}

/// Request payload for a category within a budget profile creation request.
#[derive(Debug, Deserialize, Serialize)]
pub struct CreateBudgetProfileCategory {
    /// Category name
    pub name: String,
    /// Default allocated amount
    pub amount: f64,
}