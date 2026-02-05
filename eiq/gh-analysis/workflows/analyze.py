"""
LangGraph workflow for GitHub PR review analysis using Vertex AI.

This workflow:
1. Queries GitHub API for PRs reviewed by a user in a date range
2. Processes and analyzes the review data
3. Generates analysis using Vertex AI with a standardized template
4. Outputs formatted markdown report
"""

import json
import os
import re
import warnings
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

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
TEMPLATE_PATH = TEMPLATE_DIR / "gh-analysis.jinja2.md"
PROMPT_TEMPLATE_PATH = TEMPLATE_DIR / "prompt.jinja2.md"
MAX_PAGES = 10  # GitHub search limit is 1000 results (10 pages)
MAX_REVIEWED_PRS = 50
MAX_AUTHORED_PRS = 30


class AnalysisState(TypedDict):
    """State for the PR review analysis workflow."""

    # Input
    username: str | None
    organization: str
    start_date: str
    end_date: str
    analysis_period: str
    config_path: str
    output_dir: str | None
    period: str | None  # Period key for centralized config lookup

    # GitHub API
    github_token: str

    # Vertex AI
    vertexai_project: str
    vertexai_location: str

    # Data
    pr_data: list[dict]
    authored_pr_data: list[dict]
    review_data: dict
    analysis_results: dict

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
    if start_dt.month == 1 and start_dt.day == 1 and end_dt.month == 12 and end_dt.day == 31:
        return f"{start_dt.year} (January 1 - December 31, {start_dt.year})"
    # H2
    elif start_dt.month == 7 and start_dt.day == 1 and end_dt.month == 12 and end_dt.day == 31:
        return f"{start_dt.year}H2 (July 1 - December 31, {start_dt.year})"
    # H1
    elif start_dt.month == 1 and start_dt.day == 1 and end_dt.month == 6 and end_dt.day == 30:
        return f"{start_dt.year}H1 (January 1 - June 30, {start_dt.year})"
    # Q1
    elif start_dt.month == 1 and start_dt.day == 1 and end_dt.month == 3 and end_dt.day == 31:
        return f"{start_dt.year}Q1 (January 1 - March 31, {start_dt.year})"
    # Q2
    elif start_dt.month == 4 and start_dt.day == 1 and end_dt.month == 6 and end_dt.day == 30:
        return f"{start_dt.year}Q2 (April 1 - June 30, {start_dt.year})"
    # Q3
    elif start_dt.month == 7 and start_dt.day == 1 and end_dt.month == 9 and end_dt.day == 30:
        return f"{start_dt.year}Q3 (July 1 - September 30, {start_dt.year})"
    # Q4
    elif start_dt.month == 10 and start_dt.day == 1 and end_dt.month == 12 and end_dt.day == 31:
        return f"{start_dt.year}Q4 (October 1 - December 31, {start_dt.year})"
    else:
        return f"{start_date} to {end_date}"


def _parse_github_date(date_str: str) -> datetime:
    """Parse GitHub API date string to datetime."""
    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))


def _extract_pr_info(pr_item: dict) -> dict[str, int | str] | None:
    """Extract PR number, repo, and owner from GitHub API item."""
    html_url = pr_item.get("html_url", "")
    if not html_url:
        return None

    parts = html_url.split("/")
    if len(parts) < 5:
        return None

    return {"number": int(parts[-1]), "repo": parts[4], "owner": parts[3], "html_url": html_url}


def _paginate_github_search(
    url: str, headers: dict[str, str], query: str, description: str
) -> list[dict]:
    """Paginate through GitHub search results."""
    all_items = []
    page = 1

    if RICH_AVAILABLE:
        console = Console()
        with console.status(f"[cyan]{description}...", spinner="dots"):
            while page <= MAX_PAGES:
                params = {
                    "q": query,
                    "per_page": 100,
                    "page": page,
                    "sort": "updated",
                    "order": "desc",
                }

                try:
                    response = requests.get(url, headers=headers, params=params)
                    response.raise_for_status()
                    result = response.json()

                    items = result.get("items", [])
                    if not items:
                        break

                    prs = [item for item in items if "pull_request" in item]
                    all_items.extend(prs)

                    if len(items) < 100:
                        break

                    page += 1

                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 422:
                        break
                    raise
        console.print(f"✓ [green]Found {len(all_items)} items[/green]")
    else:
        print(f"  {description}...", end="", flush=True)
        while page <= MAX_PAGES:
            params = {"q": query, "per_page": 100, "page": page, "sort": "updated", "order": "desc"}

            try:
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                result = response.json()

                items = result.get("items", [])
                if not items:
                    break

                prs = [item for item in items if "pull_request" in item]
                all_items.extend(prs)

                if len(items) < 100:
                    break

                page += 1
                print(".", end="", flush=True)

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 422:
                    break
                raise
        print(f" ✓ Found {len(all_items)} items")

    return all_items


