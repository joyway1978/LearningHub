"""
CRUD Operations Package

Provides database CRUD operations for all models.
"""

from app.crud.user import (
    get_user_by_id,
    get_user_by_email,
    create_user,
    update_user,
    delete_user,
    authenticate_user,
)

from app.crud.material import (
    get_material_by_id,
    get_material_by_id_or_raise,
    get_materials,
    count_materials,
    create_material,
    update_material,
    update_material_status,
    update_material_thumbnail,
    delete_material,
    soft_delete_material,
    increment_view_count,
    increment_like_count,
    decrement_like_count,
    check_material_exists,
)

from app.crud.like import (
    get_like_by_user_and_material,
    create_like,
    delete_like,
    delete_like_by_user_and_material,
    get_like_count_by_material,
    check_user_liked,
    toggle_like,
    get_user_liked_material_ids,
)

__all__ = [
    # User CRUD
    "get_user_by_id",
    "get_user_by_email",
    "create_user",
    "update_user",
    "delete_user",
    "authenticate_user",
    # Material CRUD
    "get_material_by_id",
    "get_material_by_id_or_raise",
    "get_materials",
    "count_materials",
    "create_material",
    "update_material",
    "update_material_status",
    "update_material_thumbnail",
    "delete_material",
    "soft_delete_material",
    "increment_view_count",
    "increment_like_count",
    "decrement_like_count",
    "check_material_exists",
    # Like CRUD
    "get_like_by_user_and_material",
    "create_like",
    "delete_like",
    "delete_like_by_user_and_material",
    "get_like_count_by_material",
    "check_user_liked",
    "toggle_like",
    "get_user_liked_material_ids",
]
