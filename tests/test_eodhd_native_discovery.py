
from stocks.research.eodhd_native_discovery import (
    NativeScreenerQuery,
    merge_native_rows,
    parse_screener_rows,
    score_native_row,
)


def test_screener_payload_data_is_parsed():
    payload = {
        "data": [
            {
                "code": "XYZ",
                "market_capitalization": 2_000_000_000,
                "adjusted_close": 20,
                "avgvol_200d": 1_000_000,
                "refund_1d_p": 2.5,
                "refund_5d_p": 8.0,
                "earnings_share": 1.5,
            }
        ]
    }
    rows = parse_screener_rows(payload)
    assert len(rows) == 1
    assert rows[0]["code"] == "XYZ"


def test_native_candidate_is_research_only_pending_shariah():
    query = NativeScreenerQuery(
        name="TEST",
        research_lane="GEM",
        sort="refund_5d_p.desc",
        filters=(),
        mover_type="POSITIVE_MOMENTUM",
    )
    row = score_native_row(
        {
            "code": "XYZ",
            "market_capitalization": 2_000_000_000,
            "adjusted_close": 20,
            "avgvol_200d": 1_000_000,
            "refund_1d_p": 2.5,
            "refund_5d_p": 8.0,
            "earnings_share": 1.5,
        },
        query=query,
    )
    assert row is not None
    assert row["research_eligible"] is True
    assert row["trade_eligible"] is False
    assert row["shariah_gate"] == "PENDING"
    assert row["execution_authority"] == "NONE"


def test_duplicate_symbol_uses_highest_research_score():
    weak = NativeScreenerQuery(
        name="TACTICAL_PULLBACK",
        research_lane="TACTICAL",
        sort="refund_1d_p.asc",
        filters=(),
        mover_type="PULLBACK",
    )
    strong = NativeScreenerQuery(
        name="CORE_MOMENTUM",
        research_lane="CORE",
        sort="refund_5d_p.desc",
        filters=(),
        mover_type="CORE_MOMENTUM",
    )
    base = {
        "code": "XYZ",
        "market_capitalization": 30_000_000_000,
        "adjusted_close": 100,
        "avgvol_200d": 2_000_000,
        "earnings_share": 5.0,
    }
    rows = merge_native_rows(
        [
            (weak, {**base, "refund_1d_p": -3.0, "refund_5d_p": -5.0}),
            (strong, {**base, "refund_1d_p": 2.0, "refund_5d_p": 10.0}),
        ],
        maximum_candidates=10,
    )
    assert len(rows) == 1
    assert rows[0]["symbol"] == "XYZ"
    assert rows[0]["native_query"] == "CORE_MOMENTUM"
