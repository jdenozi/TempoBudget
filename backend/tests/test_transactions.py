# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Tests for transaction endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_expense_transaction(client: AsyncClient, test_user, test_budget, test_category):
    """Test creating an expense transaction."""
    response = await client.post(
        f"/api/budgets/{test_budget['id']}/transactions",
        json={
            "category_id": test_category["id"],
            "title": "Grocery Shopping",
            "amount": 75.50,
            "transaction_type": "expense",
            "date": "2024-01-15",
            "comment": "Weekly groceries"
        },
        headers=test_user["headers"]
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Grocery Shopping"
    assert data["amount"] == 75.50
    assert data["transaction_type"] == "expense"
    assert data["category_id"] == test_category["id"]
    assert data["budget_id"] == test_budget["id"]


@pytest.mark.asyncio
async def test_create_income_transaction(client: AsyncClient, test_user, test_budget, test_category):
    """Test creating an income transaction."""
    response = await client.post(
        f"/api/budgets/{test_budget['id']}/transactions",
        json={
            "category_id": test_category["id"],
            "title": "Salary",
            "amount": 3000.0,
            "transaction_type": "income",
            "date": "2024-01-01"
        },
        headers=test_user["headers"]
    )

    assert response.status_code == 200
    data = response.json()
    assert data["transaction_type"] == "income"
    assert data["amount"] == 3000.0


@pytest.mark.asyncio
async def test_get_transactions(client: AsyncClient, test_user, test_budget, test_category):
    """Test retrieving transactions for a budget."""
    # Create a transaction first
    await client.post(
        f"/api/budgets/{test_budget['id']}/transactions",
        json={
            "category_id": test_category["id"],
            "title": "Test Transaction",
            "amount": 50.0,
            "transaction_type": "expense",
            "date": "2024-01-15"
        },
        headers=test_user["headers"]
    )

    response = await client.get(
        f"/api/budgets/{test_budget['id']}/transactions",
        headers=test_user["headers"]
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_update_transaction(client: AsyncClient, test_user, test_budget, test_category):
    """Test updating a transaction."""
    # Create a transaction
    create_response = await client.post(
        f"/api/budgets/{test_budget['id']}/transactions",
        json={
            "category_id": test_category["id"],
            "title": "Original Title",
            "amount": 100.0,
            "transaction_type": "expense",
            "date": "2024-01-15"
        },
        headers=test_user["headers"]
    )
    transaction_id = create_response.json()["id"]

    # Update the transaction
    response = await client.put(
        f"/api/transactions/{transaction_id}",
        json={
            "title": "Updated Title",
            "amount": 150.0
        },
        headers=test_user["headers"]
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["amount"] == 150.0


@pytest.mark.asyncio
async def test_update_nonexistent_transaction(client: AsyncClient, test_user):
    """Test updating a non-existent transaction."""
    response = await client.put(
        "/api/transactions/nonexistent-id",
        json={"title": "Test"},
        headers=test_user["headers"]
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_transaction(client: AsyncClient, test_user, test_budget, test_category):
    """Test deleting a transaction."""
    # Create a transaction
    create_response = await client.post(
        f"/api/budgets/{test_budget['id']}/transactions",
        json={
            "category_id": test_category["id"],
            "title": "To Delete",
            "amount": 50.0,
            "transaction_type": "expense",
            "date": "2024-01-15"
        },
        headers=test_user["headers"]
    )
    transaction_id = create_response.json()["id"]

    # Delete the transaction
    response = await client.delete(
        f"/api/transactions/{transaction_id}",
        headers=test_user["headers"]
    )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_transaction_with_paid_by_user(client: AsyncClient, test_user, test_budget, test_category):
    """Test creating a transaction with paid_by_user_id."""
    response = await client.post(
        f"/api/budgets/{test_budget['id']}/transactions",
        json={
            "category_id": test_category["id"],
            "title": "Shared Expense",
            "amount": 100.0,
            "transaction_type": "expense",
            "date": "2024-01-15",
            "paid_by_user_id": test_user["user"]["id"]
        },
        headers=test_user["headers"]
    )

    assert response.status_code == 200
    data = response.json()
    assert data["paid_by_user_id"] == test_user["user"]["id"]
