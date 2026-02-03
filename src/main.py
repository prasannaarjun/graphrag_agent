"""
FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.admin_routes import router as admin_router
from src.api.auth_routes import router as auth_router
from src.config import get_settings

settings = get_settings()

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


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    print(f"Starting {settings.app_name} in {settings.app_env} mode")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    print("Shutting down GraphRAG Agent")
