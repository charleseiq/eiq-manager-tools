"""Pytest configuration and fixtures."""

from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def mock_github_token():
    """Mock GitHub token for testing."""
    return "test_token_12345"


@pytest.fixture
def mock_vertexai_config():
    """Mock Vertex AI configuration."""
    return {
        "project": "test-project",
        "location": "us-east4",
    }


@pytest.fixture
def sample_pr_item():
    """Sample PR item from GitHub API."""
    return {
        "html_url": "https://github.com/EvolutionIQ/test-repo/pull/42",
        "title": "Test PR",
        "body": "This is a test PR",
        "number": 42,
        "state": "open",
    }


@pytest.fixture
def sample_review():
    """Sample review from GitHub API."""
    return {
        "user": {"login": "testuser"},
        "body": "Looks good!",
        "state": "APPROVED",
        "submitted_at": "2025-08-15T10:00:00Z",
    }


@pytest.fixture
def sample_comment():
    """Sample comment from GitHub API."""
    return {
        "user": {"login": "testuser"},
        "body": "Nice work!",
        "created_at": "2025-08-15T11:00:00Z",
    }


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file for testing."""
    config_path = tmp_path / "config.json"
    config_data = {
        "organization": "TestOrg",
        "periods": {
            "2025H2": {
                "start_date": "2025-07-01",
                "end_date": "2025-12-31",
            }
        },
        "users": [
            {
                "username": "testuser",
                "name": "Test User",
            }
        ],
    }
    import json

    with open(config_path, "w") as f:
        json.dump(config_data, f)
    return config_path


@pytest.fixture
def mock_rich_available():
    """Mock rich library availability."""
    import importlib.util

    analyze_path = Path(__file__).parent.parent / "eiq" / "gh-analysis" / "workflows" / "analyze.py"
    spec = importlib.util.spec_from_file_location("analyze", analyze_path)
    analyze_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(analyze_module)
    with patch.object(analyze_module, "RICH_AVAILABLE", True):
        yield


@pytest.fixture
def mock_rich_unavailable():
    """Mock rich library unavailability."""
    import importlib.util

    analyze_path = Path(__file__).parent.parent / "eiq" / "gh-analysis" / "workflows" / "analyze.py"
    spec = importlib.util.spec_from_file_location("analyze", analyze_path)
    analyze_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(analyze_module)
    with patch.object(analyze_module, "RICH_AVAILABLE", False):
        yield
