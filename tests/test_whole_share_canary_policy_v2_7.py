
import json
from pathlib import Path


ROOT = Path(
    __file__
).resolve().parents[1]


def test_canary_is_whole_share_and_has_no_fixed_euro_cap():
    policy = json.loads(
        (
            ROOT
            / "config/"
            "final_decision_fabric_v2_7.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    canary = policy[
        "canary"
    ]

    assert (
        canary[
            "quantity_mode"
        ]
        == "WHOLE_SHARES"
    )
    assert (
        canary[
            "fractional_shares_allowed"
        ]
        is False
    )
    assert (
        canary[
            "fixed_euro_order_cap_enabled"
        ]
        is False
    )
    assert (
        canary[
            "maximum_order_eur"
        ]
        is None
    )
    assert (
        canary[
            "primary_sizing_authority"
        ]
        == (
            "RISK_AND_PORTFOLIO_WEIGHT"
        )
    )
    assert (
        canary[
            "broker_submission_enabled_by_this_layer"
        ]
        is False
    )
