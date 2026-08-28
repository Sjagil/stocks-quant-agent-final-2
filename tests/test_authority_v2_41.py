from datetime import datetime, timezone, timedelta
from stocks.production.authority_v2_41 import arm_live, live_arm_status, set_submission, authority_status, engage_kill_switch, clear_kill_switch
from stocks.production.state_store_v2_41 import ProductionStoreV241


def cfg(tmp_path):
    return {
      "mode":"PAPER",
      "runtime":{"arm_state_path":"arm.json","kill_switch_path":"KILL"},
      "authority":{"live_arm_hours":24,"submission_enabled_by_default":False,"automatic_live_promotion":False,"automatic_champion_promotion":False},
    }


def test_live_arm_expires_and_kill_is_fail_closed(tmp_path):
    c=cfg(tmp_path); s=ProductionStoreV241(tmp_path/'db.sqlite3')
    payload=arm_live(tmp_path,c,hours=1)
    assert live_arm_status(tmp_path,c)[0]
    future=datetime.now(timezone.utc)+timedelta(hours=2)
    assert not live_arm_status(tmp_path,c,now=future)[0]
    set_submission(s,enabled=True,environment='PAPER')
    engage_kill_switch(tmp_path,c,'test')
    assert authority_status(tmp_path,c,s).kill_switch_active
    clear_kill_switch(tmp_path,c)
    assert not authority_status(tmp_path,c,s).kill_switch_active
