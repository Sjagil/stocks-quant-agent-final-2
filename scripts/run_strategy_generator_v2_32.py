from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from stocks.research.feature_registry_v2_31 import default_feature_registry
from stocks.research.strategy_generator_v2_32 import run_strategy_generator


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--governance-json", required=True)
    parser.add_argument("--output", default="artifacts/strategy_generator_v2_32/strategy_candidates.json")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    cfg = json.loads((root / "config/strategy_generator_v2_32.json").read_text())
    raw = json.loads(Path(args.governance_json).read_text())
    if isinstance(raw.get("governance"), list):
        governance = {str(row["feature_id"]): row for row in raw["governance"]}
    elif isinstance(raw.get("features"), dict):
        governance = raw["features"]
    else:
        governance = raw
    result = run_strategy_generator(
        governance,
        registry=default_feature_registry(),
        maximum_variants_per_family=int(cfg["maximum_variants_per_family"]),
        maximum_selected=int(cfg["maximum_selected"]),
        max_similarity=float(cfg["max_similarity"]),
        max_per_family=int(cfg["max_per_family"]),
        generator_config=cfg,
        source_branch=_git(root, "branch", "--show-current"),
        source_commit=_git(root, "rev-parse", "HEAD"),
    )
    output = root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result.as_dict(), indent=2, sort_keys=True, allow_nan=False) + "\n")
    print("STRATEGY_GENERATOR_V2_32", "SELECTED", result.selected_count, "FAMILIES", result.family_count)
    print("OUTPUT", output)
    print("EXECUTION_AUTHORITY", result.execution_authority)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
