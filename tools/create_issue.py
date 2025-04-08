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
    title: Annotated[
        str,
        Field(description="The title of the issue to create."),
    ],
    body: Annotated[
        Optional[str],
        Field(description="The body of the issue to create."),
    ] = None,
    repo: Annotated[
        Optional[str],
        Field(
            description="The GitHub repository in the format 'owner/repo'. This parameter is optional and can also be included in the request headers."
        ),
    ] = None,
    labels: Annotated[
        Optional[list],
        Field(description="Optional list of labels to assign to the issue."),
    ] = None,
) -> str:
    """
    Create a new issue within a GitHub repository.
    The repo parameter is optional and can also be included in the request headers.

    Args:
    - title (str): The title of the issue to create. This parameter is required.
    - body (Optional[str]): The body of the issue to create.
    - repo (Optional[str]): The GitHub repository in the format 'owner/repo'.
    - labels (Optional[list]): Optional list of labels to assign to the issue.

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
    middleware_repo = global_state.get("middleware.GithubAuthMiddleware.repo")

    # Validate repository parameter
    if not repo and not middleware_repo:
        return json.dumps({"error": "Missing required parameters: repo"})

    repo = repo or middleware_repo  # Use middleware_repo if repo is not provided

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
        created_issue = response.json()  # Parse JSON response
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return json.dumps({"error": f"Request failed: {str(e)}"})
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response")
        return json.dumps({"error": "Failed to decode JSON response"})

    logger.info(f"Created issue with title '{title}'.")
    return json.dumps(created_issue)