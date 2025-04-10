import requests
import json
from typing import Optional
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state
from core.utils.tools import doc_tag
from app.middleware.github.GithubAuthMiddleware import check_access


@doc_tag("Branches")
def create_branch_tool(
    repo: Annotated[
        str,
        Field(
            description="The GitHub repository in the format 'owner/repo'. This parameter is required."
        ),
    ],
    new_branch: Annotated[
        str,
        Field(description="The name of the new branch to create."),
    ],
    base_branch: Annotated[
        Optional[str],
        Field(
            description="The base branch from which to create the new branch (default is 'main')."
        ),
    ] = "main",
) -> str:
    """
    Creates a new branch in a specified GitHub repository based on an existing branch.

    Args:
    - repo (str): The GitHub repository in the format 'owner/repo'.
    - new_branch (str): The name of the new branch to create.
    - base_branch (Optional[str]): The base branch from which to create the new branch (default is 'main').

    Example Requests:
    - Creating a New Branch from Main:
      create_branch_tool(new_branch="feature-branch", repo="owner/repo")
    - Creating a New Branch from a Specific Base Branch:
      create_branch_tool(new_branch="feature-branch", base_branch="develop", repo="owner/repo")

    Returns:
    - JSON string indicating success or error.
    """
    logger.info(
        f"Request received to create branch '{new_branch}' from base branch '{base_branch}' in repo: {repo}"
    )

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    # Retrieve credentials and repository information
    credentials = global_state.get("middleware.GithubAuthMiddleware.credentials")

    # Prepare the URL to get the SHA of the base branch
    url = f"https://api.github.com/repos/{repo}/git/refs/heads/{base_branch}"
    headers = {"Authorization": f"token {credentials['access_token']}"}

    try:
        # Get the current base branch details
        base_branch_response = requests.get(url, headers=headers)
        base_branch_response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
        base_branch_info = base_branch_response.json()  # Parse JSON response
        base_branch_sha = base_branch_info["object"]["sha"]
        logger.info(f"Base branch SHA: {base_branch_sha}")

        # Prepare the payload to create the new branch
        create_branch_url = f"https://api.github.com/repos/{repo}/git/refs"
        payload = {"ref": f"refs/heads/{new_branch}", "sha": base_branch_sha}

        logger.info(f"Creating new branch in GitHub API with URL: {create_branch_url}")

        # Send the request to create the new branch
        create_response = requests.post(
            create_branch_url, headers=headers, json=payload
        )
        create_response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return json.dumps({"error": f"Request failed: {str(e)}"})
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response")
        return json.dumps({"error": "Failed to decode JSON response"})

    logger.info(f"Branch '{new_branch}' created successfully in repository '{repo}'.")
    return json.dumps(
        {
            "message": f"Branch '{new_branch}' created successfully.",
            "base_branch": base_branch,
        }
    )
