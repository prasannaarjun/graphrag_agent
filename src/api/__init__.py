"""API routes package."""

from .admin_routes import router as admin_router
from .auth_routes import router as auth_router
from .chat_routes import router as chat_router
from .document_routes import router as document_router
from .kb_routes import router as kb_router
from .models_routes import router as models_router

__all__ = [
    "admin_router",
    "auth_router",
    "chat_router",
    "document_router",
    "kb_router",
    "models_router",
]
