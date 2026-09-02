from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_old_entrypoints_forward_to_v2392():
    old = (ROOT / "scripts/run_continuous_quant_research_v2_39.py").read_text()
    v391 = (ROOT / "scripts/run_continuous_quant_research_v2_39_1.py").read_text()
    assert "run_continuous_quant_research_v2_39_2.py" in old
    assert "run_continuous_quant_research_v2_39_2.py" in v391
