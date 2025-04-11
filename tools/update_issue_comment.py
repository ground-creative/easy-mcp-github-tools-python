import requests
import json
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state
from app.middleware.github.GithubAuthMiddleware import check_access
from core.utils.tools import doc_tag  # Importing the doc_tag


@doc_tag("Issues")  # Adding the doc_tag decorator
def update_issue_comment_tool(
    comment_id: Annotated[
        int,
        Field(description="The ID of the comment to update."),
    ],
    new_comment: Annotated[
        str,
        Field(description="The new comment text to replace the existing comment."),
    ],
    repo: Annotated[
        str,
        Field(description="The GitHub repository in the format 'owner/repo'."),
    ],
) -> str:
    """
    Updates an existing comment on a specified issue in a GitHub repository.
    The repo parameter is required and must be included in the request headers.

    Args:
    - comment_id (int): The ID of the comment to update.
    - new_comment (str): The new text for the comment.
    - repo (str): The GitHub repository in the format 'owner/repo'.

    Returns:
    - JSON string containing the updated comment details or error.

    Example Requests:
    - Updating comment 123 in repository "owner/repo":
      update_issue_comment_tool(comment_id=123, new_comment="This is the updated comment.", repo="owner/repo")
    - Updating comment 456 in repository "anotherUser/repoName":
      update_issue_comment_tool(comment_id=456, new_comment="Fixing the previous comment.", repo="anotherUser/repoName")
    """
    logger.info(f"Request received to update comment ID {comment_id} in repo: {repo}")

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    # Retrieve credentials and repository information
    credentials = global_state.get("middleware.GithubAuthMiddleware.credentials")

    # Prepare the URL to update a comment
    url = f"https://api.github.com/repos/{repo}/issues/comments/{comment_id}"
    headers = {
        "Authorization": f"token {credentials['access_token']}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Prepare the updated comment data
    comment_data = {"body": new_comment}

    logger.info(
        f"Updating comment in GitHub API with URL: {url} and data: {comment_data}"
    )

    try:
        response = requests.patch(url, headers=headers, json=comment_data)
        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
        updated_comment = response.json()  # Parse JSON response
    except requests.exceptions.RequestException as e:
        # If GitHub returned an error response, capture and log it
        if response.status_code != 200:
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
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response")
        return {"error": "Failed to decode JSON response"}

    logger.info(f"Comment ID {comment_id} updated successfully.")
    return updated_comment
