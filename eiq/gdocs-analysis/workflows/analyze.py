"""
LangGraph workflow for Google Docs technical design document analysis using Vertex AI.

This workflow:
1. Lists all Google Docs in user's Drive within a date range (or from specified folders if configured)
2. Converts documents to markdown and saves to artifacts folder
3. Analyzes document quality, comment responses, and team engagement
4. Generates analysis using Vertex AI with a standardized template
5. Outputs formatted markdown report
"""

import json
import os
import re
import warnings
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypedDict

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # python-dotenv not installed, skip loading .env
    pass

# Suppress Google Cloud authentication warnings
warnings.filterwarnings(
    "ignore", message=".*quota project.*", category=UserWarning, module="google.auth"
)

from jinja2 import Template  # noqa: E402
from langchain_core.messages import HumanMessage, SystemMessage  # noqa: E402
from langgraph.graph import END, StateGraph  # noqa: E402
from markitdown import MarkItDown  # noqa: E402

# Import ladder utilities for level-based evaluation
try:
    from eiq.shared.ai_utils import get_vertex_ai_llm
    from eiq.shared.ladder_utils import format_level_criteria_for_prompt
except ImportError:
    # Fallback if ladder utils not available
    def format_level_criteria_for_prompt(
        level: str, ladder_file: Path | None = None, include_next_level: bool = True
    ) -> str:
        return ""


# Try to import rich for better progress display, fallback to simple prints
try:
    from rich.console import Console
    from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None  # type: ignore[assignment]
    Progress = None  # type: ignore[assignment]
    SpinnerColumn = None  # type: ignore[assignment]
    TextColumn = None  # type: ignore[assignment]
    BarColumn = None  # type: ignore[assignment]
    TimeElapsedColumn = None  # type: ignore[assignment]

# Vertex AI is now handled via shared ai_utils.get_vertex_ai_llm()
# Set Vertex AI mode before importing shared utilities
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "true")

# Google Drive API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaIoBaseDownload

    GOOGLE_APIS_AVAILABLE = True
except ImportError:
    GOOGLE_APIS_AVAILABLE = False

# Secret Manager availability check (optional, for OAuth credentials)
# We'll try importing it when needed, so just check if the package exists
try:
    import importlib

    importlib.import_module("google.cloud.secretmanager")
    SECRET_MANAGER_AVAILABLE = True
except ImportError:
    SECRET_MANAGER_AVAILABLE = False

# Constants
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
TEMPLATE_PATH = TEMPLATE_DIR / "gdocs-analysis.jinja2.md"
PROMPT_TEMPLATE_PATH = TEMPLATE_DIR / "prompt.jinja2.md"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


class AnalysisState(TypedDict):
    """State for the Google Docs analysis workflow."""

    # Input
    username: str | None
    name: str | None
    level: str | None  # Engineer level (e.g., "L4", "L5") for evaluation criteria
    start_date: str
    end_date: str
    analysis_period: str
    config_path: str
    output_dir: str | None
    period: str | None  # Period key for centralized config lookup

    # Google Drive API (no fields needed - searches all Drive automatically)

    # Vertex AI
    vertexai_project: str
    vertexai_location: str

    # Data
    documents: list[dict]
    artifacts_dir: str | None
    analysis_results: dict[str, Any]

    # Output
    markdown_report: str
    error: str | None


