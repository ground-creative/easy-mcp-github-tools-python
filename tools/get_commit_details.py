import requests
import json
from typing import List, Optional
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state
from app.middleware.github.GithubAuthMiddleware import check_access


def get_commit_details_tool(
    sha: Annotated[
        str,
        Field(description="The SHA of the commit to fetch details for."),
    ],
    repo: Annotated[
        Optional[str],
        Field(description="The GitHub repository in the format 'owner/repo'."),
    ] = None,
) -> str:
    """
    Fetch detailed information for a specific commit from a GitHub repository. The repo parameter is optional, it can also be included in the request headers.

    Args:
    - sha (str): The SHA of the commit to fetch details for.
    - repo (Optional[str]): The GitHub repository in the format 'owner/repo'. This parameter is optional, it can also be included with the request headers.

    Returns:
    - JSON string indicating the commit details or error.
    """
    logger.info(f"Fetching commit details for repo: {repo}, SHA: {sha}")

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

    headers = {"Authorization": f"token {credentials['access_token']}"}

    # Building the URL to fetch commit details
    url = f"https://api.github.com/repos/{repo}/commits/{sha}"

    # Log the URL that will be used to fetch commit details
    logger.info(f"Fetching commit details from GitHub API with URL: {url}")

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return json.dumps({"error": f"Request failed: {str(e)}"})

    try:
        commit = response.json()
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response")
        return json.dumps({"error": "Failed to decode JSON response"})

    commit_details = {
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
        "date": commit.get("commit", {}).get("committer", {}).get("date", "Unknown"),
        "url": commit.get("html_url", "#"),
        "files": [
            {
                "filename": file.get("filename", "Unknown"),
                "status": file.get("status", "Unknown"),
                "additions": file.get("additions", 0),
                "deletions": file.get("deletions", 0),
                "changes": file.get("changes", 0),
            }
            for file in commit.get("files", [])
        ],
    }

    # Log the retrieved commit details
    logger.info(f"Found commit details for SHA {sha}.")
    return json.dumps({"commit": commit_details})
