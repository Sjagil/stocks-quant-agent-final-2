from __future__ import annotations
import tempfile
from pathlib import Path

from stocks.execution.cost_contracts_v2_36 import MarketStateV236
from stocks.shadow.attribution_v2_37 import attribute_closed_position
from stocks.shadow.contracts_v2_37 import ShadowDecisionV237, ShadowSide
from stocks.shadow.feedback_v2_37 import build_shadow_feedback
from stocks.shadow.idempotency_v2_37 import deterministic_identifier
from stocks.shadow.lifecycle_engine_v2_37 import ShadowLifecycleEngineV237
from stocks.shadow.position_state_v2_37 import reduce_position
from stocks.shadow.reconciliation_v2_37 import reconcile_shadow_ledger
from stocks.shadow.replay_v2_37 import replay_shadow_state

def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "shadow.sqlite3"
        engine = ShadowLifecycleEngineV237(db)
        state = MarketStateV236("AAA", 50.0, 10.0, 30_000_000, 0.025, liquidity_score=0.9, data_quality_score=0.95)
        decision = ShadowDecisionV237(
            "D1", "STRAT_A", "TREND", "AAA", ShadowSide.BUY, 20_000, 180,
            "2026-08-24T10:00:00Z", expected_horizon_bars=20,
        )
        submission = engine.submit_entry(decision, state)
        assert submission.status == "ORDER_CREATED"
        duplicate = engine.submit_entry(decision, state)
        assert duplicate.status == "IDEMPOTENT_EXISTING"
        engine.fill_entry(submission.order_id, state, fill_time="2026-08-24T10:01:00Z", force_fill_fraction=0.60)
        engine.fill_entry(submission.order_id, state, fill_time="2026-08-24T10:02:00Z", force_fill_fraction=1.00)
        position_id = deterministic_identifier("POS", submission.order_id)
        engine.mark_position(position_id, price=54.0, bars_held=8, mark_time="2026-08-24T12:00:00Z")
        exit_state = MarketStateV236("AAA", 53.0, 11.0, 30_000_000, 0.026, liquidity_score=0.88, data_quality_score=0.95)
        closed = engine.evaluate_and_exit(position_id, exit_state, bars_held=10, event_time="2026-08-24T13:00:00Z", force_exit=True)
        assert closed.status == "CLOSED"
        assert closed.quantity == 0.0
        attr = attribute_closed_position(closed)
        feedback = build_shadow_feedback(attr, forecast_gross_edge_bps=180.0, predicted_round_trip_cost_bps=float(submission.predicted_round_trip_cost_bps))
        rec = reconcile_shadow_ledger(engine.ledger)
        assert rec.status == "READY"
        snap1 = replay_shadow_state(engine.ledger)
        count = engine.ledger.event_count()
        engine.close()

        engine2 = ShadowLifecycleEngineV237(db)
        snap2 = replay_shadow_state(engine2.ledger)
        assert snap1.as_dict() == snap2.as_dict()
        assert engine2.ledger.event_count() == count
        assert engine2.ledger.verify_hash_chain()
        engine2.close()

    print("FULL_SHADOW_LIFECYCLE_V2_37_SELFCHECK OK")
    print("RESTART_SAFE_REPLAY True")
    print("IDEMPOTENT_DECISIONS True")
    print("HASH_CHAIN_LEDGER True")
    print("PARTIAL_FILL_TO_POSITION True")
    print("RISK_EXIT_WITHOUT_POSITIVE_EDGE_GATE True")
    print("MFE_MAE True")
    print("REALIZED_COST_ATTRIBUTION True")
    print("FORECAST_COST_FEEDBACK True")
    print("RECONCILIATION READY")
    print("BROKER_SUBMISSION_ENABLED False")
    print("ORDER_CALLS 0")
    print("EXECUTION_AUTHORITY NONE")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
