"""
Pydantic models for course data.
"""

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Course(BaseModel):
    """
    Model representing a single course from a USF transcript.

    Attributes:
        subject: Course subject code (2-6 uppercase letters, e.g., 'CS', 'MATH')
        number: Course number (digits optionally followed by single letter, e.g., '101', '101L')
        title: Course title (non-empty string)
        units: Credit units (positive number)
        grade: Letter grade or special code (TCR for transfer, IP for in-progress)
        source: Source of the course data ('parsed' from transcript or 'manual' entry)
    """

    subject: str = Field(..., description="Course subject code")
    number: str = Field(..., description="Course number")
    title: str = Field(..., description="Course title")
    units: float = Field(..., ge=0, description="Credit units (must be non-negative)")
    grade: str = Field(..., description="Letter grade or special code")
    source: Literal["parsed", "manual"] = Field(
        ..., description="Source of the course data"
    )

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, v: str) -> str:
        """Validate subject code format."""
        if not re.match(r"^[A-Z]{2,6}$", v):
            raise ValueError("Subject must be 2-6 uppercase letters")
        return v

    @field_validator("number")
    @classmethod
    def validate_number(cls, v: str) -> str:
        """Validate course number format."""
        if not re.match(r"^(\d+[A-Z]?|\d*XX)$", v):
            raise ValueError(
                "Course number must be digits optionally followed by a single letter, or XX format"
            )
        return v

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate course title is not empty."""
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v

    @field_validator("grade")
    @classmethod
    def validate_grade(cls, v: str) -> str:
        """Validate grade format."""
        valid_letter_grades = {
            "A+",
            "A",
            "A-",
            "B+",
            "B",
            "B-",
            "C+",
            "C",
            "C-",
            "D+",
            "D",
            "D-",
            "F",
        }
        valid_non_gpa_grades = {"P", "S", "U", "I", "IP", "W", "NR", "AU", "TCR", "NG"}
        valid_grades = valid_letter_grades | valid_non_gpa_grades

        if v not in valid_grades:
            raise ValueError(
                f"Invalid grade: {v}. Valid grades are: {', '.join(sorted(valid_grades))}"
            )
        return v
