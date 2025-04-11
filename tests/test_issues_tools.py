import os
import sys
from app.tools.create_issue import create_issue_tool
from app.tools.get_issues import get_issues_tool
from app.tools.update_issue import update_issue_tool
from app.tools.create_issue_comment import create_issue_comment_tool
from app.tools.get_issue_comments import get_issue_comments_tool
from app.tools.update_issue_comment import update_issue_comment_tool
from app.tools.delete_issue_comment import delete_issue_comment_tool
from app.tools.get_issue_details import get_issue_details_tool
from app.tools.search_issues import search_issues_tool

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def test_create_issue(repository_setup):
    test_username, repo_name = repository_setup  # Get the repo name from the fixture
    repo = f"{test_username}/{repo_name}"
    title = "Test Issue Title"
    body = "This is a test issue created by an automated test."
    labels = ["bug", "test"]

    response_data = create_issue_tool(
        repo=repo,
        title=title,
        body=body,
        labels=labels,
    )

    assert isinstance(response_data, dict)
    assert response_data.get("title") == title
    assert response_data.get("body") == body
    if labels:
        returned_labels = [label["name"] for label in response_data.get("labels", [])]
        for label in labels:
            assert label in returned_labels


def test_get_issues(repository_setup):
    test_username, repo_name = repository_setup  # Get the repo name from the fixture
    repo = f"{test_username}/{repo_name}"
    state = "open"
    labels = "bug,test"

    title = "Test Issue Title"
    body = "This is a test issue created by an automated test."
    labels = ["bug", "test"]

    response_data = create_issue_tool(
        repo=repo,
        title=title,
        body=body,
        labels=labels,
    )

    response_data = get_issues_tool(
        repo=repo,
        state=state,
        labels=labels,
        per_page=5,
        page=1,
    )

    assert isinstance(response_data, dict)
    assert "issues" in response_data
    assert isinstance(response_data["issues"], list)
    for issue in response_data["issues"]:
        assert "title" in issue
        assert "url" in issue
        assert "state" in issue


def test_update_issue(repository_setup):
    test_username, repo_name = repository_setup  # Get the repo name from the fixture
    repo = f"{test_username}/{repo_name}"

    title = "Test Issue Title"
    response_data = create_issue_tool(
        repo=repo,
        title=title,
    )

    assert "number" in response_data

    issue_number = response_data["number"]

    # Attempt to update title and body
    response_data = update_issue_tool(
        repo=repo,
        issue_number=issue_number,
        title="Updated Title from Test",
        body="Updated body content from automated test.",
        state="closed",
        labels=["bug", "testing"],
    )

    assert isinstance(response_data, dict), "Expected response to be a dictionary"
    assert "title" in response_data, "Updated issue should contain 'title'"
    assert "body" in response_data, "Updated issue should contain 'body'"
    assert response_data["title"] == "Updated Title from Test"
    assert response_data["body"] == "Updated body content from automated test."


def test_create_issue_comment(repository_setup):
    test_username, repo_name = repository_setup  # Get the repo name from the fixture
    repo = f"{test_username}/{repo_name}"

    title = "Test Issue Title"
    response_data = create_issue_tool(
        repo=repo,
        title=title,
    )

    assert "number" in response_data

    issue_number = response_data["number"]
    comment = "This is a test comment added by an automated test."

    response_data = create_issue_comment_tool(
        repo=repo,
        issue_number=issue_number,
        comment=comment,
    )

    assert isinstance(response_data, dict)
    assert response_data.get("body") == comment
    assert "user" in response_data
    assert "created_at" in response_data


