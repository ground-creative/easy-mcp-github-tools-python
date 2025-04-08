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
        Optional[str],
        Field(description="The GitHub username whose repositories to search."),
    ],
) -> str:
    """
    Search for repositories owned by a specific user that include the given query string.
    Username parameter is optional, if repo is included in request header, the username will be extracted.

    Args:
    - query (str): The string to search for in repository names.
    - username (Optional[str]): The GitHub username to fetch repositories for.

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

    credentials = global_state.get("middleware.GithubAuthMiddleware.credentials", None)
    headers = {"Authorization": f"token {credentials['access_token']}"}
    url = f"https://api.github.com/search/repositories?q={query}+user:{username}"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
        search_results = response.json()
        logger.info(
            f"Found {search_results['total_count']} repositories owned by `{username}` matching query: {query}"
        )
        return json.dumps(
            {
                "repositories": search_results["items"],
                "total_count": search_results["total_count"],
            }
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"Search request failed for query {query} by user {username}: {e}")
        return json.dumps(
            {
                "error": f"Search request failed for query {query} by user {username}: {str(e)}"
            }
        )
    except json.JSONDecodeError:
        logger.error(
            f"Failed to decode JSON response for query {query} by user {username}"
        )
        return json.dumps(
            {
                "error": f"Failed to decode JSON response for query {query} by user {username}"
            }
        )
