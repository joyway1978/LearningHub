"""
Tests for Office to PDF Converter Service

Tests cover:
- Successful conversion
- Timeout handling
- LibreOffice not installed
- Corrupted file handling
- Invalid file formats
- MinIO download/upload failures
"""

import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

from app.services.office_converter import (
    convert_office_to_pdf,
    ConversionError,
    ConversionTimeoutError,
    CorruptedFileError,
    LibreOfficeNotInstalledError,
    _check_libreoffice_installed,
    _build_libreoffice_command,
    _is_valid_office_file,
    _run_conversion_sync,
    _get_office_file_type,
    get_converted_pdf_path,
    check_converted_pdf_exists,
    CONVERSION_TIMEOUT,
    LIBREOFFICE_CMD,
)
from app.models.material import MaterialType


class TestCheckLibreOfficeInstalled:
    """Tests for _check_libreoffice_installed function."""

    def test_returns_true_when_installed(self):
        """Should return True when LibreOffice is installed."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = "/usr/bin/soffice"
            assert _check_libreoffice_installed() is True
            mock_which.assert_called_once_with(LIBREOFFICE_CMD)

    def test_returns_false_when_not_installed(self):
        """Should return False when LibreOffice is not installed."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = None
            assert _check_libreoffice_installed() is False
            mock_which.assert_called_once_with(LIBREOFFICE_CMD)


class TestIsValidOfficeFile:
    """Tests for _is_valid_office_file function."""

    def test_valid_pptx_file(self):
        """Should return True for .pptx files."""
        assert _is_valid_office_file("/path/to/file.pptx") is True
        assert _is_valid_office_file("/path/to/file.PPTX") is True

    def test_valid_docx_file(self):
        """Should return True for .docx files."""
        assert _is_valid_office_file("/path/to/file.docx") is True
        assert _is_valid_office_file("/path/to/file.DOCX") is True

    def test_valid_xlsx_file(self):
        """Should return True for .xlsx files."""
        assert _is_valid_office_file("/path/to/file.xlsx") is True
        assert _is_valid_office_file("/path/to/file.XLSX") is True

    def test_invalid_file_formats(self):
        """Should return False for non-office file formats."""
        assert _is_valid_office_file("/path/to/file.pdf") is False
        assert _is_valid_office_file("/path/to/file.mp4") is False
        assert _is_valid_office_file("/path/to/file.txt") is False
        assert _is_valid_office_file("/path/to/file.ppt") is False  # Old format
        assert _is_valid_office_file("/path/to/file.doc") is False  # Old format


class TestGetOfficeFileType:
    """Tests for _get_office_file_type function."""

    def test_pptx_returns_pptx_type(self):
        """Should return PPTX type for .pptx files."""
        assert _get_office_file_type("/path/to/file.pptx") == MaterialType.PPTX
        assert _get_office_file_type("/path/to/file.PPTX") == MaterialType.PPTX

    def test_docx_returns_docx_type(self):
        """Should return DOCX type for .docx files."""
        assert _get_office_file_type("/path/to/file.docx") == MaterialType.DOCX
        assert _get_office_file_type("/path/to/file.DOCX") == MaterialType.DOCX

    def test_xlsx_returns_xlsx_type(self):
        """Should return XLSX type for .xlsx files."""
        assert _get_office_file_type("/path/to/file.xlsx") == MaterialType.XLSX
        assert _get_office_file_type("/path/to/file.XLSX") == MaterialType.XLSX

    def test_invalid_extension_raises_error(self):
        """Should raise ConversionError for unsupported extensions."""
        with pytest.raises(ConversionError) as exc_info:
            _get_office_file_type("/path/to/file.pdf")

        assert "Unsupported office file format" in str(exc_info.value)
        assert ".pdf" in str(exc_info.value.details.get("actual_format"))


