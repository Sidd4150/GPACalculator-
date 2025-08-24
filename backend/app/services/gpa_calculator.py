"""
GPA Calculator service for computing Grade Point Average from course data.
"""

from typing import List
from app.models.course import CourseRow
from app.exceptions import CalculationError, ValidationError
from app.constants import GRADE_POINTS, NON_GPA_GRADES, GPA_PRECISION_DIGITS
from app.utils.logger import setup_logger

logger = setup_logger("gpa_calculator")


class GPACalculator:
    """
    Service class for calculating GPA and related academic metrics.

    Handles USF grading scale and excludes non-GPA courses from calculations.
    """

    def calculate_gpa(self, courses: List[CourseRow]) -> float:
        """
        Calculate cumulative GPA from a list of courses.

        Args:
            courses: List of CourseRow objects

        Returns:
            GPA rounded to 2 decimal places

        Raises:
            ValidationError: If course data is invalid
            CalculationError: If calculation fails
        """

        if not isinstance(courses, list):
            logger.error("Invalid input type for courses: %s", type(courses))
            raise ValidationError("Courses must be provided as a list")

        if not courses:
            return 0.0

        total_quality_points = 0.0
        total_gpa_units = 0.0
        gpa_course_count = 0

        try:
            for course in courses:
                # Pydantic already validates CourseRow structure and required fields

                # Skip courses with non-GPA grades or zero units
                if course.grade not in GRADE_POINTS or course.units <= 0:
                    continue

                quality_points = GRADE_POINTS[course.grade] * course.units
                total_quality_points += quality_points
                total_gpa_units += course.units
                gpa_course_count += 1

            # Check if we have any GPA-eligible courses
            if total_gpa_units == 0:
                return 0.0

            # Calculate GPA and round to configured precision
            gpa = total_quality_points / total_gpa_units
            rounded_gpa = round(gpa, GPA_PRECISION_DIGITS)

            logger.info(
                "GPA calculation complete: %d courses, %s units, %s quality points, GPA: %s",
                gpa_course_count,
                total_gpa_units,
                total_quality_points,
                rounded_gpa,
            )

            return rounded_gpa

        except (ValidationError, CalculationError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error("Unexpected error during GPA calculation: %s", e)
            raise CalculationError(f"Failed to calculate GPA: {str(e)}")
