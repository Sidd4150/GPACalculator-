"""
Test rate limiting functionality.
"""

import os
import unittest
from fastapi.testclient import TestClient
from app.main import app


class TestRateLimiting(unittest.TestCase):
    """Test rate limiting functionality."""

    def setUp(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_rate_limiting_disabled_in_test_mode(self):
        """Test that rate limiting is disabled when TESTING=true."""
        # Verify TESTING is set
        self.assertEqual(os.getenv("TESTING"), "true")

        # Make multiple rapid requests - should all succeed since rate limiting is disabled
        for _ in range(15):  # More than the upload limit
            response = self.client.get("/api/v1/health")
            self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
