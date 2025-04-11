import requests
import json
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state
from app.middleware.github.GithubAuthMiddleware import check_access
from core.utils.tools import doc_tag  # Importing the doc_tag


@doc_tag("Repositories")  # Adding the doc_tag decorator
def get_repository_details_tool(
    repo: Annotated[
        str,
        Field(description="The GitHub repository in the format 'owner/repo'."),
    ],
) -> str:
    """
    Fetch details for a single repository from GitHub, including tags, branches, and releases.
    The repo parameter is required and must be included in the request headers.

    Args:
    - repo (str): The GitHub repository in the format 'owner/repo'.

    Returns:
    - JSON string containing the details of the repository, tags, branches, and releases or error.

    Example Requests:
    - Fetching details for repository "owner/repo":
      get_repository_details_tool(repo="owner/repo")
    - Fetching details for repository "anotherUser/repoName":
      get_repository_details_tool(repo="anotherUser/repoName")
    """
    logger.info(f"Fetching details for repository: {repo}")

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    credentials = global_state.get("middleware.GithubAuthMiddleware.credentials", None)

    headers = {"Authorization": f"token {credentials['access_token']}"}
    url = f"https://api.github.com/repos/{repo}"
    logger.info(f"Sending request to URL: {url}")

    try:
        # Fetch repository details
        response = requests.get(url, headers=headers)

        # If the response contains an error message, return that directly
        if response.status_code != 200:
            error_message = response.json().get(
                "message", f"Unexpected error: {response.status_code}"
            )
            logger.error(f"GitHub error: {error_message}")
            return {"error": error_message}

        repository_details = response.json()

        # Fetch tags
        tags_response = requests.get(
            f"https://api.github.com/repos/{repo}/tags", headers=headers
        )
        if tags_response.status_code != 200:
            error_message = tags_response.json().get(
                "message", f"Unexpected error: {tags_response.status_code}"
            )
            logger.error(f"GitHub error: {error_message}")
            return {"error": error_message}
        tags = tags_response.json()

        # Fetch branches
        branches_response = requests.get(
            f"https://api.github.com/repos/{repo}/branches", headers=headers
        )
        if branches_response.status_code != 200:
            error_message = branches_response.json().get(
                "message", f"Unexpected error: {branches_response.status_code}"
            )
            logger.error(f"GitHub error: {error_message}")
            return {"error": error_message}
        branches = branches_response.json()

        # Fetch releases
        releases_response = requests.get(
            f"https://api.github.com/repos/{repo}/releases", headers=headers
        )
        if releases_response.status_code != 200:
            error_message = releases_response.json().get(
                "message", f"Unexpected error: {releases_response.status_code}"
            )
            logger.error(f"GitHub error: {error_message}")
            return {"error": error_message}
        releases = releases_response.json()

        logger.info(f"Fetched details for repository: {repo}")
        return {
            "repository_details": repository_details,
            "tags": tags,
            "branches": branches,
            "releases": releases,
        }

    except requests.exceptions.RequestException as e:
        # Directly return the GitHub error response if present
        error_message = response.json().get(
            "message", str(e)
        )  # Get GitHub error message
        logger.error(f"GitHub error: {error_message}")
        return {"error": error_message}

    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON response for repository {repo}")
        return {"error": f"Failed to decode JSON response for repository {repo}"}
