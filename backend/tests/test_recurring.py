# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Tests for recurring transaction endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_recurring_transaction(client: AsyncClient, test_user, test_budget, test_category):
    """Test creating a recurring transaction."""
    response = await client.post(
        f"/api/budgets/{test_budget['id']}/recurring",
        json={
            "category_id": test_category["id"],
            "title": "Monthly Rent",
            "amount": 1000.0,
            "transaction_type": "expense",
            "frequency": "monthly",
            "day": 1
        },
        headers=test_user["headers"]
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Monthly Rent"
    assert data["amount"] == 1000.0
    assert data["frequency"] == "monthly"
    assert data["day"] == 1
    assert data["active"] == 1


@pytest.mark.asyncio
async def test_create_weekly_recurring(client: AsyncClient, test_user, test_budget, test_category):
    """Test creating a weekly recurring transaction."""
    response = await client.post(
        f"/api/budgets/{test_budget['id']}/recurring",
        json={
            "category_id": test_category["id"],
            "title": "Weekly Groceries",
            "amount": 100.0,
            "transaction_type": "expense",
            "frequency": "weekly",
            "day": 5  # Friday
        },
        headers=test_user["headers"]
    )

    assert response.status_code == 200
    data = response.json()
    assert data["frequency"] == "weekly"


@pytest.mark.asyncio
async def test_get_recurring_transactions(client: AsyncClient, test_user, test_budget, test_category):
    """Test retrieving recurring transactions."""
    # Create a recurring transaction
    await client.post(
        f"/api/budgets/{test_budget['id']}/recurring",
        json={
            "category_id": test_category["id"],
            "title": "Test Recurring",
            "amount": 50.0,
            "transaction_type": "expense",
            "frequency": "monthly",
            "day": 15
        },
        headers=test_user["headers"]
    )

    response = await client.get(
        f"/api/budgets/{test_budget['id']}/recurring",
        headers=test_user["headers"]
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_toggle_recurring_transaction(client: AsyncClient, test_user, test_budget, test_category):
    """Test toggling recurring transaction active status."""
    # Create a recurring transaction
    create_response = await client.post(
        f"/api/budgets/{test_budget['id']}/recurring",
        json={
            "category_id": test_category["id"],
            "title": "Toggle Test",
            "amount": 50.0,
            "transaction_type": "expense",
            "frequency": "monthly",
            "day": 1
        },
        headers=test_user["headers"]
    )
    recurring_id = create_response.json()["id"]

    # Toggle off
    toggle_response = await client.put(
        f"/api/recurring/{recurring_id}/toggle",
        headers=test_user["headers"]
    )

    assert toggle_response.status_code == 200
    assert toggle_response.json()["active"] == 0

    # Toggle on
    toggle_response2 = await client.put(
        f"/api/recurring/{recurring_id}/toggle",
        headers=test_user["headers"]
    )

    assert toggle_response2.status_code == 200
    assert toggle_response2.json()["active"] == 1


@pytest.mark.asyncio
async def test_update_recurring_transaction(client: AsyncClient, test_user, test_budget, test_category):
    """Test updating a recurring transaction."""
    # Create a recurring transaction
    create_response = await client.post(
        f"/api/budgets/{test_budget['id']}/recurring",
        json={
            "category_id": test_category["id"],
            "title": "Original",
            "amount": 100.0,
            "transaction_type": "expense",
            "frequency": "monthly",
            "day": 1
        },
        headers=test_user["headers"]
    )
    recurring_id = create_response.json()["id"]

    # Update the recurring transaction
    response = await client.put(
        f"/api/recurring/{recurring_id}",
        json={
            "title": "Updated Title",
            "amount": 150.0,
            "change_reason": "Price increase"
        },
        headers=test_user["headers"]
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["amount"] == 150.0


@pytest.mark.asyncio
async def test_update_recurring_with_future_date(client: AsyncClient, test_user, test_budget, test_category):
    """Test scheduling a future update for recurring transaction."""
    # Create a recurring transaction
    create_response = await client.post(
        f"/api/budgets/{test_budget['id']}/recurring",
        json={
            "category_id": test_category["id"],
            "title": "Future Update Test",
            "amount": 100.0,
            "transaction_type": "expense",
            "frequency": "monthly",
            "day": 1
        },
        headers=test_user["headers"]
    )
    recurring_id = create_response.json()["id"]

    # Schedule future update
    response = await client.put(
        f"/api/recurring/{recurring_id}",
        json={
            "amount": 200.0,
            "effective_date": "2030-01-01",  # Future date
            "change_reason": "Future price increase"
        },
        headers=test_user["headers"]
    )

    assert response.status_code == 200
    data = response.json()
    # Current values should remain unchanged
    assert data["amount"] == 100.0
    # But there should be a pending version
    assert data["pending_version"] is not None
    assert data["pending_version"]["amount"] == 200.0


@pytest.mark.asyncio
async def test_delete_recurring_transaction(client: AsyncClient, test_user, test_budget, test_category):
    """Test deleting a recurring transaction."""
    # Create a recurring transaction
    create_response = await client.post(
        f"/api/budgets/{test_budget['id']}/recurring",
        json={
            "category_id": test_category["id"],
            "title": "To Delete",
            "amount": 50.0,
            "transaction_type": "expense",
            "frequency": "monthly",
            "day": 1
        },
        headers=test_user["headers"]
    )
    recurring_id = create_response.json()["id"]

    # Delete the recurring transaction
    response = await client.delete(
        f"/api/recurring/{recurring_id}",
        headers=test_user["headers"]
    )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_get_recurring_versions(client: AsyncClient, test_user, test_budget, test_category):
    """Test retrieving version history for recurring transaction."""
    # Create a recurring transaction
    create_response = await client.post(
        f"/api/budgets/{test_budget['id']}/recurring",
        json={
            "category_id": test_category["id"],
            "title": "Version Test",
            "amount": 100.0,
            "transaction_type": "expense",
            "frequency": "monthly",
            "day": 1
        },
        headers=test_user["headers"]
    )
    recurring_id = create_response.json()["id"]

    # Update to create a version
    await client.put(
        f"/api/recurring/{recurring_id}",
        json={
            "amount": 150.0,
            "change_reason": "First update"
        },
        headers=test_user["headers"]
    )

    # Get versions
    response = await client.get(
        f"/api/recurring/{recurring_id}/versions",
        headers=test_user["headers"]
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_toggle_nonexistent_recurring(client: AsyncClient, test_user):
    """Test toggling non-existent recurring transaction."""
    response = await client.put(
        "/api/recurring/nonexistent-id/toggle",
        headers=test_user["headers"]
    )

    assert response.status_code == 404
