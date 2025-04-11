from typing import List, Optional
from typing_extensions import Annotated
from pydantic import Field
import requests
import json
from core.utils.logger import logger
from core.utils.state import global_state
from app.middleware.github.GithubAuthMiddleware import check_access
from core.utils.tools import doc_tag


@doc_tag("Commits")
def get_commit_details_tool(
    repo: Annotated[
        str,
        Field(description="The GitHub repository in the format 'owner/repo'."),
    ],
    sha: Annotated[
        str,
        Field(description="The SHA of the commit to fetch details for."),
    ],
    files: Annotated[
        Optional[List[str]],
        Field(description="Optional list of filenames to return diffs for."),
    ] = None,
) -> dict:
    """
    Fetch commit details or file diffs from a GitHub repository.

    If `files` is provided, returns diffs only for those files. Otherwise, returns general commit info.

    Args:
    - repo (str): The GitHub repository in the format 'owner/repo'.
    - sha (str): The SHA of the commit.
    - files (Optional[List[str]]): Optional list of filenames to filter diffs.

    Returns:
    - JSON response with commit details or file diffs.

    Example Requests:
    - Fetching details for commit SHA "abc123" in repository "owner/repo":
      get_commit_details_tool(repo="owner/repo", sha="abc123")
    - Fetching diffs for specific files in commit SHA "abc123" in repository "owner/repo":
      get_commit_info_tool(repo="owner/repo", sha="abc123", files=["src/main.py", "README.md"])
    """
    logger.info(
        f"Fetching commit info for repo: {repo}, SHA: {sha}, files filter: {files}"
    )

    auth_response = check_access(True)
    if auth_response:
        return auth_response

    credentials = global_state.get("middleware.GithubAuthMiddleware.credentials", None)
    headers = {"Authorization": f"token {credentials['access_token']}"}
    url = f"https://api.github.com/repos/{repo}/commits/{sha}"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)

        # If the request is successful, return the response data
        commit = response.json()

    except requests.exceptions.RequestException as e:
        # Capture and return the GitHub error message
        try:
            error_details = response.json()
            error_message = error_details.get("message", str(e))
        except json.JSONDecodeError:
            error_message = str(e)

        logger.error(f"GitHub request failed: {error_message}")
        return {"error": error_message}

    if files:
        file_diffs = [
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
        logger.info(f"Returning diffs for {len(file_diffs)} filtered files.")
        return {"data": {"sha": sha, "files": file_diffs}}

    # No files filter: return full commit info
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

    logger.info(f"Returning full commit details for SHA {sha}")
    return {"commit": commit_details}
