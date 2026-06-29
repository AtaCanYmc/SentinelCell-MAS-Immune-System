import os
from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models.chat_models import BaseChatModel


class LLMFactory:
    """
    Model Agnostic LLM Factory.
    Creates ChatModel instances based on provider configurations.
    """

    @staticmethod
    def _get_key(env_var: str) -> SecretStr:
        val = os.getenv(env_var)
        if not val:
            raise ValueError(
                f"Missing required API key: {env_var}. Cannot use dummy keys in production."
            )
        return SecretStr(val)

    @staticmethod
    def get_llm(provider: str) -> BaseChatModel:
        provider = provider.upper()
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
