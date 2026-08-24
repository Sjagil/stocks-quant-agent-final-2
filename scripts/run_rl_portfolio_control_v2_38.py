from __future__ import annotations
import json,argparse
from pathlib import Path
from stocks.rl.policy_challengers_v2_38 import challenger_specs

def main()->int:
  p=argparse.ArgumentParser(); p.add_argument("--output",default="artifacts/rl_v2_38/algorithm_specs.json"); a=p.parse_args(); out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps([x.as_dict() for x in challenger_specs()],indent=2)+"\n"); print("RL_PORTFOLIO_CONTROL_V2_38 OK"); print("OUTPUT",out); print("EXECUTION_AUTHORITY NONE"); return 0
if __name__=="__main__": raise SystemExit(main())
