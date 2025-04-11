import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import time
from app.tools.create_file import create_file_tool
from app.tools.update_file import update_file_tool
from app.tools.create_branch import create_branch_tool
from app.tools.get_commits import get_commits_tool
from app.tools.get_commit_details import get_commit_details_tool
from app.tools.get_files_before_commit import get_files_before_commit_tool


def test_get_commits(repository_setup):
    test_username, repo_name = repository_setup

    file_path = "src/test_get_commits.txt"
    file_content = "Initial commit for testing test_get_commits."

    # Step 1: Create a file to generate a commit
    create_file_tool(
        repo=f"{test_username}/{repo_name}",
        file_path=file_path,
        content=file_content,
        commit_message=file_content,
    )

    time.sleep(5)

    # Step 2: Fetch commits using get_commits_tool
    response = get_commits_tool(repo=f"{test_username}/{repo_name}")

    assert isinstance(response, dict)
    assert "commits" in response
    assert "total_count" in response
    assert response["total_count"] > 0

    # Step 3: Check that our commit message exists in the response
    commit_messages = [commit["message"] for commit in response["commits"]]
    assert any(
        "Initial commit for testing test_get_commits." in msg for msg in commit_messages
    )


def test_get_commits_from_branch(repository_setup):
    test_username, repo_name = repository_setup

    file_path = "src/test_get_commits_from_branch.txt"
    file_content = "Initial commit for testing test_get_commits_from_branch."
    branch = "test_get_commits_from_branch"

    # Create branch and file
    create_branch_tool(repo=f"{test_username}/{repo_name}", new_branch=branch)

    time.sleep(5)

    # Step 1: Create a file to generate a commit
    create_file_tool(
        repo=f"{test_username}/{repo_name}",
        file_path=file_path,
        content=file_content,
        commit_message=file_content,
        branch=branch,
    )

    time.sleep(5)

    # Step 2: Fetch commits using get_commits_tool
    response = get_commits_tool(repo=f"{test_username}/{repo_name}", branch=branch)

    assert isinstance(response, dict)
    assert "commits" in response
    assert "total_count" in response
    assert response["total_count"] > 0

    # Step 3: Check that our commit message exists in the response
    commit_messages = [commit["message"] for commit in response["commits"]]
    assert any(
        "Initial commit for testing test_get_commits_from_branch." in msg
        for msg in commit_messages
    )


def test_get_commit_details(repository_setup):
    test_username, repo_name = repository_setup

    file_path = "src/test_get_commit_details.txt"
    file_content = "Commit for testing get_commit_details_tool."

    # Step 1: Create a file and commit it
    create_file_tool(
        repo=f"{test_username}/{repo_name}",
        file_path=file_path,
        content=file_content,
        commit_message=file_content,
    )

    time.sleep(5)

    # Step 2: Fetch commits using get_commits_tool
    response = get_commits_tool(repo=f"{test_username}/{repo_name}")

    commits = response.get("commits", {})

    assert len(commits) > 0

    commit_sha = commits[0]["sha"]
    assert commit_sha is not None, "Failed to retrieve commit SHA"

    full_details = get_commit_details_tool(
        repo=f"{test_username}/{repo_name}",
        sha=commit_sha,
    )

    assert isinstance(full_details, dict)
    assert "commit" in full_details
    commit_info = full_details["commit"]
    assert commit_info["sha"] == commit_sha
    assert file_path in [f["filename"] for f in commit_info["files"]]

    # Step 3: Fetch file-specific diffs
    file_diff_response = get_commit_details_tool(
        repo=f"{test_username}/{repo_name}",
        sha=commit_sha,
        files=[file_path],
    )

    assert isinstance(file_diff_response, dict)
    assert "data" in file_diff_response
    data = file_diff_response["data"]
    assert data["sha"] == commit_sha
    assert len(data["files"]) == 1
    assert data["files"][0]["filename"] == file_path
    assert "patch" in data["files"][0]


def test_get_commit_details_from_branch(repository_setup):
    test_username, repo_name = repository_setup

    file_path = "src/test_get_commit_details_from_branch.txt"
    file_content = "Commit for testing test_get_commit_details_from_branch."

    branch = "test_get_commits_from_branch"

    # Create branch and file
    create_branch_tool(repo=f"{test_username}/{repo_name}", new_branch=branch)

    time.sleep(5)

    # Step 1: Create a file and commit it
    create_response = create_file_tool(
        repo=f"{test_username}/{repo_name}",
        file_path=file_path,
        content=file_content,
        commit_message=file_content,
        branch=branch,
    )

    time.sleep(5)

    # Step 2: Fetch commits using get_commits_tool
    response = get_commits_tool(repo=f"{test_username}/{repo_name}", branch=branch)

    commits = response.get("commits", {})

    assert len(commits) > 0

    commit_sha = commits[0]["sha"]
    assert commit_sha is not None, "Failed to retrieve commit SHA"

    # Step 2: Fetch full commit details
    full_details = get_commit_details_tool(
        repo=f"{test_username}/{repo_name}", sha=commit_sha
    )

    assert isinstance(full_details, dict)
    assert "commit" in full_details
    commit_info = full_details["commit"]
    assert commit_info["sha"] == commit_sha
    assert file_path in [f["filename"] for f in commit_info["files"]]

    # Step 3: Fetch file-specific diffs
    file_diff_response = get_commit_details_tool(
        repo=f"{test_username}/{repo_name}",
        sha=commit_sha,
        files=[file_path],
    )

    assert isinstance(file_diff_response, dict)
    assert "data" in file_diff_response
    data = file_diff_response["data"]
    assert data["sha"] == commit_sha
    assert len(data["files"]) == 1
    assert data["files"][0]["filename"] == file_path
    assert "patch" in data["files"][0]


def test_get_files_before_commit(repository_setup):
    test_username, repo_name = repository_setup

    file_path = "src/test_get_files_before_commit.txt"
    file_content_1 = "Initial content before change"
    file_content_2 = "Updated content after change"

    # Step 1: Create a file with initial content and commit it
    create_file_tool(
        repo=f"{test_username}/{repo_name}",
        file_path=file_path,
        content=file_content_1,
        commit_message="Initial commit for file",
    )

    time.sleep(5)

    # Step 2: Modify the file and commit the changes
    update_file_tool(
        repo=f"{test_username}/{repo_name}",
        file_path=file_path,
        new_content=file_content_2,
        commit_message="Updated file content for testing get_files_before_commit_tool",
    )

    time.sleep(5)

    # Step 3: Fetch the latest commits to get the current SHA
    response = get_commits_tool(repo=f"{test_username}/{repo_name}")
    commits = response.get("commits", [])
    assert len(commits) >= 2, "Expected at least two commits"

    current_sha = commits[0]["sha"]
    previous_sha = commits[1]["sha"]

    # Step 4: Call the function to fetch file content from before the current commit
    result = get_files_before_commit_tool(
        sha=current_sha,
        files=[file_path],
        repo=f"{test_username}/{repo_name}",
    )

    assert isinstance(result, dict)
    assert result["sha"] == previous_sha
    assert len(result["files"]) == 1

    file_info = result["files"][0]
    assert file_info["filename"] == file_path
    assert file_content_1 in file_info["content"]
