# Oracle Integration Cloud (OIC) Monitoring MCP Server

A Python FastAPI-based MCP (Model Context Protocol) server for Oracle Integration Cloud (OIC) monitoring. This server exposes read-only MCP tools to inspect OIC integrations, packages, connections, agents, metrics, design-time details, and exports. It uses OAuth2 client credentials to authenticate (IDCS/IAM) and calls OIC REST APIs using httpx. Responses are JSON-first for easy LLM consumption.

References:
- Getting Started with MCP (Concepts & Code) — Part 1: https://blogs.oracle.com/ateam/post/getting-started-with-model-context-protocol-concepts-and-code-part-1
- Getting Started with MCP (Concepts & Code) — Part 2: https://blogs.oracle.com/ateam/post/getting-started-with-model-context-protocol-concepts-and-code-part-2
- Unleashing the power of MCP with Oracle OCI GenAI: https://blogs.oracle.com/ai-and-datascience/post/unleashing-the-power-of-mcp-with-oracle-oci-genai

## Features
- FastAPI WebSocket server implementing MCP methods: `initialize`, `tools/list`, `tools/call`
- OAuth2 Client Credentials with token refresh
- Robust http client: redirects enabled, timeouts, connection pooling
- JSON-first tooling; raw text is wrapped in JSON
- Local design JSON override (`designJsonPath`) for offline testing of step/mapping/outline tools
- 20+ read-only tools (see Tools)

