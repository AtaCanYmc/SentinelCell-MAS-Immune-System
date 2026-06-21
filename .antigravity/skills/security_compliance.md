# Skill: Security Compliance & Sanitization

## Purpose
Ensure no sensitive data leaks occur and the system remains robust against injection or hallucinated payloads.

## Protocol
- **No Hardcoding:** All environment variables (API keys, endpoint secrets) must be loaded via `python-dotenv` and never committed.
- **Validation:** Every input is treated as "untrusted" until validated against the SchemaRegistry.
- **Sanitization:** Remove PII (Personally Identifiable Information) before logging to `logs/` for privacy compliance.
- **Audit:** All "Healed" packet records must be stored locally in an encrypted or restricted-access log file.
