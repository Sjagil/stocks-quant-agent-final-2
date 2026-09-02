from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from _common import artifact_ref, repo_catalog, run_worker

CAPABILITIES = ("health", "catalog", "forecast", "forecast_series")


def _repo(request: dict) -> Path:
    value = (request.get("context") or {}).get("repo_path")
    if not value:
        raise ValueError("Kronos repo_path missing")
    path = Path(value).resolve()
    if not path.is_dir():
        raise FileNotFoundError(path)
    return path


def _import_kronos(repo: Path):
    text = str(repo)
    if text not in sys.path:
        sys.path.insert(0, text)
    import torch
    from model import Kronos, KronosPredictor, KronosTokenizer
    return torch, Kronos, KronosPredictor, KronosTokenizer


def _device(torch, requested: str | None) -> str:
    requested = str(requested or "auto").lower()
    if requested != "auto":
        return requested
    if torch.cuda.is_available():
        return "cuda:0"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _health(request: dict) -> dict:
    repo = _repo(request)
    try:
        torch, _, _, _ = _import_kronos(repo)
        return {
            "state": "OK",
            "data": {
                "repo": str(repo),
                "model_import": True,
                "torch_version": str(torch.__version__),
                "device": _device(torch, "auto"),
                "capabilities": list(CAPABILITIES),
                "execution_authority": "NONE",
                "broker_calls": 0,
                "order_calls": 0,
            },
        }
    except Exception as exc:
        return {
            "state": "ERROR",
            "error": f"{type(exc).__name__}: {exc}",
        }


def _catalog(request: dict) -> dict:
    repo = _repo(request)
    return {
        "state": "OK",
        "data": {
            "purpose": (
                "Isolated Kronos K-line foundation-model research challenger; "
                "forecasting and causal historical forecast generation only."
            ),
            "models": {
                "mini": {
                    "model": "NeoQuasar/Kronos-mini",
                    "tokenizer": "NeoQuasar/Kronos-Tokenizer-2k",
                    "published_context": 2048,
                },
                "small": {
                    "model": "NeoQuasar/Kronos-small",
                    "tokenizer": "NeoQuasar/Kronos-Tokenizer-base",
                    "published_context": 512,
                },
                "base": {
                    "model": "NeoQuasar/Kronos-base",
                    "tokenizer": "NeoQuasar/Kronos-Tokenizer-base",
                    "published_context": 512,
                },
            },
            "repo_catalog": repo_catalog(
                repo,
                ("model/*.py", "examples/*.py", "finetune/*.py"),
            ),
            "execution_authority": "NONE",
        },
    }


def _read_bars(path: Path) -> pd.DataFrame:
    frame = pd.read_parquet(path).copy()
    if not isinstance(frame.index, pd.DatetimeIndex):
        timestamp_column = next(
            (
                column
                for column in ("timestamp_utc", "timestamp", "datetime", "date")
                if column in frame.columns
            ),
            None,
        )
        if timestamp_column is None:
            raise ValueError("bar parquet has no datetime index/column")
        frame[timestamp_column] = pd.to_datetime(
            frame[timestamp_column], utc=True, errors="coerce"
        )
        frame = frame.dropna(subset=[timestamp_column]).set_index(timestamp_column)
    else:
        frame.index = pd.to_datetime(frame.index, utc=True, errors="coerce")

    frame = frame.loc[~frame.index.isna()].sort_index()
    if frame.index.has_duplicates:
        raise ValueError("duplicate bar timestamps")
    required = ["open", "high", "low", "close"]
    missing = [column for column in required if column not in frame]
    if missing:
        raise ValueError(f"missing OHLC columns: {missing}")
    if "volume" not in frame:
        frame["volume"] = 0.0
    for column in ("open", "high", "low", "close", "volume"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["open", "high", "low", "close", "volume"])
    frame = frame.loc[
        frame["close"].gt(0)
        & frame["high"].ge(frame[["open", "close", "low"]].max(axis=1))
        & frame["low"].le(frame[["open", "close", "high"]].min(axis=1))
        & frame["volume"].ge(0)
    ]
    if frame.empty:
        raise ValueError("no valid bars remain")
    return frame


