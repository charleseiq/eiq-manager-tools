# Google Docs Analysis

Analyzes technical design documents and other write-ups from Google Docs to evaluate document quality, comment responses, and team engagement.

## Quick Start

```bash
# First-time setup: Authenticate (one-time)
just auth

# Run analysis
just gdocs-analyze -n varun-sundar -p 2025H2

# Or using the script directly
scripts/gdocs-analyze -n varun-sundar -p 2025H2
```

**Note:** The tool automatically searches all Google Docs owned by the user within the specified date range. No folder configuration needed!

## Features

- **Document Discovery**: Automatically finds Google Docs owned by the user within a date range
- **Owner Filtering**: Only analyzes documents where the user is the owner
- **Markdown Conversion**: Converts documents to markdown for analysis
- **Quality Evaluation**: Analyzes problem clarity, concept clarity, and execution path
- **Comment Analysis**: Evaluates how authors responded to feedback
- **Engagement Metrics**: Measures team collaboration and discussion depth
- **Artifact Storage**: Saves converted markdown files for reference

## Setup

### Prerequisites

1. Google Cloud project with Google Drive API enabled
2. Google Cloud project with Vertex AI enabled
3. Application Default Credentials configured (via `just auth`)

### Authentication Setup

The easiest way to set up authentication is using the `just auth` command:

```bash
just auth
```

This command will:
1. Set up Google Cloud Application Default Credentials (for Vertex AI)
2. Generate Google Drive OAuth token using Secret Manager (no manual credential file needed)
3. Verify all required APIs are enabled

**Manual Setup (Alternative):**

If you prefer manual setup or need to use a different authentication method:

1. Enable **Google Drive API**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Drive API" and enable it
2. OAuth credentials are managed via Secret Manager:
   - Credentials are stored in GCP Secret Manager (`google_drive_oauth_json` secret)
   - The `generate-drive-token.py` script retrieves them automatically
   - Or manually download credentials and place at `~/.config/gdocs-analysis/credentials.json`

### Configuration

**Default behavior:** The tool searches **all Google Docs** in your Google Drive that were created or modified within the specified date range. No configuration needed!

**Optional (deprecated):** If you want to limit the search to specific folders or document types, you can add `drive_folder_ids` and `document_types` to centralized `config.json`:

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
  ],
  "drive_folder_ids": [
    "1a2b3c4d5e6f7g8h9i0j",
    "9z8y7x6w5v4u3t2s1r0q"
  ],
  "document_types": [
    "Technical Design Doc",
    "TDD",
    "Design Document",
    "Architecture Review"
  ]
}
```

**Important Notes:**
- The `email` field is the same email used for JIRA (set via `EVOLUTIONIQ_EMAIL` environment variable)
- During OAuth flow, authenticate with the same Google account as this email
- **By default, all Google Docs owned by the user are searched** - no `drive_folder_ids` or `document_types` needed
- Only documents where the user is an owner are included in the analysis
- The `level` field (e.g., "L4", "L5") is optional but recommended. When specified, analysis includes:
  - **Current level criteria**: Primary evaluation expectations for the engineer's current level
  - **Next level growth areas**: Criteria for the next level to identify promotion readiness and development opportunities
- If `drive_folder_ids` is specified, only those folders will be searched (legacy behavior, deprecated)
- If `document_types` is specified with `drive_folder_ids`, only documents matching those name patterns will be included (deprecated)

### Environment Variables

```bash
EVOLUTIONIQ_EMAIL=your_email@evolutioniq.com
GOOGLE_CLOUD_PROJECT=eiq-development
GOOGLE_CLOUD_LOCATION=us-east4
```

**Note:** `EVOLUTIONIQ_EMAIL` is shared with JIRA analysis. Use the same email for both JIRA and Google account authentication.

## Usage

### Basic Commands

```bash
# Using slugified name (recommended)
scripts/gdocs-analyze -n varun-sundar -p 2025H2

# Using email/username
scripts/gdocs-analyze -u varun.sundar@evolutioniq.com -p 2025H2

# Custom date range
scripts/gdocs-analyze -n varun-sundar -s 2025-07-01 -e 2025-12-31

