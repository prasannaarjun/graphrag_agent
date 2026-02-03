"""OAuth providers package."""

from .base import BaseOAuthProvider, OAuthUserInfo
from .github import GitHubOAuthProvider
from .google import GoogleOAuthProvider

__all__ = [
    "BaseOAuthProvider",
    "OAuthUserInfo",
    "GoogleOAuthProvider",
    "GitHubOAuthProvider",
]
