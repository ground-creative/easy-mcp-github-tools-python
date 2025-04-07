# Eeasy MCP GitHub Tools

This is a set of tools for github to be used with easy mcp server.<br>
https://github.com/ground-creative/easy-mcp-python

## Capabilities

- Fetch commit history from a GitHub repository.
- Fetch details for multiple files from a GitHub repository.
- Fetch detailed information for a specific commit from a GitHub repository.

## Authentication

This application uses GitHub oAuth service to authenticate the user.

How To Authenticate:

1. Go to auth/login and authenticate

2. Use the paramater X-ACCESS-TOKEN with the request headers when making calls to the server.

## Installation

1. Clone the repository from the root folder of the easy mcp installation:

```
git clone https://github.com/ground-creative/easy-mcp-github-tools-python.git app
```

2. Install requirements:

```
pip install -r app/requirements.txt
```

3. Generate encryption key:

```
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

4. Add parameters to env file:

```
APP_HOST=Application Host ex: `https://mcp.yourdomain.com`
DB_PATH=storage/sqlite_credentials.db
CYPHER=Your Encryption Key Here

# Optional
SITE_URL=Main Application Site URL
SITE_NAME=MAin Application Site Name
```

5. Create json file `client_credentials.json` with GitHub oauth credentials in storage folder:

```
{
    "client_id": "XXXXX",
    "client_secret": "XXXXXXX"
}
```

6. Run the server:

```
# Run via fastapi wrapper
python3 run.py -s fastapi
```
