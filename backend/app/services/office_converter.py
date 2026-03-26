"""
Office to PDF Converter Service Module

Provides async Office to PDF conversion of files (PPTX, DOCX, XLSX) to PDF
using LibreOffice in headless mode. Handles downloading files from MinIO,
conversion, and uploading the converted PDF back to MinIO.
"""

import asyncio
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from app.core.storage import get_minio_client
from app.models.material import MaterialType

# Configure logger
logger = logging.getLogger(__name__)

# Conversion timeout in seconds
CONVERSION_TIMEOUT = 60

# Supported office file extensions
SUPPORTED_OFFICE_EXTENSIONS = {".pptx", ".docx", ".xlsx"}

# LibreOffice command
LIBREOFFICE_CMD = "soffice"


class ConversionError(Exception):
    """Exception raised when office file conversion fails."""

    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class LibreOfficeNotInstalledError(ConversionError):
    """Exception raised when LibreOffice is not installed."""
    pass


class ConversionTimeoutError(ConversionError):
    """Exception raised when conversion times out."""
    pass


class CorruptedFileError(ConversionError):
    """Exception raised when the source file is corrupted."""
    pass


def _check_libreoffice_installed() -> bool:
    """
    Check if LibreOffice is installed and accessible.

    Returns:
        bool: True if LibreOffice is installed, False otherwise
    """
    # Check local installation
    if shutil.which(LIBREOFFICE_CMD) is not None or shutil.which("libreoffice") is not None:
        return True

    # Check macOS installation path
    if os.path.exists("/Applications/LibreOffice.app/Contents/MacOS/soffice"):
        return True

    return False


def get_libreoffice_mode() -> tuple[str, str]:
    """
    Get the LibreOffice execution mode and command.

    Returns:
        tuple: (mode, command_path)
            - mode: "local"
            - command_path: path to soffice

    Raises:
        LibreOfficeNotInstalledError: If LibreOffice is not available
    """
    # Try 'soffice' first (standard command)
    cmd = shutil.which("soffice")
    if cmd:
        return ("local", cmd)

    # Try 'libreoffice' as fallback
    cmd = shutil.which("libreoffice")
    if cmd:
        return ("local", cmd)

    # Check common macOS installation path
    macos_path = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
    if os.path.exists(macos_path):
        return ("local", macos_path)

    raise LibreOfficeNotInstalledError(
        "LibreOffice is not installed. Please install it:\n"
        "  macOS: brew update && brew install --cask libreoffice-still\n"
        "  Ubuntu: sudo apt-get install libreoffice\n"
        "  CentOS: sudo yum install libreoffice"
    )


def get_libreoffice_cmd() -> str:
    """
    Get the LibreOffice command path.

    Returns:
        str: Path to LibreOffice command

    Raises:
        LibreOfficeNotInstalledError: If LibreOffice is not installed
    """
    _, cmd = get_libreoffice_mode()
    return cmd


def _get_office_file_type(file_path: str) -> MaterialType:
    """
    Determine the MaterialType based on file extension.

    Args:
        file_path: Path to the office file

    Returns:
        MaterialType: The type of office file

    Raises:
        ConversionError: If file extension is not supported
    """
    ext = Path(file_path).suffix.lower()

    type_map = {
        ".pptx": MaterialType.PPTX,
        ".docx": MaterialType.DOCX,
        ".xlsx": MaterialType.XLSX,
    }

    if ext not in type_map:
        raise ConversionError(
            f"Unsupported office file format: {ext}",
            {"supported_formats": list(type_map.keys()), "actual_format": ext}
        )

    return type_map[ext]


def _is_valid_office_file(file_path: str) -> bool:
    """
    Check if the file is a valid office file by extension.

    Args:
        file_path: Path to the file

    Returns:
        bool: True if valid office file, False otherwise
    """
    ext = Path(file_path).suffix.lower()
    return ext in SUPPORTED_OFFICE_EXTENSIONS


def _build_libreoffice_command(input_path: str, output_dir: str, libreoffice_cmd: str) -> list:
    """
    Build the LibreOffice command for PDF conversion.

    Args:
        input_path: Path to input office file
        output_dir: Directory for output PDF
        libreoffice_cmd: Path to LibreOffice command

    Returns:
        list: Command arguments for subprocess
    """
    return [
        libreoffice_cmd,
        "--headless",  # Run in headless mode (no GUI)
        "--convert-to", "pdf",  # Convert to PDF format
        "--outdir", output_dir,  # Output directory
        "--norestore",  # Don't restore documents from crash
        "--nolockcheck",  # Don't check for document locks
        "--nologo",  # Don't show startup logo
        input_path
    ]


