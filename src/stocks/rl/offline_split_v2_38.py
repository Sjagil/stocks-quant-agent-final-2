from __future__ import annotations
from dataclasses import dataclass, asdict
import numpy as np

@dataclass(frozen=True)
class PurgedRLSplitV238:
    train: tuple[int,...]; validation: tuple[int,...]; test: tuple[int,...]; purge_bars:int; random_shuffle:bool=False
    def as_dict(self): return asdict(self)

def purged_chronological_split(n:int, *, train_fraction:float=.60, validation_fraction:float=.20, purge_bars:int=8)->PurgedRLSplitV238:
    if n<50: raise ValueError("at least 50 rows")
    if not 0<train_fraction<1 or not 0<validation_fraction<1 or train_fraction+validation_fraction>=1: raise ValueError("invalid fractions")
    a=int(n*train_fraction); b=int(n*(train_fraction+validation_fraction)); p=max(0,int(purge_bars))
    train=np.arange(0,max(0,a-p)); val=np.arange(min(n,a+p),max(min(n,a+p),b-p)); test=np.arange(min(n,b+p),n)
    if min(len(train),len(val),len(test))==0: raise ValueError("purge leaves empty split")
    return PurgedRLSplitV238(tuple(map(int,train)),tuple(map(int,val)),tuple(map(int,test)),p,False)

__all__=["PurgedRLSplitV238","purged_chronological_split"]
