"""
Cleanup Module for AI Learning Platform

Provides functionality to clean up stale processing records and orphan files
from both the database and MinIO storage.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Set, Tuple

from sqlalchemy.orm import Session
from minio.error import S3Error

from app.database import SessionLocal
from app.core.storage import minio_client
from app.crud.material import cleanup_stale_processing_materials
from app.models.material import Material

# Configure logger
logger = logging.getLogger(__name__)

# Constants
STALE_PROCESSING_MINUTES = 30  # Processing records older than this are considered stale
BATCH_SIZE = 100  # Number of files to process in one batch for MinIO operations


class CleanupResult:
    """Result of a cleanup operation."""

    def __init__(self):
        self.cleaned_records: int = 0
        self.cleaned_files: int = 0
        self.errors: List[str] = []
        self.start_time: datetime = datetime.utcnow()
        self.end_time: datetime | None = None
        self.duration_seconds: float = 0.0

    def finish(self):
        """Mark the cleanup as finished and calculate duration."""
        self.end_time = datetime.utcnow()
        self.duration_seconds = (self.end_time - self.start_time).total_seconds()

    def to_dict(self) -> dict:
        """Convert result to dictionary for API responses."""
        return {
            "cleaned_records": self.cleaned_records,
            "cleaned_files": self.cleaned_files,
            "errors": self.errors,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": round(self.duration_seconds, 2)
        }


def get_all_material_file_paths(db: Session) -> Set[str]:
    """
    Get all file paths and thumbnail paths from the materials table.

    Args:
        db: Database session

    Returns:
        Set of file paths that are referenced in the database
    """
    materials = db.query(Material.file_path, Material.thumbnail_path).all()
    paths = set()

    for file_path, thumbnail_path in materials:
        if file_path:
            paths.add(file_path)
        if thumbnail_path:
            paths.add(thumbnail_path)

    return paths


def list_all_minio_objects() -> List[str]:
    """
    List all objects in the MinIO bucket.

    Returns:
        List of object names in the bucket
    """
    objects = []
    try:
        for obj in minio_client.client.list_objects(minio_client.bucket_name, recursive=True):
            objects.append(obj.object_name)
    except S3Error as e:
        logger.error(f"Failed to list MinIO objects: {e}")
        raise

    return objects


def delete_minio_files(object_names: List[str]) -> Tuple[int, List[str]]:
    """
    Delete multiple files from MinIO.

    Args:
        object_names: List of object names to delete

    Returns:
        Tuple of (deleted_count, errors)
    """
    deleted_count = 0
    errors = []

    # Process in batches to avoid overwhelming MinIO
    for i in range(0, len(object_names), BATCH_SIZE):
        batch = object_names[i:i + BATCH_SIZE]

        for object_name in batch:
            try:
                minio_client.delete_file(object_name)
                deleted_count += 1
                logger.debug(f"Deleted MinIO object: {object_name}")
            except S3Error as e:
                error_msg = f"Failed to delete {object_name}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
            except Exception as e:
                error_msg = f"Unexpected error deleting {object_name}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

    return deleted_count, errors


def cleanup_stale_processing_records(db: Session, max_age_minutes: int = STALE_PROCESSING_MINUTES) -> Tuple[int, int, List[str]]:
    """
    Clean up processing records that have been stuck for too long.

    This function:
    1. Finds materials with status='processing' and created_at < cutoff_time
    2. Deletes associated files from MinIO
    3. Deletes the database records

    Args:
        db: Database session
        max_age_minutes: Maximum age in minutes before considering stale

    Returns:
        Tuple of (deleted_records_count, deleted_files_count, errors)
    """
    errors = []
    deleted_files_count = 0

    # Calculate cutoff time
    cutoff_time = datetime.utcnow() - timedelta(minutes=max_age_minutes)
    logger.info(f"Looking for processing records older than {cutoff_time.isoformat()}")

    # Find stale processing materials
    stale_materials = db.query(Material).filter(
        Material.status == "processing",
        Material.created_at < cutoff_time
    ).all()

    if not stale_materials:
        logger.info("No stale processing records found")
        return 0, 0, []

    logger.info(f"Found {len(stale_materials)} stale processing records")

    # Collect files to delete from MinIO
    files_to_delete = []
    for material in stale_materials:
        if material.file_path:
            files_to_delete.append(material.file_path)
        if material.thumbnail_path:
            files_to_delete.append(material.thumbnail_path)

    # Delete files from MinIO
    if files_to_delete:
        logger.info(f"Deleting {len(files_to_delete)} files from MinIO")
        deleted_files_count, file_errors = delete_minio_files(files_to_delete)
        errors.extend(file_errors)

    # Delete database records
    deleted_records_count = len(stale_materials)
    for material in stale_materials:
        db.delete(material)

    db.commit()
    logger.info(f"Deleted {deleted_records_count} stale processing records")

    return deleted_records_count, deleted_files_count, errors


def cleanup_orphan_files(db: Session) -> Tuple[int, List[str]]:
    """
    Clean up orphan files in MinIO that are not referenced by any database record.

    This function:
    1. Lists all objects in MinIO bucket
    2. Gets all file paths from the database
    3. Deletes files that are not referenced

    Args:
        db: Database session

    Returns:
        Tuple of (deleted_files_count, errors)
    """
    errors = []

    logger.info("Starting orphan file cleanup")

    # Get all referenced file paths from database
    referenced_paths = get_all_material_file_paths(db)
    logger.info(f"Found {len(referenced_paths)} referenced file paths in database")

    # List all objects in MinIO
    try:
        all_objects = list_all_minio_objects()
    except Exception as e:
        error_msg = f"Failed to list MinIO objects: {e}"
        logger.error(error_msg)
        return 0, [error_msg]

    logger.info(f"Found {len(all_objects)} objects in MinIO bucket")

    # Find orphan files (files in MinIO but not in database)
    # Skip placeholder thumbnail and system files
    orphan_files = []
    for obj_name in all_objects:
        # Skip system files and placeholder
        if obj_name.startswith("system/") or obj_name == "placeholders/thumbnail.jpg":
            continue
        if obj_name not in referenced_paths:
            orphan_files.append(obj_name)

    if not orphan_files:
        logger.info("No orphan files found")
        return 0, []

    logger.info(f"Found {len(orphan_files)} orphan files to delete")

    # Delete orphan files
    deleted_count, delete_errors = delete_minio_files(orphan_files)
    errors.extend(delete_errors)

    logger.info(f"Deleted {deleted_count} orphan files")

    return deleted_count, errors


def run_cleanup(
    cleanup_processing: bool = True,
    cleanup_orphans: bool = True,
    max_age_minutes: int = STALE_PROCESSING_MINUTES
) -> CleanupResult:
    """
    Run the full cleanup process.

    Args:
        cleanup_processing: Whether to clean up stale processing records
        cleanup_orphans: Whether to clean up orphan files
        max_age_minutes: Maximum age for processing records

    Returns:
        CleanupResult with details of the cleanup operation
    """
    result = CleanupResult()
    db = SessionLocal()

    try:
        logger.info("=" * 60)
        logger.info("Starting cleanup task")
        logger.info("=" * 60)

        # Clean up stale processing records
        if cleanup_processing:
            logger.info("Step 1: Cleaning up stale processing records")
            try:
                records_count, files_count, errors = cleanup_stale_processing_records(
                    db, max_age_minutes
                )
                result.cleaned_records += records_count
                result.cleaned_files += files_count
                result.errors.extend(errors)
                logger.info(f"Cleaned {records_count} stale records and {files_count} files")
            except Exception as e:
                error_msg = f"Error cleaning up processing records: {e}"
                logger.error(error_msg)
                result.errors.append(error_msg)

        # Clean up orphan files
        if cleanup_orphans:
            logger.info("Step 2: Cleaning up orphan files")
            try:
                files_count, errors = cleanup_orphan_files(db)
                result.cleaned_files += files_count
                result.errors.extend(errors)
                logger.info(f"Cleaned {files_count} orphan files")
            except Exception as e:
                error_msg = f"Error cleaning up orphan files: {e}"
                logger.error(error_msg)
                result.errors.append(error_msg)

        logger.info("=" * 60)
        logger.info("Cleanup task completed")
        logger.info("=" * 60)

    except Exception as e:
        error_msg = f"Unexpected error during cleanup: {e}"
        logger.error(error_msg)
        result.errors.append(error_msg)
    finally:
        db.close()
        result.finish()

    return result


def run_cleanup_manual(
    cleanup_processing: bool = True,
    cleanup_orphans: bool = True,
    max_age_minutes: int = STALE_PROCESSING_MINUTES
) -> dict:
    """
    Run cleanup manually and return result as dictionary.

    This is a convenience function for the admin API endpoint.

    Args:
        cleanup_processing: Whether to clean up stale processing records
        cleanup_orphans: Whether to clean up orphan files
        max_age_minutes: Maximum age for processing records

    Returns:
        Dictionary with cleanup results
    """
    result = run_cleanup(cleanup_processing, cleanup_orphans, max_age_minutes)
    return result.to_dict()
