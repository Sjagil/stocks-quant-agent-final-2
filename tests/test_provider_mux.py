import pandas as pd

from stocks.data.provider_mux import (
    ProviderFrame,
    merge_provider_frames,
)


def frame(
    timestamps,
    closes,
):
    index = pd.to_datetime(
        timestamps,
        utc=True,
    )

    return pd.DataFrame(
        {
            "open": closes,
            "high": [
                value + 1
                for value
                in closes
            ],
            "low": [
                value - 1
                for value
                in closes
            ],
            "close": closes,
            "volume": [
                1000.0
                for _
                in closes
            ],
        },
        index=index,
    )


def test_mux_prefers_primary_provider() -> None:
    primary = frame(
        [
            "2026-01-01T14:30:00Z",
        ],
        [
            100.0,
        ],
    )

    fallback = frame(
        [
            "2026-01-01T14:30:00Z",
        ],
        [
            101.0,
        ],
    )

    result = merge_provider_frames(
        [
            ProviderFrame(
                "primary",
                0,
                primary,
            ),
            ProviderFrame(
                "fallback",
                1,
                fallback,
            ),
        ]
    )

    assert (
        result.frame[
            "close"
        ].iloc[0]
        == 100.0
    )

    assert (
        result.provenance[
            "source"
        ].iloc[0]
        == "primary"
    )


def test_mux_uses_fallback_for_missing_timestamp() -> None:
    primary = frame(
        [
            "2026-01-01T14:30:00Z",
        ],
        [
            100.0,
        ],
    )

    fallback = frame(
        [
            "2026-01-01T14:45:00Z",
        ],
        [
            102.0,
        ],
    )

    result = merge_provider_frames(
        [
            ProviderFrame(
                "primary",
                0,
                primary,
            ),
            ProviderFrame(
                "fallback",
                1,
                fallback,
            ),
        ]
    )

    assert len(
        result.frame
    ) == 2

    assert set(
        result.provenance[
            "source"
        ]
    ) == {
        "primary",
        "fallback",
    }


def test_mux_does_not_average_prices() -> None:
    primary = frame(
        [
            "2026-01-01T14:30:00Z",
        ],
        [
            100.0,
        ],
    )

    fallback = frame(
        [
            "2026-01-01T14:30:00Z",
        ],
        [
            110.0,
        ],
    )

    result = merge_provider_frames(
        [
            ProviderFrame(
                "primary",
                0,
                primary,
            ),
            ProviderFrame(
                "fallback",
                1,
                fallback,
            ),
        ]
    )

    assert (
        result.frame[
            "close"
        ].iloc[0]
        == 100.0
    )

    assert (
        result.frame[
            "close"
        ].iloc[0]
        != 105.0
    )

    assert (
        result.disagreement[
            "close_disagreement_bps"
        ].iloc[0]
        > 0
    )
