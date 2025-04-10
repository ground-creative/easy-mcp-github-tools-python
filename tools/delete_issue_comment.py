import requests
import json
import base64  # Importing base64 for encoding and decoding
import time  # Importing time for handling timestamps
from typing import Optional
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state
from app.middleware.github.GithubAuthMiddleware import check_access
from core.utils.tools import doc_tag  # Importing the doc_tag

# Define the validity duration for the confirmation token (in seconds)
CONFIRMATION_TOKEN_VALIDITY_DURATION = 5 * 60  # 5 minutes


@doc_tag("Issues")  # Adding the doc_tag decorator
def delete_issue_comment_tool(
    repo: Annotated[
        str,
        Field(
            description="The GitHub repository in the format 'owner/repo'."
        ),
    ],
    comment_id: Annotated[
        int,
        Field(description="The ID of the comment to delete."),
    ],
    confirmation_token: Annotated[
        Optional[str],
        Field(
            description="An optional token to confirm the deletion. If not provided, a token will be generated based on the comment ID and repository parameters. This token must be used to confirm the deletion request."
        ),
    ] = None,
) -> str:
    """
    Deletes a specified comment on an issue in a GitHub repository.

    This function first checks if a confirmation token is provided. If not, it generates a token based on the comment ID and repository parameters.
    The user must then confirm the deletion using this token. If the token is provided, the function validates it against the original request parameters before proceeding with the deletion.
    The token is valid for a specified duration.

    Args:
    - repo (str): The GitHub repository in the format 'owner/repo'.
    - comment_id (int): The ID of the comment to delete.
    - confirmation_token (Optional[str]): An optional token to confirm the deletion. If not provided, a token will be generated based on the comment ID and repository.

    Examples Correct Request:
    
    User: "Delete comment 123 for repository owner/repo"
    # Generate confirmation token to use for next request
    Assistant Action: `delete_issue_comment_tool(repo="owner/repo", comment_id=123)`
    Assistant Response: "Please confirm deletion of comment 123"
    User: "I confirm"
    # Use the confirmation token from the previous request
    Assistant Action: `delete_issue_comment_tool(repo="owner/repo", comment_id=123, confirmation_token="XXXYYY")`
    Assistant Response: "The comment 123 was deleted successfully."

    Examples Incorrect Request:
    
    Example 1:
    User: "Delete comment 123 for repository owner/repo"
    Assistant Action: `delete_issue_comment_tool(repo="owner/repo", comment_id=123, confirmation_token="made_up_token")`
    Server Response: Error: Invalid confirmation token. Please provide a valid token to confirm deletion.
    What went wrong: Instead of requesting a token and asking for confirmation, a made-up token was sent.
    Example 2:
    User: "Delete comment 123 for repository owner/repo"
    # Generate confirmation token to use for next request
    Assistant Action: `delete_issue_comment_tool(repo="owner/repo", comment_id=123)`
    Assistant Action: `delete_issue_comment_tool(repo="owner/repo", comment_id=123, confirmation_token="XXXYYY")`
    What went wrong: Confirmation token was used without asking for confirmation.

    Returns:
    - JSON string indicating success or error.
    """
    logger.info(
        f"Request received to delete comment ID {comment_id} in repo: {repo} with confirmation token: {confirmation_token}"
    )

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    # Retrieve credentials and repository information
    credentials = global_state.get("middleware.GithubAuthMiddleware.credentials")

    # Generate a confirmation token if not provided
    if not confirmation_token:
        # Create a string with the request parameters and current timestamp
        params_string = f"{comment_id}:{repo}:{int(time.time())}"
        confirmation_token = base64.b64encode(params_string.encode()).decode()
        logger.info(f"Generated confirmation token: {confirmation_token}")
        return json.dumps(
            {
                "message": f"Confirmation required to delete comment ID {comment_id}. Once confirmed, use the given confirmation_token with the same request parameters.",
                "confirmation_token": confirmation_token,
                "action": "confirm_deletion",
            }
        )

    # Decode and validate the confirmation token
    try:
        decoded_params = base64.b64decode(confirmation_token).decode()
        token_comment_id, token_repo, token_timestamp = decoded_params.split(":")
        token_timestamp = int(token_timestamp)

        # Check if the token has expired
        if time.time() - token_timestamp > CONFIRMATION_TOKEN_VALIDITY_DURATION:
            return json.dumps(
                {"error": "Confirmation token has expired. Please request a new token."}
            )

        # Check if the parameters match
        if int(token_comment_id) != comment_id or token_repo != repo:
            return json.dumps(
                {
                    "error": "Invalid confirmation token. Paramters do not match, please request a new token.",
                    "details": {
                        "token_params": {
                            "comment_id": token_comment_id,
                            "repo": token_repo,
                        },
                        "request_params": {
                            "comment_id": comment_id,
                            "repo": repo,
                        },
                    },
                }
            )
    except Exception as e:
        logger.error(f"Failed to decode confirmation token: {e}")
        return json.dumps({"error": "Invalid confirmation token."})

    # Prepare the URL to delete a comment
    url = f"https://api.github.com/repos/{repo}/issues/comments/{comment_id}"
    headers = {
        "Authorization": f"token {credentials['access_token']}",
        "Accept": "application/vnd.github.v3+json",
    }

    logger.info(f"Deleting comment in GitHub API with URL: {url}")

    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return json.dumps({"error": f"Request failed: {str(e)}"})

    logger.info(f"Comment ID {comment_id} deleted successfully.")
    return json.dumps({"message": "Comment deleted successfully."})
