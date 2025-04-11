import requests
import json
from typing import Optional
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state
from app.middleware.github.GithubAuthMiddleware import check_access
from core.utils.tools import doc_tag


@doc_tag("Repositories")
def find_repositories_by_name_tool(
    query: Annotated[
        str,
        Field(description="The string to search for in repository names."),
    ],
    username: Annotated[
        str,
        Field(description="The GitHub username whose repositories to search."),
    ],
) -> str:
    """
    Search for repositories owned by a specific user that include the given query string.
    Username parameter is optional, if repo is included in request header, the username will be extracted.

    Args:
    - query (str): The string to search for in repository names.
    - username (str): The GitHub username to fetch repositories for.

    Example Request:
    - Searching for repositories with the name "project" for user "johnDoe":
    find_repositories_by_name_tool(query="project", username="johnDoe")

    Returns:
    - JSON string containing the search results or error.
    """
    logger.info(
        f"Searching for repositories owned by `{username}` matching query: {query}"
    )

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    credentials = global_state.get("middleware.GithubAuthMiddleware.credentials", None)
    headers = {"Authorization": f"token {credentials['access_token']}"}
    url = f"https://api.github.com/search/repositories?q={query}+user:{username}"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)

        # Decode and return the search results
        search_results = response.json()
        logger.info(
            f"Found {search_results['total_count']} repositories owned by `{username}` matching query: {query}"
        )
        return {
            "repositories": search_results["items"],
            "total_count": search_results["total_count"],
        }

    except requests.exceptions.RequestException as e:
        # Capture and return the GitHub error message
        try:
            error_details = response.json()
            error_message = error_details.get("message", str(e))
        except json.JSONDecodeError:
            error_message = str(e)

        logger.error(f"GitHub request failed: {error_message}")
        return {"error": error_message}
