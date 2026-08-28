from __future__ import annotations
import argparse, json
from pathlib import Path
from stocks.research.validation_orchestrator_v2_33 import validate_strategy_candidate


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',required=True,help='JSON validation dataset')
    parser.add_argument('--output',default='artifacts/statistical_validation_v2_33/validation.json')
    args=parser.parse_args()
    payload=json.loads(Path(args.input).read_text())
    result=validate_strategy_candidate(
        strategy_id=str(payload['strategy_id']),
        period_returns=payload['period_returns'], trade_returns=payload['trade_returns'],
        trial_returns_matrix=payload['trial_returns_matrix'], trial_sharpes=payload['trial_sharpes'],
        is_fold_metrics=payload['is_fold_metrics'], oos_fold_metrics=payload['oos_fold_metrics'],
        center_parameter_score=float(payload['center_parameter_score']), neighbor_parameter_scores=payload['neighbor_parameter_scores'],
        baseline_round_trip_cost_bps=float(payload['baseline_round_trip_cost_bps']), no_leakage=bool(payload.get('no_leakage',True)),
        cross_engine_validated=bool(payload.get('cross_engine_validated',False)), p_values=payload.get('p_values'), trial_correlation=payload.get('trial_correlation'),
    )
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result.as_dict(),indent=2,sort_keys=True,allow_nan=False)+'\n')
    print('STATISTICAL_VALIDATION_V2_33', result.decision['status'], 'SCORE', round(float(result.decision['score']),6))
    print('OUTPUT', out)
    print('EXECUTION_AUTHORITY', result.execution_authority)
    return 0
if __name__=='__main__': raise SystemExit(main())
