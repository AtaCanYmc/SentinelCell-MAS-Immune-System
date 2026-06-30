import os


def setup_mock_environment():
    """Detects missing API keys and sets MOCK_LLM=true if needed."""
    openai_key = os.getenv("OPENAI_API_KEY", "")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")

    # Check if keys are missing or placeholders
    if (not openai_key or openai_key == "your_openai_api_key") and (
        not anthropic_key or anthropic_key == "your_anthropic_api_key"
    ):
        os.environ["MOCK_LLM"] = "true"


async def shutdown_sentinel(sentinel):
    """Safely stops the SentinelCell client."""
    if hasattr(sentinel, "stop"):
        await sentinel.stop()