def _run_conversion_sync(input_path: str, output_dir: str) -> str:
    """
    Run LibreOffice conversion synchronously.

    Args:
        input_path: Path to input office file
        output_dir: Directory for output PDF

    Returns:
        str: Path to the converted PDF file

    Raises:
        LibreOfficeNotInstalledError: If LibreOffice is not installed
        ConversionTimeoutError: If conversion times out
        CorruptedFileError: If the source file is corrupted
        ConversionError: For other conversion failures
    """
    # Get LibreOffice mode and command (will raise if not installed)
    mode, libreoffice_cmd = get_libreoffice_mode()

    # Validate input file exists
    if not os.path.exists(input_path):
        raise ConversionError(
            f"Input file not found: {input_path}",
            {"input_path": input_path}
        )

    # Validate input file is not empty
    if os.path.getsize(input_path) == 0:
        raise CorruptedFileError(
            "Input file is empty",
            {"input_path": input_path}
        )

    # Build command
    cmd = _build_libreoffice_command(input_path, output_dir, libreoffice_cmd)

    logger.debug(f"Running LibreOffice command: {' '.join(cmd)}")

    try:
        # Run conversion with timeout
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=CONVERSION_TIMEOUT
        )

        # Check for conversion errors
        if result.returncode != 0:
            stderr = result.stderr.lower()

            # Check for specific error patterns
            if "corrupt" in stderr or "damaged" in stderr:
                raise CorruptedFileError(
                    "The office file appears to be corrupted",
                    {"stderr": result.stderr, "returncode": result.returncode}
                )

            raise ConversionError(
                f"LibreOffice conversion failed with return code {result.returncode}",
                {"stderr": result.stderr, "stdout": result.stdout}
            )

        # Find the output PDF file
        input_filename = Path(input_path).stem
        output_path = os.path.join(output_dir, f"{input_filename}.pdf")

        # Verify output file exists
        if not os.path.exists(output_path):
            # LibreOffice might have named it differently, search for PDF files
            pdf_files = list(Path(output_dir).glob("*.pdf"))
            if not pdf_files:
                raise ConversionError(
                    "Conversion completed but PDF output file not found",
                    {"output_dir": output_dir, "expected_file": output_path}
                )
            output_path = str(pdf_files[0])

        # Verify output file has content
        if os.path.getsize(output_path) == 0:
            raise ConversionError(
                "Conversion produced an empty PDF file",
                {"output_path": output_path}
            )

        logger.info(f"Office file converted successfully: {output_path}")
        return output_path

    except subprocess.TimeoutExpired:
        logger.error(f"LibreOffice conversion timed out after {CONVERSION_TIMEOUT} seconds")
        raise ConversionTimeoutError(
            f"Conversion timed out after {CONVERSION_TIMEOUT} seconds",
            {"timeout": CONVERSION_TIMEOUT}
        )
    except (LibreOfficeNotInstalledError, CorruptedFileError, ConversionTimeoutError):
        raise
    except Exception as e:
        logger.error(f"Unexpected error during conversion: {e}")
        raise ConversionError(
            f"Unexpected error during conversion: {str(e)}",
            {"error_type": type(e).__name__}
        )


