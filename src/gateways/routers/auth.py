import os
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from src.core.session_manager import create_session_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
async def login(req: LoginRequest):
    expected_user = os.getenv("DASHBOARD_USERNAME", "admin")
    expected_pass = os.getenv("DASHBOARD_PASSWORD", "sentinel")

    if req.username != expected_user or req.password != expected_pass:
        return JSONResponse(
            status_code=401,
            content={"status": "error", "message": "Invalid credentials"},
        )

    import uuid

    session_token = create_session_token(req.username)
    csrf_token = uuid.uuid4().hex
    response = JSONResponse(content={"status": "success", "username": req.username})
    response.set_cookie(
        key="sentinel_session",
        value=session_token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=86400,
    )
    response.set_cookie(
        key="sentinel_csrf",
        value=csrf_token,
        httponly=False,
        samesite="lax",
        secure=False,
        max_age=86400,
    )
    return response


@router.post("/logout")
async def logout():
    response = JSONResponse(content={"status": "success"})
    response.delete_cookie(key="sentinel_session")
    return response
