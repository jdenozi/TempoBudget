# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""OIDC authentication routes for SSO via Authentik."""

import os
import uuid

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from starlette.config import Config

from ..database import get_db
from ..auth import create_token
from sqlalchemy import text

router = APIRouter()

# OIDC Configuration
OIDC_CLIENT_ID = os.getenv("OIDC_CLIENT_ID", "tempobudget")
OIDC_CLIENT_SECRET = os.getenv("OIDC_CLIENT_SECRET", "tempobudget-secret-tempo-2024")
OIDC_ISSUER = os.getenv("OIDC_ISSUER", "https://auth.tempo-hub.fr/application/o/tempobudget/")
OIDC_REDIRECT_URI = os.getenv("OIDC_REDIRECT_URI", "https://budget.tempo-finance.com/auth/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://budget.tempo-finance.com")

# Setup OAuth
oauth = OAuth()
oauth.register(
    name='authentik',
    client_id=OIDC_CLIENT_ID,
    client_secret=OIDC_CLIENT_SECRET,
    server_metadata_url=f"{OIDC_ISSUER}.well-known/openid-configuration",
    client_kwargs={
        'scope': 'openid email profile',
        'token_endpoint_auth_method': 'client_secret_post'
    },
    id_token_signing_alg_values_supported=['RS256']
)


@router.get("/auth/login")
async def auth_login(request: Request):
    """Initiate OIDC login flow."""
    redirect_uri = OIDC_REDIRECT_URI
    return await oauth.authentik.authorize_redirect(request, redirect_uri)


@router.get("/auth/callback")
async def auth_callback(request: Request):
    """Handle OIDC callback and create/login user."""
    try:
        token = await oauth.authentik.authorize_access_token(request)

        # Get user info from token or userinfo endpoint
        user_info = token.get('userinfo')
        if not user_info:
            # Fetch from userinfo endpoint
            user_info = await oauth.authentik.userinfo(token=token)

        email = user_info.get('email')
        name = user_info.get('name') or user_info.get('preferred_username') or email.split('@')[0] if email else None

        if not email:
            return RedirectResponse(
                url=f"{FRONTEND_URL}/login?error=Email%20requis.%20Vérifiez%20que%20le%20scope%20'email'%20est%20autorisé%20dans%20Authentik.",
                status_code=302
            )

        # Find or create user in database
        async with get_db() as db:
            # Check if user exists
            result = await db.execute(
                text("SELECT id, email, name, avatar, phone, created_at, updated_at FROM users WHERE email = :email"),
                {"email": email}
            )
            user_row = result.fetchone()

            if user_row:
                # User exists
                user_id = user_row[0]
                user = {
                    "id": user_row[0],
                    "email": user_row[1],
                    "name": user_row[2],
                    "avatar": user_row[3],
                    "phone": user_row[4],
                    "created_at": str(user_row[5]),
                    "updated_at": str(user_row[6])
                }
            else:
                # Create new user (JIT provisioning)
                user_id = str(uuid.uuid4())
                await db.execute(
                    text("""
                        INSERT INTO users (id, email, name, password_hash, created_at, updated_at)
                        VALUES (:id, :email, :name, 'oidc-no-password', datetime('now'), datetime('now'))
                    """),
                    {"id": user_id, "email": email, "name": name}
                )
                await db.commit()

                user = {
                    "id": user_id,
                    "email": email,
                    "name": name,
                    "avatar": None,
                    "phone": None,
                    "created_at": "",
                    "updated_at": ""
                }

        # Create JWT token
        jwt_token = create_token(user_id)

        # Redirect to frontend with token
        return RedirectResponse(
            url=f"{FRONTEND_URL}/auth/success?token={jwt_token}",
            status_code=302
        )

    except Exception as e:
        error_msg = str(e).replace("'", "").replace('"', '')
        return RedirectResponse(
            url=f"{FRONTEND_URL}/login?error=Erreur%20d%27authentification%3A%20{error_msg}",
            status_code=302
        )


@router.get("/auth/logout")
async def auth_logout(request: Request):
    """Logout and redirect to Authentik logout."""
    # Redirect to Authentik end session endpoint
    authentik_logout_url = f"https://auth.tempo-hub.fr/application/o/tempobudget/end-session/"
    return RedirectResponse(url=authentik_logout_url, status_code=302)
