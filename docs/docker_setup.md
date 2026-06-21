# SentinelCell Docker Setup

![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Docker Compose](https://img.shields.io/badge/Docker_Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Security Strict](https://img.shields.io/badge/Security-Strict_Sandbox-red?style=for-the-badge)

This document provides a guide on how to build, run, and manage the SentinelCell MAS Immune System within its secure, containerized environment.

## Prerequisites
- **Docker**: Ensure Docker Engine is installed.
- **Docker Compose**: Ensure Docker Compose is available.
- **Environment Variables**: You must have a properly configured `.env` file in the root directory before running the container. (Reference `.env.example` to set your API keys).

## Building and Running the Container
To build the image and run the container in the background, use the following command:
```bash
docker compose up -d --build
```

## Security and Resource Limitations
The container architecture enforces strict limits according to our `container_policy.md`:
1. **Resource Limits**: The `sentinelcell` service is hard-capped at **0.5 vCPU** and **512 MB of RAM**.
2. **Read-Only System**: The container's root file system is completely `read-only`.
3. **Privilege Drop**: The container drops all root capabilities (`cap_drop: [ALL]`), ensuring total separation from the host system.
4. **Allowed IO Directories**: The application is only permitted to write to the `/logs` directory (persistent to host) and `/temp` directory (ephemeral tmpfs).

## Monitoring and Logs
You can view the active resource usage to verify the sandbox limits:
```bash
docker stats sentinelcell_agent
```

To view the live application logs (Hackerman style):
```bash
docker compose logs -f
```

To stop the agent:
```bash
docker compose down
```
