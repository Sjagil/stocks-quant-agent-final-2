from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .nlp_context import read_nlp_context


@dataclass(frozen=True)
class ModalityState:
    name: str
    score: float
    confidence: float
    available: bool
    training_safe: bool
    source: str
    source_class: str
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CurrentContextSnapshot:
    symbol: str
    timeframe: str
    observed_at: str
    score: float
    confidence: float
    modifier: float
    modalities: tuple[ModalityState, ...]
    source: str = "MULTIMODAL_CONTEXT_V2_14"
    execution_authority: str = "NONE"

    @property
    def sentiment(self) -> float:
        # Compatibility with the previous NLP-only pipeline field name.
        return self.score

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "observed_at": self.observed_at,
            "score": self.score,
            "confidence": self.confidence,
            "modifier": self.modifier,
            "modalities": [item.to_dict() for item in self.modalities],
            "source": self.source,
            "execution_authority": self.execution_authority,
        }


def _finite(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _clip(value: float) -> float:
    return float(np.clip(value, -1.0, 1.0))


def _unavailable(name: str, source: str) -> ModalityState:
    return ModalityState(
        name=name,
        score=0.0,
        confidence=0.0,
        available=False,
        training_safe=False,
        source=source,
        source_class="UNAVAILABLE",
        details={},
    )


def _latest_reference_context(root: Path) -> Path | None:
    candidates = sorted(
        root.glob(
            "artifacts/integrations/stocks_context_reference/**/"
            "stocks_reference_contextual_candidates_v2.json"
        )
    )
    return candidates[-1] if candidates else None


def _reference_modalities(
    root: Path,
    symbol: str,
) -> tuple[ModalityState, ModalityState, ModalityState]:
    path = _latest_reference_context(root)
    if path is None:
        return (
            _unavailable("fundamental", "NO_REFERENCE_CONTEXT"),
            _unavailable("macro", "NO_REFERENCE_CONTEXT"),
            _unavailable("sec", "NO_REFERENCE_CONTEXT"),
        )

    payload = json.loads(path.read_text(encoding="utf-8"))
    row = next(
        (
            item
            for item in payload.get("records", [])
            if str(item.get("symbol", "")).upper() == symbol
        ),
        None,
    )
    if row is None:
        macro_available = bool(payload.get("macro_regime"))
        return (
            _unavailable("fundamental", str(path)),
            ModalityState(
                name="macro",
                score=0.0,
                confidence=0.25 if macro_available else 0.0,
                available=macro_available,
                training_safe=False,
                source=str(path),
                source_class="CURRENT_CAUSAL_MACRO_SNAPSHOT_NOT_HISTORY",
                details={
                    "macro_regime": payload.get("macro_regime"),
                    "macro_data_status": payload.get("macro_data_status"),
                },
            ),
            _unavailable("sec", str(path)),
        )

    fundamental_score = _finite(row.get("fundamental_score"))
    coverage = _finite(row.get("fundamental_coverage"))
    fundamental = ModalityState(
        name="fundamental",
        score=(
            _clip((fundamental_score - 50.0) / 50.0)
            if fundamental_score is not None
            else 0.0
        ),
        confidence=float(np.clip(coverage if coverage is not None else 0.0, 0.0, 1.0)),
        available=fundamental_score is not None,
        training_safe=False,
        source=str(path),
        source_class="CURRENT_CAUSAL_DISCOVERY_SNAPSHOT_NOT_HISTORY",
        details={
            "fundamental_score": fundamental_score,
            "fundamental_coverage": coverage,
            "research_score": row.get("research_score"),
            "technical_score": row.get("technical_score"),
            "liquidity_score": row.get("liquidity_score"),
            "risk_score": row.get("risk_score"),
            "shariah_gate": row.get("shariah_gate"),
        },
    )

    macro_score = _finite(row.get("macro_score"))
    macro = ModalityState(
        name="macro",
        score=(
            _clip((macro_score - 50.0) / 50.0)
            if macro_score is not None and abs(macro_score) > 1.0
            else _clip(macro_score or 0.0)
        ),
        confidence=0.7 if macro_score is not None else 0.25,
        available=macro_score is not None or bool(payload.get("macro_regime")),
        training_safe=False,
        source=str(path),
        source_class="CURRENT_CAUSAL_MACRO_SNAPSHOT_NOT_HISTORY",
        details={
            "macro_score": macro_score,
            "macro_regime": payload.get("macro_regime"),
            "macro_data_status": payload.get("macro_data_status"),
        },
    )

    sec_context = row.get("sec_context") or {}
    overlay = sec_context.get("overlay") or {}
    sec_points = _finite(overlay.get("sec_overlay_points")) or 0.0
    sec_status = str(sec_context.get("status") or "")
    sec = ModalityState(
        name="sec",
        score=_clip(sec_points / 4.0),
        confidence=0.6 if sec_status and sec_status != "UNAVAILABLE" else 0.0,
        available=bool(sec_status and sec_status != "UNAVAILABLE"),
        training_safe=False,
        source=str(path),
        source_class="SEC_RANKING_OVERLAY_CURRENT_SNAPSHOT",
        details={
            "status": sec_status,
            "sec_overlay_points": sec_points,
            "standalone_entry_allowed": sec_context.get("standalone_entry_allowed", False),
        },
    )
    return fundamental, macro, sec


def _news_modality(root: Path, symbol: str) -> ModalityState:
    nlp = read_nlp_context(root, symbol)
    return ModalityState(
        name="news",
        score=_clip(nlp.sentiment * max(nlp.confidence, 0.0)),
        confidence=float(np.clip(nlp.confidence, 0.0, 1.0)),
        available=nlp.stories > 0,
        training_safe=False,
        source=nlp.source,
        source_class="CURRENT_NEWS_NLP_SNAPSHOT",
        details={"sentiment": nlp.sentiment, "stories": nlp.stories},
    )


def _gex_modality(root: Path, symbol: str) -> ModalityState:
    candidates = (
        root / "references/Stocks/output/market_context/gex-context.json",
        root / "output/market_context/gex-context.json",
    )
    path = next((item for item in candidates if item.is_file()), None)
    if path is None:
        return _unavailable("gex", "NO_GEX_CONTEXT")

    payload = json.loads(path.read_text(encoding="utf-8"))
    row = next(
        (
            item
            for item in payload.get("contexts", [])
            if str(item.get("symbol", "")).upper() == symbol
        ),
        None,
    )
    if not row or str(row.get("status")) != "AVAILABLE_CONTEXT_ONLY":
        return _unavailable("gex", str(path))

    net = _finite(row.get("net_gex_1pct"))
    gross = _finite(row.get("gross_absolute_gex_1pct"))
    if net is not None and gross is not None and gross > 0.0:
        score = _clip(net / gross)
    else:
        legacy = _finite(row.get("net_gex_legacy"))
        score = _clip(float(np.sign(legacy)) * 0.25) if legacy is not None else 0.0

    return ModalityState(
        name="gex",
        score=score,
        confidence=float(np.clip(_finite(row.get("confidence")) or 0.0, 0.0, 1.0)),
        available=True,
        training_safe=False,
        source=str(path),
        source_class=str(row.get("source_mode") or "CURRENT_CHAIN_NOT_PIT"),
        details={
            "regime_proxy": row.get("regime_proxy"),
            "call_wall": row.get("call_wall"),
            "put_wall": row.get("put_wall"),
            "gamma_flip": row.get("gamma_flip"),
            "distance_to_call_wall_atr": row.get("distance_to_call_wall_atr"),
            "distance_to_put_wall_atr": row.get("distance_to_put_wall_atr"),
            "distance_to_flip_atr": row.get("distance_to_flip_atr"),
            "gex_concentration_top3": row.get("gex_concentration_top3"),
            "iv_skew_25d": row.get("iv_skew_25d"),
            "dealer_position_observed": False,
        },
    )


def _orderflow_modality(root: Path, symbol: str, timeframe: str) -> ModalityState:
    candidates = (
        root / "references/Stocks/output/market_context/orderflow-context.parquet",
        root / "output/market_context/orderflow-context.parquet",
    )
    path = next((item for item in candidates if item.is_file()), None)
    if path is None:
        return _unavailable("orderflow", "NO_ORDERFLOW_CONTEXT")

    try:
        frame = pd.read_parquet(path)
    except Exception:
        return _unavailable("orderflow", str(path))
    if frame.empty:
        return _unavailable("orderflow", str(path))

    work = frame.copy()
    if "symbol" in work:
        work = work.loc[work["symbol"].astype(str).str.upper() == symbol]
    if "interval" in work:
        matched = work.loc[work["interval"].astype(str).str.lower() == str(timeframe).lower()]
        if not matched.empty:
            work = matched
    if work.empty:
        return _unavailable("orderflow", str(path))
    if "timestamp_utc" in work:
        work["timestamp_utc"] = pd.to_datetime(work["timestamp_utc"], utc=True, errors="coerce")
        work = work.sort_values("timestamp_utc")
    row = work.iloc[-1].to_dict()

    score = None
    for key in ("bar_flow_score", "normalized_delta", "normalized_delta_proxy"):
        score = _finite(row.get(key))
        if score is not None:
            break

    return ModalityState(
        name="orderflow",
        score=_clip(score or 0.0),
        confidence=float(np.clip(_finite(row.get("confidence")) or 0.0, 0.0, 1.0)),
        available=True,
        training_safe=False,
        source=str(path),
        source_class=str(row.get("data_class") or "BAR_FLOW_PROXY_NOT_OBSERVED_ORDERFLOW"),
        details={
            key: row.get(key)
            for key in (
                "delta", "normalized_delta", "cvd", "delta_proxy",
                "normalized_delta_proxy", "cvd_proxy", "rvol_proxy",
                "vwap_proxy", "close_location", "flow_efficiency",
                "flow_efficiency_proxy", "classification_ratio",
                "observed_aggressor_volume", "observed_orderbook",
            )
            if key in row
        },
    )


def build_current_context_snapshot(
    project_root: str | Path,
    symbol: str,
    timeframe: str = "1h",
) -> CurrentContextSnapshot:
    root = Path(project_root).resolve()
    symbol = str(symbol).upper()
    fundamental, macro, sec = _reference_modalities(root, symbol)
    modalities = (
        _news_modality(root, symbol),
        _gex_modality(root, symbol),
        _orderflow_modality(root, symbol, timeframe),
        fundamental,
        macro,
        sec,
    )
    caps = {
        "news": 0.04,
        "gex": 0.025,
        "orderflow": 0.03,
        "fundamental": 0.025,
        "macro": 0.025,
        "sec": 0.015,
    }
    delta = sum(
        caps[item.name] * item.score * item.confidence
        for item in modalities
        if item.available
    )
    confidence_weight = sum(
        caps[item.name] * item.confidence
        for item in modalities
        if item.available
    )
    cap_weight = sum(caps[item.name] for item in modalities if item.available)
    confidence = confidence_weight / cap_weight if cap_weight > 0.0 else 0.0
    denom = sum(item.confidence for item in modalities if item.available)
    score = (
        sum(item.score * item.confidence for item in modalities if item.available) / denom
        if denom > 0.0
        else 0.0
    )
    return CurrentContextSnapshot(
        symbol=symbol,
        timeframe=str(timeframe),
        observed_at=pd.Timestamp.now(tz="UTC").isoformat(),
        score=_clip(score),
        confidence=float(np.clip(confidence, 0.0, 1.0)),
        modifier=float(np.clip(1.0 + delta, 0.85, 1.15)),
        modalities=modalities,
    )


def append_pit_context_snapshot(
    project_root: str | Path,
    snapshot: CurrentContextSnapshot,
) -> Path:
    root = Path(project_root).resolve()
    path = root / "data/agent_features/pit/context_snapshots.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)

    row: dict[str, Any] = {
        "symbol": snapshot.symbol,
        "timeframe": snapshot.timeframe,
        "observed_at": snapshot.observed_at,
        "context_score": snapshot.score,
        "context_confidence": snapshot.confidence,
        "context_modifier": snapshot.modifier,
        "execution_authority": "NONE",
    }
    for modality in snapshot.modalities:
        prefix = modality.name
        row[f"{prefix}_score"] = modality.score
        row[f"{prefix}_confidence"] = modality.confidence
        row[f"{prefix}_available"] = modality.available
        row[f"{prefix}_source_class"] = modality.source_class
        row[f"{prefix}_training_safe_at_capture"] = modality.training_safe

    new = pd.DataFrame([row])
    new["observed_at"] = pd.to_datetime(new["observed_at"], utc=True)
    if path.is_file():
        old = pd.read_parquet(path)
        old["observed_at"] = pd.to_datetime(old["observed_at"], utc=True)
        combined = pd.concat([old, new], ignore_index=True)
    else:
        combined = new
    combined = combined.sort_values("observed_at").drop_duplicates(
        subset=["symbol", "timeframe", "observed_at"],
        keep="last",
    )
    combined.to_parquet(path, index=False)
    return path
