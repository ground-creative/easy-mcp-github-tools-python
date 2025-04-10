import requests
import json
from typing import List
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state
from app.middleware.github.GithubAuthMiddleware import check_access
from core.utils.tools import doc_tag  # Importing the doc_tag


@doc_tag("Commits")  # Adding the doc_tag decorator
def get_commit_details_tool(
    repo: Annotated[
        str,
        Field(description="The GitHub repository in the format 'owner/repo'."),
    ],
    sha: Annotated[
        str,
        Field(description="The SHA of the commit to fetch details for."),
    ],
) -> str:
    """
    Fetch detailed information for a specific commit from a GitHub repository.

    Args:
    - repo (str): The GitHub repository in the format 'owner/repo'.
    - sha (str): The SHA of the commit to fetch details for.

    Returns:
    - JSON string indicating the commit details or error.

    Example Requests:
    - Fetching details for commit SHA "abc123" in repository "owner/repo":
      get_commit_details_tool(repo="owner/repo", sha="abc123")
    - Fetching details for commit SHA "def456" in repository "anotherUser/repoName":
      get_commit_details_tool(repo="anotherUser/repoName", sha="def456")
    """
    logger.info(f"Fetching commit details for repo: {repo}, SHA: {sha}")

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    credentials = global_state.get("middleware.GithubAuthMiddleware.credentials", None)

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
