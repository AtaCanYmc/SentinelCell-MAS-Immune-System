import os
import time
import orjson
import dotenv
from fastapi import APIRouter, HTTPException, Depends
from src.gateways.shared import sentinel
from src.gateways.dependencies import verify_api_key

router = APIRouter(tags=["agents"])


@router.get("/api/agents")
async def get_agents(api_key: str = Depends(verify_api_key)):
    """Returns the current state of agent circuit breakers."""
    threshold = int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "5"))
    cooldown = int(os.getenv("CIRCUIT_BREAKER_COOLDOWN", "60"))
    breakers = sentinel.orchestrator.agent_circuit_breakers
    result = []
    for agent, errors in await breakers.items():
        failures = (
            errors.get("failures", 0) if isinstance(errors, dict) else (errors or 0)
        )
        last_failure = (
            errors.get("last_failure_time", 0.0) if isinstance(errors, dict) else 0.0
        )

        status = "HEALTHY"
        if failures >= threshold:
            if time.time() - last_failure > cooldown:
                status = "RECOVERING"
            else:
                status = "TRIPPED"

        result.append(
            {
                "id": agent,
                "errors": errors,
                "status": status,
                "threshold": threshold,
                "last_failure_time": last_failure,
                "cooldown": cooldown,
            }
        )
    return {"agents": result}


@router.post("/api/agents/{agent_id}/reset")
async def reset_agent(agent_id: str, api_key: str = Depends(verify_api_key)):
    if await sentinel.orchestrator.agent_circuit_breakers.exists(agent_id):
        await sentinel.orchestrator.agent_circuit_breakers.set(
            agent_id,
            {
                "failures": 0,
                "last_failure_time": 0.0,
            },
        )
    return {"status": "ok", "agent": agent_id, "errors": 0}


@router.delete("/memory/purge")
async def purge_memory(days: int = 30, api_key: str = Depends(verify_api_key)):
    """
    Purges old hallucination corrections from the VectorDB
    to prevent memory bloat and maintain optimal RAG performance.
    """
    try:
        from src.core.memory_factory import MemoryFactory

        if days <= 0:
            raise ValueError("days parameter must be positive")
        memory_store = MemoryFactory.get_memory_store()
        deleted_count = memory_store.purge_old_memories(days=days)
        return {
            "status": "success",
            "message": f"Purged memories older than {days} days.",
            "deleted_count": deleted_count,
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        import logging

        logging.getLogger(__name__).error("Memory Purge Error: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Memory purge operation failed. Check server logs for details.",
        )


@router.post("/schema/refresh")
async def refresh_schema(
    agent_target: str = None, api_key: str = Depends(verify_api_key)
):
    """
    Purges the local schema cache for a specific agent, or all agents if none provided.
    This guarantees instant consistency for the next payload without waiting for TTL.
    """
    try:
        if agent_target:
            sentinel.validator.clear_cache(agent_target)
            return {
                "status": "success",
                "message": f"Schema cache cleared for {agent_target}",
            }
        else:
            sentinel.validator.clear_cache()
            return {"status": "success", "message": "All schema caches cleared"}
    except Exception as e:
        import logging

        logging.getLogger(__name__).error("Schema Refresh Error: %s", e)
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred. Check server logs for details.",
        )


@router.get("/api/schemas")
async def get_all_schemas(api_key: str = Depends(verify_api_key)):
    """Returns all schemas currently stored in the active Registry Store."""
    try:
        from src.core.registry_factory import RegistryFactory

        store = RegistryFactory.get_registry_store()
        schemas = await store.get_all_schemas()
        return {
            agent_id: orjson.loads(schema_str)
            if isinstance(schema_str, str)
            else schema_str
            for agent_id, schema_str in schemas.items()
        }
    except Exception as e:
        import logging

        logging.getLogger(__name__).error("Schema Fetch Error: %s", e)
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred. Check server logs for details.",
        )


@router.get("/api/config")
async def get_config(api_key: str = Depends(verify_api_key)):
    """Returns all environment variables for the settings dashboard."""
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    env_path = os.path.join(base_dir, ".env")
    config = dotenv.dotenv_values(env_path)
    return {k: v if v is not None else "" for k, v in config.items()}
