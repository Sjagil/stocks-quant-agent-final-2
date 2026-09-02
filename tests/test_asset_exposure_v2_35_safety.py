from pathlib import Path
def test_v235_has_no_live_authority():
    paths=list(Path("src/stocks/portfolio").glob("*v2_35.py"))
    text="\n".join(p.read_text() for p in paths)
    assert "placeOrder(" not in text
    assert 'execution_authority: str="NONE"' in text or 'execution_authority: str = AUTHORITY_NONE' in text or 'execution_authority: str = "NONE"' in text
