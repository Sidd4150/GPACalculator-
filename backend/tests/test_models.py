"""
Tests for Pydantic models.
"""

import pytest
from app.models.course import Course
from pydantic import ValidationError


class TestCourseRow:
    """Test cases for CourseRow model validation."""

    def test_source_field_validation(self):
        """Test source field validation."""
        # Valid sources
        course_parsed = Course(
            subject="CS",
            number="101",
            title="Test",
            units=3.0,
            grade="A",
            source="parsed",
        )
        assert course_parsed.source == "parsed"

        course_manual = Course(
            subject="CS",
            number="101",
            title="Test",
            units=3.0,
            grade="A",
            source="manual",
        )
        assert course_manual.source == "manual"

        # Invalid source
        with pytest.raises(ValidationError) as exc_info:
            Course(
                subject="CS",
                number="101",
                title="Test",
                units=3.0,
                grade="A",
                source="invalid",
            )
        assert "Input should be 'parsed' or 'manual'" in str(exc_info.value)

    def test_valid_course_row(self):
        """Test creating a valid CourseRow instance."""
        course = Course(
            subject="CS",
            number="101",
            title="Intro to Computer Science",
            units=3.0,
            grade="A",
            source="parsed",
        )
        assert course.subject == "CS"
        assert course.number == "101"
        assert course.title == "Intro to Computer Science"
        assert course.units == 3.0
        assert course.grade == "A"
        assert course.source == "parsed"

    def test_valid_course_with_letter_suffix(self):
        """Test course number with trailing letter."""
        course = Course(
            subject="ENG",
            number="101L",
            title="English Lab",
            units=1.0,
            grade="B+",
            source="parsed",
        )
        assert course.number == "101L"

    def test_valid_transfer_credit(self):
        """Test transfer credit with TCR grade."""
        course = Course(
            subject="MATH",
            number="201",
            title="Calculus I",
            units=4.0,
            grade="TCR",
            source="parsed",
        )
        assert course.grade == "TCR"

    def test_valid_courses_in_progress(self):
        """Test course in progress with IP grade."""
        course = Course(
            subject="PHY",
            number="205",
            title="Physics II",
            units=3.0,
            grade="IP",
            source="parsed",
        )
        assert course.grade == "IP"

    # Subject validation tests
    def test_subject_validation_invalid_cases(self):
        """Test various invalid subject formats."""
        invalid_subjects = ["cs", "C", "COMPSCI", "CS1", "CS-"]

        for invalid_subject in invalid_subjects:
            with pytest.raises(ValidationError) as exc_info:
                Course(
                    subject=invalid_subject,
                    number="101",
                    title="Test",
                    units=3.0,
                    grade="A",
                    source="manual",
                )
            assert "Subject must be 2-6 uppercase letters" in str(exc_info.value)

    # Number validation tests
    def test_number_digits_only(self):
        """Test course number with digits only."""
        course = Course(
            subject="CS",
            number="4950",
            title="Senior Project",
            units=3.0,
            grade="A",
            source="manual",
        )
        assert course.number == "4950"

    def test_number_with_single_letter(self):
        """Test course number with single trailing letter."""
        course = Course(
            subject="BIO",
            number="101L",
            title="Biology Lab",
            units=1.0,
            grade="A",
            source="parsed",
        )
        assert course.number == "101L"

    def test_number_xx_format(self):
        """Test XX course number format."""
        course = Course(
            subject="CS",
            number="4XX",
            title="Test Course",
            units=3.0,
            grade="A",
            source="parsed",
        )
        assert course.number == "4XX"

        course = Course(
            subject="HIST",
            number="1XX",
            title="Test Course",
            units=3.0,
            grade="A",
            source="parsed",
        )
        assert course.number == "1XX"

    def test_number_invalid_format(self):
        """Test invalid course number formats."""
        invalid_numbers = ["10A1", "A101", "101AB", "10-1", ""]

        for invalid_number in invalid_numbers:
            with pytest.raises(ValidationError) as exc_info:
                Course(
                    subject="CS",
                    number=invalid_number,
                    title="Test",
                    units=3.0,
                    grade="A",
                    source="manual",
                )
            assert (
                "Course number must be digits optionally followed by a single letter"
                in str(exc_info.value)
            )

    # Units validation tests
    def test_units_validation(self):
        """Test units validation with various values."""
        # Valid units
        valid_units = [0, 1, 3.0, 3.5, 4]
        for units in valid_units:
            course = Course(
                subject="CS",
                number="101",
                title="Test",
                units=units,
                grade="A",
                source="manual",
            )
            assert course.units == float(units)

        # Invalid units
        with pytest.raises(ValidationError) as exc_info:
            Course(
                subject="CS",
                number="101",
                title="Test",
                units=-1.0,
                grade="A",
                source="manual",
            )
        assert "Input should be greater than or equal to 0" in str(exc_info.value)

    # Grade validation tests
    def test_valid_letter_grades(self):
        """Test all valid letter grades."""
        valid_grades = [
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
        ]

        for grade in valid_grades:
            course = Course(
                subject="CS",
                number="101",
                title="Test",
                units=3.0,
                grade=grade,
                source="parsed",
            )
            assert course.grade == grade

    def test_valid_non_gpa_grades(self):
        """Test all valid non-GPA grades."""
        valid_non_gpa = ["P", "S", "U", "I", "IP", "W", "NR", "AU", "TCR", "NG"]

        for grade in valid_non_gpa:
            course = Course(
                subject="CS",
                number="101",
                title="Test",
                units=3.0,
                grade=grade,
                source="parsed",
            )
            assert course.grade == grade

    def test_invalid_grades(self):
        """Test invalid grade values."""
        invalid_grades = ["E", "Z", "a", "b+", "123", "", "A B"]

        for invalid_grade in invalid_grades:
            with pytest.raises(ValidationError) as exc_info:
                Course(
                    subject="CS",
                    number="101",
                    title="Test",
                    units=3.0,
                    grade=invalid_grade,
                    source="manual",
                )
            assert "Invalid grade" in str(exc_info.value)

    # Title validation tests
    def test_title_validation(self):
        """Test title validation with various cases."""
        # Valid titles
        valid_titles = [
            "Intro to Computer Science",
            "Intro to C++ & Data Structures",
            "A" * 200,  # Long title
        ]
        for title in valid_titles:
            course = Course(
                subject="CS",
                number="101",
                title=title,
                units=3.0,
                grade="A",
                source="parsed",
            )
            assert course.title == title

        # Invalid titles (empty or whitespace-only)
        invalid_titles = ["", "   "]
        for invalid_title in invalid_titles:
            with pytest.raises(ValidationError) as exc_info:
                Course(
                    subject="CS",
                    number="101",
                    title=invalid_title,
                    units=3.0,
                    grade="A",
                    source="manual",
                )
            assert "Title cannot be empty" in str(exc_info.value)

    # Edge cases and combinations
    def test_course_row_serialization(self):
        """Test that CourseRow can be serialized to dict."""
        course = Course(
            subject="CS",
            number="101L",
            title="Computer Science Lab",
            units=1.0,
            grade="A-",
            source="parsed",
        )

        course_dict = course.model_dump()
        expected = {
            "subject": "CS",
            "number": "101L",
            "title": "Computer Science Lab",
            "units": 1.0,
            "grade": "A-",
            "source": "parsed",
        }
        assert course_dict == expected

    def test_course_row_from_dict(self):
        """Test creating CourseRow from dictionary."""
        data = {
            "subject": "MATH",
            "number": "201",
            "title": "Calculus I",
            "units": 4.0,
            "grade": "B+",
            "source": "manual",
        }

        course = Course(**data)
        assert course.subject == "MATH"
        assert course.number == "201"
        assert course.grade == "B+"
        assert course.source == "manual"
