"""
Local HuggingFace embedding models using sentence-transformers.

Note: Groq only provides LLMs, not embedding models.
Embeddings are generated locally using HuggingFace models.
"""

from functools import lru_cache
from typing import Optional

from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings

from src.llm.model_registry import get_model_registry


class EmbeddingModel:
    """
    Local HuggingFace embedding model wrapper.

    Uses sentence-transformers for fast, local embedding generation.
    """

    def __init__(self, model_id: Optional[str] = None):
        """
        Initialize embedding model.

        Args:
            model_id: Model ID from models.yaml (e.g., 'minilm', 'bge-small')
                     If None, uses default from config.
        """
        registry = get_model_registry()

        # Use provided model or default
        model_id = model_id or registry.default_embedding
        embedding_config = registry.get_embedding(model_id)

        if not embedding_config:
            raise ValueError(f"Unknown embedding model: {model_id}")

        self.config = embedding_config
        self.model = HuggingFaceEmbeddings(
            model_name=embedding_config.model_id,
            model_kwargs={"device": "cpu"},  # Use GPU if available: "cuda"
            encode_kwargs={"normalize_embeddings": True},
        )

    @property
    def dimension(self) -> int:
        """Get embedding dimension from config."""
        return self.config.dimension

    def get_embeddings(self) -> Embeddings:
        """Get the underlying LangChain Embeddings object."""
        return self.model

    def embed_text(self, text: str) -> list[float]:
        """
        Embed a single text string.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        return self.model.embed_query(text)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Embed multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        return self.model.embed_documents(texts)


@lru_cache(maxsize=4)
def get_embedding_model(model_id: Optional[str] = None) -> EmbeddingModel:
    """
    Get a cached embedding model instance.

    Args:
        model_id: Optional model ID (uses default if None)

    Returns:
        EmbeddingModel instance
    """
    return EmbeddingModel(model_id)


def get_embeddings(model_id: Optional[str] = None) -> Embeddings:
    """
    Factory function to get LangChain Embeddings object.

    Args:
        model_id: Optional model ID

    Returns:
        LangChain Embeddings interface
    """
    return get_embedding_model(model_id).get_embeddings()
