from __future__ import annotations
import json
from typing import Any, Dict, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from .jsonrpc import JSONRPCRequest, make_error, make_result
from .tools import tool_definitions, TOOL_HANDLERS
from .oic_client import oic_client_singleton as oic


def format_mcp_response(result: Any) -> Dict[str, Any]:
    """
    Format OIC API responses into clean MCP-compatible structure.
    Handles the OIC API's content wrapper and standardizes the response format.
    """
    if not isinstance(result, dict):
        return result
    
    # Handle OIC API responses that have a 'content' wrapper
    if 'content' in result and isinstance(result['content'], dict):
        content = result['content']
        # Extract items, totalResults, hasMore from content
        formatted = {}
        if 'items' in content:
            formatted['items'] = content['items']
        if 'totalResults' in content:
            formatted['totalResults'] = content['totalResults']
        if 'hasMore' in content:
            formatted['hasMore'] = content['hasMore']
        if 'links' in content:
            formatted['links'] = content['links']
        return formatted
    
    # Handle direct responses (no content wrapper) - already clean format
    if 'items' in result or 'totalResults' in result:
        return result
    
    # For single object responses (like get_integration, get_connection, etc.)
    # Return as-is since they're already in the right format
    return result


def should_use_standard_response(result: Any) -> bool:
    """
    Determine if we should wrap the result in a standard response format.
    """
    if not isinstance(result, dict):
        return False
    
    # For list-type responses (integrations, connections, etc.), use standard format
    if 'items' in result or 'totalResults' in result:
        return True
    
    # For single object responses, return as-is for simplicity
    return False


def create_standard_response(data: Any, message: str = "Success", count: int = None) -> Dict[str, Any]:
    """
    Create a standardized MCP response format for consistent client consumption.
    """
    response = {
        "data": data,
        "message": message,
        "success": True
    }
    
    if count is not None:
        response["count"] = count
    elif isinstance(data, list):
        response["count"] = len(data)
    elif isinstance(data, dict) and "items" in data:
        response["count"] = len(data["items"])
    
    return response


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
                        # Format the response to handle OIC API structure internally
                        formatted_result = format_mcp_response(result)
                        
                        # Use standard response format for list-type responses
                        if should_use_standard_response(formatted_result):
                            final_result = create_standard_response(formatted_result, f"Successfully executed {name}")
                        else:
                            # For single object responses, return as-is
                            final_result = formatted_result
                        
                        await websocket.send_text(json.dumps(make_result(id_value, final_result)))
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