from stocks.execution.break_even_v2_36 import executable_edge_gate
from stocks.execution.cost_stress_v2_36 import stress_executable_edge

def test_cost_gate_rejects_weak_edge():
    assert executable_edge_gate(gross_edge_bps=10, expected_cost_bps=9).status == "REJECT_COSTS"

def test_hard_liquidity_blocker_cannot_be_compensated():
    result = executable_edge_gate(
        gross_edge_bps=500,
        expected_cost_bps=20,
        hard_blockers=("ADV_FRACTION_EXCEEDED",),
    )
    assert result.status == "REJECT_COSTS"
    assert "ADV_FRACTION_EXCEEDED" in result.blockers

def test_stress_degrades_edge():
    rows = stress_executable_edge(100, 20)
    assert rows[0].net_edge_bps > rows[-1].net_edge_bps
    assert [x.multiple for x in rows] == [1.0, 1.5, 2.0, 3.0]
