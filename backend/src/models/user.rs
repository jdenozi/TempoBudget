// Copyright (c) 2024 Tempo Budget
// SPDX-License-Identifier: MIT
//
// User-related data models.

//! # User Models
//!
//! This module defines user-related data structures including the main `User` entity
//! and authentication request/response types.

use serde::{Deserialize, Serialize};
use sqlx::FromRow;

/// Represents a user account in the system.
///
/// The `password_hash` field is excluded from serialization for security.
#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct User {
    /// Unique identifier (UUID)
    pub id: String,
    /// User's email address (unique)
    pub email: String,
    /// User's display name
    pub name: String,
    /// Bcrypt-hashed password (excluded from JSON serialization)
    #[serde(skip_serializing)]
    pub password_hash: String,
    /// Optional avatar URL
    pub avatar: Option<String>,
    /// Optional phone number
    pub phone: Option<String>,
    /// Timestamp when the user was created (RFC 3339 format)
    pub created_at: String,
    /// Timestamp when the user was last updated (RFC 3339 format)
    pub updated_at: String,
}

/// Request payload for user registration.
#[derive(Debug, Deserialize)]
pub struct CreateUser {
    /// Email address for the new account
    pub email: String,
    /// Display name for the new account
    pub name: String,
    /// Plain-text password (will be hashed before storage)
    pub password: String,
}

/// Request payload for user login.
#[derive(Debug, Deserialize)]
pub struct LoginRequest {
    /// User's email address
    pub email: String,
    /// User's plain-text password
    pub password: String,
}

/// Response payload for successful authentication.
#[derive(Debug, Serialize)]
pub struct AuthResponse {
    /// JWT token for subsequent authenticated requests
    pub token: String,
    /// The authenticated user's details
    pub user: User,
}