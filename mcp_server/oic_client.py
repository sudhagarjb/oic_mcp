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
        retry = httpx.Retry(max_tries=max(1, settings.http_max_retries + 1))
        limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)
        self._client = httpx.AsyncClient(
            timeout=settings.http_timeout_secs,
            limits=limits,
            transport=httpx.AsyncHTTPTransport(retries=retry),
        )
        self._lock = asyncio.Lock()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _ensure_token(self) -> str:
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
            resp = await self._client.post(settings.oauth_token_url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
            resp.raise_for_status()
            payload = resp.json()
            access_token = payload.get("access_token")
            token_type = payload.get("token_type", "Bearer")
            expires_in = int(payload.get("expires_in", 3600))
            if not access_token:
                raise RuntimeError("OAuth token endpoint did not return access_token")
            self._token = OAuth2Token(access_token=access_token, expires_in=expires_in, token_type=token_type)
            return self._token.access_token

    async def _get(self, path: str, params: Optional[dict[str, Any]] = None) -> Dict[str, Any] | Any:
        token = await self._ensure_token()
        url = f"{settings.oic_base_url}{path}"
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        resp = await self._client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        if resp.headers.get("Content-Type", "").startswith("application/json"):
            return resp.json()
        return resp.text

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

    async def get_integration(self, identifier: str, version: str) -> Any:
        return await self._get(f"/ic/api/integration/v1/integrations/{identifier}/versions/{version}")

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