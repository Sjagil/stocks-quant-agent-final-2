from pathlib import Path

import pandas as pd

from stocks.research.mtf_features import (
    timeframe_state_features,
)


def test_timeframe_features_do_not_change_past_rows():
    index = pd.date_range(
        "2026-01-05 14:30",
        periods=100,
        freq="15min",
        tz="UTC",
    )

    frame = pd.DataFrame(
        {
            "open": [
                100.0 + i * 0.1
                for i in range(100)
            ],
            "high": [
                100.5 + i * 0.1
                for i in range(100)
            ],
            "low": [
                99.5 + i * 0.1
                for i in range(100)
            ],
            "close": [
                100.2 + i * 0.1
                for i in range(100)
            ],
            "volume": [
                1000.0 + i
                for i in range(100)
            ],
        },
        index=index,
    )

    first = timeframe_state_features(
        frame.iloc[:80],
        prefix="15m",
    )

    second = timeframe_state_features(
        frame,
        prefix="15m",
    ).iloc[:80]

    pd.testing.assert_frame_equal(
        first,
        second,
    )


def test_feature_columns_are_prefixed():
    index = pd.date_range(
        "2026-01-05",
        periods=30,
        freq="h",
        tz="UTC",
    )

    frame = pd.DataFrame(
        {
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.5,
            "volume": 1000.0,
        },
        index=index,
    )

    result = timeframe_state_features(
        frame,
        prefix="4h",
    )

    assert len(result.columns) >= 10

    assert all(
        column.startswith(
            "4h_"
        )
        for column in result.columns
    )


def test_duplicate_knowledge_time_keeps_latest_bar(
    monkeypatch,
):
    import pandas as pd

    from stocks.research import (
        mtf_features,
    )
    from stocks.data.timeframe_pipeline import (
        TimeframePipeline,
        TimeframeSpec,
        TimeframeView,
    )

    index = pd.DatetimeIndex(
        [
            "2026-01-02 16:30:00+00:00",
            "2026-01-02 17:30:00+00:00",
        ]
    )

    frame = pd.DataFrame(
        {
            "open": [
                100.0,
                101.0,
            ],
            "high": [
                101.0,
                102.0,
            ],
            "low": [
                99.0,
                100.0,
            ],
            "close": [
                100.5,
                101.5,
            ],
            "volume": [
                1000.0,
                1100.0,
            ],
        },
        index=index,
    )

    pipeline = TimeframePipeline(
        symbol="TEST",
        views={
            "1h": TimeframeView(
                spec=TimeframeSpec(
                    timeframe="1h",
                    role="CONFIRMATION",
                    mode="BAR",
                    source_timeframe="1h",
                ),
                frame=frame,
            )
        },
    )

    def fake_availability(
        frame,
        *,
        timeframe,
    ):
        result = frame.copy()

        result["bar_time"] = (
            result.index
        )

        result[
            "availability_time"
        ] = pd.DatetimeIndex(
            [
                "2026-01-02 18:00:00+00:00",
                "2026-01-02 18:00:00+00:00",
            ]
        )

        return result

    monkeypatch.setattr(
        mtf_features,
        "with_availability",
        fake_availability,
    )

    result = (
        mtf_features
        .decision_surface(
            pipeline
        )
    )

    assert len(result) == 1

    assert (
        result[
            "decision_bar_time"
        ].iloc[0]
        ==
        pd.Timestamp(
            "2026-01-02 17:30:00+00:00"
        )
    )

    assert (
        result[
            "decision_close"
        ].iloc[0]
        == 101.5
    )


def test_context_join_preserves_utc_timezone():
    import pandas as pd

    from stocks.data.timeframe_pipeline import (
        TimeframePipeline,
        TimeframeSpec,
        TimeframeView,
    )
    from stocks.research.mtf_features import (
        _context_for_join,
    )

    index = pd.date_range(
        "2026-01-05 14:30",
        periods=20,
        freq="15min",
        tz="UTC",
    )

    values = [
        100.0 + i * 0.1
        for i in range(
            len(index)
        )
    ]

    frame = pd.DataFrame(
        {
            "open": values,
            "high": [
                value + 0.2
                for value in values
            ],
            "low": [
                value - 0.2
                for value in values
            ],
            "close": [
                value + 0.1
                for value in values
            ],
            "volume": [
                1000.0 + i
                for i in range(
                    len(index)
                )
            ],
        },
        index=index,
    )

    pipeline = TimeframePipeline(
        symbol="TEST",
        views={
            "15m": TimeframeView(
                spec=TimeframeSpec(
                    timeframe="15m",
                    role="TACTICAL",
                    mode="BAR",
                    source_timeframe="15m",
                ),
                frame=frame,
            )
        },
    )

    result = _context_for_join(
        pipeline,
        "15m",
    )

    dtype = result[
        "15m_availability_time"
    ].dtype

    assert isinstance(
        dtype,
        pd.DatetimeTZDtype,
    )

    assert str(
        dtype.tz
    ) == "UTC"

    assert (
        str(dtype)
        ==
        "datetime64[ns, UTC]"
    )


def test_intraday_context_cannot_carry_overnight():
    import numpy as np
    import pandas as pd

    from stocks.research.mtf_features import (
        apply_context_freshness,
    )

    frame = pd.DataFrame(
        {
            "decision_time": pd.to_datetime(
                [
                    "2026-01-06 15:30:00+00:00",
                ],
                utc=True,
            ),
            "2h_source_bar_time": pd.to_datetime(
                [
                    "2026-01-05 20:45:00+00:00",
                ],
                utc=True,
            ),
            "2h_availability_time": pd.to_datetime(
                [
                    "2026-01-05 21:00:00+00:00",
                ],
                utc=True,
            ),
            "2h_age_minutes": [
                1110.0,
            ],
            "2h_ret1": [
                0.02,
            ],
        }
    )

    result = apply_context_freshness(
        frame,
        timeframe="2h",
        feature_columns=[
            "2h_ret1",
        ],
    )

    assert (
        result[
            "2h_available"
        ].iloc[0]
        == 0
    )

    assert np.isnan(
        result[
            "2h_ret1"
        ].iloc[0]
    )

    assert pd.isna(
        result[
            "2h_source_bar_time"
        ].iloc[0]
    )


def test_same_session_intraday_context_remains_available():
    import pandas as pd

    from stocks.research.mtf_features import (
        apply_context_freshness,
    )

    frame = pd.DataFrame(
        {
            "decision_time": pd.to_datetime(
                [
                    "2026-01-06 19:30:00+00:00",
                ],
                utc=True,
            ),
            "4h_source_bar_time": pd.to_datetime(
                [
                    "2026-01-06 19:15:00+00:00",
                ],
                utc=True,
            ),
            "4h_availability_time": pd.to_datetime(
                [
                    "2026-01-06 19:30:00+00:00",
                ],
                utc=True,
            ),
            "4h_age_minutes": [
                0.0,
            ],
            "4h_ret1": [
                0.01,
            ],
        }
    )

    result = apply_context_freshness(
        frame,
        timeframe="4h",
        feature_columns=[
            "4h_ret1",
        ],
    )

    assert (
        result[
            "4h_available"
        ].iloc[0]
        == 1
    )

    assert (
        result[
            "4h_ret1"
        ].iloc[0]
        == 0.01
    )