class TestBuildLibreOfficeCommand:
    """Tests for _build_libreoffice_command function."""

    def test_command_structure(self):
        """Should build correct LibreOffice command."""
        input_path = "/tmp/input.pptx"
        output_dir = "/tmp/output"

        cmd = _build_libreoffice_command(input_path, output_dir)

        assert cmd[0] == LIBREOFFICE_CMD
        assert "--headless" in cmd
        assert "--convert-to" in cmd
        assert "pdf" in cmd
        assert "--outdir" in cmd
        assert output_dir in cmd
        assert "--norestore" in cmd
        assert "--nolockcheck" in cmd
        assert "--nologo" in cmd
        assert input_path in cmd

    def test_command_order(self):
        """Should have correct command argument order."""
        input_path = "/tmp/input.pptx"
        output_dir = "/tmp/output"

        cmd = _build_libreoffice_command(input_path, output_dir)

        # Input file should be the last argument
        assert cmd[-1] == input_path
        # Output dir should follow --outdir
        outdir_idx = cmd.index("--outdir")
        assert cmd[outdir_idx + 1] == output_dir


class TestRunConversionSync:
    """Tests for _run_conversion_sync function."""

    def test_raises_error_when_libreoffice_not_installed(self):
        """Should raise LibreOfficeNotInstalledError when soffice not found."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = None

            with pytest.raises(LibreOfficeNotInstalledError) as exc_info:
                _run_conversion_sync("/tmp/input.pptx", "/tmp/output")

            assert "not installed" in str(exc_info.value).lower()
            assert LIBREOFFICE_CMD in str(exc_info.value)

    def test_raises_error_when_input_file_not_found(self):
        """Should raise ConversionError when input file doesn't exist."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = "/usr/bin/soffice"

            with pytest.raises(ConversionError) as exc_info:
                _run_conversion_sync("/nonexistent/file.pptx", "/tmp/output")

            assert "not found" in str(exc_info.value).lower()

    def test_raises_error_when_input_file_is_empty(self):
        """Should raise CorruptedFileError when input file is empty."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = "/usr/bin/soffice"

            with tempfile.NamedTemporaryFile(mode='w', suffix='.pptx', delete=False) as f:
                f.write("")  # Empty file
                temp_path = f.name

            try:
                with pytest.raises(CorruptedFileError) as exc_info:
                    _run_conversion_sync(temp_path, "/tmp/output")

                assert "empty" in str(exc_info.value).lower()
            finally:
                os.unlink(temp_path)

    def test_successful_conversion(self):
        """Should successfully convert file and return PDF path."""
        with patch('shutil.which') as mock_which, \
             patch('subprocess.run') as mock_run:

            mock_which.return_value = "/usr/bin/soffice"
            mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")

            with tempfile.TemporaryDirectory() as temp_dir:
                # Create a dummy input file
                input_path = os.path.join(temp_dir, "input.pptx")
                with open(input_path, 'w') as f:
                    f.write("dummy content")

                # Create expected output file (LibreOffice would create this)
                output_dir = os.path.join(temp_dir, "output")
                os.makedirs(output_dir, exist_ok=True)
                expected_pdf = os.path.join(output_dir, "input.pdf")
                with open(expected_pdf, 'w') as f:
                    f.write("PDF content")

                result = _run_conversion_sync(input_path, output_dir)

                assert result == expected_pdf
                mock_run.assert_called_once()
                # Verify timeout is set correctly
                call_kwargs = mock_run.call_args[1]
                assert call_kwargs['timeout'] == CONVERSION_TIMEOUT

    def test_conversion_failure(self):
        """Should raise ConversionError when LibreOffice returns non-zero."""
        with patch('shutil.which') as mock_which, \
             patch('subprocess.run') as mock_run:

            mock_which.return_value = "/usr/bin/soffice"
            mock_run.return_value = MagicMock(
                returncode=1,
                stderr="Conversion failed",
                stdout=""
            )

            with tempfile.TemporaryDirectory() as temp_dir:
                input_path = os.path.join(temp_dir, "input.pptx")
                with open(input_path, 'w') as f:
                    f.write("dummy content")

                with pytest.raises(ConversionError) as exc_info:
                    _run_conversion_sync(input_path, temp_dir)

                assert "failed" in str(exc_info.value).lower() or "conversion" in str(exc_info.value).lower()

    def test_corrupted_file_detection(self):
        """Should raise CorruptedFileError when LibreOffice reports corruption."""
        with patch('shutil.which') as mock_which, \
             patch('subprocess.run') as mock_run:

            mock_which.return_value = "/usr/bin/soffice"
            mock_run.return_value = MagicMock(
                returncode=1,
                stderr="The file appears to be corrupt",
                stdout=""
            )

            with tempfile.TemporaryDirectory() as temp_dir:
                input_path = os.path.join(temp_dir, "input.pptx")
                with open(input_path, 'w') as f:
                    f.write("dummy content")

                with pytest.raises(CorruptedFileError) as exc_info:
                    _run_conversion_sync(input_path, temp_dir)

                assert "corrupted" in str(exc_info.value).lower()

    def test_timeout_handling(self):
        """Should raise ConversionTimeoutError when subprocess times out."""
        with patch('shutil.which') as mock_which, \
             patch('subprocess.run') as mock_run:

            mock_which.return_value = "/usr/bin/soffice"
            mock_run.side_effect = subprocess.TimeoutExpired(cmd=["soffice"], timeout=60)

            with tempfile.TemporaryDirectory() as temp_dir:
                input_path = os.path.join(temp_dir, "input.pptx")
                with open(input_path, 'w') as f:
                    f.write("dummy content")

                with pytest.raises(ConversionTimeoutError) as exc_info:
                    _run_conversion_sync(input_path, temp_dir)

                assert "timed out" in str(exc_info.value).lower() or "timeout" in str(exc_info.value).lower()
                assert exc_info.value.details.get("timeout") == CONVERSION_TIMEOUT

    def test_empty_pdf_output_detection(self):
        """Should raise ConversionError when output PDF is empty."""
        with patch('shutil.which') as mock_which, \
             patch('subprocess.run') as mock_run:

            mock_which.return_value = "/usr/bin/soffice"
            mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")

            with tempfile.TemporaryDirectory() as temp_dir:
                input_path = os.path.join(temp_dir, "input.pptx")
                with open(input_path, 'w') as f:
                    f.write("dummy content")

                # Create empty output PDF
                output_dir = os.path.join(temp_dir, "output")
                os.makedirs(output_dir, exist_ok=True)
                expected_pdf = os.path.join(output_dir, "input.pdf")
                with open(expected_pdf, 'w') as f:
                    pass  # Empty file

                with pytest.raises(ConversionError) as exc_info:
                    _run_conversion_sync(input_path, output_dir)

                assert "empty" in str(exc_info.value).lower()


class TestConvertOfficeToPdf:
    """Tests for convert_office_to_pdf async function."""

    @pytest.mark.asyncio
    async def test_successful_conversion(self):
        """Should successfully convert office file to PDF."""
        with patch('app.services.office_converter._check_libreoffice_installed') as mock_check, \
             patch('app.services.office_converter._download_from_minio') as mock_download, \
             patch('app.services.office_converter._upload_to_minio') as mock_upload, \
             patch('app.services.office_converter._run_conversion_sync') as mock_convert, \
             patch('tempfile.mkdtemp') as mock_mkdtemp:

            mock_check.return_value = True
            mock_mkdtemp.return_value = "/tmp/office_conv_123"
            mock_convert.return_value = "/tmp/office_conv_123/input.pdf"
            mock_upload.return_value = "converted/123.pdf"

            result = await convert_office_to_pdf(
                source_path="materials/1/input.pptx",
                material_id=123,
                user_id=1
            )

            assert result == "converted/123.pdf"
            mock_download.assert_called_once()
            mock_convert.assert_called_once()
            mock_upload.assert_called_once()

    @pytest.mark.asyncio
    async def test_libreoffice_not_installed(self):
        """Should raise LibreOfficeNotInstalledError."""
        with patch('app.services.office_converter._check_libreoffice_installed') as mock_check, \
             patch('app.services.office_converter._download_from_minio') as mock_download, \
             patch('tempfile.mkdtemp') as mock_mkdtemp:

            mock_check.return_value = False
            mock_mkdtemp.return_value = "/tmp/office_conv_123"

            with pytest.raises(LibreOfficeNotInstalledError):
                await convert_office_to_pdf(
                    source_path="materials/1/input.pptx",
                    material_id=123,
                    user_id=1
                )

    @pytest.mark.asyncio
    async def test_invalid_file_format(self):
        """Should raise ConversionError for invalid file format."""
        with patch('app.services.office_converter._check_libreoffice_installed') as mock_check, \
             patch('app.services.office_converter._download_from_minio') as mock_download, \
             patch('tempfile.mkdtemp') as mock_mkdtemp:

            mock_check.return_value = True
            mock_mkdtemp.return_value = "/tmp/office_conv_123"

            with pytest.raises(ConversionError) as exc_info:
                await convert_office_to_pdf(
                    source_path="materials/1/input.pdf",  # Not an office file
                    material_id=123,
                    user_id=1
                )

            assert "Invalid office file format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_conversion_timeout(self):
        """Should raise ConversionTimeoutError on timeout."""
        with patch('app.services.office_converter._check_libreoffice_installed') as mock_check, \
             patch('app.services.office_converter._download_from_minio') as mock_download, \
             patch('app.services.office_converter._run_conversion_sync') as mock_convert, \
             patch('tempfile.mkdtemp') as mock_mkdtemp:

            mock_check.return_value = True
            mock_mkdtemp.return_value = "/tmp/office_conv_123"
            mock_convert.side_effect = ConversionTimeoutError("Timeout")

            with pytest.raises(ConversionTimeoutError):
                await convert_office_to_pdf(
                    source_path="materials/1/input.pptx",
                    material_id=123,
                    user_id=1
                )

    @pytest.mark.asyncio
    async def test_corrupted_file(self):
        """Should raise CorruptedFileError for corrupted files."""
        with patch('app.services.office_converter._check_libreoffice_installed') as mock_check, \
             patch('app.services.office_converter._download_from_minio') as mock_download, \
             patch('app.services.office_converter._run_conversion_sync') as mock_convert, \
             patch('tempfile.mkdtemp') as mock_mkdtemp:

            mock_check.return_value = True
            mock_mkdtemp.return_value = "/tmp/office_conv_123"
            mock_convert.side_effect = CorruptedFileError("Corrupted")

            with pytest.raises(CorruptedFileError):
                await convert_office_to_pdf(
                    source_path="materials/1/input.pptx",
                    material_id=123,
                    user_id=1
                )

    @pytest.mark.asyncio
    async def test_download_failure(self):
        """Should raise ConversionError when download fails."""
        with patch('app.services.office_converter._check_libreoffice_installed') as mock_check, \
             patch('app.services.office_converter._download_from_minio') as mock_download, \
             patch('tempfile.mkdtemp') as mock_mkdtemp:

            mock_check.return_value = True
            mock_mkdtemp.return_value = "/tmp/office_conv_123"
            mock_download.side_effect = ConversionError("Download failed")

            with pytest.raises(ConversionError):
                await convert_office_to_pdf(
                    source_path="materials/1/input.pptx",
                    material_id=123,
                    user_id=1
                )

    @pytest.mark.asyncio
    async def test_upload_failure(self):
        """Should raise ConversionError when upload fails."""
        with patch('app.services.office_converter._check_libreoffice_installed') as mock_check, \
             patch('app.services.office_converter._download_from_minio') as mock_download, \
             patch('app.services.office_converter._run_conversion_sync') as mock_convert, \
             patch('app.services.office_converter._upload_to_minio') as mock_upload, \
             patch('tempfile.mkdtemp') as mock_mkdtemp:

            mock_check.return_value = True
            mock_mkdtemp.return_value = "/tmp/office_conv_123"
            mock_convert.return_value = "/tmp/office_conv_123/input.pdf"
            mock_upload.side_effect = ConversionError("Upload failed")

            with pytest.raises(ConversionError):
                await convert_office_to_pdf(
                    source_path="materials/1/input.pptx",
                    material_id=123,
                    user_id=1
                )


class TestGetConvertedPdfPath:
    """Tests for get_converted_pdf_path function."""

    def test_returns_correct_path(self):
        """Should return correct MinIO path for converted PDF."""
        assert get_converted_pdf_path(123) == "converted/123.pdf"
        assert get_converted_pdf_path(1) == "converted/1.pdf"
        assert get_converted_pdf_path(999999) == "converted/999999.pdf"


class TestCheckConvertedPdfExists:
    """Tests for check_converted_pdf_exists function."""

    def test_returns_true_when_file_exists(self):
        """Should return True when converted PDF exists."""
        with patch('app.services.office_converter.get_minio_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.file_exists.return_value = True
            mock_get_client.return_value = mock_client

            assert check_converted_pdf_exists(123) is True
            mock_client.file_exists.assert_called_once_with("converted/123.pdf")

    def test_returns_false_when_file_not_exists(self):
        """Should return False when converted PDF doesn't exist."""
        with patch('app.services.office_converter.get_minio_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.file_exists.return_value = False
            mock_get_client.return_value = mock_client

            assert check_converted_pdf_exists(123) is False

    def test_returns_false_on_error(self):
        """Should return False when MinIO check fails."""
        with patch('app.services.office_converter.get_minio_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.file_exists.side_effect = Exception("MinIO error")
            mock_get_client.return_value = mock_client

            assert check_converted_pdf_exists(123) is False


class TestConversionError:
    """Tests for ConversionError exception."""

    def test_error_with_message_only(self):
        """Should create error with just message."""
        error = ConversionError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.details == {}

    def test_error_with_details(self):
        """Should create error with message and details."""
        details = {"key": "value", "number": 42}
        error = ConversionError("Something went wrong", details)
        assert str(error) == "Something went wrong"
        assert error.details == details

    def test_error_inheritance(self):
        """Should be catchable as Exception."""
        error = ConversionError("Test")
        assert isinstance(error, Exception)


class TestSpecificErrors:
    """Tests for specific error types."""

    def test_libreoffice_not_installed_error_inheritance(self):
        """Should inherit from ConversionError."""
        error = LibreOfficeNotInstalledError("Not installed")
        assert isinstance(error, ConversionError)
        assert isinstance(error, Exception)

    def test_conversion_timeout_error_inheritance(self):
        """Should inherit from ConversionError."""
        error = ConversionTimeoutError("Timeout")
        assert isinstance(error, ConversionError)
        assert isinstance(error, Exception)

    def test_corrupted_file_error_inheritance(self):
        """Should inherit from ConversionError."""
        error = CorruptedFileError("Corrupted")
        assert isinstance(error, ConversionError)
        assert isinstance(error, Exception)


class TestConstants:
    """Tests for module constants."""

    def test_conversion_timeout_value(self):
        """Should have correct timeout value."""
        assert CONVERSION_TIMEOUT == 60

    def test_libreoffice_command(self):
        """Should use correct LibreOffice command."""
        assert LIBREOFFICE_CMD == "soffice"

    def test_supported_extensions(self):
        """Should support correct office formats."""
        from app.services.office_converter import SUPPORTED_OFFICE_EXTENSIONS
        assert ".pptx" in SUPPORTED_OFFICE_EXTENSIONS
        assert ".docx" in SUPPORTED_OFFICE_EXTENSIONS
        assert ".xlsx" in SUPPORTED_OFFICE_EXTENSIONS
        assert ".pdf" not in SUPPORTED_OFFICE_EXTENSIONS
