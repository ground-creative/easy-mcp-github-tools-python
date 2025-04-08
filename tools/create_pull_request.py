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
    repo: Annotated[
        Optional[str],
        Field(
            description="The GitHub repository in the format 'owner/repo'. This parameter is optional and can also be included in the request headers."
        ),
    ] = None,
    title: Annotated[
        Optional[str], Field(description="The title of the pull request.")
    ] = "Update branch",
    body: Annotated[
        Optional[str], Field(description="The body of the pull request.")
    ] = "Merging changes from base branch.",
) -> str:
    """
    Creates a pull request in a specified GitHub repository by merging changes from one branch to another.
    The repo parameter is optional and can also be included in the request headers.

    Args:
    - target_branch (str): The name of the branch to update.
    - base_branch (Optional[str]): The base branch from which to merge changes (default is 'main').
    - repo (Optional[str]): The GitHub repository in the format 'owner/repo'.
    - title (Optional[str]): The title of the pull request.
    - body (Optional[str]): The body of the pull request.

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
    middleware_repo = global_state.get("middleware.GithubAuthMiddleware.repo")

    # Validate repository parameter
    if not repo and not middleware_repo:
        return json.dumps({"error": "Missing required parameters: repo"})

    repo = repo or middleware_repo  # Use middleware_repo if repo is not provided

    # Prepare the URL to create a pull request
    create_pr_url = f"https://api.github.com/repos/{repo}/pulls"
    headers = {"Authorization": f"token {credentials['access_token']}"}

    # Prepare the payload for the pull request
    payload = {"title": title, "head": target_branch, "base": base_branch, "body": body}

    logger.info(f"Creating pull request in GitHub API with URL: {create_pr_url}")

    try:
        # Send the request to create the pull request
        create_response = requests.post(create_pr_url, headers=headers, json=payload)
        create_response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return json.dumps({"error": f"Request failed: {str(e)}"})
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response")
        return json.dumps({"error": "Failed to decode JSON response"})

    logger.info(
        f"Pull request created successfully to update branch '{target_branch}' in repository '{repo}'."
    )
    return json.dumps(
        {
            "message": f"Pull request created successfully to update branch '{target_branch}'.",
            "pull_request_url": create_response.json().get("html_url"),
        }
    )
