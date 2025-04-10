import requests
import json
from typing import Optional
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state
from core.utils.tools import doc_tag
from app.middleware.github.GithubAuthMiddleware import check_access
import base64


@doc_tag("Files")
def create_file_tool(
    repo: Annotated[
        str,
        Field(
            description="The GitHub repository in the format 'owner/repo'. This parameter is required."
        ),
    ],
    file_path: Annotated[
        str,
        Field(
            description="The path where the file will be created, including the filename."
        ),
    ],
    content: Annotated[
        str,
        Field(description="The content of the file to be created."),
    ],
    commit_message: Annotated[
        Optional[str],
        Field(description="The commit message for the file creation."),
    ] = "Add new file",
    branch: Annotated[
        Optional[str],
        Field(
            description="The branch where the file will be created (default is 'main')."
        ),
    ] = "main",
) -> str:
    """
    Adds a new file to a specified GitHub repository on a specified branch.

    Args:
    - repo (str): The GitHub repository in the format 'owner/repo'.
    - file_path (str): The path where the file will be created, including the filename.
    - content (str): The content of the file to be created.
    - commit_message (Optional[str]): The commit message for the file creation (default is 'Add new file').
    - branch (Optional[str]): The branch where the file will be created (default is 'main').

    Example Requests:
    - Creating a New File in the Default Branch:
      create_file_tool(repo="owner/repo", file_path="new_file.txt", content="This is the content of the new file.")
    - Creating a New File in a Specific Branch:
      create_file_tool(repo="owner/repo", file_path="new_file.txt", content="This is the content of the new file.", branch="develop")

    Returns:
    - JSON string indicating success or error.
    """
    logger.info(
        f"Request received to add file to repo: {repo}, file_path: {file_path}, commit_message: {commit_message}, branch: {branch}"
    )

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    # Retrieve credentials and repository information
    credentials = global_state.get("middleware.GithubAuthMiddleware.credentials")

    # Check if the specified branch exists
    branch_url = f"https://api.github.com/repos/{repo}/branches/{branch}"
    headers = {"Authorization": f"token {credentials['access_token']}"}

    try:
        branch_response = requests.get(branch_url, headers=headers)
        branch_response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        logger.error(f"Branch check failed: {e}")
        return json.dumps({"error": f"Branch '{branch}' does not exist."})

    # Prepare the URL to check if the file already exists
    check_url = f"https://api.github.com/repos/{repo}/contents/{file_path}?ref={branch}"

    try:
        # Check if the file already exists
        file_response = requests.get(check_url, headers=headers)
        if file_response.status_code == 200:
            return json.dumps(
                {"error": "File already exists. Please update the file instead."}
            )
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to check file existence: {e}")

    # Prepare the URL to create the file
    url = f"https://api.github.com/repos/{repo}/contents/{file_path}"

    # Prepare the payload
    payload = {
        "message": commit_message,
        "content": base64.b64encode(
            content.encode()
        ).decode(),  # Encode content to base64
        "branch": branch,  # Specify the branch in the payload
    }

    logger.info(f"Creating file in GitHub API with URL: {url}")

    try:
        # Send the request to create the file
        response = requests.put(url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        logger.error(
            f"Request failed: {e}, Response: {response.text if response else 'No response'}"
        )
        return json.dumps({"error": f"Request failed: {str(e)}"})
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response")
        return json.dumps({"error": "Failed to decode JSON response"})

    logger.info(
        f"File '{file_path}' created successfully in repository '{repo}' on branch '{branch}'."
    )
    return json.dumps({"message": "File created successfully.", "file_path": file_path})
