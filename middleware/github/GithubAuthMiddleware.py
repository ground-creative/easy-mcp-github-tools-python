import json
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from cryptography.fernet import Fernet
from core.utils.env import EnvConfig
from core.utils.state import global_state
from core.utils.logger import logger


# Load the encryption key from the environment variable
CYPHER = EnvConfig.get("CYPHER").encode()  # Ensure it's in bytes
fernet = Fernet(CYPHER)


class GithubAuthMiddleware(BaseHTTPMiddleware):

    def __init__(self, app, *args, **kwargs):
        super().__init__(app)
        self.db_handler = global_state.get("db_handler")

    async def dispatch(self, request: Request, call_next):
        logger.info("MCP Route middleware GithubAuthMiddleware checking credentials")
        try:
            global_state.set(
                "middleware.GithubAuthMiddleware.is_authenticated", False, True
            )
            access_token = request.headers.get("x-access-token", None)

            if not access_token:
                global_state.set(
                    "error_message",
                    f"X-ACCESS-TOKEN is a required header parameter. Please go to {EnvConfig.get('APP_HOST')}/auth/login to get the required paramaters.",
                    True,
                )
                logger.warning("No access token found in header.")
                return await call_next(request)

            try:
                cred = self.db_handler.get_credentials(access_token)
            except Exception as e:
                global_state.set(
                    "error_message",
                    f"There has been an error with authenticating, please go to {EnvConfig.get('APP_HOST')}/auth/login and authenticate again",
                    True,
                )
                logger.warning("There has been an error with authenticating.")
                return await call_next(request)

            if "error" in cred:
                global_state.set(
                    "error_message",
                    f"There has been an error with authenticating, please go to {EnvConfig.get('APP_HOST')}/auth/login and authenticate again",
                    True,
                )
                logger.warning("No credentials found. Redirecting to login.")
                return await call_next(request)  # Proceed without authentication

            global_state.set(
                "middleware.GithubAuthMiddleware.is_authenticated", True, True
            )
            global_state.set(
                "middleware.GithubAuthMiddleware.credentials", cred["credentials"], True
            )
            logger.info("User login successful.")
            repo = request.headers.get("x-repo", None)

            if repo:
                logger.info(
                    f"GithubAuthMiddleware: Adding repo `{repo}` to global state"
                )
                global_state.set("middleware.GithubAuthMiddleware.repo", repo, True)

            response = await call_next(request)
            return response

        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            global_state.set(
                "error_message",
                f"There has been an error with authenticating, please go to {EnvConfig.get('APP_HOST')}/auth/login to authenticate",
                True,
            )
            return await call_next(request)  # Proceed without authentication


def check_access(returnJsonOnError=False):

    if not global_state.get("middleware.GithubAuthMiddleware.is_authenticated"):
        logger.error("GithubAuthMiddleware: User is not authenticated.")

        if returnJsonOnError:
            return json.dumps(
                {
                    "status": "error",
                    "error": global_state.get(
                        "error_message", "User is not authenticated."
                    ),
                }
            )

        return "User is not authenticated."

    return None  # Return None if authenticated
