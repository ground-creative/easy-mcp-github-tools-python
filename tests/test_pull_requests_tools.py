import os
import sys
import time
from app.tools.create_branch import create_branch_tool
from app.tools.update_file import update_file_tool
from app.tools.create_file import create_file_tool
from app.tools.create_pull_request import create_pull_request_tool
from app.tools.get_pull_requests import get_pull_requests_tool
from app.tools.get_pull_request_details import get_pull_request_details_tool
from app.tools.merge_pull_request import merge_pull_request_tool

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def test_create_pull_request(repository_setup):
    test_username, repo_name = repository_setup  # Get the repo name from the fixture
    repo = f"{test_username}/{repo_name}"
    target_branch = "test_create_pull_request"
    base_branch = "main"
    title = "Test Pull Request Title"
    body = "This is a test pull request created by an automated test."

    # Step 1: Create the new branch
    create_branch_tool(
        repo=f"{test_username}/{repo_name}",
        new_branch=target_branch,
    )

    time.sleep(5)

    # Step 2: Make changes in the new branch (e.g., create or update a file)
    file_path = "test-folder/test_create_pull_request.txt"
    initial_content = "Initial content for pull request test."

    create_file_response = create_file_tool(
        repo=f"{test_username}/{repo_name}",
        file_path=file_path,
        content=initial_content,
        branch=target_branch,
    )

    # Ensure the file creation was successful
    assert create_file_response.get("message") == "File created successfully."

    # Step 3: Create a commit by making changes to the file
    updated_content = "Updated content in the pull request branch."

    time.sleep(5)

    update_file_response = update_file_tool(
        repo=f"{test_username}/{repo_name}",
        file_path=file_path,
        new_content=updated_content,
        commit_message="Update file for pull request",
        branch=target_branch,
    )

    # Ensure the file update was successful
    assert isinstance(update_file_response, dict)
    assert update_file_response.get("message") == "File updated successfully."

    time.sleep(5)

    # Step 4: Now that the branch has changes, attempt to create the pull request
    response_data = create_pull_request_tool(
        repo=repo,
        target_branch=target_branch,
        base_branch=base_branch,
        title=title,
        body=body,
    )

    # Check if the response is a dictionary and contains the expected fields
    assert isinstance(response_data, dict)
    assert "message" in response_data
    assert "pull_request_url" in response_data

    # Validate the response data for correctness
    assert (
        response_data.get("message")
        == f"Pull request created successfully to update branch '{target_branch}'."
    )


def test_create_get_pull_requests(repository_setup):
    test_username, repo_name = repository_setup  # Get the repo name from the fixture
    repo = f"{test_username}/{repo_name}"

    # Step 1: Create the new branch
    target_branch = "test_create_get_pull_requests"
    base_branch = "main"
    title = "Test Pull Request Title"
    body = "This is a test pull request created by an automated test."

    create_branch_tool(
        repo=f"{test_username}/{repo_name}",
        new_branch=target_branch,
    )

    # Step 2: Make changes in the new branch (e.g., create or update a file)
    file_path = "test-folder/test_create_get_pull_requests.txt"
    initial_content = "Initial content for pull request test."

    time.sleep(5)

    create_file_response = create_file_tool(
        repo=f"{test_username}/{repo_name}",
        file_path=file_path,
        content=initial_content,
        branch=target_branch,
    )

    # Ensure the file creation was successful
    assert create_file_response.get("message") == "File created successfully."

    # Step 3: Create a commit by making changes to the file
    updated_content = "Updated content in the pull request branch."

    time.sleep(5)

    update_file_response = update_file_tool(
        repo=f"{test_username}/{repo_name}",
        file_path=file_path,
        new_content=updated_content,
        commit_message="Update file for pull request",
        branch=target_branch,
    )

    # Ensure the file update was successful
    assert isinstance(update_file_response, dict)
    assert update_file_response.get("message") == "File updated successfully."

    time.sleep(5)

    # Step 4: Now that the branch has changes, create the pull request
    create_pull_request_response = create_pull_request_tool(
        repo=repo,
        target_branch=target_branch,
        base_branch=base_branch,
        title=title,
        body=body,
    )

    # Check if the pull request was created successfully
    assert isinstance(create_pull_request_response, dict)
    assert "message" in create_pull_request_response
    assert "pull_request_url" in create_pull_request_response
    assert (
        create_pull_request_response.get("message")
        == f"Pull request created successfully to update branch '{target_branch}'."
    )

    # Step 5: Fetch the created pull request and validate
    state = "open"  # Ensure we're looking for open pull requests
    sort = "created"
    order = "desc"
    per_page = 5
    page = 1

    time.sleep(5)

    response_data = get_pull_requests_tool(
        repo=repo,
        state=state,
        sort=sort,
        order=order,
        per_page=per_page,
        page=page,
    )

    # Ensure the response is a dictionary and contains the necessary fields
    assert isinstance(response_data, dict)
    assert "pull_requests" in response_data
    assert isinstance(response_data["pull_requests"], list)
    assert (
        len(response_data["pull_requests"]) > 0
    )  # Ensure at least one pull request is returned

    # Step 6: Validate the created pull request is in the list of pull requests
    pull_request_found = False
    for pr in response_data["pull_requests"]:
        if pr["title"] == title and pr["state"] == "open":
            pull_request_found = True
            break

    assert (
        pull_request_found
    ), f"Pull request with title '{title}' was not found in the list of open pull requests."


