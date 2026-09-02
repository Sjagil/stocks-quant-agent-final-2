from __future__ import annotations
import json, math, socket
from pathlib import Path
from typing import Any, Mapping
import pandas as pd

PASS_ATTESTATION_STATUS = "FINANCIAL_SCREEN_PASS_ATTESTATION_REQUIRED"

def probe_tcp(host: str, port: int, timeout_seconds: float = 0.75) -> dict[str, Any]:
    try:
        with socket.create_connection((host, int(port)), timeout=float(timeout_seconds)):
            return {"host": host, "port": int(port), "open": True, "error": None}
    except OSError as exc:
        return {"host": host, "port": int(port), "open": False, "error": f"{type(exc).__name__}: {exc}"}

def choose_open_port(configured_port: int, probes: Mapping[int, bool]) -> int | None:
    if bool(probes.get(int(configured_port), False)):
        return int(configured_port)
    for port in (7497, 7496):
        if port != int(configured_port) and bool(probes.get(port, False)):
            return port
    return None

def build_attestation_queue(verification: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "symbol","status","business_status","financial_ratio_status",
        "debt_to_market_cap","cash_to_market_cap","receivables_to_market_cap",
        "market_cap","report_date","filing_date","fundamentals_source",
        "review_status","required_evidence",
    ]
    if verification.empty:
        return pd.DataFrame(columns=columns)
    selected = verification.loc[
        verification["status"].astype(str) == PASS_ATTESTATION_STATUS
    ].copy()
    if selected.empty:
        return pd.DataFrame(columns=columns)
    keep = columns[:11]
    for col in keep:
        if col not in selected.columns:
            selected[col] = None
    selected = selected[keep]
    selected["review_status"] = "PENDING_EXTERNAL_SHARIAH_ATTESTATION"
    selected["required_evidence"] = "EXTERNAL_SHARIAH_SOURCE|METHODOLOGY|SCREENED_AT|VALID_UNTIL|EVIDENCE_URL"
    return selected.sort_values("symbol").reset_index(drop=True)

def _finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None

def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return None if not text or text.lower() == "nan" else text

def attestation_template(queue: pd.DataFrame, *, as_of: str) -> dict[str, Any]:
    rows = []
    for row in queue.to_dict(orient="records"):
        rows.append({
            "symbol": str(row.get("symbol") or "").upper(),
            "status": "PENDING_REVIEW",
            "screened_at": as_of,
            "valid_until": None,
            "source": None,
            "methodology": None,
            "evidence_url": None,
            "notes": None,
            "financial_screen_snapshot": {
                "debt_to_market_cap": _finite(row.get("debt_to_market_cap")),
                "cash_to_market_cap": _finite(row.get("cash_to_market_cap")),
                "receivables_to_market_cap": _finite(row.get("receivables_to_market_cap")),
                "report_date": _clean(row.get("report_date")),
                "filing_date": _clean(row.get("filing_date")),
                "fundamentals_source": _clean(row.get("fundamentals_source")),
            },
        })
    return {
        "schema": "shariah_attestation_review_queue_v2_10",
        "as_of": as_of,
        "trade_authority": "NONE",
        "automatic_attestation": False,
        "attestations": rows,
    }

def current_verification_row(project_root: str | Path, symbol: str) -> dict[str, Any] | None:
    root = Path(project_root).resolve()
    path = root / "artifacts/research_runtime/shariah_financial_verification/verification.csv"
    if not path.is_file():
        return None
    frame = pd.read_csv(path)
    if frame.empty or "symbol" not in frame.columns:
        return None
    match = frame.loc[frame["symbol"].astype(str).str.upper() == str(symbol).upper()]
    return None if match.empty else match.iloc[-1].to_dict()

def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    tmp.replace(path)
