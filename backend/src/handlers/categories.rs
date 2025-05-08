// Copyright (c) 2024 Tempo Budget
// SPDX-License-Identifier: MIT
//
// Category management HTTP handlers.

//! # Category Handlers
//!
//! This module provides HTTP handlers for category management within budgets:
//! - `GET /api/budgets/:budget_id/categories` - List categories
//! - `POST /api/budgets/:budget_id/categories` - Create a category
//! - `PUT /api/categories/:id` - Update a category
//! - `DELETE /api/categories/:id` - Delete a category
//!
//! Also includes budget profile template handlers.

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
        BudgetProfile, BudgetProfileCategory, Category, CreateBudgetProfile, CreateCategory,
        UpdateCategory,
    },
    DbPool,
};

/// Retrieves all categories for a specific budget.
///
/// # Endpoint
/// `GET /api/budgets/:budget_id/categories`
///
/// # Path Parameters
/// - `budget_id`: The budget's unique identifier
///
/// # Returns
/// - `200 OK` with array of `Category` objects
/// - `500 Internal Server Error` if the query fails
pub async fn get_categories(
    State(pool): State<Arc<DbPool>>,
    Path(budget_id): Path<String>,
) -> Result<Json<Vec<Category>>, StatusCode> {
    let categories = sqlx::query_as::<_, Category>(
        "SELECT id, budget_id, name, amount, created_at FROM categories WHERE budget_id = ?"
    )
        .bind(&budget_id)
        .fetch_all(pool.as_ref())
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(Json(categories))
}

/// Creates a new category within a budget.
///
/// # Endpoint
/// `POST /api/budgets/:budget_id/categories`
///
/// # Path Parameters
/// - `budget_id`: The budget's unique identifier
///
/// # Request Body
/// - `name`: Category name
/// - `amount`: Allocated amount for this category
///
/// # Returns
/// - `200 OK` with the created `Category` object
/// - `500 Internal Server Error` if creation fails
pub async fn create_category(
    State(pool): State<Arc<DbPool>>,
    Path(budget_id): Path<String>,
    Json(payload): Json<CreateCategory>,
) -> Result<Json<Category>, StatusCode> {
    let id = Uuid::new_v4().to_string();
    let now = Utc::now().to_rfc3339();

    sqlx::query(
        "INSERT INTO categories (id, budget_id, name, amount, created_at) VALUES (?, ?, ?, ?, ?)"
    )
        .bind(&id)
        .bind(&budget_id)
        .bind(&payload.name)
        .bind(payload.amount)
        .bind(&now)
        .execute(pool.as_ref())
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    let category = sqlx::query_as::<_, Category>(
        "SELECT id, budget_id, name, amount, created_at FROM categories WHERE id = ?"
    )
        .bind(&id)
        .fetch_one(pool.as_ref())
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(Json(category))
}

/// Updates an existing category.
///
/// # Endpoint
/// `PUT /api/categories/:id`
///
/// # Path Parameters
/// - `id`: The category's unique identifier
///
/// # Request Body
/// - `name`: (optional) New category name
/// - `amount`: (optional) New allocated amount
///
/// # Returns
/// - `200 OK` with the updated `Category` object
/// - `400 Bad Request` if no fields are provided
/// - `404 Not Found` if the category doesn't exist
/// - `500 Internal Server Error` if update fails
pub async fn update_category(
    State(pool): State<Arc<DbPool>>,
    Path(id): Path<String>,
    Json(payload): Json<UpdateCategory>,
) -> Result<Json<Category>, StatusCode> {
    // Build the query dynamically based on provided fields
    let mut updates = Vec::new();
    let mut values: Vec<String> = Vec::new();

    if let Some(name) = &payload.name {
        updates.push("name = ?");
        values.push(name.clone());
    }

    if let Some(amount) = payload.amount {
        updates.push("amount = ?");
        values.push(amount.to_string());
    }

    if updates.is_empty() {
        return Err(StatusCode::BAD_REQUEST);
    }

    let query = format!("UPDATE categories SET {} WHERE id = ?", updates.join(", "));

    let mut q = sqlx::query(&query);
    for value in &values {
        q = q.bind(value);
    }
    q = q.bind(&id);

    q.execute(pool.as_ref())
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    let category = sqlx::query_as::<_, Category>(
        "SELECT id, budget_id, name, amount, created_at FROM categories WHERE id = ?"
    )
        .bind(&id)
        .fetch_one(pool.as_ref())
        .await
        .map_err(|_| StatusCode::NOT_FOUND)?;

    Ok(Json(category))
}

