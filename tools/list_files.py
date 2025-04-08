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
def list_files_tool(
    folders: Annotated[
        Optional[List[str]],
        Field(description="Optional list of folder paths to filter by."),
    ] = None,
    repo: Annotated[
        Optional[str],
        Field(
            description="The GitHub repository in the format 'owner/repo'. This parameter is optional and can also be included in the request headers."
        ),
    ] = None,
    branch: Annotated[
        Optional[str],
        Field(
            description="Optional branch name to fetch files from. Defaults to the repository's default branch."
        ),
    ] = None,
) -> str:
    """
    Get a list of file paths from a GitHub repository using the git tree API.
    The repo parameter is optional, it can also be included in the request headers.

    Args:
    - folders (Optional[List[str]]): Optional list of folder paths to filter by.
    - repo (Optional[str]): The GitHub repository in the format 'owner/repo'. This parameter is optional.
    - branch (Optional[str]): Optional branch name to fetch files from. Defaults to the repository's default branch.

    Returns:
    - JSON string containing the list of file paths in the repository or error.
    """
    logger.info(
        f"Retrieving files from repository: {repo}, folders: {folders}, branch: {branch}"
    )

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return json.dumps({"error": auth_response})

    credentials = global_state.get("middleware.GithubAuthMiddleware.credentials", None)
    middleware_repo = global_state.get("middleware.GithubAuthMiddleware.repo", None)

    # Determine the repository to use
    if not repo and not middleware_repo:
        return json.dumps({"error": "Missing required parameters: repo"})

    if not repo:
        repo = middleware_repo

    # Prepare the API request
    repo_name = repo  # Use the repo parameter directly
    headers = {
        "Authorization": f"token {credentials['access_token']}"
    }  # Include the access token in the headers

    all_files = []

    # Step 1: Fetch the default branch's name if branch is not provided
    if not branch:
        branch_url = f"https://api.github.com/repos/{repo_name}/branches"
        branch_response = requests.get(branch_url, headers=headers)

        if branch_response.status_code != 200:
            return json.dumps({"error": f"GitHub API error: {branch_response.text}"})

        branch = branch_response.json()[0]["name"]  # Get the default branch name

    # Step 2: Fetch the tree from the specified branch
    tree_url = (
        f"https://api.github.com/repos/{repo_name}/git/trees/{branch}?recursive=1"
    )
    tree_response = requests.get(tree_url, headers=headers)
    if tree_response.status_code != 200:
        return json.dumps({"error": f"GitHub API error: {tree_response.text}"})

    tree_data = tree_response.json()

    # Step 3: Filter files
    for file in tree_data.get("tree", []):
        if file["type"] == "blob":  # This is a file
            file_path = file["path"]
            if folders is None or any(
                file_path.startswith(folder) for folder in folders
            ):
                all_files.append(file_path)

    logger.info(f"Found {len(all_files)} files in the repository.")
    return json.dumps({"data": {"files": all_files}})
