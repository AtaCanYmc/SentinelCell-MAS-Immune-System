import os
from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from typing import List, Any, Optional
from langchain_core.callbacks.manager import CallbackManagerForLLMRun


class MockChatModel(BaseChatModel):
    """
    A lightweight mock chat model to simulate healing and inference without external API calls.
    """

    model_name: str = "mock-model"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        # Fallback to synchronous generation
        import asyncio

        return asyncio.run(self._agenerate(messages, stop, run_manager, **kwargs))

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        prompt_text = ""
        for m in messages:
            if isinstance(m, str):
                prompt_text += m
            elif hasattr(m, "content"):
                prompt_text += str(m.content)

        prompt_lower = prompt_text.lower()
        content = '{"status": "ok", "message": "Healed via LLM fallback"}'

        if "iot" in prompt_lower or "telemetry" in prompt_lower:
            content = '{"device_id": "sensor-123", "temperature": 22.5, "status": "nominal", "timestamp": 1719734400}'
        elif (
            "finance" in prompt_lower
            or "transaction" in prompt_lower
            or "fintech" in prompt_lower
        ):
            content = '{"transaction_id": "TXN-9999", "status": "completed", "amount": 150.00, "currency": "USD", "timestamp": 1719734400}'
        elif "schema" in prompt_lower and "inference" in prompt_lower:
            content = '{"type": "object", "properties": {"status": {"type": "string"}, "message": {"type": "string"}}, "required": ["status", "message"]}'
        elif "agent_beta" in prompt_lower or "beta" in prompt_lower:
            content = '{"status": "ok", "message": "Healed via LLM fallback"}'

        # Format as markdown block if expected
        if "json" in prompt_lower:
            content = f"```json\n{content}\n```"

        message = AIMessage(content=content)
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])

    @property
    def _llm_type(self) -> str:
        return "mock-chat-model"


class LLMFactory:
    """
    Model Agnostic LLM Factory.
    Creates ChatModel instances based on provider configurations.
    """

    @staticmethod
    def _get_key(env_var: str) -> SecretStr:
        val = os.getenv(env_var)
        if not val or "your_" in val:
            raise ValueError(
                f"Missing required API key: {env_var}. Cannot use dummy keys in production."
            )
        return SecretStr(val)

    @staticmethod
    def get_llm(provider: str) -> BaseChatModel:
        # Check if MOCK_LLM is enabled or if the requested provider's key is missing/dummy
        provider = provider.upper()
        env_var_map = {
            "OPENAI": "OPENAI_API_KEY",
            "DEEPSEEK": "DEEPSEEK_API_KEY",
            "GEMINI": "GEMINI_API_KEY",
            "ANTHROPIC": "ANTHROPIC_API_KEY",
            "GROQ": "GROQ_API_KEY",
        }

        should_mock = os.getenv("MOCK_LLM") == "true"
        if not should_mock and provider in env_var_map:
            key_var = env_var_map[provider]
            key_val = os.getenv(key_var)
            if not key_val or "your_" in key_val:
                should_mock = True

        if should_mock:
            return MockChatModel()

        if provider == "OPENAI":
            return ChatOpenAI(
                api_key=LLMFactory._get_key("OPENAI_API_KEY"),
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                temperature=0,
            )
        elif provider == "ANTHROPIC":
            return ChatAnthropic(
                api_key=LLMFactory._get_key("ANTHROPIC_API_KEY"),
                model_name=os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307"),
                temperature=0,
                timeout=None,
                stop=None,
            )
        elif provider == "LOCAL_OLLAMA":
            # If Ollama connection fails, we can fall back to mock
            return ChatOllama(
                model=os.getenv("OLLAMA_MODEL", "llama3.1"),
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                temperature=0,
            )
        elif provider == "GROQ":
            return ChatGroq(
                api_key=LLMFactory._get_key("GROQ_API_KEY"),
                model=os.getenv("GROQ_MODEL", "llama3-70b-8192"),
                temperature=0,
            )
        elif provider == "GEMINI":
            return ChatGoogleGenerativeAI(
                model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
                google_api_key=LLMFactory._get_key("GEMINI_API_KEY"),
                temperature=0,
            )
        elif provider == "DEEPSEEK":
            return ChatOpenAI(
                api_key=LLMFactory._get_key("DEEPSEEK_API_KEY"),
                model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                base_url="https://api.deepseek.com/v1",
                temperature=0,
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
