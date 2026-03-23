"""
File Validation Service Module

Provides comprehensive file validation including type checking, size validation,
MIME type verification, and file extension validation.
"""

import os
import mimetypes
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from fastapi import UploadFile, HTTPException, status

from app.config import settings


class FileType(str, Enum):
    """Supported file types enumeration."""
    VIDEO = "video"
    PDF = "pdf"


class ValidationErrorCode(str, Enum):
    """Validation error codes for consistent error responses."""
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    INVALID_MIME_TYPE = "INVALID_MIME_TYPE"
    FILE_EMPTY = "FILE_EMPTY"


@dataclass
class ValidationResult:
    """Result of file validation."""
    is_valid: bool
    file_type: Optional[FileType] = None
    extension: Optional[str] = None
    mime_type: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    details: Optional[dict] = None


# MIME type mappings for validation
VIDEO_MIME_TYPES = {
    "video/mp4": ["mp4"],
    "video/webm": ["webm"],
}

PDF_MIME_TYPES = {
    "application/pdf": ["pdf"],
}

# Allowed extensions per design requirements
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "webm"}
ALLOWED_PDF_EXTENSIONS = {"pdf"}

# Size limits per design requirements
VIDEO_MAX_SIZE = 524_288_000  # 500MB
PDF_MAX_SIZE = 52_428_800  # 50MB


def get_file_extension(filename: str) -> str:
    """
    Extract file extension from filename.

    Args:
        filename: Original filename

    Returns:
        str: Lowercase extension without dot
    """
    return os.path.splitext(filename)[1].lower().lstrip(".")


def detect_mime_type(file: UploadFile) -> Tuple[Optional[str], bytes]:
    """
    Detect MIME type by reading file header.

    Args:
        file: UploadFile object

    Returns:
        Tuple of (detected MIME type, first bytes read)
    """
    # Read first 8KB for MIME detection
    sample = file.file.read(8192)
    file.file.seek(0)  # Reset file pointer

    # Use mimetypes to guess from extension first
    ext = get_file_extension(file.filename)
    mime_from_ext, _ = mimetypes.guess_type(file.filename)

    # Check magic numbers for common formats
    magic_mime = _check_magic_numbers(sample)

    if magic_mime:
        return magic_mime, sample

    return mime_from_ext, sample


def _check_magic_numbers(sample: bytes) -> Optional[str]:
    """
    Check file magic numbers to determine MIME type.

    Args:
        sample: First bytes of the file

    Returns:
        MIME type if recognized, None otherwise
    """
    if len(sample) < 4:
        return None

    # PDF: %PDF
    if sample.startswith(b"%PDF"):
        return "application/pdf"

    # MP4: various ftyp signatures
    if len(sample) >= 12:
        # Check for ftyp box
        if sample[4:8] == b"ftyp":
            # Check for MP4 variants
            major_brand = sample[8:12]
            mp4_brands = {b"mp41", b"mp42", b"isom", b"M4V ", b"M4A ", b"f4v ", b"f4a "}
            if major_brand in mp4_brands:
                return "video/mp4"

    # WebM: starts with 0x1A 0x45 0xDF 0xA3 (EBML header)
    if sample.startswith(b"\x1a\x45\xdf\xa3"):
        return "video/webm"

    return None


def validate_file_type(
    filename: str,
    mime_type: Optional[str]
) -> Tuple[bool, Optional[FileType], Optional[str]]:
    """
    Validate file type based on extension and MIME type.

    Args:
        filename: Original filename
        mime_type: Detected MIME type

    Returns:
        Tuple of (is_valid, file_type, error_message)
    """
    extension = get_file_extension(filename)

    # Check video formats
    if extension in ALLOWED_VIDEO_EXTENSIONS:
        # Validate MIME type for videos
        valid_video_mimes = set(VIDEO_MIME_TYPES.keys())
        if mime_type and mime_type not in valid_video_mimes:
            # Allow some flexibility - check if it's a video/* type
            if not mime_type.startswith("video/"):
                return (
                    False,
                    None,
                    f"Invalid MIME type for video: {mime_type}"
                )
        return True, FileType.VIDEO, None

    # Check PDF format
    if extension in ALLOWED_PDF_EXTENSIONS:
        # Validate MIME type for PDF
        valid_pdf_mimes = set(PDF_MIME_TYPES.keys())
        if mime_type and mime_type not in valid_pdf_mimes:
            if mime_type != "application/pdf":
                return (
                    False,
                    None,
                    f"Invalid MIME type for PDF: {mime_type}"
                )
        return True, FileType.PDF, None

    # Unsupported format
    return (
        False,
        None,
        f"Unsupported file format: .{extension}. "
        f"Supported formats: video (mp4, webm), PDF (pdf)"
    )


