from core.utils.env import EnvConfig

SERVICES = [
    "core.services.server_info",
    "app.services.authentication",
    "app.services.default_tools_messages",
]

INFO_SERVICE_CONFIG = {
    "service_uri": "/",
    "login_url": f"{EnvConfig.get('APP_HOST')}/auth/login",
    "site_url": EnvConfig.get("SITE_URL"),
    "site_name": EnvConfig.get("SITE_NAME"),
    "show_tools_specs": True,
    "header_params": {
        "X-ACCESS-TOKEN": "(Required) The access token for authenticating with the services, you can get one once you are authenticated via the login process."
    },
    "notes": ["All tools that use delete actions require confirmation, this is an experimental feature."]
}

PRESTART_HOOKS = {
    "fastapi": ["app.middleware.github.database.init_db"],
}

GITHUB_SCOPE = "repo,delete_repo"

MIDDLEWARE = {
    "mcp": [{"middleware": "app.middleware.github.GithubAuthMiddleware", "priority": 1}]
}
