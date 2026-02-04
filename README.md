# GitHub PR Review Analysis

A comprehensive CLI tool for analyzing GitHub PR review contributions using LangGraph workflows and Google Cloud Vertex AI.

## Quick Start

### Setup

```bash
# Install dependencies and verify configuration
just setup

# Authenticate with Google Cloud (if not already done)
just auth
```

### Run Analysis

```bash
# Using slugified name (RECOMMENDED - no quotes needed!)
just gh-analyze -n varun-sundar -p 2025H2

# Alternative: Using full name (requires quotes for spaces)
just gh-analyze -n "Varun Sundar" -p 2025H2

# Using username
just gh-analyze -u varunsundar -p 2025H2

# Using custom dates
just gh-analyze -n varun-sundar -s 2025-07-01 -e 2025-12-31
```

**Important**: Use slugified names (e.g., `varun-sundar`) instead of full names. This avoids quote issues and is the recommended approach.

## Features

- **Comprehensive Analysis**: Analyzes PR reviews, comments, and authored PRs
- **AI-Powered Insights**: Uses Vertex AI (gemini-2.5-pro) for intelligent analysis
- **Standardized Reports**: Generates consistent markdown reports with metrics
- **Flexible Input**: Supports slugified names (recommended), full names, usernames, periods, or custom dates
- **Centralized Config**: Manage multiple users and periods in a single `config.json`

## Usage

### Command-Line Interface

```bash
gh-analyze -n <name> -p <period> [options]
gh-analyze -u <username> -s <start-date> -e <end-date> [options]
gh-analyze -n <name> -s <start-date> -e <end-date> [options]
gh-analyze -u <username> -p <period> [options]
```

### Arguments

- `-n, --name NAME` - Person's name in slugified format (e.g., `varun-sundar`). Full names with spaces (e.g., `"Varun Sundar"`) are also supported but require quotes.
- `-u, --username USERNAME` - GitHub username
- `-p, --period PERIOD` - Period string: `YYYYH1`, `YYYYH2`, `YYYYQ1-Q4`, or `YYYY` (e.g., `2025H2`, `2026Q1`, `2025`)
- `-s, --start DATE` - Start date (YYYY-MM-DD)
- `-e, --end DATE` - End date (YYYY-MM-DD)

### Options

- `--org ORG` - Organization name (default: `EvolutionIQ`)
- `-o, --output DIR` - Output directory (default: `reports/<slugified-name>/<period>`)
- `--github-token TOKEN` - GitHub API token (or set `GITHUB_TOKEN` env var)
- `--project PROJECT` - Google Cloud project (or set `GOOGLE_CLOUD_PROJECT` env var)
- `--location LOCATION` - Vertex AI location (default: `us-east4`)

### Examples

```bash
# Using slugified name and period (RECOMMENDED)
gh-analyze -n varun-sundar -p 2025H2          # Second half of 2025
gh-analyze -n ariel-ledesma -p 2025H1        # First half of 2025
gh-analyze -n erin-friesen -p 2026Q1         # First quarter of 2026
gh-analyze -n varun-sundar -p 2025           # Full year 2025

# Alternative: Using full name (requires quotes)
gh-analyze -n "Varun Sundar" -p 2025H2

# Using username and dates
gh-analyze -u varunsundar -s 2025-07-01 -e 2025-12-31

# Custom output directory
gh-analyze -n varun-sundar -p 2025H2 -o custom/path

# Different organization
gh-analyze -n varun-sundar -p 2025H2 --org MyOrg
```

## Configuration

### Centralized Config (`config.json`)

The tool supports a centralized configuration file at the repository root:

```json
{
  "organization": "EvolutionIQ",
  "users": [
    {
      "username": "varunsundar",
      "name": "Varun Sundar"
    }
  ]
}
```

**Period Format**: Periods are parsed directly from the `-p` flag. Supported formats:
- `YYYYH1` - First half (Jan 1 - Jun 30)
- `YYYYH2` - Second half (Jul 1 - Dec 31)
- `YYYYQ1` - First quarter (Jan 1 - Mar 31)
- `YYYYQ2` - Second quarter (Apr 1 - Jun 30)
- `YYYYQ3` - Third quarter (Jul 1 - Sep 30)
- `YYYYQ4` - Fourth quarter (Oct 1 - Dec 31)
- `YYYY` - Full year (Jan 1 - Dec 31)

When using centralized config, you can reference users by slugified name (recommended) or full name.

### Individual Config Files

If a user is not in the centralized config, an individual `config.json` is created in the output directory.

## Output

The tool generates analysis reports in `reports/<slugified-name>/<period>/`:

- `github-review-analysis.md` - Comprehensive analysis report
- `config.json` - User configuration (if using individual configs)

### Report Contents

- Executive summary
- Comment classification (Architecture/Logic/Nits)
- PR description quality scores
- Cross-boundary contributions analysis
- Conflict management insights
- Significant changes summary
- Recommendations

## Development

### Setup

```bash
# Install dependencies including dev tools
just setup

# Run tests
just test

# Format code
just format
```

### Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=pr-review-analysis --cov-report=html

# Run specific test
uv run pytest tests/test_analyze_helpers.py
```

### Code Quality

```bash
# Lint code
uv run ruff check .

# Format code
uv run ruff format .

# Type checking
uv run mypy pr-review-analysis
```

## Architecture

The tool uses a LangGraph workflow for orchestration:

```
load_config → fetch_github → analyze → generate → save → END
```

- **load_config**: Loads user and period configuration
- **fetch_github**: Queries GitHub API for PRs and reviews
- **analyze**: Uses Vertex AI to analyze review data
- **generate**: Generates markdown report from analysis
- **save**: Saves report to file system

See `pr-review-analysis/workflows/analyze.py` for implementation details.

## Troubleshooting

### "GitHub token required"
```bash
export GITHUB_TOKEN=your_token_here
# Or add to .env file
```

### "Google Cloud project required"
```bash
export GOOGLE_CLOUD_PROJECT=your-project-id
# Or add to .env file
```

### "ModuleNotFoundError"
```bash
uv sync --extra dev
```

### Authentication Issues
```bash
just auth  # Run Google Cloud authentication
```

## Project Structure

```
.
├── gh-analyze              # Main CLI entry point
├── config.json             # Centralized configuration
├── justfile                # Convenience commands
├── pyproject.toml          # Python dependencies
├── pr-review-analysis/     # Core package
│   ├── workflows/
│   │   └── analyze.py      # LangGraph workflow
│   └── templates/
│       └── gh-analysis.jinja2.md
└── tests/                  # Test suite
```

## License

Internal tool for EvolutionIQ.
