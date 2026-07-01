import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.websockets import WebSocketState
from pydantic import BaseModel
from src.gateways.shared import sentinel
from src.gateways.dependencies import verify_api_key, verify_api_key_in_ws
from src.gateways.services.chat_srv import ChatService
from src.core.logger import get_console

console = get_console()
router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str


@router.post("/chat/test")
async def chat_test(req: ChatRequest, api_key: str = Depends(verify_api_key)):
    """
    Direct endpoint to test the configured LLM models.
    """
    try:
        from src.core.llm_factory import LLMFactory

        provider = os.getenv("PROVIDER_ORDER", "OPENAI").split(",")[0].strip()
        llm = LLMFactory.get_llm(provider)
        response = await llm.ainvoke(req.message)
        return {
            "status": "success",
            "response": response.content,
            "provider": provider,
        }
    except ValueError as ve:
        console.print(f"[bold yellow]LLM Configuration Error:[/bold yellow] {ve}")
        raise HTTPException(
            status_code=400,
            detail="LLM provider is not properly configured.",
        )
    except Exception as e:
        console.print(f"[bold red]Chat Test Error:[/bold red] {e}")
        raise HTTPException(
            status_code=500,
            detail="LLM request failed. Check server logs for details.",
        )


@router.websocket("/ws/chat")
async def websocket_chat(
    websocket: WebSocket,
    lang: str = "en",
    provider: str | None = None,
):
    """
    WebSocket endpoint for real-time LLM chat streaming.
    """
    try:
        await websocket.accept()
    except RuntimeError:
        pass

    # First Message Auth
    await verify_api_key_in_ws(websocket)

    provider_order = os.getenv("PROVIDER_ORDER", "OPENAI").split(",")
    if not provider:
        provider = provider_order[0].strip()

    if provider not in provider_order:
        console.print(
            f"[bold yellow]Warning: Requested provider '{provider}' is not in PROVIDER_ORDER. "
        )
        await websocket.close(reason=f"Available providers: {provider_order}")
        raise HTTPException(
            status_code=400,
            detail=f"Requested provider '{provider}' is not in PROVIDER_ORDER. ",
        )

    try:
        await ChatService.handle_websocket_chat(websocket, sentinel, provider, lang)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        console.print(f"[bold red]WebSocket chat error:[/bold red] {e}")
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                import orjson

                await websocket.send_text(
                    orjson.dumps({"type": "error", "content": str(e)}).decode("utf-8")
                )
            except Exception as send_err:
                console.print(
                    f"[bold red]WebSocket error sending error message:[/bold red] {send_err}"
                )
                pass
