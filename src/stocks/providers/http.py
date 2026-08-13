from __future__ import annotations

from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)


class ProviderHTTPError(RuntimeError):
    pass


class ProviderTransientError(ProviderHTTPError):
    pass


class ProviderAuthenticationError(ProviderHTTPError):
    pass


class ProviderEntitlementError(ProviderHTTPError):
    pass


class ProviderRequestError(ProviderHTTPError):
    pass


_RETRY = retry(
    retry=retry_if_exception_type(
        (
            httpx.TimeoutException,
            httpx.NetworkError,
            ProviderTransientError,
        )
    ),
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(
        initial=0.5,
        max=8.0,
    ),
    reraise=True,
)


class ProviderHTTPClient:
    def __init__(
        self,
        *,
        timeout: float = 20.0,
        user_agent: str = "stocks-quant-agent/1.0 research",
    ) -> None:
        self.client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={
                "User-Agent": user_agent,
                "Accept": "application/json",
            },
        )

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> "ProviderHTTPClient":
        return self

    def __exit__(
        self,
        exc_type,
        exc,
        tb,
    ) -> None:
        self.close()

    @staticmethod
    def _safe_endpoint(
        response: httpx.Response,
    ) -> str:
        return (
            f"{response.request.url.scheme}://"
            f"{response.request.url.host}"
            f"{response.request.url.path}"
        )

    @classmethod
    def _validate(
        cls,
        response: httpx.Response,
    ) -> None:
        status = response.status_code
        endpoint = cls._safe_endpoint(
            response
        )

        if status < 400:
            return

        if status == 401:
            raise ProviderAuthenticationError(
                f"HTTP 401 authentication failure: {endpoint}"
            )

        if status in {
            402,
            403,
        }:
            raise ProviderEntitlementError(
                f"HTTP {status} entitlement unavailable: {endpoint}"
            )

        if status == 429:
            raise ProviderTransientError(
                f"HTTP 429 rate limited: {endpoint}"
            )

        if status >= 500:
            raise ProviderTransientError(
                f"HTTP {status} provider server error: {endpoint}"
            )

        raise ProviderRequestError(
            f"HTTP {status} provider request rejected: {endpoint}"
        )

    @_RETRY
    def get_json(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        response = self.client.get(
            url,
            params=params,
            headers=headers,
        )

        self._validate(
            response
        )

        return response.json()

    @_RETRY
    def post_json(
        self,
        url: str,
        *,
        payload: Any,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        response = self.client.post(
            url,
            params=params,
            json=payload,
            headers=headers,
        )

        self._validate(
            response
        )

        return response.json()
