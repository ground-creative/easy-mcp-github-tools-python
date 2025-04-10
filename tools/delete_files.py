import requests
import json
import base64  # Importing base64 for encoding and decoding
import time  # Importing time for handling timestamps
from typing import List, Optional
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state
from app.middleware.github.GithubAuthMiddleware import check_access
from core.utils.tools import doc_tag  # Importing the doc_tag

# Define the validity duration for the confirmation token (in seconds)
CONFIRMATION_TOKEN_VALIDITY_DURATION = 5 * 60  # 5 minutes


@doc_tag("Files")  # Adding the doc_tag decorator
def delete_files_tool(
    repo: Annotated[
        str,
        Field(
            description="The GitHub repository in the format 'owner/repo'."
        ),
    ],
    file_paths: Annotated[
        List[str],
        Field(
            description="A list of paths of the files to delete, including the filenames."
        ),
    ],
    confirmation_token: Annotated[
        Optional[str],
        Field(
            description="An optional token to confirm the deletion. If not provided, a token will be generated based on the file paths and repository parameters. This token must be used to confirm the deletion request."
        ),
    ] = None,
) -> str:
    """
    Deletes specified files in a GitHub repository from a specified branch.

    This function first checks if a confirmation token is provided. If not, it generates a token based on the file paths and repository parameters.
    The user must then confirm the deletion using this token. If the token is provided, the function validates it against the original request parameters before proceeding with the deletion.
    The token is valid for a specified duration.

    Args:
    - repo (str): The GitHub repository in the format 'owner/repo'.
    - file_paths (List[str]): A list of paths of the files to delete, including the filenames.
    - confirmation_token (Optional[str]): An optional token to confirm the deletion. If not provided, a token will be generated based on the file paths and repository.

    Examples Correct Request:
    
    User: "Delete files file1.txt and file2.txt for repository owner/repo"
    # Generate confirmation token to use for next request
    Assistant Action: `delete_files_tool(repo="owner/repo", file_paths=["file1.txt", "file2.txt"])`
    Assistant Response: "Please confirm deletion of files file1.txt and file2.txt"
    User: "I confirm"
    # Use the confirmation token from the previous request
    Assistant Action: `delete_files_tool(repo="owner/repo", file_paths=["file1.txt", "file2.txt"], confirmation_token="XXXYYY")`
    Assistant Response: "The files file1.txt and file2.txt were deleted successfully."

    Incorrect Request:
    
    Example 1:
    User: "Delete files file1.txt and file2.txt for repository owner/repo"
    Assistant Action: `delete_files_tool(repo="owner/repo", file_paths=["file1.txt", "file2.txt"], confirmation_token="made_up_token")`
    Server Response: Error: Invalid confirmation token. Please provide a valid token to confirm deletion.
    What went wrong: Instead of requesting a token and asking for confirmation, a made-up token was sent.
    Example 2:
    User: "Delete files file1.txt and file2.txt for repository owner/repo"
    # Generate confirmation token to use for next request
    Assistant Action: `delete_files_tool(repo="owner/repo", file_paths=["file1.txt", "file2.txt"])`
    Assistant Action: `delete_files_tool(repo="owner/repo", file_paths=["file1.txt", "file2.txt"], confirmation_token="XXXYYY")`
    What went wrong: Confirmation token was used without asking for confirmation.

    Returns:
    - JSON string indicating success or error.
    """
    logger.info(
        f"Request received to delete files at '{file_paths}' in repo: {repo} on branch: {branch} with confirmation token: {confirmation_token}"
    )

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    # Retrieve credentials and repository information
    credentials = global_state.get("middleware.GithubAuthMiddleware.credentials")

    # Generate a confirmation token if not provided
    if not confirmation_token:
        # Create a string with the request parameters and current timestamp
        params_string = f"{','.join(file_paths)}:{repo}:{branch}:{int(time.time())}"
        confirmation_token = base64.b64encode(params_string.encode()).decode()
        logger.info(f"Generated confirmation token: {confirmation_token}")
        return json.dumps(
            {
                "message": f"Confirmation required to delete files at '{file_paths}' on branch '{branch}'. Once confirmed, use the given confirmation_token with the same request parameters.",
                "confirmation_token": confirmation_token,
                "action": "confirm_deletion",
            }
        )

    # Decode and validate the confirmation token
    try:
        decoded_params = base64.b64decode(confirmation_token).decode()
        token_file_paths, token_repo, token_branch, token_timestamp = (
            decoded_params.split(":")
        )
        token_timestamp = int(token_timestamp)

        # Check if the token has expired
        if time.time() - token_timestamp > CONFIRMATION_TOKEN_VALIDITY_DURATION:
            return json.dumps(
                {"error": "Confirmation token has expired. Please request a new token."}
            )

        # Check if the parameters match
        if (
            token_repo != repo
            or token_branch != branch
            or set(token_file_paths.split(",")) != set(file_paths)
        ):
            return json.dumps(
                {
                    "error": "Invalid confirmation token. Parameters do not match, please request a new token.",
                    "details": {
                        "token_params": {
                            "file_paths": token_file_paths.split(","),
                            "repo": token_repo,
                            "branch": token_branch,
                        },
                        "request_params": {
                            "file_paths": file_paths,
                            "repo": repo,
                            "branch": branch,
                        },
                    },
                }
            )
    except Exception as e:
        logger.error(f"Failed to decode confirmation token: {e}")
        return json.dumps({"error": "Invalid confirmation token."})

    # Prepare to delete each file
    responses = []
    for file_path in file_paths:
        # Prepare the URL to get the current file details, including the branch reference
        url = f"https://api.github.com/repos/{repo}/contents/{file_path}?ref={branch}"
        headers = {
            "Authorization": f"token {credentials['access_token']}",
            "Accept": "application/vnd.github.v3+json",
        }

        logger.info(f"Retrieving file info for deletion in GitHub API with URL: {url}")

        try:
            # Get the current file details to retrieve the SHA
            file_response = requests.get(url, headers=headers)
            file_response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
            file_info = file_response.json()  # Parse JSON response

            # Prepare the URL to delete the file
            delete_url = url
            delete_payload = {
                "message": f"Delete {file_path}",
                "sha": file_info["sha"],  # Include the SHA of the existing file
                "branch": branch,  # Include the branch in the payload
            }

            logger.info(f"Deleting file in GitHub API with URL: {delete_url}")

            # Send the request to delete the file
            response = requests.delete(delete_url, headers=headers, json=delete_payload)
            response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
            responses.append(
                {"file_path": file_path, "message": "File deleted successfully."}
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for file '{file_path}': {e}")
            responses.append(
                {"file_path": file_path, "error": f"Request failed: {str(e)}"}
            )

    logger.info(
        f"Files deletion process completed in repository '{repo}' on branch '{branch}'."
    )
    return json.dumps({"responses": responses})
