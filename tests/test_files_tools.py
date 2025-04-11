import os
import sys
from app.tools.create_file import create_file_tool
from app.tools.create_branch import create_branch_tool
from app.tools.get_files_contents import get_files_contents_tool
from app.tools.list_files import list_files_tool
from app.tools.search_files import search_files_tool
from app.tools.update_file import update_file_tool
from app.tools.get_files_details import get_files_details_tool
from app.tools.delete_files import delete_files_tool

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def test_create_file(repository_setup):
    test_username, repo_name = repository_setup

    file_path = "test-folder/test_create_file.txt"
    file_content = "Hello, this is a test file."

    response_data = create_file_tool(
        repo=f"{test_username}/{repo_name}",
        file_path=file_path,
        content=file_content,
    )

    assert isinstance(response_data, dict)
    assert response_data.get("message") == "File created successfully."


def test_create_file_from_branch(repository_setup):
    test_username, repo_name = repository_setup

    file_path = "test-folder/test_create_file_from_branch.txt"
    file_content = "Hello, this is a test file."
    new_branch = "test_create_file_from_branch"

    # Create the new branch first
    response_data = create_branch_tool(
        repo=f"{test_username}/{repo_name}",
        new_branch=new_branch,
    )

    # Now create the file in the new branch
    response_data = create_file_tool(
        repo=f"{test_username}/{repo_name}",
        file_path=file_path,
        content=file_content,
        branch=new_branch,
    )

    assert isinstance(response_data, dict)
    assert response_data.get("message") == "File created successfully."


def test_update_file(repository_setup):
    test_username, repo_name = repository_setup

    # File must already exist in the repo/branch
    file_path = "test-folder/test_update_file.txt"
    initial_content = "Initial test content."
    updated_content = "Updated content for testing."

    # First, create the file (if needed)
    create_response = create_file_tool(
        repo=f"{test_username}/{repo_name}",
        file_path=file_path,
        content=initial_content,
    )
    assert create_response.get("message") == "File created successfully."

    # Then, try updating it
    update_response = update_file_tool(
        repo=f"{test_username}/{repo_name}",
        file_path=file_path,
        new_content=updated_content,
        commit_message="Test update commit",
    )

    assert isinstance(update_response, dict)
    assert update_response.get("message") == "File updated successfully."


def test_update_file_from_branch(repository_setup):
    test_username, repo_name = repository_setup

    file_path = "test-folder/test_update_file_from_branch.txt"
    initial_content = "Initial content for branch update test."
    updated_content = "Updated content in the new branch."
    new_branch = "test_update_file_from_branch"

    # Step 1: Create the new branch
    create_branch_tool(
        repo=f"{test_username}/{repo_name}",
        new_branch=new_branch,
    )

    # Step 2: Create the file in the new branch
    create_file_response = create_file_tool(
        repo=f"{test_username}/{repo_name}",
        file_path=file_path,
        content=initial_content,
        branch=new_branch,
    )
    assert create_file_response.get("message") == "File created successfully."

    # Step 3: Update the file in the new branch
    update_file_response = update_file_tool(
        repo=f"{test_username}/{repo_name}",
        file_path=file_path,
        new_content=updated_content,
        commit_message="Update file in new branch",
        branch=new_branch,
    )

    assert isinstance(update_file_response, dict)
    assert update_file_response.get("message") == "File updated successfully."


def test_get_files_contents(repository_setup):
    test_username, repo_name = repository_setup

    file_path = "test-folder/test_get_file_contenth.txt"
    content = "Hello from main branch!"

    # Create the file
    response = create_file_tool(
        repo=f"{test_username}/{repo_name}",
        file_path=file_path,
        content=content,
    )

    # Fetch the content
    response = get_files_contents_tool(
        repo=f"{test_username}/{repo_name}",
        file_paths=[file_path],
    )

    assert isinstance(response, dict)
    file_data = response["data"]["file_contents"][0]
    assert file_data["file_path"] == file_path
    assert file_data["content"] == content


def test_get_files_contents_from_branch(repository_setup):
    test_username, repo_name = repository_setup

    file_path = "test-folder/test_get_file_content_from_branch.txt"
    content = "Hello from feature branch!"
    branch = "test_get_file_content_from_branch"

    # Create branch and file
    create_branch_tool(repo=f"{test_username}/{repo_name}", new_branch=branch)
    create_file_tool(
        repo=f"{test_username}/{repo_name}",
        file_path=file_path,
        content=content,
        branch=branch,
    )

    # Fetch the content from that branch
    response = get_files_contents_tool(
        repo=f"{test_username}/{repo_name}",
        file_paths=[file_path],
        branch=branch,
    )

    assert isinstance(response, dict)
    file_data = response["data"]["file_contents"][0]
    assert file_data["file_path"] == file_path
    assert file_data["content"] == content


