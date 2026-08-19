from __future__ import annotations

import os

import pytest

from stocks.orchestration.whole_share_sizing import (
    compute_whole_share_quantity,
    select_risk_fraction,
    stop_distance_from_atr,
)
from stocks.research.sec_fundamentals import (
    sec_user_agent,
)


def test_sec_user_agent_requires_contact_email(
    monkeypatch,
):
    monkeypatch.delenv(
        "SEC_USER_AGENT",
        raising=False,
    )

    with pytest.raises(
        ValueError,
        match="SEC_USER_AGENT_REQUIRED",
    ):
        sec_user_agent()

    monkeypatch.setenv(
        "SEC_USER_AGENT",
        "stocks-quant-agent no-contact",
    )

    with pytest.raises(
        ValueError,
        match="SEC_USER_AGENT_CONTACT_EMAIL_REQUIRED",
    ):
        sec_user_agent()


def test_sec_user_agent_accepts_declared_contact(
    monkeypatch,
):
    monkeypatch.setenv(
        "SEC_USER_AGENT",
        "stocks-quant-agent admin@example.com",
    )

    assert (
        sec_user_agent()
        == "stocks-quant-agent admin@example.com"
    )


def test_risk_fraction_never_exceeds_hard_cap():
    value = select_risk_fraction(
        0.99,
        base=0.01,
        strong=0.02,
        threshold=0.85,
        hard_max=0.015,
    )
    assert value == pytest.approx(
        0.015
    )


def test_stop_distance_uses_larger_of_atr_or_floor():
    assert stop_distance_from_atr(
        price=100.0,
        atr=0.5,
        atr_multiple=2.0,
        minimum_stop_fraction=0.02,
    ) == pytest.approx(2.0)

    assert stop_distance_from_atr(
        price=100.0,
        atr=2.0,
        atr_multiple=2.0,
        minimum_stop_fraction=0.02,
    ) == pytest.approx(4.0)


def test_whole_share_sizing_respects_risk_cash_weight():
    result = compute_whole_share_quantity(
        net_liquidation_eur=2000.0,
        execution_capacity_eur=1800.0,
        price_eur=100.0,
        stop_distance_eur=5.0,
        risk_fraction=0.01,
        cash_floor_fraction=0.03,
        maximum_single_weight=0.35,
    )

    # risk: floor(20 / 5) = 4
    # cash: floor((1800 - 60) / 100) = 17
    # weight: floor(700 / 100) = 7
    assert result["quantity"] == 4
    assert isinstance(
        result["quantity"],
        int,
    )
    assert (
        result[
            "estimated_stop_risk_eur"
        ]
        <= 20.0
    )


def test_whole_share_sizing_has_no_fixed_euro_cap():
    result = compute_whole_share_quantity(
        net_liquidation_eur=10000.0,
        execution_capacity_eur=9000.0,
        price_eur=50.0,
        stop_distance_eur=2.0,
        risk_fraction=0.01,
        cash_floor_fraction=0.03,
        maximum_single_weight=0.35,
    )

    assert result["quantity"] == 50
    assert (
        result[
            "estimated_position_notional_eur"
        ]
        == 2500.0
    )


def test_cash_floor_can_block_minimum_whole_share():
    result = compute_whole_share_quantity(
        net_liquidation_eur=1000.0,
        execution_capacity_eur=35.0,
        price_eur=20.0,
        stop_distance_eur=2.0,
        risk_fraction=0.01,
        cash_floor_fraction=0.03,
        maximum_single_weight=0.35,
    )

    assert result["quantity"] == 0
    assert (
        result["reason"]
        == (
            "WHOLE_SHARE_MINIMUM_NOT_"
            "AFFORDABLE_OR_RISK_TOO_SMALL"
        )
    )
