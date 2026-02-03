"""
Document loaders using LangChain for various file formats.
"""

import os
import tempfile
from pathlib import Path
from typing import Optional

from langchain_community.document_loaders import (
    CSVLoader,
    JSONLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredHTMLLoader,
    UnstructuredMarkdownLoader,
)
from langchain_core.documents import Document


class DocumentLoaderFactory:
    """
    Factory for creating document loaders based on file type.

    Supports: PDF, TXT, MD, HTML, CSV, JSON
    """

    SUPPORTED_EXTENSIONS = {
        ".pdf": "pdf",
        ".txt": "text",
        ".md": "markdown",
        ".html": "html",
        ".htm": "html",
        ".csv": "csv",
        ".json": "json",
    }

    @classmethod
    def get_loader(
        cls,
        file_path: str,
        file_type: Optional[str] = None,
    ):
        """
        Get appropriate loader for file.

        Args:
            file_path: Path to the file
            file_type: Optional explicit file type

        Returns:
            LangChain document loader

        Raises:
            ValueError: If file type is not supported
        """
        if file_type is None:
            ext = Path(file_path).suffix.lower()
            file_type = cls.SUPPORTED_EXTENSIONS.get(ext)

        if file_type is None:
            raise ValueError(
                f"Unsupported file type. Supported: {list(cls.SUPPORTED_EXTENSIONS.keys())}"
            )

        if file_type == "pdf":
            return PyPDFLoader(file_path)
        elif file_type == "text":
            return TextLoader(file_path, encoding="utf-8")
        elif file_type == "markdown":
            return UnstructuredMarkdownLoader(file_path)
        elif file_type == "html":
            return UnstructuredHTMLLoader(file_path)
        elif file_type == "csv":
            return CSVLoader(file_path)
        elif file_type == "json":
            return JSONLoader(file_path, jq_schema=".", text_content=False)
        else:
            raise ValueError(f"Unknown file type: {file_type}")

    @classmethod
    def load_from_bytes(
        cls,
        content: bytes,
        filename: str,
        file_type: Optional[str] = None,
    ) -> list[Document]:
        """
        Load documents from bytes content.

        Args:
            content: File content as bytes
            filename: Original filename (for type detection)
            file_type: Optional explicit file type

        Returns:
            List of LangChain Document objects
        """

        if file_type is None:
            ext = Path(filename).suffix.lower()
            file_type = cls.SUPPORTED_EXTENSIONS.get(ext)

        if file_type is None:
            raise ValueError(
                f"Unsupported file type for {filename}. "
                f"Supported: {list(cls.SUPPORTED_EXTENSIONS.keys())}"
            )

        # Write to temp file for loaders that need file path
        suffix = Path(filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            loader = cls.get_loader(tmp_path, file_type)
            documents = loader.load()

            # Add original filename to metadata
            for doc in documents:
                doc.metadata["source"] = filename

            return documents
        finally:
            os.unlink(tmp_path)

    @classmethod
    def is_supported(cls, filename: str) -> bool:
        """Check if file type is supported."""
        ext = Path(filename).suffix.lower()
        return ext in cls.SUPPORTED_EXTENSIONS


def load_documents(file_path: str) -> list[Document]:
    """
    Load documents from a file.

    Args:
        file_path: Path to the file

    Returns:
        List of LangChain Document objects
    """
    loader = DocumentLoaderFactory.get_loader(file_path)
    return loader.load()


def load_documents_from_bytes(
    content: bytes,
    filename: str,
) -> list[Document]:
    """
    Load documents from bytes content.

    Args:
        content: File content as bytes
        filename: Original filename

    Returns:
        List of LangChain Document objects
    """
    return DocumentLoaderFactory.load_from_bytes(content, filename)