async def _download_from_minio(object_name: str, local_path: str) -> None:
    """
    Download a file from MinIO to local storage.

    Args:
        object_name: Object path in MinIO
        local_path: Local path to save file

    Raises:
        ConversionError: If download fails
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

    except Exception as e:
        logger.error(f"Failed to download file from MinIO: {e}")
        raise ConversionError(
            f"Failed to download source file: {str(e)}",
            {"object_name": object_name, "local_path": local_path}
        )


async def _upload_to_minio(local_path: str, object_name: str) -> str:
    """
    Upload a file to MinIO.

    Args:
        local_path: Local path to file
        object_name: Target object name in MinIO

    Returns:
        str: Object name in MinIO

    Raises:
        ConversionError: If upload fails
    """
    try:
        minio_client = get_minio_client()
        file_size = os.path.getsize(local_path)

        with open(local_path, "rb") as f:
            minio_client.upload_file_stream(
                file_stream=f,
                object_name=object_name,
                content_type="application/pdf",
                file_size=file_size
            )

        logger.info(f"Uploaded converted PDF to {object_name}")
        return object_name

    except Exception as e:
        logger.error(f"Failed to upload PDF to MinIO: {e}")
        raise ConversionError(
            f"Failed to upload converted PDF: {str(e)}",
            {"local_path": local_path, "object_name": object_name}
        )


async def convert_office_to_pdf(
    source_path: str,
    material_id: int,
    user_id: int
) -> str:
    """
    Convert Office file to PDF using LibreOffice.

    This function downloads the source file from MinIO, converts it to PDF
    using LibreOffice in headless mode, and uploads the converted PDF back
    to MinIO. The entire operation has a 60-second timeout.

    Args:
        source_path: Path to source Office file in MinIO (e.g., "materials/1/file.pptx")
        material_id: Material ID for naming converted file
        user_id: User ID for storage organization

    Returns:
        str: Path to converted PDF in MinIO (e.g., "converted/1/123.pdf")

    Raises:
        LibreOfficeNotInstalledError: If LibreOffice is not installed
        ConversionTimeoutError: If conversion times out (60 seconds)
        CorruptedFileError: If the source file is corrupted
        ConversionError: For other conversion failures
    """
    temp_dir = None
    local_source_path = None
    converted_pdf_path = None

    try:
        # Create temporary directory for processing
        temp_dir = tempfile.mkdtemp(prefix=f"office_conv_{material_id}_")

        # Generate local paths
        source_filename = Path(source_path).name
        local_source_path = os.path.join(temp_dir, source_filename)

        # Generate output object name with user_id for storage organization
        converted_object_name = f"converted/{user_id}/{material_id}.pdf"

        logger.info(
            f"Starting office conversion for material {material_id}, "
            f"source: {source_path}"
        )

        # Step 1: Download source file from MinIO
        await _download_from_minio(source_path, local_source_path)

        # Validate file type
        if not _is_valid_office_file(local_source_path):
            raise ConversionError(
                "Invalid office file format",
                {
                    "source_path": source_path,
                    "supported_formats": list(SUPPORTED_OFFICE_EXTENSIONS)
                }
            )

        # Step 2: Run conversion in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        converted_pdf_path = await loop.run_in_executor(
            None,  # Uses default executor
            _run_conversion_sync,
            local_source_path,
            temp_dir
        )

        # Step 3: Upload converted PDF to MinIO
        result_path = await _upload_to_minio(converted_pdf_path, converted_object_name)

        logger.info(
            f"Office conversion completed for material {material_id}: "
            f"{result_path}"
        )

        return result_path

    except (LibreOfficeNotInstalledError, ConversionTimeoutError, CorruptedFileError):
        # Re-raise specific exceptions
        raise
    except ConversionError:
        # Re-raise conversion errors
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error during office conversion for material {material_id}: {e}",
            exc_info=True
        )
        raise ConversionError(
            f"Unexpected error during conversion: {str(e)}",
            {"error_type": type(e).__name__}
        )
    finally:
        # Cleanup temporary files
        _cleanup_temp_files(temp_dir, local_source_path, converted_pdf_path)


def _cleanup_temp_files(
    temp_dir: Optional[str],
    local_source_path: Optional[str],
    converted_pdf_path: Optional[str]
) -> None:
    """
    Clean up temporary files created during conversion.

    Args:
        temp_dir: Temporary directory path
        local_source_path: Path to downloaded source file
        converted_pdf_path: Path to converted PDF file
    """
    files_to_remove = [
        local_source_path,
        converted_pdf_path
    ]

    for file_path in files_to_remove:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.debug(f"Removed temporary file: {file_path}")
            except OSError as e:
                logger.warning(f"Failed to remove temporary file {file_path}: {e}")

    if temp_dir and os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)
            logger.debug(f"Removed temporary directory: {temp_dir}")
        except OSError as e:
            logger.warning(f"Failed to remove temporary directory {temp_dir}: {e}")


def get_converted_pdf_path(material_id: int, user_id: int) -> str:
    """
    Get the expected path for a converted PDF in MinIO.

    Args:
        material_id: Material ID
        user_id: User ID for storage organization

    Returns:
        str: Path to converted PDF in MinIO
    """
    return f"converted/{user_id}/{material_id}.pdf"


def check_converted_pdf_exists(material_id: int, user_id: int) -> bool:
    """
    Check if a converted PDF already exists in MinIO.

    Args:
        material_id: Material ID
        user_id: User ID for storage organization

    Returns:
        bool: True if converted PDF exists, False otherwise
    """
    try:
        minio_client = get_minio_client()
        object_name = get_converted_pdf_path(material_id, user_id)
        return minio_client.file_exists(object_name)
    except Exception as e:
        logger.warning(f"Failed to check if converted PDF exists: {e}")
        return False
