"""
Shared configuration utilities for CLI tools.

This module provides common functions for handling configuration files,
both centralized and individual user configs.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def format_analysis_period(start_date: str, end_date: str) -> str:
    """
    Format analysis period string from dates.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        Formatted period string (e.g., "2025H2 (July 1 - December 31, 2025)")
    """
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    # Match common period patterns
    period_formats = {
        (7, 1, 12, 31): lambda y: f"{y}H2 (July 1 - December 31, {y})",
        (1, 1, 6, 30): lambda y: f"{y}H1 (January 1 - June 30, {y})",
    }

    pattern_key = (start_dt.month, start_dt.day, end_dt.month, end_dt.day)
    if pattern_key in period_formats:
        return period_formats[pattern_key](start_dt.year)

    return f"{start_date} to {end_date}"


def create_github_config(
    username: str,
    start_date: str,
    end_date: str,
    organization: str,
    output_dir: Path,
) -> Path:
    """
    Create or update GitHub config.json for the user.

    Args:
        username: GitHub username
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        organization: GitHub organization name
        output_dir: Directory where config will be created

    Returns:
        Path to the created config file
    """
    config_file = output_dir / "config.json"
    period_str = format_analysis_period(start_date, end_date)

    config: dict[str, Any] = {
        "username": username,
        "organization": organization,
        "start_date": start_date,
        "end_date": end_date,
        "analysis_period": period_str,
        "notes": [
            "This config file stores the analysis parameters for this user",
            "Update start_date and end_date to change the analysis window",
            "The review_data.json file should be in this same directory",
        ],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)

    return config_file


def create_jira_config(
    username: str,
    start_date: str,
    end_date: str,
    output_dir: Path,
) -> Path:
    """
    Create or update JIRA config.json for the user.

    Args:
        username: JIRA username/email
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        output_dir: Directory where config will be created

    Returns:
        Path to the created config file
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    config_file = output_path / "config.json"

    if not config_file.exists():
        config: dict[str, Any] = {
            "username": username,
            "start_date": start_date,
            "end_date": end_date,
        }
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)

    return config_file


def load_centralized_config(config_path: Path) -> dict[str, Any] | None:
    """
    Load centralized config.json if it exists.

    Args:
        config_path: Path to config.json file

    Returns:
        Config data dict if file exists, None otherwise
    """
    if config_path.exists():
        try:
            with open(config_path) as f:
                return json.load(f)
        except Exception:
            return None
    return None


def user_exists_in_config(config_data: dict[str, Any], username: str) -> bool:
    """
    Check if a user exists in centralized config.

    Args:
        config_data: Configuration dict from config.json
        username: Username to check

    Returns:
        True if user exists, False otherwise
    """
    return any(u.get("username") == username for u in config_data.get("users", []))
