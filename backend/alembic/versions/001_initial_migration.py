"""
Initial migration - Create all tables

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables with indexes."""
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False, comment="User email address (unique, used for login)"),
        sa.Column("name", sa.String(length=100), nullable=False, comment="User display name"),
        sa.Column("hashed_password", sa.String(length=255), nullable=False, comment="Bcrypt hashed password"),
        sa.Column("avatar_url", sa.String(length=500), nullable=True, comment="URL to user's avatar image"),
        sa.Column("is_active", sa.Boolean(), nullable=False, comment="Whether the account is active"),
        sa.Column("created_at", sa.DateTime(), nullable=False, comment="Account creation timestamp"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create users indexes
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    # Create materials table
    op.create_table(
        "materials",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False, comment="Material title"),
        sa.Column("description", sa.Text(), nullable=True, comment="Material description"),
        sa.Column("type", sa.String(length=20), nullable=False, comment="Material type: video or pdf"),
        sa.Column("file_path", sa.String(length=500), nullable=False, comment="Path to file in MinIO storage"),
        sa.Column("file_size", sa.BigInteger(), nullable=False, comment="File size in bytes"),
        sa.Column("file_format", sa.String(length=20), nullable=False, comment="File format extension (e.g., mp4, pdf)"),
        sa.Column("thumbnail_path", sa.String(length=500), nullable=True, comment="Path to thumbnail image in MinIO"),
        sa.Column("uploader_id", sa.Integer(), nullable=False, comment="Foreign key to user who uploaded"),
        sa.Column("view_count", sa.Integer(), nullable=False, comment="Number of views"),
        sa.Column("like_count", sa.Integer(), nullable=False, comment="Number of likes"),
        sa.Column("status", sa.String(length=20), nullable=False, comment="Material status: active, processing, or hidden"),
        sa.Column("created_at", sa.DateTime(), nullable=False, comment="Creation timestamp"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, comment="Last update timestamp"),
        sa.ForeignKeyConstraint(["uploader_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create materials indexes (with DESC for sorting optimization)
    op.create_index(op.f("ix_materials_id"), "materials", ["id"], unique=False)
    op.create_index("idx_materials_uploader", "materials", ["uploader_id"], unique=False)
    op.create_index("idx_materials_created", "materials", [sa.desc("created_at")], unique=False)
    op.create_index("idx_materials_views", "materials", [sa.desc("view_count")], unique=False)
    op.create_index("idx_materials_likes", "materials", [sa.desc("like_count")], unique=False)

    # Create likes table
    op.create_table(
        "likes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("material_id", sa.Integer(), nullable=False, comment="Foreign key to material"),
        sa.Column("user_id", sa.Integer(), nullable=False, comment="Foreign key to user who liked"),
        sa.Column("created_at", sa.DateTime(), nullable=False, comment="Like timestamp"),
        sa.ForeignKeyConstraint(["material_id"], ["materials.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("material_id", "user_id", name="uq_likes_material_user"),
    )

    # Create likes indexes
    op.create_index(op.f("ix_likes_id"), "likes", ["id"], unique=False)

    # Create views table
    op.create_table(
        "views",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("material_id", sa.Integer(), nullable=False, comment="Foreign key to material"),
        sa.Column("user_id", sa.Integer(), nullable=True, comment="Foreign key to user who viewed (nullable for anonymous)"),
        sa.Column("ip_address", sa.String(length=45), nullable=True, comment="IP address of viewer (supports IPv6)"),
        sa.Column("created_at", sa.DateTime(), nullable=False, comment="View timestamp"),
        sa.ForeignKeyConstraint(["material_id"], ["materials.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create views indexes
    op.create_index(op.f("ix_views_id"), "views", ["id"], unique=False)
    op.create_index("idx_views_material", "views", ["material_id", "created_at"], unique=False)


def downgrade() -> None:
    """Drop all tables."""
    # Drop views table
    op.drop_index("idx_views_material", table_name="views")
    op.drop_index(op.f("ix_views_id"), table_name="views")
    op.drop_table("views")

    # Drop likes table
    op.drop_index(op.f("ix_likes_id"), table_name="likes")
    op.drop_table("likes")

    # Drop materials table
    op.drop_index("idx_materials_likes", table_name="materials")
    op.drop_index("idx_materials_views", table_name="materials")
    op.drop_index("idx_materials_created", table_name="materials")
    op.drop_index("idx_materials_uploader", table_name="materials")
    op.drop_index(op.f("ix_materials_id"), table_name="materials")
    op.drop_table("materials")

    # Drop users table
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
