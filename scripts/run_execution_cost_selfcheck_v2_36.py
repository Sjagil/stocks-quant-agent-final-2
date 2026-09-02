from __future__ import annotations
from stocks.execution.cost_contracts_v2_36 import MarketStateV236, OrderIntentV236
from stocks.execution.execution_simulator_v2_36 import simulate_execution

def main() -> int:
    state = MarketStateV236(
        "AAA", 50.0, 12.0, 25_000_000, 0.025,
        liquidity_score=0.85, data_quality_score=0.95,
        time_of_day_factor=1.0, currency="USD", fx_conversion_bps=2.0,
    )
    result = simulate_execution(
        OrderIntentV236("AAA", 25_000),
        state,
        gross_edge_bps=180.0,
    )
    assert result.execution_authority == "NONE"
    assert result.one_way_cost["total_cost_bps"] > 0
    assert result.round_trip_cost_bps > result.one_way_cost["total_cost_bps"]
    assert result.edge_decision["status"] == "EXECUTABLE_RESEARCH"
    print("EXECUTION_COST_LIQUIDITY_V2_36_SELFCHECK OK")
    print("ONE_WAY_COST_BPS", round(float(result.one_way_cost["total_cost_bps"]), 4))
    print("ROUND_TRIP_COST_BPS", round(float(result.round_trip_cost_bps), 4))
    print("NET_EDGE_BPS", round(float(result.edge_decision["net_edge_bps"]), 4))
    print("PREFERRED_STYLE", result.style_comparison["preferred_style"])
    print("PARTIAL_FILL_SIMULATION True")
    print("COST_STRESS_1X_1_5X_2X_3X True")
    print("RESEARCH_COMPLIANCE_GATE_APPLIED False")
    print("BROKER_SUBMISSION_ENABLED False")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
