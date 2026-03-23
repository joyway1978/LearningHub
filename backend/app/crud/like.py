"""
Like CRUD Operations Module

Provides Create, Read, Delete operations for Like model.
Handles like/unlike functionality with transaction support.
"""

from typing import Optional

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.material import Like, Material
from app.crud.material import increment_like_count, decrement_like_count


def get_like_by_user_and_material(
    db: Session,
    user_id: int,
    material_id: int
) -> Optional[Like]:
    """
    Get a like record by user ID and material ID.

    Args:
        db: Database session
        user_id: User ID
        material_id: Material ID

    Returns:
        Like record if found, None otherwise
    """
    return db.query(Like).filter(
        Like.user_id == user_id,
        Like.material_id == material_id
    ).first()


def create_like(
    db: Session,
    user_id: int,
    material_id: int
) -> Optional[Like]:
    """
    Create a new like record.

    Args:
        db: Database session
        user_id: User ID who likes the material
        material_id: Material ID to like

    Returns:
        Created Like record, or None if already exists

    Note:
        Uses database unique constraint to prevent duplicate likes.
        Returns None if the like already exists (IntegrityError).
    """
    try:
        db_like = Like(
            user_id=user_id,
            material_id=material_id
        )
        db.add(db_like)
        db.commit()
        db.refresh(db_like)
        return db_like
    except IntegrityError:
        # Unique constraint violation - like already exists
        db.rollback()
        return None


def delete_like(
    db: Session,
    like: Like
) -> bool:
    """
    Delete a like record.

    Args:
        db: Database session
        like: Like record to delete

    Returns:
        True if deleted successfully
    """
    db.delete(like)
    db.commit()
    return True


def delete_like_by_user_and_material(
    db: Session,
    user_id: int,
    material_id: int
) -> bool:
    """
    Delete a like record by user ID and material ID.

    Args:
        db: Database session
        user_id: User ID
        material_id: Material ID

    Returns:
        True if a like was deleted, False if no like found
    """
    like = get_like_by_user_and_material(db, user_id, material_id)
    if like:
        return delete_like(db, like)
    return False


def get_like_count_by_material(db: Session, material_id: int) -> int:
    """
    Get the total number of likes for a material.

    Args:
        db: Database session
        material_id: Material ID

    Returns:
        Number of likes
    """
    return db.query(func.count(Like.id)).filter(
        Like.material_id == material_id
    ).scalar() or 0


def check_user_liked(
    db: Session,
    user_id: int,
    material_id: int
) -> bool:
    """
    Check if a user has liked a material.

    Args:
        db: Database session
        user_id: User ID
        material_id: Material ID

    Returns:
        True if user has liked the material, False otherwise
    """
    like = get_like_by_user_and_material(db, user_id, material_id)
    return like is not None


def toggle_like(
    db: Session,
    user_id: int,
    material_id: int
) -> tuple[bool, int]:
    """
    Toggle like status for a material (like/unlike).

    This function uses database transactions to ensure consistency
    between the likes table and the material's like_count.

    Args:
        db: Database session
        user_id: User ID
        material_id: Material ID

    Returns:
        Tuple of (is_liked, like_count):
        - is_liked: True if material is now liked, False if unliked
        - like_count: Current like count for the material

    Raises:
        ValueError: If material not found
    """
    # Get material
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise ValueError(f"Material with id {material_id} not found")

    # Check if user has already liked this material
    existing_like = get_like_by_user_and_material(db, user_id, material_id)

    if existing_like:
        # Unlike: Delete like record and decrement count
        delete_like(db, existing_like)
        decrement_like_count(db, material)
        return False, material.like_count
    else:
        # Like: Create like record and increment count
        new_like = create_like(db, user_id, material_id)
        if new_like:
            increment_like_count(db, material)
            return True, material.like_count
        else:
            # Like already exists (race condition), treat as already liked
            return True, material.like_count


def get_user_liked_material_ids(
    db: Session,
    user_id: int,
    material_ids: list[int]
) -> set[int]:
    """
    Get the set of material IDs that the user has liked from a list.

    This is useful for efficiently checking like status for multiple
    materials at once (e.g., in list views).

    Args:
        db: Database session
        user_id: User ID
        material_ids: List of material IDs to check

    Returns:
        Set of material IDs that the user has liked
    """
    if not material_ids:
        return set()

    liked_ids = db.query(Like.material_id).filter(
        Like.user_id == user_id,
        Like.material_id.in_(material_ids)
    ).all()

    return {row[0] for row in liked_ids}
