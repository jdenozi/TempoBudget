# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Authentication routes."""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import create_token, hash_password, verify_password
from ..database import get_db
from ..models import AuthResponse, CreateUser, LoginRequest, User

router = APIRouter()


@router.post("/register", response_model=AuthResponse)
async def register(payload: CreateUser, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    # Check if email already exists
    result = await db.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": payload.email}
    )
    if result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    user_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()
    password_hash = hash_password(payload.password)

    await db.execute(
        text("""
            INSERT INTO users (id, email, name, password_hash, created_at, updated_at)
            VALUES (:id, :email, :name, :password_hash, :created_at, :updated_at)
        """),
        {
            "id": user_id,
            "email": payload.email,
            "name": payload.name,
            "password_hash": password_hash,
            "created_at": now,
            "updated_at": now,
        }
    )
    await db.commit()

    # Fetch the created user
    result = await db.execute(
        text("SELECT id, email, name, avatar, phone, created_at, updated_at FROM users WHERE id = :id"),
        {"id": user_id}
    )
    row = result.fetchone()
    user = User(
        id=row.id,
        email=row.email,
        name=row.name,
        avatar=row.avatar,
        phone=row.phone,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )

    token = create_token(user_id)
    return AuthResponse(token=token, user=user)


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate a user and return a JWT token."""
    result = await db.execute(
        text("SELECT id, email, name, password_hash, avatar, phone, created_at, updated_at FROM users WHERE email = :email"),
        {"email": payload.email}
    )
    row = result.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not verify_password(payload.password, row.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    user = User(
        id=row.id,
        email=row.email,
        name=row.name,
        avatar=row.avatar,
        phone=row.phone,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )

    token = create_token(row.id)
    return AuthResponse(token=token, user=user)
