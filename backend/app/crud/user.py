"""
User CRUD Operations Module

Provides Create, Read, Update, Delete operations for User model.
"""

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """
    Get a user by ID.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        User if found, None otherwise
    """
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Get a user by email address.

    Args:
        db: Database session
        email: User email address

    Returns:
        User if found, None otherwise
    """
    return db.query(User).filter(User.email == email).first()


def check_email_exists(db: Session, email: str) -> bool:
    """
    Check if a user with the given email already exists.

    Args:
        db: Database session
        email: Email address to check

    Returns:
        bool: True if email exists, False otherwise
    """
    return db.query(User).filter(User.email == email).first() is not None


def create_user(db: Session, user_data: UserCreate) -> User:
    """
    Create a new user.

    Args:
        db: Database session
        user_data: User creation data including email, name, and password

    Returns:
        User: The created user

    Raises:
        HTTPException: If email already exists
    """
    # Check if email already exists
    if check_email_exists(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "EMAIL_ALREADY_EXISTS",
                    "message": "Email address is already registered",
                    "details": {"email": user_data.email}
                }
            }
        )

    # Create user with hashed password
    db_user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=get_password_hash(user_data.password),
        avatar_url=user_data.avatar_url,
        is_active=True
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user by email and password.

    Args:
        db: Database session
        email: User email address
        password: Plain text password

    Returns:
        User if authentication successful, None otherwise
    """
    user = get_user_by_email(db, email)

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


def authenticate_user_or_raise(
    db: Session,
    email: str,
    password: str
) -> User:
    """
    Authenticate a user and raise exception if failed.

    Args:
        db: Database session
        email: User email address
        password: Plain text password

    Returns:
        User: The authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    user = authenticate_user(db, email, password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "邮箱或密码错误",
                    "details": {}
                }
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "INACTIVE_USER",
                    "message": "User account is inactive",
                    "details": {}
                }
            }
        )

    return user


def update_user(
    db: Session,
    user: User,
    user_update: UserUpdate
) -> User:
    """
    Update user information.

    Args:
        db: Database session
        user: User to update
        user_update: Update data

    Returns:
        User: The updated user
    """
    update_data = user_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return user


def update_user_password(
    db: Session,
    user: User,
    new_password: str
) -> User:
    """
    Update user password.

    Args:
        db: Database session
        user: User to update
        new_password: New plain text password

    Returns:
        User: The updated user
    """
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    """
    Delete a user.

    Args:
        db: Database session
        user: User to delete
    """
    db.delete(user)
    db.commit()


def get_users(
    db: Session,
    skip: int = 0,
    limit: int = 100
) -> list[User]:
    """
    Get a list of users with pagination.

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        list[User]: List of users
    """
    return db.query(User).offset(skip).limit(limit).all()


def count_users(db: Session) -> int:
    """
    Get total count of users.

    Args:
        db: Database session

    Returns:
        int: Total number of users
    """
    return db.query(User).count()
