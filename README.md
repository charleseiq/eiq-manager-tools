# Engineering Performance Analysis Tools

A comprehensive suite of CLI tools for analyzing engineering performance across GitHub PR reviews, JIRA sprint/epic tracking, and Google Docs technical design documents. Built with LangGraph workflows and Google Cloud Vertex AI.

## Overview

This repository provides three complementary analysis tools:

1. **[GitHub PR Review Analysis](eiq/gh-analysis/README.md)** (`gh-analyze`) - Analyzes code review quality, comment classification, and cross-boundary contributions
2. **[JIRA Sprint & Epic Analysis](eiq/jira-analysis/README.md)** (`jira-analyze`) - Tracks sprint performance, velocity, epic allocation, and worklog patterns
3. **[Google Docs Analysis](eiq/gdocs-analysis/README.md)** (`gdocs-analyze`) - Evaluates technical design document quality, comment responses, and team engagement

Together, these tools provide a comprehensive view of engineering performance across code review, planning, and documentation.

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- Google Cloud project with Vertex AI enabled
- API credentials (GitHub token, JIRA token)
- Google Cloud Application Default Credentials (set up via `just auth`)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd management

# Install dependencies
uv sync --extra dev

# Set up environment variables (copy from .env.example)
cp .env.example .env
# Edit .env with your credentials

# Set up authentication (one-time setup)
just auth
```

### Environment Variables

Create a `.env` file with:

```bash
# GitHub (for gh-analyze)
GITHUB_TOKEN=your_github_token_here

# JIRA (for jira-analyze)
JIRA_TOKEN=your_jira_api_token_here
JIRA_URL=https://yourcompany.atlassian.net
JIRA_PROJECT=WC

# EvolutionIQ Email (shared across JIRA and Google Docs)
# Use the same email for both JIRA and Google account authentication
EVOLUTIONIQ_EMAIL=your_email@evolutioniq.com

# Google Cloud (for all tools)
GOOGLE_CLOUD_PROJECT=eiq-development
GOOGLE_CLOUD_LOCATION=us-east4
```

### Configuration

Create a centralized `config.json` at the repository root:

```json
{
  "organization": "EvolutionIQ",
  "users": [
    {
      "username": "varunsundar",
      "email": "varun.sundar@evolutioniq.com",
      "name": "Varun Sundar",
      "account_id": "712020:9b24a504-5186-4db2-a263-2f66398ba887"
    }
  ]
}
```

**Note:** 
- The `email` field is used for both JIRA and Google Drive authentication. Use the same email for both.
- `drive_folder_ids` and `document_types` are optional (deprecated). By default, Google Docs analysis searches all documents owned by the user.

## Tools

### GitHub PR Review Analysis

Analyzes PR review contributions, comment quality, and cross-boundary work.

```bash
# Using slugified name (recommended)
scripts/gh-analyze -n varun-sundar -p 2025H2

# Or using just
just gh-analyze -n varun-sundar -p 2025H2
```

**Features:**
- Comment classification (Architecture/Logic/Nits)
- PR description quality scoring
- Cross-boundary contribution analysis
- Conflict management insights

📖 **[Full Documentation →](eiq/gh-analysis/README.md)**

### JIRA Sprint & Epic Analysis

Tracks sprint performance, velocity trends, and epic allocation for time tracking and reporting.

```bash
# Using slugified name (recommended)
scripts/jira-analyze -n varun-sundar -p 2025H2

# Or using just
just jira-analyze -n varun-sundar -p 2025H2
```

**Features:**
- Sprint loading and completion analysis
- Velocity trends and consistency
- Epic allocation for time sheets/capex reporting
- Worklog pattern analysis

📖 **[Full Documentation →](eiq/jira-analysis/README.md)**

### Google Docs Analysis

Evaluates technical design documents, comment responses, and team engagement.

```bash
# Using slugified name (recommended)
scripts/gdocs-analyze -n varun-sundar -p 2025H2

