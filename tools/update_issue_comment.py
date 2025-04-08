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
        Optional[str],
        Field(
            description="The GitHub repository in the format 'owner/repo'. This parameter is optional and can also be included in the request headers."
        ),
    ] = None,
) -> str:
    """
    Updates an existing comment on a specified issue in a GitHub repository.
    The repo parameter is optional and can also be included in the request headers.

    Args:
    - comment_id (int): The ID of the comment to update.
    - new_comment (str): The new text for the comment.
    - repo (Optional[str]): The GitHub repository in the format 'owner/repo'.

    Returns:
    - JSON string containing the updated comment details or error.
    """
    logger.info(f"Request received to update comment ID {comment_id} in repo: {repo}")

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
        logger.error(f"Request failed: {e}")
        return json.dumps({"error": f"Request failed: {str(e)}"})
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response")
        return json.dumps({"error": "Failed to decode JSON response"})

    logger.info(f"Comment ID {comment_id} updated successfully.")
    return json.dumps(updated_comment)
