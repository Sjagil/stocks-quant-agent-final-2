from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pandas as pd

from _common import artifact_ref, run_worker


CAPABILITIES = (
    "health",
    "catalog",
    "prepare_replay",
    "replay_intents",
)

ALGORITHM_SOURCE = 'using System;\nusing System.Collections.Generic;\nusing System.Globalization;\nusing System.IO;\nusing QuantConnect;\nusing QuantConnect.Algorithm;\nusing QuantConnect.Data;\nusing QuantConnect.Data.Subscription;\nusing QuantConnect.Orders;\n\npublic sealed class CanonicalReplayPointV2177 : BaseData\n{\n    public bool ExecuteEntry { get; set; }\n    public bool ExecuteExit { get; set; }\n\n    public override SubscriptionDataSource GetSource(\n        SubscriptionDataConfig config,\n        DateTime date,\n        bool isLiveMode)\n    {\n        var root = Environment.GetEnvironmentVariable(\n            "LEAN_CANONICAL_REPLAY_DIR");\n        if (string.IsNullOrWhiteSpace(root))\n        {\n            throw new InvalidOperationException(\n                "LEAN_CANONICAL_REPLAY_DIR missing");\n        }\n\n        var file = Path.Combine(\n            root,\n            config.Symbol.Value + ".csv");\n\n        return new SubscriptionDataSource(\n            file,\n            SubscriptionTransportMedium.LocalFile,\n            FileFormat.Csv);\n    }\n\n    public override BaseData Reader(\n        SubscriptionDataConfig config,\n        string line,\n        DateTime date,\n        bool isLiveMode)\n    {\n        if (string.IsNullOrWhiteSpace(line)\n            || line.StartsWith("timestamp,", StringComparison.Ordinal))\n        {\n            return null;\n        }\n\n        var parts = line.Split(\',\');\n        if (parts.Length < 4)\n        {\n            return null;\n        }\n\n        var timestamp = DateTime.Parse(\n            parts[0],\n            CultureInfo.InvariantCulture,\n            DateTimeStyles.AssumeUniversal\n                | DateTimeStyles.AdjustToUniversal);\n\n        var open = decimal.Parse(\n            parts[1],\n            NumberStyles.Float,\n            CultureInfo.InvariantCulture);\n\n        var entry = parts[2] == "1";\n        var exit = parts[3] == "1";\n\n        return new CanonicalReplayPointV2177\n        {\n            Symbol = config.Symbol,\n            Time = DateTime.SpecifyKind(\n                timestamp,\n                DateTimeKind.Utc),\n            Value = open,\n            ExecuteEntry = entry,\n            ExecuteExit = exit,\n        };\n    }\n\n    public override bool IsSparseData()\n    {\n        return false;\n    }\n}\n\n\npublic class CrossEngineReplayAlgorithmV2177 : QCAlgorithm\n{\n    private readonly Dictionary<Symbol, string> _names = new();\n    private string _fillsPath;\n\n    public override void Initialize()\n    {\n        SetTimeZone(TimeZones.Utc);\n        SetCash(1000000);\n        SetBenchmark(_ => 0m);\n\n        var symbolsRaw = Environment.GetEnvironmentVariable(\n            "LEAN_CANONICAL_REPLAY_SYMBOLS");\n        var startRaw = Environment.GetEnvironmentVariable(\n            "LEAN_CANONICAL_REPLAY_START");\n        var endRaw = Environment.GetEnvironmentVariable(\n            "LEAN_CANONICAL_REPLAY_END");\n        _fillsPath = Environment.GetEnvironmentVariable(\n            "LEAN_CANONICAL_REPLAY_FILLS");\n\n        if (string.IsNullOrWhiteSpace(symbolsRaw)\n            || string.IsNullOrWhiteSpace(startRaw)\n            || string.IsNullOrWhiteSpace(endRaw)\n            || string.IsNullOrWhiteSpace(_fillsPath))\n        {\n            throw new InvalidOperationException(\n                "canonical replay environment incomplete");\n        }\n\n        var start = DateTime.Parse(\n            startRaw,\n            CultureInfo.InvariantCulture,\n            DateTimeStyles.AssumeUniversal\n                | DateTimeStyles.AdjustToUniversal);\n        var end = DateTime.Parse(\n            endRaw,\n            CultureInfo.InvariantCulture,\n            DateTimeStyles.AssumeUniversal\n                | DateTimeStyles.AdjustToUniversal);\n\n        SetStartDate(start.Year, start.Month, start.Day);\n        SetEndDate(end.Year, end.Month, end.Day);\n\n        Directory.CreateDirectory(\n            Path.GetDirectoryName(_fillsPath));\n        File.WriteAllText(\n            _fillsPath,\n            "replay_symbol,timestamp,side,fill_price,quantity\\n");\n\n        foreach (\n            var raw\n            in symbolsRaw.Split(\n                \',\',\n                StringSplitOptions.RemoveEmptyEntries))\n        {\n            var ticker = raw.Trim();\n            var security = AddData<CanonicalReplayPointV2177>(\n                ticker,\n                Resolution.Hour,\n                TimeZones.Utc,\n                fillForward: false,\n                leverage: 1m);\n\n            _names[security.Symbol] = ticker;\n        }\n    }\n\n    public override void OnData(Slice data)\n    {\n        foreach (var pair in _names)\n        {\n            var point = data.Get<CanonicalReplayPointV2177>(\n                pair.Key);\n            if (point == null)\n            {\n                continue;\n            }\n\n            var holdings = Portfolio[pair.Key].Quantity;\n\n            if (point.ExecuteExit && holdings > 0)\n            {\n                MarketOrder(\n                    pair.Key,\n                    -1,\n                    asynchronous: false,\n                    tag: "XENGINE_EXIT");\n            }\n            else if (point.ExecuteEntry && holdings == 0)\n            {\n                MarketOrder(\n                    pair.Key,\n                    1,\n                    asynchronous: false,\n                    tag: "XENGINE_ENTRY");\n            }\n        }\n    }\n\n    public override void OnOrderEvent(OrderEvent orderEvent)\n    {\n        if (orderEvent.Status != OrderStatus.Filled)\n        {\n            return;\n        }\n\n        if (!_names.TryGetValue(\n            orderEvent.Symbol,\n            out var replaySymbol))\n        {\n            return;\n        }\n\n        var side = (\n            orderEvent.FillQuantity > 0\n                ? "BUY"\n                : "SELL");\n\n        var line = string.Join(\n            ",",\n            replaySymbol,\n            orderEvent.UtcTime.ToString(\n                "O",\n                CultureInfo.InvariantCulture),\n            side,\n            orderEvent.FillPrice.ToString(\n                CultureInfo.InvariantCulture),\n            Math.Abs(orderEvent.FillQuantity).ToString(\n                CultureInfo.InvariantCulture));\n\n        File.AppendAllText(\n            _fillsPath,\n            line + "\\n");\n    }\n}\n'


