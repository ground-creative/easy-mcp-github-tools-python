import requests
import json
from typing import List, Optional
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state
from app.middleware.github.GithubAuthMiddleware import check_access
from core.utils.tools import doc_tag  # Importing the doc_tag


@doc_tag("Repositories")  # Adding the doc_tag decorator
def get_repositories_tool(
    username: Annotated[
        Optional[str],
        Field(description="The GitHub username to fetch repositories for."),
    ],
    type: Annotated[
        Optional[str],
        Field(
            description="Optional type of repositories to fetch: all, owner, public, private, member."
        ),
    ] = "all",
    sort: Annotated[
        Optional[str],
        Field(
            description="Optional sorting method: created, updated, pushed, full_name."
        ),
    ] = "full_name",
    direction: Annotated[
        Optional[str], Field(description="Optional direction for sorting: asc or desc.")
    ] = "asc",
    page: Annotated[
        Optional[int], Field(description="Page number to fetch (default is 1).")
    ] = 1,
    per_page: Annotated[
        Optional[int],
        Field(
            description="Number of repositories per page (default is 30, max is 100)."
        ),
    ] = 30,
) -> str:
    """
    Fetch all repositories for a specific GitHub user, handling pagination.
    Username parameter is optional, if repo is included in request header, the username will be extracted.

    Args:
    - username (Optional[str]): The GitHub username to fetch repositories for.
    - type (Optional[str]): Type of repositories to fetch (default is 'all').
    - sort (Optional[str]): Sorting method (default is 'full_name').
    - direction (Optional[str]): Sorting direction (default is 'asc').
    - page (Optional[int]): Page number to fetch (default is 1).
    - per_page (Optional[int]): Number of repositories per page (default is 30, max is 100).

    Returns:
    - JSON string containing the list of repositories or error.
    """
    logger.info(
        f"Fetching repositories for user: {username}, type: {type}, sort: {sort}, direction: {direction}, page: {page}, per_page: {per_page}"
    )

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    credentials = global_state.get("middleware.GithubAuthMiddleware.credentials", None)
    middleware_repo = global_state.get("middleware.GithubAuthMiddleware.repo", None)

    if not username:

        if middleware_repo:
            username = middleware_repo.split("/")[0]  # Get the part before the slash
        else:
            return json.dumps(
                {
                    "error": "Missing required parameter: username",
                }
            )

    headers = (
        {"Authorization": f"token {credentials['access_token']}"} if credentials else {}
    )

    # Prepare the API request URL
    url = f"https://api.github.com/users/{username}/repos?type={type}&sort={sort}&direction={direction}&page={page}&per_page={per_page}"

    try:
        logger.info(f"Sending request to URL: {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
        repositories = response.json()

        logger.info(f"Fetched {len(repositories)} repositories for user: {username}.")
        return json.dumps(
            {"repositories": repositories, "total_count": len(repositories)}
        )

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for user {username}: {e}")
        return json.dumps({"error": f"Request failed for user {username}: {str(e)}"})
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON response for user {username}")
        return json.dumps(
            {"error": f"Failed to decode JSON response for user {username}"}
        )
