
from datetime import date

from stocks.research.shariah_financial_verification import (
    _latest_report,
    attestation_valid,
)
from stocks.research.shariah_research_precheck import (
    business_precheck,
)


def test_future_financial_filing_is_not_available():
    reports = {
        "2026-06-30": {
            "date": "2026-06-30",
            "filing_date": "2026-08-20",
            "longTermDebt": 1,
        },
        "2026-03-31": {
            "date": "2026-03-31",
            "filing_date": "2026-05-05",
            "longTermDebt": 2,
        },
    }

    selected = _latest_report(
        reports,
        decision_date=date(
            2026,
            8,
            14,
        ),
    )

    assert selected is not None
    assert (
        selected["date"]
        == "2026-03-31"
    )


def test_expired_attestation_is_not_live_eligible():
    assert (
        attestation_valid(
            {
                "status": (
                    "SHARIAH_ELIGIBLE_PIT"
                ),
                "screened_at": (
                    "2026-01-01"
                ),
                "expires_at": (
                    "2026-08-01"
                ),
            },
            decision_date=date(
                2026,
                8,
                14,
            ),
            maximum_age_days=365,
        )
        is False
    )


def test_verified_attestation_can_pass():
    assert (
        attestation_valid(
            {
                "status": (
                    "SHARIAH_ELIGIBLE_PIT"
                ),
                "screened_at": (
                    "2026-08-01"
                ),
                "expires_at": (
                    "2026-09-01"
                ),
            },
            decision_date=date(
                2026,
                8,
                14,
            ),
            maximum_age_days=120,
        )
        is True
    )


def test_business_precheck_remains_fail_closed():
    result = business_precheck(
        sector="Financial Services",
        industry="Regional Banks",
        name="Example Bank",
    )

    assert (
        result["status"]
        == "HARD_EXCLUSION_CANDIDATE"
    )

    assert (
        result[
            "final_shariah_compliance"
        ]
        is False
    )
