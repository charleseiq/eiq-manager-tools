# GitHub PR Review Analysis - Detailed Documentation

> **Note**: This is detailed documentation. For quick start, see [README.md](README.md).

## Overview

The GitHub PR Review Analysis tool provides comprehensive analysis of PR review contributions using LangGraph workflows and Google Cloud Vertex AI. It supports flexible input methods including slugified names, full names, usernames, periods, and custom date ranges.

## Prerequisites

1. **GitHub Token**: Set `GITHUB_TOKEN` environment variable or use `--github-token`
2. **Google Cloud Project**: Set `GOOGLE_CLOUD_PROJECT` environment variable or use `--project`
3. **Dependencies**: Run `just setup` or `uv sync --extra dev`
4. **Authentication**: Run `just auth` for Google Cloud authentication

## Usage

### Basic Syntax

```bash
gh-analyze -n <name> -p <period> [options]
gh-analyze -u <username> -s <start-date> -e <end-date> [options]
gh-analyze -n <name> -s <start-date> -e <end-date> [options]
gh-analyze -u <username> -p <period> [options]
```

### Arguments

- `-n, --name NAME` - Person's name (supports slugified: `varun-sundar` or full: `"Varun Sundar"`)
- `-u, --username USERNAME` - GitHub username
- `-p, --period PERIOD` - Period key from config (e.g., `2025H2`)
- `-s, --start DATE` - Start date in YYYY-MM-DD format
- `-e, --end DATE` - End date in YYYY-MM-DD format

### Options

- `--org ORG` - Organization name (default: `EvolutionIQ`)
- `-o, --output DIR` - Output directory (default: `reports/<slugified-name>/<period>`)
- `--github-token TOKEN` - GitHub API token (or set `GITHUB_TOKEN` env var)
- `--project PROJECT` - Google Cloud project (or set `GOOGLE_CLOUD_PROJECT` env var)
- `--location LOCATION` - Vertex AI location (default: `us-east4`)

### Examples

```bash
# Using slugified name with period (recommended - no quotes needed!)
gh-analyze -n varun-sundar -p 2025H2

# Using full name with period
gh-analyze -n "Varun Sundar" -p 2025H2

# Using username with period
gh-analyze -u varunsundar -p 2025H2

# Using name with custom dates
gh-analyze -n varun-sundar -s 2025-07-01 -e 2025-12-31

# Custom output directory
gh-analyze -n varun-sundar -p 2025H2 -o custom/path

# Different organization
gh-analyze -n varun-sundar -p 2025H2 --org MyOrg
```

## What It Does

1. **Creates Config**: Automatically creates `config.json` in the output directory
2. **Fetches Data**: Queries GitHub API for PRs reviewed by the user in the date range
3. **Analyzes**: Uses Vertex AI (gemini-2.5-pro) to analyze reviews and generate insights
4. **Generates Report**: Creates `github-review-analysis.md` with standardized format

## Output

The tool generates:
- `reports/<username>/<period>/config.json` - User configuration
- `reports/<username>/<period>/github-review-analysis.md` - Analysis report

The report includes:
- Executive summary
- Comment classification (Architecture/Logic/Nits)
- PR description quality scores
- Cross-boundary contributions
- Conflict management analysis
- Recommendations

## Using Justfile

```bash
# Using slugified name (recommended)
just gh-analyze -n varun-sundar -p 2025H2

# Using full name
just gh-analyze -n "Varun Sundar" -p 2025H2

# Using username
just gh-analyze -u varunsundar -p 2025H2

# Custom dates
just gh-analyze -n varun-sundar -s 2025-07-01 -e 2025-12-31
```

## Architecture

The CLI uses a LangGraph workflow located at:
`pr-review-analysis/workflows/analyze.py`

The workflow:
- Loads config
- Fetches GitHub data
- Analyzes with Vertex AI
- Generates markdown report

## Configuration

### Centralized Configuration

The tool supports a centralized `config.json` at the repository root:

```json
{
  "organization": "EvolutionIQ",
  "periods": {
    "2025H2": {
      "start_date": "2025-07-01",
      "end_date": "2025-12-31"
    },
    "2025H1": {
      "start_date": "2025-01-01",
      "end_date": "2025-06-30"
    }
  },
  "users": [
    {
      "username": "varunsundar",
      "name": "Varun Sundar"
    }
  ]
}
```

When using centralized config, you can reference users by name (slugified or full) and periods by key.

### Individual Configuration

If a user is not in the centralized config, an individual `config.json` is created in the output directory.

## Troubleshooting

### "GitHub token required"
```bash
export GITHUB_TOKEN=your_token_here
```

### "Google Cloud project required"
```bash
export GOOGLE_CLOUD_PROJECT=your-project-id
```

### "ModuleNotFoundError"
```bash
uv sync
```

## Development

See [README.md](README.md) for development setup, testing, and code quality tools.
