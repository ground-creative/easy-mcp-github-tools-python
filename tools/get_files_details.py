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
    files: Annotated[
        List[str],
        Field(
            description="List of file names to fetch details for. Ex: ['lib/file1.txt', 'assets/file2.txt']"
        ),
    ],
    repo: Annotated[
        Optional[str],
        Field(
            description="The GitHub repository in the format 'owner/repo'. This parameter is optional and can also be included in the request headers."
        ),
    ] = None,
    branch: Annotated[
        Optional[str],
        Field(
            description="Optional branch name to fetch files from. Defaults to the repository's default branch."
        ),
    ] = None,
) -> str:
    """
    Fetch details for multiple files from a GitHub repository without the content.
    The repo parameter is optional, it can also be included in the request headers.

    Args:
    - files (List[str]): List of file names to fetch details for. Ex: ['lib/file1.txt', 'assets/file2.txt']
    - repo (Optional[str]): The GitHub repository in the format 'owner/repo'.
    - branch (Optional[str]): Optional branch name to fetch files from. Defaults to the repository's default branch.

    Returns:
    - JSON string indicating the files details or error.
    """
    logger.info(
        f"File details request received for repo: {repo}, files: {files}, branch: {branch}"
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

    if not files:
        logger.error("Required parameter `files` missing")
        return json.dumps({"error": "Required parameter `files` missing"})

    headers = {"Authorization": f"token {credentials['access_token']}"}
    file_details = []

    # If branch is not provided, fetch the default branch name
    if not branch:
        branch_url = f"https://api.github.com/repos/{repo}/branches"
        branch_response = requests.get(branch_url, headers=headers)

        if branch_response.status_code != 200:
            return json.dumps({"error": f"GitHub API error: {branch_response.text}"})

        branch = branch_response.json()[0]["name"]  # Get the default branch name

    for file_path in files:
        url = f"https://api.github.com/repos/{repo}/contents/{file_path}?ref={branch}"
        logger.info(f"Fetching details for file: {file_path} from URL: {url}")

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
            file_info = response.json()

            # Create a dictionary with only the necessary metadata
            file_metadata = {
                "name": file_info.get("name"),
                "path": file_info.get("path"),
                "size": file_info.get("size"),
                "type": file_info.get("type"),
                "url": file_info.get("html_url"),
            }
            file_details.append(file_metadata)
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {file_path}: {e}")
            return json.dumps({"error": f"Request failed for {file_path}: {str(e)}"})
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON response for {file_path}")
            return json.dumps(
                {"error": f"Failed to decode JSON response for {file_path}"}
            )

    logger.info(f"Fetched details for {len(file_details)} files.")
    return json.dumps({"file_details": file_details, "total_count": len(file_details)})
