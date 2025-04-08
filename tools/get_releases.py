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
def get_releases_tool(
    per_page: Annotated[
        Optional[int],
        Field(description="Optional number of releases per page."),
    ] = None,
    page: Annotated[
        Optional[int],
        Field(description="Optional page number."),
    ] = None,
    repo: Annotated[
        Optional[str],
        Field(
            description="The GitHub repository in the format 'owner/repo'. This parameter is optional and can also be included in the request headers."
        ),
    ] = None,
    sort: Annotated[
        Optional[str],
        Field(description="Optional sorting criteria (e.g., 'created', 'updated')."),
    ] = None,
    order: Annotated[
        Optional[str],
        Field(description="Optional order of results (e.g., 'asc', 'desc')."),
    ] = None,
) -> str:
    """
    Retrieve releases within a GitHub repository.
    The repo parameter is optional and can also be included in the request headers.

    Args:
    - per_page (Optional[int]): Optional number of releases per page.
    - page (Optional[int]): Optional page number.
    - repo (Optional[str]): The GitHub repository in the format 'owner/repo'.
    - sort (Optional[str]): Optional sorting criteria (e.g., 'created', 'updated').
    - order (Optional[str]): Optional order of results (e.g., 'asc', 'desc').

    Returns:
    - JSON string containing the list of releases or error.
    """
    logger.info(
        f"Request received to retrieve releases for repo: {repo}, per_page: {per_page}, page: {page}, sort: {sort}, order: {order}"
    )

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

    # Prepare the URL
    url = f"https://api.github.com/repos/{repo}/releases"
    params = {}
    if per_page is not None:
        params["per_page"] = per_page
    if page is not None:
        params["page"] = page
    if sort:
        params["sort"] = sort
    if order:
        params["order"] = order

    headers = {"Authorization": f"token {credentials['access_token']}"}

    logger.info(
        f"Retrieving releases from GitHub API with URL: {url} and params: {params}"
    )

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return json.dumps({"error": f"Request failed: {str(e)}"})

    try:
        releases = response.json()
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response")
        return json.dumps({"error": "Failed to decode JSON response"})

    release_list = [
        {
            "id": release["id"],
            "tag_name": release["tag_name"],
            "name": release["name"],
            "url": release["html_url"],
            "published_at": release["published_at"],
        }
        for release in releases
    ]

    logger.info(f"Found {len(release_list)} releases in the repository.")

    return json.dumps(
        {
            "data": {
                "releases": release_list,
                "total_count": len(release_list),
            }
        }
    )
