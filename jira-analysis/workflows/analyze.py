"""
LangGraph workflow for JIRA sprint and epic analysis using Vertex AI.

This workflow:
1. Queries JIRA API for sprints, issues, worklogs, and epics in a date range
2. Processes and analyzes sprint metrics (loading, completion, velocity)
3. Analyzes epic allocation and time tracking
4. Generates analysis using Vertex AI with a standardized template
5. Outputs formatted markdown report
"""

import json
import os
import re
import warnings
from datetime import datetime
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

import requests  # noqa: E402
from jinja2 import Template  # noqa: E402
from langchain_core.messages import HumanMessage, SystemMessage  # noqa: E402
from langgraph.graph import END, StateGraph  # noqa: E402

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

# Use new langchain-google-genai package (supports Vertex AI)
# Set Vertex AI mode before importing
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "true")
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    # Fallback to deprecated package if new one not available
    from langchain_google_vertexai import (  # type: ignore[import-untyped]
        ChatVertexAI as ChatGoogleGenerativeAI,
    )

# Constants
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
TEMPLATE_PATH = TEMPLATE_DIR / "jira-analysis.jinja2.md"
PROMPT_TEMPLATE_PATH = TEMPLATE_DIR / "prompt.jinja2.md"


class AnalysisState(TypedDict):
    """State for the JIRA analysis workflow."""

    # Input
    username: str | None
    jira_username: str | None  # Original JIRA username from config (e.g., "sundarvarun")
    jira_email: str | None  # Email from config (for API authentication, from .env)
    user_email: str | None  # User's email from config (for assignee queries)
    name: str | None  # User's display name (for output directory)
    account_id: str | None  # JIRA account ID (different from username)
    jira_url: str
    jira_project: str | None  # JIRA project key (required for unbounded query prevention)
    start_date: str
    end_date: str
    analysis_period: str
    config_path: str
    output_dir: str | None
    period: str | None  # Period key for centralized config lookup

    # JIRA API
    jira_token: str
    jira_email: str

    # Vertex AI
    vertexai_project: str
    vertexai_location: str

    # Data
    sprints: list[dict]
    issues: list[dict]
    worklogs: list[dict]
    epics: dict[str, dict]
    sprint_metrics: dict[str, dict]
    epic_names: dict[str, str]  # Map epic_key -> epic_name
    analysis_results: dict[str, Any]  # Analysis results from LLM

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


def _parse_jira_date(date_str: str) -> datetime:
    """Parse JIRA API date string into datetime object."""
    # JIRA dates are typically ISO format: "2025-01-15T10:30:00.000+0000"
    try:
        # Try with timezone
        return datetime.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        # Try without time
        return datetime.strptime(date_str[:10], "%Y-%m-%d")


