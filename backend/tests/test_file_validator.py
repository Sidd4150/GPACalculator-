"""
Test file validation service.
"""

import unittest
from unittest.mock import Mock

from app.config import Settings
from app.utils.file_validator import FileValidator


class TestFileValidator(unittest.TestCase):
    """Test FileValidator service class."""

    def setUp(self):
        """Set up test file validator."""
        self.settings = Settings()
        self.validator = FileValidator(self.settings)

    def test_file_validation_service_initialization(self):
        """Test file validation service exists and initializes."""
        self.assertIsNotNone(self.validator)

    def test_file_size_validation(self):
        """Test file size validation."""
        # Test valid content
        pdf_content = b"%PDF-1.4\n%test content"
        self.validator.validate_file_content(pdf_content, "test.pdf")

        # Test too large
        large_content = b"x" * (self.settings.max_file_size_bytes + 1)
        with self.assertRaises(ValueError):
            self.validator.validate_file_content(large_content, "large.pdf")

        # Test empty file
        with self.assertRaises(ValueError):
            self.validator.validate_file_content(b"", "empty.pdf")

    def test_upload_file_validation_with_valid_pdf(self):
        """Test file validator with valid PDF."""
        mock_file = Mock()
        mock_file.filename = "transcript.pdf"
        mock_file.content_type = "application/pdf"

        # Should not raise exception
        self.validator.validate_upload_file(mock_file)

    def test_upload_file_validation_with_invalid_extension(self):
        """Test file validator with invalid extension."""
        mock_file = Mock()
        mock_file.filename = "document.txt"
        mock_file.content_type = "text/plain"

        with self.assertRaises(ValueError):
            self.validator.validate_upload_file(mock_file)

    def test_file_content_validation(self):
        """Test file content validation."""
        # Valid PDF content
        pdf_content = b"%PDF-1.4\n%some pdf content here"
        self.validator.validate_file_content(
            pdf_content, "test.pdf"
        )  # Should not raise

        # Oversized content
        large_content = b"x" * (self.settings.max_file_size_bytes + 1)
        with self.assertRaises(ValueError):
            self.validator.validate_file_content(large_content, "large.pdf")


if __name__ == "__main__":
    unittest.main()
