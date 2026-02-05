"""Tests for shared CLI utilities."""

import argparse
import json
from pathlib import Path

import pytest

from shared.cli_utils import (
    determine_output_dir,
    parse_period,
    resolve_time_range,
    resolve_user_identity,
    slugify,
    unslugify,
)


class TestSlugify:
    """Tests for slugify function."""

    def test_basic_slugify(self):
        """Test basic slugification."""
        assert slugify("Varun Sundar") == "varun-sundar"
        assert slugify("Ariel Ledesma") == "ariel-ledesma"

    def test_already_slugified(self):
        """Test already slugified text."""
        assert slugify("varun-sundar") == "varun-sundar"

    def test_with_underscores(self):
        """Test text with underscores."""
        assert slugify("varun_sundar") == "varun-sundar"

    def test_with_special_characters(self):
        """Test text with special characters."""
        assert slugify("Varun Sundar!@#") == "varun-sundar"
        assert slugify("Ariel Ledesma (Senior)") == "ariel-ledesma-senior"

    def test_multiple_spaces(self):
        """Test text with multiple spaces."""
        assert slugify("Varun    Sundar") == "varun-sundar"

    def test_empty_string(self):
        """Test empty string."""
        assert slugify("") == ""

    def test_leading_trailing_hyphens(self):
        """Test text with leading/trailing hyphens."""
        assert slugify("-varun-sundar-") == "varun-sundar"


class TestUnslugify:
    """Tests for unslugify function."""

    def test_basic_unslugify(self):
        """Test basic unslugification."""
        assert unslugify("varun-sundar") == "Varun Sundar"
        assert unslugify("ariel-ledesma") == "Ariel Ledesma"

    def test_single_word(self):
        """Test single word slug."""
        assert unslugify("varun") == "Varun"

    def test_multiple_words(self):
        """Test multiple words."""
        assert unslugify("varun-sundar-senior") == "Varun Sundar Senior"

    def test_empty_string(self):
        """Test empty string."""
        assert unslugify("") == ""

    def test_already_title_case(self):
        """Test that it still works with already title case."""
        assert unslugify("Varun-Sundar") == "Varun Sundar"


class TestParsePeriod:
    """Tests for parse_period function."""

    def test_h1_period(self):
        """Test H1 period parsing."""
        start, end = parse_period("2025H1")
        assert start == "2025-01-01"
        assert end == "2025-06-30"

    def test_h2_period(self):
        """Test H2 period parsing."""
        start, end = parse_period("2025H2")
        assert start == "2025-07-01"
        assert end == "2025-12-31"

    def test_q1_period(self):
        """Test Q1 period parsing."""
        start, end = parse_period("2025Q1")
        assert start == "2025-01-01"
        assert end == "2025-03-31"

    def test_q2_period(self):
        """Test Q2 period parsing."""
        start, end = parse_period("2025Q2")
        assert start == "2025-04-01"
        assert end == "2025-06-30"

    def test_q3_period(self):
        """Test Q3 period parsing."""
        start, end = parse_period("2025Q3")
        assert start == "2025-07-01"
        assert end == "2025-09-30"

    def test_q4_period(self):
        """Test Q4 period parsing."""
        start, end = parse_period("2025Q4")
        assert start == "2025-10-01"
        assert end == "2025-12-31"

    def test_full_year(self):
        """Test full year parsing."""
        start, end = parse_period("2025")
        assert start == "2025-01-01"
        assert end == "2025-12-31"

    def test_case_insensitive(self):
        """Test that parsing is case insensitive."""
        start, end = parse_period("2025h2")
        assert start == "2025-07-01"
        assert end == "2025-12-31"

    def test_with_whitespace(self):
        """Test that whitespace is stripped."""
        start, end = parse_period(" 2025H2 ")
        assert start == "2025-07-01"
        assert end == "2025-12-31"

    def test_invalid_format(self):
        """Test invalid period format."""
        with pytest.raises(ValueError, match="Invalid period format"):
            parse_period("invalid")

    def test_invalid_year(self):
        """Test invalid year format."""
        with pytest.raises(ValueError):
            parse_period("25H2")


