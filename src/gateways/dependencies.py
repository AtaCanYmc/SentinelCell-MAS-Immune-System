import os
import asyncio
import orjson
from fastapi import HTTPException, WebSocket, Depends, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.core.session_manager import verify_session_token
from src.core.logger import get_console

console = get_console()
security = HTTPBearer(auto_error=False)


def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    sentinel_session: str | None = Cookie(None),
):
    expected_api_key = os.getenv("API_KEY_SECRET")
    if not expected_api_key:
        return True

    # 1. Check for cookie-based session token
    if sentinel_session:
        username = verify_session_token(sentinel_session)
        if username:
            return username

    # 2. Check for Bearer token (API_KEY_SECRET)
    if credentials and credentials.credentials == expected_api_key:
        return credentials.credentials

    # If neither matches
    raise HTTPException(status_code=401, detail="Invalid or missing API Key or Session")


async def verify_api_key_in_ws(websocket: WebSocket):
    expected_api_key = os.getenv("API_KEY_SECRET")
    if not expected_api_key:
        return True

    session_cookie = websocket.cookies.get("sentinel_session")
    has_valid_cookie = (
        session_cookie and verify_session_token(session_cookie) is not None
    )

    if has_valid_cookie:
        return True

    try:
        auth_msg = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
        auth_data = orjson.loads(auth_msg)
        if (
            auth_data.get("type") == "AUTH"
            and auth_data.get("token") == expected_api_key
        ):
            return True
        else:
            await websocket.send_text(
                orjson.dumps({"type": "AUTH_FAILED"}).decode("utf-8")
            )
            await websocket.close(code=1008)
            raise HTTPException(
                status_code=401, detail="Invalid or missing API Key or Session"
            )
    except (asyncio.TimeoutError, Exception):
        console.print(
            "[bold red]WebSocket auth failed: Timeout or error during auth message receive[/bold red]"
        )
        try:
            await websocket.close(code=1008)
        except Exception:
            pass
        raise HTTPException(
            status_code=401, detail="Invalid or missing API Key or Session"
        )
