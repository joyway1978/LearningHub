"""
Security and JWT Authentication Module

Provides password hashing, JWT token creation/verification, and authentication utilities.
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.user import TokenPayload

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme for FastAPI
security_bearer = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: The plain text password to verify
        hashed_password: The bcrypt hashed password

    Returns:
        bool: True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: The plain text password to hash

    Returns:
        str: The bcrypt hashed password
    """
    return pwd_context.hash(password)


def generate_jwt_secret() -> str:
    """
    Generate a random JWT secret key.

    Used when JWT_SECRET_KEY is not configured (development only).

    Returns:
        str: A random 32-byte hex string
    """
    return secrets.token_hex(32)


# Cache for JWT key to ensure consistency across the application lifecycle
_jwt_secret_cache: Optional[str] = None


def get_jwt_secret() -> str:
    """
    Get JWT secret key from settings or generate one.

    Uses a cached key to ensure token creation and verification use the same key.

    Returns:
        str: JWT secret key
    """
    global _jwt_secret_cache

    # Return cached key if available
    if _jwt_secret_cache is not None:
        return _jwt_secret_cache

    secret = settings.jwt_secret_key
    if not secret or secret == "your-secret-key-change-in-production":
        # In production, this should be configured
        if settings.environment == "production":
            raise ValueError(
                "JWT_SECRET_KEY must be set in production environment"
            )
        # For development, generate a random key and cache it
        _jwt_secret_cache = generate_jwt_secret()
        return _jwt_secret_cache

    # Cache the configured key
    _jwt_secret_cache = secret
    return _jwt_secret_cache


def create_access_token(
    subject: Union[str, int],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        subject: The subject of the token (usually user ID)
        expires_delta: Optional custom expiration time

    Returns:
        str: Encoded JWT access token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access",
        "iat": datetime.utcnow()
    }

    encoded_jwt = jwt.encode(
        to_encode,
        get_jwt_secret(),
        algorithm=settings.algorithm
    )
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, int],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token.

    Refresh tokens have longer expiration than access tokens.

    Args:
        subject: The subject of the token (usually user ID)
        expires_delta: Optional custom expiration time

    Returns:
        str: Encoded JWT refresh token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Refresh tokens expire in 30 days by default
        expire = datetime.utcnow() + timedelta(days=30)

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
        "iat": datetime.utcnow()
    }

    encoded_jwt = jwt.encode(
        to_encode,
        get_jwt_secret(),
        algorithm=settings.algorithm
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[TokenPayload]:
    """
    Decode and validate a JWT token.

    Args:
        token: The JWT token to decode

    Returns:
        TokenPayload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            get_jwt_secret(),
            algorithms=[settings.algorithm]
        )
        token_data = TokenPayload(**payload)

        # Check if token is expired
        # Use timezone-aware datetime for comparison
        now = datetime.now(timezone.utc)
        if token_data.exp and now > token_data.exp:
            return None

        return token_data
    except (JWTError, ValidationError):
        return None


def verify_token_type(token: str, expected_type: str) -> Optional[TokenPayload]:
    """
    Verify a token and check its type.

    Args:
        token: The JWT token to verify
        expected_type: Expected token type ('access' or 'refresh')

    Returns:
        TokenPayload if valid and correct type, None otherwise
    """
    token_data = decode_token(token)
    if not token_data:
        return None

    if token_data.type != expected_type:
        return None

    return token_data


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from the access token.

    This is a FastAPI dependency that extracts and validates the JWT token
    from the Authorization header, then retrieves the corresponding user.

    Args:
        credentials: HTTP Bearer credentials from Authorization header
        db: Database session

    Returns:
        User: The authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error": {
                "code": "INVALID_CREDENTIALS",
                "message": "Could not validate credentials",
                "details": {}
            }
        },
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials:
        raise credentials_exception

    token_data = verify_token_type(credentials.credentials, "access")
    if not token_data:
        raise credentials_exception

    try:
        user_id = int(token_data.sub) if token_data.sub else None
    except (ValueError, TypeError):
        raise credentials_exception

    if user_id is None:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current active user.

    Extends get_current_user to also check if the user account is active.

    Args:
        current_user: The authenticated user from get_current_user

    Returns:
        User: The active authenticated user

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
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
    return current_user


async def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get the current user if authenticated, or None if not.

    This is useful for endpoints that can work with or without authentication.

    Args:
        credentials: HTTP Bearer credentials from Authorization header
        db: Database session

    Returns:
        User or None: The authenticated user if valid token, None otherwise
    """
    if not credentials:
        return None

    token_data = verify_token_type(credentials.credentials, "access")
    if not token_data:
        return None

    try:
        user_id = int(token_data.sub) if token_data.sub else None
    except (ValueError, TypeError):
        return None

    if user_id is None:
        return None

    user = db.query(User).filter(User.id == user_id).first()
    return user
