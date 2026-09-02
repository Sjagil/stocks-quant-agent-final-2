from pathlib import Path

def test_v233_has_no_order_authority():
 paths=list(Path('src/stocks/research').glob('*v2_33.py')); text='\n'.join(p.read_text() for p in paths)
 assert paths and 'placeOrder(' not in text and 'execution_authority: str = "NONE"' in text
