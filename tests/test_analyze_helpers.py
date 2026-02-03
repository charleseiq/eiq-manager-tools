"""Tests for helper functions in analyze.py."""

from datetime import datetime, timezone

import pytest

import importlib.util
from pathlib import Path

# Import analyze module directly from file path (handles hyphenated directory name)
analyze_path = Path(__file__).parent.parent / "pr-review-analysis" / "workflows" / "analyze.py"
spec = importlib.util.spec_from_file_location("analyze", analyze_path)
analyze = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analyze)

# Extract functions for easier testing
_extract_pr_info = analyze._extract_pr_info
_filter_reviews_by_user_and_date = analyze._filter_reviews_by_user_and_date
_format_analysis_period = analyze._format_analysis_period
_parse_github_date = analyze._parse_github_date


class TestFormatAnalysisPeriod:
    """Tests for _format_analysis_period function."""

    def test_h2_period(self):
        """Test H2 period formatting."""
        result = _format_analysis_period("2025-07-01", "2025-12-31")
        assert result == "2025H2 (July 1 - December 31, 2025)"

    def test_h1_period(self):
        """Test H1 period formatting."""
        result = _format_analysis_period("2025-01-01", "2025-06-30")
        assert result == "2025H1 (January 1 - June 30, 2025)"

    def test_custom_period(self):
        """Test custom date range formatting."""
        result = _format_analysis_period("2025-03-15", "2025-09-20")
        assert result == "2025-03-15 to 2025-09-20"

    def test_different_years(self):
        """Test period spanning different years."""
        result = _format_analysis_period("2024-12-01", "2025-02-28")
        assert result == "2024-12-01 to 2025-02-28"


class TestParseGithubDate:
    """Tests for _parse_github_date function."""

    def test_parse_with_z(self):
        """Test parsing date with Z timezone."""
        date_str = "2025-07-15T10:30:00Z"
        result = _parse_github_date(date_str)
        expected = datetime(2025, 7, 15, 10, 30, 0, tzinfo=timezone.utc)
        assert result == expected

    def test_parse_with_timezone(self):
        """Test parsing date with explicit timezone."""
        date_str = "2025-07-15T10:30:00+00:00"
        result = _parse_github_date(date_str)
        expected = datetime(2025, 7, 15, 10, 30, 0, tzinfo=timezone.utc)
        assert result == expected


class TestExtractPrInfo:
    """Tests for _extract_pr_info function."""

    def test_valid_pr_url(self):
        """Test extracting info from valid PR URL."""
        pr_item = {
            "html_url": "https://github.com/EvolutionIQ/repo-name/pull/123"
        }
        result = _extract_pr_info(pr_item)
        assert result is not None
        assert result["number"] == 123
        assert result["repo"] == "repo-name"
        assert result["owner"] == "EvolutionIQ"
        assert result["html_url"] == "https://github.com/EvolutionIQ/repo-name/pull/123"

    def test_missing_html_url(self):
        """Test with missing html_url."""
        pr_item = {}
        result = _extract_pr_info(pr_item)
        assert result is None

    def test_invalid_url_format(self):
        """Test with invalid URL format."""
        pr_item = {"html_url": "https://github.com/invalid"}
        result = _extract_pr_info(pr_item)
        assert result is None

    def test_empty_html_url(self):
        """Test with empty html_url."""
        pr_item = {"html_url": ""}
        result = _extract_pr_info(pr_item)
        assert result is None


