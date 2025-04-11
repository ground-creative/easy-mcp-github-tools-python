import os
import sys
from app.tools.create_branch import create_branch_tool
from app.tools.delete_branch import delete_branch_tool

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

new_branch = "feature-branch"


def test_create_branch(repository_setup):
    test_username, repo_name = repository_setup  # Get the repo name from the fixture

    # Call the function to create a new branch
    response_data = create_branch_tool(
        repo=f"{test_username}/{repo_name}", new_branch=new_branch
    )

    # Assertions to verify the branch creation
    assert (
        response_data.get("message") == f"Branch '{new_branch}' created successfully."
    )
    assert response_data.get("base_branch") == "main"


def test_delete_branch(repository_setup):
    test_username, repo_name = repository_setup  # Get the repo name from the fixture

    # Ensure the branch exists before trying to delete it
    create_branch_tool(repo=f"{test_username}/{repo_name}", new_branch=new_branch)

    # Call the function to delete the branch without confirmation token
    response_data = delete_branch_tool(
        repo=f"{test_username}/{repo_name}", branch=new_branch
    )

    assert "confirmation_token" in response_data

    # Now confirm the deletion using the generated confirmation token
    confirmation_token = response_data["confirmation_token"]
    response_data = delete_branch_tool(
        repo=f"{test_username}/{repo_name}",
        branch=new_branch,  # Use the correct branch variable
        confirmation_token=confirmation_token,
    )

    # Assertions to verify the branch deletion
    assert (
        response_data.get("message") == f"Branch '{new_branch}' deleted successfully."
    )
