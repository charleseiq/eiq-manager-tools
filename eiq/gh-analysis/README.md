# GitHub PR Review Analysis

Comprehensive analysis tool for GitHub PR reviews using LangGraph workflows and Vertex AI.

## Quick Start

### Setup

```bash
just setup
```

This will:
- Install dependencies (`uv sync`)
- Check environment variables (GITHUB_TOKEN, GOOGLE_CLOUD_PROJECT)
- Verify template file exists
- Check for centralized config

### Run Analysis

```bash
# Using slugified name with period (RECOMMENDED - no quotes needed!)
just gh-analyze -n varun-sundar -p 2025H2          # Second half of 2025
just gh-analyze -n ariel-ledesma -p 2025H1         # First half of 2025
just gh-analyze -n erin-friesen -p 2026Q1          # First quarter of 2026
just gh-analyze -n varun-sundar -p 2025            # Full year 2025

# Alternative: Using full name (requires quotes for spaces)
just gh-analyze -n "Varun Sundar" -p 2025H2

# Using username
just gh-analyze -u varunsundar -p 2025H2
```

**Note**: 
- Use slugified names (e.g., `varun-sundar`) instead of full names. The tool automatically converts them to title case for matching.
- Periods are parsed directly: `YYYYH1`, `YYYYH2`, `YYYYQ1-Q4`, or `YYYY` (e.g., `2025H2`, `2026Q1`, `2025`).

See the main [README.md](../README.md) for full documentation.

## Structure

```
eiq/gh-analysis/
├── workflows/          # LangGraph workflow implementation
│   ├── analyze.py     # Main workflow logic
│   └── __init__.py    # Package initialization
├── templates/          # Report templates
│   └── gh-analysis.jinja2.md
└── README.md           # This file
```

## Usage

### Using the CLI

```bash
# Using slugified name with period (recommended)
gh-analyze -n varun-sundar -p 2025H2          # Second half of 2025
gh-analyze -n ariel-ledesma -p 2026Q1         # First quarter of 2026
gh-analyze -n varun-sundar -p 2025            # Full year 2025

# Using username with dates
gh-analyze -u varunsundar -s 2025-07-01 -e 2025-12-31
```

### Using Just

```bash
just gh-analyze -n varun-sundar -p 2025H2
```

The `gh-analyze` CLI is the only entry point - it handles all workflow execution internally.

## Documentation

See the main [README.md](../README.md) for complete documentation.

## Architecture

The analysis uses:
- **LangGraph** for workflow orchestration
- **Vertex AI (gemini-2.5-pro)** for intelligent analysis
- **GitHub API** for data fetching
- **Markdown templates** for standardized reports

The workflow (`workflows/analyze.py`) follows LangGraph best practices with a state-based flow:
```
load_config → fetch_github → analyze → generate → save → END
```
