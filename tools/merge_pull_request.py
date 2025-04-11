import requests
import json
from typing import Optional
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger for logging information
from core.utils.state import global_state  # Importing global state management
from app.middleware.github.GithubAuthMiddleware import (
    check_access,
)  # Importing authentication check
from core.utils.tools import doc_tag  # Importing the doc_tag


@doc_tag("Pull Requests")  # Adding the doc_tag decorator
def merge_pull_request_tool(
    repo: Annotated[
        str,
        Field(description="The GitHub repository in the format 'owner/repo'."),
    ],
    pull_number: Annotated[
        int,
        Field(description="The number of the pull request to merge."),
    ],
    commit_message: Annotated[
        Optional[str], Field(description="Optional commit message for the merge.")
    ] = None,
) -> str:
    """
    Merge a specific pull request in a GitHub repository.
    The repo parameter is required and must be included in the request headers.

    Args:
    - repo (str): The GitHub repository in the format 'owner/repo'.
    - pull_number (int): The number of the pull request to merge.
    - commit_message (Optional[str]): Optional commit message for the merge.

    Returns:
    - JSON string containing the response from the GitHub API or an error message.

    Example Requests:
    - Merging pull request number 42 in repository "owner/repo":
      merge_pull_request_tool(pull_number=42, repo="owner/repo")
    - Merging pull request number 10 in repository "anotherUser/repoName" with a custom commit message:
      merge_pull_request_tool(pull_number=10, repo="anotherUser/repoName", commit_message="Merging feature branch")
    """
    logger.info(
        f"Request received to merge pull request #{pull_number} in repo: {repo}"
    )

    # Check authentication before proceeding
    auth_response = check_access(True)
    if auth_response:
        return auth_response  # Return the authentication error if it exists

    # Retrieve credentials and repository information from global state
    credentials = global_state.get("middleware.GithubAuthMiddleware.credentials", None)

    # Prepare the URL for merging the pull request
    url = f"https://api.github.com/repos/{repo}/pulls/{pull_number}/merge"
    headers = {"Authorization": f"token {credentials['access_token']}"}

    # Prepare the payload for the merge
    payload = {}
    if commit_message:
        payload["commit_message"] = commit_message

    # Log the API request details for debugging
    logger.info(f"Merging pull request with URL: {url} and payload: {payload}")

    try:
        # Make the API request to merge the pull request
        response = requests.put(url, headers=headers, json=payload)
        merge_response = response.json()  # Parse the JSON response early

        # Raise for HTTP errors after parsing to capture body info in logs
        response.raise_for_status()

    except requests.exceptions.HTTPError as http_err:
        error_message = merge_response.get("message", str(http_err))
        logger.error(f"HTTP error during PR merge: {error_message}")
        return {"error": error_message}

    except requests.exceptions.RequestException as req_err:
        logger.error(f"Request failed: {req_err}")
        return {"error": f"Request failed: {str(req_err)}"}

    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response")
        return {"error": "Failed to decode JSON response"}

    # Handle logical error: response is 200 but merge did not happen
    if not merge_response.get("merged", False):
        message = merge_response.get("message", "Pull request was not merged.")
        logger.warning(f"Merge failed logically: {message}")
        return {"error": message}

    logger.info(f"Successfully merged pull request #{pull_number}: {merge_response}")
    return merge_response
