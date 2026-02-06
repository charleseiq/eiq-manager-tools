# Engineering Performance Analysis Tools

A comprehensive suite of CLI tools for analyzing engineering performance across GitHub PR reviews, JIRA sprint/epic tracking, Google Docs technical design documents, and performance notes. Built with LangGraph workflows and Google Cloud Vertex AI.

## Features

- **Multi-source Analysis**: GitHub PRs, JIRA sprints/epics, Google Docs, and performance notes
- **Level-Based Evaluation**: Automatic inclusion of organizational ladder criteria based on engineer level
- **Fair Benchmarking**: Calibration ensures consistent evaluation across users and levels
- **Holistic Reviews**: Combines quantitative metrics with qualitative feedback
- **Batch Processing**: Run all analyses (GitHub PR Review, JIRA Sprint & Epic, Google Docs, Notes Analysis) for all users with a single command (`just analyze-all`) or individual analysis types (`-a` flag)
- **Human Context**: Notes folder for self-reviews, feedback, and additional context

## Overview

This repository provides four complementary analysis tools:

1. **[GitHub PR Review Analysis](eiq/gh-analysis/README.md)** (`gh-analyze`) - Analyzes code review quality, comment classification, and cross-boundary contributions
2. **[JIRA Sprint & Epic Analysis](eiq/jira-analysis/README.md)** (`jira-analyze`) - Tracks sprint performance, velocity, epic allocation, and worklog patterns
3. **[Google Docs Analysis](eiq/gdocs-analysis/README.md)** (`gdocs-analyze`) - Evaluates technical design document quality, comment responses, and team engagement
4. **Notes Analysis** (`notes-analyze`) - Analyzes self-reviews, feedback, and other notes files with ladder criteria

Together, these tools provide a comprehensive view of engineering performance across code review, planning, documentation, and qualitative feedback.

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

## Consistent Command-Line Interface

All analysis tools (`gh-analyze`, `jira-analyze`, `gdocs-analyze`, `notes-analyze`, `generate-review`) use consistent flags:

- **`-n, --name NAME`** - User name (slugified format recommended)
- **`-p, --period PERIOD`** - Period string (YYYYH1, YYYYH2, YYYYQ1-Q4, YYYY)
- **`-a, --all`** - Run for all users in config.json (requires `-p/--period`)
- **Positional arguments** - First arg = name, second arg = period (backward compatible)

**Examples:**
```bash
# Single user (flags - recommended)
just gh-analyze -n varun-sundar -p 2025H2
just jira-analyze -n varun-sundar -p 2025H2
just gdocs-analyze -n varun-sundar -p 2025H2
just notes-analyze -n ariel-ledesma -p 2025H2
just generate-review -n ariel-ledesma -p 2025H2

# All users (flags - recommended)
just gh-analyze -a -p 2025H2
just jira-analyze -a -p 2025H2
just gdocs-analyze -a -p 2025H2
just notes-analyze -a -p 2025H2
just generate-review -a -p 2025H2

# Single user (positional - backward compatible)
just gh-analyze varun-sundar 2025H2
just notes-analyze ariel-ledesma 2025H2
just generate-review ariel-ledesma 2025H2

# All users (positional - backward compatible, but -a flag preferred)
just generate-review -p 2025H2  # Still works, but -a is clearer
just generate-review 2025H2      # Still works, but -a is clearer
```

**Note:** Flags take precedence over positional arguments. If both are provided, flags are used.

## Level-Based Evaluation

All analysis tools support level-based evaluation using criteria from the organizational ladder (`ladder/Matrix.html`). When a `level` field (e.g., "L4", "L5") is specified in `config.json`, the analysis prompts automatically include:

1. **Current Level Criteria**: Primary evaluation expectations for the engineer's current level
2. **Next Level Growth Areas**: Criteria for the next level (e.g., L6 for an L5 engineer) to identify promotion readiness and development opportunities

This dual approach ensures:
- Evaluations are aligned with the engineer's current level expectations
- Growth areas are clearly identified for promotion readiness
- Actionable feedback focuses on both meeting current level and developing toward next level

The ladder criteria are organized by four main dimensions:
- **Technical Skills**: Quality, operational excellence, design & architecture
- **Delivery**: Incremental value delivery, self-organization
- **Feedback, Communication, Collaboration**: Feedback, communication, collaboration
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
# Using slugified name with flags (recommended)
scripts/gh-analyze -n varun-sundar -p 2025H2

# Or using positional arguments (backward compatible)
scripts/gh-analyze varun-sundar 2025H2

# Or using just
just gh-analyze -n varun-sundar -p 2025H2

