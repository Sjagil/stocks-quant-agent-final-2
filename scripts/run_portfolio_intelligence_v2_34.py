from __future__ import annotations
import argparse,json
from pathlib import Path
import pandas as pd
from stocks.portfolio.portfolio_intelligence_v2_34 import build_portfolio_intelligence

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--returns",required=True); ap.add_argument("--expected",required=True); ap.add_argument("--metadata",required=True); ap.add_argument("--validated",required=True,help="JSON file containing a list of v2.33 accepted strategy IDs"); ap.add_argument("--previous"); ap.add_argument("--output",required=True); ap.add_argument("--no-convex",action="store_true"); args=ap.parse_args()
    returns=pd.read_csv(args.returns,index_col=0); expected=pd.read_csv(args.expected,index_col=0).iloc[:,0]; metadata=pd.read_csv(args.metadata,index_col=0); previous=pd.read_csv(args.previous,index_col=0).iloc[:,0] if args.previous else None
    validated=tuple(json.loads(Path(args.validated).read_text())); result=build_portfolio_intelligence(returns,expected,metadata,validated_ids=validated,previous_weights=previous,include_convex=not args.no_convex)
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result.as_dict(),indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(out)
if __name__=="__main__": main()
