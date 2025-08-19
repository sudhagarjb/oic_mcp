from __future__ import annotations
from typing import Any, TypedDict, Optional


JSONValue = Any


class JSONRPCRequest(TypedDict, total=False):
    jsonrpc: str
    id: int | str | None
    method: str
    params: dict[str, JSONValue] | list[JSONValue]


class JSONRPCError(TypedDict):
    code: int
    message: str
    data: Optional[JSONValue]


class JSONRPCResponse(TypedDict, total=False):
    jsonrpc: str
    id: int | str | None
    result: JSONValue
    error: JSONRPCError


def make_result(id_value: int | str | None, result: JSONValue) -> JSONRPCResponse:
    return {"jsonrpc": "2.0", "id": id_value, "result": result}


def make_error(id_value: int | str | None, code: int, message: str, data: Optional[JSONValue] = None) -> JSONRPCResponse:
    return {"jsonrpc": "2.0", "id": id_value, "error": {"code": code, "message": message, "data": data}} 