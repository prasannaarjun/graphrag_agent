"""Object storage module."""

from .minio_client import MinioClient, get_minio_client

__all__ = ["MinioClient", "get_minio_client"]
