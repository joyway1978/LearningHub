"""
Material CRUD Operations Module

Provides Create, Read, Update, Delete operations for Material model.
Handles material record creation, status updates, and retrieval.
"""

from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import HTTPException, status
from sqlalchemy import desc, asc
from sqlalchemy.orm import Session, joinedload

from app.models.material import Material, MaterialStatus, MaterialType
from app.models.user import User
from app.schemas.material import MaterialCreate, MaterialUpdate


def get_material_by_id(db: Session, material_id: int, include_uploader: bool = False) -> Optional[Material]:
    """
    Get a material by ID.

    Args:
        db: Database session
        material_id: Material ID
        include_uploader: Whether to preload uploader information

    Returns:
        Material if found, None otherwise
    """
    query = db.query(Material)
    if include_uploader:
        query = query.options(joinedload(Material.uploader))
    return query.filter(Material.id == material_id).first()


def get_material_by_id_or_raise(db: Session, material_id: int) -> Material:
    """
    Get a material by ID or raise 404 exception.

    Args:
        db: Database session
        material_id: Material ID

    Returns:
        Material if found

    Raises:
        HTTPException: 404 if material not found
    """
    material = get_material_by_id(db, material_id)
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Material not found",
                    "details": {"material_id": material_id}
                }
            }
        )
    return material


def create_material(
    db: Session,
    title: str,
    description: Optional[str],
    material_type: MaterialType,
    file_path: str,
    file_size: int,
    file_format: str,
    uploader_id: int
) -> Material:
    """
    Create a new material record with processing status.

    Args:
        db: Database session
        title: Material title
        description: Material description
        material_type: Type of material (video/pdf)
        file_path: Path to file in MinIO storage
        file_size: File size in bytes
        file_format: File format extension
        uploader_id: ID of user uploading the material

    Returns:
        Material: The created material record
    """
    db_material = Material(
        title=title,
        description=description,
        type=material_type,
        file_path=file_path,
        file_size=file_size,
        file_format=file_format,
        uploader_id=uploader_id,
        status=MaterialStatus.PROCESSING,
        view_count=0,
        like_count=0
    )

    db.add(db_material)
    db.commit()
    db.refresh(db_material)

    return db_material


def update_material_status(
    db: Session,
    material: Material,
    status: MaterialStatus
) -> Material:
    """
    Update material processing status.

    Args:
        db: Database session
        material: Material to update
        status: New status value

    Returns:
        Material: The updated material
    """
    material.status = status
    db.commit()
    db.refresh(material)
    return material


def update_material_thumbnail(
    db: Session,
    material: Material,
    thumbnail_path: str
) -> Material:
    """
    Update material thumbnail path.

    Args:
        db: Database session
        material: Material to update
        thumbnail_path: Path to thumbnail in MinIO

    Returns:
        Material: The updated material
    """
    material.thumbnail_path = thumbnail_path
    db.commit()
    db.refresh(material)
    return material


def update_material(
    db: Session,
    material: Material,
    material_update: MaterialUpdate
) -> Material:
    """
    Update material information.

    Args:
        db: Database session
        material: Material to update
        material_update: Update data

    Returns:
        Material: The updated material
    """
    update_data = material_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(material, field, value)

    db.commit()
    db.refresh(material)
    return material


def delete_material(db: Session, material: Material) -> None:
    """
    Delete a material record.

    Args:
        db: Database session
        material: Material to delete
    """
    db.delete(material)
    db.commit()


# Valid sort fields to prevent SQL injection
VALID_SORT_FIELDS = {"created_at", "view_count", "like_count"}
VALID_SORT_ORDERS = {"asc", "desc"}


def get_materials(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    status: Optional[MaterialStatus] = None,
    material_type: Optional[MaterialType] = None,
    uploader_id: Optional[int] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    include_uploader: bool = True
) -> List[Material]:
    """
    Get a list of materials with optional filtering and sorting.

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Filter by status
        material_type: Filter by type
        uploader_id: Filter by uploader
        sort_by: Sort field (created_at, view_count, like_count)
        sort_order: Sort order (asc, desc)
        include_uploader: Whether to preload uploader information

    Returns:
        List[Material]: List of materials
    """
    query = db.query(Material)

    # Preload uploader to avoid N+1 problem
    if include_uploader:
        query = query.options(joinedload(Material.uploader))

    # Apply filters
    if status:
        query = query.filter(Material.status == status)
    if material_type:
        query = query.filter(Material.type == material_type)
    if uploader_id:
        query = query.filter(Material.uploader_id == uploader_id)
    if search:
        query = query.filter(Material.title.ilike(f"%{search}%"))

    # Validate and apply sorting
    if sort_by not in VALID_SORT_FIELDS:
        sort_by = "created_at"
    if sort_order not in VALID_SORT_ORDERS:
        sort_order = "desc"

    sort_column = getattr(Material, sort_by)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    return query.offset(skip).limit(limit).all()


