"""
User Schemas

Pydantic models for user data validation and serialization.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    """Base user schema with common attributes."""
    email: EmailStr = Field(..., description="User email address")
    name: str = Field(..., min_length=1, max_length=100, description="User display name")
    avatar_url: Optional[str] = Field(None, max_length=500, description="URL to user's avatar image")


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="User password (min 8 characters)"
    )


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    avatar_url: Optional[str] = Field(None, max_length=500)


class UserInDB(UserBase):
    """Schema for user data as stored in database."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    hashed_password: str = Field(..., description="Bcrypt hashed password")


class UserResponse(UserBase):
    """Schema for user data in API responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime


class UserWithStats(UserResponse):
    """Schema for user data with additional statistics."""
    materials_count: int = Field(0, description="Number of materials uploaded")
    total_views: int = Field(0, description="Total views across all materials")
    total_likes: int = Field(0, description="Total likes across all materials")


# Authentication related schemas
class Token(BaseModel):
    """Schema for authentication token response."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class TokenPayload(BaseModel):
    """Schema for JWT token payload."""
    sub: Optional[int] = Field(None, description="Subject (user ID)")
    exp: Optional[datetime] = Field(None, description="Expiration timestamp")
    type: Optional[str] = Field(None, description="Token type")


class LoginRequest(BaseModel):
    """Schema for login request."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class passwordChangeRequest(BaseModel):
    """Schema for password change request."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="New password (min 8 characters)"
    )
