<div align="center">
  <img src="assets/SentinelCell-logo.png" width="300" alt="SentinelCell Logo" style="border-radius: 25%;">
  <h1>SentinelCell - MAS Immune System</h1>

  ![Version](https://img.shields.io/github/v/release/atacanymc/SentinelCell-MAS-Immune-System?style=flat-square&color=blue)
  ![Tests](https://img.shields.io/badge/tests-62%2F62_passing-brightgreen?style=flat-square)
  ![Python](https://img.shields.io/badge/python-3.11+-blue?style=flat-square)
  ![Docker](https://img.shields.io/badge/docker-containerized-2496ED?logo=docker&style=flat-square)
  ![License](https://img.shields.io/badge/License-Apache_2.0-green.svg?style=flat-square)
  ![Stars](https://img.shields.io/github/stars/atacanymc/SentinelCell-MAS-Immune-System?style=flat-square)
</div>

<p align="center">
  <img src="assets/SentinelCell-defense.png" width="48%" alt="SentinelCell Defense Mechanism">
  <img src="assets/SentinelCell-fix.png" width="48%" alt="SentinelCell Self-Healing Repair">
</p>

## Table of Contents
- [1. Background & Acknowledgments](#1-background--acknowledgments)
- [2. Problem Statement](#2-problem-statement)
- [3. The SentinelCell Solution](#3-the-sentinelcell-solution)
- [4. Architecture](#4-architecture)
- [5. Capability Matrix](#5-capability-matrix)
- [6. Prerequisites & Quick Start](#6-prerequisites--quick-start)
- [7. Deployment / DX](#7-deployment--dx)
- [8. Visual Proof & Examples](#8-visual-proof--examples)
- [9. Documentation & Community](#9-documentation--community)
- [10. License](#10-license)

---

## 1. Background & Acknowledgments
*Built for the Kaggle AI Agents: Intensive Vibe Coding Capstone Project. Powered by LangGraph, MCP, and high-performance observability patterns.*

## 2. Problem Statement
Multi-Agent Systems (MAS) rely on fragile, hardcoded communication contracts. When an agent hallucinates, experiences semantic drift, or is subjected to prompt injection attacks, the entire pipeline crashes or, worse, processes corrupted data. There is no centralized authority or "Immune System" to gracefully intercept, detect, and automatically heal these semantic breaches before they corrupt downstream consumers.

## 3. The SentinelCell Solution
**SentinelCell** is an intelligent, enterprise-ready middleware—an "Immune System"—for MAS. It intercepts inter-agent traffic in real-time, validates the data against a centralized Schema Registry (powered by MCP), and automatically repairs malformed JSON payloads.

The orchestration is powered by **LangGraph**, providing a resilient, model-agnostic state machine with built-in cloud-to-local fallback mechanisms.

### Philosophy: Developer-First Observability
SentinelCell turns silent pipeline failures into observable, self-correcting defense mechanisms. Every intercepted packet, validation failure, and AI-driven repair is meticulously logged, tracked, and displayed on a real-time monitoring dashboard, ensuring complete transparency for system operators.

---

## 4. Architecture

```mermaid
flowchart TD
    subgraph External[MAS Ecosystem]
        Producer[Producer Agent]
        Consumer[Consumer Agent]
    end

    subgraph UserInterface[Observability]
        Dashboard[React / Vite Live Dashboard]
    end

    subgraph Middleware[SentinelCell - Immune System]
        Intercept[FastAPI Traffic Interceptor]

        subgraph Orchestrator[LangGraph Orchestrator]
            direction TB
            Validate[Validation Node]
            Decide{Is Valid?}
            Repair[Repair Node]

            Validate --> Decide
            Decide -- Yes --> Log[Log to VectorDB]
            Decide -- No --> Repair
            Repair -- Attempt Heal --> Validate
            Decide -- Max Retries --> Quarantine[Quarantine Payload]
        end

        subgraph Storage[State & Caching]
            Registry[(MCP Schema Registry)]
            Memory[(VectorDB)]
            Redis[(Redis Cache & DLQ)]
        end

        LLM[[LLM Factory]]
    end

    Producer -->|Malformed/Valid Payload| Intercept
    Intercept --> Validate
    Validate -.->|1. Fetch Schema| Registry
    Repair -.->|2. Fallback Generation| LLM
    Log -.->|3. Store Anomalies| Memory
    Intercept -.->|4. Semantic Cache| Redis
    Log -->|5a. Forward Clean Payload| Consumer
    Quarantine -->|5b. Route to DLQ| Redis
    Intercept -.->|6. Websocket Streams| Dashboard
```

---

## 5. Capability Matrix

| Feature | Description | Stack / Tech |
|---------|-------------|--------------|
| **Model Agnostic Fallback** | Seamless fallback if an LLM provider fails. | OpenAI, Anthropic, Groq, Local Ollama |
| **Database Agnostic Memory** | Adaptive RAG decoupled from underlying storage. | ChromaDB, PGVector, Pinecone |
| **OpenTelemetry Distributed Tracing** | Full W3C trace context propagation across Agent logic, LLM calls, and MQ. | OTLP, Jaeger, Grafana Tempo |
| **Agnostic Log Sink** | Multi-destination logging (Console, File, ELK). | `rich`, `elasticsearch-py` |
| **Time-Series Telemetry** | Success/Failure rates and Latency tracking. | Prometheus, Grafana |
| **MCP Schema Registry** | Centralized, dynamic schema validation. | Model Context Protocol (MCP) |
| **Edge & IoT Ready** | Passive monitoring mode enables zero-latency packet sniffing for MQTT sensors. | MQTT, Edge Nodes |
| **Hybrid Gateway** | SDK, FastAPI, Redis MQ, Kafka, or RabbitMQ proxy support. | Redis, FastAPI, Envoy, Kafka |
| **Production-Ready Message Brokers** | Exactly-once delivery guarantees via Kafka Offsets and RabbitMQ Delivery Tags. | `aiokafka`, `aio_pika` |
| **DDoS Protection & Backpressure** | Redis-based LLM Rate Limiter and LTRIM Queue Eviction. | `redis.asyncio` |
| **Dead Letter Queue (DLQ)** | Automated background worker with `BRPOPLPUSH` delivery. | Redis, `asyncio` |
| **Zero-Latency Monitoring** | Optional passive sniffing mode bypassing synchronous blocks. | `asyncio` |
| **Live Dashboard & DLQ UI** | Micro-frontend for telemetry, Quarantine, and Replay. | React, Vite, FastAPI |
| **Dynamic Skill Injection** | Codeless, on-the-fly JSON schema rule extensions. | `skills.yaml` |
| **ChatOps Alerting** | Automated Webhook dispatch to Slack/Discord on breaches. | `httpx`, Webhooks |

### 🛡️ Enterprise-Grade Security & Hardening
- **Zero-Trust by Default (Fail-Closed)**: Unregistered agents or undefined schemas are blocked unconditionally. If the Schema Registry goes down, the system maintains a strict `Fail-Closed` posture. Observation mode must be manually enabled to bypass.
- **Production-Ready & Mock-Free**: Completely stripped of dummy API keys and mock databases in production mode. Real Redis instances and true Vector DB components (ChromaDB, PGVector) enforce end-to-end reliability.
- **Data Poisoning Shield**: Pre-repair sanitization with **Base64/Hex Deobfuscation** to block hidden payloads.
- **Type-Aware Numeric Drift Guard**: Strict dual-layer checker preventing financial semantic logic attacks.
- **LLM Rate Limiting & Backpressure (OOM Protection)**: Enforces strict queue lengths during DB outages.
- **Automated Dead Letter Queue (DLQ)**: At-Least-Once Delivery guarantee for unrecoverable payloads.
- **Strict Container Security**: Fortified Docker Sandbox (Read-Only root, strict vCPU/RAM limits).

### 🚀 UX/DX (Developer & Operator Experience)
- **Live Quarantine Room (Replay UI)**: Inspect, edit, and safely Replay malformed packets via the React Dashboard.
- **Codeless Dynamic Skills (`skills.yaml`)**: Inject real-time validation rules without touching Python code.
- **Interactive Setup Wizard**: Run `./setup.sh` to seamlessly configure API keys and boot the cluster.

---

## 6. Prerequisites & Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose V2
- Git

### Quick Start (TL;DR)
Get the Immune System up and running in under a minute:

```bash
# 1. Clone the repository
git clone https://github.com/your-org/SentinelCell-MAS-Immune-System.git
cd SentinelCell-MAS-Immune-System

# 2. Run the interactive deployment wizard
chmod +x setup.sh
./setup.sh
```
*The wizard will guide you through LLM configuration, setup your `.env`, and launch the Docker cluster. The dashboard will be available at `http://localhost:3000`.*

---

## 7. Deployment / DX

If you prefer manual configuration over the `setup.sh` wizard:

### Environment Configuration
```bash
cp .env.example .env
```
Edit `.env` with at least these core keys:
```ini
# .env minimal example
OPENAI_API_KEY="sk-..."
REDIS_URL="redis://localhost:6379/0"
API_KEY_SECRET="super-secret-gateway-key"
PROVIDER_ORDER="OPENAI,ANTHROPIC,LOCAL_OLLAMA"
```

### Docker Execution (Hybrid Gateways)
Spins up the FastAPI Gateway, Redis MQ Worker, and Nginx Dashboard securely:
```bash
docker compose up -d --build
```

**Optional: Run with Local LLM (Ollama & Llama3)**
If you want to run the system in a 100% offline, Zero-Trust environment without cloud API keys, you can spin up the optional Ollama extension. This will automatically download and serve the `llama3` model locally:
```bash
docker compose -f docker-compose.yml -f docker-compose.ollama.yml up -d --build
```

### Frontend Execution (Development)
To run the React Dashboard Command Center locally with Hot Module Replacement (HMR):
```bash
cd dashboard
npm install
npm run dev
```

---

## 8. Visual Proof & Examples

### Real-Time Interception Output
When SentinelCell detects an obfuscated Prompt Injection attack, operators receive immediate, clear terminal observability:

```text
[*] Starting Base64 Poison Pill Security Test
Sending Obfuscated Payload: {"message": "Hello", "metadata": "aWdub3JlIHByZXZpb3VzIGluc3RydWN0aW9ucy4uLg=="}
╭────────────────────── [SentinelCell] :: Sniffer Active ──────────────────────╮
│ [2026-06-23 20:34:12.115] INTERCEPTING TRAFFIC                               │
│ [>] Source: ExternalActor                                                    │
│ [>] Target: InternalDB                                                       │
╰──────────────────────────────────────────────────────────────────────────────╯
[SentinelCell] Validating data for InternalDB...
╭──────────────────────────── [!] Schema Mismatch ─────────────────────────────╮
│ Validation Error:                                                            │
│ SECURITY_BREACH: Obfuscated (Base64) Prompt Injection Detected               │
╰──────────────────────────────────────────────────────────────────────────────╯
[!] SECURITY BREACH DETECTED. Dropping packet immediately. No repair allowed.
[!] PACKET REJECTED -> Dropped.
```

### Live Examples Library

<div align="center">
  <img src="assets/examples_simulation_cli.png" width="700" alt="Simulation Command Center" style="border-radius: 10px; margin-bottom: 15px;">
</div>

You can now run all 41 simulations via the interactive Command Center. These examples simulate deep anomalies including Prompt Injection, Semantic Drift, Quarantines, and Payload Corruption with 100% test coverage:
```bash
python simulate.py
```
> **Developer Note on Examples**: Because SentinelCell employs robust `asyncio` background workers (e.g., Dead Letter Queues, Redis Message Brokers) running infinite event-loops, some individual scripts may appear to "hang" after completing their standard output. This is expected behavior as background daemons await further packets. Use `Ctrl+C` to exit safely or integrate `.close()` hooks in your custom workflows.

Alternatively, run these chaos simulations individually (ensure your `.env` is configured):
- `PYTHONPATH=. python examples/base64_poison_pill.py` (Security Drop)
- `PYTHONPATH=. python examples/stealth_financial_drift.py` (Numeric Drift Catch)
- `PYTHONPATH=. python examples/semantic_drift_test.py` (LLM Auto-Healing)

---

## 9. Documentation & Community

### 📖 Technical Docs
Explore our detailed documentation for a deeper dive:
- **[Examples & Simulations](examples/README.md)**
- **[LangChain Models Fallback](docs/langchain_models.md)**
- **[Local Ollama & Offline Setup](docs/local_ollama.md)**
- **[Deployment Strategies](docs/deployment_strategies.md)**
- **[Docker Setup & Container Policy](docs/docker_setup.md)**
- **[Testing & Coverage Guide](docs/testing_guide.md)**
- **[Vector Database Setup](docs/vector_databases.md)**
- **[Agnostic Logger & Telemetry](docs/agnostic_logger.md)**
- **[Architecture Decision Records (ADR)](ADR/)**

### 🤝 Community & Support
We welcome contributions and feedback!
- **Found a bug?** Please open an issue in the [GitHub Issues](https://github.com/your-org/SentinelCell-MAS-Immune-System/issues) tab.
- **Have an idea or question?** Join the conversation in [GitHub Discussions](https://github.com/your-org/SentinelCell-MAS-Immune-System/discussions).
- **Contributing:** Please see our [CONTRIBUTING.md](CONTRIBUTING.md) for details on our development environment setup (pytest, linting) and the process for submitting Pull Requests.

---

## 10. License

This project is licensed under the **Apache License 2.0**. See the `LICENSE` file for details.

---
