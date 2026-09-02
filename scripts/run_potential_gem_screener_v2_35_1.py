from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd
from stocks.research.potential_gem_screener_v2_35_1 import screen_potential_gems

def _read(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".parquet",".pq"}: return pd.read_parquet(path)
    return pd.read_csv(path)

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True,help="CSV or parquet candidate universe")
    p.add_argument("--output-dir",default="artifacts/potential_gem_screener_v2_35_1")
    p.add_argument("--limit",type=int,default=20)
    args=p.parse_args()
    result=screen_potential_gems(_read(Path(args.input)),shortlist_limit=args.limit)
    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)
    result.ranked.to_csv(out/"ranked.csv",index=False)
    result.shortlist.to_csv(out/"shortlist.csv",index=False)
    (out/"summary.json").write_text(json.dumps(result.summary.as_dict(),indent=2,sort_keys=True)+"\n")
    print("POTENTIAL_GEM_SCREENER_V2_35_1 OK")
    print("TOTAL",result.summary.total)
    print("ELIGIBLE",result.summary.eligible)
    print("GEM_A",result.summary.tier_a)
    print("GEM_B",result.summary.tier_b)
    print("WATCH",result.summary.watch)
    print("OUTPUT",out)
    print("EXECUTION_AUTHORITY",result.execution_authority)
    return 0
if __name__=="__main__": raise SystemExit(main())
