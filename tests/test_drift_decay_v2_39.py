import pandas as pd
from stocks.research.continuous.drift_decay_v2_39 import dataframe_drift,performance_decay

def test_drift_and_decay_detect_change():
 ref=pd.DataFrame({'x':list(range(100))}); cur=pd.DataFrame({'x':list(range(100,200))})
 report,severity=dataframe_drift(ref,cur); assert not report.empty and severity>0.5
 decay=performance_decay([10]*20+[-10]*10); assert decay.severity>0.5