class JiraSession:
    """JIRA API session wrapper matching the working notebook structure."""

    def __init__(self, username: str, api_token: str, api_base: str):
        """
        Initialize JIRA session.

        Args:
            username: JIRA email (for authentication)
            api_token: JIRA API token
            api_base: Base API URL (e.g., "https://evolutioniq.atlassian.net/rest/api/3")
        """
        self.session = requests.Session()
        self.session.auth = (username, api_token)
        self.session.headers.update({"Content-Type": "application/json"})
        self.api_base = api_base

    def _search(self, jql: str, max_results: int) -> list[dict]:
        """
        Search for issues using JQL.
        Uses the new /rest/api/3/search/jql endpoint (POST with JSON body).

        Args:
            jql: JQL query string
            max_results: Maximum number of results to return (will paginate if > 5000)

        Returns:
            List of issue dictionaries
        """
        # Store original desired total (for pagination limit)
        desired_total = max(1, max_results)
        # JIRA API requires maxResults between 1 and 5000 per request
        per_request_max = min(5000, desired_total)

        url = f"{self.api_base}/search/jql"
        SEARCH_FIELDS = ["id", "self", "key"]
        # New endpoint expects fields as array, not comma-separated string
        payload = {"jql": jql, "fields": SEARCH_FIELDS, "maxResults": per_request_max}
        issues = []
        next_page_token = None

        while True:
            # Add nextPageToken if we have one from previous request
            if next_page_token:
                payload["nextPageToken"] = next_page_token
            elif "nextPageToken" in payload:
                # Remove token if we're starting fresh
                del payload["nextPageToken"]

            response = self.session.post(url, json=payload)

            # Check HTTP status first
            if response.status_code != 200:
                error_msg = f"JIRA API returned {response.status_code}. "
                try:
                    error_data = response.json()
                    if "errorMessages" in error_data:
                        error_msg += "\n".join(error_data["errorMessages"])
                    elif "errors" in error_data:
                        error_msg += str(error_data["errors"])
                    else:
                        error_msg += response.text[:500]
                except Exception:
                    error_msg += response.text[:500]
                error_msg += f"\n  URL: {url}\n  Payload: {json.dumps(payload, indent=2)}"
                raise ValueError(error_msg)

            results = response.json()

            # Check for error messages in response
            if "errorMessages" in results:
                error_message = "\n".join(results["errorMessages"])
                # Include full response for debugging
                error_message += f"\n  Full response: {json.dumps(results, indent=2)}"
                raise ValueError(error_message)

            # Extract issues from response
            # The /rest/api/3/search/jql endpoint returns issues directly in the response
            batch_issues = results.get("issues", [])
            issues.extend(batch_issues)

            # Check if this is the last page
            is_last = results.get("isLast", True)
            next_page_token = results.get("nextPageToken")

            # Stop if we've reached the last page, have no more pages, or have enough results
            if is_last or not next_page_token or len(issues) >= desired_total:
                break

        # Return only up to desired_total
        return issues[:desired_total]

    def _issue(self, key: str) -> dict:
        """
        Get a single issue by key.

        Args:
            key: Issue key (e.g., "WC-123")

        Returns:
            Issue dictionary
        """
        url = f"{self.api_base}/issue/{key}"
        return self.session.get(url).json()

    def _fields(self) -> list[dict]:
        """
        Get all available fields.

        Returns:
            List of field dictionaries
        """
        url = f"{self.api_base}/field"
        response = self.session.get(url)
        return response.json()

    @staticmethod
    def parse_description(description_data):
        """
        Parses clean text from a Jira description's structured data.

        Args:
            description_data (dict): The Jira description data (as provided in the example).

        Returns:
            str: Clean text extracted from the description.
        """
        if not isinstance(description_data, dict) or "content" not in description_data:
            return ""  # Handle invalid input

        text_parts = []
        content = description_data["content"]

        def extract_text(item):
            if isinstance(item, dict):
                if item.get("type") == "text" and "text" in item:
                    text_parts.append(item["text"])
                elif "content" in item:
                    if isinstance(item["content"], list):
                        for sub_item in item["content"]:
                            extract_text(sub_item)
                    else:
                        extract_text(item["content"])  # handles if the content is not a list.

        for item in content:
            extract_text(item)

        return " ".join(text_parts).strip()

    def search_issue(self, key: str) -> dict:
        """
        Get a single issue with parsed fields.

        Args:
            key: Issue key (e.g., "WC-123")

        Returns:
            Dictionary with parsed issue fields
        """
        issue = self._issue(key)

        fields = issue.get("fields", {})

        # Field Extraction
        description = self.parse_description(fields.get("description", {}))
        assignee = (
            fields.get("assignee", {}).get("displayName", "") if fields.get("assignee") else ""
        )
        reporter = (
            fields.get("reporter", {}).get("displayName", "") if fields.get("reporter") else ""
        )
        priority = fields.get("priority", {}).get("name", "") if fields.get("priority") else ""
        status = fields.get("status", {}).get("name", "") if fields.get("status") else ""
        labels = fields.get("labels", [])
        sprints = fields.get("customfield_10020", [])
        sprint = sprints[-1]["name"] if sprints else None
        story_points = fields.get("customfield_10033")
        story_points = int(story_points) if story_points else None
        fix_versions = [version["name"] for version in fields.get("fixVersions", [])]

        return {
            "description": description,
            "assignee": assignee,
            "reporter": reporter,
            "priority": priority,
            "status": status,
            "labels": labels,
            "sprint": sprint,
            "story_points": story_points,
            "fix_versions": fix_versions,
        }

    def search_issues(self, jql: str, max_results: int = 5000) -> dict[str, dict]:
        """
        Search for issues and return parsed issue data.

        Args:
            jql: JQL query string
            max_results: Maximum number of results to return

        Returns:
            Dictionary mapping issue keys to parsed issue data
        """
        keys = [issue["key"] for issue in self._search(jql, max_results=max_results)]
        issues = {}
        for key in keys:
            issue = self.search_issue(key)
            issues[key] = issue
        return issues


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
        # The username passed from CLI might be the email format, so check multiple fields
        username = state["username"]
        user_config = None
        for user in centralized_config.get("users", []):
            # Match by username, email, or name
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

        # JIRA URL must come from environment variable (set in state or env)
        jira_url = state.get("jira_url", "") or os.getenv("JIRA_URL", "")
        if not jira_url:
            state["error"] = (
                "JIRA_URL environment variable required. Set JIRA_URL in .env file or environment."
            )
            return state

        # Use user config directly
        config = user_config

        # Don't override username here - we'll use both username and email

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

        # JIRA URL must come from environment variable (set in state or env)
        jira_url = state.get("jira_url", "") or os.getenv("JIRA_URL", "")
        if not jira_url:
            state["error"] = (
                "JIRA_URL environment variable required. Set JIRA_URL in .env file or environment."
            )
            return state

    # For JIRA queries, we prioritize email from config (most reliable),
    # then username, then accountId as fallback
    email = config.get("email") or state.get("email")
    config_username = config.get("username")  # Original username from config (e.g., "sundarvarun")
    state_username = state.get("username")  # Username passed from CLI (might be email)

    # Debug: Print config contents
    print(f"DEBUG load_config: config keys = {list(config.keys())}")
    print(f"DEBUG load_config: email from config = {config.get('email')}")
    print(f"DEBUG load_config: state_username = {state_username}")

    # Store both username formats - we'll try email first, then username
    # JIRA assignee field can use email (preferred) or username
    # Preserve email-based username from CLI if it's an email, otherwise use config username
    if state_username and "@" in state_username:
        # CLI passed an email, preserve it
        state["username"] = state_username
    else:
        # Use config username or fallback to email
        state["username"] = config_username or state_username or email
    state["jira_username"] = config_username  # Store original JIRA username separately
    state["user_email"] = email  # Store user's email from config (for assignee query)
    print(f"DEBUG load_config: state['user_email'] = {state['user_email']}")
    # Note: jira_email in state is for authentication (from .env), not the user's email from config
    # Don't override it here - it should come from CLI/env vars
    state["name"] = config.get("name", state.get("name"))  # Store name for output directory
    state["account_id"] = config.get("account_id", state.get("account_id"))
    state["jira_url"] = jira_url.rstrip("/")
    state["jira_project"] = (
        config.get("jira_project") or state.get("jira_project") or os.getenv("JIRA_PROJECT", "")
    )
    state["start_date"] = config.get("start_date", state.get("start_date", "2025-07-01"))
    state["end_date"] = config.get("end_date", state.get("end_date", "2025-12-31"))
    state["analysis_period"] = _format_analysis_period(state["start_date"], state["end_date"])

    return state


def _paginate_jira_request(
    url: str, session: requests.Session, params: dict, description: str
) -> list[dict]:
    """Handle pagination for JIRA API requests."""
    all_results = []
    start_at = 0
    max_results = 50

    params = params.copy()
    params["startAt"] = start_at
    params["maxResults"] = max_results

    if RICH_AVAILABLE:
        console = Console()
        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            task = progress.add_task(description, total=None)
            while True:
                response = session.get(url, params=params)
                if response.status_code == 410:
                    # 410 Gone - API endpoint or fields may be deprecated
                    error_msg = "JIRA API returned 410 Gone. This may indicate:\n"
                    error_msg += "  - The API endpoint is deprecated\n"
                    error_msg += "  - Some requested fields don't exist in your JIRA instance\n"
                    error_msg += "  - The JQL query contains invalid field names\n"
                    error_msg += f"  URL: {url}\n"
                    error_msg += f"  Params: {params}"
                    raise requests.exceptions.HTTPError(error_msg, response=response)
                response.raise_for_status()
                data = response.json()

                if "values" in data:
                    results = data["values"]
                elif "issues" in data:
                    results = data["issues"]
                else:
                    results = data if isinstance(data, list) else []

                all_results.extend(results)

                # Check if there are more results
                if isinstance(data, dict):
                    if data.get("isLast", True) or len(results) < max_results:
                        break
                    start_at += max_results
                    params["startAt"] = start_at
                else:
                    break
            progress.update(task, completed=True)
    else:
        print(f"  {description}...", end="", flush=True)
        while True:
            response = session.get(url, params=params)
            if response.status_code == 410:
                # 410 Gone - API endpoint or fields may be deprecated
                error_msg = "JIRA API returned 410 Gone. This may indicate:\n"
                error_msg += "  - The API endpoint is deprecated\n"
                error_msg += "  - Some requested fields don't exist in your JIRA instance\n"
                error_msg += "  - The JQL query contains invalid field names\n"
                error_msg += f"  URL: {url}\n"
                error_msg += f"  Params: {params}"
                raise requests.exceptions.HTTPError(error_msg, response=response)
            response.raise_for_status()
            data = response.json()

            if "values" in data:
                results = data["values"]
            elif "issues" in data:
                results = data["issues"]
            else:
                results = data if isinstance(data, list) else []

            all_results.extend(results)
            print(f" {len(all_results)}", end="", flush=True)

            # Check if there are more results
            if isinstance(data, dict):
                if data.get("isLast", True) or len(results) < max_results:
                    break
                start_at += max_results
                params["startAt"] = start_at
            else:
                break
        print(" ✓")

    return all_results


