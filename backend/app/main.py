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
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .database import engine
from .routes import api_router


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
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api-docs/openapi.json",
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


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
