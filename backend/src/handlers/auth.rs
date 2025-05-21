// Copyright (c) 2024 Tempo Budget
// SPDX-License-Identifier: MIT
//
// Authentication HTTP handlers for user registration and login.

//! # Authentication Handlers
//!
//! This module provides HTTP handlers for user authentication:
//! - `POST /api/auth/register` - Create a new user account
//! - `POST /api/auth/login` - Authenticate and receive a JWT token

use axum::{
    extract::State,
    http::StatusCode,
    Json,
};
use std::sync::Arc;
use uuid::Uuid;
use chrono::Utc;
use utoipa;

use crate::{
    auth::create_token,
    models::{AuthResponse, CreateUser, LoginRequest, User},
    DbPool,
};

/// Registers a new user account.
///
/// # Endpoint
/// `POST /api/auth/register`
///
/// # Request Body
/// - `email`: User's email address (must be unique)
/// - `name`: User's display name
/// - `password`: Plain-text password (will be hashed)
///
/// # Returns
/// - `200 OK` with `AuthResponse` containing JWT token and user details
/// - `500 Internal Server Error` if registration fails
#[utoipa::path(
    post,
    path = "/api/auth/register",
    tag = "auth",
    request_body = CreateUser,
    responses(
        (status = 200, description = "User registered successfully", body = AuthResponse),
        (status = 500, description = "Registration failed")
    )
)]
pub async fn register(
    State(pool): State<Arc<DbPool>>,
    Json(payload): Json<CreateUser>,
) -> Result<Json<AuthResponse>, StatusCode> {
    // Hash the password
    let password_hash = bcrypt::hash(&payload.password, bcrypt::DEFAULT_COST)
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    let id = Uuid::new_v4().to_string();
    let now = Utc::now().to_rfc3339();

    // Insert the user into the database
    sqlx::query(
        "INSERT INTO users (id, email, name, password_hash, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?)"
    )
        .bind(&id)
        .bind(&payload.email)
        .bind(&payload.name)
        .bind(&password_hash)
        .bind(&now)
        .bind(&now)
        .execute(pool.as_ref())
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    // Retrieve the created user
    let user = sqlx::query_as::<_, User>(
        "SELECT id, email, name, password_hash, avatar, phone, created_at, updated_at
         FROM users WHERE id = ?"
    )
        .bind(&id)
        .fetch_one(pool.as_ref())
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    // Generate the JWT token
    let token = create_token(&id).map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(Json(AuthResponse { token, user }))
}

/// Authenticates a user and returns a JWT token.
///
/// # Endpoint
/// `POST /api/auth/login`
///
/// # Request Body
/// - `email`: User's email address
/// - `password`: User's plain-text password
///
/// # Returns
/// - `200 OK` with `AuthResponse` containing JWT token and user details
/// - `401 Unauthorized` if credentials are invalid
/// - `500 Internal Server Error` if authentication fails
#[utoipa::path(
    post,
    path = "/api/auth/login",
    tag = "auth",
    request_body = LoginRequest,
    responses(
        (status = 200, description = "Login successful", body = AuthResponse),
        (status = 401, description = "Invalid credentials"),
        (status = 500, description = "Authentication failed")
    )
)]
pub async fn login(
    State(pool): State<Arc<DbPool>>,
    Json(payload): Json<LoginRequest>,
) -> Result<Json<AuthResponse>, StatusCode> {
    // Find the user by email
    let user = sqlx::query_as::<_, User>(
        "SELECT id, email, name, password_hash, avatar, phone, created_at, updated_at
         FROM users WHERE email = ?"
    )
        .bind(&payload.email)
        .fetch_one(pool.as_ref())
        .await
        .map_err(|_| StatusCode::UNAUTHORIZED)?;

    // Verify the password
    let valid = bcrypt::verify(&payload.password, &user.password_hash)
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    if !valid {
        return Err(StatusCode::UNAUTHORIZED);
    }

    // Generate the JWT token
    let token = create_token(&user.id).map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(Json(AuthResponse { token, user }))
}