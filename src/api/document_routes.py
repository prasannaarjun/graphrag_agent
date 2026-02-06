"""
Document management API routes.
"""

import logging
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from src.auth.dependencies import get_current_user
from src.core.tenant import TenantContext
from src.indexing import DocumentLoaderFactory, get_document_processor, load_documents_from_bytes
from src.knowledge_graph import get_entity_extractor, get_graph_client
from src.llm import get_embedding_model
from src.object_store import get_minio_client
from src.vector_store import DocumentChunk, get_pgvector_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


class DocumentResponse(BaseModel):
    """Response model for document operations."""

    id: str
    filename: str
    size: int
    chunks: int
    status: str


class DocumentListItem(BaseModel):
    """Item in document list response."""

    id: str
    filename: str
    size: int
    uploaded_at: str


class DocumentListResponse(BaseModel):
    """Response model for document listing."""

    documents: list[DocumentListItem]
    total: int


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    user: TenantContext = Depends(get_current_user),
):
    """
    Upload and index a document.

    POST /documents/upload

    Supports: PDF, TXT, MD, HTML, CSV, JSON
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    if not DocumentLoaderFactory.is_supported(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported: {list(DocumentLoaderFactory.SUPPORTED_EXTENSIONS.keys())}",
        )

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Generate document ID
    doc_id = str(uuid.uuid4())

    # Set tenant context for downstream operations
    TenantContext.set(user.tenant_id, user.user_id, user.email)

    try:
        # 1. Upload file to MinIO
        minio = get_minio_client()
        object_name = f"{doc_id}/{file.filename}"
        await minio.upload_file(
            file_data=content,
            object_name=object_name,
            content_type=file.content_type or "application/octet-stream",
            metadata={"original_filename": file.filename},
        )

        # 2. Load and process document
        documents = load_documents_from_bytes(content, file.filename)
        processor = get_document_processor()
        chunks = processor.process_documents(documents)

        # 3. Generate embeddings
        embedding_model = get_embedding_model()
        chunk_texts = [chunk.content for chunk in chunks]
        embeddings = embedding_model.embed_texts(chunk_texts)

        # 4. Store in pgvector
        pgvector = get_pgvector_client(dimension=embedding_model.dimension)

        db_chunks = [
            DocumentChunk(
                id=str(uuid.uuid4()),
                tenant_id=user.tenant_id,
                doc_id=doc_id,
                content=chunk.content,
                embedding=embeddings[idx],
                chunk_index=str(chunk.chunk_index),
                metadata={
                    **chunk.metadata,
                    "filename": file.filename,
                },
            )
            for idx, chunk in enumerate(chunks)
        ]

        await pgvector.insert_chunks_batch(db_chunks)

        # 5. Extract entities and build knowledge graph
        doc_id_short = doc_id[:8]
        logger.info(f"KB_EXTRACT_START | doc={doc_id_short} | chunks={len(chunks)}")

        graph = get_graph_client()
        extractor = get_entity_extractor()

        entities_extracted = 0
        for idx, chunk in enumerate(chunks):
            try:
                result = await extractor.extract_and_store(
                    text=chunk.content,
                    doc_id=doc_id,
                    graph_client=graph,
                )
                entities_extracted += len(result.entities)
                logger.info(
                    f"KB_CHUNK_EXTRACT | doc={doc_id_short} | chunk={idx + 1}/{len(chunks)} | entities={len(result.entities)} | relations={len(result.relationships)}"
                )
            except Exception as extraction_error:
                # Log but don't fail the upload if extraction fails
                logger.error(
                    f"KB_CHUNK_ERROR | doc={doc_id_short} | chunk={idx + 1} | {str(extraction_error)}"
                )

        logger.info(f"KB_EXTRACT_COMPLETE | doc={doc_id_short} | total_entities={entities_extracted}")

        return DocumentResponse(
            id=doc_id,
            filename=file.filename,
            size=file_size,
            chunks=len(chunks),
            status=f"indexed (extracted {entities_extracted} entities)",
        )

    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    user: TenantContext = Depends(get_current_user),
):
    """
    List all documents for the current tenant.

    GET /documents
    """
    TenantContext.set(user.tenant_id, user.user_id, user.email)

    try:
        # List files from MinIO
        minio = get_minio_client()
        files = await minio.list_files()

        # Group by document ID (first path segment)
        docs: dict[str, DocumentListItem] = {}
        for file_info in files:
            parts = file_info["name"].split("/")
            if len(parts) >= 2:
                doc_id = parts[0]
                filename = parts[1]

                if doc_id not in docs:
                    docs[doc_id] = DocumentListItem(
                        id=doc_id,
                        filename=filename,
                        size=file_info["size"],
                        uploaded_at=str(file_info["last_modified"]),
                    )

        doc_list = list(docs.values())

        return DocumentListResponse(
            documents=doc_list,
            total=len(doc_list),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    user: TenantContext = Depends(get_current_user),
):
    """
    Delete a document and its chunks.

    DELETE /documents/{doc_id}
    """
    TenantContext.set(user.tenant_id, user.user_id, user.email)

    try:
        # Delete from pgvector
        pgvector = get_pgvector_client()
        deleted_chunks = await pgvector.delete_by_doc_id(doc_id)

        # Delete from MinIO
        minio = get_minio_client()
        files = await minio.list_files(prefix=f"{doc_id}/")

        for file_info in files:
            await minio.delete_file(file_info["name"])

        return {
            "id": doc_id,
            "chunks_deleted": deleted_chunks,
            "status": "deleted",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@router.get("/{doc_id}/search")
async def search_document(
    doc_id: str,
    query: str,
    limit: int = 5,
    user: TenantContext = Depends(get_current_user),
):
    """
    Search within a specific document.

    GET /documents/{doc_id}/search?query=...
    """
    TenantContext.set(user.tenant_id, user.user_id, user.email)

    try:
        # Generate query embedding
        embedding_model = get_embedding_model()
        query_embedding = embedding_model.embed_text(query)

        # Search in pgvector
        pgvector = get_pgvector_client(dimension=embedding_model.dimension)
        results = await pgvector.similarity_search(
            query_embedding=query_embedding,
            limit=limit,
            doc_id=doc_id,
        )

        return {
            "query": query,
            "doc_id": doc_id,
            "results": [
                {
                    "id": chunk.id,
                    "content": chunk.content,
                    "chunk_index": chunk.chunk_index,
                    "metadata": chunk.metadata,
                }
                for chunk in results
            ],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
