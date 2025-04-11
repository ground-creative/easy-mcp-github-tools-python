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
def get_pull_requests_tool(
    repo: Annotated[
        str,
        Field(description="The GitHub repository in the format 'owner/repo'."),
    ],
    state: Annotated[
        Optional[str],
        Field(
            description="Optional state of the pull requests (e.g., 'open', 'closed')."
        ),
    ] = None,
    sort: Annotated[
        Optional[str],
        Field(
            description="Optional sorting criteria (e.g., 'created', 'updated', 'popularity', 'long-running')."
        ),
    ] = None,
    order: Annotated[
        Optional[str],
        Field(description="Optional order of results (e.g., 'asc', 'desc')."),
    ] = None,
    per_page: Annotated[
        Optional[int],
        Field(description="Optional number of pull requests per page."),
    ] = None,
    page: Annotated[
        Optional[int],
        Field(description="Optional page number."),
    ] = None,
) -> str:
    """
    Fetch pull requests from a specified GitHub repository.
    The repo parameter is required and must be included in the request headers.

    Args:
    - repo (str): The GitHub repository in the format 'owner/repo'.
    - state (Optional[str]): Optional state of the pull requests (e.g., 'open', 'closed').
    - sort (Optional[str]): Optional sorting criteria (e.g., 'created', 'updated', 'popularity', 'long-running').
    - order (Optional[str]): Optional order of results (e.g., 'asc', 'desc').
    - per_page (Optional[int]): Optional number of pull requests per page.
    - page (Optional[int]): Optional page number.

    Returns:
    - JSON string containing the list of pull requests or an error message.

    Example Requests:
    - Fetching open pull requests from repository "owner/repo":
      get_pull_requests_tool(repo="owner/repo", state="open")
    - Fetching closed pull requests sorted by creation date from repository "anotherUser/repoName":
      get_pull_requests_tool(repo="anotherUser/repoName", state="closed", sort="created")
    - Fetching pull requests with a specific label from repository "owner/repo":
      get_pull_requests_tool(repo="owner/repo", labels="bug")
    """
    # Log the request details for debugging purposes
    logger.info(
        f"Request received to get pull requests for repo: {repo}, state: {state}, sort: {sort}, order: {order}, per_page: {per_page}, page: {page}"
    )

    # Check authentication before proceeding
    auth_response = check_access(True)
    if auth_response:
        return auth_response  # Return the authentication error if it exists

    # Retrieve credentials and repository information from global state
    credentials = global_state.get("middleware.GithubAuthMiddleware.credentials", None)

    # Prepare the URL for fetching pull requests
    url = f"https://api.github.com/repos/{repo}/pulls"

    # Prepare query parameters for the API request
    params = {}
    if state:
        params["state"] = state
    if sort:
        params["sort"] = sort
    if order:
        params["order"] = order
    if per_page is not None:
        params["per_page"] = per_page
    if page is not None:
        params["page"] = page

    # Set up the request headers with authorization
    headers = {"Authorization": f"token {credentials['access_token']}"}

    # Log the API request details for debugging
    logger.info(
        f"Fetching pull requests from GitHub API with URL: {url} and params: {params}"
    )

    try:
        # Make the API request to fetch pull requests
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")  # Log the error
        return {"error": f"Request failed: {str(e)}"}

    try:
        # Parse the JSON response
        pull_requests = response.json()
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response")  # Log JSON decoding error
        return {"error": "Failed to decode JSON response"}

    # Create a list of pull request details to return
    pull_request_list = [
        {
            "id": pr["id"],
            "title": pr["title"],
            "url": pr["html_url"],
            "state": pr["state"],
            "created_at": pr["created_at"],
            "updated_at": pr["updated_at"],
        }
        for pr in pull_requests
    ]

    # Log the number of pull requests found
    logger.info(f"Found {len(pull_request_list)} pull requests in the repository.")

    # Return the list of pull requests as a JSON string
    return {
        "pull_requests": pull_request_list,
        "total_count": len(pull_request_list),
    }
