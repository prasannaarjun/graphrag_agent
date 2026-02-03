"""
FastAPI dependencies for authentication.
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.auth.jwt import decode_token
from src.core.tenant import TenantContext

# HTTP Bearer token security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> TenantContext:
    """
    Dependency to get the current authenticated user.

    Can be used in route handlers to require authentication:

        @router.get("/protected")
        async def protected_route(user: TenantContext = Depends(get_current_user)):
            return {"tenant_id": user.tenant_id}

    Args:
        credentials: HTTP Bearer credentials from Authorization header

    Returns:
        TenantContext with user and tenant information

    Raises:
        HTTPException: If authentication fails
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(credentials.credentials)

        # Create and return tenant context
        return TenantContext(
            tenant_id=payload.get("tenant_id"),
            user_id=payload.get("user_id"),
            email=payload.get("email"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[TenantContext]:
    """
    Dependency to optionally get the current user.

    Returns None if no valid token is provided instead of raising an error.
    Useful for endpoints that work differently for authenticated users.

    Returns:
        TenantContext if authenticated, None otherwise
    """
    if credentials is None:
        return None

    try:
        payload = decode_token(credentials.credentials)
        return TenantContext(
            tenant_id=payload.get("tenant_id"),
            user_id=payload.get("user_id"),
            email=payload.get("email"),
        )
    except Exception:
        return None
