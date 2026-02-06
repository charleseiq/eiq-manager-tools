# GitHub PR Review Analysis

Analyzes GitHub PR review contributions using LangGraph workflows and Vertex AI to evaluate code review quality, comment classification, and cross-boundary work.

## Quick Start

```bash
# Using slugified name with period (recommended)
scripts/gh-analyze -n varun-sundar -p 2025H2

# Or using just
just gh-analyze -n varun-sundar -p 2025H2

# Run for all users in config.json
just gh-analyze -a -p 2025H2
```

## Features

- **Comment Classification**: Automatically categorizes comments as Architecture, Logic, or Nits
- **PR Description Quality**: Scores PR descriptions on context, risk, and clarity
- **Cross-Boundary Analysis**: Identifies contributions outside primary repository
- **Conflict Management**: Analyzes tone and resolution patterns
- **Significant Changes**: Highlights most impactful contributions

## Setup

### Prerequisites

1. GitHub API token with `repo` scope
2. Google Cloud project with Vertex AI enabled
3. Centralized `config.json` with user information

### Environment Variables

```bash
GITHUB_TOKEN=your_github_token_here
GOOGLE_CLOUD_PROJECT=eiq-development
GOOGLE_CLOUD_LOCATION=us-east4
```

### Configuration

Add users to `config.json`:

```json
{
  "organization": "EvolutionIQ",
  "users": [
    {
      "username": "varunsundar",
      "email": "varun.sundar@evolutioniq.com",
      "name": "Varun Sundar",
      "level": "L4"
    }
  ]
}
```

**Note:** The `level` field (e.g., "L4", "L5") is optional but recommended. When specified, analysis includes:
- **Current level criteria**: Primary evaluation expectations for the engineer's current level
- **Next level growth areas**: Criteria for the next level to identify promotion readiness and development opportunities

## Usage

### Basic Commands

```bash
# Using slugified name with flags (recommended - no quotes needed)
scripts/gh-analyze -n varun-sundar -p 2025H2

# Using positional arguments (backward compatible)
scripts/gh-analyze varun-sundar 2025H2

# Using full name (requires quotes)
scripts/gh-analyze -n "Varun Sundar" -p 2025H2

# Using username
scripts/gh-analyze -u varunsundar -p 2025H2

# Custom date range
scripts/gh-analyze -n varun-sundar -s 2025-07-01 -e 2025-12-31

# Run for all users in config.json
scripts/gh-analyze -a -p 2025H2
```

### Options

- `-a, --all` - Run analysis for all users in config.json (requires -p/--period)
- `-n, --name NAME` - Person's name (slugified format recommended). Can also be provided as first positional argument.
- `-u, --username USERNAME` - GitHub username
- `-p, --period PERIOD` - Period string (YYYYH1, YYYYH2, YYYYQ1-Q4, YYYY). Can also be provided as second positional argument.
- `-s, --start DATE` - Start date (YYYY-MM-DD)
- `-e, --end DATE` - End date (YYYY-MM-DD)
- `--org ORG` - Organization name (default: EvolutionIQ)
- `-o, --output DIR` - Output directory
- `--github-token TOKEN` - GitHub token (or set GITHUB_TOKEN env var)
- `--project PROJECT` - Google Cloud project (or set GOOGLE_CLOUD_PROJECT env var)

## Output

Reports are saved to `reports/<slugified-name>/<period>/github-review-analysis.md` and include:

- Executive summary with key metrics
- Comment distribution analysis (Architecture/Logic/Nits)
- PR description quality scores
- Cross-boundary contribution summary
- Conflict management examples
- Significant changes summary
- Recommendations

## Architecture

The analysis uses a LangGraph workflow:

```
load_config → fetch_github → analyze → generate → save → END
```

- **load_config**: Loads user configuration from centralized or individual config
- **fetch_github**: Queries GitHub API for PRs reviewed and authored by user
- **analyze**: Uses Vertex AI (gemini-2.5-pro) to analyze review data
- **generate**: Formats analysis into markdown report
- **save**: Writes report to file system

### Implementation

- **Workflow**: `workflows/analyze.py` - LangGraph state machine
- **Templates**: `templates/` - Jinja2 report templates
- **API**: GitHub REST API v3
- **AI**: Google Cloud Vertex AI (gemini-2.5-pro)

## Troubleshooting

### "GitHub token required"
```bash
export GITHUB_TOKEN=your_token_here
# Or add to .env file
```

### "No PRs found"
- Verify username matches GitHub username exactly
- Check date range includes PR creation/modification dates
- Ensure organization name is correct

### "Google Cloud project required"
```bash
export GOOGLE_CLOUD_PROJECT=eiq-development
```

## Report Structure

Each report directory includes a `notes/` folder for ad-hoc markdown files, self-reviews, and feedback. **Human feedback is essential** - while automated analysis provides valuable metrics, it doesn't capture the full picture. Use the notes folder to add context, self-reviews, manager feedback, and other human insights that complement the automated analysis.

See the [Main README](../../README.md#human-feedback-and-notes) for more details on using the notes folder.

## See Also

- [Main README](../../README.md) - Overall project documentation
- [JIRA Analysis](../jira-analysis/README.md) - Sprint and epic tracking
- [Google Docs Analysis](../gdocs-analysis/README.md) - Technical design document analysis
