import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
import json
from app.tools.create_repository import create_repository_tool
from app.tools.delete_repository import delete_repository_tool
from core.utils.state import global_state
from core.utils.env import EnvConfig


@pytest.fixture(scope="module")
def auth_setup():
    # Set up global state for testing
    global_state.set("middleware.GithubAuthMiddleware.is_authenticated", True)
    global_state.set(
        "middleware.GithubAuthMiddleware.credentials",
        {"access_token": EnvConfig.get("TEST_TOKEN")},
    )


@pytest.fixture(scope="module")
def repository_setup():
    # Set up global state for testing
    global_state.set("middleware.GithubAuthMiddleware.is_authenticated", True)
    global_state.set(
        "middleware.GithubAuthMiddleware.credentials",
        {"access_token": EnvConfig.get("TEST_TOKEN")},
    )

    test_username = EnvConfig.get("TEST_USERNAME")
    repo_name = f"test-repo-{os.urandom(4).hex()}"

    # Create the repository
    response_data = create_repository_tool(
        name=repo_name, description="Test repository", private=False, auto_init=True
    )

    assert response_data.get("name") == repo_name, "Repository creation failed"

    yield test_username, repo_name  # Provide the repository name to the tests

    # Teardown: Delete the repository
    delete_response_data = delete_repository_tool(repo=f"{test_username}/{repo_name}")

    assert "confirmation_token" in delete_response_data

    confirmation_token = delete_response_data["confirmation_token"]
    # Confirm the deletion
    delete_response_data = delete_repository_tool(
        repo=f"{test_username}/{repo_name}", confirmation_token=confirmation_token
    )

    assert (
        delete_response_data.get("message")
        == f"Repository '{test_username}/{repo_name}' deleted successfully."
    )
