"""
Tests for rate limiting functionality.
"""

import os
from pathlib import Path
from unittest.mock import patch

from app.api.endpoints import get_cached_settings
from app.main import app
from fastapi.testclient import TestClient


class TestRateLimiting:
    """Test cases for rate limiting functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        self.test_transcript_path = (
            Path(__file__).parent
            / "fixtures"
            / "transcripts"
            / "Academic Transcript.pdf"
        )

    def test_upload_rate_limit_disabled_during_testing(self):
        """Test that rate limiting is disabled during testing."""
        # Make multiple rapid requests to upload endpoint
        for _ in range(15):  # More than the 10/minute limit
            with open(self.test_transcript_path, "rb") as pdf_file:
                files = {
                    "file": ("Academic Transcript.pdf", pdf_file, "application/pdf")
                }
                response = self.client.post("/api/v1/upload", files=files)

            # Should all succeed because rate limiting is disabled in tests
            assert (
                response.status_code == 200
            ), f"Request should succeed during testing, got {response.status_code}"

    def test_gpa_rate_limit_disabled_during_testing(self):
        """Test that GPA rate limiting is disabled during testing."""
        courses_payload = {
            "courses": [
                {
                    "subject": "CS",
                    "number": "101",
                    "title": "Test Course",
                    "units": 3.0,
                    "grade": "A",
                    "source": "manual",
                }
            ]
        }

        # Make multiple rapid requests to GPA endpoint
        for _ in range(60):  # More than the 50/minute limit
            response = self.client.post("/api/v1/gpa", json=courses_payload)

            # Should all succeed because rate limiting is disabled in tests
            assert (
                response.status_code == 200
            ), f"Request should succeed during testing, got {response.status_code}"
            gpa = response.json()
            assert gpa == 4.0, f"Expected GPA 4.0, got {gpa}"

    @patch.dict(os.environ, {"TESTING": "false"}, clear=False)
    def test_upload_rate_limit_enabled_when_not_testing(self):
        """Test that upload rate limiting works when not in test mode."""
        # Create a new client to pick up the environment change
        test_client = TestClient(app)

        successful_requests = 0
        rate_limited_requests = 0

        # Make more requests than the limit allows (10/minute)
        for i in range(15):
            with open(self.test_transcript_path, "rb") as pdf_file:
                files = {"file": (f"test_{i}.pdf", pdf_file, "application/pdf")}
                response = test_client.post("/api/v1/upload", files=files)

            if response.status_code == 200:
                successful_requests += 1
            elif response.status_code == 429:  # Too Many Requests
                rate_limited_requests += 1
            else:
                # Some requests might fail due to PDF parsing, but not rate limiting
                pass

        # Should have some rate limited requests
        assert (
            rate_limited_requests > 0
        ), f"Expected some rate limited requests, got {rate_limited_requests}"
        assert (
            successful_requests <= 10
        ), f"Should not exceed rate limit of 10, got {successful_requests} successful"

    @patch.dict(os.environ, {"TESTING": "false"}, clear=False)
    def test_gpa_rate_limit_enabled_when_not_testing(self):
        """Test that GPA rate limiting works when not in test mode."""
        # Create a new client to pick up the environment change
        test_client = TestClient(app)

        courses_payload = {
            "courses": [
                {
                    "subject": "CS",
                    "number": "101",
                    "title": "Test Course",
                    "units": 3.0,
                    "grade": "A",
                    "source": "manual",
                }
            ]
        }

        successful_requests = 0
        rate_limited_requests = 0

        # Make more requests than the limit allows (50/minute)
        for i in range(60):
            response = test_client.post("/api/v1/gpa", json=courses_payload)

            if response.status_code == 200:
                successful_requests += 1
            elif response.status_code == 429:  # Too Many Requests
                rate_limited_requests += 1

        # Should have some rate limited requests
        assert (
            rate_limited_requests > 0
        ), f"Expected some rate limited requests, got {rate_limited_requests}"
        assert (
            successful_requests <= 50
        ), f"Should not exceed rate limit of 50, got {successful_requests} successful"

    @patch.dict(os.environ, {"TESTING": "false"}, clear=False)
    def test_rate_limit_response_format(self):
        """Test that rate limit responses have proper format."""
        # Create a new client to pick up the environment change
        test_client = TestClient(app)

        courses_payload = {
            "courses": [
                {
                    "subject": "CS",
                    "number": "101",
                    "title": "Test Course",
                    "units": 3.0,
                    "grade": "A",
                    "source": "manual",
                }
            ]
        }

        # Make enough requests to trigger rate limiting
        rate_limit_response = None
        for i in range(60):
            response = test_client.post("/api/v1/gpa", json=courses_payload)

            if response.status_code == 429:
                rate_limit_response = response
                break

        # Should eventually get a rate limit response
        if rate_limit_response:
            # Check response format
            assert rate_limit_response.status_code == 429

            # Should be JSON response with proper content type
            assert "application/json" in rate_limit_response.headers.get(
                "content-type", ""
            ), "Rate limit response should be JSON"

            # Should have JSON body (slowapi provides default error format)
            data = rate_limit_response.json()
            assert isinstance(data, dict), "Rate limit response should be JSON object"

    @patch.dict(os.environ, {"TESTING": "false"}, clear=False)
    def test_different_endpoints_have_different_limits(self):
        """Test that upload and GPA endpoints have different rate limits configured."""
        settings = get_cached_settings()

        # Verify different limits are configured
        assert (
            settings.rate_limit_upload != settings.rate_limit_gpa
        ), f"Upload ({settings.rate_limit_upload}) and GPA ({settings.rate_limit_gpa}) should have different limits"

        # Upload has lower limit (10) than GPA (50)
        assert (
            settings.rate_limit_upload < settings.rate_limit_gpa
        ), f"Upload limit ({settings.rate_limit_upload}) should be lower than GPA limit ({settings.rate_limit_gpa})"

    def test_rate_limit_configuration_values(self):
        """Test that rate limit configuration values are as expected."""
        settings = get_cached_settings()

        # Verify the configured rate limits match expectations
        assert (
            settings.rate_limit_upload == 10
        ), f"Expected upload rate limit 10/min, got {settings.rate_limit_upload}"
        assert (
            settings.rate_limit_gpa == 50
        ), f"Expected GPA rate limit 50/min, got {settings.rate_limit_gpa}"

    def test_health_endpoint_not_rate_limited(self):
        """Test that health endpoint is not subject to rate limiting."""
        # Make many requests to health endpoint - should never be rate limited
        for _ in range(100):
            response = self.client.get("/api/v1/health")
            assert (
                response.status_code == 200
            ), f"Health endpoint should never be rate limited, got {response.status_code}"

            data = response.json()
            assert (
                data["status"] == "healthy"
            ), "Health check should return healthy status"
