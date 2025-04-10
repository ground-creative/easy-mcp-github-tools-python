import requests
import json
import base64
from typing import Optional
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state
from app.middleware.github.GithubAuthMiddleware import check_access
from core.utils.tools import doc_tag  # Importing the doc_tag


def get_file_sha(repo: str, file_path: str, branch: str, headers: dict) -> str:
    """Fetch the SHA of the specified file in the given branch."""
    url = f"https://api.github.com/repos/{repo}/contents/{file_path}?ref={branch}"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        logger.error(f"Failed to fetch file details: {response.json().get('message')}")
        raise Exception(
            f"Failed to fetch file details: {response.json().get('message')}"
        )

    return response.json()["sha"]

@doc_tag("Files")  # Adding the doc_tag decorator
def update_file_tool(
    file_path: Annotated[
        str, Field(description="The path of the file to edit, including the filename.")
    ],
    new_content: Annotated[
        str, Field(description="The new content to write to the file.")
    ],
    repo: Annotated[
        str,
        Field(
            description="The GitHub repository in the format 'owner/repo'."
        ),
    ],
    commit_message: Annotated[
        Optional[str], Field(description="The commit message for the file update.")
    ] = "Update file",
    branch: Annotated[
        Optional[str],
        Field(
            description="The branch where the file will be updated (default is 'main')."
        ),
    ] = "main",
) -> str:
    """
    Update an existing file in a specified GitHub repository on a specified branch.
    The repo parameter is required and must be included in the request headers.

    Args:
    - file_path (str): The path of the file to edit, including the filename.
    - new_content (str): The new content to write to the file.
    - repo (str): The GitHub repository in the format 'owner/repo'.
    - commit_message (Optional[str]): The commit message for the file update (default is 'Update file').
    - branch (Optional[str]): The branch where the file will be updated (default is 'main').

    Returns:
    - JSON string indicating success or error.

    Example Requests:
    - Updating a file "README.md" in repository "owner/repo":
      update_file_tool(file_path="README.md", new_content="New content here", repo="owner/repo")
    - Updating a file "src/main.py" in repository "anotherUser/repoName" with a custom commit message:
      update_file_tool(file_path="src/main.py", new_content="print('Hello World')", repo="anotherUser/repoName", commit_message="Fix hello world script")
    - Updating a file "lib/utils.py" in repository "exampleUser/repo" on a specific branch:
      update_file_tool(file_path="lib/utils.py", new_content="def new_function(): pass", repo="exampleUser/repo", branch="develop")
    """
    logger.info(
        f"Request received to edit file in repo: {repo}, file_path: {file_path}, commit_message: {commit_message}, branch: {branch}"
    )

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    # Retrieve credentials and repository information
    credentials = global_state.get("middleware.GithubAuthMiddleware.credentials")
    headers = {"Authorization": f"token {credentials['access_token']}"}

    try:
        # Step 2: Fetch the SHA of the file
        file_sha = get_file_sha(repo, file_path, branch, headers)

        # Step 3: Prepare the payload to update the file
        payload = {
            "message": commit_message,
            "content": base64.b64encode(
                new_content.encode()
            ).decode(),  # Encode new content to base64
            "sha": file_sha,  # Include the SHA of the existing file
            "branch": branch,
        }

        # Define the URL for the update request
        url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
        logger.info(f"Updating file in GitHub API with URL: {url}")

        # Step 4: Send the request to update the file
        response = requests.put(url, headers=headers, json=payload)

        if response.status_code == 200:
            logger.info(
                f"File '{file_path}' updated successfully in repository '{repo}' on branch '{branch}'."
            )
            return json.dumps(
                {"message": "File updated successfully.", "file_path": file_path}
            )
        else:
            logger.error(f"Failed to update file: {response.json().get('message')}")
            return json.dumps(
                {"error": f"Failed to update file: {response.json().get('message')}"}
            )

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        return json.dumps({"error": str(e)})
