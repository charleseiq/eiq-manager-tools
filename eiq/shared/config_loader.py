"""Shared utilities for loading configuration and finding users."""

import json
from pathlib import Path

from eiq.shared.cli_utils import slugify


def load_config(config_path: Path | str | None = None) -> dict:
    """
    Load centralized config.json file.

    Args:
        config_path: Path to config.json (defaults to "config.json" in repo root)

    Returns:
        Config dictionary

    Raises:
        FileNotFoundError: If config.json not found
    """
    if config_path is None:
        config_path = Path("config.json")
    elif isinstance(config_path, str):
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path) as f:
        return json.load(f)


def find_user_by_slug(config: dict, user_slug: str) -> dict | None:
    """
    Find a user in config by slugified name or username.

    Args:
        config: Config dictionary
        user_slug: Slugified user identifier

    Returns:
        User dictionary if found, None otherwise
    """
    for user in config.get("users", []):
        name_slug = slugify(user.get("name", user.get("username", "")))
        username_slug = slugify(user.get("username", ""))
        if name_slug == user_slug or username_slug == user_slug:
            return user
    return None


def find_user_by_identifier(config: dict, identifier: str) -> dict | None:
    """
    Find a user in config by any identifier (name, username, email).

    Args:
        config: Config dictionary
        identifier: User identifier (name, username, or email)

    Returns:
        User dictionary if found, None otherwise
    """
    identifier_lower = identifier.lower()
    for user in config.get("users", []):
        if (
            user.get("username", "").lower() == identifier_lower
            or user.get("email", "").lower() == identifier_lower
            or user.get("name", "").lower() == identifier_lower
            or slugify(user.get("name", "")) == identifier_lower
        ):
            return user
    return None


def get_all_users(config: dict) -> list[dict]:
    """
    Get all users from config.

    Args:
        config: Config dictionary

    Returns:
        List of user dictionaries
    """
    return config.get("users", [])
