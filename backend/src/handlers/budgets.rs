// Copyright (c) 2024 Tempo Budget
// SPDX-License-Identifier: MIT
//
// Budget management HTTP handlers.

//! # Budget Handlers
//!
//! This module provides HTTP handlers for budget management:
//! - `GET /api/budgets` - List all budgets for the authenticated user
//! - `POST /api/budgets` - Create a new budget
//! - `GET /api/budgets/:id` - Get a specific budget
//! - `DELETE /api/budgets/:id` - Delete a budget

use axum::{
    extract::{Path, State},
    http::StatusCode,
    Json,
};
use std::sync::Arc;
use uuid::Uuid;
use chrono::Utc;
use utoipa;

use crate::{
    auth::AuthUser,
    models::{Budget, CreateBudget},
    DbPool,
};
use crate::models::InviteMemberRequest;

/// Retrieves all budgets for the authenticated user.
///
/// # Endpoint
/// `GET /api/budgets`
///
/// # Authentication
/// Requires a valid JWT token in the Authorization header.
///
/// # Returns
/// - `200 OK` with array of `Budget` objects
/// - `500 Internal Server Error` if the query fails
#[utoipa::path(
    get,
    path = "/api/budgets",
    tag = "budgets",
    responses(
        (status = 200, description = "List of user's budgets", body = Vec<Budget>),
        (status = 500, description = "Failed to fetch budgets")
    ),
    security(("bearer_auth" = []))
)]
pub async fn get_budgets(
    State(pool): State<Arc<DbPool>>,
    auth: AuthUser,
) -> Result<Json<Vec<Budget>>, StatusCode> {
    let budgets = sqlx::query_as::<_, Budget>(
        "SELECT id, user_id, name, budget_type, is_active, created_at, updated_at
         FROM budgets WHERE user_id = ?"
    )
        .bind(&auth.user_id)
        .fetch_all(pool.as_ref())
        .await
        .map_err(|e| {
            tracing::error!("Failed to fetch budgets: {:?}", e);
            StatusCode::INTERNAL_SERVER_ERROR
        })?;

    Ok(Json(budgets))
}

/// Creates a new budget.
///
/// # Endpoint
/// `POST /api/budgets`
///
/// # Authentication
/// Requires a valid JWT token in the Authorization header.
///
/// # Request Body
/// - `name`: Budget name/title
/// - `budget_type`: Either "personal" or "group"
///
/// # Returns
/// - `200 OK` with the created `Budget` object
/// - `500 Internal Server Error` if creation fails
///
/// # Notes
/// For group budgets, the creator is automatically added as the owner.
#[utoipa::path(
    post,
    path = "/api/budgets",
    tag = "budgets",
    request_body = CreateBudget,
    responses(
        (status = 200, description = "Budget created successfully", body = Budget),
        (status = 500, description = "Failed to create budget")
    ),
    security(("bearer_auth" = []))
)]
pub async fn create_budget(
    State(pool): State<Arc<DbPool>>,
    auth: AuthUser,
    Json(payload): Json<CreateBudget>,
) -> Result<Json<Budget>, StatusCode> {
    let id = Uuid::new_v4().to_string();
    let user_id = auth.user_id.clone();
    let now = Utc::now().to_rfc3339();

    sqlx::query(
        "INSERT INTO budgets (id, user_id, name, budget_type, is_active, created_at, updated_at)
         VALUES (?, ?, ?, ?, 0, ?, ?)"
    )
        .bind(&id)
        .bind(&user_id)
        .bind(&payload.name)
        .bind(&payload.budget_type)
        .bind(&now)
        .bind(&now)
        .execute(pool.as_ref())
        .await
        .map_err(|e| {
            tracing::error!("Failed to insert budget: {:?}", e);
            StatusCode::INTERNAL_SERVER_ERROR
        })?;

    // For group budgets, add the creator as owner
    if payload.budget_type == "group" {
        let member_id = Uuid::new_v4().to_string();
        sqlx::query(
            "INSERT INTO budget_members (id, budget_id, user_id, role, created_at) VALUES (?, ?, ?, 'owner', ?)"
        )
            .bind(&member_id)
            .bind(&id)
            .bind(&user_id)
            .bind(&now)
            .execute(pool.as_ref())
            .await
            .map_err(|e| {
                tracing::error!("Failed to insert budget member: {:?}", e);
                StatusCode::INTERNAL_SERVER_ERROR
            })?;
    }

    let budget = sqlx::query_as::<_, Budget>(
        "SELECT id, user_id, name, budget_type, is_active, created_at, updated_at
         FROM budgets WHERE id = ?"
    )
        .bind(&id)
        .fetch_one(pool.as_ref())
        .await
        .map_err(|e| {
            tracing::error!("Failed to fetch created budget: {:?}", e);
            StatusCode::INTERNAL_SERVER_ERROR
        })?;

    Ok(Json(budget))
}

