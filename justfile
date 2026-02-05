# Justfile for common tasks

# Check GitHub authentication (GITHUB_TOKEN, GOOGLE_CLOUD_PROJECT)
_check_gh_auth:
    @echo "🔍 Checking GitHub analysis authentication..."
    @if [ -z "$$GITHUB_TOKEN" ]; then \
        echo "❌ GITHUB_TOKEN not set"; \
        echo "   Get token from: https://github.com/settings/tokens"; \
        echo "   Required scopes: public_repo or repo"; \
        echo "   Add to .env file or export: export GITHUB_TOKEN=your_token"; \
        exit 1; \
    fi
    @if [ -z "$$GOOGLE_CLOUD_PROJECT" ]; then \
        echo "❌ GOOGLE_CLOUD_PROJECT not set"; \
        echo "   Set your Google Cloud project ID"; \
        echo "   Add to .env file or export: export GOOGLE_CLOUD_PROJECT=your-project-id"; \
        exit 1; \
    fi
    @echo "✓ Authentication check passed"

# Check JIRA authentication (JIRA_TOKEN, EVOLUTIONIQ_EMAIL, JIRA_URL, JIRA_PROJECT, GOOGLE_CLOUD_PROJECT)
_check_jira_auth:
    @echo "🔍 Checking JIRA analysis authentication..."
    @if [ -z "$$JIRA_TOKEN" ]; then \
        echo "❌ JIRA_TOKEN not set"; \
        echo "   Get token from: https://id.atlassian.com/manage-profile/security/api-tokens"; \
        echo "   Add to .env file or export: export JIRA_TOKEN=your_token"; \
        exit 1; \
    fi
    @if [ -z "$$EVOLUTIONIQ_EMAIL" ]; then \
        echo "❌ EVOLUTIONIQ_EMAIL not set"; \
        echo "   Set your EvolutionIQ email address (same email used for JIRA and Google account)"; \
        echo "   Add to .env file or export: export EVOLUTIONIQ_EMAIL=your_email@evolutioniq.com"; \
        exit 1; \
    fi
    @if [ -z "$$JIRA_URL" ]; then \
        echo "❌ JIRA_URL not set"; \
        echo "   Set your JIRA instance URL (e.g., https://yourcompany.atlassian.net)"; \
        echo "   Add to .env file or export: export JIRA_URL=https://yourcompany.atlassian.net"; \
        exit 1; \
    fi
    @if [ -z "$$JIRA_PROJECT" ]; then \
        echo "❌ JIRA_PROJECT not set"; \
        echo "   Set your JIRA project key (e.g., WC, PROJ)"; \
        echo "   Add to .env file or export: export JIRA_PROJECT=WC"; \
        exit 1; \
    fi
    @if [ -z "$$GOOGLE_CLOUD_PROJECT" ]; then \
        echo "❌ GOOGLE_CLOUD_PROJECT not set"; \
        echo "   Set your Google Cloud project ID"; \
        echo "   Add to .env file or export: export GOOGLE_CLOUD_PROJECT=your-project-id"; \
        exit 1; \
    fi
    @echo "✓ Authentication check passed"

# Check Google Docs authentication (GOOGLE_CLOUD_PROJECT, Google Drive token)
_check_gdocs_auth:
    @echo "🔍 Checking Google Docs analysis authentication..."
    @if [ -z "$$GOOGLE_CLOUD_PROJECT" ]; then \
        echo "❌ GOOGLE_CLOUD_PROJECT not set"; \
        echo "   Set your Google Cloud project ID"; \
        echo "   Add to .env file or export: export GOOGLE_CLOUD_PROJECT=your-project-id"; \
        exit 1; \
    fi
    @TOKEN_FILE="$$HOME/.config/gdocs-analysis/token.json"; \
    if [ ! -f "$$TOKEN_FILE" ]; then \
        echo "⚠️  Google Drive token not found: $$TOKEN_FILE"; \
        echo "   The workflow will attempt to generate it using Secret Manager"; \
        echo "   If that fails, run 'just auth' to generate the token first"; \
    else \
        echo "✓ Google Drive token found"; \
    fi
    @echo "✓ Authentication check passed"

