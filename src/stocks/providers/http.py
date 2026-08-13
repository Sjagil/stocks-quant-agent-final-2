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


_RETRY = retry(
    retry=retry_if_exception_type(
        (
            httpx.TimeoutException,
            httpx.NetworkError,
            ProviderHTTPError,
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
    def _validate(response: httpx.Response) -> None:
        if response.status_code == 429:
            raise ProviderHTTPError("rate limited")

        if response.status_code >= 500:
            raise ProviderHTTPError(
                f"provider server error {response.status_code}"
            )

        response.raise_for_status()

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

        self._validate(response)

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

        self._validate(response)

        return response.json()
