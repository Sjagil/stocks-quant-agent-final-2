from __future__ import annotations

from pathlib import Path

from _common import artifact_ref, base_health, repo_catalog, require_path, run_worker

CAPABILITIES = ("health", "catalog", "alpha158")


def _health(request: dict) -> dict:
    return base_health(request, distributions=("vnpy",), imports=("vnpy", "vnpy.alpha"), capabilities=CAPABILITIES)


def _catalog(request: dict) -> dict:
    repo = (request.get("context") or {}).get("repo_path")
    return {
        "state": "OK",
        "data": {
            "repo_catalog": repo_catalog(repo, ("*model.py", "alpha_*.py", "lab.py", "*.ipynb")),
            "purpose": "VeighNa alpha factor engineering and ML challenger; never a broker authority in this project.",
        },
    }


def _alpha158(request: dict, artifact_dir: Path) -> dict:
    payload = dict(request.get("payload") or {})
    input_path = require_path(payload, "input_parquet")
    periods = payload.get("periods") or {}
    required = ("train", "valid", "test")
    if any(name not in periods for name in required):
        raise ValueError("payload.periods must contain train, valid and test [start, end] ranges")

    import polars as pl
    from vnpy.alpha.dataset.datasets.alpha_158 import Alpha158

    frame = pl.read_parquet(input_path)
    if "timestamp" not in frame.columns:
        first = frame.columns[0] if frame.columns else ""
        if first.startswith("__index"):
            frame = frame.rename({first: "timestamp"})
        elif "datetime" not in frame.columns:
            raise ValueError("input parquet must expose timestamp or datetime")
    if "timestamp" in frame.columns:
        frame = frame.rename({"timestamp": "datetime"})
    if "symbol" not in frame.columns:
        symbol = str(payload.get("symbol") or input_path.stem.split("_")[0]).upper()
        frame = frame.with_columns(pl.lit(symbol).alias("vt_symbol"))
    elif "vt_symbol" not in frame.columns:
        frame = frame.rename({"symbol": "vt_symbol"})
    if "vwap" not in frame.columns:
        policy = str(payload.get("vwap_policy") or "reject")
        if policy == "close_proxy":
            frame = frame.with_columns(pl.col("close").alias("vwap"))
        elif policy == "hlc3_proxy":
            frame = frame.with_columns(((pl.col("high") + pl.col("low") + pl.col("close")) / 3.0).alias("vwap"))
        else:
            raise ValueError("Alpha158 requires vwap; set payload.vwap_policy to close_proxy or hlc3_proxy explicitly")

    def period(name: str) -> tuple[str, str]:
        value = periods[name]
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            raise ValueError(f"periods.{name} must be [start, end]")
        return str(value[0]), str(value[1])

    parsed_periods = {name: period(name) for name in required}
    import pandas as pd

    def utc_timestamp(value: str) -> pd.Timestamp:
        timestamp = pd.Timestamp(value)
        return timestamp.tz_localize("UTC") if timestamp.tzinfo is None else timestamp.tz_convert("UTC")

    boundaries = {
        name: (utc_timestamp(values[0]), utc_timestamp(values[1]))
        for name, values in parsed_periods.items()
    }
    for name, (start, end) in boundaries.items():
        if end < start:
            raise ValueError(f"periods.{name} end precedes start")
    if not (boundaries["train"][1] < boundaries["valid"][0] <= boundaries["valid"][1] < boundaries["test"][0]):
        raise ValueError("train/valid/test periods must be strictly chronological and non-overlapping")

    dataset = Alpha158(frame, parsed_periods["train"], parsed_periods["valid"], parsed_periods["test"])
    dataset.prepare_data(max_workers=payload.get("max_workers"))
    result_df = dataset.raw_df
    include_label = bool(payload.get("include_label", False))
    if not include_label and "label" in result_df.columns:
        result_df = result_df.drop("label")
    output = artifact_dir / "vnpy_alpha158.parquet"
    result_df.write_parquet(output)
    identifier_columns = {"datetime", "vt_symbol", "label"}
    feature_count = sum(column not in identifier_columns for column in result_df.columns)
    warnings = []
    if include_label:
        warnings.append(
            "Alpha158's upstream label is forward-looking; purge/embargo at train/validation/test boundaries is mandatory before model fitting."
        )
    return {
        "state": "OK",
        "data": {
            "rows": result_df.height,
            "columns": result_df.width,
            "feature_count": feature_count,
            "include_label": include_label,
            "label_lookahead_policy": "explicit_only; boundary purge required when included",
            "vwap_policy": payload.get("vwap_policy", "reject"),
            "periods": parsed_periods,
        },
        "warnings": warnings,
        "artifacts": [artifact_ref(output, media_type="application/vnd.apache.parquet", rows=result_df.height)],
    }


def handle(request: dict, artifact_dir: Path) -> dict:
    repo = (request.get("context") or {}).get("repo_path")
    action = request["action"]
    if action == "health":
        return _health(request)
    if action == "catalog":
        return _catalog(request)
    if action == "alpha158":
        return _alpha158(request, artifact_dir)
    raise ValueError(f"unsupported vnpy action: {action}")


if __name__ == "__main__":
    run_worker(handle)
