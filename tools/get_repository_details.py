import requests
import json
from typing import Optional
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state
from app.middleware.github.GithubAuthMiddleware import check_access
from core.utils.tools import doc_tag  # Importing the doc_tag


@doc_tag("Repositories")  # Adding the doc_tag decorator
def get_repository_details_tool(
    repo: Annotated[
        Optional[str],
        Field(
            description="The GitHub repository in the format 'owner/repo'. This parameter is optional and can also be included in the request headers."
        ),
    ] = None,
) -> str:
    """
    Fetch details for a single repository from GitHub, including tags, branches, and releases.
    The repo parameter is optional, it can also be included in the request headers.

    Args:
    - repo (Optional[str]): The GitHub repository in the format 'owner/repo'.

    Returns:
    - JSON string containing the details of the repository, tags, branches, and releases or error.
    """
    logger.info(f"Fetching details for repository: {repo}")

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    credentials = global_state.get("middleware.GithubAuthMiddleware.credentials", None)
    middleware_repo = global_state.get("middleware.GithubAuthMiddleware.repo", None)

    if not repo and not middleware_repo:
        return json.dumps({"error": "Missing required parameters: repo"})

    if not repo:
        repo = middleware_repo

    headers = {"Authorization": f"token {credentials['access_token']}"}
    url = f"https://api.github.com/repos/{repo}"
    logger.info(f"Sending request to URL: {url}")

    try:
        # Fetch repository details
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
        repository_details = response.json()

        # Fetch tags
        tags_response = requests.get(
            f"https://api.github.com/repos/{repo}/tags", headers=headers
        )
        tags_response.raise_for_status()
        tags = tags_response.json()

        # Fetch branches
        branches_response = requests.get(
            f"https://api.github.com/repos/{repo}/branches", headers=headers
        )
        branches_response.raise_for_status()
        branches = branches_response.json()

        # Fetch releases
        releases_response = requests.get(
            f"https://api.github.com/repos/{repo}/releases", headers=headers
        )
        releases_response.raise_for_status()
        releases = releases_response.json()

        logger.info(f"Fetched details for repository: {repo}")
        return json.dumps(
            {
                "repository_details": repository_details,
                "tags": tags,
                "branches": branches,
                "releases": releases,
            }
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for repository {repo}: {e}")
        return json.dumps({"error": f"Request failed for repository {repo}: {str(e)}"})
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON response for repository {repo}")
        return json.dumps(
            {"error": f"Failed to decode JSON response for repository {repo}"}
        )