def test_create_get_pull_request_details(repository_setup):
    test_username, repo_name = repository_setup  # Get the repo name from the fixture
    repo = f"{test_username}/{repo_name}"

    # Step 1: Create the new branch for the pull request
    target_branch = "test_create_pull_request_details"
    base_branch = "main"
    title = "Test Pull Request Details Title"
    body = "This is a test pull request created by an automated test for details."

    create_branch_tool(
        repo=f"{test_username}/{repo_name}",
        new_branch=target_branch,
    )

    # Step 2: Make changes in the new branch (e.g., create or update a file)
    file_path = "test-folder/test_create_pull_request_details.txt"
    initial_content = "Initial content for pull request test."

    time.sleep(5)

    create_file_response = create_file_tool(
        repo=f"{test_username}/{repo_name}",
        file_path=file_path,
        content=initial_content,
        branch=target_branch,
    )

    # Ensure the file creation was successful
    assert create_file_response.get("message") == "File created successfully."

    # Step 3: Create a commit by making changes to the file
    updated_content = "Updated content in the pull request branch."

    time.sleep(5)

    update_file_response = update_file_tool(
        repo=f"{test_username}/{repo_name}",
        file_path=file_path,
        new_content=updated_content,
        commit_message="Update file for pull request",
        branch=target_branch,
    )

    # Ensure the file update was successful
    assert isinstance(update_file_response, dict)
    assert update_file_response.get("message") == "File updated successfully."

    time.sleep(5)

    # Step 4: Now that the branch has changes, create the pull request
    create_pull_request_response = create_pull_request_tool(
        repo=repo,
        target_branch=target_branch,
        base_branch=base_branch,
        title=title,
        body=body,
    )

    # Ensure the pull request was created successfully
    assert isinstance(create_pull_request_response, dict)
    assert "message" in create_pull_request_response
    assert "pull_request_url" in create_pull_request_response
    assert (
        create_pull_request_response.get("message")
        == f"Pull request created successfully to update branch '{target_branch}'."
    )

    # Step 5: Retrieve the pull request number from the created pull request response
    pull_number = create_pull_request_response.get("pull_request_url").split("/")[-1]

    time.sleep(5)

    # Step 6: Fetch the details of the created pull request
    pull_request_details = get_pull_request_details_tool(
        pull_number=pull_number,
        repo=repo,
    )

    # Ensure the response is a dictionary and contains the necessary fields
    assert isinstance(pull_request_details, dict)
    assert "id" in pull_request_details
    assert "title" in pull_request_details
    assert "state" in pull_request_details
    assert pull_request_details["title"] == title
    assert pull_request_details["state"] == "open"  # Assuming the PR is still open


def test_merge_pull_request_tool(repository_setup):
    test_username, repo_name = repository_setup
    repo = f"{test_username}/{repo_name}"

    # Step 1: Create a new branch
    target_branch = "test_merge_pull_request"
    base_branch = "main"
    create_branch_tool(repo=repo, new_branch=target_branch)

    time.sleep(5)

    # Step 2: Create a new file in the branch
    file_path = "test-folder/test_merge_pull_request.txt"
    content = "Content for merge test"
    create_file_response = create_file_tool(
        repo=repo,
        file_path=file_path,
        content=content,
        branch=target_branch,
    )
    assert create_file_response.get("message") == "File created successfully."

    time.sleep(5)

    # Step 3: Update the file to ensure there's a commit
    updated_content = "Updated content before merging"
    update_file_response = update_file_tool(
        repo=repo,
        file_path=file_path,
        new_content=updated_content,
        commit_message="Update file for merge PR",
        branch=target_branch,
    )
    assert update_file_response.get("message") == "File updated successfully."

    time.sleep(5)

    # Step 4: Create a pull request
    title = "Test Merge Pull Request"
    body = "This is a test pull request for merging."
    pr_response = create_pull_request_tool(
        repo=repo,
        target_branch=target_branch,
        base_branch=base_branch,
        title=title,
        body=body,
    )
    assert (
        pr_response.get("message")
        == f"Pull request created successfully to update branch '{target_branch}'."
    )
    pull_number = int(pr_response.get("pull_request_url").split("/")[-1])

    time.sleep(5)

    # Step 5: Merge the pull request
    merge_response = merge_pull_request_tool(
        repo=repo,
        pull_number=pull_number,
        commit_message="Merging PR from test",
    )

    # Ensure the merge was successful
    assert isinstance(merge_response, dict)
    assert merge_response.get("merged") is True
    assert "message" in merge_response
    assert "sha" in merge_response  # Corrected from "commit_sha"
