"""
Database Initialization Module

Provides functions to initialize the database with default data,
including creating an admin user if no users exist.
"""

import os
import logging
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import get_password_hash
from app.crud.user import check_email_exists, create_user
from app.models.user import User
from app.schemas.user import UserCreate

logger = logging.getLogger(__name__)

# Default admin credentials (can be overridden via environment variables)
DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com")
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
DEFAULT_ADMIN_NAME = os.getenv("DEFAULT_ADMIN_NAME", "Administrator")


def init_db(db: Session) -> None:
    """
    Initialize the database with default data.

    Creates a default admin user if no users exist in the database.
    This should be called during application startup.

    Args:
        db: Database session
    """
    try:
        # Check if any users exist
        user_count = db.query(User).count()

        if user_count == 0:
            logger.info("No users found in database. Creating default admin user...")
            create_default_admin(db)
        else:
            logger.info(f"Database already has {user_count} user(s). Skipping default admin creation.")

    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        # Don't raise - we don't want to crash the app on init failure


def create_default_admin(db: Session) -> User:
    """
    Create the default admin user.

    Args:
        db: Database session

    Returns:
        User: The created admin user
    """
    # Check if admin email already exists (shouldn't happen if count is 0, but just in case)
    if check_email_exists(db, DEFAULT_ADMIN_EMAIL):
        logger.warning(f"Admin user with email {DEFAULT_ADMIN_EMAIL} already exists.")
        return db.query(User).filter(User.email == DEFAULT_ADMIN_EMAIL).first()

    # Create admin user
    admin_user = User(
        email=DEFAULT_ADMIN_EMAIL,
        name=DEFAULT_ADMIN_NAME,
        hashed_password=get_password_hash(DEFAULT_ADMIN_PASSWORD),
        is_active=True,
        avatar_url=None
    )

    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    logger.info(f"Default admin user created: {DEFAULT_ADMIN_EMAIL}")
    logger.warning(
        "IMPORTANT: Please change the default admin password after first login! "
        f"Current password: {DEFAULT_ADMIN_PASSWORD}"
    )

    return admin_user


def create_default_admin_if_configured(db: Session) -> None:
    """
    Create default admin user only if explicitly configured.

    This is a safer alternative that only creates the admin user
    if the CREATE_DEFAULT_ADMIN environment variable is set.

    Args:
        db: Database session
    """
    if os.getenv("CREATE_DEFAULT_ADMIN", "false").lower() == "true":
        init_db(db)
