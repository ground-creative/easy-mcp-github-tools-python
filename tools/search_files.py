import requests
import json
from typing import List, Optional
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state
from app.middleware.github.GithubAuthMiddleware import check_access
from core.utils.tools import doc_tag  # Importing the doc_tag


@doc_tag("Files")  # Adding the doc_tag decorator
def search_files_tool(
    search_string: Annotated[
        str,
        Field(description="The string to search files for in the GitHub repository."),
    ],
    repo: Annotated[
        str,
        Field(description="The GitHub repository in the format 'owner/repo'."),
    ],
    folders: Annotated[
        Optional[List[str]],
        Field(description="Optional list of folders to restrict the search."),
    ] = None,
    sort: Annotated[
        Optional[str], Field(description="The sort field. Can be 'indexed' or 'stars'.")
    ] = None,
    order: Annotated[
        Optional[str],
        Field(description="The order to sort results. Can be 'asc' or 'desc'."),
    ] = None,
    page: Annotated[
        Optional[int], Field(description="The page number of the results to fetch.")
    ] = 1,
    per_page: Annotated[
        Optional[int], Field(description="The number of results per page.")
    ] = 30,  # Default value for results per page
) -> str:
    """
    Search for a specific string in the files of a GitHub repository in the main branch.

    Args:
    - search_string (str): The string to search for in the GitHub repository.
    - repo (str): The GitHub repository in the format 'owner/repo'.
    - folders (Optional[List[str]]): Optional list of folders to restrict the search.
    - sort (Optional[str]): The sort field. Can be 'indexed' or 'stars'.
    - order (Optional[str]): The order to sort results. Can be 'asc' or 'desc'.
    - page (Optional[int]): The page number of the results to fetch.
    - per_page (Optional[int]): The number of results per page.

    Returns:
    - JSON string indicating the matching files or error.

    Example Requests:
    - Searching for the term "authentication" in repository "owner/repo":
      search_files_tool(search_string="authentication", repo="owner/repo")
    - Searching for the term "API" in a specific folder in repository "anotherUser/repoName":
      search_files_tool(search_string="API", repo="anotherUser/repoName", folders=["src"])
    - Searching for the term "bug" in repository "exampleUser/repo" and sorting by stars:
      search_files_tool(search_string="bug", repo="exampleUser/repo", sort="stars", order="desc")
    - Searching for the term "feature" in repository "owner/repo" with pagination:
      search_files_tool(search_string="feature", repo="owner/repo", page=2, per_page=50)
    """
    logger.info(
        f"Search request received for string: `{search_string}` in repo: {repo}, folders: {folders}, page: {page}, per_page: {per_page}, sort: {sort}, order: {order}"
    )

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    credentials = global_state.get("middleware.GithubAuthMiddleware.credentials", None)

    # Prepare the search URL
    url = f"https://api.github.com/search/code?q={search_string}+in:file+repo:{repo}"

    if folders:
        folder_query = "+".join(folders)
        url += f"+path:{folder_query}"

    # Add sorting and pagination parameters
    if sort:
        url += f"&sort={sort}"
    if order:
        url += f"&order={order}"
    url += f"&page={page}&per_page={per_page}"

    headers = {"Authorization": f"token {credentials['access_token']}"}

    logger.info(f"Searching GitHub API with URL: {url}")

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return {"error": f"Request failed: {str(e)}"}

    try:
        search_results = response.json()
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response")
        return {"error": "Failed to decode JSON response"}

    matching_files = [
        {
            "name": item.get("name", "Unknown"),
            "path": item.get("path", "Unknown"),
            "url": item.get("html_url", "#"),
        }
        for item in search_results.get("items", [])
    ]

    logger.info(
        f"Found {len(matching_files)} matching files for the string '{search_string}'."
    )

    return {
        "matching_files": matching_files,
        "total_count": len(matching_files),
    }
