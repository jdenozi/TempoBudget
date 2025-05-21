// Copyright (c) 2024 Tempo Budget
// SPDX-License-Identifier: MIT
//
// OpenAPI documentation configuration.

//! # OpenAPI Documentation
//!
//! This module configures the OpenAPI (Swagger) documentation for the Tempo Budget API.
//! It defines all available endpoints, request/response schemas, and security requirements.

use utoipa::OpenApi;
use utoipa::openapi::security::{HttpAuthScheme, HttpBuilder, SecurityScheme};

use crate::models::{
    // User models
    User, CreateUser, LoginRequest, AuthResponse,
    // Budget models
    Budget, CreateBudget, UpdateBudget,
    // Transaction models
    Transaction, CreateTransaction, RecurringTransaction, CreateRecurringTransaction,
    // Category models
    Category, CreateCategory, UpdateCategory,
    BudgetProfile, BudgetProfileCategory, CreateBudgetProfile, CreateBudgetProfileCategory,
    // Member models
    BudgetMember, InviteMemberRequest, BudgetMemberWithUser,
    // Invitation models
    BudgetInvitation, BudgetInvitationWithDetails,
};

use crate::handlers;

/// OpenAPI documentation for the Tempo Budget API.
#[derive(OpenApi)]
#[openapi(
    info(
        title = "Tempo Budget API",
        version = "0.1.0",
        description = "REST API for the Tempo Budget personal and group budget management application.",
        license(name = "MIT", url = "https://opensource.org/licenses/MIT"),
        contact(name = "Tempo Budget Team")
    ),
    servers(
        (url = "http://localhost:3000", description = "Local development server")
    ),
    paths(
        // Auth endpoints
        handlers::auth::register,
        handlers::auth::login,
        // Budget endpoints
        handlers::budgets::get_budgets,
        handlers::budgets::create_budget,
        handlers::budgets::get_budget,
        handlers::budgets::delete_budget,
        // Category endpoints
        handlers::categories::get_categories,
        handlers::categories::create_category,
        handlers::categories::update_category,
        handlers::categories::delete_category,
        // Transaction endpoints
        handlers::transactions::get_transactions,
        handlers::transactions::create_transaction,
        handlers::transactions::delete_transaction,
        handlers::transactions::get_recurring_transactions,
        handlers::transactions::create_recurring_transaction,
        handlers::transactions::toggle_recurring_transaction,
        handlers::transactions::delete_recurring_transaction,
        // Budget members endpoints
        handlers::budget_members::get_budget_members,
        handlers::budget_members::invite_member,
        handlers::budget_members::remove_member,
        // Invitation endpoints
        handlers::invitations::get_my_invitations,
        handlers::invitations::accept_invitation,
        handlers::invitations::reject_invitation,
    ),
    components(
        schemas(
            // User schemas
            User, CreateUser, LoginRequest, AuthResponse,
            // Budget schemas
            Budget, CreateBudget, UpdateBudget,
            // Transaction schemas
            Transaction, CreateTransaction, RecurringTransaction, CreateRecurringTransaction,
            // Category schemas
            Category, CreateCategory, UpdateCategory,
            BudgetProfile, BudgetProfileCategory, CreateBudgetProfile, CreateBudgetProfileCategory,
            // Member schemas
            BudgetMember, InviteMemberRequest, BudgetMemberWithUser,
            // Invitation schemas
            BudgetInvitation, BudgetInvitationWithDetails,
        )
    ),
    tags(
        (name = "auth", description = "Authentication endpoints"),
        (name = "budgets", description = "Budget management endpoints"),
        (name = "categories", description = "Category management endpoints"),
        (name = "transactions", description = "Transaction management endpoints"),
        (name = "members", description = "Budget member management endpoints"),
        (name = "invitations", description = "Invitation management endpoints"),
    ),
    modifiers(&SecurityAddon)
)]
pub struct ApiDoc;

/// Security scheme addon for JWT Bearer authentication.
struct SecurityAddon;

impl utoipa::Modify for SecurityAddon {
    fn modify(&self, openapi: &mut utoipa::openapi::OpenApi) {
        if let Some(components) = openapi.components.as_mut() {
            components.add_security_scheme(
                "bearer_auth",
                SecurityScheme::Http(
                    HttpBuilder::new()
                        .scheme(HttpAuthScheme::Bearer)
                        .bearer_format("JWT")
                        .description(Some("JWT token obtained from /api/auth/login"))
                        .build()
                ),
            );
        }
    }
}
