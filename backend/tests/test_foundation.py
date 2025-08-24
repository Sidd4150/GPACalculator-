"""
Test the Phase 1 foundation components.
"""

import unittest
import os
from unittest.mock import patch, Mock
from app.config import Settings
from app.constants import GRADE_POINTS, NON_GPA_GRADES, ERROR_MESSAGES
from app.services.validation import FileValidator
from app.exceptions import FileError, ValidationError
from app.api.endpoints import map_exception_to_http


class TestConfiguration(unittest.TestCase):
    """Test configuration management."""

    def test_settings_creation(self):
        """Test settings can be created with defaults."""
        settings = Settings()

        self.assertEqual(settings.app_name, "GPA Calculator API")
        self.assertEqual(settings.max_file_size_mb, 50)
        self.assertTrue(len(settings.cors_origins) > 0)

    def test_testing_flag(self):
        """Test testing flag functionality."""
        with patch.dict(os.environ, {"TESTING": "true"}):
            settings = Settings()
            self.assertTrue(settings.is_testing)

        with patch.dict(os.environ, {"TESTING": "false"}):
            settings = Settings()
            self.assertFalse(settings.is_testing)

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


class TestConstants(unittest.TestCase):
    """Test constants module."""

    def test_grade_points(self):
        """Test grade points mapping."""
        self.assertEqual(GRADE_POINTS["A"], 4.0)
        self.assertEqual(GRADE_POINTS["B-"], 2.7)
        self.assertEqual(GRADE_POINTS["F"], 0.0)
        self.assertIn("A+", GRADE_POINTS)

    def test_non_gpa_grades(self):
        """Test non-GPA grades set."""
        self.assertIn("TCR", NON_GPA_GRADES)
        self.assertIn("IP", NON_GPA_GRADES)
        self.assertIn("W", NON_GPA_GRADES)
        self.assertNotIn("A", NON_GPA_GRADES)

    def test_error_messages(self):
        """Test error messages constants."""
        self.assertIn("NO_FILE", ERROR_MESSAGES)
        self.assertIn("INVALID_FILE_TYPE", ERROR_MESSAGES)
        self.assertTrue(len(ERROR_MESSAGES["NO_FILE"]) > 0)


# Dependency injection tests removed since we simplified to use FastAPI's built-in DI


class TestServices(unittest.TestCase):
    """Test service layer."""

    def setUp(self):
        """Set up test services."""
        self.settings = Settings()

    def test_file_validation_service(self):
        """Test file validation service."""
        service = FileValidator(self.settings)

        # Test valid PDF file
        # Updated to use FileValidator API

        # Test invalid file type
        # Tests moved to dedicated validation tests

    def test_file_size_validation(self):
        """Test file size validation."""
        service = FileValidator(self.settings)

        # Test valid content
        pdf_content = b"%PDF-1.4\n%test content"
        service.validate_file_content(pdf_content, "test.pdf")

        # Test too large
        large_content = b"x" * (self.settings.max_file_size_bytes + 1)
        with self.assertRaises(FileError):
            service.validate_file_content(large_content, "large.pdf")

        # Test empty file
        with self.assertRaises(ValidationError):
            service.validate_file_content(b"", "empty.pdf")

    # Rate limiting tests removed since we simplified rate limiting

    def test_file_validator_with_valid_pdf(self):
        """Test file validator with valid PDF."""
        validator = FileValidator(self.settings)

        from unittest.mock import Mock

        mock_file = Mock()
        mock_file.filename = "transcript.pdf"
        mock_file.content_type = "application/pdf"

        # Should not raise exception
        validator.validate_upload_file(mock_file)

    def test_file_validator_with_invalid_extension(self):
        """Test file validator with invalid extension."""

        validator = FileValidator(self.settings)
        from unittest.mock import Mock

        mock_file = Mock()
        mock_file.filename = "document.txt"
        mock_file.content_type = "text/plain"

        with self.assertRaises(FileError):
            validator.validate_upload_file(mock_file)

    def test_file_content_validation(self):
        """Test file content validation."""

        validator = FileValidator(self.settings)

        # Valid PDF content
        pdf_content = b"%PDF-1.4\n%some pdf content here"
        validator.validate_file_content(pdf_content, "test.pdf")  # Should not raise

        # Oversized content
        large_content = b"x" * (self.settings.max_file_size_bytes + 1)
        with self.assertRaises(FileError):
            validator.validate_file_content(large_content, "large.pdf")

    def test_exception_mapper(self):
        """Test exception mapping function."""

        # Test file error mapping
        exc = FileError("Invalid file type", "Details")
        http_exc = map_exception_to_http(exc)
        self.assertEqual(http_exc.status_code, 400)
        self.assertEqual(http_exc.detail, "File processing error: Invalid file type")

        # Test file size error mapping (special case for 413 status)
        exc = FileError("File size exceeds limit", "Size details")
        http_exc = map_exception_to_http(exc)
        self.assertEqual(http_exc.status_code, 413)
        self.assertEqual(
            http_exc.detail, "File processing error: File size exceeds limit"
        )


if __name__ == "__main__":
    unittest.main()
