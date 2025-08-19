from __future__ import annotations
import json
import logging
import time
from typing import Any, Dict, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from .jsonrpc import JSONRPCRequest, make_error, make_result
from .tools import tool_definitions, TOOL_HANDLERS
from .oic_client import oic_client_singleton as oic

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_server.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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
    logger.info("WebSocket connection accepted")
    
    try:
        while True:
            raw = await websocket.receive_text()
            request_start_time = time.time()
            
            try:
                req: JSONRPCRequest = json.loads(raw)
                method = req.get("method")
                id_value = req.get("id")
                params = req.get("params") or {}
                if not isinstance(params, dict):
                    params = {}

                logger.info(f"Received MCP request: {method} (ID: {id_value})")
                logger.debug(f"Request params: {json.dumps(params, indent=2)}")

                if method == "initialize":
                    logger.info("Processing initialize request")
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
                    logger.info("Initialize request completed")

                elif method == "tools/list":
                    logger.info("Processing tools/list request")
                    tools = tool_definitions()
                    await websocket.send_text(json.dumps(make_result(id_value, {"tools": tools})))
                    logger.info("Tools list request completed")

                elif method == "tools/call":
                    name = params.get("name")
                    arguments = params.get("arguments") or {}
                    if not name or name not in TOOL_HANDLERS:
                        error_msg = f"Unknown tool: {name}"
                        logger.error(error_msg)
                        await websocket.send_text(json.dumps(make_error(id_value, -32601, error_msg)))
                        continue
                    
                    logger.info(f"Executing tool: {name}")
                    logger.debug(f"Tool arguments: {json.dumps(arguments, indent=2)}")
                    
                    tool_start_time = time.time()
                    try:
                        result = await TOOL_HANDLERS[name](arguments)
                        tool_execution_time = time.time() - tool_start_time
                        
                        logger.info(f"Tool {name} executed successfully in {tool_execution_time:.2f}s")
                        logger.debug(f"Tool result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                        
                        # Format the response to handle OIC API structure internally
                        format_start_time = time.time()
                        formatted_result = format_mcp_response(result)
                        format_time = time.time() - format_start_time
                        
                        logger.debug(f"Response formatting took {format_time:.2f}s")
                        
                        # Use standard response format for list-type responses
                        if should_use_standard_response(formatted_result):
                            final_result = create_standard_response(formatted_result, f"Successfully executed {name}")
                        else:
                            # For single object responses, return as-is
                            final_result = formatted_result
                        
                        await websocket.send_text(json.dumps(make_result(id_value, final_result)))
                        
                        total_request_time = time.time() - request_start_time
                        logger.info(f"Tool {name} request completed in {total_request_time:.2f}s total")
                        
                    except Exception as e:  # noqa: BLE001
                        tool_execution_time = time.time() - tool_start_time
                        error_msg = f"Tool execution error: {str(e)}"
                        logger.error(f"Tool {name} failed after {tool_execution_time:.2f}s: {e}")
                        await websocket.send_text(json.dumps(make_error(id_value, -32000, error_msg, {"name": name, "error": str(e)})))

                else:
                    error_msg = f"Unknown method: {method}"
                    logger.error(error_msg)
                    await websocket.send_text(json.dumps(make_error(id_value, -32601, error_msg)))

            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                await websocket.send_text(json.dumps(make_error(None, -32700, "Parse error")))
            except Exception as e:
                logger.error(f"Unexpected error processing request: {e}")
                await websocket.send_text(json.dumps(make_error(None, -32603, f"Internal error: {str(e)}")))
                
    except WebSocketDisconnect:
        logger.info("WebSocket connection disconnected")
        return
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        logger.info("Closing OIC client connection")
        await oic.aclose() 