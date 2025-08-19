from __future__ import annotations
from typing import Any, Awaitable, Callable, Dict, List

from .oic_client import oic_client_singleton as oic


ToolHandler = Callable[[dict[str, Any]], Awaitable[Any]]


def _schema_obj(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
	return {
		"type": "object",
		"properties": properties,
		"required": required or [],
		"additionalProperties": False,
	}


def tool_definitions() -> list[dict[str, Any]]:
	return [
		{
			"name": "list_integrations",
			"description": "List integrations. Optional: onlyActivated, limit, page",
			"inputSchema": _schema_obj(
				{
					"onlyActivated": {"type": "boolean"},
					"limit": {"type": "integer", "minimum": 1, "maximum": 1000},
					"page": {"type": "integer", "minimum": 1},
				}
			),
		},
		{
			"name": "get_integration",
			"description": "Get an integration by identifier and version",
			"inputSchema": _schema_obj(
				{
					"identifier": {"type": "string"},
					"version": {"type": "string"},
				},
				["identifier", "version"],
			),
		},
		{
			"name": "list_packages",
			"description": "List packages",
			"inputSchema": _schema_obj({"limit": {"type": "integer", "minimum": 1, "maximum": 1000}}),
		},
		{
			"name": "get_package",
			"description": "Get a package by name",
			"inputSchema": _schema_obj({"name": {"type": "string"}}, ["name"]),
		},
		{
			"name": "list_connections",
			"description": "List connections",
			"inputSchema": _schema_obj({"limit": {"type": "integer", "minimum": 1, "maximum": 1000}}),
		},
		{
			"name": "get_connection",
			"description": "Get a connection by identifier",
			"inputSchema": _schema_obj({"identifier": {"type": "string"}}, ["identifier"]),
		},
		{
			"name": "list_activated_integrations",
			"description": "List only activated integrations",
			"inputSchema": _schema_obj({"limit": {"type": "integer", "minimum": 1, "maximum": 1000}, "page": {"type": "integer", "minimum": 1}}),
		},
		{
			"name": "list_schedules",
			"description": "List schedules",
			"inputSchema": _schema_obj({"limit": {"type": "integer", "minimum": 1, "maximum": 1000}}),
		},
		{
			"name": "list_instances",
			"description": "List runtime instances with filters",
			"inputSchema": _schema_obj(
				{
					"integrationId": {"type": "string"},
					"status": {"type": "string"},
					"startTime": {"type": "string", "description": "ISO-8601"},
					"endTime": {"type": "string", "description": "ISO-8601"},
					"limit": {"type": "integer", "minimum": 1, "maximum": 1000},
				}
			),
		},
		{
			"name": "get_instance",
			"description": "Get instance by ID",
			"inputSchema": _schema_obj({"instanceId": {"type": "string"}}, ["instanceId"]),
		},
		{
			"name": "list_errors",
			"description": "List errors with optional filters",
			"inputSchema": _schema_obj({"integrationId": {"type": "string"}, "limit": {"type": "integer", "minimum": 1, "maximum": 1000}}),
		},
		{
			"name": "list_lookups",
			"description": "List lookups",
			"inputSchema": _schema_obj({"limit": {"type": "integer", "minimum": 1, "maximum": 1000}}),
		},
		{
			"name": "list_adapters",
			"description": "List available adapters",
			"inputSchema": _schema_obj({}),
		},
		{
			"name": "list_agents",
			"description": "List connectivity agents",
			"inputSchema": _schema_obj({}),
		},
		{
			"name": "list_agent_groups",
			"description": "List connectivity agent groups",
			"inputSchema": _schema_obj({}),
		},
		{
			"name": "list_metrics",
			"description": "List metrics by name and optional time range",
			"inputSchema": _schema_obj(
				{
					"metric": {"type": "string"},
					"startTime": {"type": "string", "description": "ISO-8601"},
					"endTime": {"type": "string", "description": "ISO-8601"},
				},
				["metric"],
			),
		},
		{
			"name": "list_integrations_search",
			"description": "Search integrations by terms across code, name, description, keywords (client-side filtering with paging).",
			"inputSchema": _schema_obj(
				{
					"terms": {"type": "array", "items": {"type": "string"}},
					"onlyActivated": {"type": "boolean"},
					"perPage": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50},
					"maxPages": {"type": "integer", "minimum": 1, "maximum": 200, "default": 20},
					"fields": {"type": "array", "items": {"type": "string"}, "default": ["code", "name", "description", "keywords"]},
					"caseSensitive": {"type": "boolean", "default": False},
				},
				["terms"],
			),
		},
		{
			"name": "get_integration_auto",
			"description": "Get integration details by 'code' or 'code|version'; auto-resolves latest version when needed.",
			"inputSchema": _schema_obj(
				{
					"identifier": {"type": "string"},
					"version": {"type": "string", "description": "optional; leave blank if identifier includes code|version or to auto-resolve latest"},
				},
				["identifier"],
			),
		},
		{
			"name": "fetch_raw_path",
			"description": "Fetch an arbitrary OIC relative path (e.g., /ic/api/integration/v1/flows/rest/..); returns JSON or text wrapped in JSON.",
			"inputSchema": _schema_obj(
				{
					"path": {"type": "string"},
				},
				["path"],
			),
		},
		{
			"name": "summarize_integration",
			"description": "Auto-fetch and summarize integration by code or code|version, returning trigger, targets, connections, tracking variables, and status as JSON.",
			"inputSchema": _schema_obj(
				{
					"identifier": {"type": "string"},
					"version": {"type": "string"},
				},
				["identifier"],
			),
		},
	]