def _parse_period(period_str: str) -> tuple[str, str]:
    """
    Parse period string to start and end dates.

    Supports:
    - H1/H2: Half-year (e.g., '2025H1' = Jan 1 - Jun 30, '2025H2' = Jul 1 - Dec 31)
    - Q1-Q4: Quarter (e.g., '2025Q1' = Jan 1 - Mar 31, '2025Q2' = Apr 1 - Jun 30)
    - Year: Full year (e.g., '2025' = Jan 1 - Dec 31)

    Returns:
        Tuple of (start_date, end_date) in YYYY-MM-DD format
    """
    period_str = period_str.strip().upper()

    # Half-year pattern: YYYYH1 or YYYYH2
    half_match = re.match(r"^(\d{4})H([12])$", period_str)
    if half_match:
        year = int(half_match.group(1))
        half = half_match.group(2)
        if half == "1":
            return (f"{year}-01-01", f"{year}-06-30")
        else:  # H2
            return (f"{year}-07-01", f"{year}-12-31")

    # Quarter pattern: YYYYQ1, YYYYQ2, YYYYQ3, YYYYQ4
    quarter_match = re.match(r"^(\d{4})Q([1-4])$", period_str)
    if quarter_match:
        year = int(quarter_match.group(1))
        quarter = int(quarter_match.group(2))
        quarter_dates = {
            1: (f"{year}-01-01", f"{year}-03-31"),
            2: (f"{year}-04-01", f"{year}-06-30"),
            3: (f"{year}-07-01", f"{year}-09-30"),
            4: (f"{year}-10-01", f"{year}-12-31"),
        }
        return quarter_dates[quarter]

    # Full year pattern: YYYY
    year_match = re.match(r"^(\d{4})$", period_str)
    if year_match:
        year = int(year_match.group(1))
        return (f"{year}-01-01", f"{year}-12-31")

    raise ValueError(
        f"Invalid period format: {period_str}. "
        "Use format: YYYYH1, YYYYH2, YYYYQ1-Q4, or YYYY (e.g., '2025H2', '2026Q1', '2025')"
    )


def _format_analysis_period(start_date: str, end_date: str) -> str:
    """Generate analysis_period string from dates."""
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    # Full year
    period_patterns = {
        (1, 1, 12, 31): f"{start_dt.year} (January 1 - December 31, {start_dt.year})",
        (7, 1, 12, 31): f"{start_dt.year}H2 (July 1 - December 31, {start_dt.year})",
        (1, 1, 6, 30): f"{start_dt.year}H1 (January 1 - June 30, {start_dt.year})",
        (1, 1, 3, 31): f"{start_dt.year}Q1 (January 1 - March 31, {start_dt.year})",
        (4, 1, 6, 30): f"{start_dt.year}Q2 (April 1 - June 30, {start_dt.year})",
        (7, 1, 9, 30): f"{start_dt.year}Q3 (July 1 - September 30, {start_dt.year})",
        (10, 1, 12, 31): f"{start_dt.year}Q4 (October 1 - December 31, {start_dt.year})",
    }
    pattern_key = (start_dt.month, start_dt.day, end_dt.month, end_dt.day)
    return period_patterns.get(pattern_key, f"{start_date} to {end_date}")


