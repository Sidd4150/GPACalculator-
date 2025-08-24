"""
API endpoints for GPA calculator.
"""

import tempfile
import os
from functools import lru_cache
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, File, UploadFile, Request, Depends
from pydantic import BaseModel
from slowapi import Limiter
from app.models.course import CourseRow
from app.services.parser import TranscriptParser
from app.services.gpa_calculator import GPACalculator
from app.services.validation import FileValidator
from app.config import get_settings, Settings
from app.utils.logger import setup_logger
from app.utils.exception_handler import map_exception_to_http

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
    request: Request,  # pylint: disable=unused-argument
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
        raise map_exception_to_http(e) from e


@router.post("/gpa")
@limiter.limit(f"{get_cached_settings().rate_limit_gpa}/minute")
def calculate_gpa(
    request: Request,  # pylint: disable=unused-argument
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
        raise map_exception_to_http(e) from e


@router.get("/health")
def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    settings = get_cached_settings()
    return {
        "status": "healthy",
        "service": "GPA Calculator API",
        "version": settings.app_version,
        "environment": settings.environment,
    }