# Run PR review analysis - passes all arguments through to gh-analyze
# 
# Usage examples:
#   just gh-analyze -n varun-sundar -p 2025H2            # RECOMMENDED: Slugified name, second half
#   just gh-analyze -n ariel-ledesma -p 2025H1            # First half of 2025
#   just gh-analyze -n erin-friesen -p 2026Q1             # First quarter of 2026
#   just gh-analyze -n varun-sundar -p 2025               # Full year 2025
#   just gh-analyze -n "Varun Sundar" -p 2025H2           # Alternative: Full name (quotes needed)
#   just gh-analyze -u varunsundar -p 2025H2              # Use -u for GitHub usernames
# 
# IMPORTANT: 
#   - Always use slugified names (e.g., varun-sundar) instead of full names.
#   - Periods: YYYYH1, YYYYH2, YYYYQ1-Q4, or YYYY (e.g., 2025H2, 2026Q1, 2025)
gh-analyze *args:
    #!/usr/bin/env bash
    set -e
    # Load .env file if it exists
    if [ -f .env ]; then set -a; source .env; set +a; fi
    # Check authentication
    just _check_gh_auth
    # Use uv run to ensure dependencies are available
    uv run ./scripts/gh-analyze {{args}}

# Run JIRA sprint & epic analysis - passes all arguments through to jira-analyze
# 
# Usage examples:
#   just jira-analyze -n varun-sundar -p 2025H2            # RECOMMENDED: Slugified name, second half
#   just jira-analyze -n ariel-ledesma -p 2025H1           # First half of 2025
#   just jira-analyze -n erin-friesen -p 2026Q1             # First quarter of 2026
#   just jira-analyze -n varun-sundar -p 2025               # Full year 2025
#   just jira-analyze -n "Varun Sundar" -p 2025H2           # Alternative: Full name (quotes needed)
#   just jira-analyze -u varunsundar -p 2025H2              # Use -u for JIRA usernames/account IDs
# 
# IMPORTANT: 
#   - Always use slugified names (e.g., varun-sundar) instead of full names.
#   - Periods: YYYYH1, YYYYH2, YYYYQ1-Q4, or YYYY (e.g., 2025H2, 2026Q1, 2025)
#   - Requires JIRA_TOKEN, EVOLUTIONIQ_EMAIL, and JIRA_URL environment variables
jira-analyze *args:
    #!/usr/bin/env bash
    set -e
    # Load .env file if it exists
    if [ -f .env ]; then set -a; source .env; set +a; fi
    # Check authentication
    just _check_jira_auth
    # Use uv run to ensure dependencies are available
    uv run ./scripts/jira-analyze {{args}}

# Run Google Docs analysis - passes all arguments through to gdocs-analyze
# 
# Usage examples:
#   just gdocs-analyze -n varun-sundar -p 2025H2            # RECOMMENDED: Slugified name, second half
#   just gdocs-analyze -n ariel-ledesma -p 2025H1           # First half of 2025
#   just gdocs-analyze -n erin-friesen -p 2026Q1             # First quarter of 2026
#   just gdocs-analyze -n varun-sundar -p 2025               # Full year 2025
# 
# IMPORTANT: 
#   - Always use slugified names (e.g., varun-sundar) instead of full names.
#   - Periods: YYYYH1, YYYYH2, YYYYQ1-Q4, or YYYY (e.g., 2025H2, 2026Q1, 2025)
#   - Requires Google Drive API setup (see eiq/gdocs-analysis/README.md)
gdocs-analyze *args:
    #!/usr/bin/env bash
    set -e
    # Load .env file if it exists
    if [ -f .env ]; then set -a; source .env; set +a; fi
    # Check authentication
    just _check_gdocs_auth
    # Use uv run to ensure dependencies are available
    uv run ./scripts/gdocs-analyze {{args}}

