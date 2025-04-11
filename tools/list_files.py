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
    repo: Annotated[
        str,
        Field(description="The GitHub repository in the format 'owner/repo'."),
    ],
    folders: Annotated[
        Optional[List[str]],
        Field(description="Optional list of folder paths to filter by."),
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
    The repo parameter is required and must be included in the request headers.

    Args:
    - repo (str): The GitHub repository in the format 'owner/repo'.
    - folders (Optional[List[str]]): Optional list of folder paths to filter by.
    - branch (Optional[str]): Optional branch name to fetch files from. Defaults to the repository's default branch.

    Returns:
    - JSON string containing the list of file paths in the repository or error.

    Example Requests:
    - Fetching all files from repository "owner/repo":
      list_files_tool(repo="owner/repo")
    - Fetching files from a specific folder in repository "anotherUser/repoName":
      list_files_tool(repo="anotherUser/repoName", folders=["src"])
    - Fetching files from a specific branch in repository "owner/repo":
      list_files_tool(repo="owner/repo", branch="develop")
    - Fetching files from multiple folders in repository "exampleUser/repo":
      list_files_tool(repo="exampleUser/repo", folders=["docs", "lib"])
    """
    logger.info(
        f"Retrieving files from repository: {repo}, folders: {folders}, branch: {branch}"
    )

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    credentials = global_state.get("middleware.GithubAuthMiddleware.credentials", None)

    headers = {
        "Authorization": f"token {credentials['access_token']}"
    }  # Include the access token in the headers

    all_files = []

    # Step 1: Fetch the default branch's name if branch is not provided
    if not branch:
        branch_url = f"https://api.github.com/repos/{repo}/branches"
        branch_response = requests.get(branch_url, headers=headers)

        if branch_response.status_code != 200:
            return {"error": f"GitHub API error: {branch_response.text}"}

        branch = branch_response.json()[0]["name"]  # Get the default branch name

    # Step 2: Fetch the tree from the specified branch
    tree_url = f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"
    tree_response = requests.get(tree_url, headers=headers)
    if tree_response.status_code != 200:
        return {"error": f"GitHub API error: {tree_response.text}"}

    # tree_data = tree_response.json()

    # Step 3: Filter files
    # for file in tree_data.get("tree", []):
    #    if file["type"] == "blob":  # This is a file
    #        file_path = file["path"]
    #        if folders is None or any(
    #            file_path.startswith(folder) for folder in folders
    #        ):
    #            all_files.append(file_path)

    tree_data = tree_response.json()

    # Step 3: Shallow filter: include only top-level entries in the folders (or repo root if no folders)
    shallow_files = set()
    shallow_folders = folders or [""]

    for item in tree_data.get("tree", []):
        item_path = item["path"]
        for folder in shallow_folders:
            if folder:
                prefix = folder.rstrip("/") + "/"
                if item_path.startswith(prefix):
                    relative_path = item_path[len(prefix) :]
                    if "/" not in relative_path:  # it's a shallow child
                        shallow_files.add(item_path)
            else:
                if "/" not in item_path:
                    shallow_files.add(item_path)

    all_files = sorted(shallow_files)

    logger.info(f"Found {len(all_files)} files in the repository.")
    return {"data": {"files": all_files}}
