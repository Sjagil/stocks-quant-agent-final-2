from __future__ import annotations

import json
from pathlib import Path


def production_status(output_root: Path) -> dict:
    summary = output_root / "latest_production_summary.json"
    if summary.is_file():
        return json.loads(summary.read_text(encoding="utf-8"))
    entities = []
    if output_root.is_dir():
        for path in sorted(output_root.glob("STRATEGY__*/production_result.json")):
            try:
                entities.append(json.loads(path.read_text(encoding="utf-8")))
            except Exception:
                continue
    return {
        "schema": "research_evidence_production_status_v2_39_3",
        "attempted": len(entities),
        "results": entities,
        "execution_authority": "NONE",
    }


__all__ = ["production_status"]
