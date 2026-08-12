from __future__ import annotations

import httpx


class OpenExchangeProvider:
    BASE = "https://openexchangerates.org/api"

    def __init__(self, app_id: str, timeout: float = 20.0) -> None:
        if not app_id:
            raise ValueError("OpenExchangeRates app id is required")
        self.app_id = app_id
        self.client = httpx.Client(timeout=timeout)

    def close(self) -> None:
        self.client.close()

    def latest(self, symbols: list[str] | None = None) -> dict[str, float]:
        params: dict[str, str] = {"app_id": self.app_id}
        if symbols:
            params["symbols"] = ",".join(symbols)
        response = self.client.get(f"{self.BASE}/latest.json", params=params)
        response.raise_for_status()
        return {k: float(v) for k, v in response.json().get("rates", {}).items()}
