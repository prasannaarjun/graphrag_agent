"""
MinIO object storage client with tenant-scoped bucket isolation.
"""

from typing import BinaryIO, Optional

from minio import Minio
from minio.error import S3Error

from src.config import get_settings
from src.core.tenant import TenantContext


class MinioClient:
    """
    MinIO client for tenant-isolated object storage.

    Each tenant gets their own bucket: tenant-{tenant_id}-documents
    """

    def __init__(self):
        settings = get_settings()
        self.client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )

    def _get_bucket_name(self) -> str:
        """Get bucket name for current tenant."""
        tenant_id = TenantContext.get_current().tenant_id
        # Sanitize tenant_id for bucket naming rules
        safe_id = tenant_id.lower().replace("_", "-")[:50]
        return f"tenant-{safe_id}-documents"

    async def ensure_bucket_exists(self) -> None:
        """Create tenant bucket if it doesn't exist."""
        bucket_name = self._get_bucket_name()
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
        except S3Error as e:
            if e.code != "BucketAlreadyOwnedByYou":
                raise

    async def upload_file(
        self,
        file_data: BinaryIO,
        object_name: str,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Upload a file to tenant's bucket.

        Args:
            file_data: File-like object to upload
            object_name: Name/path for the object
            content_type: MIME type of the file
            metadata: Optional metadata dict

        Returns:
            The full object path (bucket/object_name)
        """
        await self.ensure_bucket_exists()
        bucket_name = self._get_bucket_name()

        # Get file size
        file_data.seek(0, 2)
        size = file_data.tell()
        file_data.seek(0)

        self.client.put_object(
            bucket_name=bucket_name,
            object_name=object_name,
            data=file_data,
            length=size,
            content_type=content_type,
            metadata=metadata or {},
        )

        return f"{bucket_name}/{object_name}"

    async def download_file(self, object_name: str) -> bytes:
        """
        Download a file from tenant's bucket.

        Args:
            object_name: Name/path of the object

        Returns:
            File contents as bytes
        """
        bucket_name = self._get_bucket_name()

        response = self.client.get_object(bucket_name, object_name)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    async def delete_file(self, object_name: str) -> None:
        """Delete a file from tenant's bucket."""
        bucket_name = self._get_bucket_name()
        self.client.remove_object(bucket_name, object_name)

    async def list_files(self, prefix: str = "") -> list[dict]:
        """
        List files in tenant's bucket.

        Args:
            prefix: Optional prefix to filter objects

        Returns:
            List of object info dicts
        """
        bucket_name = self._get_bucket_name()

        try:
            objects = self.client.list_objects(
                bucket_name,
                prefix=prefix,
                recursive=True,
            )

            return [
                {
                    "name": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified,
                    "content_type": obj.content_type,
                }
                for obj in objects
            ]
        except S3Error as e:
            if e.code == "NoSuchBucket":
                return []
            raise

    async def get_presigned_url(
        self,
        object_name: str,
        expires_hours: int = 1,
    ) -> str:
        """
        Get a presigned URL for direct download.

        Args:
            object_name: Name/path of the object
            expires_hours: URL expiration time in hours

        Returns:
            Presigned download URL
        """
        from datetime import timedelta

        bucket_name = self._get_bucket_name()

        return self.client.presigned_get_object(
            bucket_name,
            object_name,
            expires=timedelta(hours=expires_hours),
        )

    async def file_exists(self, object_name: str) -> bool:
        """Check if a file exists in tenant's bucket."""
        bucket_name = self._get_bucket_name()

        try:
            self.client.stat_object(bucket_name, object_name)
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            raise


# Singleton instance
_minio_client: Optional[MinioClient] = None


def get_minio_client() -> MinioClient:
    """Get or create MinIO client singleton."""
    global _minio_client
    if _minio_client is None:
        _minio_client = MinioClient()
    return _minio_client
