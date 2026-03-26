"""
Thumbnail Generation Service Module

Provides asynchronous thumbnail generation for videos and PDFs.
Supports video frame extraction using ffmpeg and PDF page rendering using pdf2image.
Handles uploading generated thumbnails to MinIO and updating database records.
"""

import asyncio
import io
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image

from app.config import settings
from app.core.storage import get_minio_client
from app.crud.material import update_material_thumbnail
from app.database import SessionLocal
from app.models.material import MaterialType
from app.services.office_converter import convert_office_to_pdf

# Configure logger
logger = logging.getLogger(__name__)

# Thumbnail generation settings
THUMBNAIL_WIDTH = 480
THUMBNAIL_QUALITY = 80  # JPEG quality (0-100)
PDF_DPI = 150
VIDEO_SEEK_TIME = "00:00:01"  # Capture frame at 1 second to avoid black frames

# Placeholder path (relative to static files)
PLACEHOLDER_THUMBNAIL_PATH = "thumbnails/placeholder.png"


class ThumbnailGenerationError(Exception):
    """Exception raised when thumbnail generation fails."""
    pass


def generate_video_thumbnail(video_path: str, output_path: str) -> bool:
    """
    Generate thumbnail from video using ffmpeg.

    Extracts a frame at 1 second into the video, scales to 480px width
    while maintaining aspect ratio, and saves as JPEG with quality 80%.

    Args:
        video_path: Path to input video file
        output_path: Path for output thumbnail (JPEG)

    Returns:
        bool: True if successful, False otherwise

    Raises:
        ThumbnailGenerationError: If ffmpeg fails or output is invalid
    """
    try:
        # Build ffmpeg command
        # -ss: seek to specified time
        # -vframes 1: extract only one frame
        # -q:v 2: quality (2-31, lower is better, 2 is high quality)
        # -vf: video filter for scaling
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output file if exists
            "-i", video_path,
            "-ss", VIDEO_SEEK_TIME,
            "-vframes", "1",
            "-q:v", "2",
            "-vf", f"scale={THUMBNAIL_WIDTH}:-1",
            "-f", "image2",
            output_path
        ]

        logger.debug(f"Running ffmpeg command: {' '.join(cmd)}")

        # Run ffmpeg with timeout
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout
        )

        if result.returncode != 0:
            logger.error(f"ffmpeg failed: {result.stderr}")
            raise ThumbnailGenerationError(f"ffmpeg failed: {result.stderr}")

        # Verify output file exists and has content
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise ThumbnailGenerationError("ffmpeg produced no output")

        # Optimize the image with PIL
        _optimize_image(output_path)

        logger.info(f"Video thumbnail generated: {output_path}")
        return True

    except subprocess.TimeoutExpired:
        logger.error("ffmpeg timed out after 60 seconds")
        raise ThumbnailGenerationError("Video processing timed out")
    except Exception as e:
        logger.error(f"Video thumbnail generation failed: {e}")
        raise ThumbnailGenerationError(f"Video thumbnail generation failed: {e}")


def generate_pdf_thumbnail(pdf_path: str, output_path: str) -> bool:
    """
    Generate thumbnail from PDF using pdf2image.

    Renders the first page at 150 DPI and saves as JPEG.

    Args:
        pdf_path: Path to input PDF file
        output_path: Path for output thumbnail (JPEG)

    Returns:
        bool: True if successful, False otherwise

    Raises:
        ThumbnailGenerationError: If pdf2image fails or output is invalid
    """
    try:
        # Import pdf2image here to handle cases where it's not installed
        try:
            from pdf2image import convert_from_path
        except ImportError:
            logger.error("pdf2image not installed")
            raise ThumbnailGenerationError("pdf2image library not available")

        logger.debug(f"Converting PDF to image: {pdf_path}")

        # Convert first page to image
        images = convert_from_path(
            pdf_path,
            first_page=1,
            last_page=1,
            dpi=PDF_DPI,
            fmt="jpeg"
        )

        if not images:
            raise ThumbnailGenerationError("pdf2image produced no output")

        # Get the first (and only) image
        image = images[0]

        # Resize to target width while maintaining aspect ratio
        width, height = image.size
        if width > THUMBNAIL_WIDTH:
            ratio = THUMBNAIL_WIDTH / width
            new_height = int(height * ratio)
            image = image.resize((THUMBNAIL_WIDTH, new_height), Image.Resampling.LANCZOS)

        # Save with specified quality
        image.save(output_path, "JPEG", quality=THUMBNAIL_QUALITY, optimize=True)

        logger.info(f"PDF thumbnail generated: {output_path}")
        return True

    except Exception as e:
        logger.error(f"PDF thumbnail generation failed: {e}")
        raise ThumbnailGenerationError(f"PDF thumbnail generation failed: {e}")