def fetch_jira_data(state: AnalysisState) -> AnalysisState:
    """Fetch sprint, issue, and worklog data from JIRA API."""
    if state.get("error"):
        return state

    account_id = state.get("account_id")
    username = state.get("username")
    jira_url = state["jira_url"]
    start_date = state["start_date"]
    end_date = state["end_date"]
    jira_token = state.get("jira_token") or os.getenv("JIRA_TOKEN")
    jira_email = state.get("jira_email") or os.getenv("JIRA_EMAIL")

    if not jira_token:
        state["error"] = "JIRA token required. Set JIRA_TOKEN environment variable."
        return state

    if not jira_email:
        state["error"] = "JIRA email required. Set JIRA_EMAIL environment variable."
        return state

    if RICH_AVAILABLE:
        console = Console()
        console.print("🔍 [cyan]Fetching JIRA data...[/cyan]")
    else:
        print("🔍 Fetching JIRA data...")

    # Initialize JiraSession (critical path - matches working notebook exactly)
    api_base = f"{jira_url}/rest/api/3"
    jira_session = JiraSession(jira_email, jira_token, api_base)

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    # Build JQL query for issues assigned to user in date range
    # JIRA requires a project filter to prevent "unbounded query" errors
    jira_project = state.get("jira_project") or os.getenv("JIRA_PROJECT", "")

    # Try different assignee formats - prioritize email from config, then username, then accountId
    jira_username = state.get(
        "jira_username"
    )  # Original username from config (e.g., "sundarvarun")
    user_email = state.get("user_email")  # User's email from config (preferred for assignee query)

    # Priority: email > username > accountId
    # Email format (e.g., "varun.sundar@evolutioniq.com") is most reliable for assignee queries
    if user_email:
        assignee_query = f'assignee = "{user_email}"'
    elif jira_username:
        # Try username (e.g., "sundarvarun")
        assignee_query = f'assignee = "{jira_username}"'
    elif username:
        # Fallback to username from state (might be email)
        assignee_query = f'assignee = "{username}"'
    elif account_id:
        # Last resort: try accountId
        assignee_query = f'assignee = "{account_id}"'
    else:
        state["error"] = "Either email, username, or account_id required"
        return state

    # Format dates with quotes (JQL requires quoted date strings)
    # Use 'updated' OR 'created' to catch issues that were created OR updated in the date range
    # This is more inclusive - an issue created in the period but not updated will still be found
    # Try with date filter first, but if no results, try without date filter to debug
    if jira_project:
        jql_with_date = f'project = {jira_project} AND {assignee_query} AND ((updated >= "{start_date}" AND updated <= "{end_date}") OR (created >= "{start_date}" AND created <= "{end_date}")) ORDER BY updated DESC'
        jql_no_date = f"project = {jira_project} AND {assignee_query} ORDER BY updated DESC"
    else:
        # Try without project first, but this may fail with unbounded query error
        jql_with_date = f'{assignee_query} AND ((updated >= "{start_date}" AND updated <= "{end_date}") OR (created >= "{start_date}" AND created <= "{end_date}")) ORDER BY updated DESC'
        jql_no_date = f"{assignee_query} ORDER BY updated DESC"

    # Try with date filter first
    jql = jql_with_date

    # Use JiraSession._search() to get issue keys (critical path - matches notebook exactly)
    if RICH_AVAILABLE:
        console = Console()
        console.print("  [dim]Searching for issues...[/dim]")
        console.print(f"  [dim]JQL: {jql}[/dim]")
    else:
        print("  Searching for issues...")
        print(f"  JQL: {jql}")

    try:
        # Search for issue keys using JiraSession._search() (matches notebook exactly)
        # Pass a very large number to fetch ALL issues - pagination will continue until is_last=True
        # JIRA API limit is 5000 per request, but we'll paginate automatically
        # Start with a reasonable limit - pagination will handle the rest
        issue_list = jira_session._search(jql, max_results=10000)
        issue_keys = [issue["key"] for issue in issue_list]

        # If no results with date filter, try without date filter to debug
        if len(issue_keys) == 0 and jira_project:
            if RICH_AVAILABLE:
                console.print(
                    "  [yellow]No issues found with date filter, trying without date filter...[/yellow]"
                )
            else:
                print("  No issues found with date filter, trying without date filter...")
            jql_no_date = f"project = {jira_project} AND {assignee_query} ORDER BY updated DESC"
            if RICH_AVAILABLE:
                console.print(f"  [dim]JQL (no date): {jql_no_date}[/dim]")
            else:
                print(f"  JQL (no date): {jql_no_date}")
            issue_list_no_date = jira_session._search(jql_no_date, max_results=10000)
            issue_keys_no_date = [issue["key"] for issue in issue_list_no_date]
            if len(issue_keys_no_date) > 0:
                if RICH_AVAILABLE:
                    console.print(
                        f"  [yellow]Found {len(issue_keys_no_date)} issues without date filter - date range may be incorrect[/yellow]"
                    )
                else:
                    print(
                        f"  Found {len(issue_keys_no_date)} issues without date filter - date range may be incorrect"
                    )
                # Use the issues without date filter for now
                issue_keys = issue_keys_no_date

        if RICH_AVAILABLE:
            console.print(f"  [green]Found {len(issue_keys)} issues[/green]")
        else:
            print(f"  Found {len(issue_keys)} issues")
    except ValueError as e:
        # Handle JQL errors from _search (matches notebook error handling)
        error_msg = str(e)
        if "Unbounded JQL queries" in error_msg:
            error_msg += "\n\nTip: Add a project filter to your JQL query or set JIRA_PROJECT environment variable."
        # Print full error for debugging
        if RICH_AVAILABLE:
            console = Console()
            console.print("❌ [red]JIRA search error:[/red]")
            console.print(f"[red]{error_msg}[/red]")
        else:
            print("❌ JIRA search error:")
            print(error_msg)
        state["error"] = f"JIRA search error: {error_msg}"
        return state

    # Fetch each issue individually using JiraSession._issue() (critical path)
    issues = []
    if RICH_AVAILABLE:
        console = Console()
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            task = progress.add_task("Fetching issue details...", total=len(issue_keys))
            for issue_key in issue_keys:
                try:
                    # Use JiraSession._issue() method (critical path)
                    issue_data = jira_session._issue(issue_key)
                    issues.append(issue_data)
                except Exception as e:
                    if RICH_AVAILABLE:
                        console.print(f"  [yellow]⚠️  Failed to fetch {issue_key}: {e}[/yellow]")
                    else:
                        print(f"  ⚠️  Failed to fetch {issue_key}: {e}")
                progress.update(task, advance=1)
    else:
        print(f"  Fetching details for {len(issue_keys)} issues...", end="", flush=True)
        for idx, issue_key in enumerate(issue_keys, 1):
            try:
                # Use JiraSession._issue() method (critical path)
                issue_data = jira_session._issue(issue_key)
                issues.append(issue_data)
            except Exception as e:
                print(f"\n  ⚠️  Failed to fetch {issue_key}: {e}")
            if idx % 10 == 0:
                print(f" {idx}/{len(issue_keys)}", end="", flush=True)
        print(" ✓")

    # Extract sprints from user's issues (not all sprints from all boards)
    # Each issue has a customfield_10020 field containing sprint information
    sprint_map = {}  # sprint_id -> sprint info
    issue_sprint_map = {}  # issue_key -> list of sprint_ids

    for issue in issues:
        issue_key = issue.get("key")
        fields = issue.get("fields", {})
        sprints_field = fields.get("customfield_10020", [])  # Sprint field

        if sprints_field:
            for sprint_info in sprints_field:
                sprint_id = sprint_info.get("id")
                if sprint_id:
                    sprint_name = sprint_info.get("name", f"Sprint {sprint_id}")
                    # Store sprint info
                    sprint_map[sprint_id] = {
                        "id": sprint_id,
                        "name": sprint_name,
                        "state": sprint_info.get("state", ""),
                        "startDate": sprint_info.get("startDate"),
                        "endDate": sprint_info.get("endDate"),
                        "completeDate": sprint_info.get("completeDate"),
                    }
                    # Track which issues belong to which sprint
                    if issue_key not in issue_sprint_map:
                        issue_sprint_map[issue_key] = []
                    issue_sprint_map[issue_key].append(sprint_id)

    # Filter sprints by date range (only sprints that contain user's issues)
    filtered_sprints = []
    for _sprint_id, sprint_info in sprint_map.items():
        sprint_start = sprint_info.get("startDate")
        sprint_end = sprint_info.get("endDate")
        if sprint_start and sprint_end:
            sprint_start_dt = _parse_jira_date(sprint_start)
            sprint_end_dt = _parse_jira_date(sprint_end)
            # Include sprints that overlap with our date range
            if sprint_start_dt <= end_dt and sprint_end_dt >= start_dt:
                filtered_sprints.append(sprint_info)

    # Fetch worklogs for issues (using JiraSession)
    worklogs = []
    if RICH_AVAILABLE:
        console = Console()
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            task = progress.add_task("Fetching worklogs...", total=len(issues))
            for issue in issues:
                issue_key = issue.get("key")
                if issue_key:
                    worklog_url = f"{api_base}/issue/{issue_key}/worklog"
                    try:
                        # Use JiraSession's session for worklogs
                        worklog_response = jira_session.session.get(worklog_url)
                        if worklog_response.status_code == 200:
                            worklog_data = worklog_response.json()
                            issue_worklogs = worklog_data.get("worklogs", [])
                            for wl in issue_worklogs:
                                wl["issue_key"] = issue_key
                                worklogs.append(wl)
                    except Exception:
                        pass
                progress.update(task, advance=1)
    else:
        print(f"  Fetching worklogs for {len(issues)} issues...", end="", flush=True)
        for idx, issue in enumerate(issues, 1):
            issue_key = issue.get("key")
            if issue_key:
                worklog_url = f"{api_base}/issue/{issue_key}/worklog"
                try:
                    # Use JiraSession's session for worklogs
                    worklog_response = jira_session.session.get(worklog_url)
                    if worklog_response.status_code == 200:
                        worklog_data = worklog_response.json()
                        issue_worklogs = worklog_data.get("worklogs", [])
                        for wl in issue_worklogs:
                            wl["issue_key"] = issue_key
                            worklogs.append(wl)
                except Exception:
                    pass
            if idx % 10 == 0:
                print(f" {idx}/{len(issues)}", end="", flush=True)
        print(" ✓")

    # Organize epics using parent field and fetch epic names
    epics = {}
    epic_names = {}  # Map epic_key -> epic_name

    # First pass: collect all epic keys
    epic_keys_to_fetch = set()
    for issue in issues:
        fields = issue.get("fields", {})
        parent = fields.get("parent")
        epic_key = None

        if parent:
            epic_key = parent.get("key") if isinstance(parent, dict) else str(parent)
        else:
            issue_type = fields.get("issuetype", {})
            if issue_type.get("name", "").lower() == "epic":
                epic_key = issue.get("key")

        if epic_key and epic_key != "_no_epic":
            epic_keys_to_fetch.add(epic_key)

    # Fetch epic names from JIRA
    if RICH_AVAILABLE:
        console = Console()
        console.print(f"  [dim]Fetching epic names for {len(epic_keys_to_fetch)} epics...[/dim]")
    else:
        print(f"  Fetching epic names for {len(epic_keys_to_fetch)} epics...")

    for epic_key in epic_keys_to_fetch:
        try:
            epic_issue = jira_session._issue(epic_key)
            epic_fields = epic_issue.get("fields", {})
            epic_name = epic_fields.get("summary", epic_key)  # Use summary as name, fallback to key
            epic_names[epic_key] = epic_name
        except Exception as e:
            # If we can't fetch, use key as name
            epic_names[epic_key] = epic_key
            if RICH_AVAILABLE:
                console.print(
                    f"  [yellow]⚠️  Could not fetch epic name for {epic_key}: {e}[/yellow]"
                )
            else:
                print(f"  ⚠️  Could not fetch epic name for {epic_key}: {e}")

    # Second pass: organize issues by epic
    for issue in issues:
        fields = issue.get("fields", {})

        # Get parent (epic) from parent field
        parent = fields.get("parent")
        epic_key = None

        if parent:
            # Parent field contains the epic/parent issue
            epic_key = parent.get("key") if isinstance(parent, dict) else str(parent)
        else:
            # Check if this issue itself is an epic
            issue_type = fields.get("issuetype", {})
            if issue_type.get("name", "").lower() == "epic":
                epic_key = issue.get("key")

        # Group issues by epic (or create a "no-epic" group)
        if not epic_key:
            epic_key = "_no_epic"

        if epic_key not in epics:
            epic_name = (
                epic_names.get(epic_key, epic_key) if epic_key != "_no_epic" else "Uncategorized"
            )
            epics[epic_key] = {
                "key": epic_key,
                "name": epic_name,
                "issues": [],
                "total_time_spent": 0,
                "total_time_estimate": 0,
            }
        epics[epic_key]["issues"].append(issue)

        # Sum time spent/estimate
        time_spent = fields.get("timespent", 0) or 0
        time_estimate = fields.get("timeoriginalestimate", 0) or 0
        epics[epic_key]["total_time_spent"] += time_spent
        epics[epic_key]["total_time_estimate"] += time_estimate

    # Calculate sprint metrics based ONLY on user's issues in each sprint
    sprint_metrics = {}
    for sprint in filtered_sprints:
        sprint_id = sprint.get("id")
        sprint_name = sprint.get("name", f"Sprint {sprint_id}")

        # Find user's issues that belong to this sprint
        user_sprint_issues = []
        user_sprint_issue_keys = []
        for issue in issues:
            issue_key = issue.get("key")
            if issue_key in issue_sprint_map and sprint_id in issue_sprint_map[issue_key]:
                user_sprint_issues.append(issue)
                user_sprint_issue_keys.append(issue_key)

        if not user_sprint_issues:
            # Skip sprints with no user issues
            continue

        # Calculate metrics based ONLY on user's issues
        total_estimate = 0
        total_spent = 0
        completed_issues = 0
        completed_points = 0  # Sum of story points for completed issues
        completed_issue_keys = []

        # Track epic allocation by story points (for all issues, not just completed)
        epic_allocation = {}  # epic_key -> total story points
        total_sprint_points = 0  # Total story points in sprint (for percentage calculation)

        for issue in user_sprint_issues:
            fields = issue.get("fields", {})
            time_estimate = fields.get("timeoriginalestimate", 0) or 0
            time_spent = fields.get("timespent", 0) or 0
            status_name = fields.get("status", {}).get("name", "").lower()
            story_points = fields.get("customfield_10033")  # Story points field
            story_points = int(story_points) if story_points else 0

            total_estimate += time_estimate
            total_spent += time_spent

            # Track epic allocation
            parent = fields.get("parent")
            epic_key = None
            if parent:
                epic_key = parent.get("key") if isinstance(parent, dict) else str(parent)
            else:
                issue_type = fields.get("issuetype", {})
                if issue_type.get("name", "").lower() == "epic":
                    epic_key = issue.get("key")

            if not epic_key:
                epic_key = "Uncategorized"

            if epic_key not in epic_allocation:
                epic_allocation[epic_key] = 0
            epic_allocation[epic_key] += story_points
            total_sprint_points += story_points

            if status_name in ["done", "closed", "resolved"]:
                completed_issues += 1
                completed_points += story_points
                completed_issue_keys.append(issue.get("key"))

        # Calculate epic percentages (should add up to 100%)
        epic_percentages = {}
        if total_sprint_points > 0:
            for epic_key, points in epic_allocation.items():
                percentage = (points / total_sprint_points) * 100
                epic_percentages[epic_key] = percentage
        else:
            # If no story points, use issue count instead
            epic_allocation_by_count = {}
            for issue in user_sprint_issues:
                fields = issue.get("fields", {})
                parent = fields.get("parent")
                epic_key = None
                if parent:
                    epic_key = parent.get("key") if isinstance(parent, dict) else str(parent)
                else:
                    issue_type = fields.get("issuetype", {})
                    if issue_type.get("name", "").lower() == "epic":
                        epic_key = issue.get("key")
                if not epic_key:
                    epic_key = "Uncategorized"
                if epic_key not in epic_allocation_by_count:
                    epic_allocation_by_count[epic_key] = 0
                epic_allocation_by_count[epic_key] += 1

            total_issues_count = len(user_sprint_issues)
            if total_issues_count > 0:
                for epic_key, count in epic_allocation_by_count.items():
                    percentage = (count / total_issues_count) * 100
                    epic_percentages[epic_key] = percentage

        # Get issue summaries for accomplishments
        accomplishments = []
        for issue in user_sprint_issues:
            issue_key = issue.get("key")
            fields = issue.get("fields", {})
            summary = fields.get("summary", "")
            status_name = fields.get("status", {}).get("name", "")
            issue_type = fields.get("issuetype", {}).get("name", "")

            if status_name.lower() in ["done", "closed", "resolved"]:
                accomplishments.append({"key": issue_key, "summary": summary, "type": issue_type})

        sprint_metrics[sprint_name] = {
            "sprint_id": sprint_id,
            "name": sprint_name,
            "start_date": sprint.get("startDate"),
            "end_date": sprint.get("endDate"),
            "total_issues": len(user_sprint_issues),
            "completed_issues": completed_issues,
            "completion_rate": (completed_issues / len(user_sprint_issues) * 100)
            if user_sprint_issues
            else 0,
            "total_estimate": total_estimate,
            "total_spent": total_spent,
            "velocity": completed_points,  # Velocity in story points, not issue count
            "completed_points": completed_points,  # Also store separately for clarity
            "accomplishments": accomplishments,  # List of completed issues
            "epic_allocation": epic_percentages,  # Epic allocation percentages (should sum to 100%)
            "all_issues": [
                {
                    "key": issue.get("key"),
                    "summary": issue.get("fields", {}).get("summary", ""),
                    "status": issue.get("fields", {}).get("status", {}).get("name", ""),
                }
                for issue in user_sprint_issues
            ],
        }

    # Store epic names mapping for use in report generation
    state["epic_names"] = epic_names
    state["sprints"] = filtered_sprints
    state["issues"] = issues
    state["worklogs"] = worklogs
    state["epics"] = epics
    state["sprint_metrics"] = sprint_metrics

    if RICH_AVAILABLE:
        console = Console()
        console.print(
            f"✓ [green]Fetched {len(issues)} issues, {len(filtered_sprints)} sprints, {len(worklogs)} worklogs[/green]"
        )
    else:
        print(
            f"✓ Fetched {len(issues)} issues, {len(filtered_sprints)} sprints, {len(worklogs)} worklogs"
        )

    return state


