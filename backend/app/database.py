# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Database configuration and session management."""

import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./budget.db")

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass


async def get_db() -> AsyncSession:
    """Dependency that provides a database session."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database schema."""
    schema_path = os.path.join(os.path.dirname(__file__), "..", "schema.sql")
    async with engine.begin() as conn:
        with open(schema_path) as f:
            schema = f.read()
            for statement in schema.split(";"):
                statement = statement.strip()
                if statement:
                    await conn.execute(statement + ";")