def _get_google_drive_service(expected_email: str | None = None):
    """Get authenticated Google Drive service.

    Args:
        expected_email: Email from config (for verification/reminder during OAuth)
    """
    if not GOOGLE_APIS_AVAILABLE:
        raise ImportError(
            "Google APIs not available. Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
        )

    creds = None
    token_file = Path.home() / ".config" / "gdocs-analysis" / "token.json"
    credentials_file = Path.home() / ".config" / "gdocs-analysis" / "credentials.json"

    # Load existing token
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

    # If no valid credentials, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Try to get credentials from Secret Manager if credentials.json doesn't exist
            credentials_data = None
            if not credentials_file.exists() and SECRET_MANAGER_AVAILABLE:
                try:
                    import os
                    import tempfile

                    from google.cloud import secretmanager

                    gcp_project = os.getenv("GOOGLE_CLOUD_PROJECT", "eiq-development")
                    secret_id = "google_drive_oauth_json"
                    secret_name = f"projects/{gcp_project}/secrets/{secret_id}/versions/latest"

                    client = secretmanager.SecretManagerServiceClient()
                    response = client.access_secret_version(request={"name": secret_name})
                    credentials_data = response.payload.data.decode("UTF-8")
                except Exception:
                    # If Secret Manager fails, fall back to credentials.json requirement
                    pass

            if credentials_data:
                # Use credentials from Secret Manager
                import tempfile

                with tempfile.NamedTemporaryFile(
                    mode="w+t", encoding="utf-8", suffix=".json", delete=False
                ) as temp_file:
                    temp_file.write(credentials_data)
                    temp_file.flush()
                    temp_credentials_path = temp_file.name

                try:
                    if expected_email:
                        print(f"\n⚠️  Please authenticate with Google account: {expected_email}")
                        print("   (This should be the same email you use for JIRA)\n")
                    flow = InstalledAppFlow.from_client_secrets_file(temp_credentials_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                finally:
                    os.unlink(temp_credentials_path)
            else:
                # Fall back to credentials.json file
                if not credentials_file.exists():
                    raise FileNotFoundError(
                        f"Credentials file not found: {credentials_file}\n"
                        "Please either:\n"
                        "  1. Download credentials.json from Google Cloud Console and place it in ~/.config/gdocs-analysis/\n"
                        "  2. Or run 'just generate-drive-token' to use Secret Manager"
                    )
                if expected_email:
                    print(f"\n⚠️  Please authenticate with Google account: {expected_email}")
                    print("   (This should be the same email you use for JIRA)\n")
                flow = InstalledAppFlow.from_client_secrets_file(str(credentials_file), SCOPES)
                creds = flow.run_local_server(port=0)

        # Save credentials for next run
        token_file.parent.mkdir(parents=True, exist_ok=True)
        with open(token_file, "w") as token:
            token.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


def _list_all_documents(
    service: Any, start_date: str, end_date: str, user_email: str | None = None
) -> list[dict]:
    """List all Google Docs in user's Drive within date range, filtered by owner."""
    documents = []

    start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=UTC)
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=UTC)
    end_dt = end_dt.replace(hour=23, minute=59, second=59)

    try:
        # Query for all Google Docs (not trashed)
        # Note: Google Drive API query doesn't support filtering by owner email directly,
        # so we'll filter in Python after fetching
        query = "mimeType='application/vnd.google-apps.document' and trashed=false"
        page_token = None
        all_items = []

        # Paginate through all results
        while True:
            results = (
                service.files()
                .list(
                    q=query,
                    fields="nextPageToken, files(id, name, createdTime, modifiedTime, webViewLink, owners(emailAddress, displayName))",
                    orderBy="modifiedTime desc",
                    pageToken=page_token,
                    pageSize=1000,  # Max page size
                )
                .execute()
            )

            items = results.get("files", [])
            all_items.extend(items)

            page_token = results.get("nextPageToken")
            if not page_token:
                break

        # Filter by date range and verify ownership
        for item in all_items:
            created_time = datetime.fromisoformat(item["createdTime"].replace("Z", "+00:00"))

            # Include only if created in date range (not just modified)
            if not (start_dt <= created_time <= end_dt):
                continue

            # Filter by ownership - only include documents where user is an owner
            owners = item.get("owners", [])
            owner_emails = [
                owner.get("emailAddress", "") for owner in owners if owner.get("emailAddress")
            ]

            # If user_email is specified, only include if user is an owner
            if user_email:
                user_email_lower = user_email.lower()
                if not any(user_email_lower == email.lower() for email in owner_emails):
                    continue

            documents.append(
                {
                    "id": item["id"],
                    "name": item["name"],
                    "created_time": item["createdTime"],
                    "modified_time": item["modifiedTime"],
                    "url": item["webViewLink"],
                    "owners": [owner.get("displayName", "") for owner in owners],
                }
            )

    except HttpError as error:
        print(f"An error occurred listing documents: {error}")
        return []

    return documents


