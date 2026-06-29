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
    def get_operation_mode(reason: str) -> str:
        """Returns the current system operation mode (Active/Passive).
        ONLY call this tool if the user explicitly asks about the active/passive mode or operation mode.
        Args:
            reason: The explicit reason why you are querying the operation mode.
        """
        mode = (
            "Sniffer Mode (Passive)"
            if os.getenv("PASSIVE_MONITORING") == "true"
            else "Guardian Mode (Active)"
        )
        return mode

    @tool
    async def get_llm_metrics(reason: str) -> str:
        """Queries Redis to get current LLM rate limits and request counts for the current minute.
        ONLY call this tool if the user explicitly asks for LLM metrics, rate limits, or usage.
        Args:
            reason: The explicit reason why you are querying the LLM metrics.
        """
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
    def get_agent_circuit_breakers(reason: str) -> str:
        """Returns the health status and error count of all agent circuit breakers in the system.
        ONLY call this tool if the user explicitly asks about agent health, circuit breakers, or error counts.
        Args:
            reason: The explicit reason why you are querying the agent circuit breakers.
        """
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

    @tool
    def read_project_readme(reason: str) -> str:
        """Reads and returns the contents of the project's README.md file.
        ONLY call this tool if the user explicitly asks about the project documentation,
        overview, instructions, how it works, installation, run commands, or system architecture.
        Args:
            reason: The explicit reason why you need to read the project README.
        """
        readme_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "README.md"
        )
        if not os.path.exists(readme_path):
            return "Error: README.md not found in the project root."
        try:
            with open(readme_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error reading README.md: {e}"

    return [
        get_operation_mode,
        get_llm_metrics,
        get_agent_circuit_breakers,
        read_project_readme,
    ]
