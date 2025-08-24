"""
Essential end-to-end integration tests for the complete GPA calculator workflow.
"""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


class TestEndToEndIntegration:
    """Essential integration tests using the actual transcript PDF."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        self.test_transcript_path = (
            Path(__file__).parent
            / "fixtures"
            / "transcripts"
            / "Academic Transcript.pdf"
        )

        # Expected results from actual transcript
        self.expected_total_courses = 44
        self.expected_gpa = 3.99

    def test_complete_workflow_upload_and_gpa_calculation(self):
        """Test the complete workflow: upload transcript and calculate GPA."""
        # Upload the actual transcript PDF
        with open(self.test_transcript_path, "rb") as pdf_file:
            files = {"file": ("Academic Transcript.pdf", pdf_file, "application/pdf")}
            upload_response = self.client.post("/api/v1/upload", files=files)

        assert (
            upload_response.status_code == 200
        ), f"Upload failed: {upload_response.text}"
        courses = upload_response.json()

        # Verify expected number of courses
        assert (
            len(courses) == self.expected_total_courses
        ), f"Expected {self.expected_total_courses} courses, got {len(courses)}"

        # Calculate GPA using parsed courses
        gpa_payload = {"courses": courses}
        gpa_response = self.client.post("/api/v1/gpa", json=gpa_payload)

        assert (
            gpa_response.status_code == 200
        ), f"GPA calculation failed: {gpa_response.text}"
        gpa = gpa_response.json()

        # Verify GPA is close to expected (within 0.01)
        assert (
            abs(gpa - self.expected_gpa) < 0.01
        ), f"Expected GPA ~{self.expected_gpa}, got {gpa}"

    def test_course_parsing_accuracy(self):
        """Test that specific known courses are parsed correctly."""
        with open(self.test_transcript_path, "rb") as pdf_file:
            files = {"file": ("Academic Transcript.pdf", pdf_file, "application/pdf")}
            upload_response = self.client.post("/api/v1/upload", files=files)

        courses = upload_response.json()
        course_dict = {f"{c['subject']}_{c['number']}": c for c in courses}

        # Verify key course types are present
        assert "HIST_120" in course_dict, "Transfer credit course missing"
        assert (
            course_dict["HIST_120"]["grade"] == "TCR"
        ), "Transfer credit grade incorrect"

        assert "CS_110" in course_dict, "Institution course missing"
        assert (
            course_dict["CS_110"]["grade"] == "A+"
        ), "Institution course grade incorrect"

        assert "CS_256" in course_dict, "In-progress course missing"
        assert (
            course_dict["CS_256"]["grade"] == "IP"
        ), "In-progress course grade incorrect"

    def test_gpa_calculation_excludes_non_gpa_courses(self):
        """Test that GPA calculation properly excludes non-GPA courses."""
        with open(self.test_transcript_path, "rb") as pdf_file:
            files = {"file": ("Academic Transcript.pdf", pdf_file, "application/pdf")}
            upload_response = self.client.post("/api/v1/upload", files=files)

        courses = upload_response.json()

        # Count different course types
        tcr_courses = [c for c in courses if c["grade"] == "TCR"]
        ip_courses = [c for c in courses if c["grade"] == "IP"]
        gpa_courses = [c for c in courses if c["grade"] not in ["TCR", "IP", "NG"]]

        # Verify we have the expected distribution
        assert len(tcr_courses) > 0, "Should have transfer credit courses"
        assert len(ip_courses) > 0, "Should have in-progress courses"
        assert len(gpa_courses) > 25, "Should have substantial GPA-counting courses"

        # Calculate GPA and verify it's reasonable
        gpa_response = self.client.post("/api/v1/gpa", json={"courses": courses})
        gpa = gpa_response.json()

        # GPA should be realistic (between 0 and 4.0)
        assert 0.0 <= gpa <= 4.0, f"GPA {gpa} outside valid range"
        assert gpa > 3.9, f"Expected high GPA based on transcript, got {gpa}"
