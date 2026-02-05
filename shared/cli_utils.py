"""
Shared CLI utilities for gh-analyze and jira-analyze.

This module contains common functions used by both CLI tools:
- slugify/unslugify
- period parsing
- user identity resolution
- time range resolution
"""

import argparse
import re
from datetime import datetime
from typing import Any


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    # Convert to lowercase
    text = text.lower()
    # Replace spaces and underscores with hyphens
    text = re.sub(r"[\s_]+", "-", text)
    # Remove all non-alphanumeric characters except hyphens
    text = re.sub(r"[^a-z0-9-]", "", text)
    # Remove multiple consecutive hyphens
    text = re.sub(r"-+", "-", text)
    # Remove leading/trailing hyphens
    text = text.strip("-")
    return text


def unslugify(slug: str) -> str:
    """Convert a slug back to title case (e.g., 'varun-sundar' -> 'Varun Sundar')."""
    if not slug:
        return slug
    # Split by hyphens and title case each word
    words = slug.split("-")
    return " ".join(word.capitalize() for word in words if word)


def parse_period(period_str: str) -> tuple[str, str]:
    """
    Parse period string to start and end dates.

    Supports:
    - H1/H2: Half-year (e.g., '2025H1' = Jan 1 - Jun 30, '2025H2' = Jul 1 - Dec 31)
    - Q1-Q4: Quarter (e.g., '2025Q1' = Jan 1 - Mar 31, '2025Q2' = Apr 1 - Jun 30)
    - Year: Full year (e.g., '2025' = Jan 1 - Dec 31)

    Returns:
        Tuple of (start_date, end_date) in YYYY-MM-DD format
    """
    period_str = period_str.strip().upper()

    # Half-year pattern: YYYYH1 or YYYYH2
    half_match = re.match(r"^(\d{4})H([12])$", period_str)
    if half_match:
        year = int(half_match.group(1))
        half = half_match.group(2)
        if half == "1":
            return (f"{year}-01-01", f"{year}-06-30")
        else:  # H2
            return (f"{year}-07-01", f"{year}-12-31")

    # Quarter pattern: YYYYQ1, YYYYQ2, YYYYQ3, YYYYQ4
    quarter_match = re.match(r"^(\d{4})Q([1-4])$", period_str)
    if quarter_match:
        year = int(quarter_match.group(1))
        quarter = int(quarter_match.group(2))
        quarter_dates = {
            1: (f"{year}-01-01", f"{year}-03-31"),
            2: (f"{year}-04-01", f"{year}-06-30"),
            3: (f"{year}-07-01", f"{year}-09-30"),
            4: (f"{year}-10-01", f"{year}-12-31"),
        }
        return quarter_dates[quarter]

    # Full year pattern: YYYY
    year_match = re.match(r"^(\d{4})$", period_str)
    if year_match:
        year = int(year_match.group(1))
        return (f"{year}-01-01", f"{year}-12-31")

    raise ValueError(
        f"Invalid period format: {period_str}. "
        "Use format: YYYYH1, YYYYH2, YYYYQ1-Q4, or YYYY (e.g., '2025H2', '2026Q1', '2025')"
    )


