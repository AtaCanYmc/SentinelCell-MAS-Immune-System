<div align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/1/10/Ollama_logo.png" width="150" alt="Ollama Logo" style="border-radius: 10px; margin-bottom: 20px;">
</div>

# Local Ollama Execution Guide (Zero-Trust Offline Mode)

![Ollama](https://img.shields.io/badge/Ollama-black?style=for-the-badge&logo=ollama&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Llama3](https://img.shields.io/badge/Llama_3-0466C8?style=for-the-badge)
![Mistral](https://img.shields.io/badge/Mistral_AI-F47C20?style=for-the-badge)

The **SentinelCell MAS Immune System** supports a 100% offline, air-gapped environment using **Ollama**. This ensures that sensitive multi-agent traffic never leaves your local network during AI-driven semantic repair sequences.

By utilizing the dedicated `docker-compose.ollama.yml` extension, SentinelCell spins up an isolated Ollama server, pulls the target model, and serves LangChain requests without relying on external API keys.

---

## 1. Why Run Local?

- **Absolute Data Privacy (Zero-Trust)**: Enterprise agents communicating sensitive financial or medical data cannot risk sending malformed JSONs to external providers (like OpenAI) for repair.
- **Zero Cost**: No tokens, no rate limits, no unexpected billing.
- **100% Uptime Guarantee**: Completely immune to external provider outages.

---

## 2. Docker Compose Setup

Because Local LLMs consume significant RAM and GPU resources, Ollama has been separated from the base SentinelCell stack.

To run the full stack **with** the local Ollama daemon:

```bash
docker compose -f docker-compose.yml -f docker-compose.ollama.yml up -d --build
```

### What happens under the hood?
1. The `ollama` container starts.
2. The custom `docker/ollama/Dockerfile` temporarily runs an `ollama serve` instance.
3. It automatically executes `ollama pull llama3` (or your chosen model).
4. The model is baked into the image, making subsequent boots extremely fast.

---

## 3. Configuring Models (Examples)

By default, the stack uses `llama3`. However, Ollama supports dozens of high-performance models that excel at JSON schema correction.

To change the active model, update your `.env` file:

```ini
# Prioritize Local Ollama first
PROVIDER_ORDER=LOCAL_OLLAMA,OPENAI,ANTHROPIC

# Define the target Ollama Model
OLLAMA_MODEL=mistral
```

*(Note: If you change the model in `.env`, you must also update the `ollama pull` command in `docker/ollama/Dockerfile` before running `docker compose build`)*

### Recommended Models for Semantic Healing:

| Model | Size | `OLLAMA_MODEL` | Description |
|-------|------|----------------|-------------|
| **Llama 3 (Meta)** | 8B | `llama3` | Fast and highly capable. Excellent at adhering to strict JSON outputs and detecting adversarial payloads. |
| **Mistral** | 7B | `mistral` | Best-in-class 7B model. Known for deep reasoning and code/JSON generation. |
| **Code Llama** | 7B/13B | `codellama` | Specifically trained on code. Exceptional at repairing syntactical JSON brackets and missing commas. |
| **Gemma** | 7B | `gemma:7b` | Google's open weights model. Very lightweight and accurate for edge-node deployments. |

---

## 4. Hardware & GPU Acceleration

Running Local LLMs optimally requires hardware acceleration.

If you are on a **Linux machine with an NVIDIA GPU**, uncomment the `deploy` block inside `docker-compose.ollama.yml` to pass the GPU to the container:

```yaml
    # Optional GPU support:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

On **macOS (Apple Silicon M1/M2/M3)**, Docker may not pass the neural engine effectively. In that case, it is recommended to run Ollama natively on your Mac (`brew install ollama`) and point `.env` to `http://host.docker.internal:11434`.
