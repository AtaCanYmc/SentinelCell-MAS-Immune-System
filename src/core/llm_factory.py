import os
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from langchain_core.language_models.chat_models import BaseChatModel


class LLMFactory:
    """
    Model Agnostic LLM Factory.
    Creates ChatModel instances based on provider configurations.
    """

    @staticmethod
    def get_llm(provider: str) -> BaseChatModel:
        provider = provider.upper()
        if provider == "OPENAI":
            return ChatOpenAI(
                api_key=os.getenv("OPENAI_API_KEY", "dummy_openai_key"),
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                temperature=0,
            )
        elif provider == "ANTHROPIC":
            return ChatAnthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY", "dummy_anthropic_key"),
                model_name=os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307"),
                temperature=0,
            )
        elif provider == "LOCAL_OLLAMA":
            return ChatOllama(model=os.getenv("OLLAMA_MODEL", "llama3"), temperature=0)
        elif provider == "GROQ":
            return ChatGroq(
                api_key=os.getenv("GROQ_API_KEY", "dummy_groq_key"),
                model_name=os.getenv("GROQ_MODEL", "llama3-70b-8192"),
                temperature=0,
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