def test_list_files(repository_setup):
    test_username, repo_name = repository_setup

    # Step 1: Create files in the repository before listing
    file_paths = [
        "src/test_file_1.txt",
        "src/test_file_2.txt",
        "docs/readme.md",
        "docs/setup.md",
        "test/test_file_3.txt",
    ]

    for file_path in file_paths:
        create_file_tool(
            repo=f"{test_username}/{repo_name}",
            file_path=file_path,
            content="This is a test file.",
        )

    # Test case 1: List all files (shallow)
    response = list_files_tool(repo=f"{test_username}/{repo_name}")

    assert isinstance(response, dict)
    assert "files" in response["data"]

    # Expecting shallow listing at root
    expected_root_contents = {"README.md", "docs", "src", "test"}
    assert expected_root_contents.issubset(set(response["data"]["files"]))

    # Test case 2: Shallow listing inside specific folders
    folders = ["src", "docs"]
    response = list_files_tool(repo=f"{test_username}/{repo_name}", folders=folders)
    assert isinstance(response, dict)
    assert "files" in response["data"]

    expected_shallow_contents = {
        "src/test_file_1.txt",
        "src/test_file_2.txt",
        "docs/readme.md",
        "docs/setup.md",
    }

    # check that only top-level items in those folders are returned:
    for f in response["data"]["files"]:
        assert any(f.startswith(folder + "/") for folder in folders)

    assert expected_shallow_contents.issubset(set(response["data"]["files"]))


def test_list_files_from_branch(repository_setup):
    test_username, repo_name = repository_setup

    branch = "test_list_files_from_branch"

    # Create branch and file
    create_branch_tool(repo=f"{test_username}/{repo_name}", new_branch=branch)

    # Step 1: Create files in the repository before listing
    file_paths = [
        "src/test_file_1.txt",
        "src/test_file_2.txt",
        "docs/readme.md",
        "docs/setup.md",
        "test/test_file_3.txt",
    ]

    for file_path in file_paths:
        create_file_tool(
            repo=f"{test_username}/{repo_name}",
            file_path=file_path,
            content="This is a test file.",
            branch=branch,
        )

    # Test case 1: List all files (shallow)
    response = list_files_tool(repo=f"{test_username}/{repo_name}", branch=branch)
    assert isinstance(response, dict)
    assert "files" in response["data"]

    # Expecting shallow listing at root
    expected_root_contents = {"README.md", "docs", "src", "test"}
    assert expected_root_contents.issubset(set(response["data"]["files"]))

    # Test case 2: Shallow listing inside specific folders
    folders = ["src", "docs"]
    response = list_files_tool(
        repo=f"{test_username}/{repo_name}", folders=folders, branch=branch
    )
    assert isinstance(response, dict)
    assert "files" in response["data"]

    expected_shallow_contents = {
        "src/test_file_1.txt",
        "src/test_file_2.txt",
        "docs/readme.md",
        "docs/setup.md",
    }

    # check that only top-level items in those folders are returned:
    for f in response["data"]["files"]:
        assert any(f.startswith(folder + "/") for folder in folders)

    assert expected_shallow_contents.issubset(set(response["data"]["files"]))


def test_search_files_tool(auth_setup):

    response = search_files_tool(
        search_string="Test Repository",  # search string that should match README.md
        repo=f"zpqrtbnk/test-repo",
        page=1,
        per_page=10,
    )

    assert isinstance(response, dict)
    assert "matching_files" in response

    matching_files = response["matching_files"]

    # Assert that README.md is part of the matching files
    assert any(f["name"] == "README.md" for f in matching_files)

    response = search_files_tool(
        search_string="Build Branch",  # search string that should match README.md
        repo=f"zpqrtbnk/test-repo",
        folders=[".github/workflows"],
        page=1,
        per_page=10,
    )

    assert isinstance(response, dict)
    assert "matching_files" in response

    matching_files = response["matching_files"]

    # Assert that branch.yml is part of the matching files
    assert any(f["name"] == "branch.yml" for f in matching_files)