/// Deletes a category.
///
/// # Endpoint
/// `DELETE /api/categories/:id`
///
/// # Path Parameters
/// - `id`: The category's unique identifier
///
/// # Returns
/// - `204 No Content` on successful deletion
/// - `500 Internal Server Error` if deletion fails
pub async fn delete_category(
    State(pool): State<Arc<DbPool>>,
    Path(id): Path<String>,
) -> Result<StatusCode, StatusCode> {
    sqlx::query("DELETE FROM categories WHERE id = ?")
        .bind(&id)
        .execute(pool.as_ref())
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(StatusCode::NO_CONTENT)
}

/// Retrieves the user's budget profile template.
///
/// # Endpoint
/// `GET /api/budget-profile`
///
/// # Returns
/// - `200 OK` with tuple of `BudgetProfile` and its categories
/// - `404 Not Found` if no profile exists
/// - `500 Internal Server Error` if the query fails
///
/// # TODO
/// Extract user_id from JWT instead of using hardcoded value.
pub async fn get_budget_profile(
    State(pool): State<Arc<DbPool>>,
    // TODO: Extract user_id from JWT
) -> Result<Json<(BudgetProfile, Vec<BudgetProfileCategory>)>, StatusCode> {
    let user_id = String::from("user_1"); // Hardcoded for now

    let profile = sqlx::query_as::<_, BudgetProfile>(
        "SELECT id, user_id, name, created_at FROM budget_profiles WHERE user_id = ?"
    )
        .bind(&user_id)
        .fetch_one(pool.as_ref())
        .await
        .map_err(|_| StatusCode::NOT_FOUND)?;

    let categories = sqlx::query_as::<_, BudgetProfileCategory>(
        "SELECT id, profile_id, name, amount FROM budget_profile_categories WHERE profile_id = ?"
    )
        .bind(&profile.id)
        .fetch_all(pool.as_ref())
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(Json((profile, categories)))
}

/// Creates a new budget profile template.
///
/// # Endpoint
/// `POST /api/budget-profile`
///
/// # Request Body
/// - `name`: Profile name
/// - `categories`: Array of categories with name and amount
///
/// # Returns
/// - `200 OK` with the created `BudgetProfile` object
/// - `500 Internal Server Error` if creation fails
///
/// # TODO
/// Extract user_id from JWT instead of using hardcoded value.
pub async fn create_budget_profile(
    State(pool): State<Arc<DbPool>>,
    Json(payload): Json<CreateBudgetProfile>,
    // TODO: Extract user_id from JWT
) -> Result<Json<BudgetProfile>, StatusCode> {
    let user_id = String::from("user_1"); // Hardcoded for now
    let profile_id = Uuid::new_v4().to_string();
    let now = Utc::now().to_rfc3339();

    // Create the profile
    sqlx::query(
        "INSERT INTO budget_profiles (id, user_id, name, created_at) VALUES (?, ?, ?, ?)"
    )
        .bind(&profile_id)
        .bind(&user_id)
        .bind(&payload.name)
        .bind(&now)
        .execute(pool.as_ref())
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    // Create the categories
    for cat in payload.categories {
        let cat_id = Uuid::new_v4().to_string();
        sqlx::query(
            "INSERT INTO budget_profile_categories (id, profile_id, name, amount)
             VALUES (?, ?, ?, ?)"
        )
            .bind(&cat_id)
            .bind(&profile_id)
            .bind(&cat.name)
            .bind(cat.amount)
            .execute(pool.as_ref())
            .await
            .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    }

    let profile = sqlx::query_as::<_, BudgetProfile>(
        "SELECT id, user_id, name, created_at FROM budget_profiles WHERE id = ?"
    )
        .bind(&profile_id)
        .fetch_one(pool.as_ref())
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(Json(profile))
}