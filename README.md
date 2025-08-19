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

### How it works (high level)
- The server exposes a WebSocket endpoint that speaks JSON-RPC 2.0 (MCP). Clients call `tools/list` to discover tools and `tools/call` to execute them.
- On each tool call, the server fetches data from OIC REST APIs using an authenticated `httpx.AsyncClient`. The OAuth token is obtained via Client Credentials, cached, and refreshed on expiry.
- All outputs are JSON, with additional summaries to help LLMs consume complex payloads.
- For very large resources or offline testing, many tools accept a `designJsonPath` to read a previously downloaded integration JSON file from disk instead of calling OIC.

### Authentication flow
- Uses OAuth2 Client Credentials:
  - Token request: `OAUTH_TOKEN_URL` with `client_id`, `client_secret`, and optional `scope`.
  - Access token stored in memory and reused until expiry, then refreshed automatically.
  - No credentials are logged; errors include only minimal context.

### HTTP client behavior
- `httpx.AsyncClient` with:
  - `follow_redirects=True` to handle OIC 307 redirects between instance and design hosts.
  - Configurable timeouts (`HTTP_TIMEOUT_SECS`).
  - Lightweight retry policy (idempotent GETs are retried a small number of times; respects `HTTP_MAX_RETRIES`).
- All OIC calls attach `integrationInstance=<OIC_INSTANCE_NAME>` automatically when provided.

### Instance scoping (`OIC_INSTANCE_NAME`)
- When set, any request to OIC adds `?integrationInstance=<value>` to scope to a specific Integration instance.
- This avoids cross-instance ambiguity and matches behavior of the OIC console URLs.

### Search and paging
- `list_integrations_search` performs client-side paging over the catalog, filtering by user terms across fields (`code`, `name`, `description`, `keywords`).
- This keeps WebSocket payloads small and lets you control breadth via `perPage` and `maxPages`.

### Design-time analysis tooling
- `get_integration_auto` retrieves complete design JSON (resolving latest version when omitted).
- `summarize_integration` extracts trigger/targets/tracking variables.
- `summarize_flow_controls` and `deep_flow_outline` scan the design tree to surface control flow and provide quick textual plans.
- `summarize_mappings` lists mapping steps to guide deeper inspection.

### Step and endpoint matching
- `get_integration_step` searches the design tree for nodes whose `name` matches a provided `stepName` (exact and fuzzy). It also returns endpoints with a matching name.
- `summarize_step_io` extracts suspected SQL/query snippets and parameters from a step node. If no node is found, it falls back to a matching endpoint and returns its connection context (so you never get empty/unhelpful output).
- Both tools accept `designJsonPath` for offline analysis.

### Export integration archives
- `export_integration` downloads the integration zip archive and returns:
  - `base64`: the full archive, base64-encoded (for LLM-safe transport).
  - `listOnly=true`: return only the entry list plus small previews (text) up to `maxPreviewBytes`.
- This enables deeper static analysis or archival in downstream systems.

### JSON-first outputs
- All tools return JSON objects; text bodies are wrapped as fields.
- Summaries present structured, small-footprint overviews ideal for LLMs.

