from __future__ import annotations
import json
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from .jsonrpc import JSONRPCRequest, make_error, make_result
from .tools import tool_definitions, TOOL_HANDLERS
from .oic_client import oic_client_singleton as oic


app = FastAPI(title="OIC Monitoring MCP Server", version="0.1.0")


@app.get("/healthz")
async def healthz() -> Any:
    return JSONResponse({"status": "ok"})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                req: JSONRPCRequest = json.loads(raw)
                method = req.get("method")
                id_value = req.get("id")
                params = req.get("params") or {}
                if not isinstance(params, dict):
                    params = {}

                if method == "initialize":
                    result = {
                        "capabilities": {
                            "tools": True,
                            "notifications": False,
                            "resources": False,
                            "prompts": False,
                        },
                        "serverInfo": {
                            "name": "oic-monitoring-mcp",
                            "version": "0.1.0",
                        },
                    }
                    await websocket.send_text(json.dumps(make_result(id_value, result)))

                elif method == "tools/list":
                    tools = tool_definitions()
                    await websocket.send_text(json.dumps(make_result(id_value, {"tools": tools})))

                elif method == "tools/call":
                    name = params.get("name")
                    arguments = params.get("arguments") or {}
                    if not name or name not in TOOL_HANDLERS:
                        await websocket.send_text(json.dumps(make_error(id_value, -32601, f"Unknown tool: {name}")))
                        continue
                    try:
                        result = await TOOL_HANDLERS[name](arguments)
                        # Return result directly without content wrapper for better MCP compatibility
                        await websocket.send_text(json.dumps(make_result(id_value, result)))
                    except Exception as e:  # noqa: BLE001
                        await websocket.send_text(json.dumps(make_error(id_value, -32000, "Tool execution error", {"name": name, "error": str(e)})))

                else:
                    await websocket.send_text(json.dumps(make_error(id_value, -32601, f"Unknown method: {method}")))

            except json.JSONDecodeError:
                await websocket.send_text(json.dumps(make_error(None, -32700, "Parse error")))
    except WebSocketDisconnect:
        return
    finally:
        await oic.aclose() 