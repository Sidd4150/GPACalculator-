"""
Custom exception classes for the GPA Calculator application.
"""


class GPACalculatorException(Exception):
    """Base exception class for all GPA calculator errors."""

    def __init__(self, message: str, details: str = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class ValidationError(GPACalculatorException):
    """Raised when input validation fails."""


class FileError(GPACalculatorException):
    """Raised when file processing fails (upload, size, format, corruption)."""


class ParsingError(GPACalculatorException):
    """Raised when transcript parsing fails."""


class CalculationError(GPACalculatorException):
    """Raised when GPA calculation fails."""
