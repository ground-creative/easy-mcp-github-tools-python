import requests
import json
from typing import Optional
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state
from app.middleware.github.GithubAuthMiddleware import check_access


def global_search_tool(
    search_type: Annotated[
        str,
        Field(
            description="The type of search to perform (e.g., 'repositories', 'issues', 'pulls', 'code', 'commits', 'users')."
        ),
    ],
    query: Annotated[
        str,
        Field(description="The string to search for."),
    ],
    page: Annotated[
        Optional[int],
        Field(default=1, description="The page number of the results to return."),
    ] = 1,
    per_page: Annotated[
        Optional[int],
        Field(default=30, description="The number of results to return per page."),
    ] = 30,
) -> str:
    """
    Perform a global search on GitHub based on the specified search type and query string.

    Args:
    - search_type (str): The type of search to perform (e.g., 'repositories', 'issues', 'pulls', 'code', 'commits', 'users').
    - query (str): The string to search for.
    - page (int): The page number of the results to return.
    - per_page (int): The number of results to return per page.

    Returns:
    - JSON string containing the search results or error.

    Example Requests:
    - Searching for repositories with the keyword "machine learning":
      global_search_tool(search_type="repositories", query="machine learning")
    - Searching for issues containing the word "bug":
      global_search_tool(search_type="issues", query="bug")
    - Searching for code snippets with the term "authentication":
      global_search_tool(search_type="code", query="authentication", per_page=10)
    - Searching for users with the name "john":
      global_search_tool(search_type="users", query="john", page=2)
    """
    logger.info(
        f"Searching GitHub for {search_type} matching query: {query}, page: {page}, per_page: {per_page}"
    )

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    credentials = global_state.get("middleware.GithubAuthMiddleware.credentials", None)
    headers = {"Authorization": f"token {credentials['access_token']}"}

    # Construct the search URL based on the search type
    if search_type == "repositories":
        url = f"https://api.github.com/search/repositories?q={query}&page={page}&per_page={per_page}"
    elif search_type == "issues":
        url = f"https://api.github.com/search/issues?q={query}&page={page}&per_page={per_page}"
    elif search_type == "pulls":
        url = f"https://api.github.com/search/pulls?q={query}&page={page}&per_page={per_page}"
    elif search_type == "code":
        url = f"https://api.github.com/search/code?q={query}&page={page}&per_page={per_page}"
    elif search_type == "commits":
        url = f"https://api.github.com/search/commits?q={query}&page={page}&per_page={per_page}"
    elif search_type == "users":
        url = f"https://api.github.com/search/users?q={query}&page={page}&per_page={per_page}"
    else:
        return json.dumps(
            {
                "error": "Invalid search type. Please use 'repositories', 'issues', 'pulls', 'code', 'commits', or 'users'."
            }
        )

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
        search_results = response.json()
        logger.info(
            f"Found {search_results['total_count']} results for {search_type} matching query: {query}"
        )
        return json.dumps(
            {
                "results": search_results["items"],
                "total_count": search_results["total_count"],
                "page": page,
                "per_page": per_page,
            }
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"Search request failed for query {query}: {e}")
        return json.dumps(
            {"error": f"Search request failed for query {query}: {str(e)}"}
        )
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON response for query {query}")
        return json.dumps(
            {"error": f"Failed to decode JSON response for query {query}"}
        )
