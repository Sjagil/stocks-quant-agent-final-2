from pathlib import Path
def test_gem_modules_have_no_broker_calls():
    text="\n".join(p.read_text() for p in Path("src/stocks/research").glob("*v2_35_1.py"))
    assert "placeOrder(" not in text
    assert "automatic_live_promotion" not in text.lower()