def _repo(request: dict) -> Path:
    value = (
        request.get("context") or {}
    ).get("repo_path")
    return (
        Path(str(value)).resolve()
        if value
        else Path("__missing__")
    )


def _runtime(repo: Path) -> dict:
    docker = shutil.which("docker")
    dotnet = shutil.which("dotnet")

    local_cli = (
        repo.parent.parent
        / ".venvs/lean-cli/bin/lean"
    )
    lean_cli = (
        str(local_cli)
        if local_cli.is_file()
        else shutil.which("lean")
    )

    launcher_candidates = list(
        (repo / "Launcher/bin/Release").glob(
            "**/QuantConnect.Lean.Launcher.dll"
        )
    )
    launcher = (
        launcher_candidates[0]
        if launcher_candidates
        else None
    )

    docker_ready = False
    if docker:
        try:
            result = subprocess.run(
                [docker, "info"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            docker_ready = result.returncode == 0
        except Exception:
            docker_ready = False

    return {
        "lean_cli": lean_cli,
        "docker": docker,
        "docker_ready": docker_ready,
        "dotnet": dotnet,
        "launcher": (
            str(launcher)
            if launcher
            else None
        ),
        "full_cli_candidate": bool(
            lean_cli and docker_ready
        ),
        "local_launcher_candidate": bool(
            dotnet and launcher
        ),
    }


def _health(request: dict) -> dict:
    repo = _repo(request)
    runtime = _runtime(repo)
    full_candidate = bool(
        runtime["full_cli_candidate"]
        or runtime["local_launcher_candidate"]
    )
    return {
        "state": (
            "OK"
            if repo.is_dir()
            else "DEGRADED"
        ),
        "data": {
            "repo": str(repo),
            "repo_exists": repo.is_dir(),
            "runtime": runtime,
            "capabilities": list(CAPABILITIES),
            "full_engine_replay_candidate":
                full_candidate,
            "canonical_data_adapter":
                "LOCAL_CUSTOM_BASEDATA_V2_17_7",
            "broker_calls": 0,
            "order_calls": 0,
            "execution_authority": "NONE",
        },
        "warnings": (
            []
            if full_candidate
            else [
                "LEAN full backtest runtime unavailable"
            ]
        ),
    }


def _catalog(request: dict) -> dict:
    repo = _repo(request)
    return {
        "state": (
            "OK"
            if repo.is_dir()
            else "DEGRADED"
        ),
        "data": {
            "repo": str(repo),
            "capabilities": list(CAPABILITIES),
            "adapter":
                "CUSTOM_BASEDATA_EXECUTION_INTENT_REPLAY",
            "source_harness_only_does_not_validate": True,
            "execution_authority": "NONE",
        },
    }


def _prepare(request: dict, artifact_dir: Path) -> dict:
    payload = dict(
        request.get("payload") or {}
    )
    source = Path(
        str(payload["schedule_parquet"])
    ).resolve()
    if not source.is_file():
        raise FileNotFoundError(source)

    contract = {
        "schema": "lean_replay_contract_v2_17_7",
        "schedule_parquet": str(source),
        "execution_contract": "NEXT_OPEN_REPLAY",
        "adapter":
            "LOCAL_CUSTOM_BASEDATA_EXECUTION_INTENT_REPLAY",
        "signals_shifted_rows": 1,
        "quantity": 1,
        "whole_shares_only": True,
        "cross_engine_reselection": False,
        "broker_calls": 0,
        "order_calls": 0,
        "execution_authority": "NONE",
    }
    path = artifact_dir / "lean_replay_contract.json"
    path.write_text(
        json.dumps(
            contract,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "state": "OK",
        "data": contract,
        "artifacts": [
            artifact_ref(
                path,
                media_type="application/json",
            ),
        ],
    }


def _execution_frame(
    schedule: pd.DataFrame,
) -> pd.DataFrame:
    frames = []
    for symbol, group in schedule.groupby(
        "symbol",
        sort=True,
    ):
        work = group.copy()
        work["date"] = pd.to_datetime(
            work["date"],
            utc=True,
            errors="coerce",
        )
        work = (
            work.dropna(
                subset=["date", "open"]
            )
            .sort_values("date")
            .drop_duplicates(
                "date",
                keep="last",
            )
            .reset_index(drop=True)
        )
        work["execute_entry"] = (
            pd.to_numeric(
                work["scheduled_entry"],
                errors="coerce",
            )
            .fillna(0)
            .shift(1)
            .fillna(0)
            .astype(int)
        )
        work["execute_exit"] = (
            pd.to_numeric(
                work["scheduled_exit"],
                errors="coerce",
            )
            .fillna(0)
            .shift(1)
            .fillna(0)
            .astype(int)
        )
        work["symbol"] = str(symbol).upper()
        frames.append(
            work[
                [
                    "symbol",
                    "date",
                    "open",
                    "execute_entry",
                    "execute_exit",
                ]
            ]
        )

    if not frames:
        raise ValueError(
            "zero LEAN execution rows"
        )

    return pd.concat(
        frames,
        ignore_index=True,
    )


def _patch_json_value(
    text: str,
    key: str,
    value_json: str,
) -> str:
    pattern = (
        r'("' + re.escape(key)
        + r'"\s*:\s*)'
        + r'(?:"(?:\\.|[^"])*"|true|false|-?\d+(?:\.\d+)?)'
    )
    updated, count = re.subn(
        pattern,
        lambda match:
            match.group(1) + value_json,
        text,
        count=1,
    )
    if count != 1:
        raise ValueError(
            f"LEAN config key not found: {key}"
        )
    return updated


def _normalize_lean_fills(
    path: Path,
) -> pd.DataFrame:
    columns = [
        "replay_symbol",
        "entry_time",
        "exit_time",
        "entry_price",
        "exit_price",
        "quantity",
    ]
    if (
        not path.is_file()
        or path.stat().st_size == 0
    ):
        return pd.DataFrame(columns=columns)

    fills = pd.read_csv(path)
    if fills.empty:
        return pd.DataFrame(columns=columns)

    fills["timestamp"] = pd.to_datetime(
        fills["timestamp"],
        utc=True,
        errors="coerce",
    )
    fills["fill_price"] = pd.to_numeric(
        fills["fill_price"],
        errors="coerce",
    )
    fills["quantity"] = pd.to_numeric(
        fills["quantity"],
        errors="coerce",
    )
    fills = fills.dropna(
        subset=[
            "replay_symbol",
            "timestamp",
            "side",
            "fill_price",
            "quantity",
        ]
    ).copy()
    fills["replay_symbol"] = (
        fills["replay_symbol"]
        .astype(str)
        .str.upper()
    )
    fills["side"] = (
        fills["side"]
        .astype(str)
        .str.upper()
    )

    rows = []
    for symbol, group in fills.groupby(
        "replay_symbol",
        sort=True,
    ):
        opened = None
        for row in group.sort_values(
            "timestamp"
        ).itertuples(index=False):
            if row.side == "BUY":
                if opened is not None:
                    raise ValueError(
                        f"{symbol}: overlapping LEAN entry"
                    )
                opened = row
                continue

            if row.side != "SELL":
                continue
            if opened is None:
                raise ValueError(
                    f"{symbol}: LEAN exit without entry"
                )

            entry_qty = float(opened.quantity)
            exit_qty = float(row.quantity)
            if (
                abs(entry_qty - exit_qty)
                > 1e-12
            ):
                raise ValueError(
                    f"{symbol}: LEAN quantity mismatch "
                    f"{entry_qty} != {exit_qty}"
                )
            if (
                entry_qty <= 0
                or abs(
                    entry_qty - round(entry_qty)
                ) > 1e-12
            ):
                raise ValueError(
                    f"{symbol}: fractional LEAN quantity"
                )

            rows.append(
                {
                    "replay_symbol": symbol,
                    "entry_time": opened.timestamp,
                    "exit_time": row.timestamp,
                    "entry_price":
                        float(opened.fill_price),
                    "exit_price":
                        float(row.fill_price),
                    "quantity":
                        int(round(entry_qty)),
                }
            )
            opened = None

        if opened is not None:
            raise ValueError(
                f"{symbol}: open LEAN position remains"
            )

    return pd.DataFrame(
        rows,
        columns=columns,
    )


def _replay(request: dict, artifact_dir: Path) -> dict:
    repo = _repo(request)
    runtime = _runtime(repo)
    payload = dict(
        request.get("payload") or {}
    )

    source = Path(
        str(payload["schedule_parquet"])
    ).resolve()
    if not source.is_file():
        raise FileNotFoundError(source)

    dotnet = runtime.get("dotnet")
    launcher = runtime.get("launcher")
    if not dotnet or not launcher:
        return {
            "state": "DEGRADED",
            "data": {
                "engine": "lean",
                "mode":
                    "BLOCKED_FULL_ENGINE_REPLAY",
                "reason":
                    "LEAN_LOCAL_LAUNCHER_UNAVAILABLE",
                "parity": False,
                "execution_authority": "NONE",
            },
            "warnings": [
                "LEAN_LOCAL_LAUNCHER_UNAVAILABLE"
            ],
        }

    schedule = pd.read_parquet(source)
    execution = _execution_frame(schedule)

    data_root = artifact_dir / "canonical_data"
    data_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    symbols = []
    for symbol, group in execution.groupby(
        "symbol",
        sort=True,
    ):
        symbol = str(symbol).upper()
        symbols.append(symbol)
        target = data_root / f"{symbol}.csv"
        out = group.copy()
        out["timestamp"] = (
            pd.to_datetime(
                out["date"],
                utc=True,
            )
            .map(lambda value: value.isoformat())
        )
        out[
            [
                "timestamp",
                "open",
                "execute_entry",
                "execute_exit",
            ]
        ].to_csv(
            target,
            index=False,
        )

    execution_path = (
        artifact_dir / "execution_intents.parquet"
    )
    execution.to_parquet(
        execution_path,
        index=False,
    )

    start = pd.to_datetime(
        execution["date"],
        utc=True,
    ).min()
    end = pd.to_datetime(
        execution["date"],
        utc=True,
    ).max()

    source_file = (
        repo
        / "Algorithm.CSharp/"
        "CrossEngineReplayAlgorithmV2177.cs"
    )
    source_existed = source_file.exists()
    source_backup = (
        source_file.read_bytes()
        if source_existed
        else None
    )

    launcher_path = Path(str(launcher)).resolve()
    launcher_dir = launcher_path.parent
    runtime_config = launcher_dir / "config.json"
    source_config = repo / "Launcher/config.json"

    runtime_config_existed = (
        runtime_config.exists()
    )
    runtime_config_backup = (
        runtime_config.read_bytes()
        if runtime_config_existed
        else None
    )

    build_stdout = artifact_dir / "lean_build_stdout.txt"
    build_stderr = artifact_dir / "lean_build_stderr.txt"
    run_stdout = artifact_dir / "lean_run_stdout.txt"
    run_stderr = artifact_dir / "lean_run_stderr.txt"
    raw_fills = artifact_dir / "lean_raw_fills.csv"

    try:
        source_file.write_text(
            ALGORITHM_SOURCE,
            encoding="utf-8",
        )

        build = subprocess.run(
            [
                dotnet,
                "build",
                str(
                    repo
                    / "Launcher/"
                    "QuantConnect.Lean.Launcher.csproj"
                ),
                "-c",
                "Release",
                "--nologo",
            ],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=1200,
        )
        build_stdout.write_text(
            build.stdout,
            encoding="utf-8",
        )
        build_stderr.write_text(
            build.stderr,
            encoding="utf-8",
        )
        if build.returncode != 0:
            raise RuntimeError(
                "LEAN_BUILD_FAILED:"
                + build.stderr[-4000:]
            )

        if not runtime_config.exists():
            if not source_config.exists():
                raise FileNotFoundError(
                    source_config
                )
            shutil.copy2(
                source_config,
                runtime_config,
            )

        config_text = runtime_config.read_text(
            encoding="utf-8"
        )
        config_text = _patch_json_value(
            config_text,
            "environment",
            json.dumps("backtesting"),
        )
        config_text = _patch_json_value(
            config_text,
            "algorithm-type-name",
            json.dumps(
                "CrossEngineReplayAlgorithmV2177"
            ),
        )
        config_text = _patch_json_value(
            config_text,
            "algorithm-language",
            json.dumps("CSharp"),
        )
        algorithm_dll = (
            launcher_dir
            / "QuantConnect.Algorithm.CSharp.dll"
        )
        if not algorithm_dll.is_file():
            raise FileNotFoundError(
                algorithm_dll
            )

        config_text = _patch_json_value(
            config_text,
            "algorithm-location",
            json.dumps(str(algorithm_dll)),
        )
        config_text = _patch_json_value(
            config_text,
            "data-folder",
            json.dumps(
                str((repo / "Data").resolve())
            ),
        )
        config_text = _patch_json_value(
            config_text,
            "force-exchange-always-open",
            "true",
        )
        runtime_config.write_text(
            config_text,
            encoding="utf-8",
        )

        env = os.environ.copy()
        env.update(
            {
                "LEAN_CANONICAL_REPLAY_DIR":
                    str(data_root.resolve()),
                "LEAN_CANONICAL_REPLAY_SYMBOLS":
                    ",".join(symbols),
                "LEAN_CANONICAL_REPLAY_START":
                    start.isoformat(),
                "LEAN_CANONICAL_REPLAY_END":
                    end.isoformat(),
                "LEAN_CANONICAL_REPLAY_FILLS":
                    str(raw_fills.resolve()),
            }
        )

        completed = subprocess.run(
            [
                dotnet,
                str(launcher_path),
            ],
            cwd=launcher_dir,
            env=env,
            capture_output=True,
            text=True,
            timeout=1200,
        )
        run_stdout.write_text(
            completed.stdout,
            encoding="utf-8",
        )
        run_stderr.write_text(
            completed.stderr,
            encoding="utf-8",
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "LEAN_LAUNCHER_FAILED:"
                + completed.stdout[-3000:]
                + completed.stderr[-3000:]
            )

        normalized = _normalize_lean_fills(
            raw_fills
        )
        if normalized.empty:
            raise RuntimeError(
                "LEAN_FULL_ENGINE_REPLAY_ZERO_TRADES"
            )

        normalized_path = (
            artifact_dir
            / "normalized_ledger.parquet"
        )
        normalized.to_parquet(
            normalized_path,
            index=False,
        )

        summary = {
            "schema":
                "lean_intent_replay_v2_17_7",
            "engine": "lean",
            "mode": "FULL_ENGINE_REPLAY",
            "adapter":
                "LOCAL_LAUNCHER_CUSTOM_BASEDATA",
            "execution_semantics":
                "SCHEDULE_DERIVED_EXECUTION_INTENT_AT_OPEN",
            "signals_shifted_rows": 1,
            "runtime":
                "QuantConnect.Lean.Launcher",
            "algorithm_type":
                "CrossEngineReplayAlgorithmV2177",
            "symbols": len(symbols),
            "trades": int(len(normalized)),
            "whole_shares_only": True,
            "fractional_shares_allowed": False,
            "cross_engine_reselection": False,
            "broker_calls": 0,
            "order_calls": 0,
            "execution_authority": "NONE",
        }
        summary_path = (
            artifact_dir / "summary.json"
        )
        summary_path.write_text(
            json.dumps(
                summary,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        artifacts = [
            artifact_ref(
                normalized_path,
                media_type="application/x-parquet",
            ),
            artifact_ref(
                execution_path,
                media_type="application/x-parquet",
            ),
            artifact_ref(
                raw_fills,
                media_type="text/csv",
            ),
            artifact_ref(
                build_stdout,
                media_type="text/plain",
            ),
            artifact_ref(
                build_stderr,
                media_type="text/plain",
            ),
            artifact_ref(
                run_stdout,
                media_type="text/plain",
            ),
            artifact_ref(
                run_stderr,
                media_type="text/plain",
            ),
            artifact_ref(
                summary_path,
                media_type="application/json",
            ),
        ]

        return {
            "state": "OK",
            "data": summary,
            "artifacts": artifacts,
        }
    finally:
        if source_existed:
            source_file.write_bytes(
                source_backup
            )
        else:
            source_file.unlink(
                missing_ok=True
            )

        if runtime_config_existed:
            runtime_config.write_bytes(
                runtime_config_backup
            )
        else:
            runtime_config.unlink(
                missing_ok=True
            )


def handle(request: dict, artifact_dir: Path) -> dict:
    action = request["action"]
    if action == "health":
        return _health(request)
    if action == "catalog":
        return _catalog(request)
    if action == "prepare_replay":
        return _prepare(
            request,
            artifact_dir,
        )
    if action == "replay_intents":
        return _replay(
            request,
            artifact_dir,
        )
    raise ValueError(
        f"unsupported Lean v2.17.7 action: {action}"
    )


if __name__ == "__main__":
    run_worker(handle)
