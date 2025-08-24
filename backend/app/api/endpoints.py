"""
API endpoints for GPA calculator.
"""

import tempfile
import os
from functools import lru_cache
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, File, UploadFile, Request, Depends, HTTPException, status
from pydantic import BaseModel
from slowapi import Limiter
from app.models.course import CourseRow
from app.services.parser import TranscriptParser
from app.services.gpa_calculator import GPACalculator
from app.services.validation import FileValidator
from app.exceptions import FileError
from app.constants import EXCEPTION_HTTP_MAP, ERROR_MESSAGES
from app.config import get_settings, Settings
from app.utils.logger import setup_logger

logger = setup_logger("api")


# Cached settings for performance
@lru_cache()
def get_cached_settings() -> Settings:
    """Get cached settings instance."""
    return get_settings()


# Simple dependency provider functions
def get_transcript_parser() -> TranscriptParser:
    """Get transcript parser instance."""
    return TranscriptParser()


def get_gpa_calculator() -> GPACalculator:
    """Get GPA calculator instance."""
    return GPACalculator()


def get_file_validator() -> FileValidator:
    """Get file validator instance."""
    return FileValidator(get_cached_settings())


def map_exception_to_http(exc: Exception) -> HTTPException:
    """Map application exception to HTTP exception."""
    exc_type_name = type(exc).__name__

    # Try exact type match first
    if exc_type_name in EXCEPTION_HTTP_MAP:
        status_code, message_template = EXCEPTION_HTTP_MAP[exc_type_name]
        message = _format_exception_message(exc, message_template)

        # Handle file size errors with special status code
        if isinstance(exc, FileError) and "size" in str(exc).lower():
            status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE

        return HTTPException(status_code=status_code, detail=message)

    # Try parent class matches by checking inheritance
    for base_class in type(exc).__mro__:
        base_name = base_class.__name__
        if base_name in EXCEPTION_HTTP_MAP and base_name != exc_type_name:
            status_code, message_template = EXCEPTION_HTTP_MAP[base_name]
            message = _format_exception_message(exc, message_template)
            return HTTPException(status_code=status_code, detail=message)

    # Fallback to generic error
    logger.error("Unmapped exception: %s: %s", exc_type_name, exc)
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=ERROR_MESSAGES.get("INTERNAL_ERROR", "Internal server error"),
    )


def _format_exception_message(exc: Exception, message_template: str) -> str:
    """Format exception message using template."""
    if hasattr(exc, "message"):
        # Our custom exceptions have .message attribute
        return message_template.format(message=exc.message)
    elif "{message}" in message_template:
        # Standard exceptions use str(exc)
        return message_template.format(message=str(exc))
    else:
        # Template has no placeholder
        return message_template


# Initialize rate limiter - disable in test environment
def get_rate_limiter_key(request: Request) -> Optional[str]:
    """Get rate limiter key, but skip in test environment."""
    if os.getenv("TESTING", "false").lower() == "true":
        return None  # No rate limiting during tests
    from slowapi.util import get_remote_address

    return get_remote_address(request)


limiter = Limiter(key_func=get_rate_limiter_key)

router = APIRouter()


class CoursesRequest(BaseModel):
    """Request model for GPA calculation."""

    courses: List[CourseRow]


@router.post("/upload")
@limiter.limit(f"{get_cached_settings().rate_limit_upload}/minute")
async def upload_transcript(
    request: Request,
    file: UploadFile = File(...),
    file_validator: FileValidator = Depends(get_file_validator),
    parser: TranscriptParser = Depends(get_transcript_parser),
) -> List[Dict[str, Any]]:
    """
    Upload and parse a PDF transcript file.

    Args:
        file: PDF transcript file

    Returns:
        List of parsed courses

    Raises:
        HTTPException: If file is invalid or parsing fails
    """

    try:
        # Step 1: Validate uploaded file
        file_validator.validate_upload_file(file)

        # Step 2: Read and validate content
        content = await file.read()
        file_validator.validate_file_content(content, file.filename)

        # Step 3: Write to temp file and parse
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(content)
            temp_file.flush()
            temp_path = temp_file.name

        try:
            courses = parser.parse_transcript(temp_path)
        finally:
            # Ensure cleanup even if parsing fails
            try:
                os.unlink(temp_path)
            except OSError as cleanup_error:
                logger.warning(
                    "Failed to cleanup temp file %s: %s", temp_path, cleanup_error
                )

        # Convert courses to dictionaries for JSON response
        courses_dict = [course.model_dump() for course in courses]

        logger.info(
            "Successfully processed %d courses from %s", len(courses), file.filename
        )
        return courses_dict

    except Exception as e:
        logger.error("Failed to process transcript %s: %s", file.filename, e)
        raise map_exception_to_http(e)


@router.post("/gpa")
@limiter.limit(f"{get_cached_settings().rate_limit_gpa}/minute")
def calculate_gpa(
    request: Request,
    gpa_request: CoursesRequest,
    gpa_calculator: GPACalculator = Depends(get_gpa_calculator),
) -> float:
    """
    Calculate GPA from a list of courses.

    Args:
        request: FastAPI request object
        gpa_request: List of courses with grades and units

    Returns:
        GPA calculation results and statistics

    Raises:
        HTTPException: If calculation fails
    """

    try:
        # Calculate GPA directly (Pydantic already validates CourseRow structure)
        gpa = gpa_calculator.calculate_gpa(gpa_request.courses)

        return gpa

    except Exception as e:
        logger.error("Failed to calculate GPA: %s", e)
        raise map_exception_to_http(e)


@router.get("/health")
@limiter.limit(f"{get_cached_settings().rate_limit_health}/minute")
def health_check(request: Request) -> Dict[str, str]:
    """Health check endpoint."""
    settings = get_cached_settings()
    return {
        "status": "healthy",
        "service": "GPA Calculator API",
        "version": settings.app_version,
        "environment": settings.environment
    }
