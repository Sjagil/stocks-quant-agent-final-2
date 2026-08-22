from pathlib import Path


def test_v232_source_has_no_broker_order_authority():
    root = Path("src/stocks/research")
    paths = sorted(root.glob("*v2_32.py"))
    assert paths
    text = "\n".join(path.read_text() for path in paths)
    assert "placeOrder(" not in text
    assert 'execution_authority: str = "NONE"' in text
