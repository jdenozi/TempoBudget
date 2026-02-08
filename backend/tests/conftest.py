# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Pytest configuration and fixtures for API tests."""

import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Set test environment before importing app modules
os.environ["DB_PATH"] = ":memory:"
os.environ["JWT_SECRET"] = "test-secret-key"


def get_schema():
    """Read and return database schema."""
    schema_path = os.path.join(os.path.dirname(__file__), "..", "schema.sql")
    with open(schema_path) as f:
        return f.read()


@pytest_asyncio.fixture(scope="function")
async def client():
    """Provide an async HTTP client with isolated database for each test."""
    # Import app here to avoid issues with module loading
    from app.main import app
    from app.database import get_db

    # Create a fresh in-memory database for each test
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    test_async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    # Initialize schema
    schema = get_schema()
    async with test_engine.begin() as conn:
        for statement in schema.split(";"):
            statement = statement.strip()
            if statement:
                await conn.execute(text(statement))

    async def override_get_db():
        """Override database dependency for tests."""
        async with test_async_session() as session:
            try:
                yield session
            finally:
                await session.close()

    # Override the database dependency
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Clean up
    app.dependency_overrides.clear()
    await test_engine.dispose()


@pytest_asyncio.fixture
async def test_user(client: AsyncClient):
    """Create and return a test user with authentication token."""
    user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "password": "password123"
    }
    response = await client.post("/api/auth/register", json=user_data)
    assert response.status_code == 200, f"Failed to create test user: {response.json()}"
    data = response.json()
    return {
        "user": data["user"],
        "token": data["token"],
        "headers": {"Authorization": f"Bearer {data['token']}"}
    }


@pytest_asyncio.fixture
async def second_user(client: AsyncClient):
    """Create a second test user."""
    user_data = {
        "email": "second@example.com",
        "name": "Second User",
        "password": "password456"
    }
    response = await client.post("/api/auth/register", json=user_data)
    assert response.status_code == 200, f"Failed to create second user: {response.json()}"
    data = response.json()
    return {
        "user": data["user"],
        "token": data["token"],
        "headers": {"Authorization": f"Bearer {data['token']}"}
    }


@pytest_asyncio.fixture
async def test_budget(client: AsyncClient, test_user):
    """Create and return a test budget."""
    budget_data = {
        "name": "Test Budget",
        "budget_type": "personal"
    }
    response = await client.post(
        "/api/budgets",
        json=budget_data,
        headers=test_user["headers"]
    )
    assert response.status_code == 200, f"Failed to create test budget: {response.json()}"
    return response.json()


@pytest_asyncio.fixture
async def test_category(client: AsyncClient, test_user, test_budget):
    """Create and return a test category."""
    category_data = {
        "name": "Test Category",
        "amount": 500.0,
        "tags": ["besoin"]
    }
    response = await client.post(
        f"/api/budgets/{test_budget['id']}/categories",
        json=category_data,
        headers=test_user["headers"]
    )
    assert response.status_code == 200, f"Failed to create test category: {response.json()}"
    return response.json()
