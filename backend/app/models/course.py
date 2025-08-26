"""
Pydantic models for course data.
"""

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from ..constants import (
    COURSE_NUMBER_PATTERN,
    COURSE_SOURCES,
    COURSE_SUBJECT_PATTERN,
    GRADE_POINTS,
    MAX_COURSE_SUBJECT_LENGTH,
    MAX_COURSE_TITLE_LENGTH,
    MAX_COURSE_UNITS,
    MIN_COURSE_SUBJECT_LENGTH,
    MIN_COURSE_TITLE_LENGTH,
    MIN_COURSE_UNITS,
    NON_GPA_GRADES,
)


class Course(BaseModel):
    """
    Model representing a single course from a USF transcript.

    Attributes:
        subject: Course subject code (2-4 uppercase letters, e.g., 'CS', 'MATH')
        number: Course number (digits optionally followed by single letter, e.g., '101', '101L')
        title: Course title (non-empty string)
        units: Credit units (positive number)
        grade: Letter grade or special code (TCR for transfer, IP for in-progress)
        source: Source of the course data ('parsed' from transcript or 'manual' entry)
    """

    subject: str = Field(..., description="Course subject code")
    number: str = Field(..., description="Course number")
    title: str = Field(..., description="Course title")
    units: float = Field(
        ..., ge=MIN_COURSE_UNITS, le=MAX_COURSE_UNITS, description="Credit units"
    )
    grade: str = Field(..., description="Letter grade or special code")
    source: Literal["parsed", "manual"] = Field(
        ..., description="Source of the course data"
    )

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, v: str) -> str:
        """Validate subject code format."""
        if not re.match(COURSE_SUBJECT_PATTERN, v):
            raise ValueError(
                f"Subject must be {MIN_COURSE_SUBJECT_LENGTH}-{MAX_COURSE_SUBJECT_LENGTH} "
                f"uppercase letters"
            )
        return v

    @field_validator("number")
    @classmethod
    def validate_number(cls, v: str) -> str:
        """Validate course number format."""
        if not re.match(COURSE_NUMBER_PATTERN, v):
            raise ValueError(
                "Course number must be digits optionally followed by a single letter, or XX format"
            )
        return v

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate course title length."""
        title = v.strip()
        if len(title) < MIN_COURSE_TITLE_LENGTH:
            raise ValueError("Title cannot be empty")
        if len(title) > MAX_COURSE_TITLE_LENGTH:
            raise ValueError(
                f"Title cannot exceed {MAX_COURSE_TITLE_LENGTH} characters"
            )
        return title

    @field_validator("grade")
    @classmethod
    def validate_grade(cls, v: str) -> str:
        """Validate grade format."""
        valid_grades = set(GRADE_POINTS.keys()) | NON_GPA_GRADES

        if v not in valid_grades:
            raise ValueError(
                f"Invalid grade: {v}. Valid grades are: {', '.join(sorted(valid_grades))}"
            )
        return v

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        """Validate source matches allowed values."""
        if v not in COURSE_SOURCES.values():
            valid_sources = list(COURSE_SOURCES.values())
            raise ValueError(
                f"Invalid source: {v}. Valid sources are: {', '.join(valid_sources)}"
            )
        return v
