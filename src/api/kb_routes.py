"""
Knowledge Base API routes for entity search and stats.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.auth.dependencies import get_current_user
from src.core.tenant import TenantContext
from src.knowledge_graph import get_graph_client
from src.llm import get_embedding_model
from src.vector_store import get_pgvector_client

router = APIRouter(prefix="/kb", tags=["Knowledge Base"])


class KBStatsResponse(BaseModel):
    """Knowledge base statistics."""

    document_chunks: int
    tenant_id: str


class EntitySearchResult(BaseModel):
    """Entity search result."""

    id: str
    name: str
    type: str
    description: str


class EntitySearchResponse(BaseModel):
    """Response for entity search."""

    query: str
    results: list[EntitySearchResult]
    total: int


class EntityConnectionsResponse(BaseModel):
    """Response for entity connections."""

    entity_id: str
    entity_name: str
    connections: list[dict]


@router.get("/stats", response_model=KBStatsResponse)
async def get_kb_stats(
    user: TenantContext = Depends(get_current_user),
):
    """
    Get knowledge base statistics for the current tenant.

    GET /kb/stats
    """
    TenantContext.set(user.tenant_id, user.user_id, user.email)

    try:
        pgvector = get_pgvector_client()
        chunk_count = await pgvector.get_chunk_count()

        return KBStatsResponse(
            document_chunks=chunk_count,
            tenant_id=user.tenant_id,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/entities", response_model=EntitySearchResponse)
async def search_entities(
    query: str,
    entity_type: str = None,
    limit: int = 20,
    user: TenantContext = Depends(get_current_user),
):
    """
    Search entities in the knowledge graph.

    GET /kb/entities?query=...&entity_type=PERSON
    """
    TenantContext.set(user.tenant_id, user.user_id, user.email)

    try:
        graph = get_graph_client()
        entities = await graph.search_entities(
            query_text=query,
            entity_type=entity_type,
            limit=limit,
        )

        results = [
            EntitySearchResult(
                id=e.id,
                name=e.name,
                type=e.type,
                description=e.properties.get("description", ""),
            )
            for e in entities
        ]

        return EntitySearchResponse(
            query=query,
            results=results,
            total=len(results),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Entity search failed: {str(e)}")


@router.get("/entities/{entity_id}/connections", response_model=EntityConnectionsResponse)
async def get_entity_connections(
    entity_id: str,
    user: TenantContext = Depends(get_current_user),
):
    """
    Get connections for an entity.

    GET /kb/entities/{entity_id}/connections
    """
    TenantContext.set(user.tenant_id, user.user_id, user.email)

    try:
        graph = get_graph_client()

        # First search for entity by ID
        entities = await graph.search_entities(entity_id.split(":")[-1], limit=1)
        if not entities:
            raise HTTPException(status_code=404, detail="Entity not found")

        entity = entities[0]
        connections = await graph.get_entity_relationships(
            entity_id=entity.id,
            direction="both",
            limit=50,
        )

        return EntityConnectionsResponse(
            entity_id=entity.id,
            entity_name=entity.name,
            connections=connections,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get connections: {str(e)}")


@router.get("/search")
async def hybrid_kb_search(
    query: str,
    limit: int = 10,
    user: TenantContext = Depends(get_current_user),
):
    """
    Search across documents and knowledge graph.

    GET /kb/search?query=...
    """
    TenantContext.set(user.tenant_id, user.user_id, user.email)

    try:
        results = {
            "query": query,
            "documents": [],
            "entities": [],
        }

        # Document search
        embedding_model = get_embedding_model()
        query_embedding = embedding_model.embed_text(query)
        pgvector = get_pgvector_client(dimension=embedding_model.dimension)

        doc_results = await pgvector.similarity_search(
            query_embedding=query_embedding,
            limit=limit,
        )

        results["documents"] = [
            {
                "id": chunk.id,
                "content": chunk.content[:500],
                "doc_id": chunk.doc_id,
                "metadata": chunk.metadata,
            }
            for chunk in doc_results
        ]

        # Entity search
        graph = get_graph_client()
        entities = await graph.search_entities(query, limit=limit)

        results["entities"] = [
            {
                "id": e.id,
                "name": e.name,
                "type": e.type,
                "description": e.properties.get("description", ""),
            }
            for e in entities
        ]

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
