from __future__ import annotations

import httpx
import pandas as pd


class FredProvider:
    BASE = "https://api.stlouisfed.org/fred"

    def __init__(self, api_key: str, timeout: float = 20.0) -> None:
        if not api_key:
            raise ValueError("FRED API key is required")
        self.api_key = api_key
        self.client = httpx.Client(timeout=timeout)

    def close(self) -> None:
        self.client.close()

    def series(self, series_id: str, observation_start: str | None = None) -> pd.Series:
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
        }
        if observation_start:
            params["observation_start"] = observation_start
        response = self.client.get(f"{self.BASE}/series/observations", params=params)
        response.raise_for_status()
        observations = response.json().get("observations", [])
        idx, vals = [], []
        for row in observations:
            value = row.get("value")
            if value in (None, "."):
                continue
            idx.append(pd.Timestamp(row["date"], tz="UTC"))
            vals.append(float(value))
        return pd.Series(vals, index=idx, name=series_id, dtype="float64")