# Or using just
just gdocs-analyze -n varun-sundar -p 2025H2
```

**Features:**
- Document quality evaluation (problem clarity, concept clarity, execution path)
- Owner filtering (only analyzes documents owned by the user)
- Automatic document discovery (searches all Google Docs owned by user)
- Comment response analysis
- Team engagement metrics
- Artifact storage (markdown conversions)

**Note:** Run `just auth` first to set up Google Drive authentication using Secret Manager.

📖 **[Full Documentation →](eiq/gdocs-analysis/README.md)**

## Common Usage Patterns

### Period Formats

All tools support the same period formats:

- `YYYYH1` - First half (Jan 1 - Jun 30)
- `YYYYH2` - Second half (Jul 1 - Dec 31)
- `YYYYQ1` - First quarter (Jan 1 - Mar 31)
- `YYYYQ2` - Second quarter (Apr 1 - Jun 30)
- `YYYYQ3` - Third quarter (Jul 1 - Sep 30)
- `YYYYQ4` - Fourth quarter (Oct 1 - Dec 31)
- `YYYY` - Full year (Jan 1 - Dec 31)

### User Identification

All tools support multiple ways to identify users:

```bash
# Slugified name (RECOMMENDED - no quotes needed)
-n varun-sundar

# Full name (requires quotes)
-n "Varun Sundar"

# Username/email
-u varunsundar
-u varun.sundar@evolutioniq.com
```

### Output Structure

All tools generate reports in a consistent structure:

```
reports/
└── <slugified-name>/
    └── <period>/
        ├── <tool>-analysis.md    # Main analysis report
        ├── config.json            # User config (if individual)
        └── artifacts/             # Additional artifacts (gdocs only)
            └── *.md
```

## Development

### Setup

```bash
# Install dependencies including dev tools
uv sync --extra dev

# Install pre-commit hooks
uv run pre-commit install

# Set up authentication (one-time setup)
just auth
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=eiq.gh-analysis --cov-report=html

# Run specific test
uv run pytest tests/test_analyze_helpers.py
```

### Code Quality

```bash
# Lint code
uv run ruff check .

# Auto-fix linting issues
uv run ruff check --fix .

# Format code
uv run ruff format .

# Type checking
uv run ty check .
```

### Pre-commit Hooks

The project uses pre-commit hooks to automatically run linting, type checking, and tests:

```bash
# Run pre-commit hooks manually
pre-commit run --all-files
```

## Project Structure

```
.
├── scripts/                # CLI entry points
│   ├── gh-analyze          # GitHub PR analysis CLI
│   ├── jira-analyze        # JIRA sprint/epic analysis CLI
│   └── gdocs-analyze       # Google Docs analysis CLI
├── config.json             # Centralized configuration
├── justfile                # Convenience commands
├── pyproject.toml          # Python dependencies
├── eiq/                    # Analysis modules
│   ├── shared/             # Shared CLI utilities
│   │   ├── cli_utils.py    # Common functions (slugify, period parsing, etc.)
│   │   └── config_utils.py # Configuration file handling
│   ├── gh-analysis/        # GitHub PR analysis package
│   │   ├── workflows/      # LangGraph workflows
│   │   ├── templates/      # Report templates
│   │   └── README.md       # Detailed documentation
│   ├── jira-analysis/      # JIRA analysis package
│   │   ├── workflows/      # LangGraph workflows
│   │   ├── templates/      # Report templates
│   │   └── README.md       # Detailed documentation
│   └── gdocs-analysis/     # Google Docs analysis package
│       ├── workflows/      # LangGraph workflows
│       ├── templates/      # Report templates
│       └── README.md       # Detailed documentation
└── tests/                  # Test suite
```

## Architecture

All tools follow a consistent LangGraph workflow pattern:

```
load_config → fetch_data → analyze → generate → save → END
```

- **load_config**: Loads user and period configuration from centralized or individual config
- **fetch_data**: Queries APIs (GitHub/JIRA/Google Drive) for relevant data
- **analyze**: Uses Vertex AI (gemini-2.5-pro) to generate intelligent analysis
- **generate**: Formats analysis into markdown report using Jinja2 templates
- **save**: Writes report to file system

See individual module READMEs for workflow-specific details.

## Troubleshooting

### Common Issues

**"Token required" errors:**
- Ensure `.env` file exists and contains required tokens
- Check that environment variables are set correctly

**"Google Cloud project required":**
```bash
export GOOGLE_CLOUD_PROJECT=eiq-development
```

**"ModuleNotFoundError":**
```bash
uv sync --extra dev
```

**Authentication Issues:**
- GitHub: Verify token has correct scopes
- JIRA: Check API token and EVOLUTIONIQ_EMAIL match
- Google Drive: Run `just auth` to set up authentication using Secret Manager (see [gdocs-analysis README](eiq/gdocs-analysis/README.md))

### Getting Help

- Check individual tool READMEs for tool-specific issues
- Review `.env.example` for required environment variables
- Check `config.json` structure matches expected format

## License

Internal tool for EvolutionIQ.
