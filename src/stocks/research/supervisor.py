from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from stocks.data.multitimeframe import (
    ACTIVE_SWING_TIMEFRAMES,
    load_active_swing_bundle,
    materialize_bundle,
)
from stocks.integrations import IntegrationRegistry, IntegrationRunner
from stocks.research.fast_discovery import (
    optuna_ma_search,
    vectorbt_ma_screen,
)
from stocks.research.strategy_sources import (
    export_daily_lab_dataset,
    strategy1_technical_snapshot,
    validate_combo_lab,
)


class ResearchSupervisor:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve()

        self.integrations = IntegrationRegistry.load(
            self.project_root / "config" / "integrations.yaml",
            project_root=self.project_root,
        )

        self.runner = IntegrationRunner(self.integrations)

    def _vnpy_alpha158(
        self,
        symbol: str,
        source_path: Path,
        index,
    ) -> dict[str, Any]:
        if len(index) < 300:
            return {
                "state": "SKIPPED",
                "reason": "INSUFFICIENT_ROWS",
                "rows": len(index),
            }

        train_boundary = int(len(index) * 0.60)
        valid_boundary = int(len(index) * 0.80)

        periods = {
            "train": [
                str(index[0]),
                str(index[train_boundary - 1]),
            ],
            "valid": [
                str(index[train_boundary]),
                str(index[valid_boundary - 1]),
            ],
            "test": [
                str(index[valid_boundary]),
                str(index[-1]),
            ],
        }

        response = self.runner.run(
            "vnpy",
            "alpha158",
            {
                "input_parquet": str(source_path),
                "symbol": symbol,
                "periods": periods,
                "include_label": False,
                "vwap_policy": "hlc3_proxy",
                "max_workers": 1,
            },
        )

        return response.to_dict()

    def _external_catalogs(self) -> dict[str, Any]:
        output: dict[str, Any] = {}

        for name in (
            "qlib",
            "finrl",
            "moondev",
            "nautilus",
        ):
            output[name] = self.runner.run(
                name,
                "catalog",
            ).to_dict()

        return output

    def run_cycle(
        self,
        symbols: tuple[str, ...],
        *,
        optimize: bool = False,
        external: bool = False,
        heavy: bool = False,
    ) -> dict[str, Any]:
        generated_at = datetime.now(timezone.utc)

        result: dict[str, Any] = {
            "schema": "active_swing_research_cycle_v1",
            "generated_at": generated_at.isoformat(),
            "execution_authority": "NONE",
            "symbols": {},
            "external": {},
            "heavy": {},
        }

        daily_frames = {}

        for raw_symbol in symbols:
            symbol = raw_symbol.upper().strip()

            if not symbol:
                continue

            bundle = load_active_swing_bundle(
                self.project_root,
                symbol,
            )

            symbol_result: dict[str, Any] = {
                "available_timeframes": list(
                    bundle.available_timeframes
                ),
                "derived_artifacts": {},
                "screens": {},
            }

            if bundle.frames:
                symbol_result["derived_artifacts"] = materialize_bundle(
                    self.project_root,
                    bundle,
                )

            for timeframe in ACTIVE_SWING_TIMEFRAMES:
                frame = bundle.frames.get(timeframe)

                if frame is None or len(frame) < 60:
                    continue

                screens = vectorbt_ma_screen(frame)

                symbol_result["screens"][timeframe] = [
                    row.as_dict()
                    for row in screens[:5]
                ]

            if "1d" in bundle.frames:
                daily_frames[symbol] = bundle.frames["1d"]

                symbol_result["strategy1"] = (
                    strategy1_technical_snapshot(
                        bundle.frames["1d"],
                        symbol,
                    )
                )

            optimize_frame = (
                bundle.frames.get("1h")
                if "1h" in bundle.frames
                else bundle.frames.get("1d")
            )

            if (
                optimize
                and optimize_frame is not None
                and len(optimize_frame) >= 150
            ):
                symbol_result["optuna"] = optuna_ma_search(
                    optimize_frame,
                    n_trials=40,
                )

            if external:
                source_path = bundle.source_paths.get("1h")
                one_hour = bundle.frames.get("1h")

                if (
                    source_path is not None
                    and one_hour is not None
                ):
                    symbol_result["vnpy_alpha158"] = (
                        self._vnpy_alpha158(
                            symbol,
                            source_path,
                            one_hour.index,
                        )
                    )

            result["symbols"][symbol] = symbol_result

        if external:
            result["external"]["catalogs"] = (
                self._external_catalogs()
            )

        if heavy and daily_frames:
            dataset = export_daily_lab_dataset(
                daily_frames,
                self.project_root
                / "data"
                / "research"
                / "alpha_factory"
                / "daily_universe.parquet",
            )

            result["heavy"]["combo_lab_validation"] = (
                validate_combo_lab(
                    self.project_root,
                    dataset,
                    max_symbols=len(daily_frames),
                )
            )

        output_root = (
            self.project_root
            / "artifacts"
            / "research_runtime"
            / "cycles"
        )

        output_root.mkdir(parents=True, exist_ok=True)

        timestamp = (
            generated_at
            .strftime("%Y%m%dT%H%M%SZ")
        )

        path = output_root / f"{timestamp}.json"

        path.write_text(
            json.dumps(
                result,
                indent=2,
                sort_keys=True,
                default=str,
            )
            + "\n",
            encoding="utf-8",
        )

        result["artifact"] = str(path)

        return result
