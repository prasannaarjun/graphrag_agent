"""API routes package."""

from .admin_routes import router as admin_router
from .auth_routes import router as auth_router
from .document_routes import router as document_router

__all__ = ["admin_router", "auth_router", "document_router"]