def validate_file_size(file_size: int, file_type: FileType) -> Tuple[bool, Optional[str], Optional[dict]]:
    """
    Validate file size against limits.

    Args:
        file_size: Size in bytes
        file_type: Type of file (video or pdf)

    Returns:
        Tuple of (is_valid, error_message, details)
    """
    if file_type == FileType.VIDEO:
        max_size = VIDEO_MAX_SIZE
        max_size_mb = 500
        if file_size > max_size:
            return (
                False,
                f"Video file too large (max {max_size_mb}MB)",
                {
                    "max_size": max_size,
                    "actual_size": file_size,
                    "max_size_mb": max_size_mb
                }
            )
    elif file_type == FileType.PDF:
        max_size = PDF_MAX_SIZE
        max_size_mb = 50
        if file_size > max_size:
            return (
                False,
                f"PDF file too large (max {max_size_mb}MB)",
                {
                    "max_size": max_size,
                    "actual_size": file_size,
                    "max_size_mb": max_size_mb
                }
            )

    return True, None, None


def validate_upload_file(file: UploadFile) -> ValidationResult:
    """
    Perform comprehensive validation on an uploaded file.

    Args:
        file: FastAPI UploadFile object

    Returns:
        ValidationResult with validation status and details
    """
    # Check if file is empty
    if not file.filename:
        return ValidationResult(
            is_valid=False,
            error_code=ValidationErrorCode.FILE_EMPTY,
            error_message="No file provided",
            details={}
        )

    # Detect MIME type
    mime_type, _ = detect_mime_type(file)

    # Validate file type
    is_valid_type, file_type, type_error = validate_file_type(
        file.filename,
        mime_type
    )

    if not is_valid_type:
        return ValidationResult(
            is_valid=False,
            error_code=ValidationErrorCode.UNSUPPORTED_FORMAT,
            error_message=type_error,
            details={
                "filename": file.filename,
                "detected_mime": mime_type,
                "supported_formats": {
                    "video": list(ALLOWED_VIDEO_EXTENSIONS),
                    "pdf": list(ALLOWED_PDF_EXTENSIONS)
                }
            }
        )

    # Get file size
    # For UploadFile, we need to read content to determine size
    # The actual size validation happens in the upload endpoint
    # Here we just validate the extension and MIME type
    extension = get_file_extension(file.filename)

    return ValidationResult(
        is_valid=True,
        file_type=file_type,
        extension=extension,
        mime_type=mime_type
    )


def validate_file_with_size(
    file: UploadFile,
    file_size: int
) -> ValidationResult:
    """
    Validate uploaded file including size check.

    Args:
        file: FastAPI UploadFile object
        file_size: File size in bytes

    Returns:
        ValidationResult with validation status and details
    """
    # First validate type
    result = validate_upload_file(file)

    if not result.is_valid:
        return result

    # Validate size
    is_valid_size, size_error, size_details = validate_file_size(
        file_size,
        result.file_type
    )

    if not is_valid_size:
        return ValidationResult(
            is_valid=False,
            error_code=ValidationErrorCode.FILE_TOO_LARGE,
            error_message=size_error,
            details=size_details
        )

    return result


def raise_validation_error(result: ValidationResult) -> None:
    """
    Raise HTTPException from validation result.

    Args:
        result: Failed validation result

    Raises:
        HTTPException: With appropriate status code and error format
    """
    status_code = status.HTTP_400_BAD_REQUEST

    if result.error_code == ValidationErrorCode.FILE_TOO_LARGE:
        status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE

    raise HTTPException(
        status_code=status_code,
        detail={
            "error": {
                "code": result.error_code,
                "message": result.error_message,
                "details": result.details or {}
            }
        }
    )


def get_content_type(file_type: FileType, extension: str) -> str:
    """
    Get the appropriate content type for a file.

    Args:
        file_type: Type of file
        extension: File extension

    Returns:
        str: MIME content type
    """
    if file_type == FileType.VIDEO:
        if extension == "mp4":
            return "video/mp4"
        elif extension == "webm":
            return "video/webm"
        return "video/mp4"
    elif file_type == FileType.PDF:
        return "application/pdf"
    return "application/octet-stream"