# Run for all users in config.json
just gh-analyze -a -p 2025H2
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
# Using slugified name with flags (recommended)
scripts/jira-analyze -n varun-sundar -p 2025H2

# Or using positional arguments (backward compatible)
scripts/jira-analyze varun-sundar 2025H2

# Or using just
just jira-analyze -n varun-sundar -p 2025H2

# Run for all users in config.json
just jira-analyze -a -p 2025H2
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
# Using slugified name with flags (recommended)
just gdocs-analyze -n varun-sundar -p 2025H2

# Or using positional arguments (backward compatible)
just gdocs-analyze varun-sundar 2025H2

# Run for all users in config.json
just gdocs-analyze -a -p 2025H2
```
# Using slugified name (recommended)
scripts/gdocs-analyze -n varun-sundar -p 2025H2

# Or using just
just gdocs-analyze -n varun-sundar -p 2025H2
```

**Features:**
- Document quality evaluation (problem clarity, concept clarity, execution path)
- Owner filtering (only analyzes documents owned by the user)
- Date filtering (only includes documents **created** during the period, not just modified)
- Automatic document discovery (searches all Google Docs owned by user)
- Comment response analysis
- Team engagement metrics
- Artifact storage (markdown conversions)

**Note:** Run `just auth` first to set up Google Drive authentication using Secret Manager.

📖 **[Full Documentation →](eiq/gdocs-analysis/README.md)**

## Batch Operations

### Clean Analysis Reports

Remove all analysis reports and artifacts for a specified period:

```bash
just clean 2025H2
```

This removes:
- All analysis report files (`jira-analysis.md`, `github-review-analysis.md`, `gdocs-analysis.md`)
- All old `*-calibrated.md` files (from before in-place calibration was implemented)
- All `artifacts/` directories (containing converted Google Docs markdown files)

for all users in the specified period.

**Note:** Calibration now updates analysis files in place, so separate `-calibrated.md` files are no longer created. Any existing `-calibrated.md` files are legacy and will be removed by this command.

### Run All Analyses

Run all four analysis tools for all users sequentially:

```bash
just analyze-all 2025H2
```

This command:
1. Runs `gh-analyze`, `jira-analyze`, `gdocs-analyze`, and `notes-analyze` for all users in `config.json` sequentially (one at a time). You can also run individual analyses for all users using the `-a` flag: `just gh-analyze -a -p 2025H2`
2. Shows all progress bars and loading indicators from each analysis in real-time
3. Calibrates all reports to ensure fair benchmarking across users and levels
4. Generates holistic review packages (`review-package.md`) for each user that incorporate all analyses

**Note:**
- Analyses run sequentially to avoid rate limiting and provide clear progress visibility
- This can take significant time depending on the number of users and data volume
- All Rich progress bars from individual analyses are displayed in real-time
- The review packages prioritize notes analysis (human-written feedback) over automated analyses
- You can also run individual analysis types for all users using the `-a` flag:
  - `just gh-analyze -a -p 2025H2` - GitHub analysis for all users
  - `just jira-analyze -a -p 2025H2` - JIRA analysis for all users
  - `just gdocs-analyze -a -p 2025H2` - Google Docs analysis for all users
  - `just notes-analyze -a -p 2025H2` - Notes analysis for all users

### Calibrate Reports

After running analyses, calibrate reports to ensure fairness:

```bash
just calibrate 2025H2
```

This updates analysis reports in place, modifying only sections that need calibration to ensure:
- Ensure evaluations are appropriate for each engineer's level
- Maintain consistency across engineers at the same level
- Account for level-specific expectations from the organizational ladder
- Provide fair and constructive feedback

### Analyze Notes Files

Analyze all markdown files in the notes folder (self-reviews, feedback, etc.):

```bash
# Analyze notes for a specific user (using flags)
just notes-analyze -n ariel-ledesma -p 2025H2

# Or using positional arguments
just notes-analyze ariel-ledesma 2025H2

# Analyze notes for all users
just notes-analyze -a -p 2025H2

# Note: Notes analysis is automatically included in `just analyze-all`
```

This creates `notes-analysis.md` files that:
- Analyze all `.md` files in the `notes/` folder (excluding `README.md` and `lattice.md`)
- Combine notes with level-appropriate ladder criteria
- Identify themes, patterns, and insights across all notes
- Provide actionable insights for performance evaluation

### Generate Review Packages

Generate holistic review packages that combine all analyses:

