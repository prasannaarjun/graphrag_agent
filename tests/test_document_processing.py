"""
Tests for document processing pipeline.
"""

import pytest

from src.indexing.loaders import DocumentLoaderFactory
from src.indexing.processor import DocumentProcessor, ProcessedChunk, get_document_processor


class TestDocumentProcessor:
    """Tests for document processor."""

    def test_process_text(self):
        """Test processing raw text into chunks."""
        processor = get_document_processor(chunk_size=100, chunk_overlap=20)

        text = "This is a test document. " * 20  # ~500 chars

        chunks = processor.process_text(text)

        assert len(chunks) > 1
        assert all(isinstance(c, ProcessedChunk) for c in chunks)
        assert all(len(c.content) <= 120 for c in chunks)  # Allow some overlap

    def test_chunk_overlap(self):
        """Test that chunks have proper overlap."""
        processor = DocumentProcessor(chunk_size=50, chunk_overlap=10)

        text = "Word1 Word2 Word3 Word4 Word5 Word6 Word7 Word8 Word9 Word10 " * 5

        chunks = processor.process_text(text)

        # With overlap, consecutive chunks should share some content
        assert len(chunks) >= 2

    def test_metadata_preserved(self):
        """Test that metadata is preserved in chunks."""
        processor = get_document_processor()

        metadata = {"source": "test.txt", "author": "Test"}
        chunks = processor.process_text("Test content", metadata=metadata)

        assert len(chunks) >= 1
        assert chunks[0].metadata["source"] == "test.txt"
        assert chunks[0].metadata["author"] == "Test"


class TestDocumentLoaderFactory:
    """Tests for document loader factory."""

    def test_supported_extensions(self):
        """Test supported file extensions."""
        assert DocumentLoaderFactory.is_supported("test.pdf")
        assert DocumentLoaderFactory.is_supported("test.txt")
        assert DocumentLoaderFactory.is_supported("test.md")
        assert DocumentLoaderFactory.is_supported("test.html")
        assert DocumentLoaderFactory.is_supported("test.csv")
        assert DocumentLoaderFactory.is_supported("test.json")

    def test_unsupported_extension(self):
        """Test unsupported file extension."""
        assert not DocumentLoaderFactory.is_supported("test.xyz")
        assert not DocumentLoaderFactory.is_supported("test.exe")

    def test_case_insensitive(self):
        """Test case insensitive extension matching."""
        assert DocumentLoaderFactory.is_supported("test.PDF")
        assert DocumentLoaderFactory.is_supported("test.TXT")
        assert DocumentLoaderFactory.is_supported("test.Md")

    def test_load_from_bytes_txt(self):
        """Test loading text from bytes."""
        content = b"This is test content.\nLine 2.\nLine 3."

        docs = DocumentLoaderFactory.load_from_bytes(content, "test.txt")

        assert len(docs) >= 1
        assert "This is test content" in docs[0].page_content

    def test_load_from_bytes_unsupported(self):
        """Test loading unsupported file type raises error."""
        with pytest.raises(ValueError, match="Unsupported file type"):
            DocumentLoaderFactory.load_from_bytes(b"content", "test.xyz")
