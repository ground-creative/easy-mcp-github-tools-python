import requests
import json
from typing import List, Optional
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state
from app.middleware.github.GithubAuthMiddleware import check_access
from core.utils.tools import doc_tag  # Importing the doc_tag


@doc_tag("Files")  # Adding the doc_tag decorator
def get_files_details_tool(
    repo: Annotated[
        str,
        Field(description="The GitHub repository in the format 'owner/repo'."),
    ],
    files: Annotated[
        List[str],
        Field(
            description="List of file names to fetch details for. Ex: ['lib/file1.txt', 'assets/file2.txt']"
        ),
    ],
    branch: Annotated[
        Optional[str],
        Field(
            description="Optional branch name to fetch files from. Defaults to the repository's default branch."
        ),
    ] = None,
) -> str:
    """
    Fetch details for multiple files from a GitHub repository without the content.
    The repo parameter is required and must be included in the request headers.

    Args:
    - repo (str): The GitHub repository in the format 'owner/repo'.
    - files (List[str]): List of file names to fetch details for. Ex: ['lib/file1.txt', 'assets/file2.txt']
    - branch (Optional[str]): Optional branch name to fetch files from. Defaults to the repository's default branch.

    Returns:
    - JSON string indicating the files details or error.

    Example Requests:
    - Fetching details for files "file1.txt" and "file2.txt" in repository "owner/repo":
      get_files_details_tool(files=["file1.txt", "file2.txt"], repo="owner/repo")
    - Fetching details for files "main.py" and "helper.py" in repository "anotherUser/repoName":
      get_files_details_tool(files=["main.py", "helper.py"], repo="anotherUser/repoName", branch="develop")
    """
    logger.info(
        f"File details request received for repo: {repo}, files: {files}, branch: {branch}"
    )

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    credentials = global_state.get("middleware.GithubAuthMiddleware.credentials", None)
    headers = {"Authorization": f"token {credentials['access_token']}"}

    # If branch is not provided, fetch the default branch name
    branch = branch or get_default_branch(repo, headers)
    if isinstance(branch, dict):  # If the branch is an error response
        return branch

    # Fetch file details
    file_details = []
    for file_path in files:
        file_metadata = fetch_file_metadata(repo, file_path, branch, headers)
        if "error" in file_metadata:
            return file_metadata  # Return error immediately if encountered

        file_details.append(file_metadata)

    logger.info(f"Fetched details for {len(file_details)} files.")
    return {"file_details": file_details, "total_count": len(file_details)}


def get_default_branch(repo: str, headers: dict) -> Optional[str]:
    """
    Fetch the default branch of the repository.

    Args:
    - repo (str): The GitHub repository in the format 'owner/repo'.
    - headers (dict): Headers containing authentication token.

    Returns:
    - str: The default branch name or error message.
    """
    branch_url = f"https://api.github.com/repos/{repo}/branches"
    try:
        branch_response = requests.get(branch_url, headers=headers)
        branch_response.raise_for_status()

        # Return the default branch name
        return branch_response.json()[0]["name"]
    except requests.exceptions.RequestException as e:
        error_message = f"Request failed for default branch: {e}"
        logger.error(error_message)
        return {"error": error_message}
    except (json.JSONDecodeError, IndexError) as e:
        error_message = f"Failed to decode or parse default branch response: {e}"
        logger.error(error_message)
        return {"error": error_message}


def fetch_file_metadata(repo: str, file_path: str, branch: str, headers: dict) -> dict:
    """
    Fetch metadata for a single file from the GitHub repository.

    Args:
    - repo (str): The GitHub repository in the format 'owner/repo'.
    - file_path (str): The path to the file in the repository.
    - branch (str): The branch to fetch the file from.
    - headers (dict): Headers containing authentication token.

    Returns:
    - dict: File metadata or error message.
    """
    url = f"https://api.github.com/repos/{repo}/contents/{file_path}?ref={branch}"
    logger.info(f"Fetching details for file: {file_path} from URL: {url}")

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Create a dictionary with only the necessary metadata
        file_info = response.json()
        return {
            "name": file_info.get("name"),
            "path": file_info.get("path"),
            "size": file_info.get("size"),
            "type": file_info.get("type"),
            "url": file_info.get("html_url"),
        }
    except requests.exceptions.RequestException as e:
        error_message = f"Request failed for {file_path}: {e}"
        logger.error(error_message)
        return {"error": error_message}
    except json.JSONDecodeError:
        error_message = f"Failed to decode JSON response for {file_path}"
        logger.error(error_message)
        return {"error": error_message}
