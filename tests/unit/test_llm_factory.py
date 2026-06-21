import pytest
from src.core.llm_factory import LLMFactory
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq


def test_get_llm_openai():
    llm = LLMFactory.get_llm("OPENAI")
    assert isinstance(llm, ChatOpenAI)


def test_get_llm_anthropic(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    llm = LLMFactory.get_llm("ANTHROPIC")
    assert type(llm).__name__ == "ChatAnthropic"


def test_get_llm_gemini(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test")
    llm = LLMFactory.get_llm("GEMINI")
    assert type(llm).__name__ == "ChatGoogleGenerativeAI"


def test_get_llm_deepseek(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test")
    llm = LLMFactory.get_llm("DEEPSEEK")
    assert type(llm).__name__ == "ChatOpenAI"
    assert llm.model_name == "deepseek-chat"


def test_get_llm_groq():
    llm = LLMFactory.get_llm("GROQ")
    assert isinstance(llm, ChatGroq)


def test_get_llm_local_ollama():
    llm = LLMFactory.get_llm("LOCAL_OLLAMA")
    assert isinstance(llm, ChatOllama)


def test_get_llm_unsupported():
    with pytest.raises(ValueError, match="Unsupported LLM provider: INVALID"):
        LLMFactory.get_llm("INVALID")
