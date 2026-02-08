# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Tests for category endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_category(client: AsyncClient, test_user, test_budget):
    """Test creating a category."""
    response = await client.post(
        f"/api/budgets/{test_budget['id']}/categories",
        json={
            "name": "Groceries",
            "amount": 300.0,
            "tags": ["besoin"]
        },
        headers=test_user["headers"]
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Groceries"
    assert data["amount"] == 300.0
    assert data["budget_id"] == test_budget["id"]
    assert "besoin" in data["tags"]


@pytest.mark.asyncio
async def test_create_subcategory(client: AsyncClient, test_user, test_budget, test_category):
    """Test creating a subcategory."""
    response = await client.post(
        f"/api/budgets/{test_budget['id']}/categories",
        json={
            "name": "Subcategory",
            "amount": 100.0,
            "parent_id": test_category["id"]
        },
        headers=test_user["headers"]
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Subcategory"
    assert data["parent_id"] == test_category["id"]


@pytest.mark.asyncio
async def test_get_categories(client: AsyncClient, test_user, test_budget, test_category):
    """Test retrieving categories for a budget."""
    response = await client.get(
        f"/api/budgets/{test_budget['id']}/categories",
        headers=test_user["headers"]
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(c["id"] == test_category["id"] for c in data)


@pytest.mark.asyncio
async def test_update_category(client: AsyncClient, test_user, test_category):
    """Test updating a category."""
    response = await client.put(
        f"/api/categories/{test_category['id']}",
        json={
            "name": "Updated Category",
            "amount": 750.0
        },
        headers=test_user["headers"]
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Category"
    assert data["amount"] == 750.0


@pytest.mark.asyncio
async def test_update_category_tags(client: AsyncClient, test_user, test_category):
    """Test updating category tags."""
    response = await client.put(
        f"/api/categories/{test_category['id']}",
        json={
            "tags": ["loisir", "épargne"]
        },
        headers=test_user["headers"]
    )

    assert response.status_code == 200
    data = response.json()
    assert "loisir" in data["tags"]
    assert "épargne" in data["tags"]


@pytest.mark.asyncio
async def test_update_nonexistent_category(client: AsyncClient, test_user):
    """Test updating a non-existent category."""
    response = await client.put(
        "/api/categories/nonexistent-id",
        json={"name": "Test"},
        headers=test_user["headers"]
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_category(client: AsyncClient, test_user, test_budget):
    """Test deleting a category."""
    # Create a category to delete
    create_response = await client.post(
        f"/api/budgets/{test_budget['id']}/categories",
        json={"name": "To Delete", "amount": 100.0},
        headers=test_user["headers"]
    )
    category_id = create_response.json()["id"]

    # Delete the category
    response = await client.delete(
        f"/api/categories/{category_id}",
        headers=test_user["headers"]
    )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_category_with_subcategories_fails(client: AsyncClient, test_user, test_budget, test_category):
    """Test that deleting a category with subcategories fails."""
    # Create a subcategory
    await client.post(
        f"/api/budgets/{test_budget['id']}/categories",
        json={
            "name": "Subcategory",
            "amount": 50.0,
            "parent_id": test_category["id"]
        },
        headers=test_user["headers"]
    )

    # Try to delete parent category
    response = await client.delete(
        f"/api/categories/{test_category['id']}",
        headers=test_user["headers"]
    )

    assert response.status_code == 400
    assert "subcategories" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_parent_amount_updates_with_subcategories(client: AsyncClient, test_user, test_budget):
    """Test that parent category amount updates when subcategories are added."""
    # Create parent with 0 amount
    parent_response = await client.post(
        f"/api/budgets/{test_budget['id']}/categories",
        json={"name": "Parent", "amount": 0},
        headers=test_user["headers"]
    )
    parent_id = parent_response.json()["id"]

    # Add subcategories
    await client.post(
        f"/api/budgets/{test_budget['id']}/categories",
        json={"name": "Sub1", "amount": 100.0, "parent_id": parent_id},
        headers=test_user["headers"]
    )
    await client.post(
        f"/api/budgets/{test_budget['id']}/categories",
        json={"name": "Sub2", "amount": 150.0, "parent_id": parent_id},
        headers=test_user["headers"]
    )

    # Check parent amount
    categories_response = await client.get(
        f"/api/budgets/{test_budget['id']}/categories",
        headers=test_user["headers"]
    )
    categories = categories_response.json()
    parent = next(c for c in categories if c["id"] == parent_id)

    assert parent["amount"] == 250.0  # 100 + 150
