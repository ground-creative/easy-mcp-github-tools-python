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
def get_issue_comments_tool(
    issue_number: Annotated[
        int,
        Field(description="The number of the issue to retrieve."),
    ],
    repo: Annotated[
        str,
        Field(
            description="The GitHub repository in the format 'owner/repo'."
        ),
    ],
    page: Annotated[
        Optional[int],
        Field(description="The page number of comments to retrieve."),
    ] = 1,
    per_page: Annotated[
        Optional[int],
        Field(description="The number of comments per page."),
    ] = 30,
    sort: Annotated[
        Optional[str],
        Field(description="Field to sort comments by (e.g., 'created_at')."),
    ] = None,
    order: Annotated[
        Optional[str],
        Field(description="Order of sorting (e.g., 'asc' or 'desc')."),
    ] = None,
) -> str:
    """
    Retrieve all messages (details and comments) of a specific issue within a GitHub repository.
    The repo parameter is required and must be included in the request headers.

    Args:
    - issue_number (int): The number of the issue to retrieve. This parameter is required.
    - repo (str): The GitHub repository in the format 'owner/repo'.
    - page (Optional[int]): The page number of comments to retrieve (default is 1).
    - per_page (Optional[int]): The number of comments per page (default is 30).
    - sort (Optional[str]): Field to sort comments by (e.g., 'created_at').
    - order (Optional[str]): Order of sorting (e.g., 'asc' or 'desc').

    Returns:
    - JSON string containing the issue details and comments or error.

    Example Requests:
    - Fetching comments for issue number 123 in repository "owner/repo":
      get_issue_comments_tool(issue_number=123, repo="owner/repo")
    - Fetching comments for issue number 456 in repository "anotherUser/repoName", page 2:
      get_issue_comments_tool(issue_number=456, repo="anotherUser/repoName", page=2)
    """
    logger.info(
        f"Request received to get all messages for repo: {repo}, issue_number: {issue_number}, page: {page}, per_page: {per_page}, sort: {sort}, order: {order}"
    )

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    # Retrieve credentials and repository information
    credentials = global_state.get("middleware.GithubAuthMiddleware.credentials")

    # Prepare the URL to get the issue details
    issue_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
    headers = {"Authorization": f"token {credentials['access_token']}"}

    logger.info(f"Fetching issue details from GitHub API with URL: {issue_url}")

    try:
        # Get issue details
        issue_response = requests.get(issue_url, headers=headers)
        issue_response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
        issue_content = issue_response.json()  # Parse JSON response
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return json.dumps({"error": f"Request failed: {str(e)}"})
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response")
        return json.dumps({"error": "Failed to decode JSON response"})

    # Prepare the URL to get the issue comments with pagination
    comments_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    params = {"page": page, "per_page": per_page}
    logger.info(
        f"Fetching comments from GitHub API with URL: {comments_url} and params: {params}"
    )

    try:
        # Get issue comments
        comments_response = requests.get(comments_url, headers=headers, params=params)
        comments_response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
        comments_content = comments_response.json()  # Parse JSON response
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return json.dumps({"error": f"Request failed: {str(e)}"})
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response")
        return json.dumps({"error": "Failed to decode JSON response"})

    # Sort comments if sort and order are provided
    if sort and order:
        reverse = order.lower() == "desc"
        comments_content.sort(key=lambda x: x.get(sort), reverse=reverse)

    logger.info(
        f"Retrieved issue details and comments for issue number {issue_number}."
    )

    # Combine issue details and comments
    return json.dumps(
        {
            "issue": issue_content,
            "comments": comments_content,
            "total_comments": len(comments_content),
        }
    )
