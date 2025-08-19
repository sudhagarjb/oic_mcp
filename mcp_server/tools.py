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
		{
			"name": "summarize_flow_controls",
			"description": "Parse integration design JSON and summarize Switch, ForEach, Route, Throw Fault, and scopes with counts.",
			"inputSchema": _schema_obj(
				{
					"identifier": {"type": "string"},
					"version": {"type": "string"},
				},
				["identifier"],
			),
		},
		{
			"name": "summarize_mappings",
			"description": "Extract mapping steps and list source->target hints for quick reading (best-effort).",
			"inputSchema": _schema_obj(
				{
					"identifier": {"type": "string"},
					"version": {"type": "string"},
				},
				["identifier"],
			),
		},
		{
			"name": "get_connection_detail",
			"description": "Get a single connection by identifier.",
			"inputSchema": _schema_obj({"identifier": {"type": "string"}}, ["identifier"]),
		},
		{
			"name": "get_lookup",
			"description": "Get a lookup by name.",
			"inputSchema": _schema_obj({"name": {"type": "string"}}, ["name"]),
		},
		{
			"name": "get_library",
			"description": "Get a library by name.",
			"inputSchema": _schema_obj({"name": {"type": "string"}}, ["name"]),
		},
		{
			"name": "get_adapter",
			"description": "Get an adapter by name.",
			"inputSchema": _schema_obj({"name": {"type": "string"}}, ["name"]),
		},
		{
			"name": "search_json",
			"description": "Search any JSON-like structure returned from OIC by simple substring keys/values; helper for research.",
			"inputSchema": _schema_obj(
				{
					"data": {},
					"query": {"type": "string"},
					"maxMatches": {"type": "integer", "minimum": 1, "maximum": 500, "default": 50},
				},
				["data", "query"],
			),
		},
		{
			"name": "list_endpoints",
			"description": "List integration endpoints (name, role, connection).",
			"inputSchema": _schema_obj(
				{
					"identifier": {"type": "string"},
					"version": {"type": "string"},
				},
				["identifier"],
			),
		},
		{
			"name": "get_integration_step",
			"description": "Return raw JSON subtree of a step by name from design JSON.",
			"inputSchema": _schema_obj(
				{
					"identifier": {"type": "string"},
					"version": {"type": "string"},
					"stepName": {"type": "string"},
					"maxMatches": {"type": "integer", "minimum": 1, "maximum": 50, "default": 5},
				},
				["identifier", "stepName"],
			),
		},
		{
			"name": "summarize_step_io",
			"description": "Summarize sources/targets, suspected SQL/query, and parameters for a step by name (best-effort).",
			"inputSchema": _schema_obj(
				{
					"identifier": {"type": "string"},
					"version": {"type": "string"},
					"stepName": {"type": "string"},
				},
				["identifier", "stepName"],
			),
		},
		{
			"name": "export_integration",
			"description": "Export integration archive (zip) and list entries; returns base64 and previews for small files.",
			"inputSchema": _schema_obj(
				{
					"identifier": {"type": "string"},
					"version": {"type": "string"},
					"listOnly": {"type": "boolean"},
					"maxPreviewBytes": {"type": "integer", "minimum": 0, "maximum": 65536, "default": 8192},
				},
				["identifier"],
			),
		},
		{
			"name": "deep_flow_outline",
			"description": "Generate a compact textual outline of major flow steps (Trigger/Scopes/If/Map/Invoke/Throw/ForEach/Switch).",
			"inputSchema": _schema_obj(
				{
					"identifier": {"type": "string"},
					"version": {"type": "string"},
				},
				["identifier"],
			),
		},
		{
			"name": "summarize_integration_with_steps",
			"description": "Summarize integration plus selected steps (names) with I/O summaries inline.",
			"inputSchema": _schema_obj(
				{
					"identifier": {"type": "string"},
					"version": {"type": "string"},
					"stepNames": {"type": "array", "items": {"type": "string"}},
				},
				["identifier", "stepNames"],
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
	summary = _extract_integration_summary(details)
	# Attach counts for quick triage
	d = details.get("content", details)
	counts = {
		"endPoints": len(d.get("endPoints") or []),
		"trackingVariables": len(d.get("trackingVariables") or []),
	}
	return {"summary": summary, "counts": counts}


def _walk(obj):
	if isinstance(obj, dict):
		for k, v in obj.items():
			yield (k, v)
			yield from _walk(v)
	elif isinstance(obj, list):
		for v in obj:
			yield from _walk(v)


def _collect_controls(d: dict[str, Any]) -> dict[str, Any]:
	kinds = {"Switch": 0, "ForEach": 0, "Route": 0, "Throw new fault": 0, "Scope": 0}
	hits: list[dict[str, Any]] = []
	for k, v in _walk(d):
		if isinstance(v, dict):
			t = v.get("type") or v.get("name") or v.get("role") or ""
			if isinstance(t, str):
				for label in kinds.keys():
					if label.lower() in t.lower():
						kinds[label] += 1
						hits.append({"label": label, "name": v.get("name"), "role": v.get("role")})
	return {"counts": kinds, "examples": hits[:20]}


def _collect_mappings(d: dict[str, Any]) -> dict[str, Any]:
	mappings: list[dict[str, Any]] = []
	for k, v in _walk(d):
		if isinstance(v, dict) and (v.get("type") or "").lower().find("map") >= 0:
			mappings.append({"name": v.get("name"), "info": {k1: v.get(k1) for k1 in ("name", "type", "role") if k1 in v}})
	return {"mappings": mappings[:50], "total": len(mappings)}


async def _call_summarize_flow_controls(params: dict[str, Any]) -> Any:
	details = await oic.get_integration(params["identifier"], params.get("version"))
	if not isinstance(details, dict):
		return {"controls": {}, "raw": details}
	d = details.get("content", details)
	return {"controls": _collect_controls(d)}


async def _call_summarize_mappings(params: dict[str, Any]) -> Any:
	details = await oic.get_integration(params["identifier"], params.get("version"))
	if not isinstance(details, dict):
		return {"mappings": {}, "raw": details}
	d = details.get("content", details)
	return _collect_mappings(d)


async def _call_get_connection_detail(params: dict[str, Any]) -> Any:
	return await oic.get_connection(params["identifier"])


async def _call_get_lookup(params: dict[str, Any]) -> Any:
	return await oic.get_lookup(params["name"])


async def _call_get_library(params: dict[str, Any]) -> Any:
	return await oic.get_library(params["name"])


async def _call_get_adapter(params: dict[str, Any]) -> Any:
	return await oic.get_adapter(params["name"])


async def _call_search_json(params: dict[str, Any]) -> Any:
	data = params.get("data")
	q = str(params.get("query"))
	maxm = int(params.get("maxMatches", 50))
	matches: list[dict[str, Any]] = []
	for k, v in _walk(data):
		if len(matches) >= maxm:
			break
		if isinstance(k, str) and q.lower() in k.lower():
			matches.append({"pathKey": k, "value": v if isinstance(v, (str, int, float, bool)) else None})
		if isinstance(v, str) and q.lower() in v.lower():
			matches.append({"pathKey": k, "value": v})
	return {"matches": matches, "query": q}


def _to_design(d: dict[str, Any]) -> dict[str, Any]:
	return d.get("content", d)


async def _call_list_endpoints(params: dict[str, Any]) -> Any:
	details = await oic.get_integration(params["identifier"], params.get("version"))
	if not isinstance(details, dict):
		return {"endPoints": []}
	d = _to_design(details)
	eps = []
	for ep in d.get("endPoints", []) or []:
		conn = ep.get("connection") or {}
		eps.append({
			"name": ep.get("name"),
			"role": ep.get("role"),
			"connectionId": conn.get("id"),
			"adapter": conn.get("adapter") or conn.get("type"),
		})
	return {"endPoints": eps}


def _find_nodes_by_name(d: Any, name: str, max_matches: int) -> list[dict[str, Any]]:
	results: list[dict[str, Any]] = []
	needle = name.lower()
	for k, v in _walk(d):
		if isinstance(v, dict):
			nm = str(v.get("name", ""))
			if nm and nm.lower() == needle:
				results.append(v)
				if len(results) >= max_matches:
					break
	return results


def _find_nodes_fuzzy(d: Any, name: str, max_matches: int) -> list[dict[str, Any]]:
	results: list[dict[str, Any]] = []
	needle = name.lower()
	for k, v in _walk(d):
		if isinstance(v, dict):
			nm = str(v.get("name", ""))
			if nm and needle in nm.lower():
				results.append(v)
				if len(results) >= max_matches:
					break
	return results


async def _call_get_integration_step(params: dict[str, Any]) -> Any:
	details = await oic.get_integration(params["identifier"], params.get("version"))
	if not isinstance(details, dict):
		return {"steps": [], "endpoints": []}
	d = _to_design(details)
	steps = _find_nodes_by_name(d, params["stepName"], int(params.get("maxMatches", 5)))
	# Fuzzy fallback
	if not steps:
		steps = _find_nodes_fuzzy(d, params["stepName"], int(params.get("maxMatches", 5)))
	endpoints = []
	for ep in (d.get("endPoints") or []):
		nm = str(ep.get("name", ""))
		if nm and params["stepName"].lower() in nm.lower():
			endpoints.append(ep)
	return {"steps": steps, "endpoints": endpoints}


def _extract_sql_and_params(node: dict[str, Any]) -> dict[str, Any]:
	sql_keys = ["sql", "statement", "query", "select", "insert", "update", "delete"]
	param_keys = [
		"parameters",
		"templateParameters",
		"connectivityProperties",
		"request",
		"response",
		"payload",
		"binding",
	]
	found_sql: list[str] = []
	found_params: dict[str, Any] = {}

	for k, v in _walk(node):
		if isinstance(k, str):
			lk = k.lower()
			if any(sk in lk for sk in sql_keys) and isinstance(v, str):
				# Keep distinct snippets
				snip = v.strip()
				if snip and snip not in found_sql:
					found_sql.append(snip)
			if k in param_keys and v is not None:
				found_params.setdefault(k, v)
	return {"sql": found_sql[:5], "parameters": found_params}


async def _call_summarize_step_io(params: dict[str, Any]) -> Any:
	details = await oic.get_integration(params["identifier"], params.get("version"))
	if not isinstance(details, dict):
		return {"step": {}, "io": {}}
	d = _to_design(details)
	steps = _find_nodes_by_name(d, params["stepName"], 1)
	endpoints = d.get("endPoints") or []
	ep = next((e for e in endpoints if str(e.get("name")).lower() == params["stepName"].lower()), None)

	if not steps:
		# Fallback: treat endpoint as step if found
		if ep:
			conn = ep.get("connection") or {}
			return {
				"step": {"name": ep.get("name"), "type": "endpoint", "role": ep.get("role")},
				"io": {
					"sql": [],
					"parameters": {},
					"connection": {
						"connectionId": conn.get("id"),
						"adapter": conn.get("adapter") or conn.get("type"),
						"role": ep.get("role"),
					},
				},
			}
		return {"step": {}, "io": {}}

	step = steps[0]
	io = _extract_sql_and_params(step)
	if ep:
		conn = ep.get("connection") or {}
		io["connection"] = {
			"connectionId": conn.get("id"),
			"adapter": conn.get("adapter") or conn.get("type"),
			"role": ep.get("role"),
		}
	return {"step": {"name": step.get("name"), "type": step.get("type"), "role": step.get("role")}, "io": io}


async def _call_export_integration(params: dict[str, Any]) -> Any:
	return await oic.export_integration(
		params["identifier"],
		params.get("version"),
		list_only=bool(params.get("listOnly", False)),
		max_preview_bytes=int(params.get("maxPreviewBytes", 8192)),
	)


def _outline_from_design(d: dict[str, Any]) -> list[str]:
	lines: list[str] = []
	# Trigger
	for ep in d.get("endPoints", []) or []:
		conn = ep.get("connection") or {}
		if str(ep.get("role", "")).upper() == "SOURCE":
			lines.append(f"Trigger | Trigger using {conn.get('id')} connection of type {conn.get('type') or conn.get('adapter') or 'unknown'}")
	# Walk nodes; best-effort labels
	for k, v in _walk(d):
		if not isinstance(v, dict):
			continue
		name = str(v.get("name", ""))
		t = (v.get("type") or v.get("role") or name).lower()
		def add(lbl: str):
			if name:
				lines.append(f"{lbl} | {name}")
			else:
				lines.append(lbl)
		if "scope" in t:
			add("Scope")
		elif t.startswith("if") or "switch" in t or "route" in t:
			add("If/Switch/Route")
		elif "map" in t:
			add("Map")
		elif "invoke" in t:
			add("Invoke")
		elif "throw" in t:
			add("Throw new fault")
		elif "for each" in t or "foreach" in t:
			add("For each")
		elif "stitch" in t:
			add("Stitch")
	return lines[:500]


async def _call_deep_flow_outline(params: dict[str, Any]) -> Any:
	details = await oic.get_integration(params["identifier"], params.get("version"))
	if not isinstance(details, dict):
		return {"outline": []}
	d = _to_design(details)
	return {"outline": _outline_from_design(d)}


async def _call_summarize_integration_with_steps(params: dict[str, Any]) -> Any:
	base = await _call_summarize_integration(params)
	names: List[str] = params.get("stepNames") or []
	step_summaries: list[dict[str, Any]] = []
	for nm in names:
		sub = await _call_summarize_step_io({
			"identifier": params["identifier"],
			"version": params.get("version"),
			"stepName": nm,
		})
		step_summaries.append({"name": nm, "data": sub})
	base["steps"] = step_summaries
	return base


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
	"summarize_flow_controls": _call_summarize_flow_controls,
	"summarize_mappings": _call_summarize_mappings,
	"get_connection_detail": _call_get_connection_detail,
	"get_lookup": _call_get_lookup,
	"get_library": _call_get_library,
	"get_adapter": _call_get_adapter,
	"search_json": _call_search_json,
	"list_endpoints": _call_list_endpoints,
	"get_integration_step": _call_get_integration_step,
	"summarize_step_io": _call_summarize_step_io,
	"export_integration": _call_export_integration,
	"deep_flow_outline": _call_deep_flow_outline,
	"summarize_integration_with_steps": _call_summarize_integration_with_steps,
} 