"""
Health and admin API routes.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from src.db.session import get_db_session
from src.knowledge_graph.tenant_graph import get_graph_client
from src.object_store.minio_client import get_minio_client

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
    Returns status of all connected services.
    """
    services = {"api": "healthy"}

    # Check Postgres
    try:
        async with get_db_session() as session:
            await session.execute(text("SELECT 1"))
        services["postgres"] = "healthy"
    except Exception as e:
        services["postgres"] = f"unhealthy: {str(e)}"

    # Check Neo4j
    try:
        graph = get_graph_client()
        driver = await graph._get_driver()
        async with driver.session() as session:
            await session.run("RETURN 1")
        services["neo4j"] = "healthy"
    except Exception as e:
        services["neo4j"] = f"unhealthy: {str(e)}"

    # Check MinIO
    try:
        minio = get_minio_client()
        minio.client.list_buckets()
        services["minio"] = "healthy"
    except Exception as e:
        services["minio"] = f"unhealthy: {str(e)}"

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
