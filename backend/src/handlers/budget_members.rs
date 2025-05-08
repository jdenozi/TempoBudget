// Copyright (c) 2024 Tempo Budget
// SPDX-License-Identifier: MIT
//
// Budget member management HTTP handlers for group budgets.

//! # Budget Member Handlers
//!
//! This module provides HTTP handlers for managing members in group budgets:
//! - `GET /api/budgets/:budget_id/members` - List budget members
//! - `POST /api/budgets/:budget_id/members` - Invite a new member
//! - `DELETE /api/budgets/:budget_id/members/:member_id` - Remove a member

use axum::{
    extract::{Path, State},
    http::StatusCode,
    Json,
};
use std::sync::Arc;
use uuid::Uuid;
use chrono::Utc;

use crate::{
    auth::AuthUser,
    models::{BudgetMemberWithUser, InviteMemberRequest},
    DbPool,
};

/// Retrieves all members of a group budget.
///
/// # Endpoint
/// `GET /api/budgets/:budget_id/members`
///
/// # Authentication
/// Requires a valid JWT token. User must be a member of the budget.
///
/// # Path Parameters
/// - `budget_id`: The budget's unique identifier
///
/// # Returns
/// - `200 OK` with array of `BudgetMemberWithUser` objects
/// - `403 Forbidden` if the user is not a member of the budget
/// - `500 Internal Server Error` if the query fails
pub async fn get_budget_members(
    State(pool): State<Arc<DbPool>>,
    auth: AuthUser,
    Path(budget_id): Path<String>,
) -> Result<Json<Vec<BudgetMemberWithUser>>, StatusCode> {
    // Verify that the user has access to the budget
    let is_member = sqlx::query_scalar::<_, i64>(
        "SELECT COUNT(*) FROM budget_members WHERE budget_id = ? AND user_id = ?"
    )
        .bind(&budget_id)
        .bind(&auth.user_id)
        .fetch_one(pool.as_ref())
        .await
        .map_err(|e| {
            tracing::error!("Failed to check membership: {:?}", e);
            StatusCode::INTERNAL_SERVER_ERROR
        })?;

    if is_member == 0 {
        return Err(StatusCode::FORBIDDEN);
    }

    // Retrieve members with user information
    let members = sqlx::query_as::<_, BudgetMemberWithUser>(
        "SELECT
            bm.id, bm.budget_id, bm.user_id, bm.role, bm.created_at,
            u.name as user_name, u.email as user_email, u.avatar as user_avatar
         FROM budget_members bm
         JOIN users u ON bm.user_id = u.id
         WHERE bm.budget_id = ?"
    )
        .bind(&budget_id)
        .fetch_all(pool.as_ref())
        .await
        .map_err(|e| {
            tracing::error!("Failed to fetch members: {:?}", e);
            StatusCode::INTERNAL_SERVER_ERROR
        })?;

    Ok(Json(members))
}

/// Invites a new member to a group budget.
///
/// # Endpoint
/// `POST /api/budgets/:budget_id/members`
///
/// # Authentication
/// Requires a valid JWT token. User must be the budget owner.
///
/// # Path Parameters
/// - `budget_id`: The budget's unique identifier
///
/// # Request Body
/// - `email`: Email address of the user to invite
/// - `role`: Role to assign ("admin" or "member")
///
/// # Returns
/// - `201 Created` on successful invitation
/// - `403 Forbidden` if the user is not the budget owner
/// - `404 Not Found` if the invited email doesn't exist
/// - `409 Conflict` if the user is already a member
/// - `500 Internal Server Error` if the invitation fails
pub async fn invite_member(
    State(pool): State<Arc<DbPool>>,
    auth: AuthUser,
    Path(budget_id): Path<String>,
    Json(payload): Json<InviteMemberRequest>,
) -> Result<StatusCode, StatusCode> {
    // Verify that the user is the owner
    let is_owner = sqlx::query_scalar::<_, i64>(
        "SELECT COUNT(*) FROM budget_members WHERE budget_id = ? AND user_id = ? AND role = 'owner'"
    )
        .bind(&budget_id)
        .bind(&auth.user_id)
        .fetch_one(pool.as_ref())
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    if is_owner == 0 {
        return Err(StatusCode::FORBIDDEN);
    }

    // Verify that the email exists in the system
    let user_exists = sqlx::query_scalar::<_, i64>(
        "SELECT COUNT(*) FROM users WHERE email = ?"
    )
        .bind(&payload.email)
        .fetch_one(pool.as_ref())
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    if user_exists == 0 {
        return Err(StatusCode::NOT_FOUND);
    }

    // Check if the user is already a member
    let already_member = sqlx::query_scalar::<_, i64>(
        "SELECT COUNT(*) FROM budget_members bm
         JOIN users u ON bm.user_id = u.id
         WHERE bm.budget_id = ? AND u.email = ?"
    )
        .bind(&budget_id)
        .bind(&payload.email)
        .fetch_one(pool.as_ref())
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    if already_member > 0 {
        return Err(StatusCode::CONFLICT);
    }

    // Create the invitation
    let id = Uuid::new_v4().to_string();
    let now = Utc::now().to_rfc3339();

    sqlx::query(
        "INSERT INTO budget_invitations (id, budget_id, inviter_id, invitee_email, role, status, created_at)
         VALUES (?, ?, ?, ?, ?, 'pending', ?)"
    )
        .bind(&id)
        .bind(&budget_id)
        .bind(&auth.user_id)
        .bind(&payload.email)
        .bind(&payload.role)
        .bind(&now)
        .execute(pool.as_ref())
        .await
        .map_err(|e| {
            tracing::error!("Failed to create invitation: {:?}", e);
            StatusCode::INTERNAL_SERVER_ERROR
        })?;

    Ok(StatusCode::CREATED)
}

/// Removes a member from a group budget.
///
/// # Endpoint
/// `DELETE /api/budgets/:budget_id/members/:member_id`
///
/// # Authentication
/// Requires a valid JWT token. User must be the budget owner.
///
/// # Path Parameters
/// - `budget_id`: The budget's unique identifier
/// - `member_id`: The member record's unique identifier
///
/// # Returns
/// - `204 No Content` on successful removal
/// - `403 Forbidden` if the user is not the budget owner
/// - `500 Internal Server Error` if the removal fails
pub async fn remove_member(
    State(pool): State<Arc<DbPool>>,
    auth: AuthUser,
    Path((budget_id, member_id)): Path<(String, String)>,
) -> Result<StatusCode, StatusCode> {
    // Verify that the user is the owner
    let is_owner = sqlx::query_scalar::<_, i64>(
        "SELECT COUNT(*) FROM budget_members WHERE budget_id = ? AND user_id = ? AND role = 'owner'"
    )
        .bind(&budget_id)
        .bind(&auth.user_id)
        .fetch_one(pool.as_ref())
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    if is_owner == 0 {
        return Err(StatusCode::FORBIDDEN);
    }

    // Remove the member
    sqlx::query("DELETE FROM budget_members WHERE id = ? AND budget_id = ?")
        .bind(&member_id)
        .bind(&budget_id)
        .execute(pool.as_ref())
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(StatusCode::NO_CONTENT)
}