"""
MinIO Storage Client Module

Provides MinIO client initialization, bucket management, and file operations
including streaming upload, download URL generation, and file deletion.
"""

import io
from datetime import timedelta
from typing import BinaryIO, Optional
from urllib.parse import urljoin

from minio import Minio
from minio.error import S3Error

from app.config import settings


class MinIOClient:
    """
    MinIO client wrapper for file storage operations.

    Handles connection management, bucket operations, and file I/O with MinIO.
    """

    def __init__(self):
        """Initialize MinIO client with settings from configuration."""
        self.client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure
        )
        self.bucket_name = settings.minio_bucket_name

    def ensure_bucket_exists(self) -> None:
        """
        Ensure the materials bucket exists, creating it if necessary.

        This should be called during application startup.
        """
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                # Set bucket policy for public read access (adjust as needed)
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"AWS": ["*"]},
                            "Action": ["s3:GetObject"],
                            "Resource": [f"arn:aws:s3:::{self.bucket_name}/*"]
                        }
                    ]
                }
                import json
                self.client.set_bucket_policy(self.bucket_name, json.dumps(policy))
        except S3Error as e:
            raise RuntimeError(f"Failed to create bucket: {e}") from e

    def upload_file_stream(
        self,
        file_stream: BinaryIO,
        object_name: str,
        content_type: str,
        file_size: int
    ) -> str:
        """
        Upload a file to MinIO using streaming.

        Args:
            file_stream: Binary file stream to upload
            object_name: Target object name/path in MinIO
            content_type: MIME type of the file
            file_size: Size of the file in bytes

        Returns:
            str: The object name (path) in MinIO

        Raises:
            RuntimeError: If upload fails
        """
        try:
            # Use put_object for streaming upload
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=file_stream,
                length=file_size,
                content_type=content_type
            )
            return object_name
        except S3Error as e:
            raise RuntimeError(f"Failed to upload file to MinIO: {e}") from e

    def upload_file_bytes(
        self,
        data: bytes,
        object_name: str,
        content_type: str
    ) -> str:
        """
        Upload bytes data to MinIO.

        Args:
            data: Bytes data to upload
            object_name: Target object name/path in MinIO
            content_type: MIME type of the file

        Returns:
            str: The object name (path) in MinIO

        Raises:
            RuntimeError: If upload fails
        """
        try:
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=io.BytesIO(data),
                length=len(data),
                content_type=content_type
            )
            return object_name
        except S3Error as e:
            raise RuntimeError(f"Failed to upload file to MinIO: {e}") from e

    def get_presigned_url(
        self,
        object_name: str,
        expires: timedelta = timedelta(hours=24)
    ) -> str:
        """
        Generate a presigned URL for accessing a file.

        Args:
            object_name: Object name/path in MinIO
            expires: Expiration time for the URL

        Returns:
            str: Presigned URL for file access

        Raises:
            RuntimeError: If URL generation fails
        """
        try:
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=expires
            )
            return url
        except S3Error as e:
            raise RuntimeError(f"Failed to generate presigned URL: {e}") from e

    def get_file_url(self, object_name: str) -> str:
        """
        Get the direct URL for a file (for public access).

        Args:
            object_name: Object name/path in MinIO

        Returns:
            str: Direct URL to the file
        """
        # Construct the URL based on MinIO endpoint configuration
        protocol = "https" if settings.minio_secure else "http"
        base_url = f"{protocol}://{settings.minio_endpoint}"
        return f"{base_url}/{self.bucket_name}/{object_name}"

    def delete_file(self, object_name: str) -> None:
        """
        Delete a file from MinIO.

        Args:
            object_name: Object name/path in MinIO to delete

        Raises:
            RuntimeError: If deletion fails
        """
        try:
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
        except S3Error as e:
            raise RuntimeError(f"Failed to delete file from MinIO: {e}") from e

    def file_exists(self, object_name: str) -> bool:
        """
        Check if a file exists in MinIO.

        Args:
            object_name: Object name/path to check

        Returns:
            bool: True if file exists, False otherwise
        """
        try:
            self.client.stat_object(self.bucket_name, object_name)
            return True
        except S3Error:
            return False


# Global MinIO client instance
minio_client = MinIOClient()


def get_minio_client() -> MinIOClient:
    """
    Get the global MinIO client instance.

    Returns:
        MinIOClient: The configured MinIO client
    """
    return minio_client
