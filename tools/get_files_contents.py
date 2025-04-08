import requests
import json
import base64
from typing import List, Optional
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state
from app.middleware.github.GithubAuthMiddleware import check_access
from core.utils.tools import doc_tag  # Importing the doc_tag


@doc_tag("Files")  # Adding the doc_tag decorator
def get_files_contents_tool(
    file_paths: Annotated[
        List[str],
        Field(description="List of file paths to fetch content for."),
    ],
    repo: Annotated[
        Optional[str],
        Field(
            description="The GitHub repository in the format 'owner/repo'. This parameter is optional."
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
    Fetch content for multiple files from a GitHub repository.
    The repo parameter is optional, it can also be included in the request headers.

    Args:
    - file_paths (List[str]): List of file paths to fetch content for.
    - repo (Optional[str]): The GitHub repository in the format 'owner/repo'. This parameter is optional.
    - branch (Optional[str]): Optional branch name to fetch files from. Defaults to the repository's default branch.

    Returns:
    - JSON string containing the file contents or error.
    """
    logger.info(
        f"Request to get content for files: {file_paths} from repo: {repo}, branch: {branch}"
    )

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return json.dumps({"error": auth_response})

    credentials = global_state.get("middleware.GithubAuthMiddleware.credentials", None)
    token = credentials["access_token"]  # Get the access token

    # Determine the repository to use
    middleware_repo = global_state.get("middleware.GithubAuthMiddleware.repo", None)

    if not repo and not middleware_repo:
        return json.dumps({"error": "Missing required parameters: repo"})

    if not repo:
        repo = middleware_repo

    # Check if file_paths is provided
    if not file_paths:
        return json.dumps({"error": "Missing required parameters: file_paths"})

    file_contents = []
    for file_path in file_paths:
        try:
            # Fetch content for the specified file
            content = fetch_file_content(repo, file_path, token, branch)
            file_contents.append({"file_path": file_path, "content": content})
        except Exception as e:
            logger.error(f"Failed to fetch content for {file_path}: {e}")
            file_contents.append(
                {"file_path": file_path, "error": f"Failed to fetch content: {e}"}
            )

    # Log successful fetching
    logger.info(f"Successfully fetched content for {len(file_paths)} files.")

    # Return the content of the files
    return json.dumps(
        {"data": {"file_contents": file_contents, "total_count": len(file_contents)}}
    )


def fetch_file_content(
    repo_url: str, file_path: str, token: str, branch: Optional[str] = None
) -> str:
    """
    Fetch content for a specific file from a GitHub repository.

    Args:
    - repo_url (str): URL of the repository (e.g., 'https://github.com/owner/repo').
    - file_path (str): The file path to fetch content for.
    - token (str): GitHub personal access token.
    - branch (Optional[str]): Optional branch name to fetch the file from.

    Returns:
    - The file content or an error message.
    """
    try:
        # Prepare the API request
        headers = {"Authorization": f"token {token}"}
        content_url = f"https://api.github.com/repos/{repo_url}/contents/{file_path}"

        if branch:
            content_url += f"?ref={branch}"  # Append branch reference if provided

        logger.info(f"Fetching content for file: {file_path} from URL: {content_url}")
        response = requests.get(content_url, headers=headers)

        if response.status_code != 200:
            logger.error(f"GitHub API error: {response.text}")
            return f"Error fetching content for {file_path}: {response.text}"

        file_data = response.json()

        # Handle the encoding of the file content
        if file_data.get("encoding") == "base64":
            # Decode the base64 content
            decoded_content = base64.b64decode(file_data["content"])
            file_content = decoded_content.decode("utf-8")
            logger.info(f"Content fetched and decoded for: {file_path}")
        elif file_data.get("encoding") == "none":
            # Directly decode the 'none' encoding
            file_content = file_data["content"]
            logger.info(f"Content fetched for: {file_path}")
        else:
            logger.warning(f"Unsupported encoding for {file_path}. Skipping.")
            file_content = f"Unsupported encoding for {file_path}."

        return file_content  # Return the file content as plain text

    except Exception as e:
        error_message = f"Error fetching content for {file_path}: {str(e)}"
        logger.error(error_message)
        return error_message  # Return the error message as plain text
