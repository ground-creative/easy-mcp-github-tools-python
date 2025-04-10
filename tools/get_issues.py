import requests
import json
from typing import Optional
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state
from app.middleware.github.GithubAuthMiddleware import check_access
from core.utils.tools import doc_tag  # Importing the doc_tag


@doc_tag("Issues")  # Adding the doc_tag decorator
def get_issues_tool(
    repo: Annotated[
        str,
        Field(
            description="The GitHub repository in the format 'owner/repo'."
        ),
    ],
    state: Annotated[
        Optional[str],
        Field(description="Optional state of the issues (e.g., 'open', 'closed')."),
    ] = None,
    labels: Annotated[
        Optional[str],
        Field(description="Optional comma-separated list of labels."),
    ] = None,
    assignee: Annotated[
        Optional[str],
        Field(description="Optional GitHub username for issue assignment."),
    ] = None,
    milestone: Annotated[
        Optional[str],
        Field(description="Optional milestone number or title."),
    ] = None,
    sort: Annotated[
        Optional[str],
        Field(
            description="Optional sorting criteria (e.g., 'created', 'updated', 'comments')."
        ),
    ] = None,
    order: Annotated[
        Optional[str],
        Field(description="Optional order of results (e.g., 'asc', 'desc')."),
    ] = None,
    per_page: Annotated[
        Optional[int],
        Field(description="Optional number of issues per page."),
    ] = None,
    page: Annotated[
        Optional[int],
        Field(description="Optional page number."),
    ] = None,
) -> str:
    """
    Fetch issues from a specified GitHub repository, allowing optional filters for state, labels, assignee, and sorting.
    The repo parameter is required and must be included in the request headers.

    Args:
    - repo (str): The GitHub repository in the format 'owner/repo'.
    - state (Optional[str]): Optional state of the issues (e.g., 'open', 'closed').
    - labels (Optional[str]): Optional comma-separated list of labels.
    - assignee (Optional[str]): Optional GitHub username for issue assignment.
    - milestone (Optional[str]): Optional milestone number or title.
    - sort (Optional[str]): Optional sorting criteria (e.g., 'created', 'updated', 'comments').
    - order (Optional[str]): Optional order of results (e.g., 'asc', 'desc').
    - per_page (Optional[int]): Optional number of issues per page.
    - page (Optional[int]): Optional page number.

    Returns:
    - JSON string containing the list of issues or error.

    Example Requests:
    - Fetching open issues from repository "owner/repo":
      get_issues_tool(repo="owner/repo", state="open")
    - Fetching closed issues with label "bug" from repository "anotherUser/repoName":
      get_issues_tool(repo="anotherUser/repoName", state="closed", labels="bug")
    - Fetching issues assigned to "username" from repository "owner/repo":
      get_issues_tool(repo="owner/repo", assignee="username")
    """
    logger.info(
        f"Request received to search issues for repo: {repo}, state: {state}, labels: {labels}, assignee: {assignee}, milestone: {milestone}, sort: {sort}, order: {order}, per_page: {per_page}, page: {page}"
    )

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    credentials = global_state.get("middleware.GithubAuthMiddleware.credentials", None)

    # Prepare the search query
    q = f"repo:{repo}"
    if state:
        q += f" state:{state}"
    if labels:
        q += f" labels:{labels}"
    if assignee:
        q += f" assignee:{assignee}"
    if milestone:
        q += f" milestone:{milestone}"

    # Prepare the search URL
    url = "https://api.github.com/search/issues"

    # Prepare query parameters
    params = {
        "q": q,
        "sort": sort,
        "order": order,
        "per_page": per_page,
        "page": page,
    }

    headers = {"Authorization": f"token {credentials['access_token']}"}

    logger.info(f"Searching GitHub API with URL: {url} and params: {params}")

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return json.dumps({"error": f"Request failed: {str(e)}"})

    try:
        issues = response.json()
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response")
        return json.dumps({"error": "Failed to decode JSON response"})

    issue_list = [
        {
            "id": issue["id"],
            "title": issue["title"],
            "url": issue["html_url"],
            "state": issue["state"],
            "created_at": issue["created_at"],
            "updated_at": issue["updated_at"],
            "comments": issue["comments"],
        }
        for issue in issues.get("items", [])
    ]

    logger.info(f"Found {len(issue_list)} issues in the repository.")

    return json.dumps(
        {
            "data": {
                "issues": issue_list,
                "total_count": len(issue_list),
            }
        }
    )
