import os

# Pre-populate required environment variables for tests
# to prevent LLMFactory and other modules from raising ValueError during import.
os.environ["OPENAI_API_KEY"] = "test-openai-key"
os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"
os.environ["GROQ_API_KEY"] = "test-groq-key"
os.environ["GEMINI_API_KEY"] = "test-gemini-key"
os.environ["DEEPSEEK_API_KEY"] = "test-deepseek-key"
os.environ["PINECONE_API_KEY"] = "test-pinecone-key"