def _optimize_image(image_path: str) -> None:
    """
    Optimize an image file using PIL.

    Re-saves the image with specified quality settings to reduce file size.

    Args:
        image_path: Path to image file to optimize
    """
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (for PNG with transparency)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            # Resize if wider than target
            width, height = img.size
            if width > THUMBNAIL_WIDTH:
                ratio = THUMBNAIL_WIDTH / width
                new_height = int(height * ratio)
                img = img.resize((THUMBNAIL_WIDTH, new_height), Image.Resampling.LANCZOS)

            # Save with optimization
            img.save(image_path, "JPEG", quality=THUMBNAIL_QUALITY, optimize=True)

    except Exception as e:
        logger.warning(f"Image optimization failed (non-critical): {e}")
        # Don't raise - this is an optimization, not critical


def download_file_from_minio(object_name: str, local_path: str) -> bool:
    """
    Download a file from MinIO to local storage.

    Args:
        object_name: Object path in MinIO
        local_path: Local path to save file

    Returns:
        bool: True if successful

    Raises:
        ThumbnailGenerationError: If download fails
    """
    try:
        minio_client = get_minio_client()

        # Ensure directory exists
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        # Download file
        minio_client.client.fget_object(
            bucket_name=minio_client.bucket_name,
            object_name=object_name,
            file_path=local_path
        )

        logger.debug(f"Downloaded {object_name} to {local_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to download file from MinIO: {e}")
        raise ThumbnailGenerationError(f"Failed to download file: {e}")


def upload_thumbnail_to_minio(
    local_path: str,
    object_name: str
) -> str:
    """
    Upload a thumbnail file to MinIO.

    Args:
        local_path: Local path to thumbnail file
        object_name: Target object name in MinIO

    Returns:
        str: Object name in MinIO

    Raises:
        ThumbnailGenerationError: If upload fails
    """
    try:
        minio_client = get_minio_client()
        file_size = os.path.getsize(local_path)

        with open(local_path, "rb") as f:
            minio_client.upload_file_stream(
                file_stream=f,
                object_name=object_name,
                content_type="image/jpeg",
                file_size=file_size
            )

        logger.info(f"Uploaded thumbnail to {object_name}")
        return object_name

    except Exception as e:
        logger.error(f"Failed to upload thumbnail to MinIO: {e}")
        raise ThumbnailGenerationError(f"Failed to upload thumbnail: {e}")


def generate_thumbnail(
    material_id: int,
    user_id: int,
    file_path: str,
    file_type: MaterialType
) -> Optional[str]:
    """
    Generate thumbnail for a material and upload to MinIO.

    This is the main entry point for thumbnail generation. It:
    1. Downloads the file from MinIO
    2. Generates the appropriate thumbnail type
    3. Uploads the thumbnail to MinIO
    4. Returns the thumbnail path

    Args:
        material_id: ID of the material
        user_id: ID of the user who uploaded the material
        file_path: Path to file in MinIO
        file_type: Type of material (video or pdf)

    Returns:
        str: Path to thumbnail in MinIO, or None if generation fails
    """
    temp_dir = None
    local_file_path = None
    thumbnail_path = None

    try:
        # Create temporary directory for processing
        temp_dir = tempfile.mkdtemp(prefix=f"thumb_{material_id}_")

        # Generate paths
        file_extension = Path(file_path).suffix
        local_file_path = os.path.join(temp_dir, f"source{file_extension}")
        local_thumbnail_path = os.path.join(temp_dir, "thumbnail.jpg")

        # Generate thumbnail object name
        thumbnail_object_name = f"thumbnails/{user_id}/{material_id}.jpg"

        logger.info(
            f"Starting thumbnail generation for material {material_id}, "
            f"type: {file_type.value}"
        )

        # Step 1: Download file from MinIO
        download_file_from_minio(file_path, local_file_path)

        # Step 2: Generate thumbnail based on file type
        if file_type == MaterialType.VIDEO:
            generate_video_thumbnail(local_file_path, local_thumbnail_path)
        elif file_type == MaterialType.PDF:
            generate_pdf_thumbnail(local_file_path, local_thumbnail_path)
        elif file_type in (MaterialType.PPTX, MaterialType.DOCX, MaterialType.XLSX):
            # For Office files, convert to PDF first, then generate thumbnail
            logger.info(f"Processing Office file for thumbnail: {material_id}, type: {file_type.value}")
            try:
                # Convert Office file to PDF
                pdf_path = asyncio.run(convert_office_to_pdf(local_file_path, material_id, user_id))
                if pdf_path and os.path.exists(pdf_path):
                    # Generate thumbnail from the converted PDF
                    generate_pdf_thumbnail(pdf_path, local_thumbnail_path)
                    # Clean up the converted PDF
                    try:
                        os.remove(pdf_path)
                    except OSError:
                        pass
                else:
                    logger.warning(f"Office to PDF conversion failed for material {material_id}")
                    return None
            except Exception as e:
                logger.error(f"Failed to generate thumbnail for Office file {material_id}: {e}")
                return None
        else:
            logger.warning(f"Unsupported file type for thumbnail: {file_type}")
            return None

        # Step 3: Upload thumbnail to MinIO
        thumbnail_path = upload_thumbnail_to_minio(
            local_thumbnail_path,
            thumbnail_object_name
        )

        logger.info(
            f"Thumbnail generation completed for material {material_id}: "
            f"{thumbnail_path}"
        )

        return thumbnail_path

    except ThumbnailGenerationError as e:
        logger.error(f"Thumbnail generation failed for material {material_id}: {e}")
        return None
    except Exception as e:
        logger.error(
            f"Unexpected error during thumbnail generation for material {material_id}: {e}",
            exc_info=True
        )
        return None
    finally:
        # Cleanup temporary files
        if local_file_path and os.path.exists(local_file_path):
            try:
                os.remove(local_file_path)
            except OSError:
                pass

        if thumbnail_path and os.path.exists(os.path.join(temp_dir or "", "thumbnail.jpg")):
            try:
                os.remove(os.path.join(temp_dir, "thumbnail.jpg"))
            except OSError:
                pass

        if temp_dir and os.path.exists(temp_dir):
            try:
                os.rmdir(temp_dir)
            except OSError:
                pass


