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
      "level": "L4",
      "account_id": "712020:9b24a504-5186-4db2-a263-2f66398ba887"
    }
  ]
}
```

**Note:** 
- The `email` field is used for both JIRA and Google Drive authentication. Use the same email for both.
- The `level` field (e.g., "L4", "L5") is used to include level-specific evaluation criteria from the organizational ladder in analysis prompts. This ensures evaluations are aligned with expectations for the engineer's level.
- `drive_folder_ids` and `document_types` are optional (deprecated). By default, Google Docs analysis searches all documents owned by the user.

## Level-Based Evaluation

All analysis tools support level-based evaluation using criteria from the organizational ladder (`ladder/Matrix.html`). When a `level` field (e.g., "L4", "L5") is specified in `config.json`, the analysis prompts automatically include:

1. **Current Level Criteria**: Primary evaluation expectations for the engineer's current level
2. **Next Level Growth Areas**: Criteria for the next level (e.g., L6 for an L5 engineer) to identify promotion readiness and development opportunities

This dual approach ensures:
- Evaluations are aligned with the engineer's current level expectations
- Growth areas are clearly identified for promotion readiness
- Actionable feedback focuses on both meeting current level and developing toward next level

The ladder criteria cover:
- **Technical skills**: Code quality, testing, debugging, observability, architecture
- **Delivery**: Work breakdown, prioritization, accountability, tradeoffs
- **Feedback, Communication, Collaboration**: Feedback delivery, communication, knowledge sharing, team support
- **Leadership**: Process thinking, influence, mentoring, strategy

## Adding New Users

To add a new user to the system:

```bash
just add-report
```

This interactive command will:
1. Prompt for user details (username, email, name, level, JIRA account ID)
2. Add the user to `config.json`
3. Create the report folder structure (`reports/<slugified-name>/notes/`)
4. Create a README in the notes folder explaining its purpose

## Human Feedback and Notes

Each report directory includes a `notes/` folder for ad-hoc markdown files, self-reviews, and feedback. **Human feedback is essential** - while automated analysis provides valuable metrics, it doesn't capture the full picture. Use the notes folder to:

- **Self-reviews**: Personal reflections on work and growth
- **Feedback**: Notes from managers, peers, or stakeholders
- **Context**: Additional information that explains the metrics
- **Goals**: Development goals and progress tracking
- **Achievements**: Notable accomplishments not captured in metrics

The notes folder complements automated analysis and provides the human context that metrics alone cannot capture.

## Tools

### GitHub PR Review Analysis

Analyzes PR review contributions, comment quality, and cross-boundary work. Evaluations are tailored to the engineer's level when specified in config.

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

## Batch Operations

### Clean Analysis Reports

Remove all analysis reports for a specified period:

```bash
just clean 2025H2
```

This removes `jira-analysis.md`, `github-review-analysis.md`, and `gdocs-analysis.md` files for all users in the specified period.

### Run All Analyses

Run all three analysis tools for all users in parallel:

```bash
just analyze-all 2025H2
```

This command:
1. Runs `gh-analyze`, `jira-analyze`, and `gdocs-analyze` for all users in `config.json` in parallel
2. Calibrates all reports to ensure fair benchmarking across users and levels
3. Generates holistic review packages (`review-package.md`) for each user

**Note:** This can take significant time depending on the number of users and data volume. Progress is shown for each analysis.

### Calibrate Reports

After running analyses, calibrate reports to ensure fairness:

```bash
just calibrate 2025H2
```

This creates calibrated versions (`*-calibrated.md`) of each analysis report that:
- Ensure evaluations are appropriate for each engineer's level
- Maintain consistency across engineers at the same level
- Account for level-specific expectations from the organizational ladder
- Provide fair and constructive feedback

### Generate Review Packages

Generate holistic review packages that combine all analyses:

```bash
just review-package 2025H2
```

This creates `review-package.md` files for each user that include:
- All analysis reports (calibrated versions if available)
- Self-reviews from the `notes/` folder
- 1:1 meeting notes (`lattice.md` if available)
- Level-appropriate evaluation criteria
- Structured answers to review questions:
  - Key achievements and impact
  - Challenges and improvement suggestions
  - Development focus areas
  - Ratings for Technical Skills, Delivery, Communication/Collaboration, Leadership
  - Overall performance rating

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
        ├── jira-analysis.md
        ├── jira-analysis-calibrated.md (after calibration)
        ├── github-review-analysis.md
        ├── github-review-analysis-calibrated.md (after calibration)
        ├── gdocs-analysis.md
        ├── gdocs-analysis-calibrated.md (after calibration)
        ├── review-package.md (after review-package generation)
        ├── artifacts/ (Google Docs markdown conversions)
        └── notes/
            ├── README.md
            ├── lattice.md (1:1 meeting notes)
            └── *.md (self-reviews, feedback, etc.)
        ├── <tool>-analysis.md    # Main analysis report
        ├── notes/                 # For ad-hoc markdown files, self-reviews, and feedback
        │   ├── README.md         # Explains the purpose of the notes folder
        │   └── <your-files>.md   # Your self-reviews, feedback, etc.
        ├── config.json            # User config (if individual)
        └── artifacts/             # Additional artifacts (gdocs only)
            └── *.md
```

**Important**: The `notes/` folder is automatically created in each report directory. Use it to add human context, self-reviews, and feedback that complements the automated analysis. See the [Human Feedback and Notes](#human-feedback-and-notes) section above for more details.

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
