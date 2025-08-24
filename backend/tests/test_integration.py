"""
End-to-end integration tests for the complete GPA calculator workflow.
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app


class TestEndToEndIntegration:
    """End-to-end integration tests using the actual transcript PDF."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        self.test_transcript_path = (
            Path(__file__).parent.parent / "Academic Transcript.pdf"
        )

        # Expected course data from the actual transcript
        self.expected_total_courses = 42
        self.expected_gpa = 3.99

        # Expected specific courses (sample for verification)
        self.expected_courses = {
            # Transfer credits (should be parsed but not count toward GPA)
            "HIST_120": {
                "subject": "HIST",
                "number": "120",
                "title": "History of the U.S.",
                "units": 4.0,
                "grade": "TCR",
            },
            "MATH_101": {
                "subject": "MATH",
                "number": "101",
                "title": "Elementary Statistics",
                "units": 4.0,
                "grade": "TCR",
            },
            "CS_107": {
                "subject": "CS",
                "number": "107",
                "title": "Computing, Mobile Apps, & Web",
                "units": 4.0,
                "grade": "TCR",
            },
            # Institution courses (should count toward GPA)
            "CS_110": {
                "subject": "CS",
                "number": "110",
                "title": "Intro to Computer Science I",
                "units": 4.0,
                "grade": "A+",
            },
            "CS_112": {
                "subject": "CS",
                "number": "112",
                "title": "Intro to Computer Science II",
                "units": 4.0,
                "grade": "A+",
            },
            "CS_221": {
                "subject": "CS",
                "number": "221",
                "title": "C and Systems Programming",
                "units": 4.0,
                "grade": "A",
            },
            "CS_245": {
                "subject": "CS",
                "number": "245",
                "title": "Data Struct & Algorithms",
                "units": 4.0,
                "grade": "A+",
            },
            "CS_272N": {
                "subject": "CS",
                "number": "272N",
                "title": "Software Dev with Code Review",
                "units": 6.0,
                "grade": "A+",
            },
            "CS_362": {
                "subject": "CS",
                "number": "362",
                "title": "Foundations of AI",
                "units": 4.0,
                "grade": "A",
            },
            "CS_498": {
                "subject": "CS",
                "number": "498",
                "title": "Natural Language Coding",
                "units": 4.0,
                "grade": "A",
            },
            "CS_4XX": {
                "subject": "CS",
                "number": "4XX",
                "title": "Computer Vision & AI",
                "units": 5.0,
                "grade": "A",
            },
            "CS_4XX_SOFTWARE": {
                "subject": "CS",
                "number": "4XX",
                "title": "Software Systems",
                "units": 7.5,
                "grade": "A",
            },
            "MATH_201": {
                "subject": "MATH",
                "number": "201",
                "title": "Discrete Mathematics",
                "units": 4.0,
                "grade": "A+",
            },
            "MATH_202": {
                "subject": "MATH",
                "number": "202",
                "title": "Linear Algebra & Probability",
                "units": 4.0,
                "grade": "A",
            },
            "ENVS_100": {
                "subject": "ENVS",
                "number": "100",
                "title": "Understand our Environ w/Lab",
                "units": 4.0,
                "grade": "A-",
            },
            "ENVS_100L": {
                "subject": "ENVS",
                "number": "100L",
                "title": "Laboratory",
                "units": 0.0,
                "grade": "NG",
            },
            # Courses in progress (should be parsed but not count toward GPA)
            "CS_256": {
                "subject": "CS",
                "number": "256",
                "title": "Career Prep",
                "units": 2.0,
                "grade": "IP",
            },
            "CS_315": {
                "subject": "CS",
                "number": "315",
                "title": "Computer Architecture",
                "units": 4.0,
                "grade": "IP",
            },
            "CS_490": {
                "subject": "CS",
                "number": "490",
                "title": "Senior Team Project",
                "units": 4.0,
                "grade": "IP",
            },
        }

    def test_complete_workflow_upload_and_gpa_calculation(self):
        """Test the complete workflow: upload transcript, verify parsing, calculate GPA."""
        # Step 1: Upload the actual transcript PDF
        with open(self.test_transcript_path, "rb") as pdf_file:
            files = {"file": ("Academic Transcript.pdf", pdf_file, "application/pdf")}
            upload_response = self.client.post("/api/v1/upload", files=files)

        # Verify upload was successful
        assert (
            upload_response.status_code == 200
        ), f"Upload failed: {upload_response.text}"
        upload_data = upload_response.json()

        # Verify basic parsing results
        courses = upload_data
        assert (
            len(courses) == self.expected_total_courses
        ), f"Expected {self.expected_total_courses} courses, got {len(courses)}"

        # Step 2: Verify specific courses were parsed correctly
        self._verify_course_parsing(courses)

        # Step 3: Calculate GPA using the parsed courses
        gpa_payload = {"courses": courses}
        gpa_response = self.client.post("/api/v1/gpa", json=gpa_payload)

        # Verify GPA calculation was successful
        assert (
            gpa_response.status_code == 200
        ), f"GPA calculation failed: {gpa_response.text}"
        gpa = gpa_response.json()

        # Step 4: Verify GPA calculation results
        self._verify_gpa_calculation(gpa)

    def test_course_parsing_accuracy(self):
        """Test that all expected courses are parsed with correct details."""
        # Upload and parse the transcript
        with open(self.test_transcript_path, "rb") as pdf_file:
            files = {"file": ("Academic Transcript.pdf", pdf_file, "application/pdf")}
            upload_response = self.client.post("/api/v1/upload", files=files)

        assert upload_response.status_code == 200
        courses = upload_response.json()

        # Create a lookup dictionary for easier verification
        course_lookup = {}
        for course in courses:
            key = f"{course['subject']}_{course['number']}"
            if key in course_lookup:
                # Handle duplicate course numbers (like CS 4XX)
                key += f"_{course['title'].split()[0].upper()}"
            course_lookup[key] = course

        # Verify each expected course
        for expected_key, expected_course in self.expected_courses.items():
            assert (
                expected_key in course_lookup
            ), f"Expected course {expected_key} not found. Available keys: {list(course_lookup.keys())}"

            actual_course = course_lookup[expected_key]

            # Verify all required fields match
            assert (
                actual_course["subject"] == expected_course["subject"]
            ), f"Subject mismatch for {expected_key}"
            assert (
                actual_course["number"] == expected_course["number"]
            ), f"Number mismatch for {expected_key}"
            assert (
                actual_course["units"] == expected_course["units"]
            ), f"Units mismatch for {expected_key}"
            assert (
                actual_course["grade"] == expected_course["grade"]
            ), f"Grade mismatch for {expected_key}"

            # Title should contain expected text (allowing for minor parsing variations)
            expected_title_words = expected_course["title"].lower().split()
            actual_title_lower = actual_course["title"].lower()

            # Check that key words from expected title appear in actual title
            key_words_found = sum(
                1 for word in expected_title_words[:3] if word in actual_title_lower
            )  # Check first 3 words
            assert (
                key_words_found >= 1
            ), f"Title mismatch for {expected_key}: expected '{expected_course['title']}', got '{actual_course['title']}'"

    def test_course_type_distribution(self):
        """Test that courses are correctly categorized by type."""
        # Upload and parse the transcript
        with open(self.test_transcript_path, "rb") as pdf_file:
            files = {"file": ("Academic Transcript.pdf", pdf_file, "application/pdf")}
            upload_response = self.client.post("/api/v1/upload", files=files)

        assert upload_response.status_code == 200
        courses = upload_response.json()

        # Categorize courses by grade type
        transfer_courses = [c for c in courses if c["grade"] == "TCR"]
        institution_courses = [c for c in courses if c["grade"] not in ["TCR", "IP"]]
        progress_courses = [c for c in courses if c["grade"] == "IP"]

        # Verify expected distribution
        assert (
            len(transfer_courses) == 9
        ), f"Expected 9 transfer courses, got {len(transfer_courses)}"
        assert (
            len(institution_courses) == 27
        ), f"Expected 27 institution courses, got {len(institution_courses)}"
        assert (
            len(progress_courses) == 6
        ), f"Expected 6 in-progress courses, got {len(progress_courses)}"

        # Verify total adds up
        assert (
            len(transfer_courses) + len(institution_courses) + len(progress_courses)
            == self.expected_total_courses
        )

        # Verify specific grade distributions in institution courses
        grade_counts = {}
        for course in institution_courses:
            grade = course["grade"]
            grade_counts[grade] = grade_counts.get(grade, 0) + 1

        # This student should have mostly A grades
        a_grades = grade_counts.get("A", 0) + grade_counts.get("A+", 0)
        total_graded = len([c for c in institution_courses if c["grade"] not in ["NG"]])

        assert a_grades >= 20, f"Expected at least 20 A/A+ grades, got {a_grades}"
        assert (
            a_grades / total_graded >= 0.8
        ), f"Expected at least 80% A grades, got {a_grades/total_graded*100:.1f}%"

    def test_gpa_calculation_accuracy(self):
        """Test that GPA calculation matches manual calculation exactly."""
        # Upload and parse the transcript
        with open(self.test_transcript_path, "rb") as pdf_file:
            files = {"file": ("Academic Transcript.pdf", pdf_file, "application/pdf")}
            upload_response = self.client.post("/api/v1/upload", files=files)

        assert upload_response.status_code == 200
        courses = upload_response.json()

        # Calculate GPA
        gpa_response = self.client.post("/api/v1/gpa", json={"courses": courses})
        assert gpa_response.status_code == 200
        gpa_data = gpa_response.json()

        # Verify exact GPA match
        assert (
            gpa_data == self.expected_gpa
        ), f"Expected GPA {self.expected_gpa}, got {gpa_data}"

    def test_specific_high_value_courses(self):
        """Test that high-value courses (unusual units, important CS courses) are parsed correctly."""
        # Upload and parse the transcript
        with open(self.test_transcript_path, "rb") as pdf_file:
            files = {"file": ("Academic Transcript.pdf", pdf_file, "application/pdf")}
            upload_response = self.client.post("/api/v1/upload", files=files)

        assert upload_response.status_code == 200
        courses = upload_response.json()

        # Find specific high-value courses
        cs_272n = next(
            (c for c in courses if c["subject"] == "CS" and c["number"] == "272N"), None
        )
        assert cs_272n is not None, "Should find CS 272N (6-credit course)"
        assert (
            cs_272n["units"] == 6.0
        ), f"CS 272N should have 6 units, got {cs_272n['units']}"
        assert (
            cs_272n["grade"] == "A+"
        ), f"CS 272N should have A+ grade, got {cs_272n['grade']}"

        # Find CS 4XX courses (both should be present)
        cs_4xx_courses = [
            c for c in courses if c["subject"] == "CS" and "4XX" in c["number"]
        ]
        assert (
            len(cs_4xx_courses) == 2
        ), f"Should find exactly 2 CS 4XX courses, got {len(cs_4xx_courses)}"

        vision_course = next(
            (c for c in cs_4xx_courses if "Vision" in c["title"]), None
        )
        software_course = next(
            (c for c in cs_4xx_courses if "Software" in c["title"]), None
        )

        assert vision_course is not None, "Should find Computer Vision course"
        assert (
            vision_course["units"] == 5.0
        ), f"Computer Vision should have 5 units, got {vision_course['units']}"

        assert software_course is not None, "Should find Software Systems course"
        assert (
            software_course["units"] == 7.5
        ), f"Software Systems should have 7.5 units, got {software_course['units']}"

        # Find study abroad course (unusual high units)
        study_abroad = next(
            (c for c in courses if c["subject"] == "STU" and c["number"] == "386"), None
        )
        assert study_abroad is not None, "Should find study abroad course"
        assert (
            study_abroad["units"] == 18.0
        ), f"Study abroad should have 18 units, got {study_abroad['units']}"
        assert (
            study_abroad["grade"] == "NG"
        ), f"Study abroad should have NG grade, got {study_abroad['grade']}"

    def test_edge_case_courses(self):
        """Test parsing of edge case courses (zero units, special grades)."""
        # Upload and parse the transcript
        with open(self.test_transcript_path, "rb") as pdf_file:
            files = {"file": ("Academic Transcript.pdf", pdf_file, "application/pdf")}
            upload_response = self.client.post("/api/v1/upload", files=files)

        assert upload_response.status_code == 200
        courses = upload_response.json()

        # Find zero-unit lab course
        lab_course = next(
            (c for c in courses if c["subject"] == "ENVS" and c["number"] == "100L"),
            None,
        )
        assert lab_course is not None, "Should find ENVS 100L lab course"
        assert (
            lab_course["units"] == 0.0
        ), f"Lab course should have 0 units, got {lab_course['units']}"
        assert (
            lab_course["grade"] == "NG"
        ), f"Lab course should have NG grade, got {lab_course['grade']}"

        # Find courses with A- grade (should be rare for this high-performing student)
        a_minus_courses = [c for c in courses if c["grade"] == "A-"]
        assert len(a_minus_courses) >= 1, "Should find at least one A- course"

        # Verify specific A- course
        envs_course = next((c for c in a_minus_courses if c["subject"] == "ENVS"), None)
        assert envs_course is not None, "Should find ENVS course with A- grade"
        assert (
            envs_course["number"] == "100"
        ), f"ENVS A- course should be 100, got {envs_course['number']}"

    def test_multiline_title_parsing(self):
        """Test that courses with multiline titles are parsed correctly."""
        # Upload and parse the transcript
        with open(self.test_transcript_path, "rb") as pdf_file:
            files = {"file": ("Academic Transcript.pdf", pdf_file, "application/pdf")}
            upload_response = self.client.post("/api/v1/upload", files=files)

        assert upload_response.status_code == 200
        courses = upload_response.json()

        # Find course known to have multiline title
        software_dev_course = next(
            (c for c in courses if c["subject"] == "CS" and c["number"] == "272N"), None
        )
        assert software_dev_course is not None, "Should find CS 272N course"

        # Title should contain both parts of the multiline title
        title = software_dev_course["title"]
        assert (
            "Software Dev" in title
        ), f"Title should contain 'Software Dev', got: {title}"
        assert (
            "Code Review" in title
        ), f"Title should contain 'Code Review', got: {title}"

        # Find another multiline course
        envs_course = next(
            (c for c in courses if c["subject"] == "ENVS" and c["number"] == "100"),
            None,
        )
        assert envs_course is not None, "Should find ENVS 100 course"
        assert (
            "Environ" in envs_course["title"]
        ), f"Title should contain 'Environ', got: {envs_course['title']}"
        assert (
            "Lab" in envs_course["title"]
        ), f"Title should contain 'Lab', got: {envs_course['title']}"

    def test_performance_and_consistency(self):
        """Test that the system performs consistently with multiple runs."""
        results = []

        # Run the same upload/calculation multiple times
        for i in range(3):
            # Upload transcript
            with open(self.test_transcript_path, "rb") as pdf_file:
                files = {
                    "file": ("Academic Transcript.pdf", pdf_file, "application/pdf")
                }
                upload_response = self.client.post("/api/v1/upload", files=files)

            assert upload_response.status_code == 200
            courses = upload_response.json()

            # Calculate GPA
            gpa_response = self.client.post("/api/v1/gpa", json={"courses": courses})
            assert gpa_response.status_code == 200
            gpa_data = gpa_response.json()

            results.append({"course_count": len(courses), "gpa": gpa_data})

        # Verify all runs produced identical results
        first_result = results[0]
        for i, result in enumerate(results[1:], 1):
            assert (
                result["course_count"] == first_result["course_count"]
            ), f"Run {i+1}: Course count mismatch"
            assert result["gpa"] == first_result["gpa"], f"Run {i+1}: GPA mismatch"

    def _verify_course_parsing(self, courses):
        """Helper method to verify course parsing results."""
        # Verify course structure
        for course in courses:
            required_fields = {"subject", "number", "title", "units", "grade"}
            assert all(
                field in course for field in required_fields
            ), f"Course missing required fields: {course}"

            # Verify field types
            assert isinstance(
                course["subject"], str
            ), f"Subject should be string: {course}"
            assert isinstance(
                course["number"], str
            ), f"Number should be string: {course}"
            assert isinstance(course["title"], str), f"Title should be string: {course}"
            assert isinstance(
                course["units"], (int, float)
            ), f"Units should be numeric: {course}"
            assert isinstance(course["grade"], str), f"Grade should be string: {course}"

            # Verify field constraints
            assert len(course["subject"]) >= 2, f"Subject too short: {course}"
            assert len(course["number"]) >= 1, f"Number too short: {course}"
            assert len(course["title"].strip()) >= 1, f"Title empty: {course}"
            assert course["units"] >= 0, f"Units negative: {course}"
            assert len(course["grade"]) >= 1, f"Grade empty: {course}"

        # Verify we have the expected variety of data
        subjects = {course["subject"] for course in courses}
        grades = {course["grade"] for course in courses}

        assert "CS" in subjects, "Should have CS courses"
        assert "MATH" in subjects, "Should have MATH courses"
        assert "PHIL" in subjects, "Should have PHIL courses"

        assert "A" in grades, "Should have A grades"
        assert "A+" in grades, "Should have A+ grades"
        assert "TCR" in grades, "Should have transfer credits"
        assert "IP" in grades, "Should have in-progress courses"

    def _verify_gpa_calculation(self, gpa):
        """Helper method to verify GPA calculation results."""
        # Verify field types
        assert isinstance(gpa, (int, float)), "GPA should be numeric"

        # Verify reasonable ranges
        assert 0.0 <= gpa <= 4.0, f"GPA should be 0.0-4.0, got {gpa}"

        # Verify expected values for this specific transcript
        assert gpa == self.expected_gpa, f"Expected GPA {self.expected_gpa}, got {gpa}"