def load_config(state: AnalysisState) -> AnalysisState:
    """Load user configuration from config.json or centralized config.json."""
    config_path = Path(state["config_path"])

    # Check if it's a centralized config (config.json) with username parameter
    if config_path.name == "config.json" and state.get("username"):
        # Load centralized config and find user
        if not config_path.exists():
            state["error"] = f"Centralized config file not found: {config_path}"
            return state

        with open(config_path) as f:
            centralized_config = json.load(f)

        # Find user in the list
        username = state["username"]
        user_config = None
        for user in centralized_config.get("users", []):
            if (
                user.get("username") == username
                or user.get("email") == username
                or (username and user.get("name", "").lower() == username.lower())
            ):
                user_config = user
                break

        if not user_config:
            state["error"] = f"User '{username}' not found in centralized config"
            return state

        # Use user config directly
        config = user_config.copy()

        # Resolve period reference from state (passed from CLI)
        if "period" in state and state["period"]:
            period_key = state["period"]
            try:
                # Parse period string directly (e.g., 2025H2, 2026Q1, 2025)
                start_date, end_date = _parse_period(period_key)
                config["start_date"] = start_date
                config["end_date"] = end_date
            except ValueError as e:
                state["error"] = str(e)
                return state
    else:
        # Load individual config file
        if not config_path.exists():
            state["error"] = f"Config file not found: {config_path}"
            return state

        with open(config_path) as f:
            config = json.load(f)

    # Use email from config (same as JIRA email) - this is what user should authenticate with
    state["username"] = config.get("email") or config.get("username", state.get("username"))
    state["name"] = config.get("name", state.get("name"))
    state["start_date"] = config.get("start_date", state.get("start_date", "2025-07-01"))
    state["end_date"] = config.get("end_date", state.get("end_date", "2025-12-31"))
    state["analysis_period"] = _format_analysis_period(state["start_date"], state["end_date"])
    state["level"] = config.get("level")  # Store level for evaluation criteria

    return state