async def _call_list_integrations(params: dict[str, Any]) -> Any:
	return await oic.list_integrations(
		only_activated=params.get("onlyActivated"),
		limit=params.get("limit"),
		page=params.get("page"),
	)


async def _call_get_integration(params: dict[str, Any]) -> Any:
	return await oic.get_integration(params["identifier"], params["version"])


async def _call_list_packages(params: dict[str, Any]) -> Any:
	return await oic.list_packages(limit=params.get("limit"))


async def _call_get_package(params: dict[str, Any]) -> Any:
	return await oic.get_package(params["name"])


async def _call_list_connections(params: dict[str, Any]) -> Any:
	return await oic.list_connections(limit=params.get("limit"))


async def _call_get_connection(params: dict[str, Any]) -> Any:
	return await oic.get_connection(params["identifier"])


async def _call_list_activated_integrations(params: dict[str, Any]) -> Any:
	return await oic.list_integrations(only_activated=True, limit=params.get("limit"), page=params.get("page"))


async def _call_list_schedules(params: dict[str, Any]) -> Any:
	return await oic.list_schedules(limit=params.get("limit"))


async def _call_list_instances(params: dict[str, Any]) -> Any:
	return await oic.list_instances(
		integration_id=params.get("integrationId"),
		status=params.get("status"),
		start_time=params.get("startTime"),
		end_time=params.get("endTime"),
		limit=params.get("limit"),
	)


async def _call_get_instance(params: dict[str, Any]) -> Any:
	return await oic.get_instance(params["instanceId"])


async def _call_list_errors(params: dict[str, Any]) -> Any:
	return await oic.list_errors(integration_id=params.get("integrationId"), limit=params.get("limit"))


async def _call_list_lookups(params: dict[str, Any]) -> Any:
	return await oic.list_lookups(limit=params.get("limit"))


async def _call_list_adapters(params: dict[str, Any]) -> Any:
	return await oic.list_adapters()


async def _call_list_agents(params: dict[str, Any]) -> Any:
	return await oic.list_agents()


async def _call_list_agent_groups(params: dict[str, Any]) -> Any:
	return await oic.list_agent_groups()


async def _call_list_metrics(params: dict[str, Any]) -> Any:
	return await oic.list_metrics(metric=params["metric"], start_time=params.get("startTime"), end_time=params.get("endTime"))


def _matches_terms(value: Any, terms: List[str], case_sensitive: bool) -> bool:
	if value is None:
		return False
	text = str(value)
	if not case_sensitive:
		text = text.lower()
		terms = [t.lower() for t in terms]
	return any(t in text for t in terms)


