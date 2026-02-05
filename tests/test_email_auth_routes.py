"""
Tests for email/password authentication routes.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from src.api.auth_routes import UserLogin, UserRegistration, login, register
from src.db.models import User


class TestEmailAuthRoutes:
    """Tests for registration and login routes (mocked DB)."""

    @pytest.mark.asyncio
    @patch("src.api.auth_routes.get_db_session")
    @patch("src.api.auth_routes.create_access_token")
    async def test_register_success(self, mock_jwt, mock_db):
        """Test successful registration."""
        # Setup mock session
        mock_session_inst = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_session_inst

        # Mock execute result
        mock_result = MagicMock()
        mock_session_inst.execute.return_value = mock_result
        mock_result.scalar_one_or_none.return_value = None

        # Mock JWT creation
        mock_jwt.return_value = "fake-jwt-token"

        reg_data = UserRegistration(
            email="new@example.com", password="password123", name="New User"
        )

        response = await register(reg_data)

        assert response.access_token == "fake-jwt-token"
        assert mock_session_inst.add.called
        # Check that user was added
        added_user = mock_session_inst.add.call_args[0][0]
        assert isinstance(added_user, User)
        assert added_user.email == "new@example.com"
        assert added_user.hashed_password is not None

    @pytest.mark.asyncio
    @patch("src.api.auth_routes.get_db_session")
    async def test_register_duplicate_email(self, mock_db):
        """Test registration with existing email."""
        mock_session_inst = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_session_inst

        # Mock execute result
        mock_result = MagicMock()
        mock_session_inst.execute.return_value = mock_result
        mock_result.scalar_one_or_none.return_value = User(email="existing@example.com")

        reg_data = UserRegistration(email="existing@example.com", password="password123")

        with pytest.raises(HTTPException) as exc:
            await register(reg_data)

        assert exc.value.status_code == 400
        assert "already exists" in exc.value.detail

    @pytest.mark.asyncio
    @patch("src.api.auth_routes.get_db_session")
    @patch("src.api.auth_routes.create_access_token")
    @patch("src.api.auth_routes.verify_password")
    async def test_login_success(self, mock_verify, mock_jwt, mock_db):
        """Test successful login."""
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
        mock_jwt.return_value = "login-jwt-token"

        login_data = UserLogin(email="user@example.com", password="password123")

        response = await login(login_data)

        assert response.access_token == "login-jwt-token"

    @pytest.mark.asyncio
    @patch("src.api.auth_routes.get_db_session")
    @patch("src.api.auth_routes.verify_password")
    async def test_login_invalid_password(self, mock_verify, mock_db):
        """Test login with incorrect password."""
        mock_session_inst = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_session_inst

        # Mock execute result
        mock_result = MagicMock()
        mock_session_inst.execute.return_value = mock_result

        mock_result.scalar_one_or_none.return_value = User(
            email="user@example.com", hashed_password="hashed"
        )

        # Mock password verification failed
        mock_verify.return_value = False

        login_data = UserLogin(email="user@example.com", password="wrong")

        with pytest.raises(HTTPException) as exc:
            await login(login_data)

        assert exc.value.status_code == 401
