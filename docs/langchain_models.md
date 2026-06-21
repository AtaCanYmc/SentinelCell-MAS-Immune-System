# Supported LangChain Models

![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)
![Anthropic](https://img.shields.io/badge/Anthropic-CA8F74?style=for-the-badge&logo=anthropic&logoColor=black)
![DeepSeek](https://img.shields.io/badge/DeepSeek-1C1C1C?style=for-the-badge&logo=deepseek&logoColor=4D93E6)
![Gemini](https://img.shields.io/badge/Google%20Gemini-8E75B2?style=for-the-badge&logo=googlegemini&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-black?style=for-the-badge&logo=ollama&logoColor=white)

The **SentinelCell MAS Immune System** is designed to be completely **Model Agnostic**. It utilizes the LangChain ecosystem to seamlessly switch between various Large Language Models (LLMs) depending on availability, rate limits, or user preference.

The fallback and priority mechanism is dynamically managed via the `PROVIDER_ORDER` environment variable.

## 1. OpenAI (`OPENAI`)
- **Integration**: `langchain-openai` (`ChatOpenAI`)
- **Default Model**: `gpt-4o-mini`
- **Environment Variables**: `OPENAI_API_KEY`, `OPENAI_MODEL`
- **Use Case**: Excellent for high-accuracy semantic validation and reasoning. It is usually placed at the top of the fallback list for its reliability.

## 2. Anthropic (`ANTHROPIC`)
- **Integration**: `langchain-anthropic` (`ChatAnthropic`)
- **Default Model**: `claude-3-haiku-20240307`
- **Environment Variables**: `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`
- **Use Case**: Highly capable alternative for robust JSON schema healing and rapid context understanding.

## 3. Groq (`GROQ`)
- **Integration**: `langchain-groq` (`ChatGroq`)
- **Default Model**: `llama3-70b-8192`
- **Environment Variables**: `GROQ_API_KEY`, `GROQ_MODEL`
- **Use Case**: Provides lightning-fast inference using LPUs. Ideal for environments where near-instant network interception and packet healing are critical.

## 4. DeepSeek (`DEEPSEEK`)
- **Integration**: `langchain-openai` (`ChatOpenAI` wrapper via `api.deepseek.com`)
- **Default Model**: `deepseek-chat`
- **Environment Variables**: `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL`
- **Use Case**: Highly cost-effective and coding-optimized LLM, often providing comparable performance to OpenAI/Anthropic at a fraction of the cost. Excellent for parsing complex JSON schemas.

## 5. Google Gemini (`GEMINI`)
- **Integration**: `langchain-google-genai` (`ChatGoogleGenerativeAI`)
- **Default Model**: `gemini-1.5-flash`
- **Environment Variables**: `GEMINI_API_KEY`, `GEMINI_MODEL`
- **Use Case**: Very fast and highly capable model for multimodal processing and JSON healing. A strong competitor to OpenAI and Anthropic.

## 5. Local Ollama (`LOCAL_OLLAMA`)
- **Integration**: `langchain-ollama` (`ChatOllama`)
- **Default Model**: `llama3`
- **Environment Variables**: `OLLAMA_MODEL` (No API key required for local execution)
- **Use Case**: The ultimate fallback. Allows SentinelCell to run offline and on-premise, guaranteeing data privacy and 100% uptime when external API providers go down.

## Model Fallback Configuration
The fallback order is defined in your `.env` file via `PROVIDER_ORDER`. For example:
```env
PROVIDER_ORDER=OPENAI,GROQ,LOCAL_OLLAMA,ANTHROPIC
```
If `OPENAI` fails due to rate-limiting or an invalid API key, the `SelfHealingEngine` will automatically attempt to heal the payload using `GROQ`, and so on.
