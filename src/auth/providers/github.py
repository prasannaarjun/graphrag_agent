"""
GitHub OAuth 2.0 provider implementation.
"""

from urllib.parse import urlencode

import httpx

from src.config import get_settings

from .base import BaseOAuthProvider, OAuthUserInfo


class GitHubOAuthProvider(BaseOAuthProvider):
    """GitHub OAuth 2.0 provider."""

    AUTHORIZATION_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    USERINFO_URL = "https://api.github.com/user"
    EMAILS_URL = "https://api.github.com/user/emails"

    SCOPES = [
        "read:user",
        "user:email",
    ]

    @property
    def name(self) -> str:
        return "github"

    async def get_authorization_url(
        self,
        redirect_uri: str,
        state: str,
    ) -> str:
        """Get GitHub OAuth authorization URL."""
        settings = get_settings()

        if not settings.github_client_id:
            raise ValueError("GITHUB_CLIENT_ID not configured")

        params = {
            "client_id": settings.github_client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(self.SCOPES),
            "state": state,
        }

        return f"{self.AUTHORIZATION_URL}?{urlencode(params)}"

    async def exchange_code(
        self,
        code: str,
        redirect_uri: str,
    ) -> dict:
        """Exchange authorization code for tokens."""
        settings = get_settings()

        if not settings.github_client_id or not settings.github_client_secret:
            raise ValueError("GitHub OAuth not configured")

        data = {
            "client_id": settings.github_client_id,
            "client_secret": settings.github_client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data=data,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """Get user info from GitHub."""
        async with httpx.AsyncClient() as client:
            # Get basic user info
            response = await client.get(
                self.USERINFO_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                },
            )
            response.raise_for_status()
            data = response.json()

            # Get primary email if not public
            email = data.get("email")
            if not email:
                emails_response = await client.get(
                    self.EMAILS_URL,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/vnd.github+json",
                    },
                )
                emails_response.raise_for_status()
                emails = emails_response.json()

                # Find primary email
                for email_obj in emails:
                    if email_obj.get("primary"):
                        email = email_obj["email"]
                        break

                # Fallback to first email
                if not email and emails:
                    email = emails[0]["email"]

        return OAuthUserInfo(
            provider="github",
            provider_user_id=str(data["id"]),
            email=email or "",
            name=data.get("name") or data.get("login"),
            avatar_url=data.get("avatar_url"),
        )
