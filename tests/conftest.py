"""Test configuration."""

import pytest
import os


@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables."""
    os.environ["OPENAI_API_KEY"] = "test-key"
    os.environ["DATABASE_URL"] = "sqlite:///test.db"
    yield
    # Cleanup after tests
