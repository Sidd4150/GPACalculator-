"""
API endpoints for GPA calculator.
"""

import os
import tempfile
from functools import lru_cache
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import Settings, get_settings
from app.exceptions import TranscriptParsingError
from app.models.course import Course
from app.services.gpa_calculator import GPACalculator
from app.services.transcript_parser import TranscriptParser
from app.utils.file_validator import FileValidator
from app.utils.logger import setup_logger

logger = setup_logger("api")


# Cached settings for performance
@lru_cache
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
def get_rate_limiter_key(request: Request) -> str | None:
    """Get rate limiter key, but skip in test environment."""
    if os.getenv("TESTING", "false").lower() == "true":
        return None  # No rate limiting during tests
    return get_remote_address(request)


limiter = Limiter(key_func=get_rate_limiter_key)

router = APIRouter()


class CoursesRequest(BaseModel):
    """Request model for GPA calculation."""

    courses: list[Course]


@router.post("/upload")
@limiter.limit(f"{get_cached_settings().rate_limit_upload}/minute")
async def upload_transcript(
    request: Request,  # pylint: disable=unused-argument
    file: UploadFile = File(...),
    file_validator: FileValidator = Depends(get_file_validator),
    parser: TranscriptParser = Depends(get_transcript_parser),
) -> list[dict[str, Any]]:
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

    except ValueError as e:
        logger.error("Validation error processing transcript %s: %s", file.filename, e)
        # Check if it's a file size error for special status code
        if "size" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(e)
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except FileNotFoundError as e:
        logger.error("File not found error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File not found"
        ) from e
    except OSError as e:
        logger.error("File I/O error processing transcript %s: %s", file.filename, e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Error reading file"
        ) from e
    except TranscriptParsingError as e:
        logger.error("Parsing error for transcript %s: %s", file.filename, e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to parse transcript: {str(e)}",
        ) from e
    except Exception as e:
        logger.error("Unexpected error processing transcript %s: %s", file.filename, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


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
        # Calculate GPA directly (Pydantic already validates Course structure)
        gpa = gpa_calculator.calculate_gpa(gpa_request.courses)

        return gpa

    except ValueError as e:
        logger.error("GPA calculation error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        logger.error("Unexpected error calculating GPA: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    settings = get_cached_settings()
    return {
        "status": "healthy",
        "service": "GPA Calculator API",
        "version": settings.app_version,
        "environment": settings.environment,
    }