```bash
# Generate review packages for all users (recommended)
just generate-review -a -p 2025H2

# Or backward compatible (still works, but -a is clearer):
just generate-review -p 2025H2
just generate-review 2025H2

# Generate review package for a specific user
just generate-review -n ariel-ledesma -p 2025H2

# Or using positional arguments
just generate-review ariel-ledesma 2025H2

# Or use the legacy alias
just review-package -a -p 2025H2
```

This creates `review-package.md` files for each user that include:
- **All analysis reports** (GitHub PR Review, JIRA Sprint & Epic, Google Docs) - updated in place by calibration if run
- **Notes analysis** (comprehensive analysis of all notes files) - **HIGHEST PRIORITY** - human-written feedback is weighted more heavily than automated analyses
- **1:1 meeting notes** (`lattice.md` if available) - also high priority
- Level-appropriate evaluation criteria (used for context, not explicitly mentioned)
- Well-formatted markdown with proper headings and structure
- Structured answers to review questions:
  - Key achievements and impact (with specific project/initiative references)
  - Challenges and improvement suggestions
  - Development focus areas
  - Ratings for Technical Skills, Delivery, Communication/Collaboration, Leadership
  - Overall performance rating

**Note:** Run `just notes-analyze-all` first to generate notes analysis, or use `just analyze-all` which includes this step.

### Convert PDF Files to Markdown

Convert PDF files (e.g., review documents) to markdown:

```bash
# Convert all PDFs in reports/ directories
just convert-pdfs

# Convert PDFs in a specific path
just convert-pdfs-path reports/ariel-ledesma/2025H2/notes
```

This is useful for converting PDF review documents to markdown so they can be included in review packages.

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
        ├── jira-analysis.md (updated in place by calibration)
        ├── github-review-analysis.md (updated in place by calibration)
        ├── gdocs-analysis.md (updated in place by calibration)
        ├── notes-analysis.md (after notes-analyze)
        ├── review-package.md (after generate-review)
        ├── artifacts/ (Google Docs markdown conversions - removed by `just clean`)
        └── notes/
            ├── README.md
            ├── lattice.md (1:1 meeting notes)
            └── *.md (self-reviews, feedback, PDF conversions, etc.)
```

**Important**: The `notes/` folder is automatically created in each report directory. Use it to add human context, self-reviews, and feedback that complements the automated analysis. See the [Human Feedback and Notes](#human-feedback-and-notes) section above for more details.

## Workflow

### Complete Analysis Workflow

For a comprehensive analysis of all users for a period:

```bash
# Step 1: Run all analyses (includes calibration and notes analysis)
just analyze-all 2025H2

# This runs:
# - gh-analyze, jira-analyze, gdocs-analyze for all users
# - Calibration of all reports
# - Notes analysis for all users
# - Review package generation
```

### Individual Steps

You can also run steps individually:

```bash
# Step 1: Run individual analyses
just gh-analyze -n varun-sundar -p 2025H2
just jira-analyze -n varun-sundar -p 2025H2
just gdocs-analyze -n varun-sundar -p 2025H2

# Or run for all users at once
just gh-analyze -a -p 2025H2
just jira-analyze -a -p 2025H2
just gdocs-analyze -a -p 2025H2

# Step 2: Calibrate reports (optional but recommended)
just calibrate 2025H2

# Step 3: Analyze notes
just notes-analyze -n varun-sundar -p 2025H2
# Or using positional arguments:
just notes-analyze varun-sundar 2025H2
# Or for all users:
just notes-analyze -a -p 2025H2

# Step 4: Generate review package
just generate-review -a -p 2025H2  # All users (recommended)
# Or backward compatible:
just generate-review -p 2025H2
just generate-review 2025H2
# Or for a specific user:
just generate-review -n varun-sundar -p 2025H2
```

## Architecture

### Shared Utilities

The codebase uses shared utilities in `eiq/shared/`:

- **`ai_utils.py`**: Vertex AI LLM setup and ladder criteria loading
- **`config_loader.py`**: Configuration loading and user lookup utilities
- **`cli_utils.py`**: CLI utilities (slugify, period parsing, output directory resolution)
- **`ladder_utils.py`**: Organizational ladder parsing and formatting
- **`rich_utils.py`**: Rich console utilities for progress display

### Workflow Structure

Each analysis tool uses a LangGraph workflow:

```
load_config → fetch_data → analyze_with_vertexai → generate_report → save_report → END
```

The workflows are stateful and pass data through a `TypedDict` state object, ensuring type safety and clear data flow.

## Development

### Running Tests

```bash
just test
```

### Formatting Code

```bash
just format
```

### Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`:
- `ruff check` - Linting
- `ruff format` - Code formatting
- `ty check` - Type checking
- `pytest` - Unit tests

## License

[Add your license here]
