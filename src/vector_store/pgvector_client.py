"""
PostgreSQL + pgvector client for vector storage with tenant isolation via RLS.
"""

import json
import uuid
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import text

from src.core.tenant import TenantContext
from src.db.session import get_db_session


@dataclass
class DocumentChunk:
    """A chunk of a document with embedding."""

    id: str
    tenant_id: str
    doc_id: str
    content: str
    embedding: Optional[list[float]] = None
    chunk_index: Optional[str] = None
    metadata: Optional[dict] = None


class PgVectorClient:
    """
    PostgreSQL + pgvector client for tenant-isolated vector storage.

    Uses Row-Level Security (RLS) for automatic tenant isolation.
    """

    def __init__(self, dimension: int = 384):
        """
        Initialize pgvector client.

        Args:
            dimension: Embedding dimension (must match model output)
        """
        self.dimension = dimension

    def _get_tenant_id(self) -> str:
        """Get current tenant ID from context."""
        return TenantContext.get_current().tenant_id

    async def insert_chunk(
        self,
        doc_id: str,
        content: str,
        embedding: list[float],
        chunk_index: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Insert a document chunk with embedding.

        Args:
            doc_id: Parent document ID
            content: Chunk text content
            embedding: Embedding vector
            chunk_index: Optional chunk index/position
            metadata: Optional metadata dict

        Returns:
            Chunk ID
        """
        chunk_id = str(uuid.uuid4())
        tenant_id = self._get_tenant_id()

        async with get_db_session() as session:
            # Set tenant context for RLS
            # Note: SET doesn't support bind parameters in PostgreSQL
            await session.execute(text(f"SET app.current_tenant_id = '{tenant_id}'"))

            query = text("""
                INSERT INTO document_chunks
                (id, tenant_id, doc_id, content, embedding, chunk_index, metadata)
                VALUES
                (:id, :tenant_id, :doc_id, :content, CAST(:embedding AS vector), :chunk_index, :metadata)
            """)

            await session.execute(
                query,
                {
                    "id": chunk_id,
                    "tenant_id": tenant_id,
                    "doc_id": doc_id,
                    "content": content,
                    "embedding": f"[{','.join(map(str, embedding))}]",
                    "chunk_index": chunk_index,
                    "metadata": json.dumps(metadata) if metadata else None,
                },
            )

        return chunk_id

    async def insert_chunks_batch(
        self,
        chunks: list[DocumentChunk],
    ) -> list[str]:
        """
        Insert multiple chunks in a batch.

        Args:
            chunks: List of DocumentChunk objects

        Returns:
            List of chunk IDs
        """
        tenant_id = self._get_tenant_id()
        chunk_ids = []

        async with get_db_session() as session:
            await session.execute(text(f"SET app.current_tenant_id = '{tenant_id}'"))

            for chunk in chunks:
                chunk_id = chunk.id or str(uuid.uuid4())
                chunk_ids.append(chunk_id)

                query = text("""
                    INSERT INTO document_chunks
                    (id, tenant_id, doc_id, content, embedding, chunk_index, metadata)
                    VALUES
                    (:id, :tenant_id, :doc_id, :content, CAST(:embedding AS vector), :chunk_index, :metadata)
                """)

                await session.execute(
                    query,
                    {
                        "id": chunk_id,
                        "tenant_id": tenant_id,
                        "doc_id": chunk.doc_id,
                        "content": chunk.content,
                        "embedding": f"[{','.join(map(str, chunk.embedding))}]"
                        if chunk.embedding
                        else None,
                        "chunk_index": chunk.chunk_index,
                        "metadata": json.dumps(chunk.metadata) if chunk.metadata else None,
                    },
                )

        return chunk_ids

    async def similarity_search(
        self,
        query_embedding: list[float],
        limit: int = 5,
        doc_id: Optional[str] = None,
    ) -> list[DocumentChunk]:
        """
        Search for similar chunks using cosine similarity.

        Args:
            query_embedding: Query embedding vector
            limit: Maximum number of results
            doc_id: Optional filter by document ID

        Returns:
            List of similar DocumentChunks ordered by similarity
        """
        tenant_id = self._get_tenant_id()

        async with get_db_session() as session:
            await session.execute(text(f"SET app.current_tenant_id = '{tenant_id}'"))

            # Build query with optional doc_id filter
            base_query = """
                SELECT id, tenant_id, doc_id, content, chunk_index, metadata,
                       1 - (embedding <=> CAST(:embedding AS vector)) as similarity
                FROM document_chunks
                WHERE tenant_id = :tenant_id
            """

            if doc_id:
                base_query += " AND doc_id = :doc_id"

            base_query += " ORDER BY embedding <=> CAST(:embedding AS vector) LIMIT :limit"

            params = {
                "embedding": f"[{','.join(map(str, query_embedding))}]",
                "tenant_id": tenant_id,
                "limit": limit,
            }

            if doc_id:
                params["doc_id"] = doc_id

            result = await session.execute(text(base_query), params)
            rows = result.fetchall()

        return [
            DocumentChunk(
                id=row.id,
                tenant_id=row.tenant_id,
                doc_id=row.doc_id,
                content=row.content,
                chunk_index=row.chunk_index,
                metadata=json.loads(row.metadata) if row.metadata else None,
            )
            for row in rows
        ]

    async def delete_by_doc_id(self, doc_id: str) -> int:
        """
        Delete all chunks for a document.

        Args:
            doc_id: Document ID

        Returns:
            Number of deleted chunks
        """
        tenant_id = self._get_tenant_id()

        async with get_db_session() as session:
            await session.execute(text(f"SET app.current_tenant_id = '{tenant_id}'"))

            result = await session.execute(
                text(
                    "DELETE FROM document_chunks WHERE doc_id = :doc_id AND tenant_id = :tenant_id"
                ),
                {"doc_id": doc_id, "tenant_id": tenant_id},
            )

            return result.rowcount

    async def get_chunk_count(self, doc_id: Optional[str] = None) -> int:
        """
        Get count of chunks for tenant.

        Args:
            doc_id: Optional filter by document ID

        Returns:
            Number of chunks
        """
        tenant_id = self._get_tenant_id()

        async with get_db_session() as session:
            await session.execute(text(f"SET app.current_tenant_id = '{tenant_id}'"))

            if doc_id:
                result = await session.execute(
                    text(
                        "SELECT COUNT(*) FROM document_chunks WHERE tenant_id = :tenant_id AND doc_id = :doc_id"
                    ),
                    {"tenant_id": tenant_id, "doc_id": doc_id},
                )
            else:
                result = await session.execute(
                    text("SELECT COUNT(*) FROM document_chunks WHERE tenant_id = :tenant_id"),
                    {"tenant_id": tenant_id},
                )

            return result.scalar() or 0


def get_pgvector_client(dimension: int = 384) -> PgVectorClient:
    """Get pgvector client with specified dimension."""
    return PgVectorClient(dimension=dimension)
