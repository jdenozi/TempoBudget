# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""
Tempo Budget Backend API

FastAPI-based REST API server for the Tempo Budget application.
Swagger UI documentation is available at /docs.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

# Disable docs in production
DOCS_ENABLED = os.getenv("DOCS_ENABLED", "true").lower() == "true"
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .database import engine
from .routes import api_router, oidc_api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database schema on startup."""
    schema_path = os.path.join(os.path.dirname(__file__), "..", "schema.sql")
    async with engine.begin() as conn:
        with open(schema_path) as f:
            schema = f.read()
            # Execute each statement separately
            for statement in schema.split(";"):
                statement = statement.strip()
                if statement:
                    await conn.execute(text(statement))
    print("Database schema initialized")
    yield


app = FastAPI(
    title="Tempo Budget API",
    description="Personal and group budget management API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if DOCS_ENABLED else None,
    redoc_url="/redoc" if DOCS_ENABLED else None,
    openapi_url="/api-docs/openapi.json" if DOCS_ENABLED else None,
)

# Session middleware for OAuth state
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "tempobudget-session-secret-change-in-prod")
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)

# Include OIDC routes (at root level)
app.include_router(oidc_api_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
