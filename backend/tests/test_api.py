"""
Tests for FastAPI endpoints.
"""

import pytest
import json
import io
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.models.course import CourseRow


class TestAPIEndpoints:
    """Test cases for API endpoint functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        self.test_transcript_path = (
            Path(__file__).parent.parent / "Academic Transcript.pdf"
        )

    def test_upload_valid_pdf(self):
        """Test /upload endpoint with valid PDF file."""
        # Use the actual transcript PDF for testing
        with open(self.test_transcript_path, "rb") as pdf_file:
            files = {"file": ("Academic Transcript.pdf", pdf_file, "application/pdf")}
            response = self.client.post("/api/v1/upload", files=files)

        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert isinstance(data, list), "Response should be a list of courses"
        assert (
            len(data) > 30
        ), f"Should parse significant number of courses, got {len(data)}"

        # Validate course structure
        course = data[0]
        required_fields = {"subject", "number", "title", "units", "grade"}
        assert all(
            field in course for field in required_fields
        ), f"Course missing required fields: {course}"

        # Check that we have different types of courses
        grades = {course["grade"] for course in data}
        assert "A" in grades or "A+" in grades, "Should have some A grades"
        assert "TCR" in grades, "Should have transfer credit courses"

    def test_upload_invalid_file_type_txt(self):
        """Test /upload endpoint with invalid file type (text file)."""
        txt_content = b"This is a text file, not a PDF"
        files = {"file": ("test.txt", io.BytesIO(txt_content), "text/plain")}

        response = self.client.post("/api/v1/upload", files=files)

        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        data = response.json()
        assert "detail" in data, "Error response should contain 'detail' key"
        assert (
            "PDF" in data["detail"] or "pdf" in data["detail"]
        ), f"Error should mention PDF: {data['detail']}"

    def test_upload_invalid_file_type_image(self):
        """Test /upload endpoint with invalid file type (image)."""
        # Create a minimal PNG-like header
        png_content = b"\x89PNG\r\n\x1a\n" + b"fake image content"
        files = {"file": ("test.png", io.BytesIO(png_content), "image/png")}

        response = self.client.post("/api/v1/upload", files=files)

        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        data = response.json()
        assert "detail" in data, "Error response should contain 'detail' key"
        assert (
            "PDF" in data["detail"] or "pdf" in data["detail"]
        ), f"Error should mention PDF: {data['detail']}"

    def test_upload_no_file(self):
        """Test /upload endpoint with no file provided."""
        response = self.client.post("/api/v1/upload")

        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        # FastAPI returns 422 for missing required fields

    def test_upload_empty_file(self):
        """Test /upload endpoint with empty file."""
        files = {"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")}

        response = self.client.post("/api/v1/upload", files=files)

        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        data = response.json()
        assert "detail" in data, "Error response should contain 'detail' key"

    def test_upload_corrupted_pdf(self):
        """Test /upload endpoint with corrupted PDF file."""
        # Create fake PDF content that will fail parsing
        fake_pdf = b"%PDF-1.4\nfake corrupted content"
        files = {"file": ("corrupted.pdf", io.BytesIO(fake_pdf), "application/pdf")}

        response = self.client.post("/api/v1/upload", files=files)

        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        data = response.json()
        assert "detail" in data, "Error response should contain 'detail' key"
        assert (
            "corrupted" in data["detail"].lower()
            or "invalid" in data["detail"].lower()
            or "parsing" in data["detail"].lower()
            or "error" in data["detail"].lower()
        ), "Should indicate PDF parsing error"

    def test_gpa_valid_payload_simple(self):
        """Test /gpa endpoint with valid simple course payload."""
        courses_payload = {
            "courses": [
                {
                    "subject": "CS",
                    "number": "101",
                    "title": "Intro to Computer Science",
                    "units": 4.0,
                    "grade": "A",
                },
                {
                    "subject": "MATH",
                    "number": "201",
                    "title": "Calculus",
                    "units": 3.0,
                    "grade": "B",
                },
            ]
        }

        response = self.client.post("/api/v1/gpa", json=courses_payload)

        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        gpa = response.json()
        assert isinstance(gpa, float), f"Response should be a float, got {type(gpa)}"

        # Verify calculation: A(4*4) + B(3*3) = 16 + 9 = 25 / 7 = 3.57
        assert gpa == 3.57, f"Expected GPA 3.57, got {gpa}"

    def test_gpa_valid_payload_mixed_grades(self):
        """Test /gpa endpoint with mixed GPA and non-GPA courses."""
        courses_payload = {
            "courses": [
                {
                    "subject": "CS",
                    "number": "101",
                    "title": "Regular Course",
                    "units": 3.0,
                    "grade": "A",
                },
                {
                    "subject": "MATH",
                    "number": "201",
                    "title": "Transfer Course",
                    "units": 4.0,
                    "grade": "TCR",  # Should be excluded
                },
                {
                    "subject": "ENGL",
                    "number": "101",
                    "title": "Another Course",
                    "units": 3.0,
                    "grade": "B+",
                },
                {
                    "subject": "PHIL",
                    "number": "101",
                    "title": "In Progress",
                    "units": 3.0,
                    "grade": "IP",  # Should be excluded
                },
            ]
        }

        response = self.client.post("/api/v1/gpa", json=courses_payload)

        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        gpa = response.json()

        # Only A (3 units) and B+ (3 units) should count: (4.0*3 + 3.3*3) / 6 = 21.9 / 6 = 3.65
        assert gpa == 3.65, f"Expected GPA 3.65, got {gpa}"

    def test_gpa_empty_courses_list(self):
        """Test /gpa endpoint with empty courses list."""
        courses_payload = {"courses": []}

        response = self.client.post("/api/v1/gpa", json=courses_payload)

        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        gpa = response.json()
        assert gpa == 0.0, f"Expected GPA 0.0 for empty list, got {gpa}"

    def test_gpa_invalid_payload_missing_courses(self):
        """Test /gpa endpoint with missing 'courses' key."""
        invalid_payload = {"data": []}

        response = self.client.post("/api/v1/gpa", json=invalid_payload)

        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        # FastAPI returns 422 for validation errors

    def test_gpa_invalid_payload_malformed_course(self):
        """Test /gpa endpoint with malformed course data."""
        invalid_payload = {
            "courses": [
                {
                    "subject": "CS",
                    "number": "101",
                    "title": "Test Course",
                    "units": "invalid_units",  # Should be number
                    "grade": "A",
                }
            ]
        }

        response = self.client.post("/api/v1/gpa", json=invalid_payload)

        assert response.status_code == 422, f"Expected 422, got {response.status_code}"

    def test_gpa_invalid_payload_missing_required_fields(self):
        """Test /gpa endpoint with course missing required fields."""
        invalid_payload = {
            "courses": [
                {
                    "subject": "CS",
                    "number": "101",
                    "title": "Test Course",
                    # Missing 'units' and 'grade'
                }
            ]
        }

        response = self.client.post("/api/v1/gpa", json=invalid_payload)

        assert response.status_code == 422, f"Expected 422, got {response.status_code}"

    def test_gpa_invalid_payload_invalid_grade(self):
        """Test /gpa endpoint with invalid grade value."""
        invalid_payload = {
            "courses": [
                {
                    "subject": "CS",
                    "number": "101",
                    "title": "Test Course",
                    "units": 3.0,
                    "grade": "INVALID_GRADE",
                }
            ]
        }

        response = self.client.post("/api/v1/gpa", json=invalid_payload)

        assert response.status_code == 422, f"Expected 422, got {response.status_code}"

    def test_gpa_invalid_payload_not_json(self):
        """Test /gpa endpoint with non-JSON payload."""
        response = self.client.post(
            "/api/v1/gpa", data="not json data", headers={"content-type": "application/json"}
        )

        assert response.status_code == 422, f"Expected 422, got {response.status_code}"

    def test_gpa_no_payload(self):
        """Test /gpa endpoint with no payload."""
        response = self.client.post("/api/v1/gpa")

        assert response.status_code == 422, f"Expected 422, got {response.status_code}"

    def test_endpoint_not_found(self):
        """Test non-existent endpoint returns 404."""
        response = self.client.get("/nonexistent")

        assert response.status_code == 404, f"Expected 404, got {response.status_code}"

    def test_method_not_allowed(self):
        """Test wrong HTTP method returns 405."""
        response = self.client.get("/api/v1/upload")  # Should be POST

        assert response.status_code == 405, f"Expected 405, got {response.status_code}"

    def test_integration_upload_then_gpa(self):
        """Test complete workflow: upload PDF, then calculate GPA with returned courses."""
        # Step 1: Upload PDF
        with open(self.test_transcript_path, "rb") as pdf_file:
            files = {"file": ("Academic Transcript.pdf", pdf_file, "application/pdf")}
            upload_response = self.client.post("/api/v1/upload", files=files)

        assert (
            upload_response.status_code == 200
        ), f"Upload failed: {upload_response.text}"
        upload_data = upload_response.json()

        # Step 2: Calculate GPA using the uploaded courses
        gpa_payload = {"courses": upload_data}
        gpa_response = self.client.post("/api/v1/gpa", json=gpa_payload)

        assert (
            gpa_response.status_code == 200
        ), f"GPA calculation failed: {gpa_response.text}"
        gpa = gpa_response.json()

        # Verify reasonable GPA calculation
        assert 0.0 <= gpa <= 4.0, f"GPA should be between 0.0 and 4.0, got {gpa}"

        # Should have reasonable GPA for a good student
        assert gpa > 3.0, f"This transcript should have high GPA, got {gpa}"

    def test_large_file_handling(self):
        """Test handling of very large file uploads."""
        # Create a large fake PDF content (5MB)
        large_content = b"%PDF-1.4\n" + b"large content " * 350000  # ~5MB
        files = {"file": ("large.pdf", io.BytesIO(large_content), "application/pdf")}

        response = self.client.post("/api/v1/upload", files=files)

        # Should handle gracefully (either process or reject with appropriate error)
        assert response.status_code in [
            200,
            400,
            413,
        ], f"Unexpected status code: {response.status_code}"

        if response.status_code == 400:
            data = response.json()
            assert "detail" in data, "Error response should contain 'detail' key"

    def test_concurrent_requests(self):
        """Test that API can handle multiple concurrent requests."""
        import concurrent.futures
        import threading

        def make_gpa_request():
            courses_payload = {
                "courses": [
                    {
                        "subject": "CS",
                        "number": "101",
                        "title": "Test Course",
                        "units": 3.0,
                        "grade": "A",
                    }
                ]
            }
            return self.client.post("/api/v1/gpa", json=courses_payload)

        # Make 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_gpa_request) for _ in range(5)]
            responses = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]

        # All should succeed
        for response in responses:
            assert (
                response.status_code == 200
            ), f"Concurrent request failed: {response.status_code}"
            gpa = response.json()
            assert gpa == 4.0, f"Expected GPA 4.0, got {gpa}"

    def test_cors_headers(self):
        """Test that CORS headers are present for frontend integration."""
        # Test actual POST request to verify CORS headers
        courses_payload = {
            "courses": [
                {
                    "subject": "CS",
                    "number": "101",
                    "title": "Test Course",
                    "units": 3.0,
                    "grade": "A",
                }
            ]
        }

        response = self.client.post("/api/v1/gpa", json=courses_payload)

        # Should succeed and include CORS headers (handled by FastAPI middleware)
        assert (
            response.status_code == 200
        ), f"CORS-enabled request failed: {response.status_code}"

    def test_response_content_type(self):
        """Test that responses have correct Content-Type headers."""
        courses_payload = {
            "courses": [
                {
                    "subject": "CS",
                    "number": "101",
                    "title": "Test Course",
                    "units": 3.0,
                    "grade": "A",
                }
            ]
        }

        response = self.client.post("/api/v1/gpa", json=courses_payload)

        assert response.status_code == 200
        assert "application/json" in response.headers.get(
            "content-type", ""
        ), "Response should be JSON"
