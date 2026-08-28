from stocks.portfolio.asset_exposure_contracts_v2_35 import ExposurePolicyV235
from stocks.portfolio.asset_exposure_engine_v2_35 import PortfolioExposureSnapshot
from stocks.portfolio.exposure_constraints_v2_35 import evaluate_exposure_constraints

def test_sector_breach_blocks():
    snap=PortfolioExposureSnapshot(0.5,0.5,{"TECH":0.4},{},{"US":0.5},{"USD":0.5},{},{},0.0,())
    out=evaluate_exposure_constraints(snap,policy=ExposurePolicyV235(max_sector_weight=0.35))
    assert out.status=="BLOCK" and any(x.startswith("SECTOR_CAP") for x in out.blockers)