def process_thumbnail_generation(
    material_id: int,
    user_id: int,
    file_path: str,
    file_type: MaterialType
) -> None:
    """
    Process thumbnail generation and update database.

    This function is designed to be called as a background task.
    It handles the entire workflow including database updates.

    Args:
        material_id: ID of the material
        user_id: ID of the user who uploaded the material
        file_path: Path to file in MinIO
        file_type: Type of material
    """
    db = None

    try:
        # Generate thumbnail
        thumbnail_path = generate_thumbnail(
            material_id=material_id,
            user_id=user_id,
            file_path=file_path,
            file_type=file_type
        )

        # Update database with thumbnail path
        db = SessionLocal()

        from app.crud.material import get_material_by_id

        material = get_material_by_id(db, material_id)
        if not material:
            logger.error(f"Material {material_id} not found for thumbnail update")
            return

        if thumbnail_path:
            # Update with generated thumbnail
            update_material_thumbnail(db, material, thumbnail_path)
            logger.info(f"Updated material {material_id} with thumbnail: {thumbnail_path}")
        else:
            # Use placeholder thumbnail on failure
            # The placeholder should be pre-uploaded to MinIO
            placeholder_path = PLACEHOLDER_THUMBNAIL_PATH
            update_material_thumbnail(db, material, placeholder_path)
            logger.info(f"Updated material {material_id} with placeholder thumbnail")

    except Exception as e:
        logger.error(f"Failed to process thumbnail generation: {e}", exc_info=True)
    finally:
        if db:
            db.close()


def get_placeholder_thumbnail_data() -> bytes:
    """
    Generate a simple placeholder thumbnail image.

    Creates a simple gray image with text as a fallback when
    thumbnail generation fails.

    Returns:
        bytes: PNG image data
    """
    try:
        # Create a simple gray placeholder image
        width, height = THUMBNAIL_WIDTH, int(THUMBNAIL_WIDTH * 0.75)

        img = Image.new('RGB', (width, height), color='#CCCCCC')

        # Add some visual indication it's a placeholder
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)

        # Try to draw text (may fail if no fonts available)
        try:
            text = "No Preview"
            # Use default font
            bbox = draw.textbbox((0, 0), text)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            position = ((width - text_width) // 2, (height - text_height) // 2)
            draw.text(position, text, fill='#666666')
        except Exception:
            # If text rendering fails, just use the plain gray image
            pass

        # Save to bytes
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()

    except Exception as e:
        logger.error(f"Failed to generate placeholder: {e}")
        # Return minimal valid PNG as last resort
        return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'


def ensure_placeholder_thumbnail() -> str:
    """
    Ensure the placeholder thumbnail exists in MinIO.

    Creates and uploads a placeholder thumbnail if it doesn't exist.

    Returns:
        str: Path to placeholder thumbnail in MinIO
    """
    try:
        minio_client = get_minio_client()

        # Check if placeholder exists
        if minio_client.file_exists(PLACEHOLDER_THUMBNAIL_PATH):
            return PLACEHOLDER_THUMBNAIL_PATH

        # Generate and upload placeholder
        placeholder_data = get_placeholder_thumbnail_data()
        minio_client.upload_file_bytes(
            data=placeholder_data,
            object_name=PLACEHOLDER_THUMBNAIL_PATH,
            content_type="image/png"
        )

        logger.info(f"Created placeholder thumbnail at {PLACEHOLDER_THUMBNAIL_PATH}")
        return PLACEHOLDER_THUMBNAIL_PATH

    except Exception as e:
        logger.error(f"Failed to ensure placeholder thumbnail: {e}")
        return PLACEHOLDER_THUMBNAIL_PATH
