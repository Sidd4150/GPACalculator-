"""
Test configuration and fixtures for the GPA calculator tests.
"""

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    # Disable rate limiting during tests
    os.environ["TESTING"] = "true"

    # Set other test-specific environment variables
    os.environ["ENVIRONMENT"] = "testing"

    yield

    # Clean up after tests
    os.environ.pop("TESTING", None)
    os.environ.pop("ENVIRONMENT", None)
