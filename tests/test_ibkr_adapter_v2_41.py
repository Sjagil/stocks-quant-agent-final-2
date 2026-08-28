import os, sys, types
from datetime import datetime, timezone

from stocks.production.ibkr_adapter_v2_41 import IBKRBrokerV241


class V:
    def __init__(self,tag,value,currency='EUR'): self.tag=tag; self.value=value; self.currency=currency

class FakeIB:
    def __init__(self): self.connected=False
    def connect(self,*a,**k): self.connected=True
    def managedAccounts(self): return ['DU1']
    def accountSummary(self,account=''): return [V('NetLiquidation','10000'),V('AvailableFunds','8000'),V('TotalCashValue','5000')]
    def positions(self,account=''): return []
    def openTrades(self): return []
    def fills(self): return []
    def reqCurrentTime(self): return datetime.now(timezone.utc)
    def isConnected(self): return self.connected
    def disconnect(self): self.connected=False

class Dummy:
    def __init__(self,*a,**k): pass


def install_fake():
    m=types.ModuleType('ib_async'); m.IB=FakeIB; m.Stock=Dummy; m.Forex=Dummy; m.LimitOrder=Dummy; m.StopOrder=Dummy
    sys.modules['ib_async']=m


def cfg():
    return {'runtime':{'broker_snapshot_timeout_seconds':8},'broker':{
      'environment_env':'IBKR_ENVIRONMENT','host_env':'IBKR_HOST','port_env':'IBKR_PORT','client_id_env':'IBKR_CLIENT_ID','account_env':'IBKR_ACCOUNT',
      'default_host':'127.0.0.1','default_paper_port':7497,'default_live_port':7496,'default_client_id':41}}


def test_snapshot_derives_base_currency(monkeypatch):
    install_fake(); monkeypatch.setenv('IBKR_ENVIRONMENT','PAPER'); monkeypatch.delenv('IBKR_BASE_CURRENCY',raising=False)
    b=IBKRBrokerV241(cfg(),readonly=True); s=b.snapshot(); b.close()
    assert s.base_currency=='EUR' and s.net_liquidation==10000 and s.broker_write_calls==0


def test_configured_base_currency_mismatch_fails(monkeypatch):
    install_fake(); monkeypatch.setenv('IBKR_ENVIRONMENT','PAPER'); monkeypatch.setenv('IBKR_BASE_CURRENCY','USD')
    b=IBKRBrokerV241(cfg(),readonly=True)
    try:
        try: b.snapshot(); assert False
        except RuntimeError as e: assert 'mismatch' in str(e)
    finally: b.close()
