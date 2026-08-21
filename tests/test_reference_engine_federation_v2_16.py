from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from stocks.integrations.reference_federation import (
    EXPECTED_ENGINES,
    audit_reference_federation,
)
from stocks.research.kronos_dynamic_generalization_v2_16 import (
    aggregate_generalization,
)


ROOT = Path(__file__).resolve().parents[1]


def _config():
    return yaml.safe_load(
        (
            ROOT / "config/reference_engine_federation_v2_16.yaml"
        ).read_text(encoding="utf-8")
    )


def test_all_reference_repositories_are_declared():
    payload = _config()
    assert set(payload["engines"]) == EXPECTED_ENGINES


def test_federation_has_one_internal_writer_and_whole_share_policy():
    payload = _config()
    policy = payload["global_policy"]
    assert policy["canonical_broker_writer"] == (
        "stocks.live.service.live_submit_authorized"
    )
    assert policy["whole_shares_only"] is True
    assert policy["fractional_shares_allowed"] is False
    assert policy["fixed_euro_order_cap"] is False
    final_stage = next(
        stage
        for stage in payload["pipeline"]
        if stage["stage"] == "canonical_execution"
    )
    assert final_stage["internal_component"] == policy["canonical_broker_writer"]
    assert "engines" not in final_stage


def test_optuna_cannot_see_test_or_holdout_objective():
    payload = _config()
    policy = payload["optimization_policy"]
    assert policy["optuna_allowed_segments"] == ["train", "valid"]
    assert {"test", "holdout", "live"}.issubset(
        set(policy["optuna_forbidden_segments"])
    )


def test_external_reference_engines_have_no_execution_authority():
    audit = audit_reference_federation(ROOT)
    assert audit.invalid_authority_engines == ()
    assert audit.direct_writer_violations == ()


def test_moondev_and_vectorbt_cannot_promote_or_execute():
    payload = _config()
    moondev = payload["engines"]["MoonDev-Trading-Ai-Agents"]
    vectorbt = payload["engines"]["vectorbt"]
    assert "numerical_truth_source" in moondev["forbidden"]
    assert "risk_authority" in moondev["forbidden"]
    assert "finalist_promotion_by_itself" in vectorbt["forbidden"]


def test_vnpy_ib_is_shadow_only():
    payload = _config()
    spec = payload["engines"]["vnpy_ib"]
    assert "send_order" in spec["forbidden"]
    assert "cancel_order" in spec["forbidden"]
    assert "read_only_broker" in spec["allowed_modes"]


def test_generalization_requires_multiple_usable_folds_and_symbols():
    rows = []
    for symbol, exp, stress in (
        ("A", 20.0, 10.0),
        ("B", 15.0, 5.0),
        ("C", 5.0, 1.0),
    ):
        rows.append(
            {
                "symbol": symbol,
                "hypothesis_id": "frozen",
                "evaluated_test_folds": 2,
                "total_test_trades": 25,
                "median_test_expectancy_bps": exp,
                "median_stress_test_expectancy_bps": stress,
            }
        )
    summary = aggregate_generalization(pd.DataFrame(rows))
    assert summary.iloc[0]["status"] == "DYNAMIC_UNIVERSE_VALIDATED"
    assert summary.iloc[0]["execution_authority"] == "NONE"


def test_generalization_rejects_one_fold_evidence():
    rows = [
        {
            "symbol": symbol,
            "hypothesis_id": "weak",
            "evaluated_test_folds": 1,
            "total_test_trades": 100,
            "median_test_expectancy_bps": 100.0,
            "median_stress_test_expectancy_bps": 90.0,
        }
        for symbol in ("A", "B", "C", "D")
    ]
    summary = aggregate_generalization(pd.DataFrame(rows))
    assert summary.iloc[0]["status"] == "NOT_EVALUABLE"