def count_materials(
    db: Session,
    status: Optional[MaterialStatus] = None,
    material_type: Optional[MaterialType] = None,
    uploader_id: Optional[int] = None,
    search: Optional[str] = None
) -> int:
    """
    Get total count of materials with optional filtering.

    Args:
        db: Database session
        status: Filter by status
        material_type: Filter by type
        uploader_id: Filter by uploader

    Returns:
        int: Total number of materials
    """
    query = db.query(Material)

    if status:
        query = query.filter(Material.status == status)
    if material_type:
        query = query.filter(Material.type == material_type)
    if uploader_id:
        query = query.filter(Material.uploader_id == uploader_id)
    if search:
        query = query.filter(Material.title.ilike(f"%{search}%"))

    return query.count()


def increment_view_count(db: Session, material: Material) -> Material:
    """
    Increment material view count.

    Args:
        db: Database session
        material: Material to update

    Returns:
        Material: The updated material
    """
    material.view_count += 1
    db.commit()
    db.refresh(material)
    return material


def increment_like_count(db: Session, material: Material) -> Material:
    """
    Increment material like count.

    This function is typically called within a transaction by the like CRUD
    operations to ensure consistency between likes table and like_count.

    Args:
        db: Database session
        material: Material to update

    Returns:
        Material: The updated material
    """
    material.like_count += 1
    # Note: commit is handled by the caller (like CRUD) for transaction consistency
    db.flush()
    db.refresh(material)
    return material


def decrement_like_count(db: Session, material: Material) -> Material:
    """
    Decrement material like count.

    This function is typically called within a transaction by the like CRUD
    operations to ensure consistency between likes table and like_count.

    Args:
        db: Database session
        material: Material to update

    Returns:
        Material: The updated material
    """
    if material.like_count > 0:
        material.like_count -= 1
        # Note: commit is handled by the caller (like CRUD) for transaction consistency
        db.flush()
        db.refresh(material)
    return material


def cleanup_stale_processing_materials(
    db: Session,
    max_age_minutes: int = 30
) -> int:
    """
    Delete materials stuck in processing state for too long.

    This should be called by a scheduled cleanup task.

    Args:
        db: Database session
        max_age_minutes: Maximum age in minutes before considering stale

    Returns:
        int: Number of deleted records
    """
    cutoff_time = datetime.utcnow() - timedelta(minutes=max_age_minutes)

    stale_materials = db.query(Material).filter(
        Material.status == MaterialStatus.PROCESSING,
        Material.created_at < cutoff_time
    ).all()

    count = len(stale_materials)

    for material in stale_materials:
        db.delete(material)

    if count > 0:
        db.commit()

    return count


def get_materials_by_uploader(
    db: Session,
    uploader_id: int,
    skip: int = 0,
    limit: int = 20
) -> List[Material]:
    """
    Get materials uploaded by a specific user.

    Args:
        db: Database session
        uploader_id: User ID
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List[Material]: List of materials
    """
    return db.query(Material).filter(
        Material.uploader_id == uploader_id
    ).order_by(
        desc(Material.created_at)
    ).offset(skip).limit(limit).all()


def soft_delete_material(db: Session, material: Material) -> Material:
    """
    Soft delete a material by changing its status to hidden.

    Args:
        db: Database session
        material: Material to soft delete

    Returns:
        Material: The updated material
    """
    material.status = MaterialStatus.HIDDEN
    db.commit()
    db.refresh(material)
    return material


def check_material_exists(db: Session, material_id: int, include_hidden: bool = False) -> bool:
    """
    Check if a material exists.

    Args:
        db: Database session
        material_id: Material ID to check
        include_hidden: Whether to include hidden materials in check

    Returns:
        bool: True if material exists, False otherwise
    """
    query = db.query(Material).filter(Material.id == material_id)
    if not include_hidden:
        query = query.filter(Material.status != MaterialStatus.HIDDEN)
    return query.first() is not None
