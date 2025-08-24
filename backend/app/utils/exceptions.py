"""
Exception handling utilities for API endpoints.
"""

from fastapi import HTTPException, status
from app.exceptions import FileError
from app.constants import EXCEPTION_HTTP_MAP, ERROR_MESSAGES
from app.utils.logger import setup_logger

logger = setup_logger("exceptions")


def map_exception_to_http(exc: Exception) -> HTTPException:
    """Map application exception to HTTP exception."""
    exc_type_name = type(exc).__name__

    # Try exact type match first
    if exc_type_name in EXCEPTION_HTTP_MAP:
        status_code, message_template = EXCEPTION_HTTP_MAP[exc_type_name]
        message = _format_exception_message(exc, message_template)

        # Handle file size errors with special status code
        if isinstance(exc, FileError) and "size" in str(exc).lower():
            status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE

        return HTTPException(status_code=status_code, detail=message)

    # Try parent class matches by checking inheritance
    for base_class in type(exc).__mro__:
        base_name = base_class.__name__
        if base_name in EXCEPTION_HTTP_MAP and base_name != exc_type_name:
            status_code, message_template = EXCEPTION_HTTP_MAP[base_name]
            message = _format_exception_message(exc, message_template)
            return HTTPException(status_code=status_code, detail=message)

    # Fallback to generic error
    logger.error("Unmapped exception: %s: %s", exc_type_name, exc)
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=ERROR_MESSAGES.get("INTERNAL_ERROR", "Internal server error"),
    )


def _format_exception_message(exc: Exception, message_template: str) -> str:
    """Format exception message using template."""
    if hasattr(exc, "message"):
        # Our custom exceptions have .message attribute
        return message_template.format(message=exc.message)
    elif "{message}" in message_template:
        # Standard exceptions use str(exc)
        return message_template.format(message=str(exc))
    else:
        # Template has no placeholder
        return message_template