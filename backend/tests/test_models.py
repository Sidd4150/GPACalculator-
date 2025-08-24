"""
Tests for Pydantic models.
"""

import pytest
from pydantic import ValidationError
from app.models.course import CourseRow


class TestCourseRow:
    """Test cases for CourseRow model validation."""

    def test_valid_course_row(self):
        """Test creating a valid CourseRow instance."""
        course = CourseRow(
            subject="CS",
            number="101",
            title="Intro to Computer Science",
            units=3.0,
            grade="A",
        )
        assert course.subject == "CS"
        assert course.number == "101"
        assert course.title == "Intro to Computer Science"
        assert course.units == 3.0
        assert course.grade == "A"

    def test_valid_course_with_letter_suffix(self):
        """Test course number with trailing letter."""
        course = CourseRow(
            subject="ENG", number="101L", title="English Lab", units=1.0, grade="B+"
        )
        assert course.number == "101L"

    def test_valid_transfer_credit(self):
        """Test transfer credit with TCR grade."""
        course = CourseRow(
            subject="MATH", number="201", title="Calculus I", units=4.0, grade="TCR"
        )
        assert course.grade == "TCR"

    def test_valid_courses_in_progress(self):
        """Test course in progress with IP grade."""
        course = CourseRow(
            subject="PHY", number="205", title="Physics II", units=3.0, grade="IP"
        )
        assert course.grade == "IP"

    # Subject validation tests
    def test_subject_must_be_uppercase(self):
        """Test that subject must be uppercase letters."""
        with pytest.raises(ValidationError) as exc_info:
            CourseRow(subject="cs", number="101", title="Test", units=3.0, grade="A")
        assert "Subject must be 2-6 uppercase letters" in str(exc_info.value)

    def test_subject_too_short(self):
        """Test that subject must be at least 2 characters."""
        with pytest.raises(ValidationError) as exc_info:
            CourseRow(subject="C", number="101", title="Test", units=3.0, grade="A")
        assert "Subject must be 2-6 uppercase letters" in str(exc_info.value)

    def test_subject_too_long(self):
        """Test that subject must be at most 6 characters."""
        with pytest.raises(ValidationError) as exc_info:
            CourseRow(
                subject="COMPSCI", number="101", title="Test", units=3.0, grade="A"
            )
        assert "Subject must be 2-6 uppercase letters" in str(exc_info.value)

    def test_subject_with_numbers(self):
        """Test that subject cannot contain numbers."""
        with pytest.raises(ValidationError) as exc_info:
            CourseRow(subject="CS1", number="101", title="Test", units=3.0, grade="A")
        assert "Subject must be 2-6 uppercase letters" in str(exc_info.value)

    def test_subject_with_special_characters(self):
        """Test that subject cannot contain special characters."""
        with pytest.raises(ValidationError) as exc_info:
            CourseRow(subject="CS-", number="101", title="Test", units=3.0, grade="A")
        assert "Subject must be 2-6 uppercase letters" in str(exc_info.value)

    # Number validation tests
    def test_number_digits_only(self):
        """Test course number with digits only."""
        course = CourseRow(
            subject="CS", number="4950", title="Senior Project", units=3.0, grade="A"
        )
        assert course.number == "4950"

    def test_number_with_single_letter(self):
        """Test course number with single trailing letter."""
        course = CourseRow(
            subject="BIO", number="101L", title="Biology Lab", units=1.0, grade="A"
        )
        assert course.number == "101L"

    def test_number_xx_format(self):
        """Test XX course number format."""
        course = CourseRow(
            subject="CS", number="4XX", title="Test Course", units=3.0, grade="A"
        )
        assert course.number == "4XX"

        course = CourseRow(
            subject="HIST", number="1XX", title="Test Course", units=3.0, grade="A"
        )
        assert course.number == "1XX"

    def test_number_invalid_format(self):
        """Test invalid course number formats."""
        invalid_numbers = ["10A1", "A101", "101AB", "10-1", ""]

        for invalid_number in invalid_numbers:
            with pytest.raises(ValidationError) as exc_info:
                CourseRow(
                    subject="CS",
                    number=invalid_number,
                    title="Test",
                    units=3.0,
                    grade="A",
                )
            assert (
                "Course number must be digits optionally followed by a single letter"
                in str(exc_info.value)
            )

    # Units validation tests
    def test_units_positive_integer(self):
        """Test units as positive integer."""
        course = CourseRow(subject="CS", number="101", title="Test", units=3, grade="A")
        assert course.units == 3.0

    def test_units_positive_float(self):
        """Test units as positive float."""
        course = CourseRow(
            subject="CS", number="101", title="Test", units=3.5, grade="A"
        )
        assert course.units == 3.5

    def test_units_zero(self):
        """Test that zero units are now allowed."""
        course = CourseRow(subject="CS", number="101", title="Test", units=0, grade="A")
        assert course.units == 0.0

    def test_units_negative(self):
        """Test that negative units are invalid."""
        with pytest.raises(ValidationError) as exc_info:
            CourseRow(subject="CS", number="101", title="Test", units=-1.0, grade="A")
        assert "Input should be greater than or equal to 0" in str(exc_info.value)

    # Grade validation tests
    def test_valid_letter_grades(self):
        """Test all valid letter grades."""
        valid_grades = [
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
            course = CourseRow(
                subject="CS", number="101", title="Test", units=3.0, grade=grade
            )
            assert course.grade == grade

    def test_valid_non_gpa_grades(self):
        """Test all valid non-GPA grades."""
        valid_non_gpa = ["P", "S", "U", "I", "IP", "W", "NR", "AU", "TCR", "NG"]

        for grade in valid_non_gpa:
            course = CourseRow(
                subject="CS", number="101", title="Test", units=3.0, grade=grade
            )
            assert course.grade == grade

    def test_invalid_grades(self):
        """Test invalid grade values."""
        invalid_grades = ["E", "Z", "a", "b+", "123", "", "A B"]

        for invalid_grade in invalid_grades:
            with pytest.raises(ValidationError) as exc_info:
                CourseRow(
                    subject="CS",
                    number="101",
                    title="Test",
                    units=3.0,
                    grade=invalid_grade,
                )
            assert "Invalid grade" in str(exc_info.value)

    # Title validation tests
    def test_empty_title(self):
        """Test that empty title is invalid."""
        with pytest.raises(ValidationError) as exc_info:
            CourseRow(subject="CS", number="101", title="", units=3.0, grade="A")
        assert "Title cannot be empty" in str(exc_info.value)

    def test_whitespace_only_title(self):
        """Test that whitespace-only title is invalid."""
        with pytest.raises(ValidationError) as exc_info:
            CourseRow(subject="CS", number="101", title="   ", units=3.0, grade="A")
        assert "Title cannot be empty" in str(exc_info.value)

    def test_title_with_special_characters(self):
        """Test title with special characters."""
        course = CourseRow(
            subject="CS",
            number="101",
            title="Intro to C++ & Data Structures",
            units=3.0,
            grade="A",
        )
        assert course.title == "Intro to C++ & Data Structures"

    def test_long_title(self):
        """Test very long title."""
        long_title = "A" * 200
        course = CourseRow(
            subject="CS", number="101", title=long_title, units=3.0, grade="A"
        )
        assert course.title == long_title

    # Edge cases and combinations
    def test_course_row_serialization(self):
        """Test that CourseRow can be serialized to dict."""
        course = CourseRow(
            subject="CS",
            number="101L",
            title="Computer Science Lab",
            units=1.0,
            grade="A-",
        )

        course_dict = course.model_dump()
        expected = {
            "subject": "CS",
            "number": "101L",
            "title": "Computer Science Lab",
            "units": 1.0,
            "grade": "A-",
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
        }

        course = CourseRow(**data)
        assert course.subject == "MATH"
        assert course.number == "201"
        assert course.grade == "B+"
