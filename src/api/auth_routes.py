"""
Authentication API routes.
"""

import secrets
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from src.auth.jwt import create_access_token
from src.auth.providers import GitHubOAuthProvider, GoogleOAuthProvider

router = APIRouter(prefix="/auth", tags=["Authentication"])


# OAuth state storage (in production, use Redis or database)
_oauth_states: dict[str, str] = {}


class TokenResponse(BaseModel):
    """Token response model."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400


class UserInfo(BaseModel):
    """User info response model."""

    user_id: str
    email: str
    name: Optional[str] = None
    tenant_id: str
    avatar_url: Optional[str] = None


# Provider registry
PROVIDERS = {
    "google": GoogleOAuthProvider,
    "github": GitHubOAuthProvider,
}


@router.get("/login/{provider}")
async def oauth_login(provider: str, request: Request):
    """
    Initiate OAuth login flow.

    GET /auth/login/google
    GET /auth/login/github
    """
    if provider not in PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown provider: {provider}. Available: {list(PROVIDERS.keys())}",
        )

    oauth = PROVIDERS[provider]()
    state = secrets.token_urlsafe(32)

    # Store state for verification (in production, use Redis with TTL)
    _oauth_states[state] = provider

    # Build redirect URI
    redirect_uri = str(request.url_for("oauth_callback", provider=provider))

    auth_url = await oauth.get_authorization_url(redirect_uri, state)

    return RedirectResponse(auth_url)


@router.get("/callback/{provider}")
async def oauth_callback(
    provider: str,
    code: str,
    state: str,
    request: Request,
) -> TokenResponse:
    """
    OAuth callback - exchange code for tokens.

    GET /auth/callback/google?code=xxx&state=xxx
    """
    # Verify state
    stored_provider = _oauth_states.pop(state, None)
    if stored_provider != provider:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    if provider not in PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    oauth = PROVIDERS[provider]()
    redirect_uri = str(request.url_for("oauth_callback", provider=provider))

    try:
        # Exchange code for tokens
        tokens = await oauth.exchange_code(code, redirect_uri)
        access_token = tokens.get("access_token")

        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token from provider")

        # Get user info from provider
        user_info = await oauth.get_user_info(access_token)

        # Create tenant ID from provider user ID
        # In production, look up or create user in database
        tenant_id = f"tenant_{provider}_{user_info.provider_user_id}"
        user_id = f"{provider}_{user_info.provider_user_id}"

        # Generate JWT
        jwt_token = create_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            email=user_info.email,
            extra_claims={
                "name": user_info.name,
                "avatar_url": user_info.avatar_url,
                "provider": provider,
            },
        )

        return TokenResponse(access_token=jwt_token)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth authentication failed: {str(e)}")


@router.get("/providers")
async def list_providers():
    """List available OAuth providers."""
    return {"providers": list(PROVIDERS.keys())}
