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
def create_issue_tool(
    repo: Annotated[
        str,
        Field(description="The GitHub repository in the format 'owner/repo'."),
    ],
    title: Annotated[
        str,
        Field(description="The title of the issue to create."),
    ],
    body: Annotated[
        Optional[str],
        Field(description="The body of the issue to create."),
    ] = None,
    labels: Annotated[
        Optional[list],
        Field(description="Optional list of labels to assign to the issue."),
    ] = None,
) -> str:
    """
    Create a new issue within a GitHub repository.

    Args:
    - repo (str): The GitHub repository in the format 'owner/repo'.
    - title (str): The title of the issue to create. This parameter is required.
    - body (Optional[str]): The body of the issue to create.
    - labels (Optional[list]): Optional list of labels to assign to the issue.

    Example Requests:
    - Creating a New Issue:
      create_issue_tool(repo="owner/repo", title="New Issue Title", body="This is the body of the issue.", labels=["bug", "urgent"])

    Returns:
    - JSON string containing the created issue details or error.
    """
    logger.info(
        f"Request received to create issue in repo: {repo}, title: {title}, body: {body}, labels: {labels}"
    )

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    # Retrieve credentials and repository information
    credentials = global_state.get("middleware.GithubAuthMiddleware.credentials")

    # Prepare the URL to create the issue
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {"Authorization": f"token {credentials['access_token']}"}

    # Prepare the issue data
    issue_data = {
        "title": title,
        "body": body,
    }
    if labels:  # Only add labels if they are provided
        issue_data["labels"] = labels

    logger.info(f"Creating issue in GitHub API with URL: {url} and data: {issue_data}")

    try:
        response = requests.post(url, headers=headers, json=issue_data)
        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)

        # If the request is successful, return the issue data
        created_issue = response.json()  # Parse JSON response
        logger.info(f"Created issue with title '{title}'.")
        return created_issue

    except requests.exceptions.RequestException as e:
        # Handle GitHub error responses (e.g., 400, 404, 500)
        error_message = None
        try:
            error_details = response.json()
            if "message" in error_details:
                error_message = error_details["message"]
        except json.JSONDecodeError:
            error_message = "Failed to decode GitHub error response."

        logger.error(f"Request failed: {e}, GitHub error: {error_message}")
        return {"error": f"Request failed: {str(e)}, GitHub error: {error_message}"}

    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response")
        return {"error": "Failed to decode JSON response"}
