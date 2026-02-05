"""
Shared utilities for CLI tools.

This package provides common functionality used by both gh-analyze and jira-analyze:
- CLI utilities (slugify, period parsing, user resolution)
- Configuration utilities (config loading, creation)
"""

from shared.cli_utils import (
    determine_output_dir,
    parse_period,
    resolve_time_range,
    resolve_user_identity,
    slugify,
    unslugify,
)
from shared.config_utils import (
    create_github_config,
    create_jira_config,
    format_analysis_period,
    load_centralized_config,
    user_exists_in_config,
)

__all__ = [
    # CLI utilities
    "determine_output_dir",
    "parse_period",
    "resolve_time_range",
    "resolve_user_identity",
    "slugify",
    "unslugify",
    # Config utilities
    "create_github_config",
    "create_jira_config",
    "format_analysis_period",
    "load_centralized_config",
    "user_exists_in_config",
]
