"""Vector store module."""

from .pgvector_client import DocumentChunk, PgVectorClient, get_pgvector_client

__all__ = ["DocumentChunk", "PgVectorClient", "get_pgvector_client"]
