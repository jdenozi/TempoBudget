# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Authentication routes."""

import os
from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import create_token, get_current_user, hash_password, verify_password
from ..database import get_db
from ..models import AuthResponse, ChangePasswordRequest, CreateUser, LoginRequest, UpdateProfileRequest, User

AVATAR_DIR = os.path.join(os.getenv("DATA_PATH", os.path.join(os.path.dirname(__file__), "..", "..", "data")), "avatars")
ALLOWED_AVATAR_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2 MB

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


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Change the current user's password."""
    # Get current user with password hash
    result = await db.execute(
        text("SELECT password_hash FROM users WHERE id = :id"),
        {"id": user_id}
    )
    row = result.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verify current password
    if not verify_password(payload.current_password, row.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Hash and save new password
    new_hash = hash_password(payload.new_password)
    now = datetime.now(timezone.utc).isoformat()

    await db.execute(
        text("UPDATE users SET password_hash = :hash, updated_at = :updated_at WHERE id = :id"),
        {"hash": new_hash, "updated_at": now, "id": user_id}
    )
    await db.commit()

    return {"message": "Password changed successfully"}


@router.get("/me", response_model=User)
async def get_me(
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Return the current authenticated user."""
    result = await db.execute(
        text("SELECT id, email, name, avatar, phone, created_at, updated_at FROM users WHERE id = :id"),
        {"id": user_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return User(
        id=row.id, email=row.email, name=row.name,
        avatar=row.avatar, phone=row.phone,
        created_at=row.created_at, updated_at=row.updated_at,
    )


@router.put("/profile", response_model=User)
async def update_profile(
    payload: UpdateProfileRequest,
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's name and/or phone."""
    updates = []
    params: dict = {"id": user_id}
    if payload.name is not None:
        updates.append("name = :name")
        params["name"] = payload.name
    if payload.phone is not None:
        updates.append("phone = :phone")
        params["phone"] = payload.phone

    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    now = datetime.now(timezone.utc).isoformat()
    updates.append("updated_at = :updated_at")
    params["updated_at"] = now

    await db.execute(
        text(f"UPDATE users SET {', '.join(updates)} WHERE id = :id"),
        params,
    )
    await db.commit()

    result = await db.execute(
        text("SELECT id, email, name, avatar, phone, created_at, updated_at FROM users WHERE id = :id"),
        {"id": user_id},
    )
    row = result.fetchone()
    return User(
        id=row.id, email=row.email, name=row.name,
        avatar=row.avatar, phone=row.phone,
        created_at=row.created_at, updated_at=row.updated_at,
    )


@router.post("/avatar", response_model=User)
async def upload_avatar(
    file: Annotated[UploadFile, File()],
    user_id: Annotated[str, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Upload or replace the current user's avatar image."""
    if file.content_type not in ALLOWED_AVATAR_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image type")

    contents = await file.read()
    if len(contents) > MAX_AVATAR_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large (max 2 MB)")

    ext = file.content_type.split("/")[1]
    if ext == "jpeg":
        ext = "jpg"
    filename = f"{user_id}.{ext}"

    os.makedirs(AVATAR_DIR, exist_ok=True)

    # Remove old avatar files for this user
    for old in os.listdir(AVATAR_DIR):
        if old.startswith(f"{user_id}."):
            os.remove(os.path.join(AVATAR_DIR, old))

    filepath = os.path.join(AVATAR_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(contents)

    avatar_path = f"/api/auth/avatar/{filename}"
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        text("UPDATE users SET avatar = :avatar, updated_at = :updated_at WHERE id = :id"),
        {"avatar": avatar_path, "updated_at": now, "id": user_id},
    )
    await db.commit()

    result = await db.execute(
        text("SELECT id, email, name, avatar, phone, created_at, updated_at FROM users WHERE id = :id"),
        {"id": user_id},
    )
    row = result.fetchone()
    return User(
        id=row.id, email=row.email, name=row.name,
        avatar=row.avatar, phone=row.phone,
        created_at=row.created_at, updated_at=row.updated_at,
    )


@router.get("/avatar/{filename}")
async def get_avatar(filename: str):
    """Serve an avatar image file."""
    filepath = os.path.join(AVATAR_DIR, filename)
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Avatar not found")
    return FileResponse(filepath)