def fetch_gdocs_data(state: AnalysisState) -> AnalysisState:
    """Fetch Google Docs from user's Drive and convert to markdown."""
    if state.get("error"):
        return state

    start_date = state["start_date"]
    end_date = state["end_date"]
    output_dir_str = state.get("output_dir") or "reports"
    output_dir = Path(output_dir_str)

    if RICH_AVAILABLE:
        console = Console()
        console.print("🔍 [cyan]Fetching Google Docs...[/cyan]")
    else:
        print("🔍 Fetching Google Docs...")

    # Get expected email from config for OAuth reminder
    expected_email = state.get("username")  # This is now the email from config

    try:
        service = _get_google_drive_service(expected_email=expected_email)
    except Exception as e:
        state["error"] = f"Failed to authenticate with Google Drive: {str(e)}"
        return state

    # Search all Google Docs in user's Drive (owned by the user)
    if RICH_AVAILABLE:
        console.print("  [dim]Searching Google Docs owned by you...[/dim]")
    else:
        print("  Searching Google Docs owned by you...")

    all_documents = _list_all_documents(service, start_date, end_date, user_email=expected_email)

    if RICH_AVAILABLE:
        console.print(f"  [green]Found {len(all_documents)} documents[/green]")
    else:
        print(f"  Found {len(all_documents)} documents")

    if not all_documents:
        state["error"] = f"No Google Docs found for the date range ({start_date} to {end_date})"
        return state

    # Create artifacts directory
    artifacts_dir = output_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    state["artifacts_dir"] = str(artifacts_dir)

    # Convert documents to markdown
    # Try markitdown first, fallback to Drive API export if needed
    md_converter = MarkItDown()

    documents_with_content = []
    if RICH_AVAILABLE:
        console = Console()
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            task = progress.add_task(
                "Converting documents to markdown...", total=len(all_documents)
            )
            for doc in all_documents:
                markdown_content: str | None = None
                try:
                    # Try markitdown first (works for public docs or authenticated sessions)
                    doc_url = f"https://docs.google.com/document/d/{doc['id']}/edit"
                    result = md_converter.convert(doc_url)
                    # Ensure we have a string (markitdown may return DocumentConverterResult)
                    markdown_content = str(result) if result else None
                except Exception:
                    # Fallback: Use Google Drive API export
                    try:
                        request = service.files().export_media(
                            fileId=doc["id"], mimeType="text/plain"
                        )
                        # Download and convert to markdown (basic conversion)
                        import io

                        fh = io.BytesIO()
                        downloader = MediaIoBaseDownload(fh, request)
                        done = False
                        while done is False:
                            _, done = downloader.next_chunk()
                        text_content = fh.getvalue().decode("utf-8")
                        # Basic markdown conversion (preserve structure)
                        markdown_content = text_content
                    except Exception as e:
                        if RICH_AVAILABLE:
                            console.print(
                                f"  [yellow]⚠️  Failed to convert {doc['name']}: {e}[/yellow]"
                            )
                        else:
                            print(f"  ⚠️  Failed to convert {doc['name']}: {e}")
                        progress.update(task, advance=1)
                        continue

                if markdown_content:
                    # Save to artifacts folder
                    safe_name = re.sub(r'[<>:"/\\|?*]', "_", doc["name"])
                    artifact_path = artifacts_dir / f"{safe_name}.md"
                    with open(artifact_path, "w", encoding="utf-8") as f:
                        f.write(str(markdown_content))

                    documents_with_content.append(
                        {
                            **doc,
                            "markdown_path": str(artifact_path),
                            "markdown_preview": str(markdown_content)[
                                :2000
                            ],  # First 2000 chars for analysis
                        }
                    )
                progress.update(task, advance=1)
    else:
        print(f"  Converting {len(all_documents)} documents to markdown...", end="", flush=True)
        for idx, doc in enumerate(all_documents, 1):
            markdown_content: str | None = None
            try:
                # Try markitdown first
                doc_url = f"https://docs.google.com/document/d/{doc['id']}/edit"
                result = md_converter.convert(doc_url)
                # Ensure we have a string (markitdown may return DocumentConverterResult)
                markdown_content = str(result) if result else None
            except Exception:
                # Fallback: Use Google Drive API export
                try:
                    request = service.files().export_media(fileId=doc["id"], mimeType="text/plain")
                    import io

                    fh = io.BytesIO()
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    while done is False:
                        _, done = downloader.next_chunk()
                    text_content = fh.getvalue().decode("utf-8")
                    markdown_content = text_content
                except Exception as e:
                    print(f"\n  ⚠️  Failed to convert {doc['name']}: {e}")
                    if idx % 5 == 0:
                        print(f" {idx}/{len(all_documents)}", end="", flush=True)
                    continue

            if markdown_content:
                # Save to artifacts folder
                safe_name = re.sub(r'[<>:"/\\|?*]', "_", doc["name"])
                artifact_path = artifacts_dir / f"{safe_name}.md"
                with open(artifact_path, "w", encoding="utf-8") as f:
                    f.write(str(markdown_content))

                documents_with_content.append(
                    {
                        **doc,
                        "markdown_path": str(artifact_path),
                        "markdown_preview": str(markdown_content)[
                            :2000
                        ],  # First 2000 chars for analysis
                    }
                )
            if idx % 5 == 0:
                print(f" {idx}/{len(all_documents)}", end="", flush=True)
        print(" ✓")

    state["documents"] = documents_with_content

    if RICH_AVAILABLE:
        console = Console()
        console.print(
            f"✓ [green]Fetched and converted {len(documents_with_content)} documents[/green]"
        )
    else:
        print(f"✓ Fetched and converted {len(documents_with_content)} documents")

    return state