def analyze_with_vertexai(state: AnalysisState) -> AnalysisState:
    """Analyze JIRA data using Vertex AI."""
    if state.get("error"):
        return state

    username = state.get("username", "Unknown")
    account_id = state.get("account_id", "")
    analysis_period = state["analysis_period"]
    jira_url = state["jira_url"]
    project = state["vertexai_project"]
    location = state.get("vertexai_location", "us-east4")

    if RICH_AVAILABLE:
        console = Console()
        console.print("🤖 [cyan]Analyzing with Vertex AI...[/cyan]")
    else:
        print("🤖 Analyzing with Vertex AI...")

    # Set quota project to prevent warnings
    os.environ["GOOGLE_CLOUD_QUOTA_PROJECT"] = project

    # Initialize Vertex AI
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro",
        project=project,
        location=location,
        temperature=0.3,
    )

    # Prepare data for analysis
    sprints = state.get("sprints", [])
    issues = state.get("issues", [])
    worklogs = state.get("worklogs", [])
    epics = state.get("epics", {})
    sprint_metrics = state.get("sprint_metrics", {})

    # Load report template
    with open(TEMPLATE_PATH) as f:
        report_template_content = f.read()

    # Load prompt template
    with open(PROMPT_TEMPLATE_PATH) as f:
        prompt_template = Template(f.read())

    # Build prompt with template
    ANALYSIS_SYSTEM_PROMPT = """You are an expert at analyzing JIRA sprint and epic data for engineering performance evaluation.

Your task is to analyze sprint metrics, velocity, epic allocation, and worklog data to generate a comprehensive markdown report.

Be specific, provide examples, and focus on actionable insights for sprint planning, velocity tracking, and time allocation."""

    # Limit data to avoid token limits - summarize instead of sending everything
    # Only send key fields from a subset of issues
    issues_summary = []
    for issue in issues[:30]:  # Limit to 30 issues
        fields = issue.get("fields", {})
        issues_summary.append(
            {
                "key": issue.get("key"),
                "summary": fields.get("summary", "")[:200],  # Truncate summary
                "status": fields.get("status", {}).get("name") if fields.get("status") else None,
                "created": fields.get("created", "")[:10] if fields.get("created") else None,
                "updated": fields.get("updated", "")[:10] if fields.get("updated") else None,
                "story_points": fields.get("customfield_10033"),
            }
        )

    # Summarize epics - only send key info
    epics_summary = {
        k: {
            "key": v.get("key"),
            "issue_count": len(v.get("issues", [])),
            "total_time_spent": v.get("total_time_spent", 0),
            "total_time_estimate": v.get("total_time_estimate", 0),
        }
        for k, v in list(epics.items())[:20]
    }  # Limit to 20 epics

    # Render prompt template with data
    user_prompt = prompt_template.render(
        username=username,
        account_id=account_id,
        jira_url=jira_url,
        analysis_period=analysis_period,
        sprints_count=len(sprints),
        issues_count=len(issues),
        worklogs_count=len(worklogs),
        epics_count=len(epics),
        sprint_metrics_json=json.dumps(sprint_metrics, indent=2),
        issues_json=json.dumps(issues_summary, indent=2),
        worklogs_json=json.dumps(worklogs[:50], indent=2),  # Limit to first 50
        epics_json=json.dumps(epics_summary, indent=2),
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
    sprint_metrics = state.get("sprint_metrics", {})

    # Always generate sprint metrics section first (LLM sometimes generates minimal reports)
    username = state.get("username", "Unknown")
    analysis_period = state["analysis_period"]

    sprint_section_lines = [
        f"# JIRA Analysis: {username}",
        "",
        f"**Analysis Period**: {analysis_period}",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"- **Sprints**: {len(state.get('sprints', []))}",
        f"- **Issues**: {len(state.get('issues', []))}",
        f"- **Epics**: {len(state.get('epics', {}))}",
        "",
        "## Sprint Metrics",
        "",
    ]

    # Sort sprints by date (most recent first)
    sorted_sprints = sorted(
        sprint_metrics.items(), key=lambda x: x[1].get("start_date", ""), reverse=True
    )

    for sprint_name, metrics in sorted_sprints:
        velocity_points = metrics.get("velocity", 0)
        sprint_section_lines.extend(
            [
                f"### {sprint_name}",
                f"- Completion Rate: {metrics.get('completion_rate', 0):.1f}%",
                f"- Velocity: {velocity_points} points",
                "",
            ]
        )

        # Add accomplishments
        accomplishments = metrics.get("accomplishments", [])
        if accomplishments:
            sprint_section_lines.append("**Accomplishments:**")
            for acc in accomplishments:
                issue_key = acc.get("key", "")
                summary = acc.get("summary", "")
                sprint_section_lines.append(f"- {issue_key}: {summary}")
        else:
            sprint_section_lines.append("**Accomplishments:**")
            sprint_section_lines.append("- No completed issues")
        sprint_section_lines.append("")

    # Start with sprint metrics, then append LLM output (if any)
    if analysis_markdown.strip():
        # Remove any duplicate headers from LLM output
        llm_lines = analysis_markdown.split("\n")
        # Skip header lines if they exist
        start_idx = 0
        for i, line in enumerate(llm_lines):
            if line.startswith("#") and ("JIRA Analysis" in line or "Analysis Period" in line):
                continue
            if line.strip() and not line.startswith("#"):
                start_idx = i
                break
        analysis_markdown = "\n".join(llm_lines[start_idx:])
        combined_markdown = "\n".join(sprint_section_lines) + "\n\n" + analysis_markdown
    else:
        combined_markdown = "\n".join(sprint_section_lines)

    if analysis_markdown:
        # Post-process combined output to ensure accomplishments are included
        report_lines = combined_markdown.split("\n")
        new_report_lines = []
        i = 0
        while i < len(report_lines):
            line = report_lines[i]
            new_report_lines.append(line)

            # Check if this is a sprint header (### Sprint Name)
            if line.startswith("### ") and i + 1 < len(report_lines):
                sprint_name = line.replace("### ", "").strip()
                if sprint_name in sprint_metrics:
                    metrics = sprint_metrics[sprint_name]
                    # Look ahead to see if accomplishments are already included
                    has_accomplishments = False
                    j = i + 1
                    while j < min(i + 10, len(report_lines)):
                        if (
                            "Accomplishments" in report_lines[j]
                            or "accomplishments" in report_lines[j].lower()
                        ):
                            has_accomplishments = True
                            break
                        if j > i + 1 and report_lines[j].startswith("###"):
                            break
                        j += 1

                    # If no accomplishments found, add them after velocity line
                    if not has_accomplishments:
                        # Find where to insert (after velocity line)
                        k = i + 1
                        while k < min(i + 5, len(report_lines)):
                            if "Velocity" in report_lines[k]:
                                # Also fix velocity line if it says "issues" instead of "points"
                                velocity_line = report_lines[k]
                                if (
                                    "issues" in velocity_line.lower()
                                    and "points" not in velocity_line.lower()
                                ):
                                    velocity_points = metrics.get("velocity", 0)
                                    new_report_lines[-1] = f"- Velocity: {velocity_points} points"
                                k += 1
                                # Insert accomplishments here
                                accomplishments = metrics.get("accomplishments", [])
                                new_report_lines.append("")
                                new_report_lines.append("**Accomplishments:**")
                                if accomplishments:
                                    for acc in accomplishments:
                                        issue_key = acc.get("key", "")
                                        summary = acc.get("summary", "")
                                        new_report_lines.append(f"- {issue_key}: {summary}")
                                else:
                                    new_report_lines.append("- No completed issues")
                                break
                            k += 1
            i += 1

        state["markdown_report"] = "\n".join(new_report_lines)

    # Add epic allocation summary section (append after Sprint Metrics section)
    sprint_metrics = state.get("sprint_metrics", {})
    if sprint_metrics:
        # Use the report we just generated (which includes sprint metrics)
        report_content = state.get("markdown_report", "")
        if not report_content:
            # Fallback: use sprint section if report is empty
            report_content = (
                "\n".join(sprint_section_lines) if "sprint_section_lines" in locals() else ""
            )

        # Generate epic allocation summary
        summary_lines = [
            "",
            "---",
            "",
            "## Half-Year Summary: Epic Allocation by Sprint",
            "",
            "This section shows the percentage of work (by story points) allocated to each epic per sprint. Percentages add up to 100% per sprint.",
            "",
        ]

        # Sort sprints by date (most recent first)
        sorted_sprints = sorted(
            sprint_metrics.items(), key=lambda x: x[1].get("start_date", ""), reverse=True
        )

        # Collect all unique epics across all sprints and map to names
        epic_names_map = state.get("epic_names", {})
        epics_dict = state.get("epics", {})

        # Build epic_key -> epic_name mapping
        epic_key_to_name = {}
        for epic_key, epic_data in epics_dict.items():
            if epic_key != "_no_epic":
                epic_key_to_name[epic_key] = epic_data.get("name", epic_key)
            else:
                epic_key_to_name["Uncategorized"] = "Uncategorized"

        # Also use epic_names from state if available
        for epic_key, epic_name in epic_names_map.items():
            epic_key_to_name[epic_key] = epic_name

        all_epic_keys = set()
        for _sprint_name, metrics in sorted_sprints:
            epic_allocation = metrics.get("epic_allocation", {})
            all_epic_keys.update(epic_allocation.keys())

        # Create epic list with names, sorted by name (but keep Uncategorized last)
        epic_keys_sorted = sorted(
            [key for key in all_epic_keys if key != "Uncategorized"],
            key=lambda k: epic_key_to_name.get(k, k),
        )
        if "Uncategorized" in all_epic_keys:
            epic_keys_sorted.append("Uncategorized")

        # Create table header with epic names
        epic_names_list = [epic_key_to_name.get(key, key) for key in epic_keys_sorted]
        header = "| Sprint | " + " | ".join(epic_names_list) + " |"
        separator = "|" + "---|" * (len(epic_names_list) + 1)
        summary_lines.extend([header, separator])

        # Add rows for each sprint
        for sprint_name, metrics in sorted_sprints:
            epic_allocation = metrics.get("epic_allocation", {})
            row_values = [sprint_name]
            total_percentage = 0

            for epic_key in epic_keys_sorted:
                percentage = epic_allocation.get(epic_key, 0)
                total_percentage += percentage
                # Format percentage (show 0% if < 0.1%)
                if percentage < 0.1:
                    row_values.append("—")
                else:
                    row_values.append(f"{percentage:.1f}%")

            # Verify percentages add up to ~100% (allow small rounding differences)
            if abs(total_percentage - 100.0) > 1.0:
                row_values.append(f"⚠️ ({total_percentage:.1f}%)")

            summary_lines.append("| " + " | ".join(row_values) + " |")

        summary_lines.extend(
            [
                "",
                "**Note:** Percentages are calculated based on story points. If an issue has no story points, it's counted by issue count. Issues without an epic are marked as 'Uncategorized'.",
                "",
            ]
        )

        # Append summary at the end of the report (more reliable than trying to insert)
        summary_section = "\n".join(summary_lines)

        # Remove existing summary if it exists (to avoid duplicates)
        lines = report_content.split("\n")
        new_lines = []
        skip_summary = False
        for i, line in enumerate(lines):
            if "Half-Year Summary" in line:
                skip_summary = True
            elif skip_summary:
                # Skip until we hit the next major section or end
                if line.startswith("## ") and "Half-Year Summary" not in line:
                    skip_summary = False
                    new_lines.append(line)
                elif not line.strip():  # Empty line might be end of summary
                    # Check if next non-empty line is a new section
                    found_section = False
                    for j in range(i + 1, min(i + 5, len(lines))):
                        if lines[j].startswith("## "):
                            found_section = True
                            break
                        if lines[j].strip():
                            break
                    if found_section:
                        skip_summary = False
                if not skip_summary:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        # Append summary at the end
        if new_lines and new_lines[-1].strip():
            new_lines.append("")
        new_lines.append(summary_section)

        state["markdown_report"] = "\n".join(new_lines)

    else:
        # Fallback: generate basic report from data
        username = state.get("username", "Unknown")
        analysis_period = state["analysis_period"]
        sprints = state.get("sprints", [])
        issues = state.get("issues", [])
        epics = state.get("epics", {})
        sprint_metrics = state.get("sprint_metrics", {})

        report_lines = [
            f"# JIRA Analysis: {username}",
            "",
            f"**Analysis Period**: {analysis_period}",
            "",
            "---",
            "",
            "## Summary",
            "",
            f"- **Sprints**: {len(sprints)}",
            f"- **Issues**: {len(issues)}",
            f"- **Epics**: {len(epics)}",
            "",
            "## Sprint Metrics",
            "",
        ]

        # Sort sprints by date (most recent first)
        sorted_sprints = sorted(
            sprint_metrics.items(), key=lambda x: x[1].get("start_date", ""), reverse=True
        )

        for sprint_name, metrics in sorted_sprints:
            velocity_points = metrics.get("velocity", 0)  # Velocity is now in story points
            report_lines.extend(
                [
                    f"### {sprint_name}",
                    f"- Completion Rate: {metrics.get('completion_rate', 0):.1f}%",
                    f"- Velocity: {velocity_points} points",
                    "",
                ]
            )

            # Add accomplishments
            accomplishments = metrics.get("accomplishments", [])
            if accomplishments:
                report_lines.append("**Accomplishments:**")
                for acc in accomplishments:
                    issue_key = acc.get("key", "")
                    summary = acc.get("summary", "")
                    report_lines.append(f"- {issue_key}: {summary}")
            else:
                report_lines.append("**Accomplishments:**")
                report_lines.append("- No completed issues")
            report_lines.append("")

        # Add epic allocation summary
        if sprint_metrics:
            summary_lines = [
                "",
                "---",
                "",
                "## Half-Year Summary: Epic Allocation by Sprint",
                "",
                "This section shows the percentage of work (by story points) allocated to each epic per sprint. Percentages add up to 100% per sprint.",
                "",
            ]

            # Collect all unique epics across all sprints and map to names
            epic_names_map = state.get("epic_names", {})
            epics_dict = state.get("epics", {})

            # Build epic_key -> epic_name mapping
            epic_key_to_name = {}
            for epic_key, epic_data in epics_dict.items():
                if epic_key != "_no_epic":
                    epic_key_to_name[epic_key] = epic_data.get("name", epic_key)
                else:
                    epic_key_to_name["Uncategorized"] = "Uncategorized"

            # Also use epic_names from state if available
            for epic_key, epic_name in epic_names_map.items():
                epic_key_to_name[epic_key] = epic_name

            all_epic_keys = set()
            for _sprint_name, metrics in sorted_sprints:
                epic_allocation = metrics.get("epic_allocation", {})
                all_epic_keys.update(epic_allocation.keys())

            # Create epic list with names, sorted by name (but keep Uncategorized last)
            epic_keys_sorted = sorted(
                [key for key in all_epic_keys if key != "Uncategorized"],
                key=lambda k: epic_key_to_name.get(k, k),
            )
            if "Uncategorized" in all_epic_keys:
                epic_keys_sorted.append("Uncategorized")

            # Create table header with epic names
            epic_names_list = [epic_key_to_name.get(key, key) for key in epic_keys_sorted]
            header = "| Sprint | " + " | ".join(epic_names_list) + " |"
            separator = "|" + "---|" * (len(epic_names_list) + 1)
            summary_lines.extend([header, separator])

            # Add rows for each sprint
            for sprint_name, metrics in sorted_sprints:
                epic_allocation = metrics.get("epic_allocation", {})
                row_values = [sprint_name]

                for epic_key in epic_keys_sorted:
                    percentage = epic_allocation.get(epic_key, 0)
                    # Format percentage (show 0% if < 0.1%)
                    if percentage < 0.1:
                        row_values.append("—")
                    else:
                        row_values.append(f"{percentage:.1f}%")

                summary_lines.append("| " + " | ".join(row_values) + " |")

            summary_lines.extend(
                [
                    "",
                    "**Note:** Percentages are calculated based on story points. If an issue has no story points, it's counted by issue count. Issues without an epic are marked as 'Uncategorized'.",
                    "",
                ]
            )

            report_lines.extend(summary_lines)

        state["markdown_report"] = "\n".join(report_lines)

    return state


def save_report(state: AnalysisState) -> AnalysisState:
    """Save markdown report to file."""
    if state.get("error"):
        return state

    output_dir_arg = state.get("output_dir")

    # If output_dir is provided, use it directly (it already includes name/period from CLI)
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

        # Slugify name/username for directory (prefer name for cleaner paths)
        slugified_name = re.sub(
            r"[^a-z0-9-]", "-", display_name.lower() if display_name else "unknown"
        )
        slugified_name = re.sub(r"-+", "-", slugified_name).strip("-")

        period_str = period if period else "unknown"
        report_dir = output_dir / slugified_name / period_str

    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "jira-analysis.md"

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
workflow.add_node("fetch_jira", fetch_jira_data)
workflow.add_node("analyze", analyze_with_vertexai)
workflow.add_node("generate", generate_report)
workflow.add_node("save", save_report)

# Add edges
workflow.set_entry_point("load_config")
workflow.add_edge("load_config", "fetch_jira")
workflow.add_edge("fetch_jira", "analyze")
workflow.add_edge("analyze", "generate")
workflow.add_edge("generate", "save")
workflow.add_edge("save", END)

# Compile the workflow
app = workflow.compile()


def run(
    config_path: str,
    jira_token: str | None = None,
    jira_email: str | None = None,
    jira_url: str | None = None,
    jira_project: str | None = None,
    vertexai_project: str | None = None,
    vertexai_location: str | None = None,
    username: str | None = None,
    period: str | None = None,
    output_dir: str | None = None,
):
    """
    Run the JIRA analysis workflow.

    Args:
        config_path: Path to user config.json file or centralized config.json
        jira_token: JIRA API token (or set JIRA_TOKEN env var)
        jira_email: JIRA email (or set JIRA_EMAIL env var)
        jira_url: JIRA instance URL (or set JIRA_URL env var)
        jira_project: JIRA project key (required, or set JIRA_PROJECT env var)
        vertexai_project: Google Cloud project ID (or set GOOGLE_CLOUD_PROJECT env var)
        vertexai_location: Vertex AI location (or set GOOGLE_CLOUD_LOCATION env var)
        username: Username to use when config_path points to centralized config.json
        period: Period key (e.g., "2025H2") to use when config_path points to centralized config.json
        output_dir: Output directory for the report (defaults to reports/<username>/<period>)
    """
    # Get JIRA URL and project from parameter, env, or empty string
    resolved_jira_url = jira_url or os.getenv("JIRA_URL", "")
    resolved_jira_project = jira_project or os.getenv("JIRA_PROJECT", "")

    initial_state: AnalysisState = {
        "config_path": config_path,
        "username": username,
        "jira_username": None,  # Will be populated from config in load_config
        "jira_email": jira_email or os.getenv("JIRA_EMAIL", ""),
        "user_email": None,  # Will be populated from config in load_config (for assignee queries)
        "name": None,  # Will be populated from config in load_config
        "account_id": None,
        "jira_url": resolved_jira_url,  # Pass JIRA_URL to state
        "jira_project": resolved_jira_project,  # Pass JIRA_PROJECT to state
        "start_date": "",
        "end_date": "",
        "analysis_period": "",
        "output_dir": output_dir,
        "period": period,
        "jira_token": jira_token or os.getenv("JIRA_TOKEN", ""),
        "vertexai_project": vertexai_project or os.getenv("GOOGLE_CLOUD_PROJECT", ""),
        "vertexai_location": vertexai_location or os.getenv("GOOGLE_CLOUD_LOCATION", "us-east4"),
        "sprints": [],
        "issues": [],
        "worklogs": [],
        "epics": {},
        "sprint_metrics": {},
        "epic_names": {},
        "analysis_results": {},
        "markdown_report": "",
        "error": None,
    }

    result = app.invoke(initial_state)

    if result.get("error"):
        raise RuntimeError(result["error"])

    return result
