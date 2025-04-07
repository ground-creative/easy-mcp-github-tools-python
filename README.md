# Eeasy MCP Github Tools

This is a set of tools for github to be used with easy mcp server.<br>
https://github.com/ground-creative/easy-mcp-python

## Capabilities

- List items in drive folders
- Get items detailed info by id or name
- Read/Create/Edit documents
- Read/Create/Edit spreadsheets
- Delete items
- Move items to other folders

## Authentication

This application uses github oauth service to authenticate the user.<br>
By going to /auth/login page you can authenticate with github and get an access token.

### How To Authenticate

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

5. Create json file `client_credentials.json` with github oauth credentials in storage folder:

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