# Authenticate with Google Cloud for Vertex AI access
auth:
    #!/usr/bin/env bash
    set -e
    # Load .env file if it exists
    if [ -f .env ]; then set -a; source .env; set +a; fi
    
    echo "🔐 Setting up Google Cloud authentication..."
    echo ""
    
    if ! command -v gcloud > /dev/null 2>&1; then
        echo "❌ gcloud CLI not found"
        echo "   Install from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    echo "✓ gcloud CLI found"
    echo ""
    echo "Running: gcloud auth application-default login"
    echo "This will open a browser for authentication..."
    gcloud auth application-default login
    echo ""
    echo "✓ Authentication complete!"
    echo ""
    echo "Verifying authentication..."
    if gcloud auth application-default print-access-token > /dev/null 2>&1; then
        echo "✓ Application Default Credentials are set"
    else
        echo "⚠️  Warning: Could not verify credentials"
    fi
    echo ""
    if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
        echo "⚠️  GOOGLE_CLOUD_PROJECT not set"
        echo "   Set it with: export GOOGLE_CLOUD_PROJECT=your-project-id"
        echo "   Or add to .env file: GOOGLE_CLOUD_PROJECT=eiq-development"
    else
        echo "✓ GOOGLE_CLOUD_PROJECT is set: $GOOGLE_CLOUD_PROJECT"
        echo ""
        echo "Checking if Vertex AI API is enabled..."
        if gcloud services list --enabled --filter="name:aiplatform.googleapis.com" --format="value(name)" | grep -q aiplatform; then
            echo "✓ Vertex AI API is enabled"
        else
            echo "⚠️  Vertex AI API may not be enabled"
            echo "   Enable it with: gcloud services enable aiplatform.googleapis.com"
        fi
    fi
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📁 Setting up Google Drive authentication..."
    echo ""
    TOKEN_FILE="$HOME/.config/gdocs-analysis/token.json"
    
    if [ -f "$TOKEN_FILE" ]; then
        echo "✓ Google Drive token file exists: $TOKEN_FILE"
        echo ""
        echo "   To refresh your Google Drive authentication, delete the token file:"
        echo "   rm $TOKEN_FILE"
        echo "   Then run 'just auth' again to regenerate"
    else
        echo "ℹ️  Google Drive token file not found"
        echo ""
        echo "   Generating Google Drive token using Secret Manager..."
        echo "   ⚠️  IMPORTANT: If you're on a remote server, start an SSH tunnel with port 8989 forwarded!"
        echo ""
        
        # Try to generate token using Secret Manager
        # Use uv run to ensure we're using the project's virtual environment
        if uv run python -c "from google.cloud import secretmanager" 2>/dev/null; then
            uv run python scripts/generate-drive-token.py
            if [ -f "$TOKEN_FILE" ]; then
                echo ""
                echo "✓ Google Drive token generated successfully!"
            else
                echo ""
                echo "⚠️  Token generation may have failed or was cancelled"
                echo "   You can try again by running: just auth"
            fi
        else
            echo "⚠️  Secret Manager dependency not available"
            echo "   Installing dependencies..."
            uv sync
            echo ""
            echo "   Retrying token generation..."
            if uv run python scripts/generate-drive-token.py; then
                if [ -f "$TOKEN_FILE" ]; then
                    echo ""
                    echo "✓ Google Drive token generated successfully!"
                fi
            else
                echo ""
                echo "⚠️  Token generation failed"
                echo "   You can manually set up credentials.json (see eiq/gdocs-analysis/README.md)"
            fi
        fi
    fi
    
    echo ""
    echo "Checking if Google Drive API is enabled..."
    if [ -n "$GOOGLE_CLOUD_PROJECT" ]; then
        if gcloud services list --enabled --filter="name:drive.googleapis.com" --format="value(name)" | grep -q drive; then
            echo "✓ Google Drive API is enabled"
        else
            echo "⚠️  Google Drive API may not be enabled"
            echo "   Enable it with: gcloud services enable drive.googleapis.com --project=$GOOGLE_CLOUD_PROJECT"
        fi
    else
        echo "⚠️  Cannot check API status (GOOGLE_CLOUD_PROJECT not set)"
    fi
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Authentication setup complete!"

