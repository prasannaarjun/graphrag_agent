"""
FastAPI application entry point.
"""

import logging
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.admin_routes import router as admin_router
from src.api.auth_routes import router as auth_router
from src.api.chat_routes import router as chat_router
from src.api.document_routes import router as document_router
from src.api.kb_routes import router as kb_router
from src.api.models_routes import router as models_router
from src.config import get_settings

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
    force=True,
)

# Reduce SQLAlchemy noise
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)

# Reduce async db noise
logging.getLogger("asyncpg").setLevel(logging.WARNING)

app = FastAPI(
    title="GraphRAG Agent API",
    description="Multi-tenant GraphRAG agent with LangChain & LangGraph",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Note: TenantMiddleware is not added here because we use
# dependency injection (get_current_user) for auth instead.
# This gives more flexibility per-endpoint.

# Include routers
app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(document_router)
app.include_router(kb_router)
app.include_router(models_router)


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    print(f"Starting {settings.app_name} in {settings.app_env} mode")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    print("Shutting down GraphRAG Agent")
