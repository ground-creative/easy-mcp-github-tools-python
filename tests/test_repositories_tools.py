import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import time
from app.tools.find_repositories_by_name import find_repositories_by_name_tool
from app.tools.get_releases import get_releases_tool
from app.tools.get_repositories import get_repositories_tool
from app.tools.get_repository_details import get_repository_details_tool
from app.tools.get_tags_or_branches import get_tags_or_branches_tool


def test_get_repository_details(repository_setup):
    test_username, repo_name = repository_setup  # Get the repo name from the fixture
    # Call the function to get details for the created repository
    response_data = get_repository_details_tool(repo=f"{test_username}/{repo_name}")

    # Access the repository details correctly
    repo_details = response_data.get("repository_details")

    # Assertions to verify the repository details
    assert repo_details is not None, "Repository details not found"
    assert (
        repo_details.get("name") == repo_name
    ), f"Expected {repo_name}, but got {repo_details.get('name')}"


def test_find_repositories_by_name(repository_setup):
    test_username, repo_name = repository_setup  # Get the repo name from the fixture

    time.sleep(5)

    # Call the function to find repositories by name
    response_data = find_repositories_by_name_tool(
        query=repo_name, username=test_username
    )

    print(f"response_data {response_data}")

    # Assertions to verify that the repository is found
    assert any(
        repo["name"] == repo_name for repo in response_data.get("repositories", [])
    ), "Repository not found"


def test_get_tags_or_branches(repository_setup):
    test_username, repo_name = repository_setup  # Get the repo name from the fixture
    # Call the function to get tags or branches for the repository
    response_data = get_tags_or_branches_tool(
        repo=f"{test_username}/{repo_name}", type="branches"
    )

    # Access the branches from the response data
    branches = response_data.get("branches", [])

    # Assertions to verify that the branches are returned
    assert isinstance(branches, list), "Expected branches to be a list"
    assert len(branches) > 0, "Expected at least one branch to be returned"
    assert branches[0]["name"] == "main", "Expected the main branch to be returned"


def test_get_releases(repository_setup):
    test_username, repo_name = repository_setup  # Get the repo name from the fixture
    # Call the function to get releases for the created repository
    response_data = get_releases_tool(repo=f"{test_username}/{repo_name}")

    # Access the releases from the response data
    releases = response_data.get("data", {}).get("releases", [])

    # Assertions to verify that releases are returned
    assert isinstance(releases, list), "Expected releases to be a list"
    assert len(releases) >= 0, "Expected at least zero releases to be returned"


def test_get_repositories(repository_setup):
    test_username, repo_name = repository_setup  # Get the repo name from the fixture
    # Call the function to get repositories for the test user, sorted by creation date in descending order
    response_data = get_repositories_tool(
        username=test_username,
        sort="created",  # Sort by creation date
        direction="desc",  # Descending order
    )

    # Access the repositories from the response data
    repositories = response_data.get("repositories", [])

    # Assertions to verify that repositories are returned
    assert isinstance(repositories, list), "Expected repositories to be a list"
    assert any(
        repo["name"] == repo_name for repo in repositories
    ), "Expected the created repository to be listed"
