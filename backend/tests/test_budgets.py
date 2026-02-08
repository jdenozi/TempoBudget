# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Tests for budget endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_personal_budget(client: AsyncClient, test_user):
    """Test creating a personal budget."""
    response = await client.post(
        "/api/budgets",
        json={
            "name": "My Personal Budget",
            "budget_type": "personal"
        },
        headers=test_user["headers"]
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "My Personal Budget"
    assert data["budget_type"] == "personal"
    assert data["user_id"] == test_user["user"]["id"]
    assert "id" in data


@pytest.mark.asyncio
async def test_create_shared_budget(client: AsyncClient, test_user):
    """Test creating a shared budget."""
    response = await client.post(
        "/api/budgets",
        json={
            "name": "Shared Family Budget",
            "budget_type": "group"
        },
        headers=test_user["headers"]
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Shared Family Budget"
    assert data["budget_type"] == "group"


@pytest.mark.asyncio
async def test_get_budgets(client: AsyncClient, test_user, test_budget):
    """Test retrieving user's budgets."""
    response = await client.get(
        "/api/budgets",
        headers=test_user["headers"]
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(b["id"] == test_budget["id"] for b in data)


@pytest.mark.asyncio
async def test_get_budget_by_id(client: AsyncClient, test_user, test_budget):
    """Test retrieving a specific budget."""
    response = await client.get(
        f"/api/budgets/{test_budget['id']}",
        headers=test_user["headers"]
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_budget["id"]
    assert data["name"] == test_budget["name"]


@pytest.mark.asyncio
async def test_get_nonexistent_budget(client: AsyncClient, test_user):
    """Test retrieving a non-existent budget."""
    response = await client.get(
        "/api/budgets/nonexistent-id",
        headers=test_user["headers"]
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_own_budget(client: AsyncClient, test_user, test_budget):
    """Test deleting own budget."""
    response = await client.delete(
        f"/api/budgets/{test_budget['id']}",
        headers=test_user["headers"]
    )

    assert response.status_code == 204

    # Verify budget is deleted
    get_response = await client.get(
        f"/api/budgets/{test_budget['id']}",
        headers=test_user["headers"]
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_others_budget_forbidden(client: AsyncClient, test_user, second_user):
    """Test that deleting another user's budget is forbidden."""
    # Create budget as first user
    create_response = await client.post(
        "/api/budgets",
        json={"name": "Private Budget", "budget_type": "personal"},
        headers=test_user["headers"]
    )
    budget_id = create_response.json()["id"]

    # Try to delete as second user
    response = await client.delete(
        f"/api/budgets/{budget_id}",
        headers=second_user["headers"]
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_budget_summaries(client: AsyncClient, test_user, test_budget, test_category):
    """Test getting budget summaries."""
    response = await client.get(
        "/api/budgets/summaries",
        headers=test_user["headers"]
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    summary = next(s for s in data if s["id"] == test_budget["id"])
    assert "total_budget" in summary
    assert "total_spent" in summary
    assert "remaining" in summary
    assert "percentage" in summary


@pytest.mark.asyncio
async def test_create_budget_unauthenticated(client: AsyncClient):
    """Test creating budget without authentication."""
    response = await client.post(
        "/api/budgets",
        json={"name": "Test", "budget_type": "personal"}
    )

    assert response.status_code == 403
