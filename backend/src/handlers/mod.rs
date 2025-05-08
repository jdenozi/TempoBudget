// Copyright (c) 2024 Tempo Budget
// SPDX-License-Identifier: MIT
//
// HTTP request handlers module - re-exports all handler functions.

//! # Request Handlers
//!
//! This module contains all HTTP request handlers for the API endpoints.
//! Handlers are organized by domain: authentication, budgets, transactions,
//! categories, and group budget management.

pub mod auth;
pub mod budgets;
pub mod transactions;
pub mod categories;
pub(crate) mod budget_members;
pub(crate) mod invitations;

pub use auth::*;
pub use budgets::*;
pub use transactions::*;
pub use categories::*;
pub use budget_members::*;
pub use invitations::*;