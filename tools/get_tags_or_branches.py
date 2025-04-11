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
def get_tags_or_branches_tool(
    type: Annotated[
        str,
        Field(
            description="Specify 'tags' to list tags or 'branches' to list branches."
        ),
    ],
    repo: Annotated[
        str,
        Field(description="The GitHub repository in the format 'owner/repo'."),
    ],
    per_page: Annotated[
        Optional[int],
        Field(description="Optional number of items per page."),
    ] = None,
    page: Annotated[
        Optional[int],
        Field(description="Optional page number."),
    ] = None,
) -> str:
    """
    List either tags or branches in a GitHub repository.
    The repo parameter is required and must be included in the request headers.

    Args:
    - type (str): Specify 'tags' to list tags or 'branches' to list branches.
    - repo (str): The GitHub repository in the format 'owner/repo'.
    - per_page (Optional[int]): Optional number of items per page.
    - page (Optional[int]): Optional page number.

    Returns:
    - JSON string containing the list of tags or branches or error.

    Example Requests:
    - Fetching tags for repository "owner/repo":
      get_tags_or_branches_tool(type="tags", repo="owner/repo")
    - Fetching branches for repository "anotherUser/repoName":
      get_tags_or_branches_tool(type="branches", repo="anotherUser/repoName")
    """
    logger.info(f"Request received to list {type} for repo: {repo}")

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    credentials = global_state.get("middleware.GithubAuthMiddleware.credentials", None)

    # Prepare the URL based on the type
    if type == "tags":
        url = f"https://api.github.com/repos/{repo}/git/refs/tags"
    elif type == "branches":
        url = f"https://api.github.com/repos/{repo}/branches"
    else:
        return {"error": "Invalid type specified. Use 'tags' or 'branches'."}

    headers = {"Authorization": f"token {credentials['access_token']}"}

    # Prepare query parameters for pagination
    params = {}
    if per_page is not None:
        params["per_page"] = per_page
    if page is not None:
        params["page"] = page

    logger.info(f"Fetching {type} from GitHub API with URL: {url} and params: {params}")

    try:
        response = requests.get(url, headers=headers, params=params)

        # Check for GitHub errors directly by inspecting the response status
        if response.status_code != 200:
            error_message = response.json().get(
                "message", f"Unexpected error: {response.status_code}"
            )
            logger.error(f"GitHub error: {error_message}")
            return {"error": error_message}

        # Proceed with parsing the response if no error
        items = response.json()

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return {"error": f"Request failed: {str(e)}"}

    try:
        if type == "tags":
            item_list = [
                {
                    "tag": item["ref"].replace("refs/tags/", ""),
                    "commit_sha": item["object"]["sha"],
                    "url": item["object"]["url"],
                }
                for item in items
            ]
        else:  # type == 'branches'
            item_list = [
                {
                    "name": item["name"],
                    "commit_sha": item["commit"]["sha"],
                    "url": item["commit"]["url"],
                }
                for item in items
            ]
    except (KeyError, TypeError):
        logger.error("Unexpected structure in GitHub API response")
        return {"error": "Unexpected structure in GitHub API response"}

    logger.info(f"Found {len(item_list)} {type} in the repository.")

    return {
        type: item_list,
        "total_count": len(item_list),
    }
