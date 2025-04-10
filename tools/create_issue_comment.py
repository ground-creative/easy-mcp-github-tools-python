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
def create_issue_comment_tool(
    repo: Annotated[
        str,
        Field(
            description="The GitHub repository in the format 'owner/repo'."
        ),
    ],
    issue_number: Annotated[
        int,
        Field(
            description="The number of the issue to which the comment will be added."
        ),
    ],
    comment: Annotated[
        str,
        Field(description="The comment text to add to the issue."),
    ],
) -> str:
    """
    Adds a comment to a specified issue in a GitHub repository.

    Args:
    - repo (str): The GitHub repository in the format 'owner/repo'.
    - issue_number (int): The number of the issue to which the comment will be added.
    - comment (str): The text of the comment to add.

    Example Requests:
    - Adding a Comment to an Issue:
      create_issue_comment_tool(repo="owner/repo", issue_number=123, comment="This is a comment on the issue.")

    Returns:
    - JSON string containing the created comment details or error.
    """
    logger.info(
        f"Request received to add comment to issue number {issue_number} in repo: {repo}"
    )

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    # Retrieve credentials and repository information
    credentials = global_state.get("middleware.GithubAuthMiddleware.credentials")

    # Prepare the URL to add a comment
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    headers = {
        "Authorization": f"token {credentials['access_token']}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Prepare the comment data
    comment_data = {"body": comment}

    logger.info(
        f"Adding comment in GitHub API with URL: {url} and data: {comment_data}"
    )

    try:
        response = requests.post(url, headers=headers, json=comment_data)
        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
        created_comment = response.json()  # Parse JSON response
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return json.dumps({"error": f"Request failed: {str(e)}"})
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response")
        return json.dumps({"error": "Failed to decode JSON response"})

    logger.info(f"Comment added to issue number {issue_number}.")
    return json.dumps(created_comment)