# Testing Guide

This project uses pytest for testing, ruff for linting, and mypy for type checking.

## Setup

Install development dependencies:

```bash
uv sync --extra dev
```

Or install manually:

```bash
uv pip install pytest pytest-cov pytest-mock ruff mypy types-requests types-pyyaml
```

## Running Tests

Run all tests:

```bash
uv run pytest
```

Run with coverage:

```bash
uv run pytest --cov=pr-review-analysis --cov-report=html
```

Run specific test file:

```bash
uv run pytest tests/test_analyze_helpers.py
```

Run specific test:

```bash
uv run pytest tests/test_analyze_helpers.py::TestFormatAnalysisPeriod::test_h2_period
```

## Linting

Run ruff linting:

```bash
uv run ruff check .
```

Auto-fix linting issues:

```bash
uv run ruff check --fix .
```

Format code:

```bash
uv run ruff format .
```

## Type Checking

Run mypy:

```bash
uv run mypy pr-review-analysis
```

## Pre-commit Hooks

The project uses pre-commit hooks to automatically run linting, type checking, and tests before commits.

Install pre-commit hooks:

```bash
pre-commit install
```

Run pre-commit hooks manually:

```bash
pre-commit run --all-files
```

## Test Structure

- `tests/test_analyze_helpers.py` - Tests for helper functions (`_format_analysis_period`, `_parse_github_date`, `_extract_pr_info`, `_filter_reviews_by_user_and_date`)
- `tests/test_analyze_load_config.py` - Tests for `load_config` function
- `tests/conftest.py` - Pytest fixtures and configuration

## Writing New Tests

When adding new functions to `analyze.py`, add corresponding tests:

1. Create test functions in the appropriate test file
2. Use descriptive test names: `test_<function_name>_<scenario>`
3. Use fixtures from `conftest.py` when possible
4. Mock external dependencies (GitHub API, Vertex AI) using `pytest-mock`

Example:

```python
def test_new_function_success_case():
    """Test new_function with valid input."""
    result = new_function("valid_input")
    assert result == expected_output

def test_new_function_error_case():
    """Test new_function with invalid input."""
    with pytest.raises(ValueError):
        new_function("invalid_input")
```
