# JIRA Sprint & Epic Analysis

Analyzes JIRA sprint performance, velocity trends, and epic allocation using LangGraph workflows and Vertex AI. Designed for sprint planning, velocity tracking, and time allocation reporting.

## Quick Start

```bash
# Using slugified name with period (recommended)
scripts/jira-analyze -n varun-sundar -p 2025H2

# Or using just
just jira-analyze -n varun-sundar -p 2025H2
```

## Features

- **Sprint Board Management**: Analyzes sprint loading and completion rates
- **Velocity Analysis**: Tracks velocity trends and consistency
- **Epic Allocation**: Time distribution across epics for time sheets and capex reporting
- **Worklog Patterns**: Analyzes time tracking behavior
- **Accomplishments Summary**: Generates human-readable accomplishments from completed issues

## Setup

### Prerequisites

1. JIRA API token (from https://id.atlassian.com/manage-profile/security/api-tokens)
2. JIRA email address
3. JIRA instance URL
4. Google Cloud project with Vertex AI enabled

### Environment Variables

```bash
JIRA_TOKEN=your_jira_api_token_here
JIRA_URL=https://yourcompany.atlassian.net
JIRA_PROJECT=WC
EVOLUTIONIQ_EMAIL=your_email@evolutioniq.com
GOOGLE_CLOUD_PROJECT=eiq-development
GOOGLE_CLOUD_LOCATION=us-east4
```

**Important Notes:**
- `JIRA_URL` and `JIRA_PROJECT` must be set in `.env` file, not in `config.json`
- `EVOLUTIONIQ_EMAIL` is shared across JIRA and Google Docs (use the same email for both)

### Configuration

Add users to `config.json`:

```json
{
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

**Notes:** 
- The `email` field is used for JIRA assignee queries. Use the same email as your JIRA account.
- The `level` field (e.g., "L4", "L5") is optional but recommended. When specified, analysis includes:
  - **Current level criteria**: Primary evaluation expectations for the engineer's current level
  - **Next level growth areas**: Criteria for the next level to identify promotion readiness and development opportunities

## Usage

### Basic Commands

```bash
# Using slugified name (recommended - no quotes needed)
scripts/jira-analyze -n varun-sundar -p 2025H2

# Using full name (requires quotes)
scripts/jira-analyze -n "Varun Sundar" -p 2025H2

# Using email/username
scripts/jira-analyze -u varun.sundar@evolutioniq.com -p 2025H2

# Custom date range
scripts/jira-analyze -n varun-sundar -s 2025-07-01 -e 2025-12-31
```

### Options

- `-n, --name NAME` - Person's name (slugified format recommended)
- `-u, --username USERNAME` - JIRA username/email/account_id
- `-p, --period PERIOD` - Period string (YYYYH1, YYYYH2, YYYYQ1-Q4, YYYY)
- `-s, --start DATE` - Start date (YYYY-MM-DD)
- `-e, --end DATE` - End date (YYYY-MM-DD)
- `--jira-url URL` - JIRA instance URL (or set JIRA_URL env var)
- `--jira-project PROJECT` - JIRA project key (or set JIRA_PROJECT env var)
- `-o, --output DIR` - Output directory
- `--jira-token TOKEN` - JIRA API token (or set JIRA_TOKEN env var)
- `--jira-email EMAIL` - JIRA email (or set EVOLUTIONIQ_EMAIL env var, deprecated - use EVOLUTIONIQ_EMAIL)
- `--project PROJECT` - Google Cloud project (or set GOOGLE_CLOUD_PROJECT env var)

## Output

Reports are saved to `reports/<slugified-name>/<period>/jira-analysis.md` and include:

- Executive summary with key metrics
- Sprint loading and completion analysis
- Velocity trends and consistency metrics
- Epic allocation summary (for time sheets/capex)
- Sprint planning quality assessment
- Worklog pattern analysis
- Accomplishments summary
- Detailed sprint and epic breakdowns
- Recommendations

## Architecture

The analysis uses a LangGraph workflow:

```
load_config → fetch_jira → analyze → accomplishments → generate → save → END
```

- **load_config**: Loads user configuration and resolves period dates
- **fetch_jira**: Queries JIRA API for sprints, issues, worklogs, and epics
- **analyze**: Uses Vertex AI to analyze sprint metrics and epic allocation
- **accomplishments**: Generates human-readable accomplishments summary
- **generate**: Formats analysis into markdown report
- **save**: Writes report to file system

### Implementation

- **Workflow**: `workflows/analyze.py` - LangGraph state machine
- **Templates**: `templates/` - Jinja2 report templates
- **API**: JIRA REST API v3
- **AI**: Google Cloud Vertex AI (gemini-2.5-pro)

## Key Metrics

### Sprint Metrics
- Completion rate per sprint
- Velocity (story points completed)
- Sprint loading (issues assigned)
- Epic allocation percentages

### Epic Allocation
- Time spent per epic
- Story point distribution
- Percentage allocation for reporting

### Quality Metrics
- Issues with acceptance criteria
- Issues with references/definitions
- Planning ticket rate (TDDs, design docs)

## Troubleshooting

### "JIRA token required"
```bash
export JIRA_TOKEN=your_token_here
export EVOLUTIONIQ_EMAIL=your_email@evolutioniq.com
export JIRA_URL=https://yourcompany.atlassian.net
export JIRA_PROJECT=WC
```

### "Unbounded JQL queries"
- Ensure `JIRA_PROJECT` is set in environment variables
- The project filter is required to prevent unbounded queries

### "No issues found"
- Verify email/username matches JIRA assignee field exactly
- Check date range includes issue creation or update dates
- Ensure project key is correct

### "User not found in centralized config"
- Verify user exists in `config.json`
- Check username/email spelling matches exactly
- Try using slugified name format

## See Also

- [Main README](../../README.md) - Overall project documentation
- [GitHub Analysis](../gh-analysis/README.md) - PR review analysis
- [Google Docs Analysis](../gdocs-analysis/README.md) - Technical design document analysis
