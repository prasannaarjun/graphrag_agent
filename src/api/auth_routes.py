"""
Authentication API routes.
"""

import secrets
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy import select

from src.auth.jwt import create_access_token
from src.auth.password import hash_password, verify_password
from src.auth.providers import GitHubOAuthProvider, GoogleOAuthProvider
from src.db.models import User
from src.db.session import get_db_session

router = APIRouter(prefix="/auth", tags=["Authentication"])


# OAuth state storage (in production, use Redis or database)
_oauth_states: dict[str, str] = {}


class TokenResponse(BaseModel):
    """Token response model."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400


class UserRegistration(BaseModel):
    """User registration model."""

    email: EmailStr
    password: str
    name: Optional[str] = None


class UserLogin(BaseModel):
    """User login model."""

    email: EmailStr
    password: str


# Provider registry
PROVIDERS = {
    "google": GoogleOAuthProvider,
    "github": GitHubOAuthProvider,
}


@router.post("/register", response_model=TokenResponse)
async def register(request: UserRegistration):
    """
    Register a new user with email and password.
    """
    async with get_db_session() as session:
        # Check if user already exists
        result = await session.execute(select(User).where(User.email == request.email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(status_code=400, detail="User with this email already exists")

        # Create new user
        user_id = str(uuid.uuid4())
        tenant_id = f"tenant_{user_id[:8]}"

        new_user = User(
            id=user_id,
            tenant_id=tenant_id,
            email=request.email,
            name=request.name,
            hashed_password=hash_password(request.password),
        )
        session.add(new_user)
        # Session will commit on exit

    # Generate JWT
    jwt_token = create_access_token(
        user_id=user_id,
        tenant_id=tenant_id,
        email=request.email,
        extra_claims={"name": request.name},
    )

    return TokenResponse(access_token=jwt_token)


@router.post("/login", response_model=TokenResponse)
async def login(request: UserLogin):
    """
    Login with email and password.
    """
    async with get_db_session() as session:
        result = await session.execute(select(User).where(User.email == request.email))
        user = result.scalar_one_or_none()

        if not user or not user.hashed_password:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not verify_password(request.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        user_id = user.id
        tenant_id = user.tenant_id
        email = user.email
        name = user.name

    # Generate JWT
    jwt_token = create_access_token(
        user_id=user_id,
        tenant_id=tenant_id,
        email=email,
        extra_claims={"name": name},
    )

    return TokenResponse(access_token=jwt_token)


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """
    OAuth2 compatible token login, retrieve an access token for future requests.
    Specifically added to support the "Authorize" button in Swagger UI.
    """
    async with get_db_session() as session:
        result = await session.execute(select(User).where(User.email == form_data.username))
        user = result.scalar_one_or_none()

        if not user or not user.hashed_password:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        uid = user.id
        tid = user.tenant_id
        email = user.email
        name = user.name

    # Generate JWT
    jwt_token = create_access_token(
        user_id=uid,
        tenant_id=tid,
        email=email,
        extra_claims={"name": name},
    )

    return TokenResponse(access_token=jwt_token)


@router.get("/login/{provider}")
async def oauth_login(provider: str, request: Request):
    """
    Initiate OAuth login flow.
    """
    if provider not in PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown provider: {provider}. Available: {list(PROVIDERS.keys())}",
        )

    oauth = PROVIDERS[provider]()
    state = secrets.token_urlsafe(32)

    _oauth_states[state] = provider
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
    OAuth callback - exchange code for tokens and link/create user.
    """
    stored_provider = _oauth_states.pop(state, None)
    if stored_provider != provider:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    if provider not in PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    oauth = PROVIDERS[provider]()
    redirect_uri = str(request.url_for("oauth_callback", provider=provider))

    try:
        tokens = await oauth.exchange_code(code, redirect_uri)
        access_token = tokens.get("access_token")

        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token from provider")

        user_info = await oauth.get_user_info(access_token)

        async with get_db_session() as session:
            # Check if user exists by email
            result = await session.execute(select(User).where(User.email == user_info.email))
            user = result.scalar_one_or_none()

            if user:
                # Link account if not already linked
                user.provider = provider
                user.provider_user_id = user_info.provider_user_id
                if not user.name:
                    user.name = user_info.name
                if not user.avatar_url:
                    user.avatar_url = user_info.avatar_url
            else:
                # Create new user
                user_id = str(uuid.uuid4())
                tenant_id = f"tenant_{user_id[:8]}"
                user = User(
                    id=user_id,
                    tenant_id=tenant_id,
                    email=user_info.email,
                    name=user_info.name,
                    avatar_url=user_info.avatar_url,
                    provider=provider,
                    provider_user_id=user_info.provider_user_id,
                )
                session.add(user)

            # Capture values for JWT
            uid = user.id
            tid = user.tenant_id
            email = user.email
            name = user.name
            avatar = user.avatar_url

        # Generate JWT
        jwt_token = create_access_token(
            user_id=uid,
            tenant_id=tid,
            email=email,
            extra_claims={
                "name": name,
                "avatar_url": avatar,
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
