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
def create_repository_tool(
    name: Annotated[
        str,
        Field(description="The name of the repository to create."),
    ],
    description: Annotated[
        Optional[str],
        Field(description="A short description of the repository."),
    ] = None,
    private: Annotated[
        Optional[bool],
        Field(description="Whether the repository should be private."),
    ] = False,
    auto_init: Annotated[
        Optional[bool],
        Field(description="Whether to create an initial commit with an empty README."),
    ] = True,
) -> str:
    """
    Create a new repository on GitHub.

    Args:
    - name (str): The name of the repository to create. This parameter is required.
    - description (Optional[str]): A short description of the repository.
    - private (Optional[bool]): Whether the repository should be private.
    - auto_init (Optional[bool]): Whether to create an initial commit with an empty README.

    Example Requests:
    - Creating a Public Repository:
      create_repository_tool(name="my-new-repo", description="This is my new repository.", private=False, auto_init=True)
    - Creating a Private Repository:
      create_repository_tool(name="my-private-repo", description="This is a private repository.", private=True, auto_init=False)

    Returns:
    - JSON string containing the created repository details or error.
    """
    logger.info(
        f"Request received to create repository: {name}, description: {description}, private: {private}, auto_init: {auto_init}"
    )

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    # Retrieve credentials
    credentials = global_state.get("middleware.GithubAuthMiddleware.credentials")

    # Prepare the URL to create the repository
    url = "https://api.github.com/user/repos"
    headers = {"Authorization": f"token {credentials['access_token']}"}

    # Prepare the repository data
    repo_data = {
        "name": name,
        "description": description,
        "private": private,
        "auto_init": auto_init,
    }

    logger.info(
        f"Creating repository in GitHub API with URL: {url} and data: {repo_data}"
    )

    try:
        response = requests.post(url, headers=headers, json=repo_data)
        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
        created_repo = response.json()  # Parse JSON response
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return json.dumps({"error": f"Request failed: {str(e)}"})
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response")
        return json.dumps({"error": "Failed to decode JSON response"})

    logger.info(f"Created repository with name '{name}'.")
    return json.dumps(created_repo)
