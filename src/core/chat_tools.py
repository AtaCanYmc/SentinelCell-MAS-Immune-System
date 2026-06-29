import os
import time
import redis.asyncio as redis
from langchain_core.tools import tool

def get_chat_tools(sentinel_cell):
    """
    Factory function to generate LLM tools for the chat assistant.
    Captures the sentinel_cell instance to query agent circuit breakers dynamically.
    """

    @tool
    def get_system_time() -> str:
        """Returns the current system date and time."""
        return time.strftime("%Y-%m-%d %H:%M:%S")

    @tool
    def get_operation_mode() -> str:
        """Returns the current system operation mode (Active/Passive)."""
        mode = (
            "Sniffer Mode (Passive)"
            if os.getenv("PASSIVE_MONITORING") == "true"
            else "Guardian Mode (Active)"
        )
        return mode

    @tool
    async def get_llm_metrics() -> str:
        """Queries Redis to get current LLM rate limits and request counts for the current minute."""
        try:
            r = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))
            current_minute = int(time.time() / 60)
            llm_requests = await r.get(f"sentinel:llm_rate_limit:{current_minute}")
            reqs = int(llm_requests) if llm_requests else 0
            limit = int(os.getenv("LLM_RATE_LIMIT_PER_MIN", "50"))
            return f"LLM Requests in current minute: {reqs} / {limit} (Max allowed per min: {limit})"
        except Exception as e:
            return f"Error retrieving LLM metrics: {e}"

    @tool
    def get_agent_circuit_breakers() -> str:
        """Returns the health status and error count of all agent circuit breakers in the system."""
        try:
            threshold = int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "5"))
            breakers = sentinel_cell.orchestrator.agent_circuit_breakers
            if not breakers:
                return "All agents healthy. No error counts recorded."

            status_list = []
            for agent, errors in breakers.items():
                status = "TRIPPED (Blocked)" if errors >= threshold else "HEALTHY"
                status_list.append(
                    f"Agent: {agent} | Errors: {errors}/{threshold} | Status: {status}"
                )
            return "\n".join(status_list)
        except Exception as e:
            return f"Error retrieving agent circuit breakers: {e}"

    return [get_system_time, get_operation_mode, get_llm_metrics, get_agent_circuit_breakers]
