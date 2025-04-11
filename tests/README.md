# Running Tests Specs

## Installation

1. Add variables .env in root folder:

```
TEST_TOKEN=Your github token
TEST_USERNAME=Your github username
```

2. Install pytest:

```
pip install pytest==8.3.5
```

3. Run the tests:

```
# Run all tests
pytest

# Run all test of file
pytest test_branch_tools.py

# Run specific test
pytest test_branch_tools.py::test_create_branch
```