def test_get_files_details(repository_setup):
    test_username, repo_name = repository_setup

    # Step 1: Create files in the repository
    file_paths = [
        "test_get_files_details/test_file_1.txt",
        "test_get_files_details/test_file_2.txt",
        "test_get_files_details/readme.md",
        "test_get_files_details/setup.md",
    ]
    for path in file_paths:
        create_file_tool(
            repo=f"{test_username}/{repo_name}",
            file_path=path,
            content="This is a test file.",
        )

    # Step 2: Get file details
    response = get_files_details_tool(
        repo=f"{test_username}/{repo_name}", files=file_paths
    )

    # Step 3: Assert results
    assert isinstance(response, dict)
    assert "file_details" in response
    assert response["total_count"] == len(file_paths)

    returned_paths = {file["path"] for file in response["file_details"]}
    assert set(file_paths).issubset(returned_paths)

    for file in response["file_details"]:
        assert "name" in file
        assert "path" in file
        assert "size" in file
        assert "type" in file
        assert "url" in file


def test_get_files_details_from_branch(repository_setup):
    test_username, repo_name = repository_setup
    branch = "test_get_files_details_from_branch"

    # Create branch and file
    create_branch_tool(repo=f"{test_username}/{repo_name}", new_branch=branch)

    # Step 1: Create files in the repository
    file_paths = [
        "test_get_files_details_from_branch/test_file_1.txt",
        "test_get_files_details_from_branch/test_file_2.txt",
        "test_get_files_details_from_branch/readme.md",
        "test_get_files_details_from_branch/setup.md",
    ]
    for path in file_paths:
        create_file_tool(
            repo=f"{test_username}/{repo_name}",
            file_path=path,
            content="This is a test file.",
            branch=branch,
        )

    # Step 2: Get file details
    response = get_files_details_tool(
        repo=f"{test_username}/{repo_name}", files=file_paths, branch=branch
    )

    # Step 3: Assert results
    assert isinstance(response, dict)
    assert "file_details" in response
    assert response["total_count"] == len(file_paths)

    returned_paths = {file["path"] for file in response["file_details"]}
    assert set(file_paths).issubset(returned_paths)

    for file in response["file_details"]:
        assert "name" in file
        assert "path" in file
        assert "size" in file
        assert "type" in file
        assert "url" in file


def test_delete_files(repository_setup):
    test_username, repo_name = repository_setup

    file_path = "test_delete_files.txt"
    file_content = "Hello, this is a test file."

    response_data = create_file_tool(
        repo=f"{test_username}/{repo_name}",
        file_path=file_path,
        content=file_content,
    )

    # Test case 1: Generate confirmation token
    file_paths = [file_path]
    response_data = delete_files_tool(
        repo=f"{test_username}/{repo_name}",
        file_paths=file_paths,
    )

    assert isinstance(response_data, dict)
    assert "confirmation_token" in response_data

    confirmation_token = response_data["confirmation_token"]

    # Confirm the deletion by sending the token
    response_data = delete_files_tool(
        repo=f"{test_username}/{repo_name}",
        file_paths=file_paths,
        confirmation_token=confirmation_token,
    )

    # Assert the file has been deleted
    assert isinstance(response_data, dict)
    assert "responses" in response_data
    assert len(response_data["responses"]) > 0
    assert response_data["responses"][0]["file_path"] == file_path
    assert response_data["responses"][0]["message"] == "File deleted successfully."


def test_delete_files_from_branch(repository_setup):
    test_username, repo_name = repository_setup

    file_path = "test_delete_files.txt"
    file_content = "Hello, this is a test file."
    branch = "test_delete_files_from_branch"

    # Create branch and file
    create_branch_tool(repo=f"{test_username}/{repo_name}", new_branch=branch)

    response_data = create_file_tool(
        repo=f"{test_username}/{repo_name}",
        file_path=file_path,
        content=file_content,
        branch=branch,
    )

    # Test case 1: Generate confirmation token
    file_paths = [file_path]
    response_data = delete_files_tool(
        repo=f"{test_username}/{repo_name}", file_paths=file_paths, branch=branch
    )

    assert isinstance(response_data, dict)
    assert "confirmation_token" in response_data

    confirmation_token = response_data["confirmation_token"]

    # Confirm the deletion by sending the token
    response_data = delete_files_tool(
        repo=f"{test_username}/{repo_name}",
        file_paths=file_paths,
        branch=branch,
        confirmation_token=confirmation_token,
    )

    # Assert the file has been deleted
    assert isinstance(response_data, dict)
    assert "responses" in response_data
    assert len(response_data["responses"]) > 0
    assert response_data["responses"][0]["file_path"] == file_path
    assert response_data["responses"][0]["message"] == "File deleted successfully."