# Generate Google Drive OAuth token using Secret Manager
generate-drive-token:
    #!/usr/bin/env bash
    set -e
    # Load .env file if it exists
    if [ -f .env ]; then set -a; source .env; set +a; fi
    
    echo "🔐 Generating Google Drive OAuth token..."
    echo ""
    echo "This script uses Secret Manager to get OAuth credentials from GCP."
    echo "Make sure you have Application Default Credentials set up (run 'just auth' first)."
    echo ""
    echo "⚠️  IMPORTANT: Start an SSH tunnel with port 8989 forwarded before running this!"
    echo ""
    uv run python scripts/generate-drive-token.py

# Setup: Install dependencies and verify configuration
setup:
    @echo "Setting up Engineering Performance Analysis Tools..."
    @echo ""
    @echo "1. Installing dependencies (including test dependencies)..."
    @uv sync --extra dev || echo "⚠️  uv sync failed - you may need to install dependencies manually"
    @echo ""
    @echo "2. Setting up .env file..."
    @if [ -f ".env" ]; then \
        echo "✓ .env file already exists"; \
    else \
        if [ -f ".env.example" ]; then \
            cp .env.example .env; \
            echo "✓ Created .env from .env.example"; \
            echo "   ⚠️  Please edit .env and fill in your values:"; \
            echo "      - GITHUB_TOKEN (for gh-analyze)"; \
            echo "      - JIRA_TOKEN, JIRA_URL, JIRA_PROJECT (for jira-analyze)"; \
            echo "      - EVOLUTIONIQ_EMAIL (shared for JIRA and Google Docs)"; \
            echo "      - GOOGLE_CLOUD_PROJECT (for all tools)"; \
        else \
            echo "⚠️  .env.example not found"; \
        fi; \
    fi
    @echo ""
    @echo "3. Checking environment variables..."
    @if [ -z "$$GITHUB_TOKEN" ]; then \
        echo "⚠️  GITHUB_TOKEN not set"; \
        echo "   Get token from: https://github.com/settings/tokens"; \
        echo "   Required scopes: public_repo or repo"; \
        echo "   Add to .env file or export: export GITHUB_TOKEN=your_token"; \
    else \
        echo "✓ GITHUB_TOKEN is set"; \
    fi
    @if [ -z "$$GOOGLE_CLOUD_PROJECT" ]; then \
        echo "⚠️  GOOGLE_CLOUD_PROJECT not set"; \
        echo "   Set your Google Cloud project ID"; \
        echo "   Add to .env file or export: export GOOGLE_CLOUD_PROJECT=your-project-id"; \
    else \
        echo "✓ GOOGLE_CLOUD_PROJECT is set: $$GOOGLE_CLOUD_PROJECT"; \
    fi
    @if [ -z "$$GOOGLE_CLOUD_LOCATION" ]; then \
        echo "ℹ️  GOOGLE_CLOUD_LOCATION not set (will default to us-east4)"; \
    else \
        echo "✓ GOOGLE_CLOUD_LOCATION is set: $$GOOGLE_CLOUD_LOCATION"; \
    fi
    @echo ""
    @echo "4. Checking template files..."
    @if [ -f "eiq/gh-analysis/templates/gh-analysis.jinja2.md" ]; then \
        echo "✓ GitHub analysis template exists"; \
    else \
        echo "❌ Template file not found"; \
    fi
    @echo ""
    @echo "5. Checking centralized config..."
    @if [ -f "config.json" ]; then \
        echo "✓ config.json exists"; \
    else \
        echo "⚠️  config.json not found (will be created automatically)"; \
    fi
    @echo ""
    @echo "6. Checking Google Cloud authentication..."
    @if command -v gcloud > /dev/null 2>&1; then \
        if gcloud auth application-default print-access-token > /dev/null 2>&1; then \
            echo "✓ Google Cloud authentication is set up"; \
        else \
            echo "⚠️  Google Cloud authentication not set up"; \
            echo "   Run: just auth"; \
        fi; \
    else \
        echo "⚠️  gcloud CLI not found"; \
        echo "   Install from: https://cloud.google.com/sdk/docs/install"; \
        echo "   Then run: just auth"; \
    fi
    @echo ""
    @echo "7. Installing pre-commit hooks..."
    @if command -v pre-commit > /dev/null 2>&1; then \
        pre-commit install || echo "⚠️  pre-commit install failed"; \
        echo "✓ Pre-commit hooks installed"; \
    else \
        echo "⚠️  pre-commit not found - installing..."; \
        uv run pre-commit install || echo "⚠️  Failed to install pre-commit hooks"; \
    fi
    @echo ""
    @echo "Setup complete!"
    @echo ""
    @echo "Next steps:"
    @echo "  1. Add users: just add-report"
    @echo "  2. If not authenticated: just auth"
    @echo "  3. Run analysis:"
    @echo "     - GitHub: just gh-analyze -n <name> -p <period>"
    @echo "     - JIRA: just jira-analyze -n <name> -p <period>"
    @echo "     - Google Docs: just gdocs-analyze -n <name> -p <period>"
    @echo "  4. Run tests: just test"
    @echo "  5. Format code: just format"