def _series(values) -> pd.Series:
    idx = pd.DatetimeIndex(values)
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    else:
        idx = idx.tz_convert("UTC")
    return pd.Series(idx)


def _load_predictor(request: dict, payload: dict):
    repo = _repo(request)
    torch, Kronos, KronosPredictor, KronosTokenizer = _import_kronos(repo)

    model_name = str(payload.get("model") or "NeoQuasar/Kronos-mini")
    tokenizer_name = str(
        payload.get("tokenizer") or "NeoQuasar/Kronos-Tokenizer-2k"
    )
    max_context = int(payload.get("max_context", 512))
    device = _device(torch, str(payload.get("device") or "auto"))

    tokenizer = KronosTokenizer.from_pretrained(tokenizer_name)
    model = Kronos.from_pretrained(model_name)
    predictor = KronosPredictor(
        model,
        tokenizer,
        device=device,
        max_context=max_context,
    )
    return predictor, device, model_name, tokenizer_name


def _forecast_stats(
    prediction: pd.DataFrame,
    *,
    decision_close: float,
) -> dict[str, float]:
    close = prediction["close"].astype(float)
    high = prediction["high"].astype(float)
    low = prediction["low"].astype(float)
    path_returns = close.pct_change().dropna()
    return {
        "kronos_terminal_return": float(
            close.iloc[-1] / decision_close - 1.0
        ),
        "kronos_mean_return": float(
            close.mean() / decision_close - 1.0
        ),
        "kronos_max_upside": float(
            high.max() / decision_close - 1.0
        ),
        "kronos_min_downside": float(
            low.min() / decision_close - 1.0
        ),
        "kronos_forecast_vol": (
            float(path_returns.std(ddof=0))
            if len(path_returns)
            else 0.0
        ),
    }


def _forecast(request: dict, artifact_dir: Path) -> dict:
    payload = dict(request.get("payload") or {})
    source = Path(str(payload["input_parquet"])).resolve()
    frame = _read_bars(source)
    predictor, device, model_name, tokenizer_name = _load_predictor(
        request, payload
    )

    lookback = int(payload.get("lookback", 256))
    pred_len = int(payload.get("pred_len", 4))
    raw_future = payload.get("future_timestamps")
    if not isinstance(raw_future, list) or len(raw_future) != pred_len:
        raise ValueError(
            "forecast requires exact future_timestamps; "
            "the worker does not fabricate exchange calendars"
        )
    future = pd.to_datetime(raw_future, utc=True, errors="raise")
    context = frame.iloc[-lookback:]
    if len(context) != lookback:
        raise ValueError("insufficient context bars")

    pred = predictor.predict(
        df=context[["open", "high", "low", "close", "volume"]],
        x_timestamp=_series(context.index),
        y_timestamp=_series(future),
        pred_len=pred_len,
        T=float(payload.get("temperature", 1.0)),
        top_k=int(payload.get("top_k", 0)),
        top_p=float(payload.get("top_p", 0.9)),
        sample_count=int(payload.get("sample_count", 1)),
        verbose=bool(payload.get("verbose", False)),
    )
    pred.index = future
    output = artifact_dir / "forecast.parquet"
    pred.to_parquet(output)

    summary = {
        "schema": "kronos_forecast_v2_15",
        "model": model_name,
        "tokenizer": tokenizer_name,
        "device": device,
        "lookback": lookback,
        "pred_len": pred_len,
        "decision_timestamp": context.index[-1].isoformat(),
        **_forecast_stats(
            pred,
            decision_close=float(context["close"].iloc[-1]),
        ),
        "research_only": True,
        "standalone_entry_authority": False,
        "execution_authority": "NONE",
    }
    summary_path = artifact_dir / "summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "state": "OK",
        "data": summary,
        "artifacts": [
            artifact_ref(output, media_type="application/x-parquet", rows=len(pred)),
            artifact_ref(summary_path, media_type="application/json"),
        ],
    }


