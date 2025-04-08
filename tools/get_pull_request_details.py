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
def get_pull_request_details_tool(
    pull_number: Annotated[
        int,
        Field(description="The number of the pull request to retrieve details for."),
    ],
    repo: Annotated[
        Optional[str],
        Field(
            description="The GitHub repository in the format 'owner/repo'. This parameter is optional and can also be included in the request headers."
        ),
    ] = None,
) -> str:
    """
    Fetch detailed information about a specific pull request from a GitHub repository.
    The repo parameter is optional and can also be included in the request headers.

    Args:
    - pull_number (int): The number of the pull request to retrieve details for.
    - repo (Optional[str]): The GitHub repository in the format 'owner/repo'.

    Returns:
    - JSON string containing the pull request details or an error message.
    """
    logger.info(
        f"Request received to get details for pull request #{pull_number} in repo: {repo}"
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

    # Prepare the URL for fetching pull request details
    url = f"https://api.github.com/repos/{repo}/pulls/{pull_number}"
    headers = {"Authorization": f"token {credentials['access_token']}"}

    # Log the API request details for debugging
    logger.info(f"Fetching pull request details from GitHub API with URL: {url}")

    try:
        # Make the API request to fetch pull request details
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return json.dumps({"error": f"Request failed: {str(e)}"})

    try:
        # Parse the JSON response
        pull_request_details = response.json()
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response")
        return json.dumps({"error": "Failed to decode JSON response"})

    # Log the details retrieved
    logger.info(
        f"Retrieved details for pull request #{pull_number}: {pull_request_details}"
    )

    # Return the pull request details as a JSON string
    return json.dumps(pull_request_details)
