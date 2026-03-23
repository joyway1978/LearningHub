"""
User Model

Represents a user in the system with authentication and profile information.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.material import Material


class User(Base):
    """
    User model for storing user account information.

    Attributes:
        id: Primary key
        email: Unique email address (used for login)
        name: Display name
        hashed_password: Bcrypt hashed password
        avatar_url: URL to user's avatar image
        is_active: Whether the account is active
        created_at: Account creation timestamp
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        comment="User email address (unique, used for login)"
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="User display name"
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Bcrypt hashed password"
    )
    avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="URL to user's avatar image"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the account is active"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Account creation timestamp"
    )

    # Relationships
    materials: Mapped[list["Material"]] = relationship(
        "Material",
        back_populates="uploader",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, name={self.name})>"
