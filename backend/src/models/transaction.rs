// Copyright (c) 2024 Tempo Budget
// SPDX-License-Identifier: MIT
//
// Transaction-related data models.

//! # Transaction Models
//!
//! This module defines transaction-related data structures including regular
//! transactions and recurring transaction templates.

use serde::{Deserialize, Serialize};
use sqlx::FromRow;

/// Represents a financial transaction (income or expense).
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Transaction {
    /// Unique identifier (UUID)
    pub id: String,
    /// ID of the budget this transaction belongs to
    pub budget_id: String,
    /// ID of the category this transaction is assigned to
    pub category_id: String,
    /// Transaction title/description
    pub title: String,
    /// Transaction amount (positive value)
    pub amount: f64,
    /// Type of transaction: "income" or "expense"
    pub transaction_type: String,
    /// Date of the transaction (ISO 8601 format)
    pub date: String,
    /// Optional comment or note
    pub comment: Option<String>,
    /// Whether this transaction was generated from a recurring template (0=no, 1=yes)
    pub is_recurring: i32,
    /// Timestamp when the transaction was created (RFC 3339 format)
    pub created_at: String,
}

/// Request payload for creating a new transaction.
#[derive(Debug, Deserialize)]
pub struct CreateTransaction {
    /// ID of the budget for the transaction
    pub budget_id: String,
    /// ID of the category for the transaction
    pub category_id: String,
    /// Transaction title/description
    pub title: String,
    /// Transaction amount
    pub amount: f64,
    /// Type of transaction: "income" or "expense"
    pub transaction_type: String,
    /// Date of the transaction (ISO 8601 format)
    pub date: String,
    /// Optional comment or note
    pub comment: Option<String>,
}

/// Represents a recurring transaction template.
///
/// Recurring transactions are templates that can automatically generate
/// regular transactions based on a specified frequency.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct RecurringTransaction {
    /// Unique identifier (UUID)
    pub id: String,
    /// ID of the budget this recurring transaction belongs to
    pub budget_id: String,
    /// ID of the category for generated transactions
    pub category_id: String,
    /// Transaction title/description
    pub title: String,
    /// Transaction amount
    pub amount: f64,
    /// Type of transaction: "income" or "expense"
    pub transaction_type: String,
    /// Frequency: "daily", "weekly", "monthly", "yearly"
    pub frequency: String,
    /// Day of the period (e.g., day of month for monthly frequency)
    pub day: Option<i32>,
    /// Whether the recurring transaction is active (0=inactive, 1=active)
    pub active: i32,
    /// Timestamp when the recurring transaction was created (RFC 3339 format)
    pub created_at: String,
}

/// Request payload for creating a new recurring transaction.
#[derive(Debug, Deserialize)]
pub struct CreateRecurringTransaction {
    /// ID of the budget for the recurring transaction
    pub budget_id: String,
    /// ID of the category for generated transactions
    pub category_id: String,
    /// Transaction title/description
    pub title: String,
    /// Transaction amount
    pub amount: f64,
    /// Type of transaction: "income" or "expense"
    pub transaction_type: String,
    /// Frequency: "daily", "weekly", "monthly", "yearly"
    pub frequency: String,
    /// Day of the period (optional, depends on frequency)
    pub day: Option<i32>,
}