# SentinelCell Client Integration Guide

This guide explains how external agent platforms and services integrate with the SentinelCell API Gateway. Whether you are building agents in Python, JavaScript/Node.js, or using CLI scripts, this document outlines request formats, security authentication, and response handling.

---

## 🔒 1. Authentication

All requests to the SentinelCell API Gateway must include the gateway secret key in the request headers. If the key is missing or invalid, the gateway returns a `401 Unauthorized` or `403 Forbidden` status.

- **Header Name:** `X-Sentinel-Key`
- **Value:** Configured via `API_KEY_SECRET` in the `.env` file of the gateway.

---

## 📥 2. API Request Structure

To intercept traffic, the client agent sends a `POST` request to the `/intercept` gateway endpoint.

### Endpoint
`POST /intercept`

### Request Body (JSON)
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `source` | `string` | Yes | The ID/name of the originating sender agent (e.g. `Agent_Alpha`). |
| `target` | `string` | Yes | The ID/name of the target recipient agent (e.g. `Agent_Beta`). |
| `payload` | `string` | Yes | The raw JSON-encoded string payload containing the data message. |

#### Request Example
```json
{
  "source": "ProducerAgent",
  "target": "DatabaseAgent",
  "payload": "{\"message\": \"Write transaction\", \"amount\": 150.0}"
}
```

---

## 📤 3. API Response Structure

SentinelCell returns different responses based on the safety status of the payload.

### Scenario A: Payload is Valid (200 OK)
If the payload is clean and matches the schema, it is returned directly:
```json
{
  "status": "success",
  "payload": "{\"message\": \"Write transaction\", \"amount\": 150.0}",
  "repaired": false
}
```

### Scenario B: Payload was Malformed but Healed (200 OK)
If the payload was malformed (e.g. invalid JSON, missing required fields) but was successfully repaired:
```json
{
  "status": "success",
  "payload": "{\"message\": \"Write transaction\", \"amount\": 150.0}",
  "repaired": true,
  "original_payload": "{message: Write transaction, amount: 150}"
}
```

### Scenario C: Payload Violates Security Policies (403 Forbidden)
If the payload contains adversarial injection attacks (e.g. prompt injection, data poisoning):
```json
{
  "status": "security_rejected",
  "reason": "SECURITY_BREACH: Base64 Prompt Injection Detected",
  "original_payload": "aWdub3JlIHByZXZpb3VzIGluc3RydWN0aW9ucy4uLg=="
}
```

### Scenario D: Payload is Unrepairable / High Semantic Drift (422 Unprocessable)
If the payload fails schema validation and cannot be repaired due to high Jaccard drift (value mismatch):
```json
{
  "status": "quarantined",
  "reason": "SEMANTIC_DRIFT: Repaired payload has <30% value retention rate."
}
```

---

## 💻 4. Client Code Examples

### Python Integration
```python
import httpx
import json
import asyncio

GATEWAY_URL = "http://localhost:8000/intercept"
API_SECRET = "super-secret-gateway-key" # Matches API_KEY_SECRET

async def send_agent_message(source: str, target: str, message_dict: dict):
    headers = {
        "X-Sentinel-Key": API_SECRET,
        "Content-Type": "application/json"
    }

    data = {
        "source": source,
        "target": target,
        "payload": json.dumps(message_dict)
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(GATEWAY_URL, json=data, headers=headers)
            if response.status_code == 200:
                result = response.json()
                clean_payload = json.loads(result["payload"])
                print(f"Safe message received: {clean_payload} (Repaired: {result['repaired']})")
                return clean_payload
            elif response.status_code == 403:
                print(f"Security drop triggered: {response.json()['reason']}")
            else:
                print(f"Error intercepting: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Gateway connection error: {e}")

# Example call
# asyncio.run(send_agent_message("AgentA", "AgentB", {"msg": "hello"}))
```

### JavaScript / Node.js Integration
```javascript
const axios = require('axios');

const GATEWAY_URL = "http://localhost:8000/intercept";
const API_SECRET = "super-secret-gateway-key";

async function sendAgentMessage(source, target, messageObject) {
  const headers = {
    'X-Sentinel-Key': API_SECRET,
    'Content-Type': 'application/json'
  };

  const body = {
    source: source,
    target: target,
    payload: JSON.stringify(messageObject)
  };

  try {
    const response = await axios.post(GATEWAY_URL, body, { headers });
    const cleanPayload = JSON.parse(response.data.payload);
    console.log("Safe payload received:", cleanPayload, "Repaired:", response.data.repaired);
    return cleanPayload;
  } catch (error) {
    if (error.response && error.response.status === 403) {
      console.error("Security Blocked Payload:", error.response.data.reason);
    } else {
      console.error("Gateway error:", error.message);
    }
  }
}
```
