"""
Tests for the /auth/token endpoint (Swagger UI support).
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from src.api.auth_routes import login_for_access_token
from src.db.models import User


class TestOAuth2TokenRoute:
    """Tests for the /auth/token route (mocked DB)."""

    @pytest.mark.asyncio
    @patch("src.api.auth_routes.get_db_session")
    @patch("src.api.auth_routes.create_access_token")
    @patch("src.api.auth_routes.verify_password")
    async def test_token_login_success(self, mock_verify, mock_jwt, mock_db):
        """Test successful token login via OAuth2 form."""
        mock_session_inst = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_session_inst

        # Mock execute result
        mock_result = MagicMock()
        mock_session_inst.execute.return_value = mock_result

        fake_user = User(
            id="user-123",
            tenant_id="tenant-123",
            email="user@example.com",
            hashed_password="hashed-password",
            name="Test User",
        )
        mock_result.scalar_one_or_none.return_value = fake_user

        # Mock password verification
        mock_verify.return_value = True

        # Mock JWT
        mock_jwt.return_value = "token-jwt-token"

        # Mock form data
        form_data = MagicMock(spec=OAuth2PasswordRequestForm)
        form_data.username = "user@example.com"
        form_data.password = "password123"

        response = await login_for_access_token(form_data=form_data)

        assert response.access_token == "token-jwt-token"
        assert response.token_type == "bearer"

    @pytest.mark.asyncio
    @patch("src.api.auth_routes.get_db_session")
    async def test_token_login_user_not_found(self, mock_db):
        """Test token login with non-existent user."""
        mock_session_inst = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_session_inst

        mock_result = MagicMock()
        mock_session_inst.execute.return_value = mock_result
        mock_result.scalar_one_or_none.return_value = None

        form_data = MagicMock(spec=OAuth2PasswordRequestForm)
        form_data.username = "unknown@example.com"
        form_data.password = "any"

        with pytest.raises(HTTPException) as exc:
            await login_for_access_token(form_data=form_data)

        assert exc.value.status_code == 401
