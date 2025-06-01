// Copyright (c) 2024 Tempo Budget
// SPDX-License-Identifier: MIT
//
// API route definitions.

//! # Routes Module
//!
//! This module defines all API routes and maps them to their corresponding handlers.
//! The API is organized into the following endpoint groups:
//!
//! ## Authentication
//! - `POST /api/auth/register` - User registration
//! - `POST /api/auth/login` - User login
//!
//! ## Budgets
//! - `GET /api/budgets` - List user's budgets
//! - `POST /api/budgets` - Create a new budget
//! - `GET /api/budgets/:id` - Get a specific budget
//! - `DELETE /api/budgets/:id` - Delete a budget
//!
//! ## Budget Members
//! - `GET /api/budgets/:budget_id/members` - List budget members
//! - `POST /api/budgets/:budget_id/members` - Invite a member
//! - `DELETE /api/budgets/:budget_id/members/:member_id` - Remove a member
//!
//! ## Invitations
//! - `GET /api/invitations` - List pending invitations
//! - `POST /api/invitations/:id/accept` - Accept an invitation
//! - `POST /api/invitations/:id/reject` - Reject an invitation
//!
//! ## Categories
//! - `GET /api/budgets/:budget_id/categories` - List categories
//! - `POST /api/budgets/:budget_id/categories` - Create a category
//! - `PUT /api/categories/:id` - Update a category
//! - `DELETE /api/categories/:id` - Delete a category
//!
//! ## Transactions
//! - `GET /api/budgets/:budget_id/transactions` - List transactions
//! - `POST /api/budgets/:budget_id/transactions` - Create a transaction
//! - `DELETE /api/transactions/:id` - Delete a transaction
//!
//! ## Recurring Transactions
//! - `GET /api/budgets/:budget_id/recurring` - List recurring transactions
//! - `POST /api/budgets/:budget_id/recurring` - Create a recurring transaction
//! - `PUT /api/recurring/:id/toggle` - Toggle recurring transaction status
//! - `DELETE /api/recurring/:id` - Delete a recurring transaction

use axum::{
    routing::{get, post, put, delete},
    Router,
};
use std::sync::Arc;
use utoipa::OpenApi;
use utoipa_swagger_ui::SwaggerUi;
use crate::{handlers, DbPool};
use crate::openapi::ApiDoc;

/// Creates and configures the main application router.
///
/// # Arguments
///
/// * `pool` - Shared database connection pool
///
/// # Returns
///
/// A configured `Router` with all API routes and shared state.
pub fn create_router(pool: Arc<DbPool>) -> Router {
    Router::new()
        // Auth routes
        .route("/api/auth/register", post(handlers::register))
        .route("/api/auth/login", post(handlers::login))

        // Budget routes
        .route("/api/budgets", get(handlers::get_budgets).post(handlers::create_budget))
        .route("/api/budgets/:id", get(handlers::get_budget).delete(handlers::delete_budget))

        // Budget members routes
        .route("/api/budgets/:budget_id/members",
               get(handlers::budget_members::get_budget_members)
                   .post(handlers::budget_members::invite_member))
        .route("/api/budgets/:budget_id/members/:member_id",
               delete(handlers::budget_members::remove_member))

        // Invitations routes
        .route("/api/invitations", get(handlers::invitations::get_my_invitations))
        .route("/api/invitations/:id/accept", post(handlers::invitations::accept_invitation))
        .route("/api/invitations/:id/reject", post(handlers::invitations::reject_invitation))

        // Category routes
        .route("/api/budgets/:budget_id/categories",
               get(handlers::get_categories)
                   .post(handlers::create_category))
        .route("/api/categories/:id",
               put(handlers::update_category)
                   .delete(handlers::delete_category))

        // Transaction routes
        .route("/api/budgets/:budget_id/transactions",
               get(handlers::get_transactions)
                   .post(handlers::create_transaction))
        .route("/api/transactions/:id", delete(handlers::delete_transaction))

        // Recurring transaction routes
        .route("/api/budgets/:budget_id/recurring",
               get(handlers::get_recurring_transactions)
                   .post(handlers::create_recurring_transaction))
        .route("/api/recurring/:id/toggle", put(handlers::toggle_recurring_transaction))
        .route("/api/recurring/:id", delete(handlers::delete_recurring_transaction))

        // Swagger UI documentation
        .merge(SwaggerUi::new("/swagger-ui").url("/api-docs/openapi.json", ApiDoc::openapi()))

        .with_state(pool)
}