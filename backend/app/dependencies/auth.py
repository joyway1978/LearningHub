"""
Authentication Dependencies Module

FastAPI dependencies for authentication and authorization.
Re-exports from security module for convenience.
"""

from app.core.security import (
    get_current_user,
    get_current_active_user,
    get_optional_current_user,
    verify_token_type,
    decode_token,
)

# Re-export all authentication dependencies
__all__ = [
    "get_current_user",
    "get_current_active_user",
    "get_optional_current_user",
    "verify_token_type",
    "decode_token",
]
