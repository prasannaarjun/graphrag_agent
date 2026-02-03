"""
Google OAuth 2.0 provider implementation.
"""

from urllib.parse import urlencode

import httpx

from src.config import get_settings

from .base import BaseOAuthProvider, OAuthUserInfo


class GoogleOAuthProvider(BaseOAuthProvider):
    """Google OAuth 2.0 provider."""

    AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

    SCOPES = [
        "openid",
        "email",
        "profile",
    ]

    @property
    def name(self) -> str:
        return "google"

    async def get_authorization_url(
        self,
        redirect_uri: str,
        state: str,
    ) -> str:
        """Get Google OAuth authorization URL."""
        settings = get_settings()

        if not settings.google_client_id:
            raise ValueError("GOOGLE_CLIENT_ID not configured")

        params = {
            "client_id": settings.google_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.SCOPES),
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }

        return f"{self.AUTHORIZATION_URL}?{urlencode(params)}"

    async def exchange_code(
        self,
        code: str,
        redirect_uri: str,
    ) -> dict:
        """Exchange authorization code for tokens."""
        settings = get_settings()

        if not settings.google_client_id or not settings.google_client_secret:
            raise ValueError("Google OAuth not configured")

        data = {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            return response.json()

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """Get user info from Google."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            data = response.json()

        return OAuthUserInfo(
            provider="google",
            provider_user_id=data["id"],
            email=data["email"],
            name=data.get("name"),
            avatar_url=data.get("picture"),
        )
