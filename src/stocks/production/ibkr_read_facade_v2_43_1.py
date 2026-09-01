from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from stocks.integrations.registry import IntegrationRegistry
from stocks.integrations.runner import IntegrationRunner
from stocks.providers.env import load_project_env

from .contracts_v2_41 import BrokerSnapshot, QuoteSnapshot
from .ibkr_reference_snapshot_v2_43_1 import fetch_reference_broker_snapshot_v2431


class IBKRReadFacadeV2431:
    """Read-only production facade backed by the imported Stocks native IB API stack."""

    def __init__(self, root: str | Path, cfg: dict[str, Any]) -> None:
        self.root = Path(root).resolve()
        self.cfg = cfg
        self.write_calls = 0
        self._snapshot: BrokerSnapshot | None = None
        load_project_env(self.root)
        registry = IntegrationRegistry.load(
            self.root / "config/integrations.yaml",
            project_root=self.root,
        )
        self.runner = IntegrationRunner(registry)

    def __enter__(self) -> "IBKRReadFacadeV2431":
        result = fetch_reference_broker_snapshot_v2431(self.root)
        if result.snapshot is None:
            raise RuntimeError(
                "IBKR_REFERENCE_SNAPSHOT_UNAVAILABLE:"
                + "|".join(result.blockers)
            )
        self._snapshot = result.snapshot
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def snapshot(self) -> BrokerSnapshot:
        if self._snapshot is None:
            raise RuntimeError("IBKR_REFERENCE_SNAPSHOT_NOT_LOADED")
        return self._snapshot

    def _quote_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = self.runner.run(
            "stocks_ibkr_reference",
            "quote_read_only",
            payload,
            timeout_seconds=45,
        )
        if not response.ok or not response.artifacts:
            raise RuntimeError(
                "IBKR_REFERENCE_QUOTE_FAILED:"
                + str(response.error or getattr(response.state, "value", response.state))
            )
        data = json.loads(Path(response.artifacts[0].path).read_text(encoding="utf-8"))
        if int(data.get("broker_write_calls", 0)) != 0:
            raise RuntimeError("IBKR_REFERENCE_QUOTE_WRITE_COUNTER_NONZERO")
        return data

    def quote(self, symbol: str) -> QuoteSnapshot:
        data = self._quote_payload({"symbol": str(symbol).upper()})
        quote = dict(data.get("quote") or {})
        bid = float(quote.get("bid"))
        ask = float(quote.get("ask"))
        if bid <= 0 or ask <= 0 or ask < bid:
            raise RuntimeError(f"invalid bid/ask for {symbol}: bid={bid} ask={ask}")
        last = quote.get("last")
        return QuoteSnapshot(
            symbol=str(symbol).upper(),
            bid=bid,
            ask=ask,
            last=float(last) if last not in (None, "") else None,
            min_tick=float(quote.get("min_tick") or 0.01),
            observed_at=str(data.get("captured_at")),
        )

    def fx_to_asset_currency(self, base_currency: str, asset_currency: str = "USD") -> float:
        base = str(base_currency).upper()
        quote = str(asset_currency).upper()
        if base == quote:
            return 1.0
        data = self._quote_payload({"fx_base": base, "fx_quote": quote})
        fx = dict(data.get("fx") or {})
        bid = float(fx.get("bid") or 0)
        ask = float(fx.get("ask") or 0)
        last = float(fx.get("last") or 0)
        if bid > 0 and ask >= bid:
            return (bid + ask) / 2.0
        if last > 0:
            return last
        raise RuntimeError(f"no usable IBKR FX quote for {base}{quote}")


__all__ = ["IBKRReadFacadeV2431"]