# Run tests
test:
    @echo "🧪 Running tests..."
    @uv run pytest

# Format code with ruff
format:
    @echo "✨ Formatting code with ruff..."
    @uv run ruff format .
    @uv run ruff check --fix .

# Add a new user to config.json and create report folder structure
add-report:
    @echo "📝 Adding new user to config.json..."
    @uv run python scripts/add-report

# Clean analysis reports for a specified period
clean PERIOD:
    @echo "🧹 Cleaning analysis reports for period {{PERIOD}}..."
    @uv run python scripts/clean-reports {{PERIOD}}

# Run all analyses for all users in parallel
analyze-all PERIOD:
    @echo "🚀 Running all analyses for period {{PERIOD}}..."
    @uv run python scripts/analyze-all {{PERIOD}}
    @echo ""
    @echo "🔍 Calibrating reports for fairness..."
    @uv run python scripts/calibrate-reports {{PERIOD}}
    @echo ""
    @echo "📦 Generating review packages..."
    @uv run python scripts/generate-review-package {{PERIOD}}
    @echo ""
    @echo "✅ Complete! Review packages available in reports/*/{{PERIOD}}/review-package.md"

# Calibrate existing reports for a period
calibrate PERIOD:
    @echo "🔍 Calibrating reports for period {{PERIOD}}..."
    @uv run python scripts/calibrate-reports {{PERIOD}}

# Generate review packages for a period
review-package PERIOD:
    @echo "📦 Generating review packages for period {{PERIOD}}..."
    @uv run python scripts/generate-review-package {{PERIOD}}

# Convert PDF files to markdown
convert-pdfs:
    @echo "📄 Converting PDF files to markdown..."
    @uv run python scripts/convert-pdfs

# Convert PDF files in a specific path
convert-pdfs-path PATH:
    @echo "📄 Converting PDF files in {{PATH}}..."
    @uv run python scripts/convert-pdfs --path {{PATH}}

# Note: validate.py and fetch scripts have been removed
# Use gh-analyze for all analysis tasks
