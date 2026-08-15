
from __future__ import annotations

from typing import Any


HARD_EXCLUSION_TERMS = (
    "casino",
    "gambling",
    "sports betting",
    "sportsbook",
    "tobacco",
    "cigarette",
    "brewery",
    "breweries",
    "distillery",
    "distilleries",
    "alcoholic beverages",
    "cannabis",
    "marijuana",
    "commercial bank",
    "regional bank",
    "diversified bank",
    "mortgage finance",
    "consumer finance",
    "life insurance",
    "property & casualty insurance",
    "property and casualty insurance",
    "reinsurance",
)

REVIEW_TERMS = (
    "financial services",
    "credit services",
    "capital markets",
    "asset management",
    "insurance",
    "banking",
)


def business_precheck(
    *,
    sector: Any,
    industry: Any,
    name: Any = None,
) -> dict[str, Any]:
    text = " | ".join(
        str(value or "").strip().lower()
        for value in (sector, industry, name)
    )

    hard = sorted(
        {term for term in HARD_EXCLUSION_TERMS if term in text}
    )
    review = sorted(
        {term for term in REVIEW_TERMS if term in text}
    )

    if hard:
        status = "HARD_EXCLUSION_CANDIDATE"
    elif review:
        status = "MANUAL_REVIEW_REQUIRED"
    else:
        status = "NO_BUSINESS_EXCLUSION_FOUND"

    return {
        "status": status,
        "hard_matches": hard,
        "review_matches": review,
        "final_shariah_compliance": False,
        "financial_ratio_screen_required": True,
        "manual_verification_required": True,
        "execution_authority": "NONE",
    }
