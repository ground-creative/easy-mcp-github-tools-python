import os, base64, json
from fastapi.templating import Jinja2Templates
from fastapi import Cookie
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse
from core.utils.logger import logger
from core.utils.config import config
from core.utils.env import EnvConfig
from core.utils.state import global_state
import httpx

server_info_config = config.get("INFO_SERVICE_CONFIG", {})
main_url = server_info_config.get("service_uri", "/")
login_uri = "/auth/login"
templates_directory = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../templates")
)
templates = Jinja2Templates(directory=templates_directory)

router = APIRouter()

# GitHub OAuth Constants
GITHUB_OAUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_OAUTH_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_OAUTH_USER_URL = "https://api.github.com/user"


@router.get("/auth")
async def github_login(request: Request):
    return RedirectResponse(url=login_uri)


@router.get(login_uri)
async def github_login(request: Request, current_access_token: str = None):
    logger.info("User initiated GitHub login process.")

    with open("storage/client_credentials.json") as f:
        credentials = json.load(f)

    # Prepare the state data
    state_data = {
        "current_access_token": current_access_token,
    }
    state_encoded = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()

    # Generate the authorization URL with the state parameter
    authorization_url = f"{GITHUB_OAUTH_URL}?client_id={credentials.get('client_id')}&redirect_uri={EnvConfig.get('APP_HOST')}/auth/callback&scope={config.get('GITHUB_SCOPE')}&state={state_encoded}"

    logger.info("Redirecting user to GitHub authorization URL.")
    return RedirectResponse(url=authorization_url)


@router.get("/auth/callback")
async def github_auth_callback(request: Request):
    logger.info("Handling GitHub authentication callback.")

    if "error" in request.query_params:
        error_message = request.query_params["error"]
        logger.error(f"Authentication failed: {error_message}")
        return RedirectResponse(url="/auth/login")

    try:
        # Retrieve and decode the state parameter
        state_encoded = request.query_params.get("state")
        current_access_token = None

        if state_encoded:
            # Decode the state parameter
            state_data = json.loads(base64.urlsafe_b64decode(state_encoded).decode())
            current_access_token = state_data.get("current_access_token")

        code = request.query_params.get("code")

        with open("storage/client_credentials.json") as f:
            credentials = json.load(f)

        client_id = credentials.get("client_id")
        client_secret = credentials.get("client_secret")
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                GITHUB_OAUTH_TOKEN_URL,
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "redirect_uri": f"{EnvConfig.get('APP_HOST')}/auth/callback",
                    "state": state_encoded,
                },
                headers={"Accept": "application/json"},
            )

            token_data = token_response.json()
            access_token = token_data.get("access_token")

        if not access_token:
            logger.error("Failed to obtain access token from GitHub.")
            return RedirectResponse(url="/auth/login")

        # Fetch user information
        async with httpx.AsyncClient() as client:
            user_response = await client.get(
                GITHUB_OAUTH_USER_URL,
                headers={"Authorization": f"token {access_token}"},
            )
            user_info = user_response.json()
            user_id = user_info.get("id")

        db_handler = global_state.get("db_handler")

        # If current_access_token is provided, delete the existing credentials
        if current_access_token:
            logger.info(
                f"Deleting credentials for access token: {current_access_token}"
            )
            db_handler.delete_credentials(current_access_token, user_id)

        # Store the new credentials
        credentials_json = {
            "access_token": access_token,
            "user_id": user_id,
            # Add any other relevant user info here
        }
        # db_handler.insert_credentials(user_id, credentials_json)
        app_access_token = db_handler.insert_credentials(str(user_id), credentials_json)
        logger.info("User authenticated successfully with GitHub, credentials saved.")

        # Store user_id in cookie
        response = RedirectResponse(url="/auth/authenticated")
        response.set_cookie(
            key="access_token", value=app_access_token, httponly=True
        )  # Set cookie
        return response

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)


@router.get("/auth/authenticated")
async def github_authenticated(request: Request, access_token: str = Cookie(None)):
    logger.info("User accessed the authenticated route.")

    if access_token is None:
        return RedirectResponse(url="/auth/login")

    db_handler = global_state.get("db_handler")
    credentials = db_handler.get_credentials(access_token)

    if not credentials:
        logger.warning("Credentials not found for access token.")
        return RedirectResponse(url="/auth/login")

    site_url = server_info_config.get("site_url", "")
    site_name = server_info_config.get("site_name", site_url)

    return templates.TemplateResponse(
        "authenticated.html",
        {
            "request": request,
            "encrypted_user_id": access_token,
            "logo_url": EnvConfig.get("SERVICES_LOGO_URL"),
            "login_uri": login_uri,
            "service_info_url": EnvConfig.get("APP_HOST"),
            "favicon_url": EnvConfig.get("SERVICES_FAVICON_URL"),
            "site_url": site_url,
            "site_name": site_name,
            "mcp_server_url": f"{EnvConfig.get('MCP_SERVER_URL')}",
            "mcp_server_name": EnvConfig.get("SERVER_NAME"),
        },
    )


@router.get("/auth/reset-access-token")
async def github_reset_access_token(request: Request, access_token: str = Cookie(None)):
    logger.info("User accessed the reset access token route.")

    if access_token is None:
        return RedirectResponse(url="/auth/login")

    return RedirectResponse(url=f"/auth/login?current_access_token={access_token}")
