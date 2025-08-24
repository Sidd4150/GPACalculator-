"""
Constants for the GPA Calculator application.
"""

# USF Grade Point Scale
GRADE_POINTS = {
    "A+": 4.0,
    "A": 4.0,
    "A-": 3.7,
    "B+": 3.3,
    "B": 3.0,
    "B-": 2.7,
    "C+": 2.3,
    "C": 2.0,
    "C-": 1.7,
    "D+": 1.3,
    "D": 1.0,
    "D-": 0.7,
    "F": 0.0,
}

# Non-GPA grades that should be excluded from GPA calculations
NON_GPA_GRADES = {"P", "S", "U", "I", "IP", "W", "NR", "AU", "TCR", "NG"}

# Special grade markers
TRANSFER_CREDIT_GRADE = "TCR"
IN_PROGRESS_GRADE = "IP"
FAILING_GRADE = "F"

# Course Validation Patterns
COURSE_SUBJECT_PATTERN = r"^[A-Z]{2,6}$"
COURSE_NUMBER_PATTERN = r"^(\d+[A-Z]?|\d*XX)$"

# File Processing Constants
SUPPORTED_FILE_EXTENSIONS = [".pdf"]
SUPPORTED_MIME_TYPES = ["application/pdf"]

# PDF Processing Constants
PDF_HEADER_SIGNATURE = b"%PDF"
PDF_EXTRACTION_ENCODING = "utf-8"

# HTTP Status Messages
ERROR_MESSAGES = {
    "NO_FILE": "No file provided",
    "INVALID_FILE_TYPE": "Only PDF files are supported. Please upload a PDF transcript.",
    "EMPTY_FILE": "Uploaded file is empty",
    "FILE_TOO_LARGE": "File size exceeds maximum limit",
    "CORRUPTED_PDF": "PDF file is corrupted or invalid",
    "NO_COURSES_FOUND": "No courses found in the transcript",
    "INVALID_TRANSCRIPT": "Transcript format not supported",
    "RATE_LIMIT_EXCEEDED": "Rate limit exceeded. Please try again later.",
    "INVALID_COURSE_DATA": "Invalid course data provided",
    "GPA_CALCULATION_ERROR": "Error calculating GPA",
    "INTERNAL_ERROR": "Internal server error",
}

# Logging Constants
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# Validation Constants
MIN_COURSE_SUBJECT_LENGTH = 2
MAX_COURSE_SUBJECT_LENGTH = 6
MIN_COURSE_UNITS = 0.0
MAX_COURSE_UNITS = 20.0
MAX_COURSE_TITLE_LENGTH = 200
MIN_COURSE_TITLE_LENGTH = 1

# GPA Calculation Constants
GPA_PRECISION_DIGITS = 2
MIN_GPA = 0.0
MAX_GPA = 4.0

# Course Source Constants
COURSE_SOURCES = {
    "PARSED": "parsed",
    "MANUAL": "manual",
}

# Parsing Constants
PARSING_ARTIFACTS = [
    r"DO NOT PRINT.*$",
    r"Term Totals.*$",
    r"Attempt Hours.*$",
    r"Passed Hours.*$",
    r"Earned Hours.*$",
    r"GPA Hours.*$",
    r"Quality Points.*$",
    r"Current Term:.*$",
    r"Cumulative:.*$",
    r"Unofficial Transcript.*$",
    r"College:.*$",
    r"Major:.*$",
    r"Academic Standing:.*$",
    r"Subject.*$",
]

# Exception to HTTP mapping: exception_type -> (status_code, message_template)
EXCEPTION_HTTP_MAP = {
    # Application exceptions
    "ValidationError": (400, "Invalid input data: {message}"),
    "FileError": (400, "File processing error: {message}"),
    "ParsingError": (400, "Unable to parse transcript: {message}"),
    "CalculationError": (400, "GPA calculation failed: {message}"),
    # Standard exceptions
    "FileNotFoundError": (
        400,
        "File not found. Please ensure it's a valid transcript.",
    ),
    "PydanticValidationError": (422, "Invalid request format: {message}"),
    "ValueError": (400, "Invalid input: {message}"),
    # Generic fallback
    "Exception": (500, "Internal server error"),
}
