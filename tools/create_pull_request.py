import requests
import json
from typing import Optional
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state
from app.middleware.github.GithubAuthMiddleware import check_access
from core.utils.tools import doc_tag  # Importing the doc_tag


@doc_tag("Pull Requests")  # Adding the doc_tag decorator
def create_pull_request_tool(
    repo: Annotated[
        str,
        Field(description="The GitHub repository in the format 'owner/repo'."),
    ],
    target_branch: Annotated[
        str,
        Field(description="The name of the branch to update."),
    ],
    base_branch: Annotated[
        Optional[str],
        Field(
            description="The base branch from which to merge changes (default is 'main')."
        ),
    ] = "main",
    title: Annotated[
        Optional[str], Field(description="The title of the pull request.")
    ] = "Update branch",
    body: Annotated[
        Optional[str], Field(description="The body of the pull request.")
    ] = "Merging changes from base branch.",
) -> str:
    """
    Creates a pull request in a specified GitHub repository by merging changes from one branch to another.

    Args:
    - repo (str): The GitHub repository in the format 'owner/repo'.
    - target_branch (str): The name of the branch to update.
    - base_branch (Optional[str]): The base branch from which to merge changes (default is 'main').
    - title (Optional[str]): The title of the pull request.
    - body (Optional[str]): The body of the pull request.

    Example Requests:
    - Creating a Pull Request:
      create_pull_request_tool(repo="owner/repo", target_branch="feature-branch", base_branch="main", title="New Feature", body="Merging new feature into main branch.")

    Returns:
    - JSON string indicating success or error.
    """
    logger.info(
        f"Request received to create pull request to update branch '{target_branch}' from base branch '{base_branch}' in repo: {repo}"
    )

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    # Retrieve credentials and repository information
    credentials = global_state.get("middleware.GithubAuthMiddleware.credentials")

    # Prepare the URL to create a pull request
    create_pr_url = f"https://api.github.com/repos/{repo}/pulls"
    headers = {"Authorization": f"token {credentials['access_token']}"}

    # Prepare the payload for the pull request
    payload = {"title": title, "head": target_branch, "base": base_branch, "body": body}

    logger.info(
        f"Creating pull request in GitHub API with URL: {create_pr_url} {payload}"
    )

    try:
        # Send the request to create the pull request
        create_response = requests.post(create_pr_url, headers=headers, json=payload)
        create_response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)

    except requests.exceptions.RequestException as e:
        # Log detailed information about the error
        error_message = f"Request failed: {str(e)}"

        # Check if we have a response to log
        if create_response is not None:
            try:
                error_details = (
                    create_response.json()
                )  # Get the error details from GitHub response
            except json.JSONDecodeError:
                error_details = (
                    create_response.text
                )  # If JSON parsing fails, fall back to plain text response

            logger.error(f"{error_message}. GitHub API response: {error_details}")
            return {"error": error_message, "details": error_details}
        else:
            # If no response is available, just log the error
            logger.error(error_message)
            return {"error": error_message}

    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response from GitHub API")
        return {"error": "Failed to decode JSON response"}

    logger.info(
        f"Pull request created successfully to update branch '{target_branch}' in repository '{repo}'."
    )
    return {
        "message": f"Pull request created successfully to update branch '{target_branch}'.",
        "pull_request_url": create_response.json().get("html_url"),
    }
