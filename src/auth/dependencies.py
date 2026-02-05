"""
FastAPI dependencies for authentication.
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordBearer,
)

from src.auth.jwt import decode_token
from src.core.tenant import TenantContext

# HTTP Bearer token security scheme (generic)
security = HTTPBearer(auto_error=False)

# OAuth2 Password Bearer scheme (specifically for Swagger UI)
# username field in form will be treated as email
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    token: Optional[str] = Depends(oauth2_scheme),
) -> TenantContext:
    """
    Dependency to get the current authenticated user.
    Supports both generic HTTPBearer and OAuth2PasswordBearer (Swagger UI).
    """
    actual_token = None
    if credentials:
        actual_token = credentials.credentials
    elif token:
        actual_token = token

    if not actual_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(actual_token)

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
    token: Optional[str] = Depends(oauth2_scheme),
) -> Optional[TenantContext]:
    """
    Dependency to optionally get the current user.
    """
    actual_token = None
    if credentials:
        actual_token = credentials.credentials
    elif token:
        actual_token = token

    if not actual_token:
        return None

    try:
        payload = decode_token(actual_token)
        return TenantContext(
            tenant_id=payload.get("tenant_id"),
            user_id=payload.get("user_id"),
            email=payload.get("email"),
        )
    except Exception:
        return None