def analyze_with_vertexai(state: AnalysisState) -> AnalysisState:
    """Analyze Google Docs using Vertex AI."""
    if state.get("error"):
        return state

    username = state.get("username", "Unknown")
    name = state.get("name", username)
    analysis_period = state["analysis_period"]
    project = state["vertexai_project"]
    location = state.get("vertexai_location", "us-east4")
    documents = state.get("documents", [])

    if RICH_AVAILABLE:
        console = Console()
        console.print("🤖 [cyan]Analyzing with Vertex AI...[/cyan]")
    else:
        print("🤖 Analyzing with Vertex AI...")

    # Initialize Vertex AI LLM using shared utility (ensures gemini-2.5-pro)
    llm = get_vertex_ai_llm(project, location, temperature=0.3)

    # Load report template
    with open(TEMPLATE_PATH) as f:
        report_template_content = f.read()

    # Load prompt template
    with open(PROMPT_TEMPLATE_PATH) as f:
        prompt_template = Template(f.read())

    # Prepare document summaries for analysis
    document_summaries = []
    for doc in documents:
        document_summaries.append(
            {
                "name": doc["name"],
                "created_time": doc["created_time"],
                "modified_time": doc["modified_time"],
                "url": doc["url"],
                "owners": doc.get("owners", []),
                "preview": doc.get("markdown_preview", ""),
            }
        )

    # Get level criteria if level is specified (include next level for growth areas)
    level = state.get("level")
    level_criteria = ""
    if level:
        ladder_file = Path(__file__).parent.parent.parent.parent / "ladder" / "Matrix.html"
        level_criteria = format_level_criteria_for_prompt(
            level, ladder_file, include_next_level=True
        )

    # Build prompt with template
    ANALYSIS_SYSTEM_PROMPT = """You are an expert at analyzing technical design documents for engineering performance evaluation.

Your task is to evaluate documents rigorously against these core criteria:

1. **Problem Clarity**: Is the problem being addressed clearly defined? Does it explain the "why"?
2. **Concept Clarity**: Is the proposed solution clearly communicated? Does it effectively convey the "what"?
3. **Execution Path**: Is there a clear, actionable plan for implementation?
4. **Architecture Diagrams**: Are diagrams included for architecture changes?

Be critical and realistic. A good design doc must excel in problem clarity, concept clarity, and execution path. Missing diagrams for architecture changes is a significant gap. Documents that don't clearly convey "what" and "why" should be marked down.

Also evaluate:
- Comment response quality: how well authors addressed feedback, incorporated suggestions
- Team engagement: comment volume, discussion depth, collaboration patterns

Be specific, provide examples, and focus on actionable insights for improving technical documentation and design review processes."""

    # Append level criteria if available
    if level_criteria:
        ANALYSIS_SYSTEM_PROMPT += f"\n\n{level_criteria}"

    # Render prompt template with data
    user_prompt = prompt_template.render(
        username=username,
        name=name,
        analysis_period=analysis_period,
        documents_count=len(documents),
        documents_json=json.dumps(document_summaries, indent=2),
        report_template=report_template_content,
    )

    # Generate analysis
    messages = [SystemMessage(content=ANALYSIS_SYSTEM_PROMPT), HumanMessage(content=user_prompt)]

    try:
        response = llm.invoke(messages)
        analysis_markdown = response.content if hasattr(response, "content") else str(response)

        state["analysis_results"] = {"markdown": analysis_markdown}

        if RICH_AVAILABLE:
            console = Console()
            console.print("✓ [green]Analysis complete[/green]")
        else:
            print("✓ Analysis complete")
    except Exception as e:
        state["error"] = f"Vertex AI analysis failed: {str(e)}"
        if RICH_AVAILABLE:
            console = Console()
            console.print(f"❌ [red]{state['error']}[/red]")
        else:
            print(f"❌ {state['error']}")

    return state


def generate_report(state: AnalysisState) -> AnalysisState:
    """Generate final markdown report."""
    if state.get("error"):
        return state

    analysis_markdown = state.get("analysis_results", {}).get("markdown", "")
    documents = state.get("documents", [])
    username = state.get("username", "Unknown")
    name = state.get("name", username)
    analysis_period = state["analysis_period"]

    # If LLM generated complete markdown, use it
    if analysis_markdown and "{{" not in analysis_markdown:
        state["markdown_report"] = analysis_markdown
        return state

    # Fallback: generate basic report
    report_lines = [
        f"# Google Docs Analysis: {name}",
        "",
        f"**Analysis Period**: {analysis_period}",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"- **Documents Analyzed**: {len(documents)}",
        "",
        "## Documents",
        "",
    ]

    for doc in documents:
        report_lines.extend(
            [
                f"### {doc['name']}",
                f"- **Created**: {doc['created_time'][:10]}",
                f"- **Modified**: {doc['modified_time'][:10]}",
                f"- **URL**: {doc['url']}",
                f"- **Artifact**: {doc.get('markdown_path', 'N/A')}",
                "",
            ]
        )

    if analysis_markdown:
        report_lines.extend(["---", "", analysis_markdown])

    state["markdown_report"] = "\n".join(report_lines)

    return state