# Custom output directory
scripts/gdocs-analyze -n varun-sundar -p 2025H2 -o reports/custom/path
```

### Options

- `-n, --name NAME` - Person's name (slugified format recommended)
- `-u, --username USERNAME` - Email or username
- `-p, --period PERIOD` - Period string (YYYYH1, YYYYH2, YYYYQ1-Q4, YYYY)
- `-s, --start DATE` - Start date (YYYY-MM-DD)
- `-e, --end DATE` - End date (YYYY-MM-DD)
- `-o, --output DIR` - Output directory
- `--project PROJECT` - Google Cloud project (or set GOOGLE_CLOUD_PROJECT env var)
- `--location LOCATION` - Vertex AI location (default: us-east4)

## Output

The analysis generates:

1. **Report**: `reports/<name>/<period>/gdocs-analysis.md`
   - Document quality analysis
   - Comment response evaluation
   - Team engagement metrics
   - Recommendations

2. **Artifacts**: `reports/<name>/<period>/artifacts/`
   - Markdown versions of all analyzed documents
   - Useful for reference and further analysis

## Evaluation Criteria

### Document Quality

Documents are evaluated against three core criteria:

1. **Clarity of Problem Statement**
   - Is the problem being addressed clearly defined?
   - Is the "why" (motivation/context) clearly explained?
   - Can a reader understand what problem this design solves?

2. **Clarity of Concept and Communication**
   - Is the proposed solution concept clearly explained?
   - Does it effectively communicate the "what" (what is being built/changed)?
   - Are technical concepts explained accessibly?
   - Is the document free of ambiguity?

3. **Clear Execution Path**
   - Is there a concrete, actionable plan for implementation?
   - Are steps, phases, dependencies, and sequencing clearly defined?
   - Is it clear how to proceed from reading to implementing?

**Additional Requirements:**
- **Diagrams**: Required for architecture changes. Diagrams should illustrate current vs. proposed state.
- Documents must excel in all three core areas to receive high scores.
- Missing diagrams for architecture changes results in lower scores.

### Comment Responses
- **Response Rate**: How many comments received responses?
- **Response Quality**: Were responses thoughtful and helpful?
- **Feedback Incorporation**: Were suggestions incorporated?
- **Clarification**: Did authors provide additional context when requested?

### Team Engagement
- **Comment Volume**: How many comments were made?
- **Discussion Depth**: How substantive were the discussions?
- **Collaboration**: Did multiple team members engage?
- **Review Quality**: Were comments constructive and helpful?

## Architecture

The analysis uses a LangGraph workflow:

```
load_config → fetch_gdocs → analyze → generate → save → END
```

- **load_config**: Loads user configuration (email from config.json)
- **fetch_gdocs**: Searches Google Drive for documents owned by the user, filters by date range, and converts to markdown
- **analyze**: Uses Vertex AI to evaluate document quality, responses, and engagement
- **generate**: Formats analysis into markdown report
- **save**: Writes report and artifacts to file system

### Implementation

- **Workflow**: `workflows/analyze.py` - LangGraph state machine
- **Templates**: `templates/` - Jinja2 report templates
- **API**: Google Drive API v3
- **Conversion**: markitdown library (with Google Drive API fallback)
- **AI**: Google Cloud Vertex AI (gemini-2.5-pro)

## Troubleshooting

### Authentication Issues

**"Google Drive token not found":**
- Run `just auth` to generate the token automatically using Secret Manager
- Or manually run `just generate-drive-token` if you need to regenerate

**"Failed to authenticate with Google Drive":**
- Delete `~/.config/gdocs-analysis/token.json` and run `just auth` again
- Ensure Google Drive API is enabled in your Google Cloud project
- Verify OAuth consent screen is configured
- Ensure Application Default Credentials are set up (run `just auth`)

**"Please authenticate with Google account":**
- During OAuth flow, use the same Google account as your `EVOLUTIONIQ_EMAIL`
- This should match your JIRA email
- If on a remote server, ensure SSH tunnel on port 8989 is set up

### No Documents Found

- Ensure documents were created/modified within the date range
- **Important**: Only documents where the user is an owner are included
- Verify you are the owner of the documents (not just a viewer/editor)
- Check that the email in `config.json` matches the Google account that owns the documents
- If using `drive_folder_ids` (deprecated), verify folder IDs are correct in `config.json`
- If using `document_types` (deprecated), check that document names match the patterns

### Conversion Errors

- Check that documents are accessible (not private/restricted)
- Ensure `markitdown[all]` is installed
- Some complex documents may not convert perfectly
- Tool falls back to Google Drive API export if markitdown fails

## Report Structure

Each report directory includes a `notes/` folder for ad-hoc markdown files, self-reviews, and feedback. **Human feedback is essential** - while automated analysis provides valuable metrics, it doesn't capture the full picture. Use the notes folder to add context, self-reviews, manager feedback, and other human insights that complement the automated analysis.

See the [Main README](../../README.md#human-feedback-and-notes) for more details on using the notes folder.

## See Also

- [Main README](../../README.md) - Overall project documentation
- [GitHub Analysis](../gh-analysis/README.md) - PR review analysis
- [JIRA Analysis](../jira-analysis/README.md) - Sprint and epic tracking
