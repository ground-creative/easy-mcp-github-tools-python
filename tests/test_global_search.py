import os
import sys
from app.tools.global_search import global_search_tool

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def test_global_search_tool_repositories(auth_setup):
    search_type = "repositories"
    query = "machine learning"

    result = global_search_tool(search_type=search_type, query=query)

    assert isinstance(result, dict)
    assert "results" in result
    assert "total_count" in result
    assert "page" in result
    assert "per_page" in result
    assert isinstance(result["results"], list)
    assert isinstance(result["total_count"], int)


def test_global_search_tool_code(auth_setup):
    result = global_search_tool(search_type="code", query="authentication")

    assert isinstance(result, dict)
    assert "results" in result
    assert isinstance(result["results"], list)


def test_global_search_tool_invalid_type(auth_setup):
    result = global_search_tool(search_type="invalid", query="test")

    assert isinstance(result, dict)
    assert "error" in result
