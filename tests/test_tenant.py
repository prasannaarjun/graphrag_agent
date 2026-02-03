"""
Tests for tenant context management.
"""

import pytest

from src.core.tenant import TenantContext


class TestTenantContext:
    """Tests for TenantContext."""

    def test_set_and_get_context(self):
        """Test setting and getting tenant context."""
        TenantContext.set(tenant_id="tenant_123", user_id="user_456", email="test@example.com")

        ctx = TenantContext.get_current()

        assert ctx.tenant_id == "tenant_123"
        assert ctx.user_id == "user_456"
        assert ctx.email == "test@example.com"

        # Cleanup
        TenantContext.clear()

    def test_get_current_without_context(self):
        """Test getting context when not set raises error."""
        TenantContext.clear()

        with pytest.raises(RuntimeError, match="No tenant context set"):
            TenantContext.get_current()

    def test_get_current_or_none(self):
        """Test get_current_or_none returns None when not set."""
        TenantContext.clear()

        ctx = TenantContext.get_current_or_none()

        assert ctx is None

    def test_clear_context(self):
        """Test clearing tenant context."""
        TenantContext.set(tenant_id="test", user_id="user")
        TenantContext.clear()

        assert TenantContext.get_current_or_none() is None
