"""
Logging configuration for the GPA Calculator application.
"""

import logging
import sys
from pathlib import Path


def setup_logger(name: str = "gpa_calculator", level: str = "INFO") -> logging.Logger:
    """
    Set up a logger with consistent formatting.

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    log_instance = logging.getLogger(name)

    # Prevent duplicate handlers if logger already exists
    if log_instance.handlers:
        return log_instance

    # Set logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    log_instance.setLevel(numeric_level)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    log_instance.addHandler(console_handler)

    # File handler (optional, for production)
    try:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        file_handler = logging.FileHandler(log_dir / "gpa_calculator.log")
        file_handler.setFormatter(formatter)
        log_instance.addHandler(file_handler)
    except (OSError, PermissionError):
        # If we can't write to file, continue with console logging only
        log_instance.warning("Could not create file handler, using console logging only")

    return log_instance


# Create default logger
logger = setup_logger()