def test_get_issue_comments(repository_setup):
    test_username, repo_name = repository_setup  # Get the repo name from the fixture
    repo = f"{test_username}/{repo_name}"

    # Step 1: Create an issue
    title = "Test Issue for Comments"
    body = "This issue is used to test comment retrieval."
    labels = ["test"]
    issue_response = create_issue_tool(
        repo=repo,
        title=title,
        body=body,
        labels=labels,
    )
    issue_number = issue_response["number"]

    # Step 2: Add a comment to the issue
    comment_text = "This is a test comment."
    comment_response = create_issue_comment_tool(
        repo=repo,
        issue_number=issue_number,
        comment=comment_text,
    )
    assert comment_response["body"] == comment_text

    # Step 3: Retrieve the issue details and comments
    response_data = get_issue_comments_tool(
        issue_number=issue_number,
        repo=repo,
        page=1,
        per_page=10,
    )

    assert isinstance(response_data, dict)
    assert "issue" in response_data
    assert "comments" in response_data
    assert isinstance(response_data["comments"], list)
    assert response_data["issue"]["number"] == issue_number

    comment_bodies = [comment["body"] for comment in response_data["comments"]]
    assert comment_text in comment_bodies


def test_update_issue_comment(repository_setup):
    test_username, repo_name = repository_setup  # Get the repo name from the fixture
    repo = f"{test_username}/{repo_name}"

    # Step 1: Create a test issue
    issue_title = "Test Issue for Comment Update"
    issue_response = create_issue_tool(
        repo=repo,
        title=issue_title,
    )

    assert "number" in issue_response, "Issue creation failed"
    issue_number = issue_response["number"]

    # Step 2: Add a comment to the created issue
    original_comment = "Original comment for testing update."
    comment_response = create_issue_comment_tool(
        repo=repo,
        issue_number=issue_number,
        comment=original_comment,
    )

    assert "id" in comment_response, "Comment creation failed"
    comment_id = comment_response["id"]

    # Step 3: Update the comment
    updated_comment_text = "This comment has been updated by a test case."
    update_response = update_issue_comment_tool(
        comment_id=comment_id,
        new_comment=updated_comment_text,
        repo=repo,
    )

    assert isinstance(
        update_response, dict
    ), "Expected update response to be a dictionary"
    assert "body" in update_response, "Updated comment should contain 'body'"
    assert (
        update_response["body"] == updated_comment_text
    ), "Comment text was not updated"


def test_delete_issue_comment(repository_setup):
    test_username, repo_name = repository_setup
    repo_full_name = f"{test_username}/{repo_name}"

    test_username, repo_name = repository_setup  # Get the repo name from the fixture
    repo = f"{test_username}/{repo_name}"

    issue_title = "Test Issue for Comment Update"
    issue_response = create_issue_tool(
        repo=repo,
        title=issue_title,
    )

    assert "number" in issue_response, "Issue creation failed"
    issue_number = issue_response["number"]

    comment_body = "This is a test comment to be deleted."
    create_response = create_issue_comment_tool(
        repo=repo_full_name,
        issue_number=issue_number,
        comment=comment_body,
    )

    assert isinstance(create_response, dict)
    assert "id" in create_response, "ID not found after create_issue_comment_tool"
    comment_id = create_response["id"]

    response_data = delete_issue_comment_tool(
        repo=repo_full_name,
        comment_id=comment_id,
    )

    assert isinstance(response_data, dict)
    assert "confirmation_token" in response_data
    assert response_data["action"] == "confirm_deletion"

    confirmation_token = response_data["confirmation_token"]

    confirm_response = delete_issue_comment_tool(
        repo=repo_full_name,
        comment_id=comment_id,
        confirmation_token=confirmation_token,
    )

    assert isinstance(confirm_response, dict)
    assert confirm_response.get("message") == "Comment deleted successfully."


