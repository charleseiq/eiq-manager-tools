# JIRA Sprint & Epic Analysis

A LangGraph-based workflow for analyzing JIRA sprint performance, velocity, and epic allocation.

## Overview

This module analyzes JIRA data to provide insights into:
- **Sprint Board Management**: Loading before sprint start and completion rates
- **Velocity Analysis**: Trends and consistency in sprint velocity
- **Epic Allocation**: Time distribution across epics for time sheet and capex reporting
- **Worklog Patterns**: Time tracking behavior and patterns

## Quick Start

### Prerequisites

1. JIRA API token (get from https://id.atlassian.com/manage-profile/security/api-tokens)
2. JIRA email address
3. JIRA instance URL
4. Google Cloud project with Vertex AI enabled

### Setup

1. Add JIRA credentials to `.env`:
   ```bash
   JIRA_TOKEN=your_jira_api_token
   JIRA_EMAIL=your_email@example.com
   JIRA_URL=https://yourcompany.atlassian.net
   ```

2. Run analysis:
   ```bash
   # Using slugified name with period (RECOMMENDED)
   just jira-analyze -n varun-sundar -p 2025H2
   
   # Using username
   just jira-analyze -u varunsundar -p 2025H2
   ```

## Usage

### Command Line

```bash
# Using slugified name with period (RECOMMENDED - no quotes needed!)
jira-analyze -n varun-sundar -p 2025H2          # Second half of 2025
jira-analyze -n ariel-ledesma -p 2025H1         # First half of 2025
jira-analyze -n erin-friesen -p 2026Q1          # First quarter of 2026
jira-analyze -n varun-sundar -p 2025            # Full year 2025

# Alternative: Using full name (requires quotes for spaces)
jira-analyze -n "Varun Sundar" -p 2025H2

# Using username with dates
jira-analyze -u varunsundar -s 2025-07-01 -e 2025-12-31
```

### Period Formats

- `YYYYH1` - First half (Jan 1 - Jun 30)
- `YYYYH2` - Second half (Jul 1 - Dec 31)
- `YYYYQ1` - First quarter (Jan 1 - Mar 31)
- `YYYYQ2` - Second quarter (Apr 1 - Jun 30)
- `YYYYQ3` - Third quarter (Jul 1 - Sep 30)
- `YYYYQ4` - Fourth quarter (Oct 1 - Dec 31)
- `YYYY` - Full year (Jan 1 - Dec 31)

## Configuration

### Centralized Config (`config.json`)

```json
{
  "users": [
    {
      "username": "varunsundar",
      "account_id": "5d1234567890abcdef",
      "name": "Varun Sundar"
    }
  ]
}
```

**Important Notes:**
- `jira_url` is NOT in config.json - it must be set in `.env` file as `JIRA_URL`
- Periods are parsed directly from the `-p` flag. No need to define them in config!

## Output

Reports are saved to `reports/<slugified-name>/<period>/jira-analysis.md` and include:

1. **Executive Summary** - Key metrics at a glance
2. **Sprint Board Management** - Loading and completion analysis
3. **Velocity Analysis** - Trends and consistency
4. **Epic Allocation & Time Tracking** - Day allocation for time sheets/capex
5. **Sprint Planning Quality** - Planning accuracy metrics
6. **Worklog Patterns** - Time logging behavior
7. **Recommendations** - Actionable insights

## Architecture

- **LangGraph Workflow**: Orchestrates data fetching, analysis, and report generation
- **JIRA REST API**: Fetches sprints, issues, worklogs, and epics
- **Vertex AI**: Generates comprehensive analysis using Gemini 2.5 Pro
- **Jinja2 Templates**: Standardized report format

## See Also

- [Main README](../README.md) - Overall project documentation
- [GitHub Analysis](../pr-review-analysis/README.md) - Similar analysis for GitHub PRs
