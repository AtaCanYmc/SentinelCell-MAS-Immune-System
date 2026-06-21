# ADR-008: Testcontainers for Integration Testing

## Status
**Accepted**

## Context
SentinelCell relies heavily on external infrastructure: Redis (MQ and Registry), PostgreSQL (PGVector and Registry), Supabase, Firebase, ChromaDB, etc. Our unit tests utilize Mock objects to simulate these dependencies. However, Mocks cannot verify real-world network latency, connection pooling, SQL dialect quirks, or protocol-specific behaviors, leading to "false confidence".

## Decision
We integrated the **`testcontainers` (Python)** library for all tests inside `tests/integration/`.

## Rationale
1. **Absolute Reliability**: Tests run against actual, ephemeral Docker containers (e.g., `redis:7-alpine`, `postgres:15-alpine`) rather than mocked Python classes.
2. **Zero Configuration**: Developers do not need to manually install, configure, or clean up local databases before running tests. `testcontainers` manages the lifecycle natively.
3. **CI/CD Readiness**: Integration tests mirror production environments identically within GitHub Actions or other CI pipelines.

## Consequences
- **Positive**: Extremely high confidence in the integration layer and database adapters. Eliminates "works on my machine" issues.
- **Negative**: Test execution time is longer due to container image pulling and startup overhead. Requires the Docker Daemon to be running on the host machine.