def test_get_issue_details(repository_setup):
    test_username, repo_name = repository_setup  # Get the repo name from the fixture
    repo = f"{test_username}/{repo_name}"

    # Step 1: Create an issue
    title = "Test Issue for Issue Details"
    body = "This issue is used to test retrieving issue details."
    labels = ["test"]
    issue_response = create_issue_tool(
        repo=repo,
        title=title,
        body=body,
        labels=labels,
    )
    issue_number = issue_response["number"]

    # Step 2: Retrieve the issue details
    response_data = get_issue_details_tool(
        issue_number=issue_number,
        repo=repo,
    )

    # Assertions with failure messages for better debugging
    assert isinstance(
        response_data, dict
    ), f"Expected response data to be a dictionary, but got {type(response_data)}"
    assert (
        "number" in response_data
    ), f"'number' key is missing in the response data: {response_data}"
    assert (
        response_data["number"] == issue_number
    ), f"Expected issue number {issue_number}, but got {response_data['number']}"
    assert (
        "title" in response_data
    ), f"'title' key is missing in the response data: {response_data}"
    assert (
        response_data["title"] == title
    ), f"Expected issue title '{title}', but got '{response_data['title']}'"
    assert (
        "body" in response_data
    ), f"'body' key is missing in the response data: {response_data}"
    assert (
        response_data["body"] == body
    ), f"Expected issue body '{body}', but got '{response_data['body']}'"
    assert (
        "labels" in response_data
    ), f"'labels' key is missing in the response data: {response_data}"
    assert isinstance(
        response_data["labels"], list
    ), f"Expected 'labels' to be a list, but got {type(response_data['labels'])}"
    assert (
        len(response_data["labels"]) == 1
    ), f"Expected 1 label, but got {len(response_data['labels'])} labels"
    assert (
        response_data["labels"][0]["name"] == "test"
    ), f"Expected label name 'test', but got '{response_data['labels'][0]['name']}'"


def test_search_issues(repository_setup):
    test_username, repo_name = repository_setup  # Get the repo name from the fixture
    repo = f"{test_username}/{repo_name}"
    state = "open"
    labels = "bug,test"
    query = "feature"
    search_comments = True

    # Create some test issues (assuming create_issue_tool works)
    title = "Test Issue Title"
    body = "This is a test issue created by an automated test."
    labels = ["bug", "test"]

    # Creating an issue using the create_issue_tool function
    create_issue_tool(
        repo=repo,
        title=title,
        body=body,
        labels=labels,
    )

    # Now, test the search_issues_tool function
    response_data = search_issues_tool(
        repo=repo,
        state=state,
        labels=labels,
        per_page=5,
        page=1,
        search_comments=search_comments,
        query=query,
    )

    # Validate the response
    assert isinstance(response_data, dict)
    assert "data" in response_data
    assert "issues" in response_data["data"]
    assert isinstance(response_data["data"]["issues"], list)

    for issue in response_data["data"]["issues"]:
        assert "title" in issue
        assert "url" in issue
        assert "state" in issue
        # Check if comments are being searched and included if there are any matches
        if search_comments:
            assert "messages" in issue  # Check for matching comments
            assert isinstance(issue["messages"], list)
            for message in issue["messages"]:
                assert "comment" in message
                assert (
                    query in message["comment"]
                )  # Ensure the comment matches the search query


def test_search_issues_with_comments(repository_setup):
    test_username, repo_name = repository_setup  # Get the repo name from the fixture
    repo = f"{test_username}/{repo_name}"
    state = "open"
    labels = "bug,test"
    query = "test comment"  # We will search for this comment text in the issue
    search_comments = True

    # Create an issue using the create_issue_tool function
    title = "Test Issue Title"
    response_data = create_issue_tool(
        repo=repo,
        title=title,
    )

    assert "number" in response_data  # Ensure the issue was created and has a number

    issue_number = response_data["number"]
    comment = "This is a test comment added by an automated test."

    # Create a comment on the issue using the create_issue_comment_tool function
    response_data = create_issue_comment_tool(
        repo=repo,
        issue_number=issue_number,
        comment=comment,
    )

    assert "id" in response_data  # Ensure the comment was created and has an ID

    # Now, test the search_issues_tool function, searching for the comment
    response_data = search_issues_tool(
        repo=repo,
        state=state,
        labels=labels,
        per_page=5,
        page=1,
        search_comments=search_comments,
        query=query,
    )

    # Validate the response
    assert isinstance(response_data, dict)
    assert "data" in response_data
    assert "issues" in response_data["data"]
    assert isinstance(response_data["data"]["issues"], list)

    for issue in response_data["data"]["issues"]:
        assert "title" in issue
        assert "url" in issue
        assert "state" in issue
        # Check if comments are being searched and included if there are any matches
        if search_comments:
            assert "messages" in issue  # Check for matching comments
            assert isinstance(issue["messages"], list)
            for message in issue["messages"]:
                assert "comment" in message
                assert (
                    query in message["comment"]
                )  # Ensure the comment matches the search query
