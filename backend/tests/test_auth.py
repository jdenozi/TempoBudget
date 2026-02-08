# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Tests for authentication endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """Test successful user registration."""
    response = await client.post("/api/auth/register", json={
        "email": "newuser@example.com",
        "name": "New User",
        "password": "securepassword123"
    })

    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert "user" in data
    assert data["user"]["email"] == "newuser@example.com"
    assert data["user"]["name"] == "New User"
    assert "id" in data["user"]


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user):
    """Test registration with existing email fails."""
    response = await client.post("/api/auth/register", json={
        "email": "test@example.com",  # Same as test_user
        "name": "Another User",
        "password": "password123"
    })

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient):
    """Test registration with invalid email format."""
    response = await client.post("/api/auth/register", json={
        "email": "not-an-email",
        "name": "Test User",
        "password": "password123"
    })

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_register_short_password(client: AsyncClient):
    """Test registration with too short password."""
    response = await client.post("/api/auth/register", json={
        "email": "valid@example.com",
        "name": "Test User",
        "password": "short"  # Less than 6 characters
    })

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user):
    """Test successful login."""
    response = await client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })

    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert "user" in data
    assert data["user"]["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user):
    """Test login with wrong password."""
    response = await client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "wrongpassword"
    })

    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Test login with non-existent email."""
    response = await client.post("/api/auth/login", json={
        "email": "nobody@example.com",
        "password": "password123"
    })

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_change_password_success(client: AsyncClient, test_user):
    """Test successful password change."""
    response = await client.post(
        "/api/auth/change-password",
        json={
            "current_password": "password123",
            "new_password": "newpassword456"
        },
        headers=test_user["headers"]
    )

    assert response.status_code == 200
    assert "success" in response.json()["message"].lower()

    # Verify new password works
    login_response = await client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "newpassword456"
    })
    assert login_response.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_current(client: AsyncClient, test_user):
    """Test password change with wrong current password."""
    response = await client.post(
        "/api/auth/change-password",
        json={
            "current_password": "wrongpassword",
            "new_password": "newpassword456"
        },
        headers=test_user["headers"]
    )

    assert response.status_code == 400
    assert "incorrect" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_change_password_unauthenticated(client: AsyncClient):
    """Test password change without authentication."""
    response = await client.post(
        "/api/auth/change-password",
        json={
            "current_password": "password123",
            "new_password": "newpassword456"
        }
    )

    assert response.status_code == 403  # No auth header
