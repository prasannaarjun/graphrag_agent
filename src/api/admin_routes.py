"""
Health and admin API routes.
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["Admin"])


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    services: dict[str, str]


class AppInfo(BaseModel):
    """Application info response."""

    name: str
    version: str
    docs: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    GET /health

    Returns status of all connected services.
    """
    # TODO: Add actual health checks for Neo4j, PostgreSQL, MinIO
    services = {
        "api": "healthy",
        "neo4j": "healthy",
        "postgres": "healthy",
        "minio": "healthy",
    }

    # Check if any service is unhealthy
    all_healthy = all(s == "healthy" for s in services.values())

    return HealthResponse(status="healthy" if all_healthy else "degraded", services=services)


@router.get("/", response_model=AppInfo)
async def root():
    """
    API root - returns API info.

    GET /
    """
    return AppInfo(name="GraphRAG Agent API", version="0.1.0", docs="/docs")