def _filter_reviews_by_user_and_date(
    reviews: list[dict], comments: list[dict], username: str, start_dt: datetime, end_dt: datetime
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Filter reviews and comments by user and date range."""
    filtered_reviews = []
    for review in reviews:
        if review.get("user", {}).get("login") == username:
            submitted_at = review.get("submitted_at")
            if submitted_at:
                review_date = _parse_github_date(submitted_at)
                if start_dt <= review_date <= end_dt:
                    filtered_reviews.append(
                        {
                            "user": username,
                            "body": review.get("body", ""),
                            "state": review.get("state", ""),
                            "submitted_at": submitted_at,
                        }
                    )

    filtered_comments = []
    for comment in comments:
        if comment.get("user", {}).get("login") == username:
            created_at = comment.get("created_at")
            if created_at:
                comment_date = _parse_github_date(created_at)
                if start_dt <= comment_date <= end_dt:
                    filtered_comments.append({"author": username, "body": comment.get("body", "")})

    return filtered_reviews, filtered_comments


def _fetch_reviewed_pr_details(
    pr_info: dict[str, int | str],
    headers: dict[str, str],
    username: str,
    start_dt: datetime,
    end_dt: datetime,
    review_data: dict[str, dict],
) -> None:
    """Fetch PR details, reviews, and comments for a reviewed PR."""
    pr_number = pr_info["number"]
    repo = pr_info["repo"]
    owner = pr_info["owner"]

    try:
        # Fetch PR details
        pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
        pr_response = requests.get(pr_url, headers=headers)
        pr_response.raise_for_status()
        pr_details = pr_response.json()

        # Fetch reviews and comments
        reviews_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        reviews_response = requests.get(reviews_url, headers=headers)
        reviews_response.raise_for_status()
        reviews = reviews_response.json()

        comments_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/comments"
        comments_response = requests.get(comments_url, headers=headers)
        comments_response.raise_for_status()
        comments = comments_response.json()

        # Filter reviews/comments by user and date
        filtered_reviews, filtered_comments = _filter_reviews_by_user_and_date(
            reviews, comments, username, start_dt, end_dt
        )

        if filtered_reviews or filtered_comments:
            review_data["review_data"][str(pr_number)] = {
                "repo": repo,
                "author": pr_details.get("user", {}).get("login", "unknown"),
                "created_at": pr_details.get("created_at", "")[:10]
                if pr_details.get("created_at")
                else "",
                "merged_at": pr_details.get("merged_at"),
                "reviews": filtered_reviews,
                "review_comments": filtered_comments,
            }
            review_data["pr_descriptions"][str(pr_number)] = pr_details.get("body", "")
    except Exception:
        pass  # Skip failed PRs


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
            if user.get("username") == username:
                user_config = user
                break

        if not user_config:
            state["error"] = f"User '{username}' not found in centralized config"
            return state

        # Get organization from top-level config
        organization = centralized_config.get("organization", "EvolutionIQ")

        # Use user config directly
        config = user_config

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
        organization = config.get("organization", "EvolutionIQ")

    state["username"] = config["username"]
    state["organization"] = organization
    state["start_date"] = config.get("start_date", "2025-07-01")
    state["end_date"] = config.get("end_date", "2025-12-31")
    state["analysis_period"] = _format_analysis_period(state["start_date"], state["end_date"])

    # Use output_dir from state (passed from CLI), fallback to config file's parent directory
    if "output_dir" not in state or not state["output_dir"]:
        state["output_dir"] = str(config_path.parent)

    return state


def fetch_github_data(state: AnalysisState) -> AnalysisState:
    """Fetch PR review data from GitHub API."""
    if state.get("error"):
        return state

    username = state["username"]
    organization = state["organization"]
    start_date = state["start_date"]
    end_date = state["end_date"]
    github_token = state.get("github_token") or os.getenv("GITHUB_TOKEN")

    if not github_token:
        state["error"] = "GitHub token required. Set GITHUB_TOKEN environment variable."
        return state

    if not username:
        state["error"] = "Username is required."
        return state

    # Type narrowing: username is guaranteed to be str here
    assert username is not None

    if RICH_AVAILABLE:
        console = Console()
        console.print("🔍 [cyan]Fetching GitHub data...[/cyan]")
    else:
        print("🔍 Fetching GitHub data...")

    headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3+json"}

    # Search for PRs reviewed by user
    query_reviewed = f"org:{organization} reviewed-by:{username} type:pr"
    url = "https://api.github.com/search/issues"

    all_reviewed_prs = _paginate_github_search(
        url, headers, query_reviewed, "Searching for reviewed PRs"
    )

    # Search for PRs authored by user
    query_authored = (
        f"org:{organization} author:{username} type:pr created:{start_date}..{end_date}"
    )
    all_authored_prs = _paginate_github_search(
        url, headers, query_authored, "Searching for authored PRs"
    )

    # Extract PR info from search results
    reviewed_pr_list = []
    for pr_item in all_reviewed_prs:
        pr_info = _extract_pr_info(pr_item)
        if pr_info:
            pr_info["type"] = "reviewed"
            reviewed_pr_list.append(pr_info)

    authored_pr_list = []
    for pr_item in all_authored_prs:
        pr_info = _extract_pr_info(pr_item)
        if pr_info:
            pr_info["type"] = "authored"
            authored_pr_list.append(pr_info)

    state["pr_data"] = reviewed_pr_list
    state["authored_pr_data"] = authored_pr_list

    # Fetch detailed data for each PR
    review_data = {
        "review_data": {},
        "pr_descriptions": {},
        "authored_prs": {},
        "analysis_period": f"Pull Requests Reviewed ({start_date} to {end_date})",
        "start_date": start_date,
        "end_date": end_date,
    }

    start_dt = datetime.fromisoformat(start_date).replace(tzinfo=UTC)
    end_dt = datetime.fromisoformat(end_date + "T23:59:59").replace(tzinfo=UTC)

    # Fetch authored PRs data for significant changes analysis
    authored_pr_list = state.get("authored_pr_data", [])

    for pr_info in authored_pr_list[:MAX_AUTHORED_PRS]:
        pr_number = pr_info["number"]
        repo = pr_info["repo"]
        owner = pr_info["owner"]

        try:
            pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
            pr_response = requests.get(pr_url, headers=headers)
            pr_response.raise_for_status()
            pr_details = pr_response.json()

            created_at = pr_details.get("created_at", "")
            if created_at:
                created_dt = _parse_github_date(created_at)
                if start_dt <= created_dt <= end_dt:
                    review_data["authored_prs"][str(pr_number)] = {
                        "repo": repo,
                        "title": pr_details.get("title", ""),
                        "body": pr_details.get("body", ""),
                        "created_at": created_at[:10],
                        "merged_at": pr_details.get("merged_at"),
                        "additions": pr_details.get("additions", 0),
                        "deletions": pr_details.get("deletions", 0),
                        "changed_files": pr_details.get("changed_files", 0),
                        "html_url": pr_details.get("html_url", ""),
                        "state": pr_details.get("state", ""),
                    }
        except Exception:
            continue

    # Fetch reviewed PRs data
    total_reviewed = min(len(reviewed_pr_list), MAX_REVIEWED_PRS)

    if RICH_AVAILABLE and total_reviewed > 0:
        console = Console()
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Fetching {total_reviewed} reviewed PRs...", total=total_reviewed
            )
            for pr_info in reviewed_pr_list[:MAX_REVIEWED_PRS]:
                _fetch_reviewed_pr_details(
                    pr_info,
                    headers,
                    username,
                    start_dt,
                    end_dt,
                    review_data,  # type: ignore[arg-type]
                )
                progress.update(task, advance=1)
    else:
        if total_reviewed > 0:
            print(f"  Fetching {total_reviewed} reviewed PRs...", end="", flush=True)
        for idx, pr_info in enumerate(reviewed_pr_list[:MAX_REVIEWED_PRS], 1):
            _fetch_reviewed_pr_details(pr_info, headers, username, start_dt, end_dt, review_data)  # type: ignore[arg-type]
            if idx % 10 == 0:
                print(f" {idx}/{total_reviewed}", end="", flush=True)
        if total_reviewed > 0:
            print(f" ✓ Processed {len(review_data['review_data'])} PRs")

    state["review_data"] = review_data

    if RICH_AVAILABLE:
        console = Console()
        console.print(f"✓ [green]Fetched data for {len(review_data['review_data'])} PRs[/green]")
    else:
        print(f"✓ Fetched data for {len(review_data['review_data'])} PRs")

    return state


def analyze_with_vertexai(state: AnalysisState) -> AnalysisState:
    """Analyze review data using Vertex AI."""
    if state.get("error"):
        return state

    review_data = state["review_data"]
    username = state["username"]
    organization = state["organization"]
    analysis_period = state["analysis_period"]

    # Prepare data for analysis
    prs = review_data.get("review_data", {})
    pr_descriptions = review_data.get("pr_descriptions", {})

    # Collect all comments with context
    all_comments = []
    for pr_num, pr_info in prs.items():
        for review in pr_info.get("reviews", []):
            if review.get("body"):
                all_comments.append(
                    {
                        "pr_number": pr_num,
                        "repo": pr_info.get("repo"),
                        "type": "review",
                        "body": review["body"],
                        "state": review.get("state", ""),
                    }
                )
        for comment in pr_info.get("review_comments", []):
            if comment.get("body"):
                all_comments.append(
                    {
                        "pr_number": pr_num,
                        "repo": pr_info.get("repo"),
                        "type": "comment",
                        "body": comment["body"],
                    }
                )

    # Prepare PR details for analysis
    pr_details = []
    for pr_num, pr_info in prs.items():
        pr_details.append(
            {
                "number": pr_num,
                "repo": pr_info.get("repo"),
                "author": pr_info.get("author"),
                "created_at": pr_info.get("created_at"),
                "merged_at": pr_info.get("merged_at"),
                "description": pr_descriptions.get(pr_num, ""),
                "review_count": len(pr_info.get("reviews", [])),
                "comment_count": len(pr_info.get("review_comments", [])),
            }
        )

    # Prepare authored PRs data for significant changes analysis
    authored_prs = review_data.get("authored_prs", {})
    authored_pr_list_for_analysis = []
    for pr_num, pr_info in authored_prs.items():
        authored_pr_list_for_analysis.append(
            {
                "number": pr_num,
                "repo": pr_info.get("repo"),
                "title": pr_info.get("title", ""),
                "body": pr_info.get("body", ""),
                "created_at": pr_info.get("created_at"),
                "merged_at": pr_info.get("merged_at"),
                "additions": pr_info.get("additions", 0),
                "deletions": pr_info.get("deletions", 0),
                "changed_files": pr_info.get("changed_files", 0),
                "html_url": pr_info.get("html_url", ""),
                "state": pr_info.get("state", ""),
            }
        )

    # Initialize Vertex AI
    project = state.get("vertexai_project") or os.getenv("GOOGLE_CLOUD_PROJECT")
    location = state.get("vertexai_location") or os.getenv("GOOGLE_CLOUD_LOCATION", "us-east4")

    if not project:
        state["error"] = (
            "Vertex AI project required. Set GOOGLE_CLOUD_PROJECT environment variable."
        )
        return state

    # Use ChatGoogleGenerativeAI with Vertex AI mode
    # Ensure Vertex AI mode is enabled and set project/location
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
    os.environ["GOOGLE_CLOUD_PROJECT"] = project
    os.environ["GOOGLE_CLOUD_LOCATION"] = location
    # Set quota project to suppress authentication warnings
    os.environ["GOOGLE_CLOUD_QUOTA_PROJECT"] = project

    # Initialize LLM - will use Vertex AI automatically due to env vars
    # The new package uses 'model' parameter, old package uses 'model_name'
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.3)
    except TypeError:
        # Fallback for old API if needed
        llm = ChatGoogleGenerativeAI(
            model_name="gemini-2.5-pro", project=project, location=location, temperature=0.3
        )

    # Load report template
    with open(TEMPLATE_PATH) as f:
        report_template_content = f.read()

    # Load prompt template
    with open(PROMPT_TEMPLATE_PATH) as f:
        prompt_template = Template(f.read())

    # Build prompt with template
    ANALYSIS_SYSTEM_PROMPT = """
    You are an expert at analyzing GitHub PR reviews for engineering performance evaluation.

    Your task is to analyze review data and generate a comprehensive markdown report.

    Be specific, provide examples, and focus on actionable insights.
    """

    # Render prompt template with data
    user_prompt = prompt_template.render(
        username=username,
        organization=organization,
        analysis_period=analysis_period,
        prs_reviewed_count=len(prs),
        total_reviews=sum(len(pr.get("reviews", [])) for pr in prs.values()),
        total_review_comments=sum(len(pr.get("review_comments", [])) for pr in prs.values()),
        authored_prs_count=len(authored_pr_list_for_analysis),
        pr_details_json=json.dumps(pr_details, indent=2),
        review_comments_json=json.dumps(all_comments, indent=2),
        pr_descriptions_json=json.dumps(pr_descriptions, indent=2),
        authored_prs_json=json.dumps(authored_pr_list_for_analysis, indent=2),
        report_template=report_template_content,
    )

    try:
        messages = [
            SystemMessage(content=ANALYSIS_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]

        if RICH_AVAILABLE:
            console = Console()
            console.print("🤖 [cyan]Analyzing with Vertex AI (gemini-2.5-pro)...[/cyan]")
            with console.status("[cyan]Generating analysis report...", spinner="dots"):
                response = llm.invoke(messages)
                content = response.content if hasattr(response, "content") else str(response)
                markdown_report = (
                    content.strip() if isinstance(content, str) else str(content).strip()
                )
        else:
            print("🤖 Analyzing with Vertex AI (gemini-2.5-pro)...")
            print("  Generating analysis report...", end="", flush=True)
            response = llm.invoke(messages)
            content = response.content if hasattr(response, "content") else str(response)
            markdown_report = content.strip() if isinstance(content, str) else str(content).strip()
            print(" ✓")

        # Remove markdown code blocks if present
        if markdown_report.startswith("```"):
            lines = markdown_report.split("\n")
            # Remove opening code block
            if lines[0].startswith("```"):
                lines = lines[1:]
            # Remove closing code block
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            markdown_report = "\n".join(lines)

        # Store the markdown report directly
        state["markdown_report"] = markdown_report
        state["analysis_results"] = {"markdown": markdown_report}  # Keep for compatibility

        if RICH_AVAILABLE:
            console.print("✓ [green]Analysis complete[/green]")
        else:
            print("✓ Analysis complete")

    except Exception as e:
        state["error"] = f"Vertex AI analysis failed: {str(e)}"
        import traceback

        traceback.print_exc()
        return state

    return state


def generate_report(state: AnalysisState) -> AnalysisState:
    """Generate final markdown report - LLM should have filled it, but use Jinja2 as fallback."""
    if state.get("error"):
        return state

    # If LLM already generated complete markdown, use it
    if state.get("markdown_report") and "{{" not in state["markdown_report"]:
        return state

    # Fallback: render template with Jinja2 if LLM didn't fill all placeholders
    fallback_template_path = TEMPLATE_PATH
    with open(fallback_template_path) as f:
        template = Template(f.read())

    analysis = state.get("analysis_results", {})
    review_data = state["review_data"]
    username = state["username"]
    analysis_period = state["analysis_period"]

    prs = review_data.get("review_data", {})
    total_comments = sum(
        len(pr.get("reviews", [])) + len(pr.get("review_comments", [])) for pr in prs.values()
    )

    # Prepare template context with defaults
    template_context = {
        "username": username,
        "analysis_period": analysis_period,
        "executive_summary": analysis.get("executive_summary", "Analysis pending"),
        "prs_reviewed_count": len(prs),
        "architecture_pct": analysis.get("architecture_pct", 0),
        "logic_pct": analysis.get("logic_pct", 0),
        "nits_pct": analysis.get("nits_pct", 0),
        "avg_context_score": analysis.get("avg_context_score", "N/A"),
        "avg_risk_score": analysis.get("avg_risk_score", "N/A"),
        "avg_clarity_score": analysis.get("avg_clarity_score", "N/A"),
        "cross_boundary_count": analysis.get("cross_boundary_count", 0),
        "response_time_range": analysis.get("response_time_range", "N/A"),
        "architecture_count": analysis.get("architecture_count", 0),
        "logic_count": analysis.get("logic_count", 0),
        "nits_count": analysis.get("nits_count", 0),
        "total_comments": total_comments,
        "comment_analysis": analysis.get("comment_analysis", "Analysis pending"),
        "architecture_examples": analysis.get("architecture_examples", "Examples pending"),
        "pr_description_table": analysis.get("pr_description_table", "Table pending"),
        "pr_description_analysis": analysis.get("pr_description_analysis", "Analysis pending"),
        "cross_boundary_table": analysis.get("cross_boundary_table", "Table pending"),
        "cross_boundary_with_comments": analysis.get("cross_boundary_with_comments", 0),
        "cross_boundary_repos_count": analysis.get("cross_boundary_repos_count", 0),
        "cross_boundary_repos": analysis.get("cross_boundary_repos", "N/A"),
        "cross_boundary_nature": analysis.get("cross_boundary_nature", "N/A"),
        "conflict_management_examples": analysis.get(
            "conflict_management_examples", "Examples pending"
        ),
        "conflict_analysis": analysis.get("conflict_analysis", "Analysis pending"),
        "significant_changes": analysis.get(
            "significant_changes", "No significant changes identified"
        ),
        "summary": analysis.get("summary", "Summary pending"),
        "recommendations": analysis.get("recommendations", "Recommendations pending"),
        "template_usage_pct": analysis.get("template_usage_pct", 0),
        "template_fill_pct": analysis.get("template_fill_pct", 0),
    }

    markdown_report = template.render(**template_context)

    state["markdown_report"] = markdown_report
    return state


def save_report(state: AnalysisState) -> AnalysisState:
    """Save the generated report to file."""
    if state.get("error"):
        return state

    if RICH_AVAILABLE:
        console = Console()
        console.print("💾 [cyan]Saving report...[/cyan]")

    output_dir_str = state["output_dir"]
    if not output_dir_str:
        state["error"] = "Output directory is required"
        return state
    output_dir = Path(output_dir_str)
    output_file = output_dir / "github-review-analysis.md"

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        f.write(state["markdown_report"])

    if RICH_AVAILABLE:
        console.print(f"✓ [green]Report saved to: {output_file}[/green]")
    else:
        print(f"✓ Report saved to: {output_file}")

    return state


# Build the workflow graph
workflow = StateGraph(AnalysisState)  # type: ignore[type-arg]

# Add nodes
workflow.add_node("load_config", load_config)
workflow.add_node("fetch_github", fetch_github_data)
workflow.add_node("analyze", analyze_with_vertexai)
workflow.add_node("generate", generate_report)
workflow.add_node("save", save_report)

# Add edges
workflow.set_entry_point("load_config")
workflow.add_edge("load_config", "fetch_github")
workflow.add_edge("fetch_github", "analyze")
workflow.add_edge("analyze", "generate")  # Generate step ensures template is rendered
workflow.add_edge("generate", "save")
workflow.add_edge("save", END)

# Compile the workflow
app = workflow.compile()


def run(
    config_path: str,
    github_token: str | None = None,
    vertexai_project: str | None = None,
    vertexai_location: str | None = None,
    username: str | None = None,
    period: str | None = None,
    output_dir: str | None = None,
):
    """
    Run the PR review analysis workflow.

    Args:
        config_path: Path to user config.json file or centralized config.json
        github_token: GitHub API token (or set GITHUB_TOKEN env var)
        vertexai_project: Google Cloud project ID (or set GOOGLE_CLOUD_PROJECT env var)
        vertexai_location: Vertex AI location (or set GOOGLE_CLOUD_LOCATION env var)
        username: Username to use when config_path points to centralized config.json
        period: Period key (e.g., "2025H2") to use when config_path points to centralized config.json
        output_dir: Output directory for the report (defaults to config file's parent directory)
    """
    # Validate required parameters
    if github_token is None:
        raise ValueError("github_token is required")
    if vertexai_project is None:
        raise ValueError("vertexai_project is required")
    if vertexai_location is None:
        vertexai_location = "us-east4"  # Default location

    initial_state: AnalysisState = {
        "config_path": config_path,
        "username": username or "",  # Only used for centralized config
        "organization": "",  # Will be loaded from config
        "start_date": "",  # Will be loaded from config
        "end_date": "",  # Will be loaded from config
        "analysis_period": "",  # Will be generated from dates
        "period": period,  # Period key (e.g., "2025H2") for centralized config
        "output_dir": output_dir or "",  # Output directory from CLI
        "github_token": github_token,
        "vertexai_project": vertexai_project,
        "vertexai_location": vertexai_location,
        "pr_data": [],
        "authored_pr_data": [],
        "review_data": {},
        "analysis_results": {},
        "markdown_report": "",
        "error": None,
    }

    result = app.invoke(initial_state)

    if result.get("error"):
        raise RuntimeError(result["error"])

    return result
