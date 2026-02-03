"""
Tenant context management for multi-tenancy.
Uses contextvars for request-scoped tenant isolation.
"""

from contextvars import ContextVar
from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

# Context variable for tenant context
_tenant_context: ContextVar[Optional["TenantContext"]] = ContextVar("tenant_context", default=None)


@dataclass
class TenantContext:
    """
    Holds tenant-specific context for the current request.

    All database operations should use this to scope data access.
    """

    tenant_id: str
    user_id: str
    email: Optional[str] = None

    @classmethod
    def get_current(cls) -> "TenantContext":
        """
        Get the current tenant context.

        Raises:
            RuntimeError: If no tenant context is set.
        """
        ctx = _tenant_context.get()
        if ctx is None:
            raise RuntimeError("No tenant context set. Ensure TenantMiddleware is applied.")
        return ctx

    @classmethod
    def get_current_or_none(cls) -> Optional["TenantContext"]:
        """Get the current tenant context or None if not set."""
        return _tenant_context.get()

    @classmethod
    def set(cls, tenant_id: str, user_id: str, email: Optional[str] = None) -> "TenantContext":
        """
        Set the tenant context for the current request.

        Args:
            tenant_id: The tenant identifier
            user_id: The user identifier
            email: Optional user email

        Returns:
            The created TenantContext
        """
        ctx = cls(tenant_id=tenant_id, user_id=user_id, email=email)
        _tenant_context.set(ctx)
        return ctx

    @classmethod
    def clear(cls) -> None:
        """Clear the current tenant context."""
        _tenant_context.set(None)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract tenant context from JWT and set it for the request.

    Skips authentication for public endpoints like /health, /docs, /auth/*.
    """

    # Endpoints that don't require authentication
    PUBLIC_PATHS = {
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    PUBLIC_PREFIXES = ("/auth/",)

    async def dispatch(self, request: Request, call_next):
        # Skip auth for public endpoints
        path = request.url.path

        if path in self.PUBLIC_PATHS or path.startswith(self.PUBLIC_PREFIXES):
            return await call_next(request)

        # Extract and validate JWT token
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

        token = auth_header.replace("Bearer ", "")

        try:
            # Import here to avoid circular imports
            from src.auth.jwt import decode_token

            payload = decode_token(token)

            # Set tenant context
            TenantContext.set(
                tenant_id=payload.get("tenant_id"),
                user_id=payload.get("user_id"),
                email=payload.get("email"),
            )
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

        try:
            response = await call_next(request)
            return response
        finally:
            # Clear context after request
            TenantContext.clear()
