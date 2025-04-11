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
    repo: Annotated[
        str,
        Field(description="The GitHub repository in the format 'owner/repo'."),
    ],
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
) -> str:
    """
    Updates an existing issue in a GitHub repository by modifying its title, body, state (open or closed), and labels.
    The repo parameter is required and must be included in the request headers.

    Args:
    - issue_number (int): The number of the issue to update.
    - title (Optional[str]): The new title of the issue.
    - body (Optional[str]): The new body of the issue.
    - state (Optional[str]): The state of the issue (open or closed).
    - labels (Optional[list]): Optional list of labels to assign to the issue.
    - repo (str): The GitHub repository in the format 'owner/repo'.

    Returns:
    - JSON string containing the updated issue details or error.

    Example Requests:
    - Updating issue number 123 in repository "owner/repo":
      update_issue_tool(issue_number=123, title="New Title", body="Updated issue body.", repo="owner/repo")
    - Closing issue number 456 in repository "anotherUser/repoName":
      update_issue_tool(issue_number=456, state="closed", repo="anotherUser/repoName")
    - Adding labels to issue number 789 in repository "exampleUser/repo":
      update_issue_tool(issue_number=789, labels=["bug", "urgent"], repo="exampleUser/repo")
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
        return {"error": "Missing required parameters: repo"}

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
        if response.status_code != 200:  # Check if GitHub returned an error
            try:
                error_message = response.json().get("message", "No message provided")
                logger.error(f"GitHub error: {error_message}")
                return {"error": f"GitHub error: {error_message}"}
            except json.JSONDecodeError:
                logger.error(
                    f"GitHub returned an error, but the response could not be parsed: {response.text}"
                )
                return {"error": f"GitHub error: {response.text}"}
        logger.error(f"Request failed: {e}")
        return {"error": f"Request failed: {str(e)}"}

    logger.info(f"Updated issue number {issue_number}.")
    return updated_issue
