import requests
import json
import base64
from typing import List
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state
from app.middleware.github.GithubAuthMiddleware import check_access
from core.utils.tools import doc_tag  # Importing the doc_tag


@doc_tag("Files")  # Adding the doc_tag decorator
def get_files_before_commit_tool(
    sha: Annotated[
        str,
        Field(description="The current commit SHA."),
    ],
    files: Annotated[
        List[str],
        Field(description="List of target file names to retrieve."),
    ],
    repo: Annotated[
        str,
        Field(
            description="The GitHub repository in the format 'owner/repo'."
        ),
    ],
) -> str:
    """
    Retrieve multiple content from multiple files before a given commit SHA.
    The repo parameter is required and must be included in the request headers.

    Args:
    - sha (str): The current commit SHA.
    - files (List[str]): List of target file names to retrieve.
    - repo (str): The GitHub repository in the format 'owner/repo'.

    Returns:
    - JSON string indicating files details such as size, name, and URL, and the total files count.

    Example Requests:
    - Fetching files "file1.txt" and "file2.txt" before commit SHA "abc123" in repository "owner/repo":
      get_files_before_commit_tool(sha="abc123", files=["file1.txt", "file2.txt"], repo="owner/repo")
    - Fetching files "main.py" and "utils.py" before commit SHA "def456" in repository "anotherUser/repoName":
      get_files_before_commit_tool(sha="def456", files=["main.py", "utils.py"], repo="anotherUser/repoName")
    """
    logger.info(
        f"Retrieving files before commit SHA: {sha}, files: {files}, repo: {repo}"
    )

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    credentials = global_state.get("middleware.GithubAuthMiddleware.credentials", None)
    middleware_repo = global_state.get("middleware.GithubAuthMiddleware.repo", None)

    # Determine the repository to use
    if not repo and not middleware_repo:
        return json.dumps({"error": "Missing required parameters: repo"})

    if not repo:
        repo = middleware_repo

    if not isinstance(files, list) or len(files) == 0:
        return json.dumps({"error": "file names must be a non-empty list"})

    headers = {"Authorization": f"token {credentials['access_token']}"}

    # Step 1: Get commit details to find the parent SHA
    commit_url = f"https://api.github.com/repos/{repo}/commits/{sha}"
    logger.info(f"Fetching commit details from: {commit_url}")

    commit_response = requests.get(commit_url, headers=headers)
    if commit_response.status_code != 200:
        return json.dumps({"error": f"GitHub API error: {commit_response.text}"})

    commit_data = commit_response.json()
    parent_sha = commit_data.get("parents", [{}])[0].get("sha")

    if not parent_sha:
        return json.dumps(
            {"error": "No parent commit found. This might be the first commit."}
        )

    files_data = []

    # Step 2: Fetch each file's metadata and content from the parent commit
    for filename in files:
        file_url = (
            f"https://api.github.com/repos/{repo}/contents/{filename}?ref={parent_sha}"
        )
        logger.info(f"Fetching file before commit from: {file_url}")

        file_response = requests.get(file_url, headers=headers)
        if file_response.status_code != 200:
            files_data.append(
                {
                    "filename": filename,
                    "error": f"GitHub API error: {file_response.text}",
                }
            )
            continue

        file_data = file_response.json()
        file_content_encoded = file_data.get("content", "")
        file_content = (
            base64.b64decode(file_content_encoded).decode("utf-8")
            if file_content_encoded
            else "File content not available"
        )

        files_data.append(
            {
                "filename": filename,
                "html_url": file_data.get("html_url", ""),
                "size": file_data.get("size", ""),
                "content": (
                    file_content
                    if file_data.get("size", 0) < 50000
                    else "file size exceeds 50000 bytes, use html_url to view file."
                ),
            }
        )

    logger.info(f"Found {len(files_data)} files.")
    return json.dumps({"data": {"sha": parent_sha, "files": files_data}})
