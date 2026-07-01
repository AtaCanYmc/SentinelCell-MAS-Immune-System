import os
import time
import orjson
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import redis.asyncio as redis
from src.gateways.dependencies import verify_api_key
from src.core.logger import get_console

console = get_console()
router = APIRouter(tags=["hitl"])


class HITLApprovalRequest(BaseModel):
    approval_id: str
    decision: str  # "APPROVED" or "REJECTED"


@router.post("/api/hitl/approval")
async def submit_hitl_approval(
    req: HITLApprovalRequest, api_key: str = Depends(verify_api_key)
):
    """
    Submits HITL (Human-in-the-Loop) approval decision.
    Dashboard operator clicks "Approve" or "Reject" to trigger this endpoint.
    """
    try:
        if req.decision not in ["APPROVED", "REJECTED"]:
            raise HTTPException(
                status_code=400,
                detail="Decision must be 'APPROVED' or 'REJECTED'",
            )

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url)

        # Retrieve and update pending status from Redis
        hitl_key = f"sentinel:hitl:{req.approval_id}"
        approval_data = await r.get(hitl_key)

        if not approval_data:
            await r.aclose()
            raise HTTPException(
                status_code=404,
                detail="HITL approval ID not found or expired",
            )

        data = orjson.loads(approval_data)
        data["status"] = req.decision
        data["decided_at"] = time.time()

        await r.setex(
            hitl_key,
            300,  # 5 minute TTL
            orjson.dumps(data).decode("utf-8"),
        )

        # Notify dashboard via Redis PubSub
        await r.publish(
            "sentinel.logs",
            orjson.dumps(
                {
                    "type": "HITL_DECISION",
                    "approval_id": req.approval_id,
                    "decision": req.decision,
                }
            ).decode("utf-8"),
        )

        # Also notify the orchestrator (or any waiter) via the HITL decision channel
        try:
            await r.publish(
                f"sentinel:hitl:channel:{req.approval_id}",
                orjson.dumps(data).decode("utf-8"),
            )
        except Exception as e:
            console.print(
                f"[bold yellow]HITL decision channel publish error:[/bold yellow] {e}"
            )
            pass

        await r.aclose()

        return {
            "status": "success",
            "message": f"HITL approval {req.decision}",
            "approval_id": req.approval_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        console.print(f"[bold red]HITL Approval Error:[/bold red] {e}")
        raise HTTPException(
            status_code=500,
            detail="HITL approval submission failed. Check server logs for details.",
        )
