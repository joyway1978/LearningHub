"""
View Tracking Service Module

Provides view counting functionality with deduplication logic.
Uses in-memory cache to track recent views and prevent duplicate counting.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Union

from sqlalchemy.orm import Session

from app.crud.material import increment_view_count
from app.models.material import Material, View
from app.models.user import User

logger = logging.getLogger(__name__)

# In-memory cache for view deduplication
# Key: (material_id, user_id or ip_address)
# Value: last_view_time
_view_cache: Dict[Tuple[int, Union[int, str]], datetime] = {}

# Deduplication window in minutes
VIEW_DEDUPLICATION_MINUTES = 10


def _get_cache_key(material_id: int, user_id: Optional[int], ip_address: Optional[str]) -> Tuple[int, Union[int, str]]:
    """
    Generate a cache key for view tracking.

    Args:
        material_id: ID of the material being viewed
        user_id: ID of the authenticated user (if any)
        ip_address: IP address of the viewer

    Returns:
        Tuple of (material_id, user_id or ip_address)
    """
    if user_id is not None:
        return (material_id, user_id)
    # Use IP address for anonymous users
    return (material_id, ip_address or "unknown")


def _is_duplicate_view(cache_key: Tuple[int, Union[int, str]]) -> bool:
    """
    Check if this view is a duplicate within the deduplication window.

    Args:
        cache_key: The cache key for this view

    Returns:
        bool: True if this is a duplicate view, False otherwise
    """
    last_view_time = _view_cache.get(cache_key)
    if last_view_time is None:
        return False

    cutoff_time = datetime.utcnow() - timedelta(minutes=VIEW_DEDUPLICATION_MINUTES)
    return last_view_time > cutoff_time


def _update_view_cache(cache_key: Tuple[int, Union[int, str]]) -> None:
    """
    Update the view cache with the current timestamp.

    Args:
        cache_key: The cache key to update
    """
    _view_cache[cache_key] = datetime.utcnow()


def _cleanup_old_cache_entries() -> None:
    """
    Clean up cache entries older than the deduplication window.
    This prevents memory leaks from the cache growing indefinitely.
    """
    cutoff_time = datetime.utcnow() - timedelta(minutes=VIEW_DEDUPLICATION_MINUTES)
    keys_to_remove = [
        key for key, last_view in _view_cache.items()
        if last_view < cutoff_time
    ]
    for key in keys_to_remove:
        del _view_cache[key]


def record_view(
    db: Session,
    material: Material,
    user: Optional[User] = None,
    ip_address: Optional[str] = None
) -> bool:
    """
    Record a view for a material with deduplication.

    This function:
    1. Checks if this is a duplicate view (same user/IP within 10 minutes)
    2. If not duplicate, increments the view count
    3. Creates a view record in the database
    4. Updates the cache

    Args:
        db: Database session
        material: The material being viewed
        user: The authenticated user (if any)
        ip_address: The IP address of the viewer

    Returns:
        bool: True if view was recorded, False if it was a duplicate
    """
    user_id = user.id if user else None
    cache_key = _get_cache_key(material.id, user_id, ip_address)

    # Check for duplicate view
    if _is_duplicate_view(cache_key):
        logger.debug(f"Duplicate view detected for material {material.id}, user {user_id}, ip {ip_address}")
        return False

    try:
        # Increment view count on material
        increment_view_count(db, material)

        # Create view record
        view_record = View(
            material_id=material.id,
            user_id=user_id,
            ip_address=ip_address
        )
        db.add(view_record)
        db.commit()

        # Update cache
        _update_view_cache(cache_key)

        # Periodically clean up old cache entries (1% chance per call)
        import random
        if random.random() < 0.01:
            _cleanup_old_cache_entries()

        logger.debug(f"View recorded for material {material.id}, user {user_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to record view for material {material.id}: {e}")
        db.rollback()
        return False


def record_view_async(
    material_id: int,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None
) -> bool:
    """
    Record a view asynchronously using a background task.

    This is a wrapper that creates its own database session.
    Should be called with background_tasks.add_task().

    Args:
        material_id: ID of the material being viewed
        user_id: ID of the authenticated user (if any)
        ip_address: IP address of the viewer

    Returns:
        bool: True if view was recorded, False otherwise
    """
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        from app.crud.material import get_material_by_id
        material = get_material_by_id(db, material_id)
        if not material:
            logger.warning(f"Material {material_id} not found for view recording")
            return False

        user = None
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()

        return record_view(db, material, user, ip_address)
    except Exception as e:
        logger.error(f"Error in async view recording: {e}")
        return False
    finally:
        db.close()


def get_view_count_stats(db: Session, material_id: int) -> dict:
    """
    Get view statistics for a material.

    Args:
        db: Database session
        material_id: ID of the material

    Returns:
        Dictionary with view statistics
    """
    from sqlalchemy import func

    total_views = db.query(View).filter(View.material_id == material_id).count()

    # Get unique viewers (by user_id or ip_address)
    unique_user_views = db.query(View).filter(
        View.material_id == material_id,
        View.user_id.isnot(None)
    ).distinct(View.user_id).count()

    unique_anonymous_views = db.query(View).filter(
        View.material_id == material_id,
        View.user_id.is_(None),
        View.ip_address.isnot(None)
    ).distinct(View.ip_address).count()

    # Views in last 24 hours
    last_24h = datetime.utcnow() - timedelta(hours=24)
    views_24h = db.query(View).filter(
        View.material_id == material_id,
        View.created_at >= last_24h
    ).count()

    # Views in last 7 days
    last_7d = datetime.utcnow() - timedelta(days=7)
    views_7d = db.query(View).filter(
        View.material_id == material_id,
        View.created_at >= last_7d
    ).count()

    return {
        "total_views": total_views,
        "unique_user_views": unique_user_views,
        "unique_anonymous_views": unique_anonymous_views,
        "views_24h": views_24h,
        "views_7d": views_7d
    }


def get_cache_stats() -> dict:
    """
    Get statistics about the view cache.

    Returns:
        Dictionary with cache statistics
    """
    return {
        "cache_size": len(_view_cache),
        "deduplication_window_minutes": VIEW_DEDUPLICATION_MINUTES
    }
