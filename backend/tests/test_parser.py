"""
Tests for PDF transcript parser.
"""

from pathlib import Path

import pytest

from app.models.course import Course
from app.services.transcript_parser import TranscriptParser


class TestTranscriptParser:
    """Test cases for transcript parsing functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = TranscriptParser()
        self.sample_transcript_path = (
            Path(__file__).parent
            / "fixtures"
            / "transcripts"
            / "Academic Transcript.pdf"
        )

    def test_parse_pdf_file_exists(self):
        """Test that parser can read the sample PDF file."""
        assert self.sample_transcript_path.exists(), (
            "Sample transcript PDF should exist"
        )

        courses = self.parser.parse_transcript(str(self.sample_transcript_path))
        assert isinstance(courses, list), "Parser should return a list of courses"

    def test_extract_text_from_pdf(self):
        """Test basic PDF text extraction."""
        text = self.parser.extract_text(str(self.sample_transcript_path))

        assert isinstance(text, str), "Extracted text should be a string"
        assert len(text) > 0, "Extracted text should not be empty"
        assert "University of San Francisco" in text, "Should contain university name"
        assert "Ryan Fahimi" in text, "Should contain student name"

    def test_detect_transcript_sections(self):
        """Test detection of the three main transcript sections."""
        text = self.parser.extract_text(str(self.sample_transcript_path))
        sections = self.parser.identify_sections(text)

        assert "transfer_credit" in sections, "Should detect transfer credit section"
        assert "institution_credit" in sections, (
            "Should detect institution credit section"
        )
        assert "courses_in_progress" in sections, (
            "Should detect courses in progress section"
        )

        # Verify section content is not empty
        assert len(sections["transfer_credit"]) > 0, (
            "Transfer credit section should not be empty"
        )
        assert len(sections["institution_credit"]) > 0, (
            "Institution credit section should not be empty"
        )
        assert len(sections["courses_in_progress"]) > 0, (
            "Courses in progress section should not be empty"
        )

    def test_parse_transfer_credit_courses(self):
        """Test parsing of transfer credit courses with TCR grades."""
        courses = self.parser.parse_transcript(str(self.sample_transcript_path))
        transfer_courses = [c for c in courses if c.grade == "TCR"]

        assert len(transfer_courses) == 10, (
            "Should find exactly 10 transfer credit courses"
        )

        # All transfer courses should have TCR grade and valid properties
        for course in transfer_courses:
            assert course.grade == "TCR", (
                f"Transfer course {course.subject} {course.number} should have TCR grade"
            )
            assert course.units > 0, "Transfer courses should have positive units"
            assert course.title, "Transfer courses should have titles"

    def test_parse_institution_credit_courses(self):
        """Test parsing of institution credit courses with letter grades."""
        courses = self.parser.parse_transcript(str(self.sample_transcript_path))
        institution_courses = [c for c in courses if c.grade not in ["TCR", "IP"]]

        assert len(institution_courses) == 28, (
            "Should find exactly 28 institution credit courses"
        )

        # Verify institution courses have valid letter grades and properties
        valid_grades = {
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
            "NG",
        }
        for course in institution_courses:
            assert course.grade in valid_grades, (
                f"Institution course should have valid grade, got {course.grade}"
            )
            assert course.units >= 0, (
                "Institution courses should have non-negative units"
            )
            assert course.title, "Institution courses should have titles"

    def test_parse_courses_in_progress(self):
        """Test parsing of courses currently in progress."""
        courses = self.parser.parse_transcript(str(self.sample_transcript_path))
        in_progress_courses = [c for c in courses if c.grade == "IP"]

        assert len(in_progress_courses) == 6, (
            "Should find exactly 6 courses in progress"
        )

        # Verify in-progress courses have IP grade and valid properties
        for course in in_progress_courses:
            assert course.grade == "IP", "In-progress course should have IP grade"
            assert course.units >= 0, (
                "In-progress courses should have non-negative units"
            )
            assert course.title, "In-progress courses should have titles"

    def test_handle_multiline_titles(self):
        """Test parsing of course titles that span multiple lines."""
        courses = self.parser.parse_transcript(str(self.sample_transcript_path))

        # Find course with multiline title
        multiline_course = next(
            (c for c in courses if "Software Dev with" in c.title), None
        )
        assert multiline_course is not None, "Should find course with multiline title"
        assert "Code Review" in multiline_course.title, (
            "Should include full multiline title"
        )

        # Test another multiline title
        envs_course = next(
            (c for c in courses if c.subject == "ENVS" and "Environ" in c.title), None
        )
        assert envs_course is not None, "Should find ENVS course with multiline title"
        assert "w/Lab" in envs_course.title, "Should include full multiline title"

    def test_handle_special_grades(self):
        """Test parsing of special grade codes."""
        courses = self.parser.parse_transcript(str(self.sample_transcript_path))

        # Test NG grade (No Grade)
        ng_courses = [c for c in courses if c.grade == "NG"]
        assert len(ng_courses) > 0, "Should find courses with NG grade"

        ng_course = ng_courses[0]
        assert ng_course.units >= 0, "NG course should have valid units"

        # Test courses with lab sections that have special handling
        lab_course = next(
            (
                c
                for c in courses
                if "Laboratory" in c.title and "DO NOT PRINT" in c.title
            ),
            None,
        )
        if lab_course:
            assert lab_course.grade == "NG", (
                "Lab course marked DO NOT PRINT should have NG grade"
            )
            assert lab_course.units == 0.0, (
                "Lab course marked DO NOT PRINT should have 0 units"
            )

    def test_handle_course_numbers_with_letters(self):
        """Test parsing of course numbers with trailing letters."""
        courses = self.parser.parse_transcript(str(self.sample_transcript_path))

        # Test course numbers with letters
        cs_272n = next(
            (c for c in courses if c.subject == "CS" and c.number == "272N"), None
        )
        assert cs_272n is not None, "Should find CS 272N course"

        envs_100l = next(
            (c for c in courses if c.subject == "ENVS" and c.number == "100L"), None
        )
        assert envs_100l is not None, "Should find ENVS 100L course"

        cs_315l = next(
            (c for c in courses if c.subject == "CS" and c.number == "315L"), None
        )
        assert cs_315l is not None, "Should find CS 315L course"

    def test_handle_variable_credit_hours(self):
        """Test parsing of courses with non-standard credit hours."""
        courses = self.parser.parse_transcript(str(self.sample_transcript_path))

        # Test 6-credit course
        six_credit = next((c for c in courses if c.units == 6.0), None)
        assert six_credit is not None, "Should find 6-credit course"

        # Test fractional credit course
        fractional_credit = next((c for c in courses if c.units == 2.5), None)
        assert fractional_credit is not None, "Should find 2.5-credit course"

        # Test 0-credit course
        zero_credit = next((c for c in courses if c.units == 0.0), None)
        assert zero_credit is not None, "Should find 0-credit course"

    def test_course_regex_patterns(self):
        """Test unified regex pattern used for course parsing."""
        # Test that unified regex pattern is compiled correctly
        assert self.parser._course_pattern is not None, (
            "Should have unified course pattern"
        )

        # Test standard course line pattern by parsing a small section with known course
        test_section = "CS 110 UG Intro to Computer Science I A+ 4.000 16.00"
        courses = self.parser.parse_section_courses(test_section)

        assert len(courses) == 1, "Should parse exactly one course from test section"
        course = courses[0]
        assert course.subject == "CS", "Should extract subject correctly"
        assert course.number == "110", "Should extract number correctly"
        assert course.title == "Intro to Computer Science I", (
            "Should extract title correctly"
        )
        assert course.grade == "A+", "Should extract grade correctly"
        assert course.units == 4.0, "Should extract units correctly"

    def test_parse_complete_transcript(self):
        """Test parsing the complete transcript and verify totals."""
        courses = self.parser.parse_transcript(str(self.sample_transcript_path))

        assert len(courses) == 44, (
            "Should parse exactly 44 courses from Academic Transcript.pdf"
        )

        # Verify we have courses from all types (transfer, institution, in-progress)
        grades = {course.grade for course in courses}
        assert "TCR" in grades, "Should have transfer credit courses with TCR grade"
        assert "IP" in grades, "Should have in-progress courses with IP grade"
        assert any(grade not in ["TCR", "IP"] for grade in grades), (
            "Should have regular graded courses"
        )

        # Verify all courses are valid Course instances
        for course in courses:
            assert isinstance(course, Course), (
                "All parsed items should be Course instances"
            )
            assert course.subject, "All courses should have subject"
            assert course.number, "All courses should have number"
            assert course.title, "All courses should have title"
            assert course.units >= 0, "All courses should have non-negative units"
            assert course.grade, "All courses should have grade"

    def test_error_handling(self):
        """Test parser error handling for invalid inputs."""
        # Test non-existent file
        with pytest.raises(FileNotFoundError):
            self.parser.parse_transcript("nonexistent_file.pdf")

        # Test empty section
        courses = self.parser.parse_section_courses("")
        assert len(courses) == 0, "Should return empty list for empty section"

        # Test invalid section format
        courses = self.parser.parse_section_courses("Invalid section format")
        assert len(courses) == 0, "Should return empty list for invalid section format"

    def test_section_boundary_detection(self):
        """Test accurate detection of section boundaries."""
        text = self.parser.extract_text(str(self.sample_transcript_path))
        sections = self.parser.identify_sections(text)

        # Verify section boundaries don't overlap
        transfer_text = sections["transfer_credit"]
        institution_text = sections["institution_credit"]
        progress_text = sections["courses_in_progress"]

        # Transfer section should contain TCR grades
        assert "TCR" in transfer_text, "Transfer section should contain TCR grades"

        # Institution section should contain letter grades
        assert any(
            grade in institution_text for grade in ["A+", "A", "A-", "B+", "B"]
        ), "Institution section should contain letter grades"

        # Progress section should be clearly marked
        assert "COURSES IN PROGRESS" in progress_text, (
            "Progress section should be clearly marked"
        )
