// Copyright (c) 2024 Tempo Budget
// SPDX-License-Identifier: MIT
//
// Budget invitation HTTP handlers.

//! # Invitation Handlers
//!
//! This module provides HTTP handlers for managing budget invitations:
//! - `GET /api/invitations` - List pending invitations for the current user
//! - `POST /api/invitations/:id/accept` - Accept an invitation
//! - `POST /api/invitations/:id/reject` - Reject an invitation

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
    models::BudgetInvitationWithDetails,
    DbPool,
};

/// Retrieves all pending invitations for the authenticated user.
///
/// # Endpoint
/// `GET /api/invitations`
///
/// # Authentication
/// Requires a valid JWT token.
///
/// # Returns
/// - `200 OK` with array of `BudgetInvitationWithDetails` objects
/// - `500 Internal Server Error` if the query fails
pub async fn get_my_invitations(
    State(pool): State<Arc<DbPool>>,
    auth: AuthUser,
) -> Result<Json<Vec<BudgetInvitationWithDetails>>, StatusCode> {
    let user_email = sqlx::query_scalar::<_, String>(
        "SELECT email FROM users WHERE id = ?"
    )
        .bind(&auth.user_id)
        .fetch_one(pool.as_ref())
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    let invitations = sqlx::query_as::<_, (String, String, String, String, String, String, String, String, String)>(
        "SELECT
            bi.id, bi.budget_id, b.name as budget_name, bi.inviter_id, u.name as inviter_name,
            bi.invitee_email, bi.role, bi.status, bi.created_at
         FROM budget_invitations bi
         JOIN budgets b ON bi.budget_id = b.id
         JOIN users u ON bi.inviter_id = u.id
         WHERE bi.invitee_email = ? AND bi.status = 'pending'"
    )
        .bind(&user_email)
        .fetch_all(pool.as_ref())
        .await
        .map_err(|e| {
            tracing::error!("Failed to fetch invitations: {:?}", e);
            StatusCode::INTERNAL_SERVER_ERROR
        })?
        .into_iter()
        .map(|(id, budget_id, budget_name, inviter_id, inviter_name, invitee_email, role, status, created_at)| {
            BudgetInvitationWithDetails {
                id,
                budget_id,
                budget_name,
                inviter_id,
                inviter_name,
                invitee_email,
                role,
                status,
                created_at,
            }
        })
        .collect();

    Ok(Json(invitations))
}

/// Accepts a budget invitation.
///
/// # Endpoint
/// `POST /api/invitations/:id/accept`
///
/// # Authentication
/// Requires a valid JWT token. User must be the invitation recipient.
///
/// # Path Parameters
/// - `id`: The invitation's unique identifier
///
/// # Returns
/// - `200 OK` on successful acceptance
/// - `400 Bad Request` if the invitation is not pending
/// - `403 Forbidden` if the user is not the intended recipient
/// - `404 Not Found` if the invitation doesn't exist
/// - `500 Internal Server Error` if the operation fails
///
/// # Side Effects
/// - Creates a new budget member record
/// - Updates the invitation status to "accepted"
pub async fn accept_invitation(
    State(pool): State<Arc<DbPool>>,
    auth: AuthUser,
    Path(invitation_id): Path<String>,
) -> Result<StatusCode, StatusCode> {
    // Get the invitation details
    let invitation = sqlx::query_as::<_, (String, String, String, String)>(
        "SELECT budget_id, invitee_email, role, status FROM budget_invitations WHERE id = ?"
    )
        .bind(&invitation_id)
        .fetch_one(pool.as_ref())
        .await
        .map_err(|_| StatusCode::NOT_FOUND)?;

    let (budget_id, invitee_email, role, status) = invitation;

    if status != "pending" {
        return Err(StatusCode::BAD_REQUEST);
    }

    // Verify that the invitation is for this user
    let user_email = sqlx::query_scalar::<_, String>(
        "SELECT email FROM users WHERE id = ?"
    )
        .bind(&auth.user_id)
        .fetch_one(pool.as_ref())
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    if user_email != invitee_email {
        return Err(StatusCode::FORBIDDEN);
    }

    // Add the member to the budget
    let member_id = Uuid::new_v4().to_string();
    let now = Utc::now().to_rfc3339();

    sqlx::query(
        "INSERT INTO budget_members (id, budget_id, user_id, role, created_at) VALUES (?, ?, ?, ?, ?)"
    )
        .bind(&member_id)
        .bind(&budget_id)
        .bind(&auth.user_id)
        .bind(&role)
        .bind(&now)
        .execute(pool.as_ref())
        .await
        .map_err(|e| {
            tracing::error!("Failed to add member: {:?}", e);
            StatusCode::INTERNAL_SERVER_ERROR
        })?;

    // Mark the invitation as accepted
    sqlx::query("UPDATE budget_invitations SET status = 'accepted' WHERE id = ?")
        .bind(&invitation_id)
        .execute(pool.as_ref())
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(StatusCode::OK)
}

/// Rejects a budget invitation.
///
/// # Endpoint
/// `POST /api/invitations/:id/reject`
///
/// # Authentication
/// Requires a valid JWT token. User must be the invitation recipient.
///
/// # Path Parameters
/// - `id`: The invitation's unique identifier
///
/// # Returns
/// - `200 OK` on successful rejection
/// - `400 Bad Request` if the invitation is not pending
/// - `403 Forbidden` if the user is not the intended recipient
/// - `404 Not Found` if the invitation doesn't exist
/// - `500 Internal Server Error` if the operation fails
pub async fn reject_invitation(
    State(pool): State<Arc<DbPool>>,
    auth: AuthUser,
    Path(invitation_id): Path<String>,
) -> Result<StatusCode, StatusCode> {
    // Get the invitation details
    let invitation = sqlx::query_as::<_, (String, String)>(
        "SELECT invitee_email, status FROM budget_invitations WHERE id = ?"
    )
        .bind(&invitation_id)
        .fetch_one(pool.as_ref())
        .await
        .map_err(|_| StatusCode::NOT_FOUND)?;

    let (invitee_email, status) = invitation;

    if status != "pending" {
        return Err(StatusCode::BAD_REQUEST);
    }

    // Verify that the invitation is for this user
    let user_email = sqlx::query_scalar::<_, String>(
        "SELECT email FROM users WHERE id = ?"
    )
        .bind(&auth.user_id)
        .fetch_one(pool.as_ref())
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    if user_email != invitee_email {
        return Err(StatusCode::FORBIDDEN);
    }

    // Mark the invitation as rejected
    sqlx::query("UPDATE budget_invitations SET status = 'rejected' WHERE id = ?")
        .bind(&invitation_id)
        .execute(pool.as_ref())
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(StatusCode::OK)
}