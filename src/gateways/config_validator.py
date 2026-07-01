import os
import sys
from src.core.logger import get_console

console = get_console()


def validate_startup_config():
    if "pytest" in sys.modules:
        return

    # 1. Base requirements
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        console.print(
            "[bold yellow][!] Warning: REDIS_URL not set. Running with local fallback state.[/bold yellow]"
        )

    # 2. Schema Registry requirements
    registry_provider = os.getenv("SCHEMA_REGISTRY_PROVIDER", "REDIS").upper()
    if registry_provider == "SUPABASE":
        if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
            raise ValueError(
                "SCHEMA_REGISTRY_PROVIDER is SUPABASE, but SUPABASE_URL or SUPABASE_KEY is missing."
            )
    elif registry_provider == "POSTGRES":
        if not os.getenv("SCHEMA_POSTGRES_URI") and not os.getenv("POSTGRES_URI"):
            raise ValueError(
                "SCHEMA_REGISTRY_PROVIDER is POSTGRES, but SCHEMA_POSTGRES_URI or POSTGRES_URI is missing."
            )

    # 3. Vector DB requirements
    vector_provider = os.getenv("VECTOR_DB_PROVIDER", "CHROMADB").upper()
    if vector_provider == "PINECONE":
        if not os.getenv("PINECONE_API_KEY"):
            raise ValueError(
                "VECTOR_DB_PROVIDER is PINECONE, but PINECONE_API_KEY is missing."
            )
    elif vector_provider == "PGVECTOR":
        if not os.getenv("POSTGRES_URI"):
            raise ValueError(
                "VECTOR_DB_PROVIDER is PGVECTOR, but POSTGRES_URI is missing."
            )

    # 4. LLM Providers API Keys validation
    providers_str = os.getenv("PROVIDER_ORDER", "OPENAI,LOCAL_OLLAMA,ANTHROPIC,GROQ")
    providers = [p.strip().upper() for p in providers_str.split(",") if p.strip()]
    for provider in providers:
        if provider == "OPENAI" and not os.getenv("OPENAI_API_KEY"):
            raise ValueError(
                "LLM provider list contains OPENAI, but OPENAI_API_KEY is missing."
            )
        elif provider == "ANTHROPIC" and not os.getenv("ANTHROPIC_API_KEY"):
            raise ValueError(
                "LLM provider list contains ANTHROPIC, but ANTHROPIC_API_KEY is missing."
            )
        elif provider == "GROQ" and not os.getenv("GROQ_API_KEY"):
            raise ValueError(
                "LLM provider list contains GROQ, but GROQ_API_KEY is missing."
            )
        elif provider == "GEMINI" and not os.getenv("GEMINI_API_KEY"):
            raise ValueError(
                "LLM provider list contains GEMINI, but GEMINI_API_KEY is missing."
            )
        elif provider == "DEEPSEEK" and not os.getenv("DEEPSEEK_API_KEY"):
            raise ValueError(
                "LLM provider list contains DEEPSEEK, but DEEPSEEK_API_KEY is missing."
            )