def save_report(state: AnalysisState) -> AnalysisState:
    """Save markdown report to file."""
    if state.get("error"):
        return state

    output_dir_arg = state.get("output_dir")

    # If output_dir is provided, use it directly
    if output_dir_arg:
        report_dir = Path(output_dir_arg)
    else:
        # Fallback: construct path from name/username and period
        output_dir = Path("reports")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Use name if available, otherwise fallback to username
        name = state.get("name")
        username = state.get("username", "unknown")
        display_name = name or username
        period = state.get("period", "unknown")

        # Slugify name/username for directory
        slugified_name = re.sub(
            r"[^a-z0-9-]", "-", display_name.lower() if display_name else "unknown"
        )
        slugified_name = re.sub(r"-+", "-", slugified_name).strip("-")

        period_str = period if period else "unknown"
        report_dir = output_dir / slugified_name / period_str

    report_dir.mkdir(parents=True, exist_ok=True)

    # Create notes folder for ad-hoc markdown files, self-reviews, and feedback
    notes_dir = report_dir / "notes"
    notes_dir.mkdir(exist_ok=True)

    report_path = report_dir / "gdocs-analysis.md"

    with open(report_path, "w") as f:
        f.write(state["markdown_report"])

    if RICH_AVAILABLE:
        console = Console()
        console.print(f"✓ [green]Report saved to {report_path}[/green]")
    else:
        print(f"✓ Report saved to {report_path}")

    return state


# Build the workflow graph
workflow = StateGraph(AnalysisState)  # type: ignore[type-arg]

# Add nodes
workflow.add_node("load_config", load_config)
workflow.add_node("fetch_gdocs", fetch_gdocs_data)
workflow.add_node("analyze", analyze_with_vertexai)
workflow.add_node("generate", generate_report)
workflow.add_node("save", save_report)

# Add edges
workflow.set_entry_point("load_config")
workflow.add_edge("load_config", "fetch_gdocs")
workflow.add_edge("fetch_gdocs", "analyze")
workflow.add_edge("analyze", "generate")
workflow.add_edge("generate", "save")
workflow.add_edge("save", END)

# Compile the workflow
app = workflow.compile()


def run(
    config_path: str,
    vertexai_project: str | None = None,
    vertexai_location: str | None = None,
    username: str | None = None,
    period: str | None = None,
    output_dir: str | None = None,
):
    """
    Run the Google Docs analysis workflow.

    Args:
        config_path: Path to user config.json file or centralized config.json
        vertexai_project: Google Cloud project ID (or set GOOGLE_CLOUD_PROJECT env var)
        vertexai_location: Vertex AI location (or set GOOGLE_CLOUD_LOCATION env var)
        username: Username to use when config_path points to centralized config.json
        period: Period key (e.g., "2025H2") to use when config_path points to centralized config.json
        output_dir: Output directory for the report (defaults to reports/<username>/<period>)
    """
    initial_state: AnalysisState = {
        "config_path": config_path,
        "username": username,
        "name": None,
        "level": None,  # Will be loaded from config
        "start_date": "",
        "end_date": "",
        "analysis_period": "",
        "output_dir": output_dir,
        "period": period,
        "vertexai_project": vertexai_project or os.getenv("GOOGLE_CLOUD_PROJECT", ""),
        "vertexai_location": vertexai_location or os.getenv("GOOGLE_CLOUD_LOCATION", "us-east4"),
        "documents": [],
        "artifacts_dir": None,
        "analysis_results": {},
        "markdown_report": "",
        "error": None,
    }

    result = app.invoke(initial_state)

    if result.get("error"):
        raise RuntimeError(result["error"])

    return result
