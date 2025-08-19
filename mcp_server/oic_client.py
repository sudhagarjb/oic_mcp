from __future__ import annotations
import asyncio
import time
import logging
from typing import Any, Dict, Optional

import httpx
import base64
import zipfile
import io

from .settings import settings

# Setup logging for OIC client
logger = logging.getLogger(__name__)

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
                logger.debug("Using existing OAuth token")
                return self._token.access_token
            
            logger.info("Fetching new OAuth token")
            token_start_time = time.time()
            
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
            
            token_time = time.time() - token_start_time
            logger.info(f"OAuth token fetched successfully in {token_time:.2f}s")
            return self._token.access_token

    def _with_instance_param(self, params: Optional[dict[str, Any]]) -> dict[str, Any] | None:
        params = dict(params or {})
        from .settings import settings as _s
        if _s.oic_instance_name:
            params.setdefault("integrationInstance", _s.oic_instance_name)
        return params or None

    async def _request(self, path: str, params: Optional[dict[str, Any]] = None, headers_override: Optional[dict[str, str]] = None) -> httpx.Response:
        self._ensure_client()
        token = await self._ensure_token()
        url = f"{settings.oic_base_url}{path}"
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        if headers_override:
            headers.update(headers_override)
        
        request_start_time = time.time()
        logger.debug(f"Making HTTP request to: {url}")
        logger.debug(f"Request params: {params}")
        
        assert self._client is not None
        resp = await self._client.get(url, headers=headers, params=self._with_instance_param(params))
        
        request_time = time.time() - request_start_time
        logger.info(f"HTTP request to {path} completed in {request_time:.2f}s (Status: {resp.status_code})")
        
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
        logger.info(f"Calling list_integrations - only_activated: {only_activated}, limit: {limit}, page: {page}")
        
        params: dict[str, Any] = {}
        if only_activated is not None:
            params["onlyActivated"] = str(only_activated).lower()
        if limit is not None:
            params["limit"] = limit
        if page is not None:
            params["page"] = page
        
        start_time = time.time()
        result = await self._get("/ic/api/integration/v1/integrations", params=params or None)
        execution_time = time.time() - start_time
        
        # Log response details
        if isinstance(result, dict):
            items_count = len(result.get("items", [])) if "items" in result else 0
            total_results = result.get("totalResults", 0)
            has_more = result.get("hasMore", False)
            logger.info(f"list_integrations returned {items_count} items, total: {total_results}, hasMore: {has_more} in {execution_time:.2f}s")
        else:
            logger.warning(f"list_integrations returned non-dict result: {type(result)} in {execution_time:.2f}s")
        
        return result

    async def list_all_integrations(self, only_activated: bool | None = None, max_pages: int = 100, per_page: int = 100) -> list[Dict[str, Any]]:
        """
        Fetch all integrations across all pages, handling pagination issues.
        Returns a deduplicated list of all integrations found.
        """
        logger.info(f"Starting list_all_integrations - only_activated: {only_activated}, max_pages: {max_pages}, per_page: {per_page}")
        
        all_integrations = []
        seen_codes = set()  # Track seen integration codes to avoid duplicates
        page = 1
        total_start_time = time.time()
        consecutive_empty_pages = 0  # Track consecutive pages with no new integrations
        max_consecutive_empty = 3  # Stop after 3 consecutive pages with no new integrations
        
        while page <= max_pages:
            page_start_time = time.time()
            logger.info(f"Fetching page {page}/{max_pages}")
            
            try:
                data = await self.list_integrations(only_activated=only_activated, limit=per_page, page=page)
                
                # Handle different response structures
                items = []
                if isinstance(data, dict):
                    if "items" in data:
                        items = data["items"]
                    elif "content" in data and isinstance(data["content"], dict) and "items" in data["content"]:
                        items = data["content"]["items"]
                    elif "data" in data and isinstance(data["data"], dict) and "items" in data["data"]:
                        items = data["data"]["items"]
                
                if not items:
                    logger.info(f"No items found on page {page}, stopping pagination")
                    break  # No more items to fetch
                
                # Add only unique integrations (by code)
                new_integrations = []
                for item in items:
                    code = item.get("code")
                    if code and code not in seen_codes:
                        seen_codes.add(code)
                        new_integrations.append(item)
                
                all_integrations.extend(new_integrations)
                
                page_time = time.time() - page_start_time
                logger.info(f"Page {page}: found {len(items)} items, {len(new_integrations)} new unique, total so far: {len(all_integrations)} in {page_time:.2f}s")
                
                # Check if we got any new integrations
                if len(new_integrations) == 0:
                    consecutive_empty_pages += 1
                    logger.info(f"No new unique integrations on page {page}. Consecutive empty pages: {consecutive_empty_pages}")
                    
                    if consecutive_empty_pages >= max_consecutive_empty:
                        logger.info(f"Stopping pagination after {consecutive_empty_pages} consecutive pages with no new integrations")
                        break
                else:
                    consecutive_empty_pages = 0  # Reset counter when we find new integrations
                
                # Check if there are more pages
                has_more = False
                if isinstance(data, dict):
                    has_more = bool(data.get("hasMore")) or bool(data.get("content", {}).get("hasMore")) or bool(data.get("data", {}).get("hasMore"))
                
                if not has_more:
                    logger.info(f"No more pages indicated by API response")
                    break
                
                page += 1
                
            except Exception as e:
                # Log error and break to avoid infinite loops
                page_time = time.time() - page_start_time
                logger.error(f"Error fetching page {page} after {page_time:.2f}s: {e}")
                break
        
        total_time = time.time() - total_start_time
        logger.info(f"list_all_integrations completed: fetched {len(all_integrations)} unique integrations from {page-1} pages in {total_time:.2f}s")
        
        return all_integrations

    async def resolve_latest_version(self, code: str, max_pages: int = 50, per_page: int = 100) -> Optional[str]:
        logger.info(f"Resolving latest version for code: {code}")
        start_time = time.time()
        
        # Use the new list_all_integrations method for better pagination handling
        all_integrations = await self.list_all_integrations(max_pages=max_pages, per_page=per_page)
        
        for integration in all_integrations:
            if integration.get("code") == code:
                version = integration.get("version")
                execution_time = time.time() - start_time
                logger.info(f"Found latest version for {code}: {version} in {execution_time:.2f}s")
                return version
        
        execution_time = time.time() - start_time
        logger.warning(f"No version found for code {code} in {execution_time:.2f}s")
        return None

    async def get_integration(self, identifier: str, version: str | None) -> Any:
        logger.info(f"Getting integration: {identifier}, version: {version}")
        start_time = time.time()
        
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
        result = await self._get(f"/ic/api/integration/v1/integrations/{encoded}")
        
        execution_time = time.time() - start_time
        logger.info(f"get_integration completed for {identifier} in {execution_time:.2f}s")
        return result

    async def export_integration(self, identifier: str, version: str | None, list_only: bool = False, max_preview_bytes: int = 8192) -> Dict[str, Any]:
        # Export archive (zip) of the integration
        code = identifier
        ver = version or ""
        if "|" in identifier and not version:
            code, ver = identifier.split("|", 1)
        if not ver:
            ver = await self.resolve_latest_version(code) or ""
            if not ver:
                raise httpx.HTTPStatusError("Version not found for code", request=None, response=httpx.Response(404))
        encoded = f"{code}%7C{ver}"
        resp = await self._request(
            f"/ic/api/integration/v1/integrations/{encoded}/archive",
            headers_override={"Accept": "application/zip"},
        )
        cd = resp.headers.get("Content-Disposition", "")
        file_name = None
        if "filename=" in cd:
            file_name = cd.split("filename=", 1)[-1].strip('"')
        content_b64 = base64.b64encode(resp.content).decode("ascii")
        result: Dict[str, Any] = {
            "contentType": resp.headers.get("Content-Type", ""),
            "fileName": file_name or f"{code}_{ver}.zip",
            "size": len(resp.content),
        }
        # Optionally list entries
        try:
            zf = zipfile.ZipFile(io.BytesIO(resp.content))
            entries = []
            for zi in zf.infolist():
                ent: Dict[str, Any] = {"name": zi.filename, "size": zi.file_size}
                if not list_only and zi.file_size <= max_preview_bytes and not zi.is_dir():
                    data = zf.read(zi)
                    # Try to decode as text for JSON/XML readability
                    try:
                        ent["textPreview"] = data.decode("utf-8", errors="replace")
                    except Exception:  # noqa: BLE001
                        pass
                entries.append(ent)
            result["entries"] = entries
        except Exception:  # noqa: BLE001
            # Keep just the archive
            pass
        if not list_only:
            result["archiveBase64"] = content_b64
        return result

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