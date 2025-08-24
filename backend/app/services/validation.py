"""
Validation services for the GPA Calculator application.
"""

from typing import Optional
from fastapi import UploadFile
from app.constants import (
    SUPPORTED_FILE_EXTENSIONS,
    SUPPORTED_MIME_TYPES,
    ERROR_MESSAGES,
    PDF_HEADER_SIGNATURE,
)
from app.config import Settings
from app.exceptions import FileError, ValidationError
from app.utils.logger import setup_logger

logger = setup_logger("validation")


class FileValidator:
    """Handles file validation operations."""

    def __init__(self, settings: Settings):
        """Initialize validator with settings."""
        self.settings = settings

    def validate_upload_file(self, file: UploadFile) -> None:
        """Validate uploaded file."""
        self._validate_filename(file.filename)
        self._validate_content_type(file.content_type)

    def validate_file_content(
        self, content: bytes, filename: Optional[str] = None
    ) -> None:
        """Validate file content after reading."""
        self._validate_file_size(len(content), filename)
        self._validate_pdf_content(content, filename)

    def _validate_filename(self, filename: Optional[str]) -> None:
        """Validate filename is present and has correct extension."""
        if not filename:
            logger.warning("Upload attempt with no filename")
            raise ValidationError(ERROR_MESSAGES["NO_FILE"])

        if not any(filename.lower().endswith(ext) for ext in SUPPORTED_FILE_EXTENSIONS):
            logger.warning("Invalid file extension: %s", filename)
            raise FileError(
                ERROR_MESSAGES["INVALID_FILE_TYPE"],
                f"Supported extensions: {', '.join(SUPPORTED_FILE_EXTENSIONS)}",
            )

    def _validate_content_type(self, content_type: Optional[str]) -> None:
        """Validate MIME type if provided."""
        if content_type and not any(
            content_type.startswith(mime) for mime in SUPPORTED_MIME_TYPES
        ):
            logger.warning("Invalid content type: %s", content_type)
            raise FileError(
                ERROR_MESSAGES["INVALID_FILE_TYPE"],
                f"Supported types: {', '.join(SUPPORTED_MIME_TYPES)}",
            )

    def _validate_file_size(self, size: int, filename: Optional[str] = None) -> None:
        """Validate file size is within limits."""
        if size == 0:
            logger.warning("Empty file uploaded: %s", filename)
            raise ValidationError(ERROR_MESSAGES["EMPTY_FILE"])

        if size > self.settings.max_file_size_bytes:
            logger.warning("File too large: %s bytes, file: %s", size, filename)
            raise FileError(
                f"{ERROR_MESSAGES['FILE_TOO_LARGE']} ({self.settings.max_file_size_mb}MB)",
                f"File size: {size} bytes",
            )

    def _validate_pdf_content(
        self, content: bytes, filename: Optional[str] = None
    ) -> None:
        """Validate PDF content structure."""
        if not content.startswith(PDF_HEADER_SIGNATURE):
            logger.warning("Invalid PDF header: %s", filename)
            raise FileError(
                ERROR_MESSAGES["CORRUPTED_PDF"],
                f"Missing PDF signature in file: {filename}",
            )


class RequestValidator:
    """Handles HTTP request validation."""

    def __init__(self, settings: Settings):
        """Initialize validator with settings."""
        self.settings = settings

    def validate_request_size(
        self, content_length: Optional[str], client_ip: str = "unknown"
    ) -> None:
        """
        Validate incoming request size before processing.

        Args:
            content_length: Content-Length header value
            client_ip: Client IP for logging

        Raises:
            FileError: If request exceeds size limits
        """
        if content_length:
            try:
                size = int(content_length)
                if size > self.settings.max_file_size_bytes:
                    logger.warning(
                        "Request too large: %s bytes from %s", size, client_ip
                    )
                    raise FileError(
                        f"Request entity too large. Maximum size is {self.settings.max_file_size_mb}MB.",
                        f"Request size: {size} bytes",
                    )
            except ValueError as exc:
                logger.warning(
                    "Invalid Content-Length header: %s from %s",
                    content_length,
                    client_ip,
                )
                raise ValidationError("Invalid Content-Length header") from exc


# Factory functions for dependency injection
def create_file_validator(settings: Settings) -> FileValidator:
    """Create file validator instance."""
    return FileValidator(settings)


def create_request_validator(settings: Settings) -> RequestValidator:
    """Create request validator instance."""
    return RequestValidator(settings)
