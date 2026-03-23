"""
Admin Router Module

Provides administrative API endpoints for system management,
including manual cleanup operations and scheduler management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from app.core.scheduler import (
    trigger_cleanup_now,
    get_scheduled_jobs,
    pause_job,
    resume_job,
    is_scheduler_running
)
from app.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["Admin"])


class CleanupRequest(BaseModel):
    """Request model for manual cleanup."""
    cleanup_processing: bool = Field(
        default=True,
        description="Clean up stale processing records"
    )
    cleanup_orphans: bool = Field(
        default=True,
        description="Clean up orphan files"
    )
    max_age_minutes: int = Field(
        default=30,
        ge=1,
        le=1440,
        description="Maximum age in minutes for processing records"
    )


class CleanupResponse(BaseModel):
    """Response model for cleanup operation."""
    success: bool
    cleaned_records: int
    cleaned_files: int
    duration_seconds: float
    errors: list[str]


class SchedulerStatusResponse(BaseModel):
    """Response model for scheduler status."""
    running: bool
    jobs: list[dict]


class JobControlResponse(BaseModel):
    """Response model for job control operations."""
    success: bool
    message: str
    job_id: str


def check_admin_access(current_user: User) -> None:
    """
    Check if the current user has admin access.

    For this implementation, we use a simple check based on user email domain
    or a specific admin flag. In production, you should implement proper
    role-based access control (RBAC).

    Args:
        current_user: The currently authenticated user

    Raises:
        HTTPException: If user is not an admin
    """
    # Simple admin check - in production, use proper RBAC
    # For now, we'll consider users with specific emails as admins
    # or you can add an `is_admin` field to the User model
    admin_emails = ["admin@example.com", "admin@ailearn.com"]

    # Check if user has admin privileges
    # This is a placeholder - implement proper admin check based on your needs
    is_admin = (
        current_user.email in admin_emails or
        current_user.email.endswith("@admin.ailearn.com") or
        getattr(current_user, 'is_admin', False)
    )

    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "FORBIDDEN",
                    "message": "Admin access required",
                    "details": {}
                }
            }
        )


@router.post(
    "/cleanup",
    response_model=CleanupResponse,
    summary="Trigger manual cleanup",
    description="Manually trigger the cleanup task to remove stale records and orphan files."
)
async def manual_cleanup(
    request: CleanupRequest,
    current_user: User = Depends(get_current_active_user)
) -> CleanupResponse:
    """
    Manually trigger the cleanup task.

    - **cleanup_processing**: Clean up stale processing records (default: true)
    - **cleanup_orphans**: Clean up orphan files not referenced in database (default: true)
    - **max_age_minutes**: Maximum age in minutes for processing records (default: 30)

    Requires admin privileges.

    Returns cleanup results including counts of cleaned records and files.
    """
    check_admin_access(current_user)

    try:
        result = await trigger_cleanup_now()

        return CleanupResponse(
            success=len(result.get("errors", [])) == 0,
            cleaned_records=result.get("cleaned_records", 0),
            cleaned_files=result.get("cleaned_files", 0),
            duration_seconds=result.get("duration_seconds", 0.0),
            errors=result.get("errors", [])
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "CLEANUP_FAILED",
                    "message": f"Cleanup operation failed: {str(e)}",
                    "details": {}
                }
            }
        )


@router.get(
    "/scheduler/status",
    response_model=SchedulerStatusResponse,
    summary="Get scheduler status",
    description="Get the current status of the background task scheduler."
)
async def scheduler_status(
    current_user: User = Depends(get_current_active_user)
) -> SchedulerStatusResponse:
    """
    Get scheduler status and scheduled jobs.

    Requires admin privileges.

    Returns scheduler running status and list of scheduled jobs.
    """
    check_admin_access(current_user)

    return SchedulerStatusResponse(
        running=is_scheduler_running(),
        jobs=get_scheduled_jobs()
    )


@router.post(
    "/scheduler/jobs/{job_id}/pause",
    response_model=JobControlResponse,
    summary="Pause a scheduled job",
    description="Pause a specific scheduled job by ID."
)
async def pause_scheduled_job(
    job_id: str,
    current_user: User = Depends(get_current_active_user)
) -> JobControlResponse:
    """
    Pause a scheduled job.

    - **job_id**: ID of the job to pause

    Requires admin privileges.
    """
    check_admin_access(current_user)

    success = pause_job(job_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "JOB_NOT_FOUND",
                    "message": f"Job {job_id} not found",
                    "details": {"job_id": job_id}
                }
            }
        )

    return JobControlResponse(
        success=True,
        message=f"Job {job_id} paused successfully",
        job_id=job_id
    )


@router.post(
    "/scheduler/jobs/{job_id}/resume",
    response_model=JobControlResponse,
    summary="Resume a paused job",
    description="Resume a specific paused job by ID."
)
async def resume_scheduled_job(
    job_id: str,
    current_user: User = Depends(get_current_active_user)
) -> JobControlResponse:
    """
    Resume a paused job.

    - **job_id**: ID of the job to resume

    Requires admin privileges.
    """
    check_admin_access(current_user)

    success = resume_job(job_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "JOB_NOT_FOUND",
                    "message": f"Job {job_id} not found",
                    "details": {"job_id": job_id}
                }
            }
        )

    return JobControlResponse(
        success=True,
        message=f"Job {job_id} resumed successfully",
        job_id=job_id
    )
