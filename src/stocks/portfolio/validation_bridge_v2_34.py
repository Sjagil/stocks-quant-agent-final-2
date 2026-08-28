from __future__ import annotations
from collections.abc import Iterable, Mapping

def validated_strategy_ids(decisions: Iterable[object]) -> tuple[str,...]:
    result=[]
    for d in decisions:
        if isinstance(d,Mapping):
            sid=str(d.get("strategy_id","")).strip(); status=str(d.get("status","")).strip(); blockers=tuple(d.get("blockers",()) or ())
        else:
            sid=str(getattr(d,"strategy_id","")).strip(); status=str(getattr(d,"status","")).strip(); blockers=tuple(getattr(d,"blockers",()) or ())
        if sid and status=="PROMOTE_VALIDATION" and not blockers: result.append(sid)
    return tuple(sorted(set(result)))

__all__=["validated_strategy_ids"]
