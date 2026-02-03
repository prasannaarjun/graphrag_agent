"""
Base OAuth provider interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class OAuthUserInfo:
    """User information from OAuth provider."""

    provider: str
    provider_user_id: str
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None


class BaseOAuthProvider(ABC):
    """Abstract base class for OAuth providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'google', 'github')."""
        pass

    @abstractmethod
    async def get_authorization_url(
        self,
        redirect_uri: str,
        state: str,
    ) -> str:
        """
        Get the OAuth authorization URL.

        Args:
            redirect_uri: URL to redirect to after authorization
            state: Random state string for CSRF protection

        Returns:
            Authorization URL to redirect user to
        """
        pass

    @abstractmethod
    async def exchange_code(
        self,
        code: str,
        redirect_uri: str,
    ) -> dict:
        """
        Exchange authorization code for tokens.

        Args:
            code: Authorization code from callback
            redirect_uri: Same redirect URI used in authorization

        Returns:
            Dict containing access_token and optionally refresh_token
        """
        pass

    @abstractmethod
    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """
        Get user information using access token.

        Args:
            access_token: OAuth access token

        Returns:
            OAuthUserInfo with user details
        """
        pass
