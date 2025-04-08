import requests
import json
from typing import Optional
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state
from app.middleware.github.GithubAuthMiddleware import check_access
from core.utils.tools import doc_tag  # Importing the doc_tag


@doc_tag("Issues")  # Adding the doc_tag decorator
def get_issue_details_tool(
    issue_number: Annotated[
        int,
        Field(description="The number of the issue to retrieve."),
    ],
    repo: Annotated[
        Optional[str],
        Field(
            description="The GitHub repository in the format 'owner/repo'. This parameter is optional and can also be included in the request headers."
        ),
    ] = None,
) -> str:
    """
    Retrieve the details of a specific issue within a GitHub repository.
    The repo parameter is optional and can also be included in the request headers.

    Args:
    - issue_number (int): The number of the issue to retrieve. This parameter is required.
    - repo (Optional[str]): The GitHub repository in the format 'owner/repo'.

    Returns:
    - JSON string containing the issue details or error.
    """
    logger.info(
        f"Request received to get issue details for repo: {repo}, issue_number: {issue_number}"
    )

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    # Retrieve credentials and repository information
    credentials = global_state.get("middleware.GithubAuthMiddleware.credentials")
    middleware_repo = global_state.get("middleware.GithubAuthMiddleware.repo")

    # Validate repository parameter
    if not repo and not middleware_repo:
        return json.dumps({"error": "Missing required parameters: repo"})

    repo = repo or middleware_repo  # Use middleware_repo if repo is not provided

    # Prepare the URL to get the issue content
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
    headers = {"Authorization": f"token {credentials['access_token']}"}

    logger.info(f"Fetching issue details from GitHub API with URL: {url}")

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
        issue_content = response.json()  # Parse JSON response
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return json.dumps({"error": f"Request failed: {str(e)}"})
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response")
        return json.dumps({"error": "Failed to decode JSON response"})

    logger.info(f"Retrieved issue details for issue number {issue_number}.")
    return json.dumps(issue_content)
