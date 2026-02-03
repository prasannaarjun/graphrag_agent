"""
Tests for authentication functionality.
"""


from src.auth.jwt import create_access_token, create_refresh_token, decode_token


class TestJWT:
    """Tests for JWT token handling."""

    def test_create_access_token(self):
        """Test creating an access token."""
        token = create_access_token(
            user_id="user_123", tenant_id="tenant_456", email="test@example.com"
        )

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_token(self):
        """Test decoding a valid token."""
        token = create_access_token(
            user_id="user_123", tenant_id="tenant_456", email="test@example.com"
        )

        payload = decode_token(token)

        assert payload["user_id"] == "user_123"
        assert payload["tenant_id"] == "tenant_456"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "access"

    def test_token_with_extra_claims(self):
        """Test token with extra claims."""
        token = create_access_token(
            user_id="user_123",
            tenant_id="tenant_456",
            extra_claims={"role": "admin", "org": "acme"},
        )

        payload = decode_token(token)

        assert payload["role"] == "admin"
        assert payload["org"] == "acme"

    def test_refresh_token(self):
        """Test creating a refresh token."""
        token = create_refresh_token(user_id="user_123", tenant_id="tenant_456")

        payload = decode_token(token)

        assert payload["type"] == "refresh"
        assert payload["user_id"] == "user_123"
