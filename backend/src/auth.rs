// Copyright (c) 2024 Tempo Budget
// SPDX-License-Identifier: MIT
//
// Authentication and authorization module for JWT token handling.

//! # Authentication Module
//!
//! This module provides JWT-based authentication functionality including:
//! - Token creation and verification
//! - Request authentication via the `AuthUser` extractor
//!
//! ## Security Notes
//! - Tokens expire after 24 hours
//! - The JWT secret should be set via the `JWT_SECRET` environment variable

use jsonwebtoken::{decode, encode, DecodingKey, EncodingKey, Header, Validation};
use serde::{Deserialize, Serialize};
use std::env;
use axum::{
    extract::FromRequestParts,
    http::{request::Parts, StatusCode},
};

/// JWT claims structure containing user identification and expiration.
#[derive(Debug, Serialize, Deserialize)]
pub struct Claims {
    /// Subject - the user ID
    pub sub: String,
    /// Expiration timestamp (Unix epoch)
    pub exp: usize,
}

/// Creates a new JWT token for the specified user.
///
/// # Arguments
///
/// * `user_id` - The unique identifier of the user
///
/// # Returns
///
/// A `Result` containing the encoded JWT string on success, or a JWT error on failure.
///
/// # Example
///
/// ```ignore
/// let token = create_token("user-uuid-here")?;
/// ```
pub fn create_token(user_id: &str) -> Result<String, jsonwebtoken::errors::Error> {
    let secret = env::var("JWT_SECRET").unwrap_or_else(|_| "secret".to_string());

    let expiration = chrono::Utc::now()
        .checked_add_signed(chrono::Duration::hours(24))
        .expect("valid timestamp")
        .timestamp();

    let claims = Claims {
        sub: user_id.to_string(),
        exp: expiration as usize,
    };

    encode(
        &Header::default(),
        &claims,
        &EncodingKey::from_secret(secret.as_bytes()),
    )
}

/// Verifies a JWT token and extracts its claims.
///
/// # Arguments
///
/// * `token` - The JWT token string to verify
///
/// # Returns
///
/// A `Result` containing the decoded `Claims` on success, or a JWT error on failure.
pub fn verify_token(token: &str) -> Result<Claims, jsonwebtoken::errors::Error> {
    let secret = env::var("JWT_SECRET").unwrap_or_else(|_| "secret".to_string());

    let token_data = decode::<Claims>(
        token,
        &DecodingKey::from_secret(secret.as_bytes()),
        &Validation::default(),
    )?;

    Ok(token_data.claims)
}

/// Authenticated user extractor for Axum handlers.
///
/// This struct can be used as an extractor in Axum route handlers to require
/// authentication. It automatically validates the `Authorization` header and
/// extracts the user ID from the JWT token.
///
/// # Example
///
/// ```ignore
/// async fn protected_route(auth: AuthUser) -> impl IntoResponse {
///     format!("Hello, user {}", auth.user_id)
/// }
/// ```
pub struct AuthUser {
    /// The authenticated user's unique identifier
    pub user_id: String,
}

#[axum::async_trait]
impl<S> FromRequestParts<S> for AuthUser
where
    S: Send + Sync,
{
    type Rejection = StatusCode;

    async fn from_request_parts(parts: &mut Parts, _state: &S) -> Result<Self, Self::Rejection> {
        // Retrieve the Authorization header
        let auth_header = parts
            .headers
            .get("Authorization")
            .and_then(|h| h.to_str().ok())
            .ok_or(StatusCode::UNAUTHORIZED)?;

        // Verify the "Bearer TOKEN" format
        if !auth_header.starts_with("Bearer ") {
            return Err(StatusCode::UNAUTHORIZED);
        }

        let token = &auth_header[7..];

        // Verify the token
        let claims = verify_token(token).map_err(|_| StatusCode::UNAUTHORIZED)?;

        Ok(AuthUser {
            user_id: claims.sub,
        })
    }
}