/// Retrieves a specific budget by ID.
///
/// # Endpoint
/// `GET /api/budgets/:id`
///
/// # Path Parameters
/// - `id`: The budget's unique identifier
///
/// # Returns
/// - `200 OK` with the `Budget` object
/// - `404 Not Found` if the budget doesn't exist
#[utoipa::path(
    get,
    path = "/api/budgets/{id}",
    tag = "budgets",
    params(
        ("id" = String, Path, description = "Budget unique identifier")
    ),
    responses(
        (status = 200, description = "Budget details", body = Budget),
        (status = 404, description = "Budget not found")
    )
)]
pub async fn get_budget(
    State(pool): State<Arc<DbPool>>,
    Path(id): Path<String>,
) -> Result<Json<Budget>, StatusCode> {
    let budget = sqlx::query_as::<_, Budget>(
        "SELECT id, user_id, name, budget_type, is_active, created_at, updated_at
         FROM budgets WHERE id = ?"
    )
        .bind(&id)
        .fetch_one(pool.as_ref())
        .await
        .map_err(|e| {
            tracing::error!("Failed to fetch budget: {:?}", e);
            StatusCode::NOT_FOUND
        })?;

    Ok(Json(budget))
}

/// Deletes a budget.
///
/// # Endpoint
/// `DELETE /api/budgets/:id`
///
/// # Authentication
/// Requires a valid JWT token in the Authorization header.
///
/// # Path Parameters
/// - `id`: The budget's unique identifier
///
/// # Returns
/// - `204 No Content` on successful deletion
/// - `403 Forbidden` if the user doesn't own the budget
/// - `500 Internal Server Error` if deletion fails
///
/// # Authorization
/// User must be either the budget owner (for group budgets) or the creator
/// (for personal budgets).
#[utoipa::path(
    delete,
    path = "/api/budgets/{id}",
    tag = "budgets",
    params(
        ("id" = String, Path, description = "Budget unique identifier")
    ),
    responses(
        (status = 204, description = "Budget deleted successfully"),
        (status = 403, description = "Not authorized to delete this budget"),
        (status = 500, description = "Failed to delete budget")
    ),
    security(("bearer_auth" = []))
)]
pub async fn delete_budget(
    State(pool): State<Arc<DbPool>>,
    auth: AuthUser,
    Path(id): Path<String>,
) -> Result<StatusCode, StatusCode> {
    // Check if user is owner (for group budgets)
    let is_owner = sqlx::query_scalar::<_, i64>(
        "SELECT COUNT(*) FROM budget_members WHERE budget_id = ? AND user_id = ? AND role = 'owner'"
    )
        .bind(&id)
        .bind(&auth.user_id)
        .fetch_one(pool.as_ref())
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    // Check if it's the user's own budget (for personal budgets)
    let is_my_budget = sqlx::query_scalar::<_, i64>(
        "SELECT COUNT(*) FROM budgets WHERE id = ? AND user_id = ?"
    )
        .bind(&id)
        .bind(&auth.user_id)
        .fetch_one(pool.as_ref())
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    if is_owner == 0 && is_my_budget == 0 {
        return Err(StatusCode::FORBIDDEN);
    }

    // Delete the budget (cascade deletes related records)
    sqlx::query("DELETE FROM budgets WHERE id = ?")
        .bind(&id)
        .execute(pool.as_ref())
        .await
        .map_err(|e| {
            tracing::error!("Failed to delete budget: {:?}", e);
            StatusCode::INTERNAL_SERVER_ERROR
        })?;

    Ok(StatusCode::NO_CONTENT)
}