"""
Test configuration and fixtures for the GPA calculator tests.
"""

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    os.environ["ENVIRONMENT"] = "testing"
    yield
    os.environ.pop("ENVIRONMENT", None)
