import requests
import json
from typing import List, Optional
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state
from app.middleware.github.GithubAuthMiddleware import check_access


def get_commits_tool(
    repo: Annotated[
        Optional[str],
        Field(
            description="Optional, the GitHub repository in the format 'owner/repo'."
        ),
    ] = None,
    branch: Annotated[
        Optional[str],
        Field(
            default="main", description="Optional, the branch to fetch commits from."
        ),
    ] = "main",
    path: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Optional, specify file or folder path for commits.",
        ),
    ] = None,
    per_page: Annotated[
        Optional[int],
        Field(
            default=15, description="Optional, number of commits to return per page."
        ),
    ] = 15,
    since: Annotated[
        Optional[str],
        Field(
            default=None,
            description=(
                "Optional, fetch commits since this timestamp in ISO 8601 format (e.g., "
                "'2023-10-10T14:30:00Z')."
            ),
        ),
    ] = None,
    until: Annotated[
        Optional[str],
        Field(
            default=None,
            description=(
                "Optional, fetch commits until this timestamp in ISO 8601 format (e.g., "
                "'2023-10-10T14:30:00Z')."
            ),
        ),
    ] = None,
) -> str:
    """
    Fetch commit history from a GitHub repository. The repo parameter is optional, it can also be included in the request headers.

    Args:
    - repo (Optional[str]): The GitHub repository in the format 'owner/repo'. This parameter is optional, it can also be included with the request headers.
    - branch (Optional[str]): The branch to fetch commits from. Default is 'main'.
    - path (Optional[str]): Specific file or folder path.
    - per_page (Optional[int]): Number of commits to return per page. Default is 15.
    - since (Optional[str]): Fetch commits since this timestamp in ISO 8601 format (e.g., '2023-10-10T14:30:00Z').
    - until (Optional[str]): Fetch commits until this timestamp in ISO 8601 format (e.g., '2023-10-10T14:30:00Z').

    Returns:
    - JSON string indicating the commits or error.
    """
    logger.info(
        f"Received request to fetch commits for repo: {repo}, branch: {branch}, path: {path}, per_page: {per_page}, since: {since}, until: {until}"
    )

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    credentials = global_state.get("middleware.GithubAuthMiddleware.credentials", None)
    middleware_repo = global_state.get("middleware.GithubAuthMiddleware.repo", None)

    if not repo and not middleware_repo:
        return json.dumps({"error": "Missing required parameters: repo"})

    if not repo:
        repo = middleware_repo

    # Ensure per_page is a positive integer
    if per_page <= 0:
        return json.dumps(
            {"error": "Invalid value for per_page. It must be a positive integer."}
        )

    headers = {"Authorization": f"token {credentials['access_token']}"}

    # Building the base URL
    url = (
        f"https://api.github.com/repos/{repo}/commits?sha={branch}&per_page={per_page}"
    )

    if since:
        url += f"&since={since}"

    if until:
        url += f"&until={until}"  # Add the until parameter if provided

    # Optional: If path is provided, include it
    if path:
        url += f"&path={path}"

    logger.info(f"Fetching commits from GitHub API with URL: {url}")

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return json.dumps({"error": f"Request failed: {str(e)}"})

    try:
        commits = response.json()
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response")
        return json.dumps({"error": "Failed to decode JSON response"})

    commit_list = [
        {
            "sha": commit.get("sha", "N/A"),
            "message": commit.get("commit", {}).get("message", "No message"),
            "author": (
                f"{commit.get('commit', {}).get('author', {}).get('name', 'Unknown')} "
                f"[@{commit.get('author', {}).get('login', 'N/A')}]"
                f"(https://github.com/{commit.get('author', {}).get('login', 'N/A')})"
                if commit.get("author")
                else "Unknown Author"
            ),
            "committer": (
                f"{commit.get('commit', {}).get('committer', {}).get('name', 'Unknown')} "
                f"[@{commit.get('committer', {}).get('login', 'N/A')}]"
                f"(https://github.com/{commit.get('committer', {}).get('login', 'N/A')})"
                if commit.get("committer")
                else "Unknown Committer"
            ),
            "date": commit.get("commit", {})
            .get("committer", {})
            .get("date", "Unknown"),
            "url": commit.get("html_url", "#"),
        }
        for commit in commits
    ]

    logger.info(f"Found {len(commit_list)} commits for the given request.")
    return json.dumps({"commits": commit_list, "total_count": len(commit_list)})
