"""
Test configuration management.
"""

import unittest

from app.config import Settings


class TestSettings(unittest.TestCase):
    """Test Settings class configuration management."""

    def test_settings_creation(self):
        """Test settings can be created with defaults."""
        settings = Settings()

        self.assertEqual(settings.app_name, "GPA Calculator API")
        self.assertEqual(settings.max_file_size_mb, 50)
        self.assertTrue(len(settings.cors_origins) > 0)

    def test_cors_origins(self):
        """Test CORS origins configuration."""
        settings = Settings()
        origins = settings.cors_origins
        self.assertIn("http://localhost:3000", origins)
        self.assertIn("http://localhost:5173", origins)

    def test_file_size_calculation(self):
        """Test file size calculation in bytes."""
        settings = Settings(max_file_size_mb=25)
        expected_bytes = 25 * 1024 * 1024
        self.assertEqual(settings.max_file_size_bytes, expected_bytes)


if __name__ == "__main__":
    unittest.main()
