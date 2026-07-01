import os
import orjson
from fastapi import APIRouter, WebSocket, Depends, HTTPException
from pydantic import BaseModel
from src.gateways.shared import sentinel
from src.gateways.dependencies import verify_api_key
from src.gateways.services.execution_srv import ExecutionService
from src.core.logger import get_console

console = get_console()
router = APIRouter(tags=["examples"])


class ReplayRequest(BaseModel):
    source: str
    target: str
    payload: str


@router.post("/api/dlq/replay")
async def replay_payload(req: ReplayRequest, api_key: str = Depends(verify_api_key)):
    """Manually replays a payload from the Quarantine UI."""
    try:
        result = await sentinel.intercept(
            source=req.source, target=req.target, payload=req.payload
        )
        if result is None:
            raise HTTPException(
                status_code=400,
                detail="Replay failed. Payload was rejected again.",
            )
        return {"status": "success", "result": result}
    except HTTPException:
        raise
    except Exception as e:
        console.print(f"[bold red]DLQ Replay Error:[/bold red] {e}")
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred. Check server logs for details.",
        )


@router.get("/api/examples")
async def list_examples(api_key: str = Depends(verify_api_key)):
    """Lists available interactive simulation examples with description."""
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    json_path = os.path.join(base_dir, "examples", "examples.json")
    if not os.path.exists(json_path):
        return {"examples": []}
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            examples = orjson.loads(f.read())
        return {"examples": examples}
    except Exception as e:
        console.print(f"[bold red]Error reading examples.json:[/bold red] {e}")
        return {"examples": []}


@router.websocket("/ws/examples/run/{script_name}")
async def ws_run_example(websocket: WebSocket, script_name: str):
    """Runs a simulation script and streams stdout/stderr back in real-time."""
    await ExecutionService.run_simulation_script(websocket, script_name)