class TestResolveUserIdentity:
    """Tests for resolve_user_identity function."""

    def test_with_name_in_config(self, temp_config_file):
        """Test resolving user identity from name in config."""
        config_path = Path(temp_config_file)
        with open(config_path) as f:
            config_data = json.load(f)

        parser = argparse.ArgumentParser()
        name, username = resolve_user_identity(
            "Test User", None, config_data, parser, prefer_email=False
        )
        assert name == "Test User"
        assert username == "testuser"

    def test_with_slugified_name(self, temp_config_file):
        """Test resolving user identity from slugified name."""
        config_path = Path(temp_config_file)
        with open(config_path) as f:
            config_data = json.load(f)

        parser = argparse.ArgumentParser()
        name, username = resolve_user_identity(
            "test-user", None, config_data, parser, prefer_email=False
        )
        assert name == "Test User"
        assert username == "testuser"

    def test_with_username(self, temp_config_file):
        """Test resolving user identity from username."""
        config_path = Path(temp_config_file)
        with open(config_path) as f:
            config_data = json.load(f)

        parser = argparse.ArgumentParser()
        name, username = resolve_user_identity(
            None, "testuser", config_data, parser, prefer_email=False
        )
        assert name == "Test User"
        assert username == "testuser"

    def test_prefer_email(self):
        """Test preferring email when prefer_email=True."""
        config_data = {
            "users": [{"name": "Test User", "username": "testuser", "email": "test@example.com"}]
        }

        parser = argparse.ArgumentParser()
        name, username = resolve_user_identity(
            "Test User", None, config_data, parser, prefer_email=True
        )
        assert name == "Test User"
        assert username == "test@example.com"

    def test_no_config_with_name(self):
        """Test error when name provided but no config."""
        parser = argparse.ArgumentParser()
        with pytest.raises(SystemExit):
            resolve_user_identity("Test User", None, None, parser, prefer_email=False)

    def test_user_not_found(self, temp_config_file):
        """Test error when user not found in config."""
        config_path = Path(temp_config_file)
        with open(config_path) as f:
            config_data = json.load(f)

        parser = argparse.ArgumentParser()
        with pytest.raises(SystemExit):
            resolve_user_identity("Nonexistent User", None, config_data, parser, prefer_email=False)

    def test_no_username_resolved(self):
        """Test error when no username can be resolved."""
        config_data = {"users": [{"name": "Test User"}]}

        parser = argparse.ArgumentParser()
        with pytest.raises(SystemExit):
            resolve_user_identity("Test User", None, config_data, parser, prefer_email=False)


class TestResolveTimeRange:
    """Tests for resolve_time_range function."""

    def test_with_period(self):
        """Test resolving time range from period."""
        parser = argparse.ArgumentParser()
        period_key, start, end = resolve_time_range("2025H2", None, None, None, parser)
        assert period_key == "2025H2"
        assert start == "2025-07-01"
        assert end == "2025-12-31"

    def test_with_dates(self):
        """Test resolving time range from dates."""
        parser = argparse.ArgumentParser()
        period_key, start, end = resolve_time_range(None, "2025-07-01", "2025-12-31", None, parser)
        assert period_key == "2025H2"
        assert start == "2025-07-01"
        assert end == "2025-12-31"

    def test_with_custom_dates(self):
        """Test resolving time range from custom dates."""
        parser = argparse.ArgumentParser()
        period_key, start, end = resolve_time_range(None, "2025-03-15", "2025-09-20", None, parser)
        assert period_key == "2025-03-15_to_2025-09-20"
        assert start == "2025-03-15"
        assert end == "2025-09-20"

    def test_invalid_period(self):
        """Test error with invalid period."""
        parser = argparse.ArgumentParser()
        with pytest.raises(SystemExit):
            resolve_time_range("invalid", None, None, None, parser)

    def test_no_period_or_dates(self):
        """Test error when neither period nor dates provided."""
        parser = argparse.ArgumentParser()
        with pytest.raises(SystemExit):
            resolve_time_range(None, None, None, None, parser)


class TestDetermineOutputDir:
    """Tests for determine_output_dir function."""

    def test_with_output_arg(self):
        """Test with explicit output argument."""
        result = determine_output_dir("/custom/output", "Test User", "testuser", "2025H2")
        assert result == "/custom/output"

    def test_with_name(self):
        """Test with name provided."""
        result = determine_output_dir(None, "Test User", "testuser", "2025H2")
        assert result == "reports/test-user/2025H2"

    def test_with_username_only(self):
        """Test with username only."""
        result = determine_output_dir(None, None, "testuser", "2025H2")
        assert result == "reports/testuser/2025H2"

    def test_slugified_name(self):
        """Test that name is slugified."""
        result = determine_output_dir(None, "Varun Sundar", "varunsundar", "2025H2")
        assert result == "reports/varun-sundar/2025H2"
