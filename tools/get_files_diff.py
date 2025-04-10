import requests
import json
from typing import List
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state
from app.middleware.github.GithubAuthMiddleware import check_access
from core.utils.tools import doc_tag  # Importing the doc_tag


@doc_tag("Files")  # Adding the doc_tag decorator
def get_file_differences_tool(
    repo: Annotated[
        str,
        Field(
            description="The GitHub repository in the format 'owner/repo'."
        ),
    ],
    sha: Annotated[
        str,
        Field(description="The SHA of the commit to fetch file differences for."),
    ],
    files: Annotated[
        List[str],
        Field(description="List of file names to retrieve diffs for."),
    ],
) -> str:
    """
    Fetch file differences for a specific commit from a GitHub repository.
    The repo parameter is required and must be included in the request headers.

    Args:
    - repo (str): The GitHub repository in the format 'owner/repo'.
    - sha (str): The SHA of the commit.
    - files (List[str]): List of files to retrieve diffs for.

    Returns:
    - JSON string indicating the file differences or error.

    Example Requests:
    - Fetching file differences for files "file1.txt" and "file2.txt" at commit SHA "abc123" in repository "owner/repo":
      get_file_differences_tool(sha="abc123", files=["file1.txt", "file2.txt"], repo="owner/repo")
    - Fetching file differences for files "main.py" and "utils.py" at commit SHA "def456" in repository "anotherUser/repoName":
      get_file_differences_tool(sha="def456", files=["main.py", "utils.py"], repo="anotherUser/repoName")
    """
    logger.info(
        f"Fetching file differences for SHA: {sha}, files: {files}, repo: {repo}"
    )

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    credentials = global_state.get("middleware.GithubAuthMiddleware.credentials", None)

    headers = {"Authorization": f"token {credentials['access_token']}"}
    url = f"https://api.github.com/repos/{repo}/commits/{sha}"

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

    file_changes = [
        {
            "filename": file.get("filename"),
            "status": file.get("status"),
            "additions": file.get("additions", 0),
            "deletions": file.get("deletions", 0),
            "changes": file.get("changes", 0),
            "patch": file.get("patch", "No patch available"),
        }
        for file in commit.get("files", [])
        if file.get("filename") in files
    ]

    logger.info(f"Found {len(file_changes)} file differences for SHA {sha}.")
    return json.dumps({"data": {"sha": sha, "files": file_changes}})
