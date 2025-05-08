// Copyright (c) 2024 Tempo Budget
// SPDX-License-Identifier: MIT
//
// Transaction management HTTP handlers.

//! # Transaction Handlers
//!
//! This module provides HTTP handlers for transaction management:
//! - `GET /api/budgets/:budget_id/transactions` - List transactions
//! - `POST /api/budgets/:budget_id/transactions` - Create a transaction
//! - `DELETE /api/transactions/:id` - Delete a transaction
//!
//! Also includes recurring transaction handlers:
//! - `GET /api/budgets/:budget_id/recurring` - List recurring transactions
//! - `POST /api/budgets/:budget_id/recurring` - Create a recurring transaction
//! - `PUT /api/recurring/:id/toggle` - Toggle recurring transaction active status
//! - `DELETE /api/recurring/:id` - Delete a recurring transaction

use axum::{
    extract::{Path, State},
    http::StatusCode,
    Json,
};
use std::sync::Arc;
use uuid::Uuid;
use chrono::Utc;

use crate::{
    models::{
        CreateRecurringTransaction, CreateTransaction, RecurringTransaction, Transaction,
    },
    DbPool,
};

/// Retrieves all transactions for a specific budget.
///
/// # Endpoint
/// `GET /api/budgets/:budget_id/transactions`
///
/// # Path Parameters
/// - `budget_id`: The budget's unique identifier
///
/// # Returns
/// - `200 OK` with array of `Transaction` objects (sorted by date descending)
/// - `500 Internal Server Error` if the query fails
pub async fn get_transactions(
    State(pool): State<Arc<DbPool>>,
    Path(budget_id): Path<String>,
) -> Result<Json<Vec<Transaction>>, StatusCode> {
    let transactions = sqlx::query_as::<_, Transaction>(
        "SELECT id, budget_id, category_id, title, amount, transaction_type, date, comment,
         is_recurring, created_at FROM transactions WHERE budget_id = ? ORDER BY date DESC"
    )
        .bind(&budget_id)
        .fetch_all(pool.as_ref())
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(Json(transactions))
}

/// Creates a new transaction.
///
/// # Endpoint
/// `POST /api/budgets/:budget_id/transactions`
///
/// # Request Body
/// - `budget_id`: Budget ID for the transaction
/// - `category_id`: Category ID for the transaction
/// - `title`: Transaction title/description
/// - `amount`: Transaction amount
/// - `transaction_type`: Either "income" or "expense"
/// - `date`: Transaction date (ISO 8601 format)
/// - `comment`: (optional) Additional notes
///
/// # Returns
/// - `200 OK` with the created `Transaction` object
/// - `500 Internal Server Error` if creation fails
pub async fn create_transaction(
    State(pool): State<Arc<DbPool>>,
    Json(payload): Json<CreateTransaction>,
) -> Result<Json<Transaction>, StatusCode> {
    let id = Uuid::new_v4().to_string();
    let now = Utc::now().to_rfc3339();

    sqlx::query(
        "INSERT INTO transactions (id, budget_id, category_id, title, amount, transaction_type,
         date, comment, is_recurring, created_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)"
    )
        .bind(&id)
        .bind(&payload.budget_id)
        .bind(&payload.category_id)
        .bind(&payload.title)
        .bind(payload.amount)
        .bind(&payload.transaction_type)
        .bind(&payload.date)
        .bind(&payload.comment)
        .bind(&now)
        .execute(pool.as_ref())
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    let transaction = sqlx::query_as::<_, Transaction>(
        "SELECT id, budget_id, category_id, title, amount, transaction_type, date, comment,
         is_recurring, created_at FROM transactions WHERE id = ?"
    )
        .bind(&id)
        .fetch_one(pool.as_ref())
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(Json(transaction))
}

/// Deletes a transaction.
///
/// # Endpoint
/// `DELETE /api/transactions/:id`
///
/// # Path Parameters
/// - `id`: The transaction's unique identifier
///
/// # Returns
/// - `204 No Content` on successful deletion
/// - `500 Internal Server Error` if deletion fails
pub async fn delete_transaction(
    State(pool): State<Arc<DbPool>>,
    Path(id): Path<String>,
) -> Result<StatusCode, StatusCode> {
    sqlx::query("DELETE FROM transactions WHERE id = ?")
        .bind(&id)
        .execute(pool.as_ref())
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(StatusCode::NO_CONTENT)
}