def resolve_user_identity(
    name: str | None,
    username: str | None,
    config_data: dict[str, Any] | None,
    parser: argparse.ArgumentParser,
    prefer_email: bool = False,
) -> tuple[str | None, str]:
    """
    Resolve user's name and username from CLI arguments and config.

    Args:
        name: User's name (may be slugified)
        username: User's username/email
        config_data: Configuration dict from config.json
        parser: ArgumentParser for error reporting
        prefer_email: If True, prefer email field over username (for JIRA)

    Returns:
        Tuple of (resolved_name, resolved_username)
    """
    resolved_name = name
    resolved_username = username

    # If name looks like a slug (contains hyphens and no spaces), convert to title case
    if resolved_name and "-" in resolved_name and " " not in resolved_name:
        resolved_name = unslugify(resolved_name)

    if resolved_name and not resolved_username:
        # Lookup username from name
        if not config_data:
            parser.error("Name provided but config.json not found. Use --username instead.")

        # Try exact match first (case-insensitive)
        found_user = None
        # Type narrowing: config_data is not None here (checked above)
        assert config_data is not None
        for user in config_data.get("users", []):
            user_name = user.get("name", "")
            if user_name.lower() == resolved_name.lower():
                found_user = user
                break

        # If not found, try matching against slugified version
        if not found_user:
            name_slug = slugify(resolved_name)
            for user in config_data.get("users", []):
                user_name = user.get("name", "")
                if slugify(user_name) == name_slug:
                    found_user = user
                    resolved_name = user_name  # Use the canonical name from config
                    break

        if found_user:
            # Prefer email for JIRA, username for GitHub
            if prefer_email:
                resolved_username = found_user.get("email") or found_user.get("username")
            else:
                resolved_username = found_user.get("username") or found_user.get("email")

            if not resolved_username:
                parser.error(f"User '{resolved_name}' has no username/email in config")
        else:
            parser.error(f"User '{resolved_name}' not found in config.json")

    # Ensure resolved_username is not None before returning
    if resolved_username is None:
        parser.error(
            "Could not resolve username. Provide --username or ensure name exists in config.json"
        )

    elif resolved_username and not resolved_name and config_data:
        # Lookup name from username/email
        for user in config_data.get("users", []):
            if user.get("username") == resolved_username or user.get("email") == resolved_username:
                resolved_name = user.get("name")
                # If we matched by username but email exists and prefer_email, use email
                if prefer_email and user.get("email") and user.get("username") == resolved_username:
                    resolved_username = user.get("email")
                break

    if resolved_username is None:
        parser.error(
            "Could not resolve username. Provide --username or ensure name exists in config.json"
        )

    # Type narrowing: resolved_username is guaranteed to be str here
    assert resolved_username is not None
    return resolved_name, resolved_username


def resolve_time_range(
    period: str | None,
    start_date: str | None,
    end_date: str | None,
    config_data: dict[str, Any] | None,  # pylint: disable=unused-argument
    parser: argparse.ArgumentParser,
) -> tuple[str, str, str]:
    """
    Resolve period key and dates from arguments.

    Returns:
        Tuple of (period_key, start_date, end_date)
    """
    period_key = period
    resolved_start = start_date
    resolved_end = end_date

    if period_key and not (resolved_start and resolved_end):
        # Parse period string directly (e.g., 2025H2, 2026Q1, 2025)
        try:
            resolved_start, resolved_end = parse_period(period_key)
        except ValueError as e:
            parser.error(str(e))

    elif (resolved_start and resolved_end) and not period_key:
        # Derive period key from dates
        start_dt = datetime.strptime(resolved_start, "%Y-%m-%d")
        end_dt = datetime.strptime(resolved_end, "%Y-%m-%d")

        # Match common period patterns using dictionary lookup
        period_patterns = {
            (1, 1, 12, 31): lambda y: str(y),  # Full year
            (7, 1, 12, 31): lambda y: f"{y}H2",  # Second half
            (1, 1, 6, 30): lambda y: f"{y}H1",  # First half
            (1, 1, 3, 31): lambda y: f"{y}Q1",  # Q1
            (4, 1, 6, 30): lambda y: f"{y}Q2",  # Q2
            (7, 1, 9, 30): lambda y: f"{y}Q3",  # Q3
            (10, 1, 12, 31): lambda y: f"{y}Q4",  # Q4
        }

        pattern_key = (start_dt.month, start_dt.day, end_dt.month, end_dt.day)
        if pattern_key in period_patterns:
            period_key = period_patterns[pattern_key](start_dt.year)
        else:
            period_key = f"{resolved_start}_to_{resolved_end}"

    if resolved_start is None or resolved_end is None:
        parser.error("Could not resolve date range. Provide --period or both --start and --end")

    # Ensure all values are strings (not None) before returning
    if period_key is None:
        parser.error("Could not resolve period key")

    # Type narrowing: all values are guaranteed to be str here
    assert period_key is not None
    assert resolved_start is not None
    assert resolved_end is not None
    return period_key, resolved_start, resolved_end


def determine_output_dir(
    output_arg: str | None, name: str | None, username: str, period_key: str
) -> str:
    """Determine the final output directory path."""
    if output_arg:
        return output_arg

    # Use slugified name if available, otherwise slugify username
    slugified_name = slugify(name) if name else slugify(username)

    return f"reports/{slugified_name}/{period_key}"