## Quickstart
1. Clone the repo and enter the directory
2. Create and populate `.env` from `.env.example`
3. Create a virtual environment and install dependencies
4. Run the server (defaults to ws://127.0.0.1:8085/ws)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# cp .env.example .env  # example file in repo; fill values
./scripts/run-local.sh
```

WebSocket endpoint: `ws://127.0.0.1:8085/ws`

Example client calls:
```bash
# Initialize
python3 scripts/ws-call.py initialize

# Tools list (shows all available tools)
python3 scripts/ws-call.py tools/list

# List first 3 integrations
python3 scripts/ws-call.py tools/call '{"name":"list_integrations","arguments":{"limit":3}}' | python3 -c "import json,sys; j=json.load(sys.stdin); print(json.dumps(j['result']['data']['items'][:3], indent=2))"

# Search integrations for "order" and "customer"
python3 scripts/ws-call.py tools/call '{"name":"list_integrations_search","arguments":{"terms":["order","customer"],"perPage":100,"maxPages":30}}'

# Get integration details (auto-resolves latest version)
python3 scripts/ws-call.py tools/call '{"name":"get_integration_auto","arguments":{"identifier":"CL_CUS_ORD_PAY_CLD_TO_ORA_APP_IN"}}'

# Summarize an integration and key steps (auto resolves latest)
python3 scripts/ws-call.py tools/call '{"name":"summarize_integration_with_steps","arguments":{"identifier":"CL_CUS_ORD_PAY_CLD_TO_ORA_APP_IN","stepNames":["insertJsonData","InsertOrderHeader"]}}'

# Use a local design JSON for step I/O summary (offline)
python3 scripts/ws-call.py tools/call '{"name":"summarize_step_io","arguments":{"identifier":"CL_CUS_ORD_PAY_CLD_TO_ORA_APP_IN","designJsonPath":"out/CL_CUS_ORD_PAY_CLD_TO_ORA_APP_IN.json","stepName":"insertJsonData"}}'

# Export an integration archive and list entries only
python3 scripts/ws-call.py tools/call '{"name":"export_integration","arguments":{"identifier":"CL_CUS_ORD_PAY_CLD_TO_ORA_APP_IN","listOnly":true}}'

# Get flow controls summary
python3 scripts/ws-call.py tools/call '{"name":"summarize_flow_controls","arguments":{"identifier":"CL_CUS_ORD_PAY_CLD_TO_ORA_APP_IN"}}'

# List connections
python3 scripts/ws-call.py tools/call '{"name":"list_connections","arguments":{"limit":5}}' | python3 -c "import json,sys; j=json.load(sys.stdin); print(json.dumps(j['result']['data']['items'][:3], indent=2))"
```

**Note**: All responses are in JSON format with internal response formatting handled by the MCP server.

**Response Formats:**

1. **List-type responses** (integrations, connections, packages, etc.):
   ```json
   {
     "jsonrpc": "2.0",
     "id": 1,
     "result": {
       "data": {
         "items": [...],
         "totalResults": N,
         "hasMore": bool
       },
       "message": "Successfully executed tool_name",
       "success": true,
       "count": N
     }
   }
   ```

2. **Single object responses** (get_integration, get_connection, etc.):
   ```json
   {
     "jsonrpc": "2.0",
     "id": 1,
     "result": {
       "name": "...",
       "code": "...",
       "status": "...",
       ...
     }
   }
   ```

**Example JSON parsing:**
```bash
# Get first 2 integrations (list-type response)
python3 scripts/ws-call.py tools/call '{"name":"list_integrations","arguments":{"limit":2}}' | python3 -c "import json,sys; j=json.load(sys.stdin); print(json.dumps(j['result']['data']['items'][:2], indent=2))"

# Get total count
python3 scripts/ws-call.py tools/call '{"name":"list_integrations","arguments":{"limit":2}}' | python3 -c "import json,sys; j=json.load(sys.stdin); print('Total integrations:', j['result']['data']['totalResults'])"

# Get items count
python3 scripts/ws-call.py tools/call '{"name":"list_integrations","arguments":{"limit":2}}' | python3 -c "import json,sys; j=json.load(sys.stdin); print('Items returned:', j['result']['count'])"

# Get integration name (list-type response)
python3 scripts/ws-call.py tools/call '{"name":"list_integrations","arguments":{"limit":1}}' | python3 -c "import json,sys; j=json.load(sys.stdin); print('Integration name:', j['result']['data']['items'][0]['name'])"

# Get integration details (single object response)
python3 scripts/ws-call.py tools/call '{"name":"get_integration_auto","arguments":{"identifier":"CL_CUS_ORD_PAY_CLD_TO_ORA_APP_IN"}}' | python3 -c "import json,sys; j=json.load(sys.stdin); print('Integration name:', j['result']['name'])"
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

Example `.env` (inline):
```ini
OIC_BASE_URL=https://caratlane-oic-test-bmdzqmmqkmi3-bo.integration.ap-mumbai-1.ocp.oraclecloud.com
OIC_INSTANCE_NAME=caratlane-oic-test-bmdzqmmqkmi3-bo
OAUTH_TOKEN_URL=https://<idcs-tenant>.identity.oraclecloud.com/oauth2/v1/token
OAUTH_CLIENT_ID=xxxxxxxxxxxxxxxx
OAUTH_CLIENT_SECRET=yyyyyyyyyyyyyyyy
OAUTH_SCOPE="urn:opc:idm:__myscopes__"  # optional; quote if multi-line
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

### Passing envs from `mcp.json`
- For command-type servers, populate the `env` object as shown. This fully avoids `.env` files and is ideal for editor-integrated MCP clients.
- For websocket-type servers, start the server with `.env` or process envs, then point the client to the URL.

## Production hardening
- Run behind TLS (reverse proxy like Nginx/Traefik) and restrict network access.
- Store secrets in a vault. Avoid committing `.env`.
- Set minimal OAuth client privileges for read-only.
- Consider Docker for immutable deployments and CI/CD.
- Monitor process/WebSocket payload sizes; use client-side paging for large lists.
- Enable access logs and metrics on your reverse proxy.

## Operations & troubleshooting
- Health check: GET `/healthz` returns `{ "status": "ok" }`.
- Startup issues: verify `.env` values and token URL reachability.
- 401/403: validate client credentials and scope; some tenants require scope.
- 404 on certain flow paths: prefer design-time `get_integration_auto` and analysis tools.
- Large responses: narrow with search terms and paging; avoid returning entire catalogs to LLMs.

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