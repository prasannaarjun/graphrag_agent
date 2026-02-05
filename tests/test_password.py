"""
Tests for password hashing and verification.
"""

from src.auth.password import hash_password, verify_password


class TestPassword:
    """Tests for password handling."""

    def test_hash_password(self):
        """Test that hashing a password returns a string."""
        password = "strong-password-123"
        hashed = hash_password(password)

        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed != password
        assert len(hashed) > 10

    def test_verify_correct_password(self):
        """Test verifying the correct password."""
        password = "secret-password"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_incorrect_password(self):
        """Test verifying an incorrect password."""
        password = "secret-password"
        hashed = hash_password(password)

        assert verify_password("wrong-password", hashed) is False

    def test_different_hashes_for_same_password(self):
        """Test that same password produces different hashes (salting)."""
        password = "secret-password"
        hashed1 = hash_password(password)
        hashed2 = hash_password(password)

        assert hashed1 != hashed2
        assert verify_password(password, hashed1) is True
        assert verify_password(password, hashed2) is True
