"""
Document processing and chunking pipeline.
"""

from dataclasses import dataclass
from typing import Optional

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


@dataclass
class ProcessedChunk:
    """A processed document chunk ready for embedding."""

    content: str
    chunk_index: int
    metadata: dict


class DocumentProcessor:
    """
    Document processor for chunking text.

    Uses LangChain's RecursiveCharacterTextSplitter for intelligent chunking.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[list[str]] = None,
    ):
        """
        Initialize document processor.

        Args:
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks
            separators: Custom separators for splitting
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators or ["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )

    def process_documents(
        self,
        documents: list[Document],
    ) -> list[ProcessedChunk]:
        """
        Process documents into chunks.

        Args:
            documents: List of LangChain Document objects

        Returns:
            List of ProcessedChunk objects
        """
        chunks = []

        # Split all documents
        split_docs = self.splitter.split_documents(documents)

        for idx, doc in enumerate(split_docs):
            chunks.append(
                ProcessedChunk(
                    content=doc.page_content,
                    chunk_index=idx,
                    metadata=doc.metadata,
                )
            )

        return chunks

    def process_text(
        self,
        text: str,
        metadata: Optional[dict] = None,
    ) -> list[ProcessedChunk]:
        """
        Process raw text into chunks.

        Args:
            text: Raw text content
            metadata: Optional metadata to attach

        Returns:
            List of ProcessedChunk objects
        """
        # Split text
        texts = self.splitter.split_text(text)

        return [
            ProcessedChunk(
                content=chunk_text,
                chunk_index=idx,
                metadata=metadata or {},
            )
            for idx, chunk_text in enumerate(texts)
        ]


def get_document_processor(
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> DocumentProcessor:
    """
    Get a document processor instance.

    Args:
        chunk_size: Target chunk size
        chunk_overlap: Overlap between chunks

    Returns:
        DocumentProcessor instance
    """
    return DocumentProcessor(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