async def _call_list_integrations_search(params: dict[str, Any]) -> Any:
	terms: List[str] = params.get("terms", [])
	if not terms:
		return {"items": [], "totalMatched": 0}
	fields: List[str] = params.get("fields") or ["code", "name", "description", "keywords"]
	per_page: int = params.get("perPage") or 50
	max_pages: int = params.get("maxPages") or 20
	only_activated = params.get("onlyActivated")
	case_sensitive: bool = bool(params.get("caseSensitive", False))

	matched: List[dict[str, Any]] = []
	for page in range(1, max_pages + 1):
		page_data = await oic.list_integrations(only_activated=only_activated, limit=per_page, page=page)
		items = (page_data or {}).get("items") or (page_data.get("content", {}).get("items", [])) if isinstance(page_data, dict) else []
		for it in items:
			if any(_matches_terms(it.get(f), terms, case_sensitive) for f in fields):
				matched.append({
					"code": it.get("code"),
					"name": it.get("name"),
					"version": it.get("version"),
					"status": it.get("status"),
				})
		# detect hasMore from either top-level or nested content
		has_more = False
		if isinstance(page_data, dict):
			has_more = bool(page_data.get("hasMore")) or bool(page_data.get("content", {}).get("hasMore"))
		if not has_more:
			break

	return {"items": matched, "totalMatched": len(matched)}


async def _call_get_integration_auto(params: dict[str, Any]) -> Any:
	return await oic.get_integration(params["identifier"], params.get("version"))


async def _call_fetch_raw_path(params: dict[str, Any]) -> Any:
	return await oic.get_raw_path(params["path"])


def _endpoint_role_name_safe(ep: dict[str, Any]) -> str:
	role = ep.get("role") or ep.get("name") or ""
	return str(role)


def _extract_integration_summary(data: dict[str, Any]) -> dict[str, Any]:
	# Normalize content location
	d = data
	if isinstance(d, dict) and "content" in d and isinstance(d["content"], dict):
		d = d["content"]
	code = d.get("code")
	name = d.get("name")
	version = d.get("version")
	status = d.get("status")
	pattern = d.get("pattern") or d.get("style")
	end_points = d.get("endPoints") or []

	trigger = None
	targets: list[dict[str, Any]] = []
	for ep in end_points:
		role = _endpoint_role_name_safe(ep).upper()
		conn = (ep.get("connection") or {})
		item = {
			"role": role,
			"connectionId": conn.get("id"),
			"agentRequired": conn.get("agentRequired"),
			"adapter": conn.get("adapter") or conn.get("type"),
			"privateEndpoint": conn.get("privateEndpoint"),
		}
		if role in ("SOURCE", "TRIGGER") and trigger is None:
			trigger = item
		else:
			targets.append(item)

	tracking_vars: list[dict[str, Any]] = []
	for tv in d.get("trackingVariables") or []:
		tracking_vars.append({
			"name": tv.get("name"),
			"primary": tv.get("primary"),
			"xpath": tv.get("xpath"),
		})

	return {
		"code": code,
		"name": name,
		"version": version,
		"status": status,
		"pattern": pattern,
		"trigger": trigger,
		"targets": targets,
		"trackingVariables": tracking_vars,
		"links": d.get("links"),
	}


async def _call_summarize_integration(params: dict[str, Any]) -> Any:
	details = await oic.get_integration(params["identifier"], params.get("version"))
	if not isinstance(details, dict):
		return {"summary": {}, "raw": details}
	return {"summary": _extract_integration_summary(details)}


TOOL_HANDLERS: Dict[str, ToolHandler] = {
	"list_integrations": _call_list_integrations,
	"get_integration": _call_get_integration,
	"list_packages": _call_list_packages,
	"get_package": _call_get_package,
	"list_connections": _call_list_connections,
	"get_connection": _call_get_connection,
	"list_activated_integrations": _call_list_activated_integrations,
	"list_schedules": _call_list_schedules,
	"list_instances": _call_list_instances,
	"get_instance": _call_get_instance,
	"list_errors": _call_list_errors,
	"list_lookups": _call_list_lookups,
	"list_adapters": _call_list_adapters,
	"list_agents": _call_list_agents,
	"list_agent_groups": _call_list_agent_groups,
	"list_metrics": _call_list_metrics,
	"list_integrations_search": _call_list_integrations_search,
	"get_integration_auto": _call_get_integration_auto,
	"fetch_raw_path": _call_fetch_raw_path,
	"summarize_integration": _call_summarize_integration,
} 