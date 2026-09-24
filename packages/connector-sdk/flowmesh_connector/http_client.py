"""
FlowMesh Enterprise Requests-based HTTP Client
Provides resilient HTTP session management, connection pooling, automated retries with backoff,
and authentication handling for external SaaS, IT service management (ServiceNow), and REST APIs.
"""

import time
import logging
from typing import Dict, Any, Optional, Tuple, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

logger = logging.getLogger("flowmesh.connector.http")


class FlowMeshHttpClient:
    """Enterprise HTTP client wrapping requests.Session with connection pooling and retries."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        status_forcelist: Optional[Tuple[int, ...]] = None,
        default_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.base_url = (base_url or "").rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

        headers = {
            "User-Agent": "FlowMesh-Enterprise-Connector/1.0",
            "Accept": "application/json",
        }
        if default_headers:
            headers.update(default_headers)
        self.session.headers.update(headers)

        retries = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist or (429, 500, 502, 503, 504),
            raise_on_status=False,
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(
            pool_connections=25,
            pool_maxsize=50,
            max_retries=retries,
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def set_basic_auth(self, username: str, password: str) -> None:
        """Sets HTTP Basic Authentication on the persistent session."""
        self.session.auth = (username, password)

    def set_bearer_token(self, token: str) -> None:
        """Injects Authorization: Bearer <token> into default session headers."""
        self.session.headers["Authorization"] = f"Bearer {token}"

    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Any] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> requests.Response:
        """Executes a managed HTTP request using requests.Session with timing and metrics."""
        url = endpoint if endpoint.startswith(("http://", "https://")) else f"{self.base_url}/{endpoint.lstrip('/')}"
        req_timeout = timeout or self.timeout

        t0 = time.perf_counter()
        try:
            response = self.session.request(
                method=method.upper(),
                url=url,
                params=params,
                json=json_data,
                data=data,
                headers=headers,
                timeout=req_timeout,
            )
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
            logger.debug(
                "HTTP %s %s -> status %d (%0.2fms)",
                method.upper(),
                url,
                response.status_code,
                elapsed_ms,
            )
            return response
        except requests.RequestException as exc:
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
            logger.error("HTTP request failed %s %s after %0.2fms: %s", method, url, elapsed_ms, exc)
            raise

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> requests.Response:
        return self.request("GET", endpoint, params=params, **kwargs)

    def post(self, endpoint: str, json_data: Optional[Any] = None, **kwargs: Any) -> requests.Response:
        return self.request("POST", endpoint, json_data=json_data, **kwargs)

    def patch(self, endpoint: str, json_data: Optional[Any] = None, **kwargs: Any) -> requests.Response:
        return self.request("PATCH", endpoint, json_data=json_data, **kwargs)

    def delete(self, endpoint: str, **kwargs: Any) -> requests.Response:
        return self.request("DELETE", endpoint, **kwargs)

    def close(self) -> None:
        """Closes the underlying requests session and connection pool."""
        self.session.close()
