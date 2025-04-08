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
def update_issue_tool(
    issue_number: Annotated[
        int,
        Field(description="The number of the issue to update."),
    ],
    title: Annotated[
        Optional[str],
        Field(description="The new title of the issue."),
    ] = None,
    body: Annotated[
        Optional[str],
        Field(description="The new body of the issue."),
    ] = None,
    state: Annotated[
        Optional[str],
        Field(description="The state of the issue (open or closed)."),
    ] = None,
    labels: Annotated[
        Optional[list],
        Field(description="Optional list of labels to assign to the issue."),
    ] = None,
    repo: Annotated[
        Optional[str],
        Field(
            description="The GitHub repository in the format 'owner/repo'. This parameter is optional and can also be included in the request headers."
        ),
    ] = None,
) -> str:
    """
    Updates an existing issue in a GitHub repository by modifying its title, body, state (open or closed), and labels.
    The repo parameter is optional and can also be included in the request headers.

    Args:
    - issue_number (int): The number of the issue to update.
    - title (Optional[str]): The new title of the issue.
    - body (Optional[str]): The new body of the issue.
    - state (Optional[str]): The state of the issue (open or closed).
    - labels (Optional[list]): Optional list of labels to assign to the issue.
    - repo (Optional[str]): The GitHub repository in the format 'owner/repo'.

    Returns:
    - JSON string containing the updated issue details or error.
    """
    logger.info(
        f"Request received to update issue number {issue_number} in repo: {repo}, title: {title}, body: {body}, state: {state}, labels: {labels}"
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

    # Prepare the URL to update the issue
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
    headers = {
        "Authorization": f"token {credentials['access_token']}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Prepare the issue data
    issue_data = {}
    if title:
        issue_data["title"] = title
    if body:
        issue_data["body"] = body
    if state:
        issue_data["state"] = state
    if labels:
        issue_data["labels"] = labels

    logger.info(f"Updating issue in GitHub API with URL: {url} and data: {issue_data}")

    try:
        response = requests.patch(url, headers=headers, json=issue_data)
        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
        updated_issue = response.json()  # Parse JSON response
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return json.dumps({"error": f"Request failed: {str(e)}"})
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response")
        return json.dumps({"error": "Failed to decode JSON response"})

    logger.info(f"Updated issue number {issue_number}.")
    return json.dumps(updated_issue)
