
#!/usr/bin/env python3
from pathlib import Path

from stocks.research.candidate_strategy_matrix import (
    write_candidate_strategy_matrix,
)

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    matrix, opportunities, audit, path = (
        write_candidate_strategy_matrix(ROOT)
    )
    print(
        "CANDIDATE_STRATEGY_MATRIX",
        "HYDRATED_SYMBOLS",
        audit["hydrated_symbols"],
        "VALIDATED_STRATEGIES",
        audit["broadly_validated_strategies"],
        "ROWS",
        audit["matrix_rows"],
        "POSITIVE_LOCAL",
        audit["positive_local_evidence_rows"],
        "ACTIVE",
        audit["active_boundary_rows"],
        "RECENT",
        audit["recent_entry_rows"],
        "OPPORTUNITIES",
        audit["opportunity_rows"],
    )
    if not matrix.empty:
        columns = [
            "symbol",
            "strategy",
            "research_lane",
            "shariah_gate",
            "trailing_trades",
            "trailing_expectancy_bps",
            "trailing_stress_expectancy_bps",
            "trailing_profit_factor",
            "setup_state",
            "bars_since_entry",
            "local_evidence_positive",
            "applicability_score",
            "research_opportunity",
            "trade_gate",
        ]
        print(matrix[columns].head(60).to_string(index=False))
    print("OUTPUT", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