## Quickstart
1. Clone the repo and enter the directory
2. Create and populate `.env` from `.env.example`
3. Create a virtual environment and install dependencies
4. Run the server (defaults to ws://127.0.0.1:8085/ws)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# cp .env.example .env  # example file in repo; fill values
./scripts/run-local.sh
```

WebSocket endpoint: `ws://127.0.0.1:8085/ws`

Example client calls:
```bash
# Initialize
python scripts/ws-call.py initialize

# Tools list
python scripts/ws-call.py tools/list

# Search integrations for "order" and "customer"
python scripts/ws-call.py tools/call '{"name":"list_integrations_search","arguments":{"terms":["order","customer"],"perPage":100,"maxPages":30}}'

# Summarize an integration and key steps (auto resolves latest)
python scripts/ws-call.py tools/call '{"name":"summarize_integration_with_steps","arguments":{"identifier":"CL_CUS_ORD_PAY_CLD_TO_ORA_APP_IN","stepNames":["insertJsonData","InsertOrderHeader"]}}'

# Use a local design JSON for step I/O summary (offline)
python scripts/ws-call.py tools/call '{"name":"summarize_step_io","arguments":{"identifier":"CL_CUS_ORD_PAY_CLD_TO_ORA_APP_IN","designJsonPath":"out/CL_CUS_ORD_PAY_CLD_TO_ORA_APP_IN.json","stepName":"insertJsonData"}}'

# Export an integration archive and list entries only
python scripts/ws-call.py tools/call '{"name":"export_integration","arguments":{"identifier":"CL_CUS_ORD_PAY_CLD_TO_ORA_APP_IN","listOnly":true}}'
```

## Configuration (.env)
```ini
# OIC Endpoint base (no trailing slash), e.g. instance host
OIC_BASE_URL=https://<your-instance>.integration.<region>.ocp.oraclecloud.com

# Optional instance name to attach as integrationInstance query param
OIC_INSTANCE_NAME=

# OAuth2 Client Credentials (IDCS/IAM)
# Example: https://<idcs>.identity.oraclecloud.com/oauth2/v1/token
OAUTH_TOKEN_URL=
OAUTH_CLIENT_ID=
OAUTH_CLIENT_SECRET=
# Optional; leave empty if not required. If multi-line, put in quotes as a single line.
OAUTH_SCOPE=

# Optional HTTP settings
HTTP_TIMEOUT_SECS=30
HTTP_MAX_RETRIES=2
```

## Tools (Read-only)
All tools are discoverable via `tools/list` and invocable via `tools/call`.

- `list_integrations`: List integrations. Optional: `onlyActivated`, `limit`, `page`.
- `get_integration`: Get integration by `identifier` and `version`.
- `list_packages`: List packages.
- `get_package`: Get a package by `name`.
- `list_connections`: List connections.
- `get_connection`: Get connection by `identifier`.
- `list_activated_integrations`: List only activated integrations.
- `list_schedules`: List schedules.
- `list_instances`: List runtime instances with filters (`integrationId`, `status`, `startTime`, `endTime`, `limit`).
- `get_instance`: Get a runtime instance by `instanceId`.
- `list_errors`: List recent errors, optional `integrationId`, `limit`.
- `list_lookups`: List lookups.
- `list_adapters`: List available adapters.
- `list_agents`: List connectivity agents.
- `list_agent_groups`: List connectivity agent groups.
- `list_metrics`: List metrics by `metric`, optional `startTime`, `endTime`.
- `list_integrations_search`: Client-side paged search across `code`, `name`, `description`, `keywords`. Args: `terms`, optional `onlyActivated`, `perPage`, `maxPages`, `fields`, `caseSensitive`.
- `get_integration_auto`: Get design-time details by `code` or `code|version` (auto-resolves latest).
- `fetch_raw_path`: Fetch any relative OIC path (JSON or text wrapped in JSON).
- `summarize_integration`: High-level summary including trigger/targets/tracking variables.
- `summarize_flow_controls`: Count and sample flow-control constructs (Switch/ForEach/Route/Fault/Scope).
- `summarize_mappings`: Extract mapping steps.
- `get_connection_detail`: Retrieve a single connection by `identifier`.
- `get_lookup`: Retrieve a lookup by `name`.
- `get_library`: Retrieve a library by `name`.
- `get_adapter`: Retrieve an adapter by `name`.
- `search_json`: Utility to search any JSON-like structure by substring.
- `list_endpoints`: List integration endpoints with role and connection.
- `get_integration_step`: Return raw JSON subtree(s) for a `stepName`. Also returns matching endpoints. Supports `designJsonPath`.
- `summarize_step_io`: For a `stepName`, extract suspected SQL/query snippets and parameters; falls back to endpoint match. Supports `designJsonPath`.
- `export_integration`: Export archive (zip) as base64; can return `listOnly` of entries and previews.
- `deep_flow_outline`: Produce a compact textual outline of the flow.
- `summarize_integration_with_steps`: Combine summarize_integration + selected step I/O summaries.

Notes:
- Many tools accept optional `version`. If omitted, latest is resolved automatically by the client.
- For offline/local testing, pass `designJsonPath` pointing to a previously-fetched design JSON file.

## MCP client config (examples)
You can connect via WebSocket URL or have a client spawn the server.

- Example `mcp.json` (WebSocket):
```json
{
  "servers": {
    "oic-mcp": {
      "type": "websocket",
      "url": "ws://127.0.0.1:8085/ws"
    }
  }
}
```

- Example `mcp.json` (Command-spawned):
```json
{
  "servers": {
    "oic-mcp": {
      "type": "command",
      "command": ".venv/bin/uvicorn",
      "args": ["mcp_server.main:app", "--host", "127.0.0.1", "--port", "8085", "--ws", "websockets"],
      "env": {
        "OIC_BASE_URL": "https://<instance>.integration.<region>.ocp.oraclecloud.com",
        "OIC_INSTANCE_NAME": "<optional>",
        "OAUTH_TOKEN_URL": "https://<idcs>.identity.oraclecloud.com/oauth2/v1/token",
        "OAUTH_CLIENT_ID": "<client_id>",
        "OAUTH_CLIENT_SECRET": "<client_secret>",
        "OAUTH_SCOPE": "<optional>",
        "HTTP_TIMEOUT_SECS": "30",
        "HTTP_MAX_RETRIES": "2"
      }
    }
  }
}
```

## Production hardening
- Run behind TLS (reverse proxy like Nginx/Traefik) and restrict network access.
- Store secrets in a vault. Avoid committing `.env`.
- Set minimal OAuth client privileges for read-only.
- Consider Docker for immutable deployments.
- Monitor process and WebSocket payload sizes; use client-side paging for large lists.

## Docker (optional)
```bash
docker build -t oic-mcp:latest .
docker run -p 8085:8085 --env-file .env oic-mcp:latest
```

## Troubleshooting
- 403/401 from token URL: verify OAuth credentials and scope.
- 404 on flow paths: use design-time tools (`get_integration_auto`) and analysis tools (`summarize_*`).
- Payload too big over WebSocket: use `list_integrations_search` with paging and filters.

## License
MIT 