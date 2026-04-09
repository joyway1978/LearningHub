"""
Reactions Router Module

Handles material reaction endpoints (thumbs up/down, question, insight).
Implements toggle behavior with proper authorization.
"""

from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.dependencies.auth import get_current_active_user, get_optional_current_user
from app.models.material import Material, MaterialReaction
from app.models.user import User

router = APIRouter()

# Valid reaction types
VALID_REACTION_TYPES = {"thumbs_up", "thumbs_down", "question", "insight"}

# Emoji mapping for display
REACTION_EMOJI = {
    "thumbs_up": "👍",
    "thumbs_down": "👎",
    "question": "❓",
    "insight": "💡"
}

# Tooltip text
REACTION_TOOLTIP = {
    "thumbs_up": "有帮助",
    "thumbs_down": "没帮助",
    "question": "有疑问",
    "insight": "有启发"
}


def _validate_reaction_type(reaction_type: str) -> None:
    """Validate reaction type is allowed."""
    if reaction_type not in VALID_REACTION_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"reaction_type must be one of: {', '.join(sorted(VALID_REACTION_TYPES))}"
        )


def _get_material_or_404(db: Session, material_id: int) -> Material:
    """Get material by ID or raise 404."""
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )
    return material


@router.post("/{material_id}/reactions", response_model=dict)
async def add_or_update_reaction(
    material_id: int,
    reaction_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Add or update a reaction on a material.

    If user already has a reaction, it will be updated to the new type.
    This implements toggle behavior for reaction switching.

    Args:
        material_id: ID of the material to react to
        reaction_data: JSON body with "reaction_type" field
        current_user: Authenticated user
        db: Database session

    Returns:
        dict: Reaction details and counts

    Raises:
        400: Invalid reaction_type
        401: Not authenticated
        404: Material not found
    """
    reaction_type = reaction_data.get("reaction_type")
    if not reaction_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="reaction_type is required"
        )

    _validate_reaction_type(reaction_type)
    material = _get_material_or_404(db, material_id)

    # Check for existing reaction
    existing = db.query(MaterialReaction).filter(
        MaterialReaction.material_id == material_id,
        MaterialReaction.user_id == current_user.id
    ).first()

    if existing:
        # Update existing reaction
        if existing.reaction_type == reaction_type:
            # Same type, no change needed
            return {
                "id": existing.id,
                "material_id": material_id,
                "user_id": current_user.id,
                "reaction_type": reaction_type,
                "emoji": REACTION_EMOJI[reaction_type],
                "tooltip": REACTION_TOOLTIP[reaction_type],
                "message": "Reaction already exists",
                "counts": get_reaction_counts(db, material_id)
            }

        # Different type, update it
        existing.reaction_type = reaction_type
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)

        return {
            "id": existing.id,
            "material_id": material_id,
            "user_id": current_user.id,
            "reaction_type": reaction_type,
            "emoji": REACTION_EMOJI[reaction_type],
            "tooltip": REACTION_TOOLTIP[reaction_type],
            "message": "Reaction updated",
            "counts": get_reaction_counts(db, material_id)
        }
    else:
        # Create new reaction
        try:
            reaction = MaterialReaction(
                material_id=material_id,
                user_id=current_user.id,
                reaction_type=reaction_type
            )
            db.add(reaction)
            db.commit()
            db.refresh(reaction)

            return {
                "id": reaction.id,
                "material_id": material_id,
                "user_id": current_user.id,
                "reaction_type": reaction_type,
                "emoji": REACTION_EMOJI[reaction_type],
                "tooltip": REACTION_TOOLTIP[reaction_type],
                "message": "Reaction added",
                "counts": get_reaction_counts(db, material_id)
            }
        except IntegrityError:
            db.rollback()
            # Concurrent request created the reaction
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Reaction already exists. Please refresh and try again."
            )


@router.delete("/{material_id}/reactions", response_model=dict)
async def remove_reaction(
    material_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Remove user's reaction from a material.

    Args:
        material_id: ID of the material
        current_user: Authenticated user
        db: Database session

    Returns:
        dict: Success message and updated counts

    Raises:
        401: Not authenticated
        404: Material not found or no reaction to remove
    """
    _get_material_or_404(db, material_id)

    reaction = db.query(MaterialReaction).filter(
        MaterialReaction.material_id == material_id,
        MaterialReaction.user_id == current_user.id
    ).first()

    if not reaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No reaction found to remove"
        )

    db.delete(reaction)
    db.commit()

    return {
        "message": "Reaction removed",
        "counts": get_reaction_counts(db, material_id)
    }


@router.get("/{material_id}/reactions", response_model=dict)
async def get_reaction_stats(
    material_id: int,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Get reaction statistics for a material.

    Returns counts for each reaction type and optionally the current user's reaction.

    Args:
        material_id: ID of the material
        current_user: Optional authenticated user
        db: Database session

    Returns:
        dict: Reaction counts and user reaction status

    Raises:
        404: Material not found
    """
    _get_material_or_404(db, material_id)

    counts = get_reaction_counts(db, material_id)

    result = {
        "material_id": material_id,
        "counts": counts,
        "total": sum(counts.values()),
        "reactions": [
            {
                "type": rt,
                "emoji": REACTION_EMOJI[rt],
                "tooltip": REACTION_TOOLTIP[rt],
                "count": counts[rt]
            }
            for rt in VALID_REACTION_TYPES
        ]
    }

    # Include current user's reaction if authenticated
    if current_user:
        user_reaction = db.query(MaterialReaction).filter(
            MaterialReaction.material_id == material_id,
            MaterialReaction.user_id == current_user.id
        ).first()

        if user_reaction:
            result["user_reaction"] = {
                "id": user_reaction.id,
                "type": user_reaction.reaction_type,
                "emoji": REACTION_EMOJI[user_reaction.reaction_type],
                "tooltip": REACTION_TOOLTIP[user_reaction.reaction_type],
                "created_at": user_reaction.created_at.isoformat()
            }
        else:
            result["user_reaction"] = None

    return result


@router.get("/{material_id}/reactions/me", response_model=dict)
async def get_my_reaction(
    material_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's reaction for a specific material.

    Args:
        material_id: ID of the material
        current_user: Authenticated user
        db: Database session

    Returns:
        dict: User's reaction details or null

    Raises:
        401: Not authenticated
        404: Material not found
    """
    _get_material_or_404(db, material_id)

    reaction = db.query(MaterialReaction).filter(
        MaterialReaction.material_id == material_id,
        MaterialReaction.user_id == current_user.id
    ).first()

    if reaction:
        return {
            "has_reaction": True,
            "reaction": {
                "id": reaction.id,
                "type": reaction.reaction_type,
                "emoji": REACTION_EMOJI[reaction.reaction_type],
                "tooltip": REACTION_TOOLTIP[reaction.reaction_type],
                "created_at": reaction.created_at.isoformat(),
                "updated_at": reaction.updated_at.isoformat()
            }
        }
    else:
        return {
            "has_reaction": False,
            "reaction": None
        }


def get_reaction_counts(db: Session, material_id: int) -> dict:
    """
    Get reaction counts for a material.

    Args:
        db: Database session
        material_id: Material ID

    Returns:
        dict: Count for each reaction type
    """
    counts = {rt: 0 for rt in VALID_REACTION_TYPES}

    reactions = db.query(MaterialReaction).filter(
        MaterialReaction.material_id == material_id
    ).all()

    for reaction in reactions:
        if reaction.reaction_type in counts:
            counts[reaction.reaction_type] += 1

    return counts