def _forecast_series(request: dict, artifact_dir: Path) -> dict:
    payload = dict(request.get("payload") or {})
    source = Path(str(payload["input_parquet"])).resolve()
    frame = _read_bars(source)
    predictor, device, model_name, tokenizer_name = _load_predictor(
        request, payload
    )

    lookback = int(payload.get("lookback", 256))
    pred_len = int(payload.get("pred_len", 4))
    stride = int(payload.get("stride", 8))
    batch_size = int(payload.get("batch_size", 8))
    sample_count = int(payload.get("sample_count", 1))
    seed = int(payload.get("seed", 17))
    np.random.seed(seed)
    import torch
    torch.manual_seed(seed)
    temperature = float(payload.get("temperature", 1.0))
    top_k = int(payload.get("top_k", 0))
    top_p = float(payload.get("top_p", 0.9))

    if lookback < 32 or pred_len < 1 or stride < 1 or batch_size < 1:
        raise ValueError("invalid forecast-series parameters")

    last_decision = len(frame) - pred_len - 1
    decisions = list(range(lookback - 1, last_decision + 1, stride))
    if not decisions:
        raise ValueError("no historical decision windows available")

    records: list[dict[str, Any]] = []

    for batch_start in range(0, len(decisions), batch_size):
        batch_indices = decisions[batch_start : batch_start + batch_size]
        contexts = []
        x_ts = []
        y_ts = []

        for decision_index in batch_indices:
            start = decision_index - lookback + 1
            context = frame.iloc[start : decision_index + 1]
            future_index = frame.index[
                decision_index + 1 : decision_index + 1 + pred_len
            ]
            contexts.append(
                context[["open", "high", "low", "close", "volume"]]
            )
            x_ts.append(_series(context.index))
            y_ts.append(_series(future_index))

        predictions = predictor.predict_batch(
            df_list=contexts,
            x_timestamp_list=x_ts,
            y_timestamp_list=y_ts,
            pred_len=pred_len,
            T=temperature,
            top_k=top_k,
            top_p=top_p,
            sample_count=sample_count,
            verbose=False,
        )

        for decision_index, context, future_ts, prediction in zip(
            batch_indices, contexts, y_ts, predictions
        ):
            prediction.index = pd.DatetimeIndex(future_ts)
            records.append(
                {
                    "decision_index": int(decision_index),
                    "decision_timestamp": frame.index[decision_index],
                    "decision_close": float(frame["close"].iloc[decision_index]),
                    "forecast_end_timestamp": frame.index[
                        decision_index + pred_len
                    ],
                    "lookback": lookback,
                    "pred_len": pred_len,
                    **_forecast_stats(
                        prediction,
                        decision_close=float(context["close"].iloc[-1]),
                    ),
                    "model": model_name,
                    "tokenizer": tokenizer_name,
                    "device": device,
                    "causal_context_end": frame.index[decision_index],
                    "future_prices_used_as_model_input": False,
                    "future_timestamps_only": True,
                    "execution_authority": "NONE",
                }
            )

        print(
            "KRONOS_FORECAST_PROGRESS",
            min(batch_start + batch_size, len(decisions)),
            "/",
            len(decisions),
        )

    result = pd.DataFrame(records)
    output = artifact_dir / "historical_forecasts.parquet"
    result.to_parquet(output, index=False)
    summary = {
        "schema": "kronos_historical_forecast_series_v2_15",
        "rows": int(len(result)),
        "model": model_name,
        "tokenizer": tokenizer_name,
        "device": device,
        "lookback": lookback,
        "pred_len": pred_len,
        "stride": stride,
        "sample_count": sample_count,
        "seed": seed,
        "point_in_time": True,
        "future_prices_used_as_model_input": False,
        "future_timestamps_only": True,
        "standalone_entry_authority": False,
        "execution_authority": "NONE",
    }
    summary_path = artifact_dir / "summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "state": "OK",
        "data": summary,
        "artifacts": [
            artifact_ref(
                output,
                media_type="application/x-parquet",
                rows=len(result),
            ),
            artifact_ref(summary_path, media_type="application/json"),
        ],
    }


def handle(request: dict, artifact_dir: Path) -> dict:
    action = request.get("action")
    if action == "health":
        return _health(request)
    if action == "catalog":
        return _catalog(request)
    if action == "forecast":
        return _forecast(request, artifact_dir)
    if action == "forecast_series":
        return _forecast_series(request, artifact_dir)
    raise ValueError(f"unsupported Kronos action: {action}")


if __name__ == "__main__":
    run_worker(handle)
