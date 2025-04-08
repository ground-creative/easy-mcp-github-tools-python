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
    pull_number: Annotated[
        int,
        Field(description="The number of the pull request to merge."),
    ],
    repo: Annotated[
        Optional[str],
        Field(
            description="The GitHub repository in the format 'owner/repo'. This parameter is optional and can also be included in the request headers."
        ),
    ] = None,
    commit_message: Annotated[
        Optional[str], Field(description="Optional commit message for the merge.")
    ] = None,
) -> str:
    """
    Merge a specific pull request in a GitHub repository.
    The repo parameter is optional and can also be included in the request headers.

    Args:
    - pull_number (int): The number of the pull request to merge.
    - repo (Optional[str]): The GitHub repository in the format 'owner/repo'.
    - commit_message (Optional[str]): Optional commit message for the merge.

    Returns:
    - JSON string containing the response from the GitHub API or an error message.
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
    middleware_repo = global_state.get("middleware.GithubAuthMiddleware.repo", None)

    # Use the middleware repository if no specific repo is provided
    if not repo:
        repo = middleware_repo

    # Validate repository parameter
    if not repo:
        return json.dumps({"error": "Missing required parameters: repo"})

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
        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return json.dumps({"error": f"Request failed: {str(e)}"})

    try:
        # Parse the JSON response
        merge_response = response.json()
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response")
        return json.dumps({"error": "Failed to decode JSON response"})

    # Log the response from merging the pull request
    logger.info(f"Successfully merged pull request #{pull_number}: {merge_response}")

    # Return the response as a JSON string
    return json.dumps(merge_response)
