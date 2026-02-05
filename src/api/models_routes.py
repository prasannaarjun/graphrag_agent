"""
Models API routes for listing available LLM and embedding models.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from src.llm import get_model_registry

router = APIRouter(prefix="/models", tags=["Models"])


class ModelInfo(BaseModel):
    """Model information."""

    id: str
    name: str
    model_id: str
    context_window: int
    description: str
    provider: str
    recommended: bool


class EmbeddingInfo(BaseModel):
    """Embedding model information."""

    id: str
    name: str
    model_id: str
    dimension: int
    description: str
    recommended: bool


class ModelsResponse(BaseModel):
    """Response for listing models."""

    default_model: str
    default_embedding: str
    models: list[ModelInfo]
    embeddings: list[EmbeddingInfo]


@router.get("", response_model=ModelsResponse)
async def list_models():
    """
    List all available LLM and embedding models.

    GET /models
    """
    registry = get_model_registry()

    models = [
        ModelInfo(
            id=m.id,
            name=m.name,
            model_id=m.model_id,
            context_window=m.context_window,
            description=m.description,
            provider=m.provider,
            recommended=m.recommended,
        )
        for m in registry.list_models()
    ]

    embeddings = [
        EmbeddingInfo(
            id=e.id,
            name=e.name,
            model_id=e.model_id,
            dimension=e.dimension,
            description=e.description,
            recommended=e.recommended,
        )
        for e in registry.list_embeddings()
    ]

    return ModelsResponse(
        default_model=registry.default_model,
        default_embedding=registry.default_embedding,
        models=models,
        embeddings=embeddings,
    )


@router.get("/llm")
async def list_llm_models():
    """
    List LLM models only.

    GET /models/llm
    """
    registry = get_model_registry()

    return {
        "default": registry.default_model,
        "models": [
            {
                "id": m.id,
                "name": m.name,
                "provider": m.provider,
                "context_window": m.context_window,
            }
            for m in registry.list_models()
        ],
    }


@router.get("/embeddings")
async def list_embedding_models():
    """
    List embedding models only.

    GET /models/embeddings
    """
    registry = get_model_registry()

    return {
        "default": registry.default_embedding,
        "models": [
            {
                "id": e.id,
                "name": e.name,
                "dimension": e.dimension,
            }
            for e in registry.list_embeddings()
        ],
    }
