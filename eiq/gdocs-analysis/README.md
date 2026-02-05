# Google Docs Analysis

Analyzes technical design documents and other write-ups from Google Docs to evaluate document quality, comment responses, and team engagement.

## Quick Start

```bash
# Using slugified name with period (recommended)
scripts/gdocs-analyze -n varun-sundar -p 2025H2

# Or using just
just gdocs-analyze -n varun-sundar -p 2025H2
```

## Features

- **Document Scraping**: Automatically finds Google Docs from specified folders
- **Markdown Conversion**: Converts documents to markdown for analysis
- **Quality Evaluation**: Analyzes clarity, completeness, technical depth, and structure
- **Comment Analysis**: Evaluates how authors responded to feedback
- **Engagement Metrics**: Measures team collaboration and discussion depth
- **Artifact Storage**: Saves converted markdown files for reference

## Setup

### Prerequisites

1. Google Cloud project with Google Drive API enabled
2. OAuth 2.0 credentials configured
3. Google Drive folders with design documents
4. Google Cloud project with Vertex AI enabled

### Google Drive API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable **Google Drive API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Drive API" and enable it
3. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as application type
   - Download credentials JSON file
4. Place credentials file:
   ```bash
   mkdir -p ~/.config/gdocs-analysis
   cp /path/to/downloaded/credentials.json ~/.config/gdocs-analysis/credentials.json
   ```

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
      "name": "Varun Sundar"
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
- The `email` field is the same email used for JIRA
- During OAuth flow, authenticate with the same Google account as this email
- **By default, all Google Docs in your Drive are searched** - no `drive_folder_ids` or `document_types` needed
- If `drive_folder_ids` is specified, only those folders will be searched (legacy behavior)
- If `document_types` is specified with `drive_folder_ids`, only documents matching those name patterns will be included

### Environment Variables

```bash
EVOLUTIONIQ_EMAIL=your_email@evolutioniq.com
GOOGLE_CLOUD_PROJECT=your-project-id
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
- **Clarity**: How easy is the document to understand?
- **Completeness**: Does it cover all necessary aspects (problem, solution, alternatives, risks, implementation)?
- **Technical Depth**: Does it demonstrate deep technical understanding?
- **Structure**: Is it well-organized with clear sections?

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

- **load_config**: Loads user configuration and Google Drive folder IDs
- **fetch_gdocs**: Lists documents from Google Drive folders and converts to markdown
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

**"Credentials file not found":**
- Ensure `credentials.json` is in `~/.config/gdocs-analysis/`
- Verify file was downloaded from Google Cloud Console

**"Failed to authenticate with Google Drive":**
- Delete `~/.config/gdocs-analysis/token.json` and re-authenticate
- Ensure Google Drive API is enabled in your Google Cloud project
- Verify OAuth consent screen is configured

**"Please authenticate with Google account":**
- During OAuth flow, use the same Google account as the email in `config.json`
- This should match your JIRA email

### No Documents Found

- Ensure documents were created/modified within the date range
- Verify you have read access to the documents
- If using `drive_folder_ids`, verify folder IDs are correct in `config.json`
- If using `document_types`, check that document names match the patterns

### Conversion Errors

- Check that documents are accessible (not private/restricted)
- Ensure `markitdown[all]` is installed
- Some complex documents may not convert perfectly
- Tool falls back to Google Drive API export if markitdown fails

## See Also

- [Main README](../../README.md) - Overall project documentation
- [GitHub Analysis](../gh-analysis/README.md) - PR review analysis
- [JIRA Analysis](../jira-analysis/README.md) - Sprint and epic tracking
