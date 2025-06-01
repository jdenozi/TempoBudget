// Copyright (c) 2024 Tempo Budget
// SPDX-License-Identifier: MIT
//
// Main entry point for the Tempo Budget backend API server.

//! # Tempo Budget Backend
//!
//! This module serves as the entry point for the Tempo Budget API server.
//! It initializes the database connection pool, sets up logging, and starts
//! the HTTP server with configured routes and middleware.

mod auth;
mod handlers;
mod models;
mod openapi;
mod routes;

use sqlx::sqlite::{SqlitePool, SqliteConnectOptions};
use dotenvy::dotenv;
use std::{env, sync::Arc, str::FromStr};
use tower_http::cors::{Any, CorsLayer};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

/// Type alias for the SQLite connection pool used throughout the application.
pub type DbPool = SqlitePool;

/// Application entry point.
///
/// Initializes the following components:
/// - Environment variables from `.env` file
/// - Tracing/logging subscriber
/// - SQLite database connection pool
/// - Database schema
/// - HTTP server with CORS middleware
#[tokio::main]
async fn main() {
    // Load environment variables from .env file
    dotenv().ok();

    // Initialize the logging subscriber
    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::new(
            env::var("RUST_LOG").unwrap_or_else(|_| "info".into()),
        ))
        .with(tracing_subscriber::fmt::layer())
        .init();

    // Create the SQLx connection pool with create_if_missing option
    let database_url = env::var("DATABASE_URL").unwrap_or_else(|_| "sqlite:budget.db".into());

    let connect_options = SqliteConnectOptions::from_str(&database_url)
        .expect("Invalid DATABASE_URL")
        .create_if_missing(true);

    let pool = SqlitePool::connect_with(connect_options)
        .await
        .expect("Failed to connect to database");

    tracing::info!("Database pool created");

    // Initialize the database schema
    sqlx::query(&std::fs::read_to_string("schema.sql").expect("Failed to read schema.sql"))
        .execute(&pool)
        .await
        .expect("Failed to initialize schema");

    tracing::info!("Database schema initialized");

    let pool = Arc::new(pool);

    // Configure CORS middleware
    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods(Any)
        .allow_headers(Any);

    // Create the application router (includes Swagger UI)
    let app = routes::create_router(pool)
        .layer(cors);
    
    // Start the HTTP server
    let port = env::var("PORT").unwrap_or_else(|_| "3000".to_string());
    let addr = format!("0.0.0.0:{}", port);

    tracing::info!("Server starting on {}", addr);

    let listener = tokio::net::TcpListener::bind(&addr)
        .await
        .expect("Failed to bind");

    axum::serve(listener, app)
        .await
        .expect("Server failed");
}