/// Retrieves all recurring transactions for a specific budget.
///
/// # Endpoint
/// `GET /api/budgets/:budget_id/recurring`
///
/// # Path Parameters
/// - `budget_id`: The budget's unique identifier
///
/// # Returns
/// - `200 OK` with array of `RecurringTransaction` objects
/// - `500 Internal Server Error` if the query fails
pub async fn get_recurring_transactions(
    State(pool): State<Arc<DbPool>>,
    Path(budget_id): Path<String>,
) -> Result<Json<Vec<RecurringTransaction>>, StatusCode> {
    let transactions = sqlx::query_as::<_, RecurringTransaction>(
        "SELECT id, budget_id, category_id, title, amount, transaction_type, frequency, day,
         active, created_at FROM recurring_transactions WHERE budget_id = ?"
    )
        .bind(&budget_id)
        .fetch_all(pool.as_ref())
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(Json(transactions))
}

/// Creates a new recurring transaction.
///
/// # Endpoint
/// `POST /api/budgets/:budget_id/recurring`
///
/// # Request Body
/// - `budget_id`: Budget ID for the recurring transaction
/// - `category_id`: Category ID for generated transactions
/// - `title`: Transaction title/description
/// - `amount`: Transaction amount
/// - `transaction_type`: Either "income" or "expense"
/// - `frequency`: One of "daily", "weekly", "monthly", "yearly"
/// - `day`: (optional) Day of the period for scheduling
///
/// # Returns
/// - `200 OK` with the created `RecurringTransaction` object
/// - `500 Internal Server Error` if creation fails
pub async fn create_recurring_transaction(
    State(pool): State<Arc<DbPool>>,
    Json(payload): Json<CreateRecurringTransaction>,
) -> Result<Json<RecurringTransaction>, StatusCode> {
    let id = Uuid::new_v4().to_string();
    let now = Utc::now().to_rfc3339();

    sqlx::query(
        "INSERT INTO recurring_transactions (id, budget_id, category_id, title, amount,
         transaction_type, frequency, day, active, created_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)"
    )
        .bind(&id)
        .bind(&payload.budget_id)
        .bind(&payload.category_id)
        .bind(&payload.title)
        .bind(payload.amount)
        .bind(&payload.transaction_type)
        .bind(&payload.frequency)
        .bind(payload.day)
        .bind(&now)
        .execute(pool.as_ref())
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    let transaction = sqlx::query_as::<_, RecurringTransaction>(
        "SELECT id, budget_id, category_id, title, amount, transaction_type, frequency, day,
         active, created_at FROM recurring_transactions WHERE id = ?"
    )
        .bind(&id)
        .fetch_one(pool.as_ref())
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(Json(transaction))
}

/// Toggles the active status of a recurring transaction.
///
/// # Endpoint
/// `PUT /api/recurring/:id/toggle`
///
/// # Path Parameters
/// - `id`: The recurring transaction's unique identifier
///
/// # Returns
/// - `200 OK` with the updated `RecurringTransaction` object
/// - `404 Not Found` if the recurring transaction doesn't exist
/// - `500 Internal Server Error` if update fails
pub async fn toggle_recurring_transaction(
    State(pool): State<Arc<DbPool>>,
    Path(id): Path<String>,
) -> Result<Json<RecurringTransaction>, StatusCode> {
    // Get the current state
    let current = sqlx::query_as::<_, RecurringTransaction>(
        "SELECT id, budget_id, category_id, title, amount, transaction_type, frequency, day,
         active, created_at FROM recurring_transactions WHERE id = ?"
    )
        .bind(&id)
        .fetch_one(pool.as_ref())
        .await
        .map_err(|_| StatusCode::NOT_FOUND)?;

    // Toggle the state
    let new_active = !current.active;

    sqlx::query("UPDATE recurring_transactions SET active = ? WHERE id = ?")
        .bind(new_active)
        .bind(&id)
        .execute(pool.as_ref())
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    // Get the updated version
    let updated = sqlx::query_as::<_, RecurringTransaction>(
        "SELECT id, budget_id, category_id, title, amount, transaction_type, frequency, day,
         active, created_at FROM recurring_transactions WHERE id = ?"
    )
        .bind(&id)
        .fetch_one(pool.as_ref())
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(Json(updated))
}

/// Deletes a recurring transaction.
///
/// # Endpoint
/// `DELETE /api/recurring/:id`
///
/// # Path Parameters
/// - `id`: The recurring transaction's unique identifier
///
/// # Returns
/// - `204 No Content` on successful deletion
/// - `500 Internal Server Error` if deletion fails
pub async fn delete_recurring_transaction(
    State(pool): State<Arc<DbPool>>,
    Path(id): Path<String>,
) -> Result<StatusCode, StatusCode> {
    sqlx::query("DELETE FROM recurring_transactions WHERE id = ?")
        .bind(&id)
        .execute(pool.as_ref())
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(StatusCode::NO_CONTENT)
}