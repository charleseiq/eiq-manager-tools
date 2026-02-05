# Google Docs Analysis

Analyze technical design documents and other write-ups from Google Docs to evaluate document quality, comment responses, and team engagement.

## Features

- **Document Scraping**: Automatically finds and downloads Google Docs from specified folders
- **Markdown Conversion**: Converts Google Docs to markdown using `markitdown`
- **Quality Evaluation**: Analyzes document clarity, completeness, technical depth, and structure
- **Comment Analysis**: Evaluates how authors responded to feedback and incorporated suggestions
- **Engagement Metrics**: Measures team collaboration, comment volume, and discussion depth
- **Artifact Storage**: Saves converted markdown files to an `artifacts` folder for reference

## Setup

### 1. Install Dependencies

```bash
uv sync
```

### 2. Google Drive API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Google Drive API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click "Enable"
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as the application type
   - Download the credentials JSON file
5. Place credentials file:
   ```bash
   mkdir -p ~/.config/gdocs-analysis
   cp /path/to/downloaded/credentials.json ~/.config/gdocs-analysis/credentials.json
   ```

### 3. Configuration

**Using Centralized Config (Recommended):**

Add `drive_folder_ids` and `document_types` to your centralized `config.json`:

```json
{
  "organization": "EvolutionIQ",
  "drive_folder_ids": [
    "1a2b3c4d5e6f7g8h9i0j",
    "9z8y7x6w5v4u3t2s1r0q"
  ],
  "document_types": [
    "Technical Design Doc",
    "TDD",
    "Design Document",
    "Architecture Review"
  ],
  "users": [
    {
      "username": "user",
      "email": "user@example.com",  # Same email used for JIRA
      "name": "User Name"
    }
  ]
}
```

**Note:** The `email` field in your user config is the same email you use for JIRA. During Google Drive OAuth authentication, make sure to log in with the same Google account as this email.

**Finding Folder IDs:**
- Open the Google Drive folder in your browser
- The folder ID is in the URL: `https://drive.google.com/drive/folders/FOLDER_ID_HERE`

## Usage

### Basic Usage

```bash
# Using slugified name and period
gdocs-analyze -n varun-sundar -p 2025H2

# Using username and dates
gdocs-analyze -u user@example.com -s 2025-07-01 -e 2025-12-31

# Specify output directory
gdocs-analyze -n varun-sundar -p 2025H2 -o reports/custom/path
```

### Period Formats

- `2025H1` - First half (Jan 1 - Jun 30)
- `2025H2` - Second half (Jul 1 - Dec 31)
- `2025Q1` - Q1 (Jan 1 - Mar 31)
- `2025Q2` - Q2 (Apr 1 - Jun 30)
- `2025Q3` - Q3 (Jul 1 - Sep 30)
- `2025Q4` - Q4 (Oct 1 - Dec 31)
- `2025` - Full year (Jan 1 - Dec 31)

### Environment Variables

Set these in your `.env` file or environment:

```bash
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-east4
```

## Output

The analysis generates:

1. **Report**: `reports/<name>/<period>/gdocs-analysis.md`
   - Comprehensive analysis of document quality
   - Comment response evaluation
   - Team engagement metrics
   - Recommendations for improvement

2. **Artifacts**: `reports/<name>/<period>/artifacts/`
   - Markdown versions of all analyzed documents
   - Useful for reference and further analysis

## Evaluation Criteria

### Document Quality
- **Clarity**: How easy is the document to understand?
- **Completeness**: Does it cover all necessary aspects?
- **Technical Depth**: Does it demonstrate deep understanding?
- **Structure**: Is it well-organized and logical?

### Comment Responses
- **Response Rate**: How many comments received responses?
- **Response Quality**: Were responses thoughtful and helpful?
- **Feedback Incorporation**: Were suggestions incorporated?
- **Clarification**: Did authors provide additional context?

### Team Engagement
- **Comment Volume**: How many comments were made?
- **Discussion Depth**: How substantive were the discussions?
- **Collaboration**: Did multiple team members engage?
- **Review Quality**: Were comments constructive?

## Troubleshooting

### Authentication Issues

If you see authentication errors:
1. Check that `credentials.json` is in `~/.config/gdocs-analysis/`
2. Delete `~/.config/gdocs-analysis/token.json` and re-authenticate
3. Ensure Google Drive API is enabled in your Google Cloud project

### No Documents Found

- Verify folder IDs are correct
- Check that documents match the `document_types` in config
- Ensure documents were created/modified within the date range
- Verify you have read access to the folders

### Conversion Errors

If markdown conversion fails:
- Check that documents are accessible (not private/restricted)
- Ensure `markitdown[all]` is installed
- Some complex documents may not convert perfectly

## Example

```bash
# Analyze Varun Sundar's design docs for H2 2025
gdocs-analyze -n varun-sundar -p 2025H2

# Output:
# - reports/varun-sundar/2025H2/gdocs-analysis.md
# - reports/varun-sundar/2025H2/artifacts/*.md
```

## Integration with Other Analysis Tools

This tool complements:
- **JIRA Analysis** (`jira-analyze`): Sprint and epic tracking
- **PR Review Analysis** (`gh-analyze`): Code review quality

Together, these provide a comprehensive view of engineering performance across documentation, planning, and code review.
