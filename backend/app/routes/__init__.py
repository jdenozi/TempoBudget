# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""API routes module."""

from fastapi import APIRouter
from .auth import router as auth_router
from .budgets import router as budgets_router
from .categories import router as categories_router
from .transactions import router as transactions_router
from .budget_members import router as budget_members_router
from .invitations import router as invitations_router
from .pro import router as pro_router
from .oidc import router as oidc_router

api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(budgets_router, prefix="/budgets", tags=["budgets"])
api_router.include_router(categories_router, tags=["categories"])
api_router.include_router(transactions_router, tags=["transactions"])
api_router.include_router(budget_members_router, tags=["budget_members"])
api_router.include_router(invitations_router, prefix="/invitations", tags=["invitations"])
api_router.include_router(pro_router, prefix="/pro", tags=["pro"])

# OIDC router (at root level, not under /api)
oidc_api_router = oidc_router
