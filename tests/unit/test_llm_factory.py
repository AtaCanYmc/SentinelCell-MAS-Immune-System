import pytest
from src.core.llm_factory import LLMFactory
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq


def test_get_llm_openai():
    llm = LLMFactory.get_llm("OPENAI")
    assert isinstance(llm, ChatOpenAI)


def test_get_llm_anthropic():
    llm = LLMFactory.get_llm("ANTHROPIC")
    assert isinstance(llm, ChatAnthropic)


def test_get_llm_groq():
    llm = LLMFactory.get_llm("GROQ")
    assert isinstance(llm, ChatGroq)


def test_get_llm_local_ollama():
    llm = LLMFactory.get_llm("LOCAL_OLLAMA")
    assert isinstance(llm, ChatOllama)


def test_get_llm_unsupported():
    with pytest.raises(ValueError, match="Unsupported LLM provider: INVALID"):
        LLMFactory.get_llm("INVALID")
