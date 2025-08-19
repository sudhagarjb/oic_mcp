from __future__ import annotations
import asyncio
import time
from typing import Any, Dict, Optional

import httpx

from .settings import settings


class OAuth2Token:
    def __init__(self, access_token: str, expires_in: int, token_type: str = "Bearer") -> None:
        self.access_token = access_token
        self.token_type = token_type
        # refresh a bit before actual expiry
        self.expires_at_epoch = int(time.time()) + max(expires_in - 30, 0)

    def is_expired(self) -> bool:
        return time.time() >= self.expires_at_epoch


class OICClient:
    def __init__(self) -> None:
        self._token: Optional[OAuth2Token] = None
        self._client: Optional[httpx.AsyncClient] = None
        self._lock = asyncio.Lock()

    def _create_client(self) -> httpx.AsyncClient:
        limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)
        return httpx.AsyncClient(
            timeout=settings.http_timeout_secs,
            limits=limits,
            follow_redirects=True,
        )

    def _ensure_client(self) -> None:
        if self._client is None:
            self._client = self._create_client()

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _ensure_token(self) -> str:
        self._ensure_client()
        async with self._lock:
            if self._token is not None and not self._token.is_expired():
                return self._token.access_token
            data = {
                "grant_type": "client_credentials",
                "client_id": settings.oauth_client_id,
                "client_secret": settings.oauth_client_secret,
            }
            if settings.oauth_scope:
                data["scope"] = settings.oauth_scope
            assert self._client is not None
            resp = await self._client.post(
                settings.oauth_token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            payload = resp.json()
            access_token = payload.get("access_token")
            token_type = payload.get("token_type", "Bearer")
            expires_in = int(payload.get("expires_in", 3600))
            if not access_token:
                raise RuntimeError("OAuth token endpoint did not return access_token")
            self._token = OAuth2Token(access_token=access_token, expires_in=expires_in, token_type=token_type)
            return self._token.access_token

    def _with_instance_param(self, params: Optional[dict[str, Any]]) -> dict[str, Any] | None:
        params = dict(params or {})
        from .settings import settings as _s
        if _s.oic_instance_name:
            params.setdefault("integrationInstance", _s.oic_instance_name)
        return params or None

    async def _request(self, path: str, params: Optional[dict[str, Any]] = None) -> httpx.Response:
        self._ensure_client()
        token = await self._ensure_token()
        url = f"{settings.oic_base_url}{path}"
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        assert self._client is not None
        resp = await self._client.get(url, headers=headers, params=self._with_instance_param(params))
        resp.raise_for_status()
        return resp

    async def _get(self, path: str, params: Optional[dict[str, Any]] = None) -> Dict[str, Any] | Any:
        resp = await self._request(path, params)
        if resp.headers.get("Content-Type", "").startswith("application/json"):
            return resp.json()
        return resp.text

    async def get_raw_path(self, path: str, params: Optional[dict[str, Any]] = None) -> Dict[str, Any]:
        resp = await self._request(path, params)
        content_type = resp.headers.get("Content-Type", "")
        body: Dict[str, Any] = {"contentType": content_type}
        if content_type.startswith("application/json"):
            body["json"] = resp.json()
        else:
            # Return text safely for non-JSON (XML, etc.)
            body["text"] = resp.text
        return body

    # Integration design endpoints
    async def list_integrations(self, only_activated: bool | None = None, limit: int | None = None, page: int | None = None) -> Any:
        params: dict[str, Any] = {}
        if only_activated is not None:
            params["onlyActivated"] = str(only_activated).lower()
        if limit is not None:
            params["limit"] = limit
        if page is not None:
            params["page"] = page
        return await self._get("/ic/api/integration/v1/integrations", params=params or None)

    async def resolve_latest_version(self, code: str, max_pages: int = 20, per_page: int = 100) -> Optional[str]:
        for page in range(1, max_pages + 1):
            data = await self.list_integrations(limit=per_page, page=page)
            items = (data or {}).get("items") or (data.get("content", {}).get("items", [])) if isinstance(data, dict) else []
            for it in items:
                if it.get("code") == code:
                    return it.get("version")
            has_more = isinstance(data, dict) and (bool(data.get("hasMore")) or bool(data.get("content", {}).get("hasMore")))
            if not has_more:
                break
        return None

    async def get_integration(self, identifier: str, version: str | None) -> Any:
        # Accept 'CODE|VERSION' in identifier, or separate code + version; auto-resolve latest if version is empty
        code = identifier
        ver = version or ""
        if "|" in identifier and not version:
            code, ver = identifier.split("|", 1)
        if not ver:
            ver = await self.resolve_latest_version(code) or ""
            if not ver:
                raise httpx.HTTPStatusError("Version not found for code", request=None, response=httpx.Response(404))
        encoded = f"{code}%7C{ver}"
        return await self._get(f"/ic/api/integration/v1/integrations/{encoded}")

    async def list_packages(self, limit: int | None = None) -> Any:
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        # Some tenants expose packages under integration v1, others under design v1
        try:
            return await self._get("/ic/api/integration/v1/packages", params=params or None)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return await self._get("/ic/api/design/v1/packages", params=params or None)
            raise

    async def get_package(self, name: str) -> Any:
        try:
            return await self._get(f"/ic/api/integration/v1/packages/{name}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return await self._get(f"/ic/api/design/v1/packages/{name}")
            raise

    async def list_connections(self, limit: int | None = None) -> Any:
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        return await self._get("/ic/api/integration/v1/connections", params=params or None)

    async def get_connection(self, identifier: str) -> Any:
        return await self._get(f"/ic/api/integration/v1/connections/{identifier}")

    async def list_schedules(self, limit: int | None = None) -> Any:
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        return await self._get("/ic/api/integration/v1/schedules", params=params or None)

    async def list_lookups(self, limit: int | None = None) -> Any:
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        return await self._get("/ic/api/integration/v1/lookups", params=params or None)

    async def get_lookup(self, name: str) -> Any:
        try:
            return await self._get(f"/ic/api/integration/v1/lookups/{name}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return await self._get(f"/ic/api/design/v1/lookups/{name}")
            raise

    async def list_libraries(self, limit: int | None = None) -> Any:
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        try:
            return await self._get("/ic/api/integration/v1/libraries", params=params or None)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return await self._get("/ic/api/design/v1/libraries", params=params or None)
            raise

    async def get_library(self, name: str) -> Any:
        try:
            return await self._get(f"/ic/api/integration/v1/libraries/{name}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return await self._get(f"/ic/api/design/v1/libraries/{name}")
            raise

    async def get_adapter(self, name: str) -> Any:
        # Some tenants expose adapter detail under adapters/{name}
        return await self._get(f"/ic/api/integration/v1/adapters/{name}")

    async def list_adapters(self) -> Any:
        return await self._get("/ic/api/integration/v1/adapters")

    async def list_agents(self) -> Any:
        # Connectivity agents connected to OIC
        return await self._get("/ic/api/integration/v1/agents")

    async def list_agent_groups(self) -> Any:
        return await self._get("/ic/api/integration/v1/agentgroups")

    # Monitoring endpoints (names can vary; try common patterns)
    async def list_instances(self, integration_id: Optional[str] = None, status: Optional[str] = None, start_time: Optional[str] = None, end_time: Optional[str] = None, limit: Optional[int] = None) -> Any:
        params: dict[str, Any] = {}
        if integration_id:
            params["integrationId"] = integration_id
        if status:
            params["status"] = status
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        if limit is not None:
            params["limit"] = limit
        # Try two common endpoints
        try:
            return await self._get("/ic/api/integration/v1/monitoring/instances", params=params or None)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return await self._get("/ic/api/monitoring/v1/instances", params=params or None)
            raise

    async def get_instance(self, instance_id: str) -> Any:
        try:
            return await self._get(f"/ic/api/integration/v1/monitoring/instances/{instance_id}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return await self._get(f"/ic/api/monitoring/v1/instances/{instance_id}")
            raise

    async def list_errors(self, integration_id: Optional[str] = None, limit: Optional[int] = None) -> Any:
        params: dict[str, Any] = {}
        if integration_id:
            params["integrationId"] = integration_id
        if limit is not None:
            params["limit"] = limit
        try:
            return await self._get("/ic/api/integration/v1/monitoring/errors", params=params or None)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return await self._get("/ic/api/monitoring/v1/errors", params=params or None)
            raise

    async def list_metrics(self, metric: str, start_time: Optional[str] = None, end_time: Optional[str] = None) -> Any:
        params: dict[str, Any] = {"metric": metric}
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        try:
            return await self._get("/ic/api/integration/v1/monitoring/metrics", params=params)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return await self._get("/ic/api/monitoring/v1/metrics", params=params)
            raise


oic_client_singleton = OICClient() 