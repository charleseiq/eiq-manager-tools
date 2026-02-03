"""Tests for load_config function."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

import importlib.util
from pathlib import Path

# Import analyze module directly from file path (handles hyphenated directory name)
analyze_path = Path(__file__).parent.parent / "pr-review-analysis" / "workflows" / "analyze.py"
spec = importlib.util.spec_from_file_location("analyze", analyze_path)
analyze = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analyze)

AnalysisState = analyze.AnalysisState
load_config = analyze.load_config


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_centralized_config(self, temp_config_file):
        """Test loading from centralized config.json."""
        state: AnalysisState = {
            "config_path": str(temp_config_file),
            "username": "testuser",
            "organization": "",
            "start_date": "",
            "end_date": "",
            "analysis_period": "",
            "output_dir": "",
            "github_token": "",
            "vertexai_project": "",
            "vertexai_location": "",
            "pr_data": [],
            "authored_pr_data": [],
            "review_data": {},
            "analysis_results": {},
            "markdown_report": "",
            "error": None,
            "period": "2025H2",
        }

        result = load_config(state)

        assert result["username"] == "testuser"
        assert result["organization"] == "TestOrg"
        assert result["start_date"] == "2025-07-01"
        assert result["end_date"] == "2025-12-31"
        assert "2025H2" in result["analysis_period"]
        assert result.get("error") is None

    def test_load_centralized_config_user_not_found(self, temp_config_file):
        """Test loading config with non-existent user."""
        state: AnalysisState = {
            "config_path": str(temp_config_file),
            "username": "nonexistent",
            "organization": "",
            "start_date": "",
            "end_date": "",
            "analysis_period": "",
            "output_dir": "",
            "github_token": "",
            "vertexai_project": "",
            "vertexai_location": "",
            "pr_data": [],
            "authored_pr_data": [],
            "review_data": {},
            "analysis_results": {},
            "markdown_report": "",
            "error": None,
            "period": "2025H2",
        }

        result = load_config(state)

        assert result.get("error") is not None
        assert "not found" in result["error"].lower()

    def test_load_centralized_config_period_not_found(self, temp_config_file):
        """Test loading config with non-existent period."""
        state: AnalysisState = {
            "config_path": str(temp_config_file),
            "username": "testuser",
            "organization": "",
            "start_date": "",
            "end_date": "",
            "analysis_period": "",
            "output_dir": "",
            "github_token": "",
            "vertexai_project": "",
            "vertexai_location": "",
            "pr_data": [],
            "authored_pr_data": [],
            "review_data": {},
            "analysis_results": {},
            "markdown_report": "",
            "error": None,
            "period": "2026H1",
        }

        result = load_config(state)

        assert result.get("error") is not None
        assert "period" in result["error"].lower()

    def test_load_individual_config(self, tmp_path):
        """Test loading from individual config file."""
        config_path = tmp_path / "user_config.json"
        config_data = {
            "username": "testuser",
            "organization": "TestOrg",
            "start_date": "2025-01-01",
            "end_date": "2025-06-30",
        }
        with open(config_path, "w") as f:
            json.dump(config_data, f)

        state: AnalysisState = {
            "config_path": str(config_path),
            "username": "",
            "organization": "",
            "start_date": "",
            "end_date": "",
            "analysis_period": "",
            "output_dir": "",
            "github_token": "",
            "vertexai_project": "",
            "vertexai_location": "",
            "pr_data": [],
            "authored_pr_data": [],
            "review_data": {},
            "analysis_results": {},
            "markdown_report": "",
            "error": None,
        }

        result = load_config(state)

        assert result["username"] == "testuser"
        assert result["organization"] == "TestOrg"
        assert result["start_date"] == "2025-01-01"
        assert result["end_date"] == "2025-06-30"
        assert result.get("error") is None

    def test_load_config_file_not_found(self):
        """Test loading non-existent config file."""
        state: AnalysisState = {
            "config_path": "/nonexistent/config.json",
            "username": "",
            "organization": "",
            "start_date": "",
            "end_date": "",
            "analysis_period": "",
            "output_dir": "",
            "github_token": "",
            "vertexai_project": "",
            "vertexai_location": "",
            "pr_data": [],
            "authored_pr_data": [],
            "review_data": {},
            "analysis_results": {},
            "markdown_report": "",
            "error": None,
        }

        result = load_config(state)

        assert result.get("error") is not None
        assert "not found" in result["error"].lower()

    def test_load_config_output_dir_from_state(self, temp_config_file):
        """Test that output_dir from state is preserved."""
        state: AnalysisState = {
            "config_path": str(temp_config_file),
            "username": "testuser",
            "organization": "",
            "start_date": "",
            "end_date": "",
            "analysis_period": "",
            "output_dir": "/custom/output",
            "github_token": "",
            "vertexai_project": "",
            "vertexai_location": "",
            "pr_data": [],
            "authored_pr_data": [],
            "review_data": {},
            "analysis_results": {},
            "markdown_report": "",
            "error": None,
            "period": "2025H2",
        }

        result = load_config(state)

        assert result["output_dir"] == "/custom/output"