class TestFilterReviewsByUserAndDate:
    """Tests for _filter_reviews_by_user_and_date function."""

    def test_filter_reviews_in_range(self):
        """Test filtering reviews within date range."""
        username = "testuser"
        start_dt = datetime(2025, 7, 1, tzinfo=timezone.utc)
        end_dt = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

        reviews = [
            {
                "user": {"login": "testuser"},
                "body": "Good PR",
                "state": "APPROVED",
                "submitted_at": "2025-08-15T10:00:00Z",
            },
            {
                "user": {"login": "otheruser"},
                "body": "Another review",
                "state": "COMMENTED",
                "submitted_at": "2025-08-15T10:00:00Z",
            },
            {
                "user": {"login": "testuser"},
                "body": "Out of range",
                "state": "APPROVED",
                "submitted_at": "2026-01-15T10:00:00Z",
            },
        ]

        comments = []

        filtered_reviews, filtered_comments = _filter_reviews_by_user_and_date(
            reviews, comments, username, start_dt, end_dt
        )

        assert len(filtered_reviews) == 1
        assert filtered_reviews[0]["body"] == "Good PR"
        assert len(filtered_comments) == 0

    def test_filter_comments_in_range(self):
        """Test filtering comments within date range."""
        username = "testuser"
        start_dt = datetime(2025, 7, 1, tzinfo=timezone.utc)
        end_dt = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

        reviews = []

        comments = [
            {
                "user": {"login": "testuser"},
                "body": "Nice work",
                "created_at": "2025-09-15T10:00:00Z",
            },
            {
                "user": {"login": "otheruser"},
                "body": "Another comment",
                "created_at": "2025-09-15T10:00:00Z",
            },
            {
                "user": {"login": "testuser"},
                "body": "Out of range",
                "created_at": "2026-01-15T10:00:00Z",
            },
        ]

        filtered_reviews, filtered_comments = _filter_reviews_by_user_and_date(
            reviews, comments, username, start_dt, end_dt
        )

        assert len(filtered_reviews) == 0
        assert len(filtered_comments) == 1
        assert filtered_comments[0]["body"] == "Nice work"

    def test_filter_both_reviews_and_comments(self):
        """Test filtering both reviews and comments."""
        username = "testuser"
        start_dt = datetime(2025, 7, 1, tzinfo=timezone.utc)
        end_dt = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

        reviews = [
            {
                "user": {"login": "testuser"},
                "body": "Review comment",
                "state": "APPROVED",
                "submitted_at": "2025-08-15T10:00:00Z",
            }
        ]

        comments = [
            {
                "user": {"login": "testuser"},
                "body": "Inline comment",
                "created_at": "2025-08-16T10:00:00Z",
            }
        ]

        filtered_reviews, filtered_comments = _filter_reviews_by_user_and_date(
            reviews, comments, username, start_dt, end_dt
        )

        assert len(filtered_reviews) == 1
        assert len(filtered_comments) == 1

    def test_empty_inputs(self):
        """Test with empty inputs."""
        username = "testuser"
        start_dt = datetime(2025, 7, 1, tzinfo=timezone.utc)
        end_dt = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

        filtered_reviews, filtered_comments = _filter_reviews_by_user_and_date(
            [], [], username, start_dt, end_dt
        )

        assert len(filtered_reviews) == 0
        assert len(filtered_comments) == 0

    def test_boundary_dates(self):
        """Test filtering at boundary dates."""
        username = "testuser"
        start_dt = datetime(2025, 7, 1, tzinfo=timezone.utc)
        end_dt = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

        reviews = [
            {
                "user": {"login": "testuser"},
                "body": "Start boundary",
                "state": "APPROVED",
                "submitted_at": "2025-07-01T00:00:00Z",
            },
            {
                "user": {"login": "testuser"},
                "body": "End boundary",
                "state": "APPROVED",
                "submitted_at": "2025-12-31T23:59:59Z",
            },
            {
                "user": {"login": "testuser"},
                "body": "Before start",
                "state": "APPROVED",
                "submitted_at": "2025-06-30T23:59:59Z",
            },
            {
                "user": {"login": "testuser"},
                "body": "After end",
                "state": "APPROVED",
                "submitted_at": "2026-01-01T00:00:00Z",
            },
        ]

        comments = []

        filtered_reviews, filtered_comments = _filter_reviews_by_user_and_date(
            reviews, comments, username, start_dt, end_dt
        )

        assert len(filtered_reviews) == 2
        assert any(r["body"] == "Start boundary" for r in filtered_reviews)
        assert any(r["body"] == "End boundary" for r in filtered_reviews)
