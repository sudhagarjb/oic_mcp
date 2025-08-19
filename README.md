# Oracle Integration Cloud (OIC) Monitoring MCP Server

A Python FastAPI-based MCP (Model Context Protocol) server for Oracle Integration Cloud (OIC) monitoring. This server exposes read-only MCP tools to inspect OIC integrations, packages, connections, agents, metrics, and runtime instances. It uses OAuth2 client credentials to authenticate via Oracle Identity (IDCS/IAM) and calls OIC REST APIs via httpx.

References:
- Getting Started with MCP (Concepts & Code) — Part 1: https://blogs.oracle.com/ateam/post/getting-started-with-model-context-protocol-concepts-and-code-part-1
- Getting Started with MCP (Concepts & Code) — Part 2: https://blogs.oracle.com/ateam/post/getting-started-with-model-context-protocol-concepts-and-code-part-2
- Unleashing the power of MCP with Oracle OCI GenAI: https://blogs.oracle.com/ai-and-datascience/post/unleashing-the-power-of-mcp-with-oracle-oci-genai

## Features
- FastAPI WebSocket server implementing core MCP methods: `initialize`, `tools/list`, `tools/call`
- OAuth2 client credentials (IDCS/IAM) via `httpx` for token acquisition and refresh
- 16 read-only OIC monitoring tools (see Tools section)
- Async http client with retry and timeouts
- Ready-to-run with `uvicorn` or Docker

## Quickstart
1. Clone the repo and enter the directory
2. Create and populate `.env` from `.env.example`
3. Create a virtual environment and install dependencies
4. Run the server

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env with your values
uvicorn mcp_server.main:app --host 0.0.0.0 --port 8080 --ws websockets --proxy-headers --forwarded-allow-ips='*'
```

WebSocket endpoint: `ws://localhost:8080/ws`

## Configuration (.env)
```ini
# OIC Endpoint base (no trailing slash), e.g. https://your-instance-namespace.integration.ocp.oraclecloud.com
OIC_BASE_URL=

# OAuth2 Client Credentials (IDCS/IAM)
OAUTH_TOKEN_URL=  # e.g. https://idcs-<tenant>.identity.oraclecloud.com/oauth2/v1/token
OAUTH_CLIENT_ID=
OAUTH_CLIENT_SECRET=
OAUTH_SCOPE=      # optional; leave empty if not required

# Optional HTTP settings
HTTP_TIMEOUT_SECS=30
HTTP_MAX_RETRIES=2
```

## Tools (Read-only)
The following MCP tools are exposed via `tools/list` and invocable via `tools/call`:

1. `list_integrations`
2. `get_integration` (args: `identifier`, `version`)
3. `list_packages`
4. `get_package` (args: `name`)
5. `list_connections`
6. `get_connection` (args: `identifier`)
7. `list_activated_integrations`
8. `list_schedules`
9. `list_instances` (args: optional filters: `integrationId`, `startTime`, `endTime`, `status`, `limit`)
10. `get_instance` (args: `instanceId`)
11. `list_errors` (args: optional `integrationId`, `limit`)
12. `list_lookups`
13. `list_adapters`
14. `list_agents`
15. `list_agent_groups`
16. `list_metrics` (args: `metric`, optional `startTime`, `endTime`)

Note: Endpoints are implemented against OIC REST conventions under `ic/api/integration/v1` and `ic/api/monitoring/v1`. Some tenant versions may differ; you can override path templates in `mcp_server/oic_client.py` if needed.

## MCP Protocol
This server implements a minimal MCP over JSON-RPC 2.0 on WebSocket:
- `initialize`
- `tools/list`: returns tool definitions with JSON Schemas for arguments
- `tools/call`: routes to specific tool handlers

See Oracle A-Team blogs for conceptual background and sample flows:
- https://blogs.oracle.com/ateam/post/getting-started-with-model-context-protocol-concepts-and-code-part-1
- https://blogs.oracle.com/ateam/post/getting-started-with-model-context-protocol-concepts-and-code-part-2

## Docker (optional)
```bash
docker build -t oic-mcp:latest .
docker run -p 8080:8080 --env-file .env oic-mcp:latest
```

## Security
- Store secrets in `.env` or platform secret manager.
- Use a dedicated OAuth client for machine access with least privileges.
- For production, enable TLS termination (behind a reverse proxy) or run on secure hosting.

## License
MIT 