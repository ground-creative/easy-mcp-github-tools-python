import requests
import json
from typing import List, Optional
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state
from app.middleware.github.GithubAuthMiddleware import check_access


def get_files_details_tool(
    file_paths: Annotated[
        List[str],
        Field(description="List of file paths to fetch details for."),
    ],
    repo: Annotated[
        Optional[str],
        Field(description="The GitHub repository in the format 'owner/repo'."),
    ] = None,
) -> str:
    """
    Fetch details for multiple files from a GitHub repository. The repo parameter is optional, it can also be included in the request headers.

    Args:
    - file_paths (List[str]): List of file paths to fetch details for.
    - repo (Optional[str]): The GitHub repository in the format 'owner/repo'. This parameter is optional, it can also be included with the request headers.

    Returns:
    - JSON string indicating the files details or error.
    """
    logger.info(f"File details request received for repo: {repo}, files: {file_paths}")

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

    if not file_paths:
        logger.error("Required parameter `files_paths` missing")
        return json.dumps({"error": "Required parameter `files_paths` missing"})

    headers = {"Authorization": f"token {credentials['access_token']}"}
    file_details = []

    for file_path in file_paths:
        url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
        logger.info(f"Fetching details for file: {file_path} from URL: {url}")

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
            file_details.append(response.json())
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
