import pytest
from stocks.research.continuous.runtime_lock_v2_39 import exclusive_runtime_lock

def test_runtime_lock_blocks_second_process_handle(tmp_path):
 p=tmp_path/'lock'
 with exclusive_runtime_lock(p):
  with pytest.raises(RuntimeError):
   with exclusive_runtime_lock(p): pass
